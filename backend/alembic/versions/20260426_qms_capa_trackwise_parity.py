"""QMS CAPA TrackWise parity fields and workflow normalization.

Revision ID: 20260426_qms_capa_trackwise_parity
Revises: 20260425_env_monitoring_result_trend_status
Create Date: 2026-04-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260426_qms_capa_trackwise_parity"
down_revision = "20260425_env_monitoring_result_trend_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_events", sa.Column("role_at_time", sa.String(length=255), nullable=True))

    op.add_column("capas", sa.Column("product_material_affected", sa.String(length=255), nullable=True))
    op.add_column("capas", sa.Column("batch_lot_number", sa.String(length=100), nullable=True))
    op.add_column(
        "capas",
        sa.Column("gmp_classification", sa.String(length=50), nullable=False, server_default="minor"),
    )
    op.add_column("capas", sa.Column("regulatory_reporting_justification", sa.Text(), nullable=True))
    op.add_column("capas", sa.Column("root_cause_category", sa.String(length=100), nullable=True))
    op.add_column("capas", sa.Column("effectiveness_check_method", sa.String(length=200), nullable=True))
    op.add_column("capas", sa.Column("effectiveness_evidence_note", sa.Text(), nullable=True))

    op.alter_column("capa_actions", "evidence", new_column_name="completion_evidence")

    op.execute("UPDATE capas SET current_status='open' WHERE current_status='draft'")
    op.execute("UPDATE capas SET current_status='investigation' WHERE current_status='under_review'")
    op.execute("UPDATE capas SET current_status='action_plan_approved' WHERE current_status='approved'")
    op.execute("UPDATE capas SET current_status='closed' WHERE current_status='completed'")
    op.execute("UPDATE capa_actions SET status='pending' WHERE status='open'")
    op.execute("UPDATE capa_actions SET status='complete' WHERE status IN ('completed', 'done')")


def downgrade() -> None:
    op.execute("UPDATE capa_actions SET status='open' WHERE status='pending'")
    op.execute("UPDATE capa_actions SET status='completed' WHERE status='complete'")
    op.execute("UPDATE capas SET current_status='draft' WHERE current_status='open'")
    op.execute("UPDATE capas SET current_status='under_review' WHERE current_status='investigation'")
    op.execute("UPDATE capas SET current_status='approved' WHERE current_status='action_plan_approved'")

    op.alter_column("capa_actions", "completion_evidence", new_column_name="evidence")

    op.drop_column("capas", "effectiveness_evidence_note")
    op.drop_column("capas", "effectiveness_check_method")
    op.drop_column("capas", "root_cause_category")
    op.drop_column("capas", "regulatory_reporting_justification")
    op.drop_column("capas", "gmp_classification")
    op.drop_column("capas", "batch_lot_number")
    op.drop_column("capas", "product_material_affected")
    op.drop_column("audit_events", "role_at_time")
