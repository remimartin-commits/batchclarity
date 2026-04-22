# Audit — 2026-04-21 — Event Bus Hook Registry

## What was built
core/tasks.py refactored from a file that directly imported CAPA, Equipment,
TrainingAssignment, Document to a clean hook registry with zero module imports.

## Design
- OverdueHook = Callable[[], Awaitable[object]]
- _overdue_hooks: dict[str, OverdueHook] = {}
- register_overdue_hook(name, hook) — called at startup
- clear_overdue_hooks() — for test isolation
- run_overdue_checks() — iterates registry, catches exceptions per-hook

## Each module owns its hook
- qms/tasks.py → check_overdue_capas()
- equipment/tasks.py → check_calibration_due()
- training/tasks.py → check_overdue_training()
- core/documents/tasks.py → check_document_reviews()

## Registered in main.py lifespan
clear_overdue_hooks()
register_overdue_hook("qms_overdue_capas", check_overdue_capas)
register_overdue_hook("equipment_calibration", check_calibration_due)
register_overdue_hook("training_overdue", check_overdue_training)
register_overdue_hook("document_reviews", check_document_reviews)

## Outstanding issue
All hooks count and return — none call NotificationService.
This must be fixed before compliance go-live (see post-fix audit 2026-04-23).
