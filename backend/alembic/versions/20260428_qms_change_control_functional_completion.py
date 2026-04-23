"""QMS change control functional completion fields and workflow.

Revision ID: 20260428_qms_change_control_functional_completion
Revises: 20260427_qms_deviation_functional_completion
Create Date: 2026-04-28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260428_qms_change_control_functional_completion"
down_revision = "20260427_qms_deviation_functional_completion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "change_controls",
        sa.Column("regulatory_filing_required", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("change_controls", sa.Column("regulatory_filing_type", sa.String(length=100), nullable=True))
    op.add_column(
        "change_controls",
        sa.Column("validation_qualification_required", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("change_controls", sa.Column("validation_scope_description", sa.Text(), nullable=True))
    op.add_column("change_controls", sa.Column("affected_document_ids", sa.JSON(), nullable=True))
    op.add_column("change_controls", sa.Column("affected_equipment_ids", sa.JSON(), nullable=True))
    op.add_column("change_controls", sa.Column("affected_sop_document_ids", sa.JSON(), nullable=True))
    op.add_column("change_controls", sa.Column("implementation_plan", sa.Text(), nullable=True))
    op.add_column("change_controls", sa.Column("implementation_target_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("change_controls", sa.Column("pre_change_verification_checklist", sa.JSON(), nullable=True))
    op.add_column("change_controls", sa.Column("post_change_effectiveness_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("change_controls", sa.Column("post_change_effectiveness_outcome", sa.String(length=100), nullable=True))
    op.add_column("change_controls", sa.Column("post_change_effectiveness_approver_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        "fk_change_controls_post_change_effectiveness_approver_id",
        "change_controls",
        "users",
        ["post_change_effectiveness_approver_id"],
        ["id"],
    )
    op.add_column("change_controls", sa.Column("approval_signature_roles", sa.JSON(), nullable=True))

    op.execute("UPDATE change_controls SET current_status='in_implementation' WHERE current_status='implementation'")


def downgrade() -> None:
    op.execute("UPDATE change_controls SET current_status='implementation' WHERE current_status='in_implementation'")
    op.drop_column("change_controls", "approval_signature_roles")
    op.drop_constraint("fk_change_controls_post_change_effectiveness_approver_id", "change_controls", type_="foreignkey")
    op.drop_column("change_controls", "post_change_effectiveness_approver_id")
    op.drop_column("change_controls", "post_change_effectiveness_outcome")
    op.drop_column("change_controls", "post_change_effectiveness_date")
    op.drop_column("change_controls", "pre_change_verification_checklist")
    op.drop_column("change_controls", "implementation_target_date")
    op.drop_column("change_controls", "implementation_plan")
    op.drop_column("change_controls", "affected_sop_document_ids")
    op.drop_column("change_controls", "affected_equipment_ids")
    op.drop_column("change_controls", "affected_document_ids")
    op.drop_column("change_controls", "validation_scope_description")
    op.drop_column("change_controls", "validation_qualification_required")
    op.drop_column("change_controls", "regulatory_filing_type")
    op.drop_column("change_controls", "regulatory_filing_required")
