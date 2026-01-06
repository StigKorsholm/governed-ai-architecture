# Governed AI Architecture

This repository documents a **decision-first reference architecture** for building AI-assisted systems that are **safe enough to act on** in regulated environments.

The focus is not on models, prompts, or benchmarks.

It is on the **architectural decisions** required to make AI outputs:
- auditable,
- reproducible,
- governable,
- and resilient to probabilistic failure.

This work is developed **in the open**. Decisions evolve, but they do so explicitly and traceably.

---

## What this repository is

- A reference architecture for **governed AI systems**
- A concrete exploration of **trust engineering**
- A curated system of **Architecture Decision Records (ADRs)**

The architecture assumes:
- AI outputs are probabilistic,
- production systems require determinism,
- and trust must be engineered, not asserted.

---

## What this repository is not

- Not a framework
- Not a product
- Not a demo
- Not optimized for quick wins

There is no "run this to get magic."

---

## Architecture at a glance

> LLMs produce proposals.  
> Truth lives in the graph.  
> Everything progresses through deterministic validation and auditable human checkpoints.

```mermaid
flowchart LR

%% =========================
%% Actors
%% =========================
SME["Human Reviewers<br/>(SME / Architect / Risk)"]:::actor

%% =========================
%% Orchestration
%% =========================
N8N["Orchestrator<br/>n8n workflows<br/><i>control flow only</i>"]:::control

%% =========================
%% Deterministic gates
%% =========================
VAL["Deterministic Validators<br/>Schema + Invariants + Domain Rules<br/><b>FAIL / STOP / WARN</b>"]:::gate
CP["Human Checkpoints (CP-1..CP-4)<br/>Maker–Checker at CP-3<br/><i>explicit approvals</i>"]:::gate

%% =========================
%% Authority-bound data stores
%% =========================
GRAPH["Neo4j Knowledge Graph<br/><b>System of Record</b><br/>tables • capabilities • mappings<br/>bounded contexts • waves • risks"]:::truth
PG["PostgreSQL<br/><b>Audit & Governance Store</b><br/>run manifests • approvals • overrides<br/>errors • translations • prompt issues"]:::audit
OBJ["Artifact Store (FS / Object Storage)<br/><b>Immutable run artifacts</b><br/>reports • diagrams • OpenAPI<br/>SQL scripts • reconciliation packs"]:::artifact

%% =========================
%% LLM (proposal generator)
%% =========================
LLM["LLM (local/on-prem default)<br/><b>Generates proposals</b><br/><i>never authoritative</i>"]:::llm

%% =========================
%% Flows
%% =========================
N8N -->|invoke| LLM
LLM -->|proposals| VAL
VAL -->|validated updates| GRAPH
VAL -->|evidence & outputs| OBJ
VAL -->|audit signals| PG
VAL -->|STOP| CP
CP -->|approve / override / reject| PG
CP -->|resume| N8N
GRAPH -->|deterministic queries| OBJ
OBJ -->|review| SME

%% =========================
%% Styling
%% =========================
classDef actor fill:#ffffff,stroke:#6e7781,stroke-width:1px;
classDef control fill:#eef6ff,stroke:#0969da,stroke-width:1px;
classDef gate fill:#fff8c5,stroke:#9a6700,stroke-width:1px;
classDef truth fill:#f6ffed,stroke:#1a7f37,stroke-width:1px;
classDef audit fill:#fff0f6,stroke:#bf3989,stroke-width:1px;
classDef artifact fill:#f5f0ff,stroke:#8250df,stroke-width:1px;
classDef llm fill:#f6f8fa,stroke:#24292f,stroke-width:1px;

class SME actor;
class N8N control;
class VAL,CP gate;
class GRAPH truth;
class PG audit;
class OBJ artifact;
class LLM llm;

linkStyle default stroke-width:1px,opacity:0.65;
```

See [`docs/diagrams/authority-boundaries.mmd`](./docs/diagrams/authority-boundaries.mmd)

---

## How to read this repository

1. Start with the **architecture decisions**  
   → [`docs/decisions/`](./docs/decisions/)

2. Read **ADR-000** to understand scope and stance.

3. Skim other ADRs by concern (trust, execution, governance, learning).

4. Treat all code as **supporting artifacts**, not sources of truth.

---

## Status

This is a **work in progress**.

Architectural principles are stable.  
Decisions may be refined or superseded.  
Nothing changes silently.

---

## Context

This work is accompanied by a public article series exploring the reasoning behind these decisions:

- [Designing Target Architecture with AI — An ADR-Driven Approach](https://www.linkedin.com/pulse/designing-target-architecture-ai-adr-driven-approach-korsholm-3yvxe)
- [Why Trustworthy AI Is an Architecture Problem, Not a Model Problem](https://www.linkedin.com/pulse/why-trustworthy-ai-architecture-problem-model-stig-pedersen-korsholm-wmlje)
- [Why the Knowledge Model Must Be a Graph (and What Breaks When It Isn't)](https://www.linkedin.com/pulse/why-knowledge-model-must-graph-what-breaks-when-isnt-korsholm-6zzte)

---

## Author

**Stig Pedersen Korsholm**  
Lead Domain Architect  
[LinkedIn](https://www.linkedin.com/in/stigkorsholm)
