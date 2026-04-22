# ADR-001: Modular Monolith Over Microservices

- **Status**: Accepted
- **Date**: 2026-04-21
- **Deciders**: Product/Platform Architecture
- **Technical Area**: Architecture

## Context

The platform must replace many pharma systems while preserving strict GMP controls, validation traceability, and predictable delivery. Early-stage scope includes foundation controls (auth, audit, e-signature, workflow), then module-by-module expansion. Team capacity and validation overhead are key constraints.

## Decision

Adopt a modular monolith architecture with hard module boundaries instead of a microservices architecture.

## Consequences

### Positive

- Single deployable simplifies release validation, installation qualification, and operational control.
- Lower distributed-systems complexity (network failures, retries, eventual consistency, service discovery).
- Faster iteration for shared GMP foundation controls and consistent enforcement across modules.
- Easier end-to-end testing and traceability within one runtime and one migration stream.

### Negative

- Requires strict internal boundary enforcement to prevent coupling drift.
- Independent module scaling is less granular than microservices.
- Long-term extraction to services requires explicit interface discipline from the start.

### Follow-up Actions

- Enforce architecture tests for module boundaries and cross-module dependency rules.
- Maintain module-level API contracts and ADRs for future extraction readiness.
- Keep cross-module communication constrained to approved patterns.

## Alternatives Considered

- Microservices from day one: rejected due to high platform and validation overhead too early.
- Layered monolith without module boundaries: rejected due to high coupling risk.

## Compliance / Validation Notes (GMP)

- 21 CFR Part 11 impact: centralized audit/e-sign controls are easier to apply consistently.
- EU Annex 11 impact: supports stronger computerized system control and change management.
- Validation impact (GAMP 5 Category 5): reduces validation surface by avoiding many independently deployed services.
