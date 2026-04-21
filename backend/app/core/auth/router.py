from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.config import settings
from app.core.auth.service import AuthService
from app.core.auth.dependencies import get_current_user
from app.core.auth.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer = HTTPBearer()


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=500)
    totp_code: str | None = Field(None, max_length=16, description="Required when MFA is enabled")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginResponse(BaseModel):
    tokens: TokenResponse
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=500)
    new_password: str = Field(..., min_length=1, max_length=500)


class MfaVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=16)


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    user = await AuthService.authenticate_user(db, body.username, body.password, ip)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or account locked.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled.")

    if user.is_mfa_enabled:
        if not body.totp_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA code is required for this account.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not AuthService.verify_totp(user.totp_secret or "", body.totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    access_token, access_expires = AuthService.create_access_token(user)
    refresh_token, refresh_expires = AuthService.create_refresh_token(user)

    await AuthService.create_session(
        db,
        user,
        access_token,
        access_expires,
        refresh_token,
        refresh_expires,
        ip,
        user_agent,
    )

    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return LoginResponse(
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        ),
        user={
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "must_change_password": user.must_change_password,
            "is_mfa_enabled": user.is_mfa_enabled,
        },
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(body: RefreshRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    row = await AuthService.refresh_tokens(db, body.refresh_token.strip(), ip, user_agent)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    _user, access_token, refresh_token, _access_exp, _refresh_exp = row
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    await AuthService.invalidate_session(db, credentials.credentials, reason="logout")
    return {"message": "Logged out successfully."}


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    ok, errors = await AuthService.change_password(
        db, current_user, body.current_password, body.new_password, ip
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=errors)
    return {"message": "Password updated successfully."}


@router.post("/mfa/enroll")
async def mfa_enroll(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        uri = await AuthService.enroll_mfa_start(db, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"provisioning_uri": uri}


@router.post("/mfa/verify")
async def mfa_verify(
    body: MfaVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await AuthService.enroll_mfa_finish(db, current_user, body.code)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code. MFA was not enabled.",
        )
    return {"message": "MFA enabled successfully.", "is_mfa_enabled": True}


@router.get("/me")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    permissions = await AuthService.get_user_permissions(db, current_user.id)
    roles = [
        {"id": r.id, "name": r.name, "description": r.description}
        for r in (current_user.roles or [])
    ]
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "must_change_password": current_user.must_change_password,
        "is_mfa_enabled": current_user.is_mfa_enabled,
        "site_id": current_user.site_id,
        "roles": roles,
        "permissions": sorted(permissions),
    }
