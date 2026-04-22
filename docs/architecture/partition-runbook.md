# Partition Runbook for High-Volume Tables

## Scope

This runbook defines a zero-downtime migration approach for:

- `audit_events`
- `test_results`
- `batch_record_steps`

It is **documentation-only** for TASK-030. Do not execute these steps directly in production until approved.

## Goals

- Move high-write tables to PostgreSQL range partitions.
- Preserve all application behavior and query compatibility.
- Keep rollback path available until post-cutover validation completes.

## Assumptions

- PostgreSQL (Supabase) is the active database.
- Migration window permits dual-write safety checks.
- Existing indexes and constraints are known.
- Alembic is the migration tool of record.

## Table Partition Strategy

- **Partition key**
  - `audit_events`: `event_at` (monthly)
  - `test_results`: `created_at` (monthly)
  - `batch_record_steps`: `created_at` (monthly)
- **Granularity**: monthly partitions, created in advance for next 3 months.
- **Retention**: maintain all history; no archive/drop in this runbook.

## Zero-Downtime Cutover Plan

Repeat this sequence table-by-table.

1. **Pre-checks**
   - Confirm table row count and size.
   - Record baseline query latency (list endpoints + key aggregates).
   - Confirm no long-running locks on target table.

2. **Create partitioned parent + initial partitions**
   - Create a new partitioned table (`<table>_p`) with identical columns.
   - Recreate PK/unique/index set appropriate for partitioned structure.
   - Create current + next N month partitions.

3. **Backfill existing data**
   - Copy historical rows from source table into partitioned table in batches.
   - Verify row counts per day/month between source and partitioned destination.

4. **Dual-write safety window (optional but recommended)**
   - Add temporary trigger on source table that mirrors writes to `<table>_p`.
   - Monitor divergence counters (source vs destination deltas).

5. **Cutover (short lock window)**
   - Acquire lock.
   - Rename original table to `<table>_old`.
   - Rename partitioned table `<table>_p` to original table name.
   - Repoint/restore dependent indexes, constraints, and grants.

6. **Post-cutover validation**
   - Validate read/write API flows.
   - Compare row counts and sampled row hashes.
   - Re-run latency checks.

7. **Rollback plan**
   - If validation fails, reverse renames (`<table>` -> `<table>_failed`, `<table>_old` -> `<table>`).
   - Disable mirror trigger if enabled.

8. **Finalize**
   - After stability window, drop `<table>_old`.
   - Keep scheduled partition creation job in place.

## Alembic Migration Template (Documentation Only)

```python
"""partition <table_name> by month

Revision ID: <new_revision_id>
Revises: <previous_revision_id>
Create Date: <timestamp>
"""

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # 1) Create partitioned parent (example key: created_at)
    op.execute("""
    CREATE TABLE <table_name>_p (
      -- copy all columns from <table_name>
      LIKE <table_name> INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES
    ) PARTITION BY RANGE (<partition_column>);
    """)

    # 2) Create partitions (example monthly partition)
    op.execute("""
    CREATE TABLE <table_name>_p_2026_04
      PARTITION OF <table_name>_p
      FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
    """)

    # 3) Backfill historical data
    op.execute("""
    INSERT INTO <table_name>_p
    SELECT * FROM <table_name>;
    """)

    # 4) Cutover rename
    op.execute("ALTER TABLE <table_name> RENAME TO <table_name>_old;")
    op.execute("ALTER TABLE <table_name>_p RENAME TO <table_name>;")

    # 5) Recreate grants/triggers as needed


def downgrade() -> None:
    # Reverse rename first
    op.execute("ALTER TABLE <table_name> RENAME TO <table_name>_p;")
    op.execute("ALTER TABLE <table_name>_old RENAME TO <table_name>;")
    op.execute("DROP TABLE IF EXISTS <table_name>_p CASCADE;")
```

Notes:

- For large tables, replace one-shot `INSERT INTO ... SELECT` with batched copy by time window.
- For partitioned PK/unique constraints, ensure the partition key is included when required.
- Adjust index definitions per PostgreSQL partitioning best practices.

## Dev Clone Test Plan

Run on a development DB clone before any production change.

1. **Baseline snapshot**
   - Save row counts for all three tables.
   - Save endpoint smoke outputs for:
     - audit-backed endpoints
     - LIMS test result list/review
     - MES batch step execution history

2. **Execute migration on clone**
   - Apply Alembic revision with partition template customized per table.

3. **Data validation**
   - Compare row counts before/after.
   - Spot-check random records by ID.
   - Confirm foreign key relationships still resolve.

4. **Behavior validation**
   - Run backend tests:
     - `pytest tests/test_architecture_boundaries.py -v`
     - `pytest tests/ -x -q`
   - Exercise API create/list/update flows for QMS/LIMS/MES paths touching these tables.

5. **Performance validation**
   - Compare representative query timings against baseline.
   - Confirm partition pruning occurs for time-bounded queries (`EXPLAIN ANALYZE`).

6. **Rollback rehearsal**
   - Execute documented rollback on clone and verify application health.

## Operational Checklist for Production Approval

- [ ] DBA and application owner sign-off
- [ ] Maintenance/cutover window approved
- [ ] Rollback commands tested on clone
- [ ] Monitoring dashboards prepared for lock/wait/error spikes
- [ ] Partition creation automation in place (monthly ahead-of-time)

