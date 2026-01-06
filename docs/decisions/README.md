# Architecture Decision Records

This directory contains the **Architecture Decision Records (ADRs)** that define the governed AI architecture.

These ADRs form a **decision system**, not a linear checklist.

Each decision constrains others. Together, they define how the system behaves under uncertainty, failure, audit, and change.

---

## How to read these ADRs

ADR numbers reflect the **order in which decisions were made**, not the order in which they should be read.

### Recommended reading path

**1. ADR-000 — Epic**

Defines the problem, scope, and architectural stance.

**2. Epistemic decisions — where truth lives**

- ADR-001 Graph as system of record
- ADR-002 Audit & governance store
- ADR-003 Immutable artifacts
- ADR-015 Deterministic diagrams

**3. Trust decisions — preventing corruption**

- ADR-006 LLM outputs as proposals
- ADR-007 Graph invariants as contracts
- ADR-009 STOP conditions
- ADR-010 Validator-backed confidence

**4. Execution decisions**

- ADR-004 Orchestration model
- ADR-005 References, not payloads
- ADR-014 OpenAPI as canonical output

**5. Governance decisions**

- ADR-008 Human checkpoints
- ADR-012 Data classification & audit integrity
- ADR-013 BIAN as reference model

**6. Learning decisions**

- ADR-017 Structured memory
- ADR-018 Prompt versioning & regression tests

---

## ADR Index

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-000](./ADR-000-epic.md) | Validator-Gated AI-Assisted Modernization Pipeline | ✅ Accepted |
| [ADR-001](./ADR-001.md) | Graph as System of Record | ✅ Accepted |
| [ADR-002](./ADR-002.md) | PostgreSQL as Audit/Governance Store | ✅ Accepted |
| [ADR-003](./ADR-003.md) | Artifacts in Filesystem with Run-Scoped Paths | ✅ Accepted |
| [ADR-004](./ADR-004.md) | Orchestrate with n8n Using Modular Workflows | ✅ Accepted |
| [ADR-005](./ADR-005.md) | Pass References Not Payloads | ✅ Accepted |
| [ADR-006](./ADR-006.md) | LLM Outputs as Proposals | ✅ Accepted |
| [ADR-007](./ADR-007.md) | Graph Invariants as Contracts | ✅ Accepted |
| [ADR-008](./ADR-008.md) | Human Checkpoints | ✅ Accepted |
| [ADR-009](./ADR-009.md) | Migration STOP Conditions | ✅ Accepted |
| [ADR-010](./ADR-010.md) | Validator-Backed Confidence | ✅ Accepted |
| [ADR-011](./ADR-011.md) | Local LLM for Production | ✅ Accepted |
| [ADR-012](./ADR-012.md) | Data Classification & Audit Integrity | ✅ Accepted |
| [ADR-013](./ADR-013.md) | BIAN as Reference Model | ✅ Accepted |
| [ADR-014](./ADR-014.md) | OpenAPI as Canonical Output | ✅ Accepted |
| [ADR-015](./ADR-015.md) | Deterministic Diagrams | ✅ Accepted |
| [ADR-016](./ADR-016.md) | Evidence Appendix | ✅ Accepted |
| [ADR-017](./ADR-017.md) | Structured Memory | ✅ Accepted |
| [ADR-018](./ADR-018.md) | Prompt Versioning | ✅ Accepted |

---

## Decision philosophy

These decisions optimize for:
- safety over speed,
- explicitness over convenience,
- reproducibility over cleverness.

Automation without governance is treated as deferred failure.

---

## Decision graph

```
                              ADR-000
                    Validator-Gated AI Pipeline
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            ▼                   ▼                   ▼
        ADR-001             ADR-006             ADR-008
    Graph as SoR        LLM as Proposals     Human Checkpoints
            │                   │                   │
    ┌───────┼───────┐     ┌─────┴─────┐       ┌─────┴─────┐
    │       │       │     │           │       │           │
    ▼       ▼       ▼     ▼           ▼       ▼           ▼
ADR-002 ADR-003 ADR-007  ADR-010   ADR-015  ADR-009   ADR-017
Postgres Files  Invariants Confidence Diagrams STOP    Learning
                                                          │
                                                          ▼
                                                      ADR-018
                                                      Prompts
```
