"""Add MFA fields on users and refresh token fields on user_sessions.

Revision ID: 20260422_auth_mfa_refresh
Revises: None
Create Date: 2026-04-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260422_auth_mfa_refresh"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("totp_secret", sa.String(length=64), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "is_mfa_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.alter_column("users", "is_mfa_enabled", server_default=None)

    op.add_column(
        "user_sessions",
        sa.Column("refresh_token_hash", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "user_sessions",
        sa.Column("refresh_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_user_sessions_refresh_token_hash",
        "user_sessions",
        ["refresh_token_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_sessions_refresh_token_hash", table_name="user_sessions")
    op.drop_column("user_sessions", "refresh_expires_at")
    op.drop_column("user_sessions", "refresh_token_hash")
    op.drop_column("users", "is_mfa_enabled")
    op.drop_column("users", "totp_secret")
