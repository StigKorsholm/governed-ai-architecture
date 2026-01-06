"""
01_load_hierarchy.py

Loads BIAN hierarchy from index_hierarchy.json into Neo4j.

Creates:
  (:BusinessArea)-[:HAS_DOMAIN]->(:BusinessDomain)
  (:BusinessDomain)-[:HAS_SERVICE]->(:BIANServiceDomain)

Run: python 01_load_hierarchy.py

Prerequisites:
  - pip install neo4j
  - Run 00_clear_database.py first (optional, for clean import)
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
HIERARCHY_FILE = DATA_DIR / "index_hierarchy.json"

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
# CREATE CONSTRAINTS
# ============================================

def create_constraints():
    """Create uniqueness constraints."""
    print("Creating constraints...")
    
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (ba:BusinessArea) REQUIRE ba.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (bd:BusinessDomain) REQUIRE bd.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (sd:BIANServiceDomain) REQUIRE sd.object_id IS UNIQUE",
    ]
    
    for cypher in constraints:
        try:
            run_cypher(cypher)
        except Exception as e:
            print(f"  Note: {e}")
    
    print("Constraints created.")


# ============================================
# LOAD HIERARCHY
# ============================================

def load_hierarchy(run_id: str):
    """Load the BIAN hierarchy from JSON."""
    
    if not HIERARCHY_FILE.exists():
        print(f"ERROR: {HIERARCHY_FILE} not found!")
        print("Run the BIAN scraper first to generate this file.")
        return False
    
    print(f"Loading hierarchy from {HIERARCHY_FILE}...")
    print(f"Run ID: {run_id}")
    
    with open(HIERARCHY_FILE, "r", encoding="utf-8") as f:
        hierarchy = json.load(f)
    
    ba_count = 0
    bd_count = 0
    sd_count = 0
    
    for ba in hierarchy:
        ba_name = ba["business_area"]
        
        run_cypher("""
            MERGE (ba:BusinessArea {name: $name})
            SET ba._imported_at = datetime(),
                ba._run_id = $run_id
        """, {"name": ba_name, "run_id": run_id})
        ba_count += 1
        
        for bd in ba.get("business_domains", []):
            bd_name = bd["business_domain"]
            
            run_cypher("""
                MATCH (ba:BusinessArea {name: $ba_name})
                MERGE (bd:BusinessDomain {name: $bd_name})
                SET bd._imported_at = datetime(),
                    bd._run_id = $run_id
                MERGE (ba)-[:HAS_DOMAIN]->(bd)
            """, {"ba_name": ba_name, "bd_name": bd_name, "run_id": run_id})
            bd_count += 1
            
            for sd in bd.get("service_domains", []):
                sd_name = sd["name"]
                sd_object_id = sd.get("object_id")
                sd_url = sd.get("url")
                
                run_cypher("""
                    MATCH (bd:BusinessDomain {name: $bd_name})
                    MERGE (sd:BIANServiceDomain {object_id: $object_id})
                    SET sd.name = $name,
                        sd.url = $url,
                        sd._imported_at = datetime(),
                        sd._run_id = $run_id
                    MERGE (bd)-[:HAS_SERVICE]->(sd)
                """, {
                    "bd_name": bd_name,
                    "name": sd_name,
                    "object_id": sd_object_id,
                    "url": sd_url,
                    "run_id": run_id
                })
                sd_count += 1
    
    print(f"Loaded: {ba_count} Business Areas, {bd_count} Business Domains, {sd_count} Service Domains")
    return True


# ============================================
# VERIFY
# ============================================

def verify_import():
    """Verify the import."""
    print("\nVerifying import...")
    
    result = run_cypher("""
        MATCH (ba:BusinessArea)
        OPTIONAL MATCH (ba)-[:HAS_DOMAIN]->(bd:BusinessDomain)
        OPTIONAL MATCH (bd)-[:HAS_SERVICE]->(sd:BIANServiceDomain)
        RETURN count(DISTINCT ba) AS business_areas,
               count(DISTINCT bd) AS business_domains,
               count(DISTINCT sd) AS service_domains
    """)
    
    if result:
        r = result[0]
        print(f"  Business Areas: {r['business_areas']}")
        print(f"  Business Domains: {r['business_domains']}")
        print(f"  Service Domains: {r['service_domains']}")
    
    print("\nSample hierarchy:")
    result = run_cypher("""
        MATCH (ba:BusinessArea)-[:HAS_DOMAIN]->(bd:BusinessDomain)-[:HAS_SERVICE]->(sd:BIANServiceDomain)
        RETURN ba.name AS business_area, bd.name AS business_domain, sd.name AS service_domain
        LIMIT 5
    """)
    for row in result:
        print(f"  {row['business_area']} → {row['business_domain']} → {row['service_domain']}")


# ============================================
# MAIN
# ============================================

def main():
    print("=" * 60)
    print("BIAN Hierarchy Loader")
    print("=" * 60)
    
    try:
        connect()
        run_cypher("RETURN 1")
        print("Connected to Neo4j.")
    except Exception as e:
        print(f"ERROR: Cannot connect to Neo4j: {e}")
        print(f"Check that Neo4j is running at {NEO4J_URI}")
        return
    
    # Generate run ID
    run_id = f"bian-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Load
    create_constraints()
    if load_hierarchy(run_id):
        verify_import()
    
    print("\n" + "=" * 60)
    print(f"Hierarchy loaded successfully! (run_id: {run_id})")
    print("Next: Run 02_enrich_domains.py")
    print("=" * 60)
    
    driver.close()


if __name__ == "__main__":
    main()
