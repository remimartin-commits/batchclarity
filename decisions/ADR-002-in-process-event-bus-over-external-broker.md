# ADR-002: In-Process Event Bus Over External Broker

- **Status**: Accepted
- **Date**: 2026-04-21
- **Deciders**: Product/Platform Architecture
- **Technical Area**: Architecture

## Context

Modules must communicate without direct lateral imports or shared database coupling. Current stage prioritizes boundary safety, implementation speed, and controlled operational complexity. Cross-module signals are needed for loose coupling.

## Decision

Use an in-process event bus for module-to-module communication in the modular monolith. Defer external broker adoption until scale or reliability requirements clearly justify it.

## Consequences

### Positive

- Keeps modules decoupled at service and schema boundaries while remaining simple to implement.
- Lower operational burden than running Kafka/RabbitMQ/SNS+SQS at early stage.
- Easier debugging and deterministic behavior within a single process.
- Supports progressive hardening and future migration to external broker behind a stable event contract.

### Negative

- Event durability and replay capabilities are weaker than a dedicated broker unless explicitly implemented.
- Horizontal scaling beyond one process needs added delivery guarantees.
- Future migration to an external broker requires adapter implementation and rollout planning.

### Follow-up Actions

- Define explicit event contracts and versioning rules now.
- Add event logging/outbox pattern if reliability requirements increase.
- Keep event publisher/subscriber interfaces broker-agnostic.

## Alternatives Considered

- External broker now: rejected due to premature infrastructure and validation complexity.
- Direct module API calls everywhere: rejected because it risks tighter runtime coupling.

## Compliance / Validation Notes (GMP)

- 21 CFR Part 11 impact: event-driven flows must preserve auditability and attributable actions.
- EU Annex 11 impact: requires controlled change and traceability for event contracts.
- Validation impact (GAMP 5 Category 5): incremental complexity is lower with in-process design at this stage.
