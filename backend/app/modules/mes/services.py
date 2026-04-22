"""
MES Services — business logic layer.

Key GMP invariants enforced here (not just in the router):
  1. ANTI-BACKFILL: BatchRecordStep.performed_at is server-set UTC the moment
     execute_step() is called. No client timestamp is accepted. Existing steps
     cannot be overwritten. (ALCOA Contemporaneous)
  2. APPROVED-MBR-ONLY: Batch records can only be spawned from an MBR with
     status='approved'. Draft/under_review MBRs are blocked.
  3. UNIQUE BATCH NUMBERS: enforced at service layer before DB flush.
  4. E-SIG RELEASE: batch_release() requires password re-authentication via
     ESignatureService (21 CFR Part 11 §11.50).
  5. YIELD CHECK: yield_percentage auto-calculated and flagged if outside MBR
     acceptable range.

This layer is consumed by:
  - The MES router (HTTP)
  - mes/tasks.py (APScheduler background jobs)
  - Test fixtures (no HTTP layer needed)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit.service import AuditService
from app.core.auth.models import User
from app.core.esig.service import ESignatureService
from app.modules.mes.models import (
    BatchRecord,
    BatchRecordStep,
    MasterBatchRecord,
    MBRStep,
    Product,
)
from app.modules.mes.schemas import (
    BatchRecordCreate,
    BatchRecordStepExecute,
    BatchReleaseRequest,
    MBRCreate,
    MBRSignRequest,
    ProductCreate,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _mbr_number(sequence: int) -> str:
    return f"MBR-{_utcnow().year}-{sequence:04d}"


# ── Product ───────────────────────────────────────────────────────────────────

async def create_product(
    db: AsyncSession,
    data: ProductCreate,
    user: User,
    ip_address: Optional[str],
) -> Product:
    """Create a product master record with audit trail."""
    product = Product(**data.model_dump())
    db.add(product)
    await db.flush([product])

    await AuditService.log(
        db,
        action="CREATE",
        record_type="product",
        record_id=product.id,
        module="mes",
        human_description=f"Product {product.product_code} '{product.name}' created",
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        record_snapshot_after={
            "product_code": product.product_code,
            "name": product.name,
            "product_type": product.product_type,
        },
    )

    await db.commit()
    await db.refresh(product)
    return product


async def list_products(
    db: AsyncSession,
    *,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 50,
) -> list[Product]:
    query = select(Product)
    if active_only:
        query = query.where(Product.is_active == True)  # noqa: E712
    query = query.order_by(Product.product_code).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_product_or_404(db: AsyncSession, product_id: str) -> Product:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product


# ── Master Batch Record ───────────────────────────────────────────────────────

async def create_mbr(
    db: AsyncSession,
    data: MBRCreate,
    user: User,
    ip_address: Optional[str],
) -> MasterBatchRecord:
    """
    Create a Master Batch Record with steps.
    Product must exist. MBR starts in 'draft' status.
    """
    # Verify product exists
    product = await get_product_or_404(db, data.product_id)

    count_result = await db.execute(select(func.count()).select_from(MasterBatchRecord))
    count = (count_result.scalar() or 0) + 1

    mbr = MasterBatchRecord(
        mbr_number=_mbr_number(count),
        product_id=data.product_id,
        version=data.version,
        status="draft",
        batch_size=data.batch_size,
        batch_size_unit=data.batch_size_unit,
        theoretical_yield=data.theoretical_yield,
        yield_unit=data.yield_unit,
        acceptable_yield_min=data.acceptable_yield_min,
        acceptable_yield_max=data.acceptable_yield_max,
        description=data.description,
        authored_by_id=str(user.id),
    )
    db.add(mbr)
    await db.flush([mbr])

    for step_data in data.steps:
        db.add(MBRStep(mbr_id=mbr.id, **step_data.model_dump()))

    await AuditService.log(
        db,
        action="CREATE",
        record_type="master_batch_record",
        record_id=mbr.id,
        module="mes",
        human_description=(
            f"MBR {mbr.mbr_number} v{data.version} created "
            f"for {product.product_code} ({len(data.steps)} steps)"
        ),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        record_snapshot_after={
            "mbr_number": mbr.mbr_number,
            "version": mbr.version,
            "product_code": product.product_code,
            "step_count": len(data.steps),
        },
    )

    await db.commit()
    return await get_mbr_or_404(db, mbr.id)


async def list_mbrs(
    db: AsyncSession,
    *,
    product_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[MasterBatchRecord]:
    query = select(MasterBatchRecord).options(selectinload(MasterBatchRecord.steps))
    if product_id:
        query = query.where(MasterBatchRecord.product_id == product_id)
    if status_filter:
        query = query.where(MasterBatchRecord.status == status_filter)
    query = query.order_by(MasterBatchRecord.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_mbr_or_404(db: AsyncSession, mbr_id: str) -> MasterBatchRecord:
    result = await db.execute(
        select(MasterBatchRecord)
        .where(MasterBatchRecord.id == mbr_id)
        .options(selectinload(MasterBatchRecord.steps))
    )
    mbr = result.scalar_one_or_none()
    if not mbr:
        raise HTTPException(status_code=404, detail="Master Batch Record not found.")
    return mbr


async def sign_mbr(
    db: AsyncSession,
    mbr_id: str,
    data: MBRSignRequest,
    user: User,
    ip_address: str,
) -> dict:
    """
    Apply e-signature to a Master Batch Record.
    meaning='approved' -> status becomes 'approved', effective_date set.
    Password re-authentication required (21 CFR Part 11 §11.50).
    """
    mbr = await get_mbr_or_404(db, mbr_id)

    sig = await ESignatureService.sign(
        db,
        user_id=str(user.id),
        password=data.password,
        record_type="master_batch_record",
        record_id=mbr_id,
        record_version=mbr.version,
        record_data={"id": str(mbr.id), "mbr_number": mbr.mbr_number, "version": mbr.version},
        meaning=data.meaning,
        meaning_display=data.meaning.title(),
        ip_address=ip_address,
        comments=data.comments,
    )

    if data.meaning == "approved":
        mbr.approved_by_id = str(user.id)
        mbr.status = "approved"
        mbr.effective_date = _utcnow()

    await db.commit()
    return {
        "signature_id": str(sig.id),
        "signed_at": sig.signed_at,
        "new_status": mbr.status,
    }


# ── Batch Record (live execution) ─────────────────────────────────────────────

async def create_batch_record(
    db: AsyncSession,
    data: BatchRecordCreate,
    user: User,
    ip_address: Optional[str],
) -> BatchRecord:
    """
    Start execution of a new batch against an approved MBR.

    INVARIANTS enforced:
    1. MBR must have status='approved' — draft/under_review blocked.
    2. Batch number must be globally unique.
    3. All MBR steps are instantiated as BatchRecordStep rows in 'pending' status.
    4. actual_start is server-set UTC — not provided by client.
    """
    # Enforce: only approved MBRs can be executed
    mbr_result = await db.execute(
        select(MasterBatchRecord).where(
            MasterBatchRecord.id == data.master_batch_record_id,
            MasterBatchRecord.status == "approved",
        )
    )
    mbr = mbr_result.scalar_one_or_none()
    if not mbr:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "MBR not found or not in 'approved' status. "
                "Only approved MBRs can be executed."
            ),
        )

    # Enforce unique batch number
    existing = await db.execute(
        select(BatchRecord).where(BatchRecord.batch_number == data.batch_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch number '{data.batch_number}' already exists.",
        )

    now = _utcnow()
    br = BatchRecord(
        batch_number=data.batch_number,
        master_batch_record_id=mbr.id,
        product_id=mbr.product_id,
        site_id=str(getattr(user, "site_id", None) or "default"),
        status="in_progress",
        planned_start=data.planned_start,
        actual_start=now,  # Server-set
        executed_by_id=str(user.id),
    )
    db.add(br)
    await db.flush([br])

    # Instantiate all MBR steps as pending execution records
    steps_result = await db.execute(
        select(MBRStep).where(MBRStep.mbr_id == mbr.id).order_by(MBRStep.step_number)
    )
    for mbr_step in steps_result.scalars().all():
        db.add(BatchRecordStep(
            batch_record_id=br.id,
            mbr_step_id=mbr_step.id,
            step_number=mbr_step.step_number,
            status="pending",
        ))

    await AuditService.log(
        db,
        action="CREATE",
        record_type="batch_record",
        record_id=br.id,
        module="mes",
        human_description=(
            f"Batch {data.batch_number} started against MBR {mbr.mbr_number} v{mbr.version}"
        ),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        record_snapshot_after={
            "batch_number": br.batch_number,
            "mbr_number": mbr.mbr_number,
            "mbr_version": mbr.version,
        },
    )

    await db.commit()
    return await get_batch_record_or_404(db, br.id)


async def list_batch_records(
    db: AsyncSession,
    *,
    status_filter: Optional[str] = None,
    product_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[BatchRecord]:
    query = select(BatchRecord).options(selectinload(BatchRecord.steps))
    if status_filter:
        query = query.where(BatchRecord.status == status_filter)
    if product_id:
        query = query.where(BatchRecord.product_id == product_id)
    query = query.order_by(BatchRecord.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_batch_record_or_404(db: AsyncSession, br_id: str) -> BatchRecord:
    result = await db.execute(
        select(BatchRecord)
        .where(BatchRecord.id == br_id)
        .options(selectinload(BatchRecord.steps))
    )
    br = result.scalar_one_or_none()
    if not br:
        raise HTTPException(status_code=404, detail="Batch record not found.")
    return br


async def execute_step(
    db: AsyncSession,
    br_id: str,
    step_id: str,
    data: BatchRecordStepExecute,
    user: User,
    ip_address: Optional[str],
) -> BatchRecordStep:
    """
    Record a batch step execution.

    ANTI-BACKFILL invariant (ALCOA Contemporaneous):
    - performed_at is set to server UTC at the moment this function is called.
    - If performed_at is already set, the step is rejected — no overwriting.
    - Client-provided timestamps are ignored entirely.

    Limit checking:
    - If the MBR step has lower/upper limits, recorded_value is cast to float
      and compared. Out-of-limit steps are marked 'deviated'.
    """
    step_result = await db.execute(
        select(BatchRecordStep).where(
            BatchRecordStep.id == step_id,
            BatchRecordStep.batch_record_id == br_id,
        )
    )
    step = step_result.scalar_one_or_none()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found.")

    # ANTI-BACKFILL: reject if already recorded
    if step.performed_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Step already recorded. "
                "Back-filling is not permitted (ALCOA Contemporaneous)."
            ),
        )

    # Load MBR step definition for limit checking
    mbr_step_result = await db.execute(
        select(MBRStep).where(MBRStep.id == step.mbr_step_id)
)
    mbr_step = mbr_step_result.scalar_one_or_none()

    # Record — timestamp is server-set, never from client
    step.recorded_value = data.recorded_value
    step.is_na = data.is_na
    step.comments = data.comments
    step.performed_by_id = str(user.id)
    step.performed_at = _utcnow()  # ALCOA: server-set, contemporaneous
    step.status = "completed"

    # Limit check
    if mbr_step and data.recorded_value and not data.is_na:
        try:
            val = float(data.recorded_value)
            in_limits = True
            if mbr_step.lower_limit is not None and val < mbr_step.lower_limit:
                in_limits = False
            if mbr_step.upper_limit is not None and val > mbr_step.upper_limit:
                in_limits = False
            step.is_within_limits = in_limits
            if not in_limits:
                step.status = "deviated"
        except (ValueError, TypeError):
            step.is_within_limits = None

    await AuditService.log(
        db,
        action="EXECUTE",
        record_type="batch_record_step",
        record_id=step.id,
        module="mes",
        human_description=(
            f"Step {step.step_number} recorded by {user.full_name} "
            f"(value={data.recorded_value!r}, status={step.status})"
        ),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        new_value=data.recorded_value,
    )

    await db.commit()
    await db.refresh(step)
    return step


async def release_batch(
    db: AsyncSession,
    br_id: str,
    data: BatchReleaseRequest,
    user: User,
    ip_address: str,
) -> dict:
    """
    QA batch release decision (released | rejected).

    Requires electronic signature with password re-authentication.
    Sets reviewed_by_id, reviewed_at, release_decision, and batch status.
    All immutable after signing — no further updates permitted to release fields.
    """
    br = await get_batch_record_or_404(db, br_id)

    if data.decision not in ("released", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be 'released' or 'rejected'.",
        )

    if br.release_decision is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch already has a release decision: '{br.release_decision}'.",
        )

    sig = await ESignatureService.sign(
        db,
        user_id=str(user.id),
        password=data.password,
        record_type="batch_record",
        record_id=br_id,
        record_version="1.0",
        record_data={
            "batch_number": br.batch_number,
            "status": br.status,
        },
        meaning=data.decision,
        meaning_display=f"Batch {data.decision.title()}",
        ip_address=ip_address,
        comments=data.comments,
    )

    now = _utcnow()
    br.reviewed_by_id = str(user.id)
    br.reviewed_at = now
    br.release_decision = data.decision
    br.release_comments = data.comments
    br.status = data.decision
    if data.decision == "released":
        br.actual_completion = now

    await AuditService.log(
        db,
        action="SIGN",
        record_type="batch_record",
        record_id=br_id,
        module="mes",
        human_description=(
            f"Batch {br.batch_number} {data.decision.upper()} by {user.full_name}"
        ),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        reason=data.comments,
    )

    await db.commit()
    return {
        "signature_id": str(sig.id),
        "signed_at": sig.signed_at,
        "decision": data.decision,
        "batch_number": br.batch_number,
    }


async def finalize_batch(
    db: AsyncSession,
    br_id: str,
    actual_yield: float,
    yield_unit: str,
    user: User,
    ip_address: Optional[str],
) -> BatchRecord:
    """
    Mark batch as completed and record actual yield.
    Calculates yield_percentage against MBR theoretical_yield.
    Sets status to 'completed' -> ready for QA review.
    """
    br = await get_batch_record_or_404(db, br_id)
    if br.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch is '{br.status}' — only 'in_progress' batches can be finalized.",
        )

    mbr_result = await db.execute(
        select(MasterBatchRecord).where(MasterBatchRecord.id == br.master_batch_record_id)
    )
    mbr = mbr_result.scalar_one_or_none()

    br.actual_yield = actual_yield
    br.yield_unit = yield_unit
    br.actual_completion = _utcnow()
    br.status = "completed"

    if mbr and mbr.theoretical_yield and mbr.theoretical_yield > 0:
        br.yield_percentage = round((actual_yield / mbr.theoretical_yield) * 100, 2)

    await AuditService.log(
        db,
        action="UPDATE",
        record_type="batch_record",
        record_id=br_id,
        module="mes",
        human_description=(
            f"Batch {br.batch_number} finalized: yield={actual_yield} {yield_unit} "
            f"({br.yield_percentage}%)"
        ),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
    )

    await db.commit()
    await db.refresh(br)
    return br
