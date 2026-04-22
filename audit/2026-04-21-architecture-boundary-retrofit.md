# Audit — 2026-04-21 — Architecture Boundary Retrofit

## What Cursor did
Removed hard cross-module FKs and added architecture enforcement tests.

## Changes made
1. mes/models.py: BatchRecordStep.deviation_id → linked_deviation_id (String(36), no FK)
2. core/tasks.py: refactored from direct model imports to hook registry
3. Module task hooks created: qms/tasks.py, equipment/tasks.py, training/tasks.py, documents/tasks.py
4. main.py: hooks registered at startup via register_overdue_hook()
5. Architecture tests: test_architecture_boundaries.py (AST-based)
6. Migration: 20260423_decouple_cross_module_fks.py

## Verdict
Real work. AST parsing is genuine. Migration has downgrade path.
Key gap: hooks count but don't notify (see post-fix audit 2026-04-23).
