# Prompt Record — 2026-04-22 — MES + Full Module Skeleton

## Context
Second major build session. Foundation was in place. Agent was asked to build
all six business modules and wire them together.

## Prompt (reconstructed)
Build the full module skeleton for the GMP platform:
- QMS: CAPA, CAPAAction, Deviation, ChangeControl
- MES: Product, MasterBatchRecord, MBRStep, BatchRecord, BatchRecordStep
- Equipment: Equipment, CalibrationRecord, QualificationRecord, MaintenanceRecord
- Training: TrainingCurriculum, CurriculumItem, TrainingAssignment, TrainingCompletion
- LIMS: TestMethod, Specification, SpecificationTest, Sample, TestResult, OOSInvestigation
- ENV Monitoring: MonitoringLocation, AlertLimit, MonitoringResult, SamplingPlan, MonitoringTrend

Also build routers, services, background task hooks. Wire APScheduler.

## Output produced
- backend/app/modules/qms/models.py, router.py
- backend/app/modules/mes/models.py, router.py
- backend/app/modules/equipment/models.py, router.py
- backend/app/modules/training/models.py, router.py
- backend/app/modules/lims/models.py, router.py
- backend/app/modules/env_monitoring/models.py, router.py
- backend/app/core/tasks.py (initial version — later refactored)

## Issues found in audit (2026-04-23)
- CRITICAL: mes/models.py had ForeignKey("deviations.id") — cross-module FK
- ISSUE: core/tasks.py imported CAPA, Equipment, TrainingAssignment directly
- Both fixed by Cursor post-audit with migration 20260423_decouple_cross_module_fks.py

## Remaining issues (as of 2026-04-23 audit)
See audit/2026-04-23-post-fix-audit.md for full findings.
Short version:
- Overdue hooks count but never call NotificationService — highest priority fix
- is_overdue and TrainingAssignment.status="overdue" never written by scheduler
- create_all unguarded in production
- CORS wildcard
- Migration silently swallows exceptions
