# GMP Platform — AI Orchestration Framework README

> **Path B — Operating System for Autonomous AI Software Development**
> CI-enforced module boundaries. Deterministic chaos testing. 3-day audit loops.
> Task queue orchestration. Built for AI agents that build production software.

---

## What This Is

The same codebase. A different lens.

Under the hood, this platform is a **domain-agnostic framework for autonomous software
development at scale**. The GMP compliance use case is the proving ground — if the framework
holds under pharmaceutical regulatory requirements (ALCOA+, 21 CFR Part 11, GAMP 5),
it holds under anything.

The framework assets are fully transferable to any domain where autonomous AI coding agents
need to operate safely, verifiably, and without human oversight for extended periods.

---

## The Framework Assets

### 1. CI-Enforced Architecture Boundaries
Boundaries between modules are enforced by AST-parsing CI tests — not by convention.
No pull request can merge if it contains a cross-module import or cross-module foreign key.

```python
# backend/tests/test_architecture_boundaries.py
# Real AST parsing — no grep, no regex shortcuts
# Runs on every commit. Fails the build. Non-negotiable.
```

**Why this matters for AI agents:** LLMs leak coupling. Without hard enforcement,
every feature adds implicit cross-module dependencies that compound into an unmaintainable
ball of mud within 10 sessions. This prevents that entirely.

### 2. Deterministic Chaos Suite
Five reproducible failure scenarios that run weekly and on every major change:

| Scenario | What It Proves |
|---|---|
| DB connection kill mid-transaction | No partial writes escape to application state |
| 10x latency injection | Timeouts are handled, not silently ignored |
| Event bus fill to 10,000 items | Queue backpressure doesn't crash the process |
| Message corruption + dead-letter | Bad messages are quarantined, not re-queued forever |
| Process crash + recovery | Restart returns to last-known-good state |

```bash
python chaos.py  # All 5 pass or the build is broken
```

**Why this matters for AI agents:** LLMs don't test failure paths. They write happy-path code.
The chaos suite forces failure handling to be real, not decorative.

### 3. 3-Day Audit Loop
Every 72 hours, a GitHub Actions workflow generates a machine-readable audit report:

```json
{
  "health": "GREEN | AMBER | RED",
  "git_activity": { "commits_last_3_days": 12 },
  "test_results": { "architecture_tests": "PASS", "full_suite": "PASS" },
  "chaos_results": { "all_scenarios_pass": true },
  "task_queue": { "pending": 8, "blocked": 0, "done": 3 },
  "module_completeness": { "qms": { "tier": "SKELETON", "missing_files": [] } }
}
```

RED health = workflow fails. AMBER = warning annotation. GREEN = proceed.

**Why this matters for AI agents:** Without a structured check-in mechanism, autonomous agents
drift. They complete tasks that don't matter, miss blockers, and accumulate technical debt
silently. The audit loop is the forcing function that keeps the build on track.

### 4. Task Queue Orchestration
A structured, machine-readable backlog (`TASK_QUEUE.md`) that agents consume directly:

```
TASK-018 [P0] — Build NotificationService — DONE
TASK-001 [P0] — Wire notifications into hooks — PENDING (depends on TASK-018)
TASK-002 [P0] — Update status flags — PENDING
```

Rules:
- Priority ordering: P0 > P1 > P2 > P3
- Dependency graph explicit — no implicit ordering
- Status transitions: PENDING → IN_PROGRESS → DONE | BLOCKED
- Agents write start timestamps and completion summaries directly into the file

**Why this matters for AI agents:** LLMs without a task queue re-solve already-solved problems,
start new features while old ones are broken, and have no memory of what changed and why.
The task queue is persistent state across sessions.

### 5. Module Tier Registry
Every module has a verified advancement tier. Nothing self-reports as done if it isn't:

```json
{
  "qms": { "tier": "SKELETON", "last_advanced": null },
  "core/notify": { "tier": "FUNCTIONAL", "last_advanced": "2026-04-21" }
}
```

Tier advancement requires explicit evidence: tests passing, files present, functionality verified.
No tier is changed without meeting the advancement checklist in `BUILDING_RULES.md`.

**Why this matters for AI agents:** LLMs declare victory prematurely. "Done" in an LLM means
"I wrote the code." The tier system makes "done" mean "it works, it's tested, it's validated."

### 6. The BUILDING_RULES.md Specification
A 14-section master positive specification that Cursor reads at the start of every session.
Every decision — DB schema, API design, migration patterns, security, GMP compliance —
is pre-decided in this document. Cursor doesn't improvise on structural decisions.

Sections:
1. Module Lifecycle | 2. DB Design | 3. API Design | 4. Service Layer
5. GMP Compliance | 6. Testing | 7. Migrations | 8. Background Tasks
9. Integration | 10. Performance | 11. Observability | 12. Security
13. Frontend | 14. Autonomous Operation Rules

---

## Why GMP? Because Compliance Is the Hardest Test

A pharmaceutical GMP platform is the adversarial proving ground for this framework:

| GMP Requirement | Framework Feature Tested |
|---|---|
| Immutable audit trail (Part 11) | No partial writes survive chaos scenarios |
| ALCOA+ data integrity | Boundary enforcement prevents data leakage between modules |
| Regulatory change control | All schema changes via Alembic migration —no ad-hoc DDL |
| Validation (GAMP 5) | Module tier system enforces IQ/OQ before VALIDATED tier |
| 21 CFR Part 11 e-signatures | Service layer pattern enforces re-auth before signing |

If the framework handles GMP, it handles fintech, healthcare, legal, defence, or any other
regulated domain.

---

## The AI Governance Angle

This is not just a coding tool. It's an **AI governance system**:

| Governance Need | How This Solves It |
|---|---|
| What did the AI build? | Every commit tagged by task ID; audit report shows git activity |
| Is the AI building the right thing? | Task queue prioritisation by human-set P0/P1/P2/P3 |
| Did the AI break anything? | Chaos suite + architecture tests on every change |
| Is the AI on track? | 3-day audit loop with GREEN/AMBER/RED health signal |
| Can I trust what the AI claims is done? | Module tier system — tier ≠ "AI said it's done" |
| What happens when the AI gets confused? | BLOCKED status + escalation to human reviewer |

**This is the missing layer in current AI coding tools.** Cursor, Copilot, Devin, etc. can
write code. None of them have a built-in governance layer for *verifying that the code is
correct, compliant, and doesn't accumulate hidden technical debt over time.*

---

## Structural Separation (Planned)

The framework is being extracted into a generic `core/` layer:

```
gmp-platform/
├── core/                   ← Domain-agnostic (extractable to any project)
│   ├── boundary_engine/    ← AST boundary enforcement
│   ├── event_bus/          ← Hook registry + async event dispatch
│   ├── task_orchestrator/  ← Task queue reader/writer
│   └── audit_reporter/     ← Structured GREEN/AMBER/RED report generator
├── gmp/                    ← GMP-specific modules
│   └── modules/            ← qms, mes, lims, equipment, training, env_monitoring
└── connectors/             ← Generic API adapters (SAP, DeltaV, LIMS instruments)
```

See TASK-019 in `TASK_QUEUE.md` for extraction timeline.

---

## Market Signal Strategy

Two parallel narratives. Same codebase. Let the market decide:

**Narrative A — GMP Compliance Platform:**
- Target: QA Managers, VP Quality, Compliance Officers at 50-500 person pharma/biotech
- Message: "Replace TrackWise, Syncade, LIMS. One validated system. GAMP 5 Category 5."
- Sales cycle: 6-18 months (validation, procurement, IT security review)

**Narrative B — AI Governance Framework:**
- Target: CTOs, VP Engineering, DevOps leads at tech companies using AI coding tools
- Message: "Your AI coding agent needs a governance layer. Here it is."
- Sales cycle: 2-6 weeks (engineering buy-in, trial, SaaS subscription)

Nothing changes in the build. The narrative and structure adapt to whichever signal is stronger.

---

## Running the Framework

```bash
# Start the API
cd backend && uv run uvicorn app.main:app --reload

# Run architecture boundary enforcement
uv run pytest backend/tests/test_architecture_boundaries.py -v

# Run chaos suite (all 5 scenarios must pass)
uv run python chaos.py

# Generate audit report (GREEN/AMBER/RED)
uv run python scripts/generate_audit_report.py

# Check module tier registry
cat registry.json
```

---

## Start an Autonomous Build Session

Open Cursor. Press Ctrl+I. Paste:

```
Read the following files before doing anything:
- .cursorrules
- BUILDING_RULES.md
- SESSION_STARTER_TEMPLATE.md
- TASK_QUEUE.md
- registry.json

Then start on the highest-priority PENDING task in TASK_QUEUE.md.
Update TASK_QUEUE.md with your start timestamp and status before writing any code.
Run quality gates when done. Update TASK_QUEUE.md and registry.json before finishing.
```

---

*Built by: Matrix Agent (supervision) + Cursor (autonomous coding)*
*Review cycle: Every 3 days via audit/reports/YYYY-MM-DD-audit.json*
*Framework status: Path A (GMP) + Path B (AI governance) — both paths warm*
