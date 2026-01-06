# WF-Load-BIAN: Load BIAN Reference Data into Neo4j

> **Status:** ✅ Complete  
> **Last Updated:** 2025-01-05  
> **Run ID Example:** `bian-20250105-164205`

## Purpose

Load the complete BIAN (Banking Industry Architecture Network) Service Landscape v13 into Neo4j as a reference graph for:
- Mapping legacy systems to BIAN domains
- Generating NFRs based on BIAN patterns
- Designing BIAN-compliant microservices
- Understanding service domain relationships

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  BIAN Website                      BIAN GitHub                          │
│  (Service Landscape)               (bian-official/public)               │
│         │                                  │                            │
│         ▼                                  ▼                            │
│  ┌─────────────┐                  ┌─────────────────┐                   │
│  │bian_scrape.py│                  │ yamls/*.yaml    │                   │
│  └──────┬──────┘                  │ (OpenAPI specs) │                   │
│         │                         └────────┬────────┘                   │
│         ▼                                  │                            │
│  ┌─────────────────────┐                   │                            │
│  │ output/              │                   │                            │
│  │ ├─ index_hierarchy  │                   │                            │
│  │ └─ service_domains/ │                   │                            │
│  └──────────┬──────────┘                   │                            │
│             │                              │                            │
└─────────────┼──────────────────────────────┼────────────────────────────┘
              │                              │
              ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           LOADER SCRIPTS                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────┐                                               │
│  │ 00_clear_database.py │  Optional: Clear/manage existing data         │
│  └──────────┬───────────┘                                               │
│             ▼                                                           │
│  ┌──────────────────────┐                                               │
│  │ 01_load_hierarchy.py │  Creates: BA → BD → SD structure              │
│  │                      │  Input: index_hierarchy.json                  │
│  └──────────┬───────────┘                                               │
│             ▼                                                           │
│  ┌──────────────────────┐                                               │
│  │ 02_enrich_domains.py │  Adds: role, features, patterns, TRIGGERS     │
│  │                      │  Input: service_domains/*.json                │
│  └──────────┬───────────┘                                               │
│             ▼                                                           │
│  ┌──────────────────────┐                                               │
│  │ 03_load_yaml.py      │  Adds: CR, BQ, Operations, Schemas            │
│  │                      │  Input: yamls/*.yaml                          │
│  └──────────┬───────────┘                                               │
│             │                                                           │
└─────────────┼───────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              NEO4J                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  (:BusinessArea)-[:HAS_DOMAIN]->(:BusinessDomain)                       │
│  (:BusinessDomain)-[:HAS_SERVICE]->(:BIANServiceDomain)                 │
│  (:BIANServiceDomain)-[:TRIGGERS]->(:BIANServiceDomain)                 │
│  (:BIANServiceDomain)-[:HAS_CR]->(:BIANControlRecord)                   │
│  (:BIANServiceDomain)-[:HAS_BQ]->(:BIANBehaviorQualifier)               │
│  (:BIANServiceDomain)-[:HAS_OPERATION]->(:BIANOperation)                │
│  (:BIANServiceDomain)-[:HAS_SCHEMA]->(:BIANSchema)                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Scripts

### 00_clear_database.py

**Purpose:** Database management with safe deletion options.

**Options:**
1. Delete ALL data (entire database)
2. Delete BIAN data only (keeps Legacy tables, Capabilities, etc.)
3. Delete specific import run (by `_run_id`)
4. Create constraints only

**Usage:**
```bash
python 00_clear_database.py
# Interactive menu - select option and confirm
```

---

### 01_load_hierarchy.py

**Purpose:** Create the BIAN organizational structure.

**Input:** `scraper/output/index_hierarchy.json`

**Creates:**
```
(:BusinessArea {name, _run_id, _imported_at})
(:BusinessDomain {name, _run_id, _imported_at})
(:BIANServiceDomain {name, object_id, url, _run_id, _imported_at})

(:BusinessArea)-[:HAS_DOMAIN]->(:BusinessDomain)
(:BusinessDomain)-[:HAS_SERVICE]->(:BIANServiceDomain)
```

**Output:**
- 5 Business Areas
- 38 Business Domains
- 327 Service Domains

---

### 02_enrich_domains.py

**Purpose:** Add rich metadata and relationships to Service Domains.

**Input:** `scraper/output/service_domains/*.json` (327 files)

**Updates BIANServiceDomain with:**
| Property | Source | Description |
|----------|--------|-------------|
| `role` | role_definition | What the SD does |
| `example_of_use` | example_of_use | Usage example |
| `executive_summary` | executive_summary | Brief description |
| `key_features` | key_features[] | List of capabilities |
| `functional_pattern` | relations_all.realized_by[0].name | BIAN pattern (Fulfill, Manage, etc.) |

**Creates:**
```
(:BIANServiceDomain)-[:TRIGGERS]->(:BIANServiceDomain)
```

**Output:**
- 238 domains with role definitions
- 86 domains with functional patterns
- ~849 TRIGGERS relationships

**Functional Patterns Found:**
| Pattern | Count |
|---------|-------|
| Fulfill | 13 |
| Process | 13 |
| Manage | 11 |
| Analyze | 10 |
| Administer | 7 |
| Agree Terms | 7 |
| Design | 6 |
| Direct | 5 |
| Track | 5 |
| Monitor | 4 |
| Allocate | 3 |
| Develop | 1 |
| Maintain | 1 |

---

### 03_load_yaml.py

**Purpose:** Load API specifications from BIAN OpenAPI YAML files.

**Input:** `api/public/release13.0.0/semantic-apis/oas3/yamls/*.yaml` (250 files)

**Creates:**
```
(:BIANControlRecord {id, name, _run_id})
(:BIANBehaviorQualifier {id, name, _run_id})
(:BIANOperation {id, name, action_term, summary, http_method, path, _run_id})
(:BIANSchema {id, name, type, _run_id})

(:BIANServiceDomain)-[:HAS_CR]->(:BIANControlRecord)
(:BIANServiceDomain)-[:HAS_BQ]->(:BIANBehaviorQualifier)
(:BIANServiceDomain)-[:HAS_OPERATION]->(:BIANOperation)
(:BIANServiceDomain)-[:HAS_SCHEMA]->(:BIANSchema)
(:BIANOperation)-[:FOR_CR]->(:BIANControlRecord)
(:BIANOperation)-[:FOR_BQ]->(:BIANBehaviorQualifier)
```

**Output:**
- 246 Control Records
- 692 Behavior Qualifiers
- 4,319 Operations
- 15,679 Schemas

**Not Matched:** 1 (Party Reference Data Directory - not in Service Landscape)

---

## Neo4j Schema

### Node Labels

| Label | Count | Key Properties |
|-------|-------|----------------|
| BusinessArea | 5 | name |
| BusinessDomain | 38 | name |
| BIANServiceDomain | 327 | object_id, name, functional_pattern, role |
| BIANControlRecord | 246 | id, name |
| BIANBehaviorQualifier | 692 | id, name |
| BIANOperation | 4,319 | id, name, action_term, http_method |
| BIANSchema | 15,679 | id, name, type |

### Relationships

| Type | From | To | Count |
|------|------|----|----|
| HAS_DOMAIN | BusinessArea | BusinessDomain | 38 |
| HAS_SERVICE | BusinessDomain | BIANServiceDomain | 327 |
| TRIGGERS | BIANServiceDomain | BIANServiceDomain | ~849 |
| HAS_CR | BIANServiceDomain | BIANControlRecord | 246 |
| HAS_BQ | BIANServiceDomain | BIANBehaviorQualifier | 692 |
| HAS_OPERATION | BIANServiceDomain | BIANOperation | 4,319 |
| HAS_SCHEMA | BIANServiceDomain | BIANSchema | 15,679 |
| FOR_CR | BIANOperation | BIANControlRecord | ~1,500 |
| FOR_BQ | BIANOperation | BIANBehaviorQualifier | ~2,800 |

### Constraints

```cypher
CREATE CONSTRAINT FOR (ba:BusinessArea) REQUIRE ba.name IS UNIQUE
CREATE CONSTRAINT FOR (bd:BusinessDomain) REQUIRE bd.name IS UNIQUE
CREATE CONSTRAINT FOR (sd:BIANServiceDomain) REQUIRE sd.object_id IS UNIQUE
CREATE CONSTRAINT FOR (cr:BIANControlRecord) REQUIRE cr.id IS UNIQUE
CREATE CONSTRAINT FOR (bq:BIANBehaviorQualifier) REQUIRE bq.id IS UNIQUE
CREATE CONSTRAINT FOR (op:BIANOperation) REQUIRE op.id IS UNIQUE
CREATE CONSTRAINT FOR (s:BIANSchema) REQUIRE s.id IS UNIQUE
```

---

## Run ID Tracking

Every import assigns a `_run_id` to all created/updated nodes.

**Format:** `bian-YYYYMMDD-HHMMSS`

**Example:** `bian-20250105-164205`

**Query import runs:**
```cypher
MATCH (n)
WHERE n._run_id IS NOT NULL
RETURN DISTINCT n._run_id AS run_id, 
       count(*) AS nodes,
       min(n._imported_at) AS imported_at
ORDER BY imported_at DESC
```

**Delete specific run:**
```cypher
MATCH (n {_run_id: "bian-20250105-164205"})
DETACH DELETE n
```

---

## Verification Queries

### Quick stats
```cypher
MATCH (sd:BIANServiceDomain)
OPTIONAL MATCH (sd)-[:HAS_CR]->(cr)
OPTIONAL MATCH (sd)-[:HAS_BQ]->(bq)
OPTIONAL MATCH (sd)-[:HAS_OPERATION]->(op)
RETURN count(DISTINCT sd) AS domains,
       count(DISTINCT cr) AS crs,
       count(DISTINCT bq) AS bqs,
       count(DISTINCT op) AS ops
```

### Functional patterns
```cypher
MATCH (sd:BIANServiceDomain)
WHERE sd.functional_pattern IS NOT NULL
RETURN sd.functional_pattern AS pattern, count(*) AS count
ORDER BY count DESC
```

### Sample domain with full structure
```cypher
MATCH (ba:BusinessArea)-[:HAS_DOMAIN]->(bd:BusinessDomain)-[:HAS_SERVICE]->(sd:BIANServiceDomain {name: "Current Account"})
OPTIONAL MATCH (sd)-[:HAS_CR]->(cr)
OPTIONAL MATCH (sd)-[:HAS_BQ]->(bq)
RETURN ba.name, bd.name, sd.name, sd.functional_pattern,
       cr.name AS control_record,
       collect(DISTINCT bq.name) AS behavior_qualifiers
```

---

## Dependencies

- Python 3.10+
- neo4j (Python driver)
- pyyaml
- Neo4j 5.x

---

## Related Workflows

| Workflow | Status | Description |
|----------|--------|-------------|
| WF-Load-BIAN | ✅ Complete | This workflow |
| WF-Derive-BQ-NFR | 🔜 Planned | Generate NFRs per Behavior Qualifier |
| WF-Design-Microservices | 🔜 Planned | Group BQs into microservices |

---

## Change Log

| Date | Change |
|------|--------|
| 2025-01-05 | Initial version - all scripts working |
| 2025-01-05 | Fixed functional_pattern extraction (relations_all not relations_service_domains) |
| 2025-01-05 | Added _run_id tracking to all nodes |
| 2025-01-05 | Added delete options (all/BIAN only/by run_id) |
