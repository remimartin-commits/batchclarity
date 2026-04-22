# ADR-003: Module Sequencing (Inventory First, MES Last)

- **Status**: Accepted
- **Date**: 2026-04-21
- **Deciders**: Product/Platform Architecture
- **Technical Area**: Delivery

## Context

The platform roadmap includes multiple GMP modules with dependency relationships. MES is operationally critical and depends on stable upstream master data and quality controls. Sequencing impacts delivery risk, validation efficiency, and rework.

## Decision

Build modules in this order: Inventory first, MES last.

## Consequences

### Positive

- Establishes foundational master data and material flows before complex execution logic.
- Reduces churn in MES by stabilizing upstream domains first.
- Improves validation sequencing by hardening lower-risk modules before high-criticality execution modules.
- Enables cleaner interfaces and fewer late-stage schema pivots.

### Negative

- MES business value realization is delayed relative to a MES-first approach.
- Upstream modules must be sufficiently complete to avoid blocking later MES delivery.

### Follow-up Actions

- Maintain explicit interface contracts between Inventory and downstream modules.
- Track dependency readiness criteria before starting MES implementation.
- Revisit sequence only via new ADR if risk or business priorities materially change.

## Alternatives Considered

- MES first: rejected due to high downstream dependency and rework risk.
- Parallel full-module development: rejected due to boundary drift and validation overhead risk.

## Compliance / Validation Notes (GMP)

- 21 CFR Part 11 impact: phased rollout supports controlled, testable deployment of critical controls.
- EU Annex 11 impact: sequencing supports stronger lifecycle and change control discipline.
- Validation impact (GAMP 5 Category 5): staged complexity reduces validation risk accumulation.
