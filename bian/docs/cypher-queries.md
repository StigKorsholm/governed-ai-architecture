# Useful Cypher Queries

## Basic Stats

### Count all node types
```cypher
MATCH (n)
RETURN labels(n)[0] AS label, count(*) AS count
ORDER BY count DESC
```

### Full hierarchy stats
```cypher
MATCH (ba:BusinessArea)
OPTIONAL MATCH (ba)-[:HAS_DOMAIN]->(bd:BusinessDomain)
OPTIONAL MATCH (bd)-[:HAS_SERVICE]->(sd:BIANServiceDomain)
OPTIONAL MATCH (sd)-[:HAS_CR]->(cr)
OPTIONAL MATCH (sd)-[:HAS_BQ]->(bq)
OPTIONAL MATCH (sd)-[:HAS_OPERATION]->(op)
RETURN count(DISTINCT ba) AS business_areas,
       count(DISTINCT bd) AS business_domains,
       count(DISTINCT sd) AS service_domains,
       count(DISTINCT cr) AS control_records,
       count(DISTINCT bq) AS behavior_qualifiers,
       count(DISTINCT op) AS operations
```

## Exploring the Hierarchy

### List all Business Areas and their Domains
```cypher
MATCH (ba:BusinessArea)-[:HAS_DOMAIN]->(bd:BusinessDomain)
RETURN ba.name AS business_area, collect(bd.name) AS business_domains
ORDER BY ba.name
```

### Find Service Domains in a Business Domain
```cypher
MATCH (bd:BusinessDomain {name: "Payments"})-[:HAS_SERVICE]->(sd:BIANServiceDomain)
RETURN sd.name, sd.functional_pattern, sd.role
ORDER BY sd.name
```

## Functional Patterns

### Count by functional pattern
```cypher
MATCH (sd:BIANServiceDomain)
WHERE sd.functional_pattern IS NOT NULL
RETURN sd.functional_pattern AS pattern, count(*) AS count
ORDER BY count DESC
```

### Find all "Fulfill" pattern domains
```cypher
MATCH (sd:BIANServiceDomain {functional_pattern: "Fulfill"})
RETURN sd.name, sd.role
ORDER BY sd.name
```

## Service Domain Relationships

### Find what a Service Domain triggers
```cypher
MATCH (sd:BIANServiceDomain {name: "Payment Order"})-[:TRIGGERS]->(target)
RETURN target.name AS triggers
```

### Find what triggers a Service Domain
```cypher
MATCH (source)-[:TRIGGERS]->(sd:BIANServiceDomain {name: "Financial Accounting"})
RETURN source.name AS triggered_by
```

### Most connected Service Domains
```cypher
MATCH (sd:BIANServiceDomain)
OPTIONAL MATCH (sd)-[:TRIGGERS]->(out)
OPTIONAL MATCH (in)-[:TRIGGERS]->(sd)
WITH sd, count(DISTINCT out) AS outgoing, count(DISTINCT in) AS incoming
RETURN sd.name, outgoing, incoming, outgoing + incoming AS total
ORDER BY total DESC
LIMIT 20
```

## Control Records and Behavior Qualifiers

### Service Domain with all its CRs and BQs
```cypher
MATCH (sd:BIANServiceDomain {name: "Current Account"})
OPTIONAL MATCH (sd)-[:HAS_CR]->(cr)
OPTIONAL MATCH (sd)-[:HAS_BQ]->(bq)
RETURN sd.name,
       cr.name AS control_record,
       collect(DISTINCT bq.name) AS behavior_qualifiers
```

### BQs with most operations
```cypher
MATCH (bq:BIANBehaviorQualifier)<-[:FOR_BQ]-(op:BIANOperation)
RETURN bq.name, count(op) AS operation_count
ORDER BY operation_count DESC
LIMIT 20
```

## Operations

### Find all operations for a Service Domain
```cypher
MATCH (sd:BIANServiceDomain {name: "Payment Order"})-[:HAS_OPERATION]->(op)
RETURN op.name, op.action_term, op.http_method, op.path
ORDER BY op.action_term, op.name
```

### Count operations by action term
```cypher
MATCH (op:BIANOperation)
RETURN op.action_term, count(*) AS count
ORDER BY count DESC
```

### Find all Execute operations
```cypher
MATCH (sd:BIANServiceDomain)-[:HAS_OPERATION]->(op:BIANOperation {action_term: "Execute"})
RETURN sd.name AS service_domain, op.name AS operation
ORDER BY sd.name
```

## Path Finding

### Find path between two Service Domains
```cypher
MATCH path = shortestPath(
  (a:BIANServiceDomain {name: "Customer Offer"})-[:TRIGGERS*..5]->(b:BIANServiceDomain {name: "Payment Order"})
)
RETURN [n IN nodes(path) | n.name] AS path
```

### Find all paths from Sales to Operations
```cypher
MATCH (ba1:BusinessArea {name: "Sales and Service"})-[:HAS_DOMAIN]->()-[:HAS_SERVICE]->(sd1:BIANServiceDomain)
MATCH (ba2:BusinessArea {name: "Operations and Execution"})-[:HAS_DOMAIN]->()-[:HAS_SERVICE]->(sd2:BIANServiceDomain)
MATCH path = (sd1)-[:TRIGGERS*1..3]->(sd2)
RETURN sd1.name AS from_sd, sd2.name AS to_sd, length(path) AS hops
LIMIT 20
```

## Import Run Management

### List all import runs
```cypher
MATCH (n)
WHERE n._run_id IS NOT NULL
RETURN DISTINCT n._run_id AS run_id, 
       count(*) AS nodes,
       min(n._imported_at) AS imported_at
ORDER BY imported_at DESC
```

### Delete a specific run
```cypher
// Preview what will be deleted
MATCH (n {_run_id: "bian-20250105-143022"})
RETURN labels(n)[0] AS label, count(*) AS count

// Actually delete (uncomment to run)
// MATCH (n {_run_id: "bian-20250105-143022"})
// DETACH DELETE n
```

## Visualization Queries

### Small graph for visualization (50 nodes max)
```cypher
MATCH (ba:BusinessArea)-[:HAS_DOMAIN]->(bd:BusinessDomain)-[:HAS_SERVICE]->(sd:BIANServiceDomain)
WHERE ba.name = "Sales and Service"
OPTIONAL MATCH (sd)-[:TRIGGERS]->(target:BIANServiceDomain)
RETURN ba, bd, sd, target
LIMIT 50
```

### Service Domain with full structure
```cypher
MATCH (sd:BIANServiceDomain {name: "Current Account"})
OPTIONAL MATCH (sd)-[:HAS_CR]->(cr)
OPTIONAL MATCH (sd)-[:HAS_BQ]->(bq)
OPTIONAL MATCH (sd)-[:TRIGGERS]->(target)
RETURN sd, cr, bq, target
```
