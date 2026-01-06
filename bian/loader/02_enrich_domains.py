"""
02_enrich_domains.py

Enriches BIANServiceDomain nodes with data from scraped JSON files.

Updates:
  BIANServiceDomain nodes with:
    - role, example_of_use, executive_summary, key_features
    - functional_pattern (from relations_all.realized_by[0])

Creates:
  (:BIANServiceDomain)-[:TRIGGERS]->(:BIANServiceDomain)

Run: python 02_enrich_domains.py

Prerequisites:
  - Run 01_load_hierarchy.py first
  - pip install neo4j
"""

import json
from datetime import datetime
from pathlib import Path
from neo4j import GraphDatabase

# ============================================
# CONFIGURATION - UPDATE THESE!
# ============================================

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"  # ← Change this!

# Path to your scraped data (from bian_scrape.py output)
DATA_DIR = Path(r"G:\bian_scaper\output")  # ← Change this!
SERVICE_DOMAINS_DIR = DATA_DIR / "service_domains"

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
# EXTRACT FUNCTIONAL PATTERN
# ============================================

KNOWN_PATTERNS = [
    "Fulfill", "Manage", "Administer", "Register", "Maintain",
    "Direct", "Monitor", "Analyze", "Evaluate", "Execute", "Operate",
    "Allocate", "Agree Terms", "Design", "Develop", "Process", "Track"
]


def extract_functional_pattern(data: dict) -> str | None:
    """Extract functional pattern from relations_all.realized_by[0].name"""
    relations_all = data.get("relations_all", {})
    realized_by = relations_all.get("realized_by", [])
    
    if not realized_by:
        return None
    
    first_name = realized_by[0].get("name", "")
    for pattern in KNOWN_PATTERNS:
        if first_name == pattern:
            return pattern
    
    return None


# ============================================
# ENRICH DOMAINS
# ============================================

def enrich_domains(run_id: str):
    """Load enrichment data from JSON files and update Neo4j nodes."""
    
    if not SERVICE_DOMAINS_DIR.exists():
        print(f"ERROR: {SERVICE_DOMAINS_DIR} not found!")
        return
    
    json_files = list(SERVICE_DOMAINS_DIR.glob("*.json"))
    print(f"Found {len(json_files)} service domain JSON files.")
    print(f"Run ID: {run_id}")
    
    enriched_count = 0
    error_count = 0
    pattern_counts = {}
    
    for json_file in json_files:
        object_id = json_file.stem
        
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if "error" in data and len(data) <= 4:
                error_count += 1
                continue
            
            role = data.get("role_definition", "")
            example_of_use = data.get("example_of_use", "")
            executive_summary = data.get("executive_summary", "")
            key_features = data.get("key_features", [])
            
            # Clean key_features
            key_features = [
                f.strip() for f in key_features 
                if f and f.strip() and f.strip() not in ["**", "General comment"]
            ]
            
            functional_pattern = extract_functional_pattern(data)
            
            if functional_pattern:
                pattern_counts[functional_pattern] = pattern_counts.get(functional_pattern, 0) + 1
            
            run_cypher("""
                MATCH (sd:BIANServiceDomain {object_id: $object_id})
                SET sd.role = $role,
                    sd.example_of_use = $example_of_use,
                    sd.executive_summary = $executive_summary,
                    sd.key_features = $key_features,
                    sd.functional_pattern = $functional_pattern,
                    sd._enriched_at = datetime(),
                    sd._run_id = $run_id
            """, {
                "object_id": object_id,
                "role": role,
                "example_of_use": example_of_use,
                "executive_summary": executive_summary,
                "key_features": key_features,
                "functional_pattern": functional_pattern,
                "run_id": run_id
            })
            
            enriched_count += 1
            
            if enriched_count % 50 == 0:
                print(f"  Enriched {enriched_count} domains...")
                
        except Exception as e:
            print(f"  Error processing {object_id}: {e}")
            error_count += 1
    
    print(f"\nEnriched {enriched_count} domains, {error_count} errors/skipped")
    print(f"\nFunctional patterns found:")
    for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        print(f"  {pattern}: {count}")


# ============================================
# CREATE RELATIONSHIPS
# ============================================

def create_relationships():
    """Create TRIGGERS relationships between Service Domains."""
    
    print("\nCreating inter-domain relationships...")
    
    json_files = list(SERVICE_DOMAINS_DIR.glob("*.json"))
    triggers_count = 0
    triggered_by_count = 0
    
    for json_file in json_files:
        object_id = json_file.stem
        
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if "error" in data and len(data) <= 4:
                continue
            
            relations = data.get("relations_service_domains", {})
            
            for target in relations.get("triggers", []):
                target_id = target.get("object_id")
                if target_id and target_id != object_id:
                    run_cypher("""
                        MATCH (source:BIANServiceDomain {object_id: $source_id})
                        MATCH (target:BIANServiceDomain {object_id: $target_id})
                        MERGE (source)-[:TRIGGERS]->(target)
                    """, {"source_id": object_id, "target_id": target_id})
                    triggers_count += 1
            
            for source in relations.get("triggered_by", []):
                source_id = source.get("object_id")
                if source_id and source_id != object_id:
                    run_cypher("""
                        MATCH (target:BIANServiceDomain {object_id: $target_id})
                        MATCH (source:BIANServiceDomain {object_id: $source_id})
                        MERGE (source)-[:TRIGGERS]->(target)
                    """, {"target_id": object_id, "source_id": source_id})
                    triggered_by_count += 1
                        
        except Exception as e:
            pass
    
    print(f"Created relationships: {triggers_count + triggered_by_count} total")
    
    result = run_cypher("MATCH ()-[r:TRIGGERS]->() RETURN count(r) AS total")
    if result:
        print(f"Total TRIGGERS relationships: {result[0]['total']}")


# ============================================
# VERIFY
# ============================================

def verify_enrichment():
    """Verify the enrichment."""
    print("\nVerifying enrichment...")
    
    result = run_cypher("""
        MATCH (sd:BIANServiceDomain)
        WHERE sd.role IS NOT NULL AND sd.role <> ''
        RETURN count(sd) AS enriched
    """)
    if result:
        print(f"  Domains with role: {result[0]['enriched']}")
    
    result = run_cypher("""
        MATCH (sd:BIANServiceDomain)
        WHERE sd.functional_pattern IS NOT NULL
        RETURN sd.functional_pattern AS pattern, count(*) AS count
        ORDER BY count DESC
    """)
    if result:
        print("  Functional patterns:")
        for row in result:
            print(f"    {row['pattern']}: {row['count']}")


# ============================================
# MAIN
# ============================================

def main():
    print("=" * 60)
    print("BIAN Domain Enrichment")
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
        print("ERROR: No Service Domains found. Run 01_load_hierarchy.py first!")
        return
    
    print(f"Found {result[0]['count']} Service Domains to enrich.")
    
    run_id = f"bian-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    enrich_domains(run_id)
    create_relationships()
    verify_enrichment()
    
    print("\n" + "=" * 60)
    print(f"Enrichment complete! (run_id: {run_id})")
    print("Next: Run 03_load_yaml.py")
    print("=" * 60)
    
    driver.close()


if __name__ == "__main__":
    main()
