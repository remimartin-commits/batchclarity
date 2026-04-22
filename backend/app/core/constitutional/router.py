from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.auth.dependencies import get_current_user
from app.core.auth.models import User
from app.core.constitutional.service import get_constitutional_rules

router = APIRouter(prefix="/constitutional", tags=["Constitutional"])


@router.get("/rules")
async def list_constitutional_rules(
    current_user: User = Depends(get_current_user),
):
    # Endpoint is authenticated because constitutional constraints are operationally sensitive.
    _ = current_user
    return get_constitutional_rules()

