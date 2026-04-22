# ADR-004 — Module as Capability: From GMP to General Intelligence Architecture

**Date:** 2026-04-22
**Status:** ACCEPTED
**Deciders:** Project Owner + Matrix Agent
**Related:** ADR-001 (Modular Monolith), ADR-002 (Event Bus), dual-path-strategy.md

---

## Context

The GMP platform is architected as a modular monolith with strict boundary enforcement between
functional modules (QMS, MES, LIMS, Equipment, Training, ENV Monitoring). Each module:

- Has a defined purpose and owns its data exclusively
- Cannot import from other modules (enforced by AST tests)
- Communicates only through the foundation layer
- Has an independent verification lifecycle (tier: SKELETON → FUNCTIONAL → HARDENED → VALIDATED)

The insight in this ADR: **this is not a pharmaceutical architecture. It's a general architecture
for any system where no single component should have unchecked authority.**

Current AI systems are monolithic — one model, one context, one failure mode. The GMP architecture
is the opposite: separation of concerns, distributed verification, and human oversight at defined
boundaries. The question is whether to make this explicit in the design.

---

## Decision

**The module architecture is intentionally dual-purpose.** Every design decision for the GMP
platform also serves as a design decision for a self-governing AI system.

The mapping is exact and will be maintained in `registry.json` as `ai_analogue` fields.
No code changes are required — only naming, documentation, and architectural intent.

---

## Module Mapping

| GMP Module | AI Analogue | Core Function |
|---|---|---|
| **LIMS** | Information Purity Engine | Samples data streams. Verifies provenance. Detects distortion. Quarantines anomalous outputs. Every data point has chain of custody. |
| **MES** | Execution Orchestrator | Manages task sequencing. Step-by-step execution with verification. No step is marked done without evidence. Back-fill prevention = no retroactive falsification. |
| **QMS** | Alignment Guard | Checks outputs against intent. Flags deviation. Manages corrective action loops. Human-approved change control before implementation. |
| **Equipment** | Capability Verification Engine | Tracks whether each tool/agent is within its verified operating envelope. Re-qualification required after drift detected. |
| **Training** | Capability Certification | Ensures sub-components have demonstrated competency before being trusted. Skills expire. Re-certification required. |
| **ENV Monitoring** | Operating Environment Sentinel | Monitors the context in which modules operate. Detects environmental drift that degrades outputs even when modules appear functional. |
| **Foundation: Audit** | Provenance Graph Engine | Every action is immutably logged: who, what, when, original value, new value. Non-repudiable. The backbone of trust. |
| **Foundation: E-Sig** | Non-Repudiation Service | Cryptographically verified commitment. Re-authentication required. Cannot be forged or delegated. |
| **Foundation: Workflow** | State Machine Orchestrator | Defined state transitions. No skipping states. History preserved. |
| **Foundation: Documents** | Versioned Knowledge Base | Version-controlled. Approval-gated. Nothing is deleted — only superseded. |
| **Integration: DeltaV** | Hardcode Interface | Human-defined immutable constraints. Emergency stops. Constitutional boundaries. Read-only from the system's perspective — never overridden by module logic. |

---

## Why LIMS is the Highest-Priority Module for Path B

The Information Purity Engine is the foundational trust layer. Without verified information
provenance, every other module operates on potentially corrupted inputs:

- The Alignment Guard (QMS) cannot detect deviation if the reference data is manipulated
- The Execution Orchestrator (MES) cannot verify completion if execution records can be falsified
- The Provenance Graph (Audit) is meaningless if the events being logged are themselves distorted

**LIMS must be built first and hardened before any other module can be trusted.**

This is consistent with Path A: LIMS is also the module that directly governs product quality
decisions in GMP — a failed batch released because of a falsified test result is the highest
regulatory risk scenario.

---

## What "Information Purity" Means Operationally

A data point is considered **pure** if it satisfies all of the following:

1. **Provenance verified** — the source is a known, trusted, and currently-qualified input
2. **Chain of custody intact** — every transformation is logged, attributed, and timestamped
3. **Original preserved** — the raw input exists alongside any derived/transformed version
4. **Correction is transparent** — if the data was corrected, the original is not deleted; the
   correction references it explicitly (append-only correction model)
5. **Anomaly detection passed** — the value is within the specification for this data type at
   this context (OOS check)
6. **Timing is contemporaneous** — the record timestamp was set by the server at the moment of
   capture, not retrospectively

A data point **fails purity** if any of the above conditions cannot be verified. Failed results
are quarantined (OOSInvestigation created) rather than silently passed through.

---

## What "Hardcode Interface" Means (DeltaV / Constitutional Layer)

The hardcode layer is not a module — it's a constraint system. It defines what **cannot** be
changed by any other module regardless of what the optimization process would suggest.

Three tiers (from `docs/architecture/information-purity-spec.md`):

| Tier | Definition | Who Can Change | Review Frequency |
|---|---|---|---|
| Constitutional | Safety, ethics, core boundaries | Human review only, explicit process | Quarterly |
| Operational | Performance thresholds, resource limits | Human default; AI may propose, never implement | Monthly |
| Tactical | Routing logic, prioritization weights | AI autonomous, fully logged | Retroactive review |

In the current build, the Constitutional layer is implemented as:
- `.cursorrules` §14.4 — what Cursor must never do autonomously
- BUILDING_RULES.md §14 — escalation conditions that halt autonomous operation
- `core/boundary_engine` — AST-enforced structural constraints

These are protected: any change requires a human-reviewed commit. This is the technical
implementation of "constitutional law changeable only through deliberate human process."

---

## The Five Hard Problems (Unsolved — tracked, not ignored)

These are known open problems in this architecture. They are documented here so they are not
forgotten and so future design decisions can be evaluated against them.

| Problem | Why It's Hard | Current Mitigation |
|---|---|---|
| Module verification of other modules | Who checks the checker? Infinite regress. | Cryptographic audit trail + human spot-check (same as GMP validation). Regress stops at human. |
| Distortion detection in information | "Pure" vs "manipulated" is context-dependent. | Operational definition in `docs/architecture/information-purity-spec.md`. OOS framework is the mechanism. Acknowledged as partially solved. |
| Autonomous goal evolution | Self-modifying modules cause alignment drift. | Constitutional layer is immutable. Tactical autonomy is logged. Self-modification requires human approval (§14.4 of BUILDING_RULES). |
| Human review bottleneck | System evolves faster than human review cycles. | 3-day audit loop + BLOCKED status = forced human checkpoint. Accepted constraint for now. |
| Emergent coordination failures | Modules individually safe, collectively unstable. | Chaos suite tests collective failure scenarios. TASK-017 (real-app chaos) will extend this. |

---

## Consequences

### What this changes
- `registry.json` — every module now has `ai_analogue` and `ai_analogue_function` fields
- `docs/architecture/information-purity-spec.md` — operational definition of information purity
- `TASK_QUEUE.md` — TASK-032 (Constitutional layer formalization) added

### What this does NOT change
- The build sprint — P0/P1 GMP tasks remain the priority
- The code — no module renames, no structural changes
- The validation path — Path A (GMP) remains the primary revenue path

### Risk
- If the dual-purpose framing confuses Cursor during autonomous sessions, it may build
  AI-governance features instead of GMP features. Mitigation: BUILDING_RULES.md explicitly
  states the build is GMP-first. AI analogue names are documentation only.

---

*Decided by: Project Owner + Matrix Agent*
*Date: 2026-04-22*
*Next review: at first external stakeholder conversation (Path A or Path B)*
