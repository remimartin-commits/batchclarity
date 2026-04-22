# ADR 003 — Dual-Path Strategy: GMP Platform + AI Governance Framework

**Date:** 2026-04-23
**Status:** ACCEPTED
**Deciders:** Matrix Agent + Project Owner
**Supersedes:** N/A
**Related:** ADR 001 (Architecture Boundaries), ADR 002 (Module Tier System)

---

## Context

The GMP compliance platform has a long sales cycle (6-18 months). Pharmaceutical companies
require formal validation, procurement review, IT security sign-off, and regulatory approval
before adopting any new GMP system. This is structural — it cannot be shortened.

The same codebase contains a framework that is entirely domain-agnostic:
- CI-enforced module boundaries (AST parsing)
- Deterministic chaos testing suite
- 3-day automated audit loop
- Task queue orchestration with priority and dependency tracking
- Module tier registry with advancement requirements
- Master specification document (BUILDING_RULES.md)

This framework is the missing governance layer for autonomous AI coding agents. The AI coding
tools market (Cursor, Copilot, Devin, etc.) moves on a 2-6 week sales cycle — an order of
magnitude faster than pharma.

The question: **do we pick one path, or keep both warm?**

---

## Decision

**Keep both paths warm. The build does not change. Only the narrative and structure adapt.**

Specifically:
1. Maintain two README files: `README-GMP.md` (regulatory focus) + `README-AI.md` (AI governance focus)
2. Extract the framework layer into a named `core/` directory (TASK-019 — background, non-blocking)
3. Test both narratives in the market (LinkedIn posts, conversations) to get signal
4. Let market response determine which path to double down on
5. If GMP path gains traction first: accelerate module tier advancement toward VALIDATED
6. If AI governance path gains traction first: accelerate `core/` extraction and open-source it

---

## Rationale

### Why not pick one path?

The GMP path requires real customers to go through a 6-18 month adoption cycle. We cannot
know within the next 90 days whether it will succeed. Abandoning the AI governance angle
during that wait period is an unnecessary opportunity cost.

### Why not fully pursue both simultaneously?

The build itself doesn't change. There is no meaningful cost to maintaining both narratives —
only the README files differ. TASK-019 (core extraction) is explicitly tagged P3 and
non-blocking — it doesn't compete with the GMP sprint.

### Why does the same codebase serve both paths?

Because the framework assets (boundary enforcement, chaos testing, audit loop, task queue,
tier registry) are inherently domain-agnostic. The GMP compliance use case is the proving
ground — it's the hardest test the framework could face. Passing it demonstrates the framework
works under regulatory requirements, which is the strongest possible proof for any domain.

### The AI Governance Framing

The current generation of AI coding tools lack:
1. Verifiable output (how do you know the AI built what you think it built?)
2. Long-term continuity (each session loses context)
3. Technical debt detection (AI doesn't test failure paths)
4. Advancement verification (AI declares victory prematurely)
5. Human-in-the-loop checkpoints (no structured escalation mechanism)

This codebase solves all five. That's the AI governance product.

---

## Consequences

### Positive
- Reduces risk of single-path failure (long GMP sales cycle)
- Opens a faster-moving market as a parallel opportunity
- Forces the framework layer to be clean enough to extract — which is good engineering anyway
- Both narratives reinforce each other (GMP = hardest possible proving ground for the framework)

### Negative / Risks
- Maintaining two READMEs creates a documentation sync burden (low — they describe different angles)
- TASK-019 (core extraction) could temporarily disrupt imports if done carelessly (mitigated: constraint is no GMP files moved)
- Market messaging could be confusing if both narratives are presented simultaneously to the same audience (mitigated: target different audiences)

### Neutral
- The build sprint is unchanged — P0/P1 GMP tasks remain the priority
- The 3-day audit loop covers both paths (same codebase, same health signal)

---

## Trigger Conditions for Doubling Down

### Signal: GMP path is working
- At least one QA Manager or VP Quality has seen a demo and expressed purchase intent
- OR: A validation engagement (IQ/OQ work) has been scoped or contracted
- **Action:** Prioritise module tier advancement. Add URS/IQ/OQ tasks to queue. Bring forward TASK-012, TASK-013.

### Signal: AI governance path is working
- At least 50 LinkedIn engagement responses on AI governance angle (not GMP angle)
- OR: A CTO / VP Engineering has asked for a demo or trial access
- **Action:** Accelerate TASK-019 (core extraction). Create landing page for AI governance product. Consider open-sourcing `core/`.

### Signal: Neither is working after 90 days
- No meaningful engagement on either narrative
- **Action:** Revisit with Matrix Agent. Do not pivot the build without a full review session.

---

## Implementation

| Item | File | Status |
|---|---|---|
| GMP narrative | README-GMP.md | DONE |
| AI governance narrative | README-AI.md | DONE |
| Core extraction task | TASK_QUEUE.md (TASK-019) | QUEUED |
| Framework extraction | core/ directory | PENDING (TASK-019) |

---

## Review

This decision is reviewed as part of every 3-day audit cycle.
Health of both paths is assessed by Matrix Agent at each review.

*Decided by: Matrix Agent*
*Next review: 2026-04-26*
