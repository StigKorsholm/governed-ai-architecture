# Workflows

This directory will contain n8n workflow exports.

## Status

🔜 **Placeholder — implementation pending**

## Intent

Workflows orchestrate the pipeline phases (see ADR-004).

Each workflow is:
- **Modular** — can be updated independently
- **Stateless** — state lives in external stores
- **Observable** — logging, metrics, error capture
- **Idempotent** — safe to re-run

## Planned Workflows

| Workflow | Description |
|----------|-------------|
| WF-MIP-Main | Main orchestrator |
| WF-Extract-Schema | Schema extraction |
| WF-Derive-Capabilities | Capability derivation |
| WF-Map-BIAN | BIAN mapping |
| WF-Design-BoundedContexts | BC design |
| WF-Design-Microservices | MS design |
| WF-Generate-APIs | API generation |
| WF-Plan-Migration | Migration planning |

## Related ADRs

- [ADR-004: n8n Orchestration](../docs/decisions/ADR-004.md)
- [ADR-005: References Not Payloads](../docs/decisions/ADR-005.md)
