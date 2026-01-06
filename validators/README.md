# Validators

This directory will contain validation code for the governed AI architecture.

## Status

🔜 **Placeholder — implementation pending**

## Intent

Validators are first-class architecture components (see ADR-006).

They are not safety nets added at the end. They are **core product code** with:
- Explicit contracts
- Version control
- Test coverage
- Documentation

## Planned Structure

```
validators/
├── schema/           # JSON Schema validators
├── graph/            # Cypher invariant queries
├── domain/           # Domain-specific rules
└── reconciliation/   # Migration checks
```

## Related ADRs

- [ADR-006: LLM Outputs as Proposals](../docs/decisions/ADR-006.md)
- [ADR-007: Graph Invariants](../docs/decisions/ADR-007.md)
- [ADR-010: Validator-Backed Confidence](../docs/decisions/ADR-010.md)
