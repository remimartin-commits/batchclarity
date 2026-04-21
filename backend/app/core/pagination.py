"""Shared pagination utilities — GMP Platform.

Provides a consistent pagination pattern across all list endpoints.

Usage:
    from app.core.pagination import paginate, PaginatedResponse, PaginationParams

    @router.get("/items", response_model=PaginatedResponse[ItemOut])
    async def list_items(
        p: PaginationParams = Depends(),
        db: AsyncSession = Depends(get_db),
    ):
        query = select(Item).order_by(Item.created_at.desc())
        return await paginate(db, query, p, ItemOut)
"""
from typing import Generic, TypeVar, Type, Sequence
from math import ceil

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

T = TypeVar("T")


class PaginationParams:
    """FastAPI dependency for pagination query parameters."""

    def __init__(
        self,
        skip: int = Query(default=0, ge=0, description="Number of records to skip"),
        limit: int = Query(
            default=50, ge=1, le=500, description="Maximum records to return (max 500)"
        ),
    ):
        self.skip = skip
        self.limit = limit

    @property
    def page(self) -> int:
        """1-based page number derived from skip/limit."""
        return (self.skip // self.limit) + 1


class PaginationMeta(BaseModel):
    """Metadata returned alongside paginated results."""

    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response envelope."""

    items: list[T]
    meta: PaginationMeta

    model_config = {"arbitrary_types_allowed": True}


async def paginate(
    db: AsyncSession,
    query: Select,
    params: PaginationParams,
    schema: Type[T] | None = None,
) -> PaginatedResponse:
    """Execute a paginated SQLAlchemy query and return a PaginatedResponse.

    Args:
        db: AsyncSession
        query: A SQLAlchemy Select statement (without offset/limit applied)
        params: PaginationParams dependency
        schema: Optional Pydantic schema to validate results through.
                If None, raw ORM objects are returned in items.

    Returns:
        PaginatedResponse with items and meta.
    """
    # Count total matching rows
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Fetch paginated rows
    paginated_query = query.offset(params.skip).limit(params.limit)
    result = await db.execute(paginated_query)
    rows = result.scalars().all()

    # Optionally validate through Pydantic schema
    if schema is not None:
        items = [schema.model_validate(row) for row in rows]
    else:
        items = list(rows)

    total_pages = ceil(total / params.limit) if params.limit > 0 else 1

    return PaginatedResponse(
        items=items,
        meta=PaginationMeta(
            total=total,
            page=params.page,
            page_size=params.limit,
            total_pages=total_pages,
            has_next=params.skip + params.limit < total,
            has_previous=params.skip > 0,
        ),
    )


def apply_pagination(query: Select, params: PaginationParams) -> Select:
    """Apply offset/limit to a query without fetching count.

    Use this when you don't need total count metadata — slightly more efficient.
    """
    return query.offset(params.skip).limit(params.limit)
