from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit.service import AuditService
from app.core.auth.dependencies import get_current_user_with_permission
from app.core.auth.models import PasswordHistory, Permission, Role, Site, User
from app.core.auth.service import AuthService
from app.core.database import get_db

router = APIRouter(prefix="/users", tags=["User Management"])


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=12, max_length=500)
    employee_id: str | None = Field(default=None, max_length=100)
    department: str | None = Field(default=None, max_length=100)
    job_title: str | None = Field(default=None, max_length=150)
    site_id: str | None = Field(default=None, max_length=36)
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    employee_id: str | None = Field(default=None, max_length=100)
    department: str | None = Field(default=None, max_length=100)
    job_title: str | None = Field(default=None, max_length=150)
    site_id: str | None = Field(default=None, max_length=36)
    is_active: bool | None = None


class RoleCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = None
    is_system_role: bool = False
    permission_codes: list[str] = Field(default_factory=list)


class RoleUpdateRequest(BaseModel):
    description: str | None = None
    permission_codes: list[str] | None = None


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "employee_id": user.employee_id,
        "department": user.department,
        "job_title": user.job_title,
        "site_id": user.site_id,
        "is_active": user.is_active,
        "must_change_password": user.must_change_password,
        "is_mfa_enabled": user.is_mfa_enabled,
        "roles": [{"id": r.id, "name": r.name} for r in (user.roles or [])],
    }


async def _active_admin_count(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count(User.id))
        .join(User.roles)
        .where(
            Role.name == "Administrator",
            User.is_active.is_(True),
        )
    )
    return int(result.scalar() or 0)


@router.get("")
async def list_users(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_user_with_permission("admin.users.manage")),
):
    result = await db.execute(select(User).options(selectinload(User.roles)).order_by(User.username.asc()))
    users = result.scalars().all()
    return [_user_payload(u) for u in users]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_with_permission("admin.users.manage")),
):
    password_errors = AuthService.validate_password_strength(body.password)
    if password_errors:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=password_errors)

    if body.site_id:
        site_row = await db.execute(select(Site).where(Site.id == body.site_id, Site.is_active.is_(True)))
        if not site_row.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid site_id.")

    user = User(
        username=body.username.strip(),
        email=body.email.lower(),
        full_name=body.full_name.strip(),
        hashed_password=AuthService.hash_password(body.password),
        employee_id=body.employee_id,
        department=body.department,
        job_title=body.job_title,
        site_id=body.site_id,
        is_active=body.is_active,
        must_change_password=True,
    )
    db.add(user)
    try:
        await db.flush([user])
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username/email already exists.") from exc
    db.add(
        PasswordHistory(
            user_id=user.id,
            hashed_password=user.hashed_password,
            set_at=datetime.now(timezone.utc),
        )
    )

    await AuditService.log(
        db,
        action="CREATE",
        record_type="user",
        record_id=user.id,
        module="auth",
        human_description=f"User {user.username} created by {current_user.username}",
        user_id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        ip_address=request.client.host if request.client else None,
        record_snapshot_after={"username": user.username, "email": user.email, "site_id": user.site_id},
    )
    await db.commit()
    await db.refresh(user)
    return _user_payload(user)


@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    body: UserUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_with_permission("admin.users.manage")),
):
    result = await db.execute(select(User).options(selectinload(User.roles)).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    updates = body.model_dump(exclude_unset=True)
    if "site_id" in updates and updates["site_id"]:
        site_row = await db.execute(select(Site).where(Site.id == updates["site_id"], Site.is_active.is_(True)))
        if not site_row.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid site_id.")

    before = _user_payload(user)
    for key, value in updates.items():
        if key == "email" and value is not None:
            value = value.lower()
        setattr(user, key, value)
    try:
        await db.flush([user])
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Update violates unique constraints.") from exc

    await AuditService.log(
        db,
        action="UPDATE",
        record_type="user",
        record_id=user.id,
        module="auth",
        human_description=f"User {user.username} updated by {current_user.username}",
        user_id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        ip_address=request.client.host if request.client else None,
        record_snapshot_before=before,
        record_snapshot_after=_user_payload(user),
        reason="administrative_update",
    )
    await db.commit()
    await db.refresh(user)
    return _user_payload(user)


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_with_permission("admin.users.manage")),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if not user.is_active:
        return {"message": "User already deactivated."}
    if user.username == "admin":
        admins = await _active_admin_count(db)
        if admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the last active administrator.",
            )

    user.is_active = False
    user.locked_until = datetime.now(timezone.utc)
    await db.flush([user])

    await AuditService.log(
        db,
        action="DEACTIVATE",
        record_type="user",
        record_id=user.id,
        module="auth",
        human_description=f"User {user.username} deactivated by {current_user.username}",
        user_id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        ip_address=request.client.host if request.client else None,
        reason="administrative_deactivation",
    )
    await db.commit()
    return {"message": "User deactivated successfully."}


@router.get("/roles")
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_user_with_permission("admin.roles.manage")),
):
    result = await db.execute(select(Role).options(selectinload(Role.permissions)).order_by(Role.name.asc()))
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "is_system_role": r.is_system_role,
            "permissions": sorted([p.code for p in (r.permissions or [])]),
        }
        for r in rows
    ]


@router.post("/roles", status_code=status.HTTP_201_CREATED)
async def create_role(
    body: RoleCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_with_permission("admin.roles.manage")),
):
    role = Role(name=body.name.strip(), description=body.description, is_system_role=body.is_system_role)
    db.add(role)
    try:
        await db.flush([role])
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role name already exists.") from exc

    if body.permission_codes:
        perm_result = await db.execute(select(Permission).where(Permission.code.in_(body.permission_codes)))
        perms = perm_result.scalars().all()
        missing = sorted(set(body.permission_codes) - {p.code for p in perms})
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown permission codes: {', '.join(missing)}",
            )
        for perm in perms:
            role.permissions.append(perm)
        await db.flush([role])

    await AuditService.log(
        db,
        action="CREATE",
        record_type="role",
        record_id=role.id,
        module="auth",
        human_description=f"Role {role.name} created by {current_user.username}",
        user_id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        ip_address=request.client.host if request.client else None,
        record_snapshot_after={"name": role.name, "permissions": sorted([p.code for p in role.permissions])},
    )
    await db.commit()
    await db.refresh(role)
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_system_role": role.is_system_role,
    }


@router.patch("/roles/{role_id}")
async def update_role(
    role_id: str,
    body: RoleUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_with_permission("admin.roles.manage")),
):
    result = await db.execute(select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

    before_permissions = sorted([p.code for p in role.permissions])
    if body.description is not None:
        role.description = body.description

    if body.permission_codes is not None:
        perm_result = await db.execute(select(Permission).where(Permission.code.in_(body.permission_codes)))
        perms = perm_result.scalars().all()
        missing = sorted(set(body.permission_codes) - {p.code for p in perms})
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown permission codes: {', '.join(missing)}",
            )
        role.permissions = list(perms)
        await db.flush([role])

    await AuditService.log(
        db,
        action="UPDATE",
        record_type="role",
        record_id=role.id,
        module="auth",
        human_description=f"Role {role.name} updated by {current_user.username}",
        user_id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        ip_address=request.client.host if request.client else None,
        record_snapshot_before={"permissions": before_permissions},
        record_snapshot_after={"permissions": sorted([p.code for p in role.permissions])},
        reason="administrative_update",
    )
    await db.commit()
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_system_role": role.is_system_role,
        "permissions": sorted([p.code for p in role.permissions]),
    }


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_with_permission("admin.roles.manage")),
):
    result = await db.execute(select(Role).options(selectinload(Role.users)).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    if role.is_system_role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="System roles cannot be deleted.")
    if role.users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role is currently assigned to users; revoke assignments first.",
        )

    await AuditService.log(
        db,
        action="DELETE",
        record_type="role",
        record_id=role.id,
        module="auth",
        human_description=f"Role {role.name} deleted by {current_user.username}",
        user_id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        ip_address=request.client.host if request.client else None,
        reason="administrative_delete",
    )
    await db.delete(role)
    await db.commit()
    return {"message": "Role deleted successfully."}


@router.get("/permissions")
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_user_with_permission("admin.roles.manage")),
):
    result = await db.execute(select(Permission).order_by(Permission.code.asc()))
    return [
        {
            "id": p.id,
            "code": p.code,
            "module": p.module,
            "resource": p.resource,
            "action": p.action,
            "description": p.description,
        }
        for p in result.scalars().all()
    ]


@router.post("/{user_id}/roles/{role_id}")
async def assign_role(
    user_id: str,
    role_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_with_permission("admin.roles.manage")),
):
    u_result = await db.execute(select(User).options(selectinload(User.roles)).where(User.id == user_id))
    user = u_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    r_result = await db.execute(select(Role).where(Role.id == role_id))
    role = r_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

    if any(r.id == role.id for r in user.roles):
        return {"message": "Role already assigned."}

    user.roles.append(role)
    await db.flush([user])
    await AuditService.log(
        db,
        action="ROLE_ASSIGN",
        record_type="user_role",
        record_id=user.id,
        module="auth",
        human_description=f"Assigned role {role.name} to user {user.username}",
        user_id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"message": "Role assigned successfully."}


@router.delete("/{user_id}/roles/{role_id}")
async def revoke_role(
    user_id: str,
    role_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_with_permission("admin.roles.manage")),
):
    u_result = await db.execute(select(User).options(selectinload(User.roles)).where(User.id == user_id))
    user = u_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    role = next((r for r in user.roles if r.id == role_id), None)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role assignment not found.")
    if role.is_system_role and user.username == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke the system admin role from admin user.",
        )
    if role.name == "Administrator":
        admins = await _active_admin_count(db)
        if user.is_active and admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot revoke role from the last active administrator.",
            )

    user.roles = [r for r in user.roles if r.id != role_id]
    await db.flush([user])
    await AuditService.log(
        db,
        action="ROLE_REVOKE",
        record_type="user_role",
        record_id=user.id,
        module="auth",
        human_description=f"Revoked role {role.name} from user {user.username}",
        user_id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"message": "Role revoked successfully."}
