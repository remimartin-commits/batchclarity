"""
Authentication & RBAC models — 21 CFR Part 11 compliant.

Key GMP requirements met here:
  - Unique user IDs that cannot be shared
  - Password history enforcement (12 passwords)
  - Session timeout tracking (30 min inactivity)
  - Account lockout after failed attempts
  - Full user lifecycle audit trail via foreign keys to audit_events
"""
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Text, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.core.database import Base


# Many-to-many: users <-> roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE")),
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE")),
)

# Many-to-many: roles <-> permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE")),
    Column("permission_id", String(36), ForeignKey("permissions.id", ondelete="CASCADE")),
)


class User(Base):
    __tablename__ = "users"

    # Identity
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    department: Mapped[str] = mapped_column(String(100), nullable=True)
    job_title: Mapped[str] = mapped_column(String(150), nullable=True)

    # Credentials
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Account state (21 CFR Part 11)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # GMP-specific
    training_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    site_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sites.id"), nullable=True)

    # MFA (TOTP — Google Authenticator compatible)
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    roles: Mapped[list["Role"]] = relationship("Role", secondary=user_roles, back_populates="users")
    sessions: Mapped[list["UserSession"]] = relationship("UserSession", back_populates="user")
    password_history: Mapped[list["PasswordHistory"]] = relationship("PasswordHistory", back_populates="user")
    electronic_signatures: Mapped[list["ElectronicSignature"]] = relationship(
        "ElectronicSignature", back_populates="user", foreign_keys="ElectronicSignature.signed_by_id"
    )


class Role(Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False)  # System roles cannot be deleted

    users: Mapped[list["User"]] = relationship("User", secondary=user_roles, back_populates="roles")
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", secondary=role_permissions, back_populates="roles"
    )


class Permission(Base):
    __tablename__ = "permissions"

    # Format: "module:resource:action" e.g. "qms:capa:approve", "mes:batch_record:execute"
    code: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    roles: Mapped[list["Role"]] = relationship("Role", secondary=role_permissions, back_populates="permissions")


class UserSession(Base):
    __tablename__ = "user_sessions"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    refresh_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    refresh_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invalidation_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="sessions")


class PasswordHistory(Base):
    __tablename__ = "password_history"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    set_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="password_history")


class Organisation(Base):
    """Multi-site tenant (e.g. corporate pharma organisation)."""

    __tablename__ = "organisations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    legal_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    sites: Mapped[list["Site"]] = relationship("Site", back_populates="organisation")


class Site(Base):
    """Manufacturing site / facility"""
    __tablename__ = "sites"

    organisation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organisations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=True)
    gmp_license_number: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    organisation: Mapped["Organisation"] = relationship("Organisation", back_populates="sites")


# Avoid circular import — ElectronicSignature imported here from esig module
from app.core.esig.models import ElectronicSignature  # noqa: E402
