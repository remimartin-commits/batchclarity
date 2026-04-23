"""QMS deviation functional completion fields and workflow.

Revision ID: 20260427_qms_deviation_functional_completion
Revises: 20260426_qms_capa_trackwise_parity
Create Date: 2026-04-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260427_qms_deviation_functional_completion"
down_revision = "20260426_qms_capa_trackwise_parity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deviations",
        sa.Column("gmp_impact_classification", sa.String(length=20), nullable=False, server_default="major"),
    )
    op.add_column(
        "deviations",
        sa.Column("potential_patient_impact", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("deviations", sa.Column("potential_patient_impact_justification", sa.Text(), nullable=True))
    op.add_column("deviations", sa.Column("batches_affected", sa.JSON(), nullable=True))
    op.add_column("deviations", sa.Column("product_affected", sa.String(length=255), nullable=True))
    op.add_column("deviations", sa.Column("immediate_containment_actions", sa.Text(), nullable=True))
    op.add_column("deviations", sa.Column("immediate_containment_actions_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("deviations", sa.Column("root_cause_category", sa.String(length=100), nullable=True))
    op.add_column("deviations", sa.Column("requires_capa", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column(
        "deviations",
        sa.Column("regulatory_notification_required", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("deviations", sa.Column("regulatory_authority_name", sa.String(length=255), nullable=True))
    op.add_column("deviations", sa.Column("regulatory_notification_deadline", sa.DateTime(timezone=True), nullable=True))
    op.add_column("deviations", sa.Column("no_capa_needed_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("deviations", sa.Column("no_capa_needed_justification", sa.Text(), nullable=True))

    op.execute("UPDATE deviations SET current_status='open' WHERE current_status='draft'")
    op.execute("UPDATE deviations SET current_status='under_investigation' WHERE current_status='under_review'")
    op.execute("UPDATE deviations SET current_status='pending_approval' WHERE current_status='approved'")

    op.execute("UPDATE deviations SET immediate_containment_actions = COALESCE(immediate_action, description)")
    op.execute("UPDATE deviations SET immediate_containment_actions_at = created_at")
    op.execute("UPDATE deviations SET batches_affected = to_jsonb(ARRAY[batch_number]) WHERE batch_number IS NOT NULL")


def downgrade() -> None:
    op.execute("UPDATE deviations SET current_status='draft' WHERE current_status='open'")
    op.execute("UPDATE deviations SET current_status='under_review' WHERE current_status='under_investigation'")
    op.execute("UPDATE deviations SET current_status='approved' WHERE current_status='pending_approval'")

    op.drop_column("deviations", "no_capa_needed_justification")
    op.drop_column("deviations", "no_capa_needed_confirmed")
    op.drop_column("deviations", "regulatory_notification_deadline")
    op.drop_column("deviations", "regulatory_authority_name")
    op.drop_column("deviations", "regulatory_notification_required")
    op.drop_column("deviations", "requires_capa")
    op.drop_column("deviations", "root_cause_category")
    op.drop_column("deviations", "immediate_containment_actions_at")
    op.drop_column("deviations", "immediate_containment_actions")
    op.drop_column("deviations", "product_affected")
    op.drop_column("deviations", "batches_affected")
    op.drop_column("deviations", "potential_patient_impact_justification")
    op.drop_column("deviations", "potential_patient_impact")
    op.drop_column("deviations", "gmp_impact_classification")
