"""ENV: exceeds_alert_limit on results; status on monitoring_trends.

Revision ID: 20260425_env_monitoring_result_trend_status
Revises: 20260424_lims_test_result_correction_fields
Create Date: 2026-04-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260425_env_monitoring_result_trend_status"
down_revision = "20260424_lims_test_result_correction_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "monitoring_results",
        sa.Column("exceeds_alert_limit", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "monitoring_trends",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
    )


def downgrade() -> None:
    op.drop_column("monitoring_trends", "status")
    op.drop_column("monitoring_results", "exceeds_alert_limit")
