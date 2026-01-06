"""
03_load_yaml.py

Loads BIAN OpenAPI YAML specifications into Neo4j.

Creates:
  (:BIANServiceDomain)-[:HAS_CR]->(:BIANControlRecord)
  (:BIANServiceDomain)-[:HAS_BQ]->(:BIANBehaviorQualifier)
  (:BIANServiceDomain)-[:HAS_OPERATION]->(:BIANOperation)
  (:BIANServiceDomain)-[:HAS_SCHEMA]->(:BIANSchema)
  (:BIANOperation)-[:FOR_CR]->(:BIANControlRecord)
  (:BIANOperation)-[:FOR_BQ]->(:BIANBehaviorQualifier)

Run: python 03_load_yaml.py

Prerequisites:
  - Run 01_load_hierarchy.py and 02_enrich_domains.py first
  - pip install neo4j pyyaml
"""

import re
from datetime import datetime
from pathlib import Path
from neo4j import GraphDatabase

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    exit(1)

# ============================================
# CONFIGURATION - UPDATE THESE!
# ============================================

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"  # ← Change this!

# Path to your YAML files
YAML_DIR = Path(r"D:\bian\public\release13.0.0\semantic-apis\oas3\yamls")  # ← Change this!

# ============================================
# NEO4J CONNECTION
# ============================================

driver = None


def connect():
    global driver
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def run_cypher(cypher: str, parameters: dict = None):
    """Execute a Cypher statement."""
    with driver.session() as session:
        result = session.run(cypher, parameters or {})
        return result.data()


# ============================================
# HELPERS
# ============================================

ACTION_TERMS = [
    'Initiate', 'Create', 'Update', 'Retrieve', 'Execute',
    'Request', 'Notify', 'Exchange', 'Control', 'Register',
    'Capture', 'Grant', 'Evaluate', 'Provide', 'Allocate'
]


def normalize_name(name: str) -> str:
    """Normalize name for matching and IDs."""
    return re.sub(r'[^a-z0-9]', '', name.lower())


def extract_action_term(operation_id: str) -> str:
    """Extract the action term from an operationId."""
    for term in ACTION_TERMS:
        if operation_id.startswith(term) or term in operation_id:
            return term
    return "Unknown"


# ============================================
# CREATE CONSTRAINTS
# ============================================

def create_constraints():
    """Create constraints for new node types."""
    print("Creating constraints...")
    
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (cr:BIANControlRecord) REQUIRE cr.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (bq:BIANBehaviorQualifier) REQUIRE bq.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (op:BIANOperation) REQUIRE op.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:BIANSchema) REQUIRE s.id IS UNIQUE",
    ]
    
    for cypher in constraints:
        try:
            run_cypher(cypher)
        except Exception as e:
            print(f"  Note: {e}")
    
    print("Constraints created.")


# ============================================
# FIND SERVICE DOMAIN
# ============================================

def find_service_domain(sd_name: str) -> str | None:
    """Find matching BIANServiceDomain by name."""
    
    # Exact match
    result = run_cypher("""
        MATCH (sd:BIANServiceDomain)
        WHERE sd.name = $name
        RETURN sd.object_id AS object_id
    """, {"name": sd_name})
    if result:
        return result[0]["object_id"]
    
    # Case-insensitive
    result = run_cypher("""
        MATCH (sd:BIANServiceDomain)
        WHERE toLower(sd.name) = toLower($name)
        RETURN sd.object_id AS object_id
    """, {"name": sd_name})
    if result:
        return result[0]["object_id"]
    
    # Normalized (remove spaces, special chars)
    normalized = normalize_name(sd_name)
    result = run_cypher("""
        MATCH (sd:BIANServiceDomain)
        WHERE toLower(replace(replace(replace(sd.name, ' ', ''), '-', ''), '&', '')) = $normalized
        RETURN sd.object_id AS object_id
    """, {"normalized": normalized})
    if result:
        return result[0]["object_id"]
    
    # Partial match
    result = run_cypher("""
        MATCH (sd:BIANServiceDomain)
        WITH sd, toLower(replace(replace(sd.name, ' ', ''), '-', '')) AS norm_name
        WHERE norm_name CONTAINS $partial OR $partial CONTAINS norm_name
        RETURN sd.object_id AS object_id
        LIMIT 1
    """, {"partial": normalized[:15]})
    if result:
        return result[0]["object_id"]
    
    return None


# ============================================
# PARSE YAML
# ============================================

def parse_yaml_file(yaml_path: Path) -> dict:
    """Parse a BIAN OpenAPI YAML file."""
    
    with open(yaml_path, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    
    info = spec.get("info", {})
    sd_name = info.get("title", yaml_path.stem)
    sd_id = normalize_name(sd_name)
    
    control_records = {}
    behavior_qualifiers = {}
    operations = []
    
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method, op_data in methods.items():
            if not isinstance(op_data, dict):
                continue
            
            tags = op_data.get("tags", [])
            if not tags:
                continue
            
            tag = tags[0]
            operation_id = op_data.get("operationId", "")
            summary = op_data.get("summary", "")
            
            target_type = None
            target_name = None
            
            if tag.startswith("CR - "):
                target_type = "CR"
                target_name = tag.replace("CR - ", "").strip()
                control_records[target_name] = {
                    "id": f"{sd_id}-CR-{normalize_name(target_name)}",
                    "name": target_name
                }
            elif tag.startswith("BQ - "):
                target_type = "BQ"
                target_name = tag.replace("BQ - ", "").strip()
                behavior_qualifiers[target_name] = {
                    "id": f"{sd_id}-BQ-{normalize_name(target_name)}",
                    "name": target_name
                }
            
            if target_type and operation_id:
                operations.append({
                    "id": f"{sd_id}-OP-{operation_id}",
                    "name": operation_id,
                    "action_term": extract_action_term(operation_id),
                    "summary": summary,
                    "http_method": method.upper(),
                    "path": path,
                    "target_type": target_type,
                    "target_name": target_name
                })
    
    schemas = []
    for schema_name, schema_def in spec.get("components", {}).get("schemas", {}).items():
        if schema_name == "HTTPError":
            continue
        schemas.append({
            "id": f"{sd_id}-SCHEMA-{normalize_name(schema_name)}",
            "name": schema_name,
            "type": schema_def.get("type", "object")
        })
    
    return {
        "sd_name": sd_name,
        "sd_id": sd_id,
        "control_records": list(control_records.values()),
        "behavior_qualifiers": list(behavior_qualifiers.values()),
        "operations": operations,
        "schemas": schemas
    }


# ============================================
# LOAD YAML TO NEO4J
# ============================================

def load_yaml_to_neo4j(yaml_data: dict, sd_object_id: str, run_id: str):
    """Load parsed YAML data into Neo4j."""
    
    sd_id = yaml_data["sd_id"]
    
    # Control Records
    for cr in yaml_data["control_records"]:
        run_cypher("""
            MATCH (sd:BIANServiceDomain {object_id: $sd_object_id})
            MERGE (cr:BIANControlRecord {id: $id})
            SET cr.name = $name, cr._imported_at = datetime(), cr._run_id = $run_id
            MERGE (sd)-[:HAS_CR]->(cr)
        """, {"sd_object_id": sd_object_id, "id": cr["id"], "name": cr["name"], "run_id": run_id})
    
    # Behavior Qualifiers
    for bq in yaml_data["behavior_qualifiers"]:
        run_cypher("""
            MATCH (sd:BIANServiceDomain {object_id: $sd_object_id})
            MERGE (bq:BIANBehaviorQualifier {id: $id})
            SET bq.name = $name, bq._imported_at = datetime(), bq._run_id = $run_id
            MERGE (sd)-[:HAS_BQ]->(bq)
        """, {"sd_object_id": sd_object_id, "id": bq["id"], "name": bq["name"], "run_id": run_id})
    
    # Operations
    for op in yaml_data["operations"]:
        target_id = f"{sd_id}-{op['target_type']}-{normalize_name(op['target_name'])}"
        
        run_cypher("""
            MATCH (sd:BIANServiceDomain {object_id: $sd_object_id})
            MERGE (op:BIANOperation {id: $id})
            SET op.name = $name, op.action_term = $action_term, op.summary = $summary,
                op.http_method = $http_method, op.path = $path,
                op._imported_at = datetime(), op._run_id = $run_id
            MERGE (sd)-[:HAS_OPERATION]->(op)
        """, {
            "sd_object_id": sd_object_id,
            "id": op["id"],
            "name": op["name"],
            "action_term": op["action_term"],
            "summary": op["summary"],
            "http_method": op["http_method"],
            "path": op["path"],
            "run_id": run_id
        })
        
        # Link to CR or BQ
        if op["target_type"] == "CR":
            run_cypher("""
                MATCH (op:BIANOperation {id: $op_id})
                MATCH (target:BIANControlRecord {id: $target_id})
                MERGE (op)-[:FOR_CR]->(target)
            """, {"op_id": op["id"], "target_id": target_id})
        else:
            run_cypher("""
                MATCH (op:BIANOperation {id: $op_id})
                MATCH (target:BIANBehaviorQualifier {id: $target_id})
                MERGE (op)-[:FOR_BQ]->(target)
            """, {"op_id": op["id"], "target_id": target_id})
    
    # Schemas
    for schema in yaml_data["schemas"]:
        run_cypher("""
            MATCH (sd:BIANServiceDomain {object_id: $sd_object_id})
            MERGE (s:BIANSchema {id: $id})
            SET s.name = $name, s.type = $type, s._imported_at = datetime(), s._run_id = $run_id
            MERGE (sd)-[:HAS_SCHEMA]->(s)
        """, {"sd_object_id": sd_object_id, "id": schema["id"], "name": schema["name"], "type": schema["type"], "run_id": run_id})


# ============================================
# MAIN LOADER
# ============================================

def load_all_yaml(run_id: str):
    """Load all YAML files."""
    
    if not YAML_DIR.exists():
        print(f"ERROR: {YAML_DIR} not found!")
        return
    
    yaml_files = list(YAML_DIR.glob("*.yaml"))
    print(f"Found {len(yaml_files)} YAML files.")
    print(f"Run ID: {run_id}")
    
    loaded = 0
    not_matched = []
    errors = []
    
    for yaml_file in yaml_files:
        try:
            yaml_data = parse_yaml_file(yaml_file)
            sd_name = yaml_data["sd_name"]
            sd_object_id = find_service_domain(sd_name)
            
            if not sd_object_id:
                not_matched.append(sd_name)
                continue
            
            load_yaml_to_neo4j(yaml_data, sd_object_id, run_id)
            loaded += 1
            
            if loaded % 25 == 0:
                print(f"  Loaded {loaded} YAML files...")
                
        except Exception as e:
            errors.append((yaml_file.name, str(e)))
    
    print(f"\nLoaded: {loaded}, Not matched: {len(not_matched)}, Errors: {len(errors)}")
    
    if not_matched:
        print(f"\nNot matched ({len(not_matched)}):")
        for name in not_matched[:5]:
            print(f"  - {name}")


# ============================================
# VERIFY
# ============================================

def verify_import():
    """Verify the import."""
    print("\nVerifying YAML import...")
    
    result = run_cypher("""
        MATCH (sd:BIANServiceDomain)
        OPTIONAL MATCH (sd)-[:HAS_CR]->(cr)
        OPTIONAL MATCH (sd)-[:HAS_BQ]->(bq)
        OPTIONAL MATCH (sd)-[:HAS_OPERATION]->(op)
        OPTIONAL MATCH (sd)-[:HAS_SCHEMA]->(s)
        RETURN count(DISTINCT sd) AS domains,
               count(DISTINCT cr) AS crs,
               count(DISTINCT bq) AS bqs,
               count(DISTINCT op) AS ops,
               count(DISTINCT s) AS schemas
    """)
    
    if result:
        r = result[0]
        print(f"  Service Domains: {r['domains']}")
        print(f"  Control Records: {r['crs']}")
        print(f"  Behavior Qualifiers: {r['bqs']}")
        print(f"  Operations: {r['ops']}")
        print(f"  Schemas: {r['schemas']}")


# ============================================
# MAIN
# ============================================

def main():
    print("=" * 60)
    print("BIAN YAML Loader (OpenAPI Specs)")
    print("=" * 60)
    
    try:
        connect()
        run_cypher("RETURN 1")
        print("Connected to Neo4j.")
    except Exception as e:
        print(f"ERROR: Cannot connect to Neo4j: {e}")
        return
    
    result = run_cypher("MATCH (sd:BIANServiceDomain) RETURN count(sd) AS count")
    if not result or result[0]["count"] == 0:
        print("ERROR: No Service Domains found. Run 01 and 02 first!")
        return
    
    print(f"Found {result[0]['count']} Service Domains.")
    
    run_id = f"bian-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    create_constraints()
    load_all_yaml(run_id)
    verify_import()
    
    print("\n" + "=" * 60)
    print(f"YAML loading complete! (run_id: {run_id})")
    print("BIAN reference data is now fully loaded.")
    print("=" * 60)
    
    driver.close()


if __name__ == "__main__":
    main()
