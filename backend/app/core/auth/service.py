"""
Authentication Service — 21 CFR Part 11 compliant.
Handles: login, token issuance, session management, password validation,
         account lockout, password history enforcement.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import hashlib
import secrets

import pyotp
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.auth.models import User, UserSession, PasswordHistory, Role, Permission
from app.core.audit.service import AuditService
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:

    # ── Password utilities ────────────────────────────────────────────────────

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    @staticmethod
    def validate_password_strength(password: str) -> list[str]:
        """Returns list of validation errors. Empty list = password is valid."""
        errors = []
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters.")
        if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter.")
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter.")
        if settings.PASSWORD_REQUIRE_NUMBER and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number.")
        if settings.PASSWORD_REQUIRE_SPECIAL and not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in password):
            errors.append("Password must contain at least one special character.")
        return errors

    @staticmethod
    async def check_password_history(db: AsyncSession, user_id: str, new_password: str) -> bool:
        """Returns True if password was used in last N passwords (not allowed)."""
        result = await db.execute(
            select(PasswordHistory)
            .where(PasswordHistory.user_id == user_id)
            .order_by(PasswordHistory.set_at.desc())
            .limit(settings.PASSWORD_HISTORY_COUNT)
        )
        history = result.scalars().all()
        return any(pwd_context.verify(new_password, h.hashed_password) for h in history)

    # ── Login / Lockout ───────────────────────────────────────────────────────

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, username: str, password: str, ip_address: str
    ) -> Optional["User"]:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user:
            # Timing-safe: still hash to prevent user enumeration
            pwd_context.verify(password, "$2b$12$dummy.hash.to.prevent.timing.attack.xxxxxxxxxx")
            await AuditService.log_login(
                db,
                user_id=None,
                username=username,
                full_name="Unknown",
                ip_address=ip_address,
                success=False,
                failure_reason="unknown_username",
            )
            return None

        # Check lockout
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            await AuditService.log_login(
                db, user_id=user.id, username=user.username, full_name=user.full_name,
                ip_address=ip_address, success=False, failure_reason="account_locked"
            )
            return None

        if not AuthService.verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.now(timezone.utc) + timedelta(
                    minutes=settings.LOCKOUT_DURATION_MINUTES
                )
            await AuditService.log_login(
                db, user_id=user.id, username=user.username, full_name=user.full_name,
                ip_address=ip_address, success=False, failure_reason="wrong_password"
            )
            return None

        # Successful login — reset lockout counters
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(timezone.utc)
        await AuditService.log_login(
            db, user_id=user.id, username=user.username, full_name=user.full_name,
            ip_address=ip_address, success=True
        )
        return user

    # ── JWT Tokens ────────────────────────────────────────────────────────────

    @staticmethod
    def create_access_token(user: "User") -> tuple[str, datetime]:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return token, expire

    @staticmethod
    def create_refresh_token(user: "User") -> tuple[str, datetime]:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "sub": user.id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
            "jti": secrets.token_hex(16),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return token, expire

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError:
            return None

    # ── Sessions ──────────────────────────────────────────────────────────────

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user: "User",
        access_token: str,
        access_expires: datetime,
        refresh_token: str,
        refresh_expires: datetime,
        ip_address: str,
        user_agent: str,
    ) -> "UserSession":
        access_hash = hashlib.sha256(access_token.encode()).hexdigest()
        refresh_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        session = UserSession(
            user_id=user.id,
            token_hash=access_hash,
            refresh_token_hash=refresh_hash,
            refresh_expires_at=refresh_expires,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=access_expires,
            last_activity_at=datetime.now(timezone.utc),
        )
        db.add(session)
        await db.flush([session])
        return session

    @staticmethod
    async def invalidate_session(db: AsyncSession, token: str, reason: str = "logout") -> None:
        th = hashlib.sha256(token.encode()).hexdigest()
        result = await db.execute(
            select(UserSession).where(
                (UserSession.token_hash == th) | (UserSession.refresh_token_hash == th)
            )
        )
        for session in result.scalars().all():
            session.invalidated_at = datetime.now(timezone.utc)
            session.invalidation_reason = reason

    @staticmethod
    def _as_utc(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            # SQLite commonly returns naive datetimes even for timezone=True columns.
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    async def refresh_tokens(
        db: AsyncSession,
        refresh_token: str,
        ip_address: str,
        user_agent: str,
    ) -> Optional[Tuple["User", str, str, datetime, datetime]]:
        payload = AuthService.decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        rhash = hashlib.sha256(refresh_token.encode()).hexdigest()
        result = await db.execute(
            select(UserSession).where(
                UserSession.refresh_token_hash == rhash,
                UserSession.user_id == user_id,
                UserSession.invalidated_at.is_(None),
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            return None
        now = datetime.now(timezone.utc)
        refresh_expires_at = AuthService._as_utc(session.refresh_expires_at)
        if refresh_expires_at is None or refresh_expires_at < now:
            return None
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user or not user.is_active:
            return None
        access_token, access_expires = AuthService.create_access_token(user)
        new_refresh, refresh_expires = AuthService.create_refresh_token(user)
        session.token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        session.refresh_token_hash = hashlib.sha256(new_refresh.encode()).hexdigest()
        session.expires_at = access_expires
        session.refresh_expires_at = refresh_expires
        session.last_activity_at = now
        session.ip_address = ip_address
        session.user_agent = user_agent
        await db.flush([session])
        return user, access_token, new_refresh, access_expires, refresh_expires

    @staticmethod
    def totp_provisioning_uri(secret: str, account_label: str) -> str:
        return pyotp.TOTP(secret).provisioning_uri(name=account_label, issuer_name=settings.APP_NAME)

    @staticmethod
    def verify_totp(secret: str, code: str) -> bool:
        if not secret or not code:
            return False
        return bool(pyotp.TOTP(secret).verify(code.strip().replace(" ", ""), valid_window=1))

    @staticmethod
    async def enroll_mfa_start(db: AsyncSession, user: "User") -> str:
        """Persist a new secret (not yet enabled) and return otpauth URI for QR display."""
        if user.is_mfa_enabled:
            raise ValueError("MFA is already enabled for this user.")
        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.is_mfa_enabled = False
        await db.flush([user])
        label = user.email or user.username
        return AuthService.totp_provisioning_uri(secret, label)

    @staticmethod
    async def enroll_mfa_finish(db: AsyncSession, user: "User", code: str) -> bool:
        if not user.totp_secret:
            return False
        if not AuthService.verify_totp(user.totp_secret, code):
            return False
        user.is_mfa_enabled = True
        await db.flush([user])
        await AuditService.log(
            db,
            action="MFA_ENABLED",
            record_type="user",
            record_id=user.id,
            module="auth",
            human_description=f"TOTP MFA enabled for user {user.username}",
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
        )
        return True

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user: "User",
        current_password: str,
        new_password: str,
        ip_address: str,
    ) -> tuple[bool, list[str]]:
        """Returns (success, error_messages)."""
        errors: list[str] = []
        if not AuthService.verify_password(current_password, user.hashed_password):
            return False, ["Current password is incorrect."]
        errors = AuthService.validate_password_strength(new_password)
        if errors:
            return False, errors
        if await AuthService.check_password_history(db, user.id, new_password):
            return False, ["You cannot reuse a recent password."]
        user.hashed_password = AuthService.hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        user.must_change_password = False
        user.failed_login_attempts = 0
        user.locked_until = None
        db.add(
            PasswordHistory(
                user_id=user.id,
                hashed_password=user.hashed_password,
                set_at=datetime.now(timezone.utc),
            )
        )
        await AuditService.log(
            db,
            action="PASSWORD_CHANGE",
            record_type="user",
            record_id=user.id,
            module="auth",
            human_description=f"Password changed for user {user.username}",
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            ip_address=ip_address,
        )
        await db.flush([user])
        return True, []

    # ── Permissions ───────────────────────────────────────────────────────────

    @staticmethod
    async def get_user_permissions(db: AsyncSession, user_id: str) -> set[str]:
        result = await db.execute(
            select(Permission.code)
            .join(Permission.roles)
            .join(Role.users)
            .where(User.id == user_id)
        )
        return {row[0] for row in result.fetchall()}

    @staticmethod
    async def has_permission(db: AsyncSession, user_id: str, permission_code: str) -> bool:
        perms = await AuthService.get_user_permissions(db, user_id)
        return permission_code in perms
