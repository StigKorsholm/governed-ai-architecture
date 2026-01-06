# ADR-000: Validator-Gated AI-Assisted Modernization Pipeline

> **Status:** ✅ Accepted  
> **Date:** 2025-12-22  
> **Triggered By:** —  
> **Triggers:** ADR-001, ADR-006, ADR-008

---

## Summary

* **Decision:** All AI-generated outputs in the modernization pipeline must pass through deterministic validators before being accepted as truth, with explicit human checkpoints for high-risk decisions.
* **Chosen approach:** Validator-gated, checkpoint-controlled, graph-authoritative architecture.
* **Why:** AI outputs are probabilistic; production systems require determinism; trust must be engineered, not asserted.
* **Scope:** This is the epic ADR. It establishes the philosophical and architectural foundation for all other decisions.

---

## Context

Banking system modernization—particularly migrating legacy COBOL/DB2 systems to modern architectures—is high-stakes work where errors have material consequences.

AI assistance promises acceleration: extracting capabilities from schemas, mapping to reference models, designing bounded contexts, generating migration plans.

But AI outputs are inherently probabilistic:
- Models hallucinate plausible-sounding nonsense
- Confidence scores don't correlate reliably with correctness
- "Pretty but wrong" is indistinguishable from "pretty and right"

The failure mode is not that AI gets things wrong sometimes.

The failure mode is that **we can't tell when it's wrong**.

In regulated environments, this is unacceptable:
- Audit boards require defensible positions
- Risk committees require traceable decisions
- Delivery teams require reliable foundations

This ADR establishes the architectural response to that fundamental constraint.

---

## Decision Drivers

1. **Probabilistic outputs require deterministic gates** — We cannot rely on AI self-reported confidence
2. **Traceability is non-negotiable** — Every claim must be traceable to source and validation
3. **Human judgment cannot be automated away** — Some decisions require explicit human accountability
4. **Reproducibility enables trust** — Same inputs must produce same outputs
5. **Learning must be governed** — System improvement cannot corrupt past decisions
6. **Fail-fast is cheaper than fail-late** — Catch errors early, not at production

---

## Considered Options

### Option 1 — LLM-First: Trust AI outputs, review at end

**Description:** Let AI generate outputs freely; humans review final deliverables.

**Pros:**
- Maximum speed
- Minimum friction
- Easy to implement

**Cons:**
- Errors compound silently
- Review doesn't scale
- "Pretty but wrong" passes undetected
- Audit trail is "someone looked at it"

### Option 2 — Rules-Only: No AI, pure automation

**Description:** Use only deterministic transformations; no AI in the pipeline.

**Pros:**
- Fully reproducible
- No hallucination risk
- Easy to audit

**Cons:**
- Cannot handle semantic tasks (capability extraction, domain mapping)
- Requires exhaustive rule definition
- Loses the value proposition of AI assistance

### Option 3 — Validator-Gated: AI proposes, validators verify ✅ **Chosen**

**Description:** AI generates proposals that must pass deterministic validation before being accepted. Human checkpoints gate high-risk phases.

**Pros:**
- Leverages AI capability for semantic tasks
- Maintains deterministic guarantees for correctness
- Enables audit and traceability
- Allows system improvement over time

**Cons:**
- More engineering complexity
- Slower than pure AI
- Requires explicit validator design
- Human checkpoints add process overhead

---

## Decision

We will implement a **validator-gated, checkpoint-controlled, graph-authoritative architecture** with these principles:

### 1. AI outputs are proposals, not truth

Every LLM-generated output enters the system as a **proposal**. Proposals have no authority until validated.

### 2. Truth lives in the graph

Neo4j is the system of record for modernization knowledge. If it's not in the graph, it's not true. The graph is queryable, versionable, and auditable.

### 3. Validators are first-class architecture

Validators are not safety nets added at the end. They are **core architecture components** with explicit contracts, versioning, and tests.

### 4. Human checkpoints are architectural control points

Some decisions require human judgment and accountability. Checkpoints are not exceptions to automation—they are **designed control points** where humans must explicitly approve progression.

### 5. Confidence is derived from validation, not self-reporting

Confidence scores come from validator pass rates, evidence quality, and structural signals—not from LLM self-reported confidence.

### 6. Fail-fast at every gate

If validation fails, the pipeline stops. Errors do not propagate. This is a feature, not a limitation.

---

## Decision Rationale

This architecture is chosen because it addresses the fundamental constraint:

> AI outputs cannot be trusted without enforcement.

The validator-gated pattern:
- **Preserves AI value** — Semantic tasks (extraction, mapping) use AI capability
- **Maintains determinism** — Validation is deterministic; same input → same decision
- **Enables audit** — Every output has traceable validation evidence
- **Allows improvement** — Learning from corrections is governed, not ad-hoc

The alternative approaches fail:
- LLM-First accumulates errors silently
- Rules-Only cannot perform semantic tasks

Validator-gated is the pragmatic middle path.

---

## Consequences

### Architectural Implications

| Consequence | Triggers ADR |
|-------------|--------------|
| We need a canonical representation of modernization knowledge | ADR-001 |
| AI outputs cannot be trusted without enforcement | ADR-006 |
| Some decisions cannot be safely automated | ADR-008 |

### Positive Consequences

- Higher trust in AI-assisted outputs
- Deterministic validation despite probabilistic generation
- Auditable decision trail
- Reproducible runs
- Scalable human oversight (focused on flagged items)

### Negative Consequences

- More engineering work upfront
- Slower than pure AI generation
- Requires validator design discipline
- Human checkpoints add process time

---

## Notes / Out of Scope

- Specific validator implementations are not specified here
- Technology choices (Neo4j, PostgreSQL, n8n) are captured in subsequent ADRs
- This ADR establishes philosophy; implementation details follow

---

## References

- **LinkedIn Article:** [Designing Target Architecture with AI — An ADR-Driven Approach](https://www.linkedin.com/pulse/designing-target-architecture-ai-adr-driven-approach-korsholm-3yvxe) (2025-12-22)
- **LinkedIn Article:** [Why Trustworthy AI Is an Architecture Problem, Not a Model Problem](https://www.linkedin.com/pulse/why-trustworthy-ai-architecture-problem-model-stig-pedersen-korsholm-wmlje) (2026-01-01)
