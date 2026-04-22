"""LIMS test_results: append-only correction chain (is_invalidated, corrects_result_id).

Revision ID: 20260424_lims_test_result_correction_fields
Revises: 20260423_decouple_cross_module_fks
Create Date: 2026-04-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260424_lims_test_result_correction_fields"
down_revision = "20260423_decouple_cross_module_fks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "test_results",
        sa.Column("is_invalidated", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "test_results",
        sa.Column("corrects_result_id", sa.String(length=36), nullable=True),
    )
    op.create_index(
        "ix_test_results_corrects_result_id",
        "test_results",
        ["corrects_result_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_test_results_corrects_result_id",
        "test_results",
        "test_results",
        ["corrects_result_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_test_results_corrects_result_id", "test_results", type_="foreignkey")
    op.drop_index("ix_test_results_corrects_result_id", table_name="test_results")
    op.drop_column("test_results", "corrects_result_id")
    op.drop_column("test_results", "is_invalidated")
