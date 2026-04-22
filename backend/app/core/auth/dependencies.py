"""
FastAPI dependencies for authentication and authorisation.
Import these in every router — never decode tokens manually in route handlers.
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.auth.models import User
from app.core.auth.service import AuthService

bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validates the bearer token and returns the authenticated User object."""
    payload = AuthService.decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    result = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.id == payload["sub"])
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or disabled.",
        )
    return user


def get_current_user_with_permission(permission_code: str):
    """
    Factory: returns a dependency that checks a specific permission.
    Usage: Depends(get_current_user_with_permission("qms:capa:approve"))
    """
    async def _check(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        has = await AuthService.has_permission(db, current_user.id, permission_code)
        if not has:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission_code}",
            )
        return current_user
    return _check


def get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"
