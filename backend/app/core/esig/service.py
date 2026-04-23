"""
Electronic Signature Service — 21 CFR Part 11.
Re-authenticates the user at point of signing, generates a cryptographic token,
hashes the record content, and writes an immutable signature record.
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.esig.models import ElectronicSignature, SignatureRequirement
from app.core.auth.models import User, Role, user_roles
from app.core.auth.service import AuthService
from app.core.audit.service import AuditService
from app.core.config import settings
from fastapi import HTTPException, status


class ESignatureService:

    @staticmethod
    def _hash_record(record_data: dict) -> str:
        """SHA-256 of the canonical JSON representation of the record at signing time."""
        canonical = json.dumps(record_data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    @staticmethod
    def _create_signature_token(user: User, record_type: str, record_id: str,
                                 meaning: str, record_hash: str, signed_at: datetime) -> str:
        """JWT signed with platform secret — provides cryptographic non-repudiation."""
        payload = {
            "sub": user.id,
            "username": user.username,
            "record_type": record_type,
            "record_id": record_id,
            "meaning": meaning,
            "record_hash": record_hash,
            "signed_at": signed_at.isoformat(),
            "iss": "gmp-platform",
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    async def sign(
        db: AsyncSession,
        *,
        user_id: str,
        username: str | None = None,
        password: str,          # Re-authentication required per 21 CFR Part 11
        record_type: str,
        record_id: str,
        record_version: str,
        record_data: dict,       # Full record snapshot at time of signing
        meaning: str,
        meaning_display: str,
        ip_address: str,
        comments: str | None = None,
    ) -> ElectronicSignature:
        """
        Apply an electronic signature to a GMP record.
        Steps:
          1. Re-authenticate the user (password required every time)
          2. Hash the record content
          3. Create cryptographic signature token
          4. Write immutable ElectronicSignature record
          5. Write audit event
        """
        # Step 1 — Re-authenticate (Part 11 §11.200(a)(1))
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        if username is not None and user.username != username:
            await AuditService.log(
                db, action="SIGN_FAILED", record_type=record_type, record_id=record_id,
                module="esig", human_description=f"Failed signature attempt by {user.full_name} — username mismatch",
                user_id=user.id, username=user.username, full_name=user.full_name, ip_address=ip_address,
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Signature failed: username does not match authenticated user.")

        if not AuthService.verify_password(password, user.hashed_password):
            await AuditService.log(
                db, action="SIGN_FAILED", record_type=record_type, record_id=record_id,
                module="esig", human_description=f"Failed signature attempt by {user.full_name} — wrong password",
                user_id=user.id, username=user.username, full_name=user.full_name, ip_address=ip_address,
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Signature failed: incorrect password.")

        roles_result = await db.execute(
            select(Role.name)
            .join(user_roles, Role.id == user_roles.c.role_id)
            .where(user_roles.c.user_id == user.id)
            .order_by(Role.name.asc())
        )
        role_at_time = ", ".join([r[0] for r in roles_result.all()]) or "Unassigned"

        # Step 2 — Hash the record
        record_hash = ESignatureService._hash_record(record_data)
        signed_at = datetime.now(timezone.utc)

        # Step 3 — Cryptographic token
        token = ESignatureService._create_signature_token(
            user, record_type, record_id, meaning, record_hash, signed_at
        )

        # Step 4 — Write signature record
        sig = ElectronicSignature(
            signed_by_id=user.id,
            signed_by_username=user.username,
            signed_by_full_name=user.full_name,
            record_type=record_type,
            record_id=record_id,
            record_version=record_version,
            record_hash=record_hash,
            meaning=meaning,
            meaning_display=meaning_display,
            signed_at=signed_at,
            auth_method="password",
            auth_verified=True,
            signature_token=token,
            ip_address=ip_address,
            comments=comments,
        )
        db.add(sig)
        await db.flush([sig])

        # Step 5 — Audit
        await AuditService.log_signature(
            db, record_type=record_type, record_id=record_id, module="esig",
            meaning=meaning, user_id=user.id, username=user.username,
            full_name=user.full_name, role_at_time=role_at_time, ip_address=ip_address,
        )

        return sig

    @staticmethod
    async def get_required_signatures(
        db: AsyncSession, record_type: str, from_state: str, to_state: str
    ) -> list[SignatureRequirement]:
        result = await db.execute(
            select(SignatureRequirement).where(
                SignatureRequirement.record_type == record_type,
                SignatureRequirement.from_state == from_state,
                SignatureRequirement.to_state == to_state,
                SignatureRequirement.is_active == True,
            )
        )
        return result.scalars().all()

    @staticmethod
    async def get_record_signatures(
        db: AsyncSession, record_type: str, record_id: str
    ) -> list[ElectronicSignature]:
        result = await db.execute(
            select(ElectronicSignature).where(
                ElectronicSignature.record_type == record_type,
                ElectronicSignature.record_id == record_id,
            ).order_by(ElectronicSignature.signed_at)
        )
        return result.scalars().all()
