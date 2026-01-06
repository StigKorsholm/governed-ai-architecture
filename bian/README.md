# BIAN Reference Data

Load the complete BIAN (Banking Industry Architecture Network) Service Landscape v13 into Neo4j.

## Quick Start

```bash
# 1. Get BIAN API specs
cd api
git clone https://github.com/bian-official/public.git

# 2. Load into Neo4j
cd ../loader
pip install -r requirements.txt
# Edit scripts to set Neo4j password and paths
python 00_clear_database.py
python 01_load_hierarchy.py
python 02_enrich_domains.py
python 03_load_yaml.py
```

## What Gets Loaded

| Node Type | Count |
|-----------|-------|
| Business Areas | 5 |
| Business Domains | 38 |
| Service Domains | 327 |
| Control Records | ~246 |
| Behavior Qualifiers | ~692 |
| Operations | ~4,300 |
| Schemas | ~15,600 |

## Related ADRs

- [ADR-013: BIAN as Reference Model](../docs/decisions/ADR-013.md)
