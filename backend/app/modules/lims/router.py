"""LIMS API — Samples, Test Results, OOS Investigations, Specifications."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.auth.dependencies import get_current_user, get_client_ip
from app.core.auth.models import User
from app.core.audit.service import AuditService
from app.core.esig.service import ESignatureService
from app.modules.lims.models import (
    Sample, TestResult, OOSInvestigation, Specification,
)
from app.modules.lims.schemas import (
    SampleCreate, SampleOut,
    TestResultCreate, TestResultOut, TestResultReviewRequest,
    OOSInvestigationOut, SpecificationCreate, SpecificationOut,
)

router = APIRouter(prefix="/lims", tags=["LIMS"])


# ── Specifications ────────────────────────────────────────────────────────────

@router.post("/specifications", response_model=SpecificationOut, status_code=201)
async def create_specification(
    body: SpecificationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Specification).where(Specification.spec_number == body.spec_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Spec number '{body.spec_number}' already exists.")

    spec = Specification(**body.model_dump(), status="draft")
    db.add(spec)
    await db.flush([spec])
    await AuditService.log(
        db, action="CREATE", record_type="specification", record_id=spec.id,
        module="lims",
        human_description=f"Specification {body.spec_number} '{body.name}' created",
        user_id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, ip_address=get_client_ip(request),
    )
    await db.refresh(spec)
    return spec


@router.get("/specifications", response_model=list[SpecificationOut])
async def list_specifications(
    skip: int = 0, limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Specification).order_by(Specification.spec_number).offset(skip).limit(limit)
    )
    return result.scalars().all()


# ── Samples ───────────────────────────────────────────────────────────────────

@router.post("/samples", response_model=SampleOut, status_code=201)
async def create_sample(
    body: SampleCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Sample).where(Sample.sample_number == body.sample_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Sample number '{body.sample_number}' already exists.")

    now = datetime.now(timezone.utc)
    sample = Sample(
        **body.model_dump(),
        sampled_by_id=current_user.id,
        received_at=now,
        received_by_id=current_user.id,
        status="received",
    )
    db.add(sample)
    await db.flush([sample])
    await AuditService.log(
        db, action="CREATE", record_type="sample", record_id=sample.id,
        module="lims",
        human_description=f"Sample {body.sample_number} received ({body.sample_type})",
        user_id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, ip_address=get_client_ip(request),
    )
    await db.refresh(sample)
    return sample


@router.get("/samples", response_model=list[SampleOut])
async def list_samples(
    status_filter: str | None = None,
    sample_type: str | None = None,
    skip: int = 0, limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Sample)
    if status_filter:
        query = query.where(Sample.status == status_filter)
    if sample_type:
        query = query.where(Sample.sample_type == sample_type)
    result = await db.execute(
        query.order_by(Sample.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/samples/{sample_id}", response_model=SampleOut)
async def get_sample(
    sample_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Sample).where(Sample.id == sample_id))
    sample = result.scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found.")
    return sample


# ── Test Results ──────────────────────────────────────────────────────────────

@router.post("/samples/{sample_id}/results", response_model=TestResultOut, status_code=201)
async def enter_result(
    sample_id: str,
    body: TestResultCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sample_result = await db.execute(select(Sample).where(Sample.id == sample_id))
    sample = sample_result.scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found.")

    now = datetime.now(timezone.utc)
    result_obj = TestResult(
        sample_id=sample_id,
        test_method_id=body.test_method_id,
        specification_test_id=body.specification_test_id,
        result_value=body.result_value,
        result_numeric=body.result_numeric,
        unit=body.unit,
        analyst_id=current_user.id,
        tested_at=body.tested_at,
        entered_at=now,
        status="pending_review",
        is_oos=False,
    )
    db.add(result_obj)
    await db.flush([result_obj])
    await AuditService.log(
        db, action="CREATE", record_type="test_result", record_id=result_obj.id,
        module="lims",
        human_description=f"Test result entered for sample {sample.sample_number}: {body.result_value} {body.unit or ''}",
        user_id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, ip_address=get_client_ip(request),
    )
    await db.refresh(result_obj)
    return result_obj


@router.get("/samples/{sample_id}/results", response_model=list[TestResultOut])
async def list_results(
    sample_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TestResult).where(TestResult.sample_id == sample_id)
        .order_by(TestResult.tested_at)
    )
    return result.scalars().all()


@router.post("/results/{result_id}/review")
async def review_result(
    result_id: str,
    body: TestResultReviewRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """QA review of a test result. OOS triggers automatic investigation creation."""
    result_obj_q = await db.execute(select(TestResult).where(TestResult.id == result_id))
    result_obj = result_obj_q.scalar_one_or_none()
    if not result_obj:
        raise HTTPException(status_code=404, detail="Test result not found.")

    sig = await ESignatureService.sign(
        db,
        user_id=current_user.id,
        password=body.password,
        record_type="test_result",
        record_id=result_id,
        record_version="1.0",
        record_data={"result_value": result_obj.result_value, "status": result_obj.status},
        meaning=body.decision,
        meaning_display=f"Result {body.decision.upper()}",
        ip_address=get_client_ip(request),
        comments=body.comments,
    )

    now = datetime.now(timezone.utc)
    result_obj.status = body.decision
    result_obj.reviewer_id = current_user.id
    result_obj.reviewed_at = now
    result_obj.review_comments = body.comments
    result_obj.signature_id = sig.id

    investigation_id = None
    if body.decision == "oos":
        result_obj.is_oos = True
        # Auto-create OOS investigation
        count_q = await db.execute(select(func.count()).select_from(OOSInvestigation))
        count = (count_q.scalar() or 0) + 1
        inv_number = f"OOS-{datetime.now(timezone.utc).year}-{count:04d}"
        investigation = OOSInvestigation(
            investigation_number=inv_number,
            sample_id=result_obj.sample_id,
            initial_result_id=result_id,
            assigned_to_id=current_user.id,
            status="open",
        )
        db.add(investigation)
        await db.flush([investigation])
        result_obj.linked_investigation_id = investigation.id
        investigation_id = investigation.id

        await AuditService.log(
            db, action="CREATE", record_type="oos_investigation", record_id=investigation.id,
            module="lims",
            human_description=f"OOS investigation {inv_number} auto-created for result {result_id}",
            user_id=current_user.id, username=current_user.username,
            full_name=current_user.full_name, ip_address=get_client_ip(request),
        )

    return {
        "signature_id": sig.id,
        "decision": body.decision,
        "oos_investigation_id": investigation_id,
    }


# ── OOS Investigations ────────────────────────────────────────────────────────

@router.get("/oos-investigations", response_model=list[OOSInvestigationOut])
async def list_oos_investigations(
    status_filter: str | None = None,
    skip: int = 0, limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(OOSInvestigation)
    if status_filter:
        query = query.where(OOSInvestigation.status == status_filter)
    result = await db.execute(
        query.order_by(OOSInvestigation.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()
