"""MES API — Products, Master Batch Records, Electronic Batch Records."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.auth.dependencies import get_current_user, get_client_ip
from app.core.auth.models import User
from app.core.audit.service import AuditService
from app.core.esig.service import ESignatureService
from app.modules.mes.models import (
    Product, MasterBatchRecord, MBRStep, BatchRecord, BatchRecordStep,
)
from app.modules.mes.schemas import (
    ProductCreate, ProductOut,
    MBRCreate, MBROut, MBRSignRequest,
    BatchRecordCreate, BatchRecordOut, BatchRecordStepExecute,
    BatchRecordStepOut, BatchReleaseRequest,
)

router = APIRouter(prefix="/mes", tags=["MES"])


# ── Products ──────────────────────────────────────────────────────────────────

@router.post("/products", response_model=ProductOut, status_code=201)
async def create_product(
    body: ProductCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = Product(**body.model_dump())
    db.add(product)
    await db.flush([product])
    await AuditService.log(
        db, action="CREATE", record_type="product", record_id=product.id,
        module="mes",
        human_description=f"Product {product.product_code} '{product.name}' created",
        user_id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, ip_address=get_client_ip(request),
    )
    await db.refresh(product)
    return product


@router.get("/products", response_model=list[ProductOut])
async def list_products(
    skip: int = 0, limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product).where(Product.is_active == True)
        .order_by(Product.product_code).offset(skip).limit(limit)
    )
    return result.scalars().all()


# ── Master Batch Records ──────────────────────────────────────────────────────

@router.post("/mbrs", response_model=MBROut, status_code=201)
async def create_mbr(
    body: MBRCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check product exists
    prod_result = await db.execute(select(Product).where(Product.id == body.product_id))
    product = prod_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    count_result = await db.execute(select(func.count()).select_from(MasterBatchRecord))
    count = (count_result.scalar() or 0) + 1
    mbr_number = f"MBR-{datetime.now(timezone.utc).year}-{count:04d}"

    mbr = MasterBatchRecord(
        mbr_number=mbr_number,
        product_id=body.product_id,
        version=body.version,
        status="draft",
        batch_size=body.batch_size,
        batch_size_unit=body.batch_size_unit,
        theoretical_yield=body.theoretical_yield,
        yield_unit=body.yield_unit,
        acceptable_yield_min=body.acceptable_yield_min,
        acceptable_yield_max=body.acceptable_yield_max,
        description=body.description,
        authored_by_id=current_user.id,
    )
    db.add(mbr)
    await db.flush([mbr])

    for step_data in body.steps:
        step = MBRStep(mbr_id=mbr.id, **step_data.model_dump())
        db.add(step)

    await AuditService.log(
        db, action="CREATE", record_type="master_batch_record", record_id=mbr.id,
        module="mes",
        human_description=f"MBR {mbr_number} v{body.version} created for {product.product_code}",
        user_id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, ip_address=get_client_ip(request),
    )
    await db.refresh(mbr)
    return mbr


@router.get("/mbrs", response_model=list[MBROut])
async def list_mbrs(
    product_id: str | None = None,
    status_filter: str | None = None,
    skip: int = 0, limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(MasterBatchRecord)
    if product_id:
        query = query.where(MasterBatchRecord.product_id == product_id)
    if status_filter:
        query = query.where(MasterBatchRecord.status == status_filter)
    result = await db.execute(
        query.order_by(MasterBatchRecord.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/mbrs/{mbr_id}", response_model=MBROut)
async def get_mbr(
    mbr_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MasterBatchRecord).where(MasterBatchRecord.id == mbr_id))
    mbr = result.scalar_one_or_none()
    if not mbr:
        raise HTTPException(status_code=404, detail="Master Batch Record not found.")
    return mbr


@router.post("/mbrs/{mbr_id}/sign")
async def sign_mbr(
    mbr_id: str,
    body: MBRSignRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MasterBatchRecord).where(MasterBatchRecord.id == mbr_id))
    mbr = result.scalar_one_or_none()
    if not mbr:
        raise HTTPException(status_code=404, detail="MBR not found.")

    sig = await ESignatureService.sign(
        db,
        user_id=current_user.id,
        password=body.password,
        record_type="master_batch_record",
        record_id=mbr_id,
        record_version=mbr.version,
        record_data={"id": mbr.id, "mbr_number": mbr.mbr_number, "version": mbr.version},
        meaning=body.meaning,
        meaning_display=body.meaning.title(),
        ip_address=get_client_ip(request),
        comments=body.comments,
    )
    now = datetime.now(timezone.utc)
    if body.meaning == "approved":
        mbr.approved_by_id = current_user.id
        mbr.status = "approved"
        mbr.effective_date = now

    return {"signature_id": sig.id, "signed_at": sig.signed_at, "new_status": mbr.status}


# ── Batch Records (live execution) ────────────────────────────────────────────

@router.post("/batch-records", response_model=BatchRecordOut, status_code=201)
async def create_batch_record(
    body: BatchRecordCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mbr_result = await db.execute(
        select(MasterBatchRecord).where(
            MasterBatchRecord.id == body.master_batch_record_id,
            MasterBatchRecord.status == "approved",
        )
    )
    mbr = mbr_result.scalar_one_or_none()
    if not mbr:
        raise HTTPException(
            status_code=400,
            detail="MBR not found or not in 'approved' status. Only approved MBRs can be executed.",
        )

    # Check batch number is unique
    existing = await db.execute(
        select(BatchRecord).where(BatchRecord.batch_number == body.batch_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Batch number '{body.batch_number}' already exists.")

    now = datetime.now(timezone.utc)
    br = BatchRecord(
        batch_number=body.batch_number,
        master_batch_record_id=mbr.id,
        product_id=mbr.product_id,
        site_id=current_user.site_id or "default",
        status="in_progress",
        planned_start=body.planned_start,
        actual_start=now,
        executed_by_id=current_user.id,
    )
    db.add(br)
    await db.flush([br])

    # Create step execution records from MBR steps
    steps_result = await db.execute(
        select(MBRStep).where(MBRStep.mbr_id == mbr.id).order_by(MBRStep.step_number)
    )
    for mbr_step in steps_result.scalars().all():
        step = BatchRecordStep(
            batch_record_id=br.id,
            mbr_step_id=mbr_step.id,
            step_number=mbr_step.step_number,
            status="pending",
        )
        db.add(step)

    await AuditService.log(
        db, action="CREATE", record_type="batch_record", record_id=br.id,
        module="mes",
        human_description=f"Batch {body.batch_number} started against MBR {mbr.mbr_number}",
        user_id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, ip_address=get_client_ip(request),
    )
    await db.refresh(br)
    return br


@router.get("/batch-records", response_model=list[BatchRecordOut])
async def list_batch_records(
    status_filter: str | None = None,
    product_id: str | None = None,
    skip: int = 0, limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(BatchRecord)
    if status_filter:
        query = query.where(BatchRecord.status == status_filter)
    if product_id:
        query = query.where(BatchRecord.product_id == product_id)
    result = await db.execute(
        query.order_by(BatchRecord.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/batch-records/{br_id}", response_model=BatchRecordOut)
async def get_batch_record(
    br_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BatchRecord).where(BatchRecord.id == br_id))
    br = result.scalar_one_or_none()
    if not br:
        raise HTTPException(status_code=404, detail="Batch record not found.")
    return br


@router.patch("/batch-records/{br_id}/steps/{step_id}", response_model=BatchRecordStepOut)
async def execute_step(
    br_id: str,
    step_id: str,
    body: BatchRecordStepExecute,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute / record a batch record step. Timestamp is server-set (ALCOA Contemporaneous)."""
    result = await db.execute(
        select(BatchRecordStep).where(
            BatchRecordStep.id == step_id,
            BatchRecordStep.batch_record_id == br_id,
        )
    )
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found.")

    if step.performed_at is not None:
        raise HTTPException(
            status_code=400,
            detail="Step already recorded. Back-filling is not permitted (ALCOA Contemporaneous).",
        )

    mbr_step_result = await db.execute(
        select(MBRStep).where(MBRStep.id == step.mbr_step_id)
    )
    mbr_step = mbr_step_result.scalar_one_or_none()

    step.recorded_value = body.recorded_value
    step.is_na = body.is_na
    step.comments = body.comments
    step.performed_by_id = current_user.id
    step.performed_at = datetime.now(timezone.utc)  # Server-set, never client-provided
    step.status = "completed"

    # Check limits if applicable
    if mbr_step and body.recorded_value and not body.is_na:
        try:
            val = float(body.recorded_value)
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
        db, action="EXECUTE", record_type="batch_record_step", record_id=step.id,
        module="mes",
        human_description=f"Step {step.step_number} recorded by {current_user.full_name}",
        user_id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, ip_address=get_client_ip(request),
        new_value=body.recorded_value,
    )
    await db.refresh(step)
    return step


@router.post("/batch-records/{br_id}/release")
async def release_batch(
    br_id: str,
    body: BatchReleaseRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """QA release decision — requires electronic signature."""
    result = await db.execute(select(BatchRecord).where(BatchRecord.id == br_id))
    br = result.scalar_one_or_none()
    if not br:
        raise HTTPException(status_code=404, detail="Batch record not found.")

    sig = await ESignatureService.sign(
        db,
        user_id=current_user.id,
        password=body.password,
        record_type="batch_record",
        record_id=br_id,
        record_version="1.0",
        record_data={"batch_number": br.batch_number, "status": br.status},
        meaning=body.decision,
        meaning_display=f"Batch {body.decision.title()}",
        ip_address=get_client_ip(request),
        comments=body.comments,
    )

    br.reviewed_by_id = current_user.id
    br.reviewed_at = datetime.now(timezone.utc)
    br.release_decision = body.decision
    br.release_comments = body.comments
    br.status = body.decision  # "released" or "rejected"

    return {
        "signature_id": sig.id,
        "signed_at": sig.signed_at,
        "decision": body.decision,
        "batch_number": br.batch_number,
    }
