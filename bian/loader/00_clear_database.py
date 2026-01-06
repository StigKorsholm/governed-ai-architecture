"""
00_clear_database.py

Clears Neo4j database with options:
  1. Delete ALL data (entire database)
  2. Delete only BIAN-related nodes (keeps other data)
  3. Delete specific import run (by _run_id)

Run: python 00_clear_database.py

Prerequisites:
  pip install neo4j
"""

from datetime import datetime
from neo4j import GraphDatabase

# ============================================
# CONFIGURATION - UPDATE THESE!
# ============================================

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"  # ← Change this!

# BIAN node labels (used for selective deletion)
BIAN_LABELS = [
    "BusinessArea",
    "BusinessDomain", 
    "BIANServiceDomain",
    "BIANControlRecord",
    "BIANBehaviorQualifier",
    "BIANOperation",
    "BIANSchema",
]

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
# SHOW STATS
# ============================================

def show_current_stats():
    """Show what's currently in the database."""
    print("\n" + "-" * 40)
    print("Current database contents:")
    print("-" * 40)
    
    result = run_cypher("""
        MATCH (n)
        RETURN labels(n)[0] AS label, count(*) AS count
        ORDER BY count DESC
    """)
    
    total_nodes = 0
    bian_nodes = 0
    other_nodes = 0
    
    if result:
        for row in result:
            label = row['label']
            count = row['count']
            total_nodes += count
            
            is_bian = label in BIAN_LABELS
            marker = "  [BIAN]" if is_bian else ""
            print(f"  {label}: {count}{marker}")
            
            if is_bian:
                bian_nodes += count
            else:
                other_nodes += count
    else:
        print("  (empty)")
    
    result = run_cypher("""
        MATCH ()-[r]->()
        RETURN type(r) AS type, count(*) AS count
        ORDER BY count DESC
    """)
    
    if result:
        print("\nRelationships:")
        for row in result:
            print(f"  {row['type']}: {row['count']}")
    
    print(f"\nSummary: {total_nodes} total nodes ({bian_nodes} BIAN, {other_nodes} other)")
    
    return {"total": total_nodes, "bian": bian_nodes, "other": other_nodes}


def show_import_runs():
    """Show existing import runs."""
    print("\n" + "-" * 40)
    print("Import runs (by _run_id):")
    print("-" * 40)
    
    result = run_cypher("""
        MATCH (n)
        WHERE n._run_id IS NOT NULL
        RETURN DISTINCT n._run_id AS run_id, 
               count(*) AS nodes,
               min(n._imported_at) AS imported_at
        ORDER BY imported_at DESC
        LIMIT 10
    """)
    
    if result:
        for row in result:
            print(f"  {row['run_id']}: {row['nodes']} nodes ({row['imported_at']})")
        return [r['run_id'] for r in result]
    else:
        print("  (no import runs found)")
        return []


# ============================================
# DELETE FUNCTIONS
# ============================================

def delete_all():
    """Delete ALL nodes and relationships."""
    print("\n⚠️  Deleting ALL data...")
    
    batch_size = 10000
    total_deleted = 0
    
    while True:
        result = run_cypher(f"""
            MATCH (n)
            WITH n LIMIT {batch_size}
            DETACH DELETE n
            RETURN count(*) AS deleted
        """)
        
        deleted = result[0]["deleted"] if result else 0
        total_deleted += deleted
        
        if deleted == 0:
            break
        
        print(f"  Deleted {total_deleted} nodes...")
    
    print(f"✅ All data deleted. Total: {total_deleted} nodes")


def delete_bian_only():
    """Delete only BIAN-related nodes."""
    print("\n⚠️  Deleting BIAN data only...")
    
    total_deleted = 0
    
    for label in BIAN_LABELS:
        result = run_cypher(f"""
            MATCH (n:{label})
            WITH n
            DETACH DELETE n
            RETURN count(*) AS deleted
        """)
        
        deleted = result[0]["deleted"] if result else 0
        total_deleted += deleted
        
        if deleted > 0:
            print(f"  Deleted {deleted} {label} nodes")
    
    print(f"✅ BIAN data deleted. Total: {total_deleted} nodes")


def delete_by_run_id(run_id: str):
    """Delete all nodes from a specific import run."""
    print(f"\n⚠️  Deleting data from run: {run_id}...")
    
    result = run_cypher("""
        MATCH (n {_run_id: $run_id})
        WITH n
        DETACH DELETE n
        RETURN count(*) AS deleted
    """, {"run_id": run_id})
    
    deleted = result[0]["deleted"] if result else 0
    print(f"✅ Deleted {deleted} nodes from run '{run_id}'")


# ============================================
# CREATE CONSTRAINTS
# ============================================

def create_constraints():
    """Create uniqueness constraints for all node types."""
    print("\nCreating constraints...")
    
    constraints = [
        # Hierarchy
        ("BusinessArea", "name"),
        ("BusinessDomain", "name"),
        ("BIANServiceDomain", "object_id"),
        # YAML entities
        ("BIANControlRecord", "id"),
        ("BIANBehaviorQualifier", "id"),
        ("BIANOperation", "id"),
        ("BIANSchema", "id"),
    ]
    
    for label, prop in constraints:
        try:
            run_cypher(f"""
                CREATE CONSTRAINT IF NOT EXISTS 
                FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE
            """)
            print(f"  ✅ {label}.{prop}")
        except Exception as e:
            print(f"  ⚠️  {label}.{prop}: {e}")
    
    print("Constraints created.")


# ============================================
# MAIN
# ============================================

def main():
    print("=" * 60)
    print("BIAN Neo4j Database Manager")
    print("=" * 60)
    
    try:
        connect()
        run_cypher("RETURN 1")
        print("Connected to Neo4j.")
    except Exception as e:
        print(f"ERROR: Cannot connect to Neo4j: {e}")
        print(f"Check that Neo4j is running at {NEO4J_URI}")
        return
    
    # Show current state
    stats = show_current_stats()
    run_ids = show_import_runs()
    
    # Menu
    print("\n" + "=" * 60)
    print("Options:")
    print("=" * 60)
    print("  1. Delete ALL data (entire database)")
    print("  2. Delete BIAN data only (keeps other nodes)")
    if run_ids:
        print("  3. Delete specific import run (by _run_id)")
    print("  4. Create constraints only (no deletion)")
    print("  0. Cancel")
    
    choice = input("\nSelect option (0-4): ").strip()
    
    if choice == "0":
        print("Cancelled.")
        driver.close()
        return
    
    elif choice == "1":
        print("\n" + "!" * 60)
        print("⚠️  WARNING: This will DELETE ALL DATA in the database!")
        print("   This includes non-BIAN data (Legacy tables, Capabilities, etc.)")
        print("!" * 60)
        confirm = input("\nType 'DELETE ALL' to confirm: ")
        if confirm == "DELETE ALL":
            delete_all()
            create_constraints()
        else:
            print("Aborted.")
    
    elif choice == "2":
        print("\n" + "-" * 60)
        print("This will delete only BIAN-related nodes:")
        for label in BIAN_LABELS:
            print(f"  - {label}")
        print("\nOther data (Legacy tables, Capabilities, etc.) will be kept.")
        print("-" * 60)
        confirm = input("\nType 'YES' to confirm: ")
        if confirm == "YES":
            delete_bian_only()
            create_constraints()
        else:
            print("Aborted.")
    
    elif choice == "3" and run_ids:
        print("\nAvailable run IDs:")
        for rid in run_ids:
            print(f"  - {rid}")
        run_id = input("\nEnter _run_id to delete: ").strip()
        if run_id in run_ids:
            confirm = input(f"Delete all nodes from '{run_id}'? (YES/no): ")
            if confirm == "YES":
                delete_by_run_id(run_id)
            else:
                print("Aborted.")
        else:
            print(f"Run ID '{run_id}' not found.")
    
    elif choice == "4":
        create_constraints()
    
    else:
        print("Invalid option.")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)
    
    driver.close()


if __name__ == "__main__":
    main()
