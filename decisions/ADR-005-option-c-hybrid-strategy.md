# ADR-005 — Option C: Hybrid Strategy (GMP Now, Truth Layer Later)

**Date:** 2026-04-22
**Status:** ACCEPTED
**Deciders:** Project Owner + Matrix Agent
**Related:** ADR-001 (Modular Monolith), ADR-002 (Event Bus), ADR-004 (Module as Capability)
**Evidence:** `C:\workspace\STRATEGIC_ANALYSIS.md` (58,618 bytes, 25 citations, 2026-04-22)

---

## Context

The project reached a formal strategic inflection point on 2026-04-22. Three options were
evaluated in a full decision analysis (Matrix Agent, 4,500 words, 25 cited market sources):

- **Option A — GMP Only:** Complete and ship the GMP compliance platform as a vertical B2B
  SaaS product. TAM ~$3.2B by 2032. Ceiling ~$50M ARR. Narrow but achievable.
- **Option B — Mega AI Pivot:** Immediately pivot to a multi-agent AI platform where GMP
  becomes one domain output. Abandons ~70% of validated architecture. Requires immediate
  significant capital. Competes directly against OpenAI Agents SDK (March 2025), Google ADK
  (April 2025), LangGraph, CrewAI, AutoGen — all better funded.
- **Option C — Hybrid (SELECTED):** Ship the GMP platform to generate revenue and create a
  live regulatory proof-of-concept, then abstract the underlying ALCOA+ data integrity
  primitives into a domain-agnostic truth layer for AI systems.

**Formal decision matrix scores (11 dimensions, scored 1–5):**
Option A 37/55 · Option B 27/55 · **Option C 51/55**

### The Decisive Insight

> The GMP platform is not pharma software that happens to resemble a truth infrastructure.
> It IS a truth infrastructure — validated under the world's most demanding compliance regime
> (FDA 21 CFR Part 11, criminal penalties since 1997) — that currently runs in pharma.
>
> The ALCOA+ principles (Attributable, Legible, Contemporaneous, Original, Accurate,
> Complete, Consistent, Enduring, Available) are not pharmaceutical-specific. They are a
> universal framework for verifiable, trustworthy data, applicable to AI agent outputs and
> information provenance as directly as to pharmaceutical batch records.
>
> The six GMP modules — with their cross-references and event propagation (LIMS OOS
> auto-triggering QMS Deviation, Equipment calibration expiry blocking MES operations,
> ENV excursion cascading to batch review) — constitute a multi-agent coordination system
> with verified handoffs and an append-only audit trail. No current multi-agent AI framework
> (LangGraph, CrewAI, AutoGen, OpenAI Agents SDK, Google ADK) has this. The GMP platform
> is the reference implementation of the piece they are all missing.
>
> The QMS deviation workflow (identify anomaly → attribute → root-cause → verify fix) is,
> structurally, a Socratic examination engine: an adversarial truth-testing protocol,
> codified in software, validated by federal regulators.

---

## Decision

**Option C is adopted as the formal strategic path for this project.**

This is not hedging between two strategies. It is deliberate sequencing: do the first thing
to completion so it funds, proves, and positions the second thing.

### Phase 1 — Months 1–6: Ship GMP v1.0

- Complete remaining ~30% of the GMP platform (all 6 modules functional, validation docs ready)
- Recruit 5–10 biotech/CDMO design partners at significant discount for case study rights
- Target: at least one live GxP deployment generating recurring revenue before Phase 2 begins
- Critical path: TASK-029 (QMS FUNCTIONAL) → TASK-031 (Frontend QMS CAPA demo screen)

### Phase 2 — Months 6–18: Abstract the Truth Layer (Internal Only)

- Extract audit trail engine, append-only record pattern, e-signature layer, and cross-module
  event propagation into a domain-agnostic internal SDK
- Do NOT launch publicly — instrument, test, and validate internally only
- Publish one technical article: mapping ALCOA+ principles to EU AI Act audit requirements
  (Articles 9, 10, 12, 17 and Annex IV) — claim conceptual ground before others name it
  (Outline: `docs/articles/alcoa-eu-ai-act-mapping-outline.md`)

### Phase 3 — Months 18–36: Open the Truth Layer

- With GMP revenue funding operations and a proven SDK, open to:
  - AI companies building agent systems that need inter-agent verification infrastructure
  - Adjacent regulated industries (medical devices, food safety, financial compliance)
  - AI governance platforms needing operational enforcement, not just policy documentation
- Fundraising narrative at this stage: validated product + proven infrastructure +
  dual customer base + regulatory proof-of-concept under FDA requirements

---

## Guard Rails — Mandatory Before Phase 2 SDK Extraction Begins

These conditions are **immutable until superseded by a new ADR with Project Owner sign-off**.
Encoded in TASK_QUEUE.md as TASK-035 (LOCKED).

| # | Guard Condition | How to Verify |
|---|----------------|---------------|
| G1 | At least **2 modules at FUNCTIONAL tier** in registry.json | `registry.json` — check tier fields |
| G2 | At least **1 paying design partner** live on the GMP platform | Active Supabase tenant + signed agreement |
| G3 | **TASK-029 DONE** (QMS FUNCTIONAL tier) | TASK_QUEUE.md status |
| G4 | **TASK-031 DONE** (Frontend QMS CAPA demo screen) | Working UI — cannot sell without UI |

**Until all four conditions are met:**
- Cursor builds GMP features only
- No SDK extraction
- No abstract truth layer architecture work
- No Phase 2 positioning conversations

The purpose of these guards: prevent the most common failure pattern among technically
sophisticated founders — beginning the bigger vision before the proof-of-concept is funded
and live, leaving both halves half-built with no revenue and no credibility.

---

## The Failure Mode This ADR Exists to Prevent

```
Month 2: GMP customer acquisition is slower than hoped. The mega AI vision looks exciting.
         "Let's just start exploring the SDK abstraction..."

Month 4: The truth layer SDK is 40% done. The GMP platform is 80% done.
         No customers on either. Both pitches lack a live deployment.

Month 8: Neither product is finished. Neither is validated.
         No revenue. No credibility. Both stories are unconvincing.
```

The guard conditions are the technical lock against this failure mode.
If a guard condition is not met, the correct response is to fix what is blocking it —
not to start Phase 2 early.

---

## Why Not Option B — The Honest Version

Option B's vision is correct. The long-term direction is a multi-agent AI platform
with a verified truth layer. The problem is sequencing, not vision.

Option B requires:
- Abandoning 70% of working, partially-validated architecture — the same architecture that IS
  the proof-of-concept for the truth infrastructure the new platform would need to build anyway
- Immediate significant capital before any revenue exists ($500K–$2M estimated to reach a
  competitive MVP, 12–24 months)
- Racing directly against OpenAI Agents SDK, Google ADK, LangGraph, CrewAI — none of which
  can be outspent or out-distributed by a resource-constrained team

The GMP platform, live under FDA requirements, proves the truth infrastructure more
convincingly than any amount of funding raised to rebuild from scratch. That proof takes
~6 months and generates revenue. Option B takes 18–36 months and burns cash with no revenue.

**Option B's vision. Option C's sequencing. That is the correct path.**

---

## The Three Non-Obvious Strategic Positions

These asymmetric advantages must be preserved and not disclosed prematurely:

**1. Pharma compliance is the hardest proof-of-concept environment for truth infrastructure.**
FDA 21 CFR Part 11 has enforced accuracy, attribution, immutability, and audit accessibility
with criminal penalties since 1997. The EU AI Act imposes fines. Pharma's bar is higher.
A live GxP deployment is proof of truth infrastructure that no AI-native competitor can
replicate without first building what this project has already built.

**2. The QMS deviation workflow is an already-built Socratic examination engine.**
The deviation process — identify anomaly, attribute it, root-cause analyze, verify the fix
addresses root cause not symptom — is a structured adversarial challenge protocol, already
in the codebase, already validated by federal regulators. This is the "devil's advocate agent"
pattern missing from every multi-agent framework. It does not need to be built; it needs to
be abstracted. That abstraction is Phase 2 work.

**3. The scarcest resource in AI right now is not intelligence — it is verifiability.**
Every major AI company can produce text that sounds correct. Very few can produce a verifiable,
immutable, attributed record of why an output is correct — with source provenance, timestamps,
and an audit trail showing what conditions would invalidate the claim. AI regulation will
require this. The companies that see this now are 2–3 years ahead of the enforcement curve.

---

## What This ADR Does NOT Change

- Build priority: GMP P0/P1 tasks remain primary for all autonomous build sessions
- Code structure: no module renames, no architectural changes required
- ADR-004 (Module as Capability) mapping: documentation only, never a directive that
  overrides GMP feature work
- The validation path: GMP product (Path A) is the primary revenue path through Phase 1

---

## Consequences

### Files created or updated by this decision

- `decisions/ADR-005-option-c-hybrid-strategy.md` — this file
- `TASK_QUEUE.md` — TASK-033 (article outline), TASK-034 (design partners),
  TASK-035 (LOCKED: truth layer SDK), Option C guard rails section
- `README.md` — Strategic Path section added
- `docs/articles/alcoa-eu-ai-act-mapping-outline.md` — article structure for Phase 2

### What triggers the next review of this ADR

Guard condition G2 being met: first paying design partner live on the GMP platform.
At that point: evaluate Phase 2 timeline, formalize SDK extraction scope, begin public
positioning of the ALCOA+ truth layer concept.

---

*Decided by: Project Owner + Matrix Agent*
*Date: 2026-04-22*
*Guard rail review trigger: First paying design partner live*
*Full strategic evidence: C:\workspace\STRATEGIC_ANALYSIS.md*
