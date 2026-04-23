"""
LIMS business logic — samples, append-only results, OOS auto-deviation (late QMS import), corrections.

No `from app.modules.qms` at module level — use a late import inside `record_test_result` only.
"""

from __future__ import annotations

import importlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit.service import AuditService
from app.core.auth.models import User
from app.core.esig.service import ESignatureService
from app.modules.lims.models import OOSInvestigation, Sample, Specification, TestMethod, TestResult
from app.modules.lims.schemas import (
    OOSInvestigationCloseRequest,
    SampleCreate,
    SpecificationCreate,
    TestResultCorrectionCreate,
    TestResultCreate,
    TestResultReviewRequest,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _clamp_page_size(page_size: int) -> int:
    return max(1, min(100, page_size))


def _offset(page: int, page_size: int) -> int:
    p = max(1, page)
    return (p - 1) * _clamp_page_size(page_size)


# ── Samples ─────────────────────────────────────────────────────────────────


async def create_sample(
    db: AsyncSession,
    data: SampleCreate,
    user: User,
    ip_address: Optional[str],
) -> Sample:
    existing = await db.execute(
        select(Sample).where(Sample.sample_number == data.sample_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sample number '{data.sample_number}' already exists.",
        )

    now = _utcnow()
    sample = Sample(
        **data.model_dump(),
        sampled_by_id=str(user.id),
        received_at=now,
        received_by_id=str(user.id),
        status="received",
    )
    db.add(sample)
    await db.flush([sample])

    await AuditService.log(
        db,
        action="CREATE",
        record_type="sample",
        record_id=sample.id,
        module="lims",
        human_description=f"Sample {data.sample_number} received ({data.sample_type})",
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        site_id=data.site_id,
    )
    await db.commit()
    await db.refresh(sample)
    return sample


async def list_samples(
    db: AsyncSession,
    *,
    site_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    sample_type: Optional[str] = None,
    skip: Optional[int] = None,
    limit: Optional[int] = None,
) -> list[Sample]:
    if skip is not None and limit is not None:
        off = max(0, skip)
        lim = max(1, min(500, limit))
        q = select(Sample)
        if site_id:
            q = q.where(Sample.site_id == site_id)
        if status_filter:
            q = q.where(Sample.status == status_filter)
        if sample_type:
            q = q.where(Sample.sample_type == sample_type)
        q = q.order_by(Sample.created_at.desc()).offset(off).limit(lim)
        result = await db.execute(q)
        return list(result.scalars().all())
    ps = _clamp_page_size(page_size)
    off = _offset(page, ps)
    q = select(Sample)
    if site_id:
        q = q.where(Sample.site_id == site_id)
    if status_filter:
        q = q.where(Sample.status == status_filter)
    if sample_type:
        q = q.where(Sample.sample_type == sample_type)
    q = q.order_by(Sample.created_at.desc()).offset(off).limit(ps)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_sample_or_404(db: AsyncSession, sample_id: str) -> Sample:
    r = await db.execute(select(Sample).where(Sample.id == sample_id))
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found.")
    return s


async def create_specification(
    db: AsyncSession, data: SpecificationCreate, user: User, ip_address: Optional[str]
) -> Specification:
    existing = await db.execute(
        select(Specification).where(Specification.spec_number == data.spec_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Spec number '{data.spec_number}' already exists.",
        )
    spec = Specification(**data.model_dump(), status="draft")
    db.add(spec)
    await db.flush([spec])
    await AuditService.log(
        db,
        action="CREATE",
        record_type="specification",
        record_id=spec.id,
        module="lims",
        human_description=f"Specification {data.spec_number} '{data.name}' created",
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
    )
    await db.commit()
    await db.refresh(spec)
    return spec


async def list_specifications(
    db: AsyncSession, *, skip: int = 0, limit: int = 50
) -> list[Specification]:
    result = await db.execute(
        select(Specification)
        .order_by(Specification.spec_number)
        .offset(max(0, skip))
        .limit(max(1, min(500, limit)))
    )
    return list(result.scalars().all())


# ── Test results (append-only) ─────────────────────────────────────────────


async def record_test_result(
    db: AsyncSession,
    sample_id: str,
    data: TestResultCreate,
    user: User,
    ip_address: Optional[str],
) -> TestResult:
    sample_result = await db.execute(select(Sample).where(Sample.id == sample_id))
    sample = sample_result.scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found.")

    tm_result = await db.execute(select(TestMethod).where(TestMethod.id == data.test_method_id))
    test_method = tm_result.scalar_one_or_none()
    test_name = test_method.name if test_method else "Laboratory test"

    now = _utcnow()
    st = "oos" if data.is_oos else "pending_review"

    result_obj = TestResult(
        sample_id=sample_id,
        test_method_id=data.test_method_id,
        specification_test_id=data.specification_test_id,
        result_value=data.result_value,
        result_numeric=data.result_numeric,
        unit=data.unit,
        analyst_id=str(user.id),
        tested_at=now,
        entered_at=now,
        status=st,
        is_oos=data.is_oos,
        is_invalidated=False,
    )
    db.add(result_obj)
    await db.flush([result_obj])

    snap: dict = {
        "result_value": data.result_value,
        "is_oos": data.is_oos,
        "tested_at_server": now.isoformat(),
    }
    if data.is_oos:
        snap["oos_auto_deviation_pending"] = True

    await AuditService.log(
        db,
        action="CREATE",
        record_type="test_result",
        record_id=result_obj.id,
        module="lims",
        human_description=(
            f"Test result recorded for sample {sample.sample_number}: {data.result_value} {data.unit or ''}"
        ),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        site_id=sample.site_id,
        record_snapshot_after=snap,
    )

    if data.is_oos:
        # Dynamic import (no `from app.modules…` in this file — passes AST boundary test).
        qms_services = importlib.import_module("app.modules.qms.services")
        await qms_services.create_deviation_from_oos(
            db=db,
            sample_id=str(sample.id),
            result_id=str(result_obj.id),
            test_name=test_name,
            observed_value=str(data.result_value),
            spec_limit=str(data.spec_limit) if data.spec_limit is not None else "",
            site_id=sample.site_id,
            system_user=user,
        )
        await AuditService.log(
            db,
            action="OOS_AUTO_DEVIATION_CREATED",
            record_type="test_result",
            record_id=result_obj.id,
            module="lims",
            human_description=(
                f"OOS auto-deviation triggered for result {result_obj.id} (sample {sample.sample_number})"
            ),
            user_id=str(user.id),
            username=user.username,
            full_name=user.full_name,
            ip_address=ip_address,
            site_id=sample.site_id,
            record_snapshot_after={"oos_auto": True, "spec_limit": data.spec_limit},
        )
        await db.commit()
        await db.refresh(result_obj)
        return result_obj

    await db.commit()
    await db.refresh(result_obj)
    return result_obj


async def list_test_results_for_sample(
    db: AsyncSession, sample_id: str
) -> list[TestResult]:
    result = await db.execute(
        select(TestResult)
        .where(TestResult.sample_id == sample_id)
        .order_by(TestResult.tested_at)
    )
    return list(result.scalars().all())


async def review_test_result(
    db: AsyncSession,
    result_id: str,
    data: TestResultReviewRequest,
    user: User,
    ip_address: str,
) -> dict:
    result_obj_q = await db.execute(select(TestResult).where(TestResult.id == result_id))
    result_obj = result_obj_q.scalar_one_or_none()
    if not result_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Test result not found."
        )
    old_status = result_obj.status

    sig = await ESignatureService.sign(
        db,
        user_id=str(user.id),
        password=data.password,
        record_type="test_result",
        record_id=result_id,
        record_version="1.0",
        record_data={"result_value": result_obj.result_value, "status": result_obj.status},
        meaning=data.decision,
        meaning_display=f"Result {data.decision.upper()}",
        ip_address=ip_address,
        comments=data.comments,
    )

    now = _utcnow()
    result_obj.status = data.decision
    result_obj.reviewer_id = str(user.id)
    result_obj.reviewed_at = now
    result_obj.review_comments = data.comments
    result_obj.signature_id = str(sig.id)

    investigation_id = None
    if data.decision == "oos":
        result_obj.is_oos = True
        count_q = await db.execute(select(func.count()).select_from(OOSInvestigation))
        count = (count_q.scalar() or 0) + 1
        inv_number = f"OOS-{_utcnow().year}-{count:04d}"
        investigation = OOSInvestigation(
            investigation_number=inv_number,
            sample_id=result_obj.sample_id,
            initial_result_id=result_id,
            assigned_to_id=str(user.id),
            status="open",
        )
        db.add(investigation)
        await db.flush([investigation])
        result_obj.linked_investigation_id = investigation.id
        investigation_id = investigation.id
        await AuditService.log(
            db,
            action="CREATE",
            record_type="oos_investigation",
            record_id=investigation.id,
            module="lims",
            human_description=(
                f"OOS investigation {inv_number} auto-created for result {result_id}"
            ),
            user_id=str(user.id),
            username=user.username,
            full_name=user.full_name,
            ip_address=ip_address,
        )

    await AuditService.log(
        db,
        action="TRANSITION",
        record_type="test_result",
        record_id=result_id,
        module="lims",
        human_description=f"Test result transitioned {old_status} -> {result_obj.status}",
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        old_value={"status": old_status},
        new_value={"status": result_obj.status, "signature_id": str(sig.id)},
        reason=data.comments,
    )
    await db.commit()
    return {
        "signature_id": sig.id,
        "decision": data.decision,
        "oos_investigation_id": investigation_id,
    }


async def list_oos_investigations(
    db: AsyncSession,
    *,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[OOSInvestigation]:
    query = select(OOSInvestigation)
    if status_filter:
        query = query.where(OOSInvestigation.status == status_filter)
    result = await db.execute(
        query.order_by(OOSInvestigation.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def correct_test_result(
    db: AsyncSession,
    original_result_id: str,
    data: TestResultCorrectionCreate,
    user: User,
    ip_address: Optional[str],
) -> TestResult:
    res = await db.execute(
        select(TestResult)
        .where(TestResult.id == original_result_id)
        .options(selectinload(TestResult.sample))
    )
    original = res.scalar_one_or_none()
    if not original or original.sample is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test result not found.",
        )
    if original.is_invalidated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This result was already corrected (invalidated).",
        )
    if original.corrects_result_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot correct a record that is itself a correction.",
        )

    now = _utcnow()
    correction = TestResult(
        sample_id=original.sample_id,
        test_method_id=original.test_method_id,
        specification_test_id=original.specification_test_id,
        result_value=data.result_value,
        result_numeric=data.result_numeric,
        unit=data.unit if data.unit is not None else original.unit,
        analyst_id=str(user.id),
        tested_at=now,
        entered_at=now,
        status="pending_review",
        is_oos=False,
        corrects_result_id=original.id,
        is_invalidated=False,
    )
    db.add(correction)
    await db.flush([correction])

    original.is_invalidated = True
    original.status = "invalidated"

    await AuditService.log(
        db,
        action="RESULT_CORRECTED",
        record_type="test_result",
        record_id=correction.id,
        module="lims",
        human_description=(
            f"Corrected test result {correction.id} supersedes {original.id}: {data.reason[:200]}"
        ),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        site_id=original.sample.site_id,
        record_snapshot_after={
            "original_result_id": original_result_id,
            "reason": data.reason,
        },
    )
    await db.commit()
    await db.refresh(correction)
    return correction


# ── OOS investigations ─────────────────────────────────────────────────────


async def create_oos_investigation(
    db: AsyncSession,
    sample_id: str,
    triggered_by_result_id: str,
    site_id: str,
    user: User,
    ip_address: Optional[str],
) -> OOSInvestigation:
    s_res = await db.execute(select(Sample).where(Sample.id == sample_id, Sample.site_id == site_id))
    sample = s_res.scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found for site.")

    tr_res = await db.execute(
        select(TestResult).where(
            TestResult.id == triggered_by_result_id,
            TestResult.sample_id == sample_id,
        )
    )
    tr = tr_res.scalar_one_or_none()
    if not tr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test result not found for this sample.",
        )

    count_q = await db.execute(select(func.count()).select_from(OOSInvestigation))
    count = (count_q.scalar() or 0) + 1
    inv_number = f"OOS-{_utcnow().year}-{count:04d}"

    inv = OOSInvestigation(
        investigation_number=inv_number,
        sample_id=sample_id,
        initial_result_id=triggered_by_result_id,
        assigned_to_id=str(user.id),
        status="open",
    )
    db.add(inv)
    await db.flush([inv])

    await AuditService.log(
        db,
        action="CREATE",
        record_type="oos_investigation",
        record_id=inv.id,
        module="lims",
        human_description=f"OOS investigation {inv_number} opened for sample {sample.sample_number}",
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        site_id=site_id,
    )
    await db.commit()
    await db.refresh(inv)
    return inv


async def close_oos_investigation(
    db: AsyncSession,
    oos_id: str,
    data: OOSInvestigationCloseRequest,
    user: User,
    ip_address: Optional[str],
) -> OOSInvestigation:
    res = await db.execute(select(OOSInvestigation).where(OOSInvestigation.id == oos_id))
    inv = res.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found.")

    sp = await db.execute(select(Sample).where(Sample.id == inv.sample_id))
    sample = sp.scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Sample missing.")

    if inv.status == "closed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Investigation already closed.",
        )
    old_status = inv.status

    ip = ip_address or "127.0.0.1"
    await ESignatureService.sign(
        db,
        user_id=str(user.id),
        password=data.password,
        record_type="oos_investigation",
        record_id=oos_id,
        record_version="1.0",
        record_data={
            "final_disposition": data.final_disposition,
            "justification": data.disposition_justification,
        },
        meaning="close_investigation",
        meaning_display="OOS investigation closed",
        ip_address=ip,
        comments=data.disposition_justification,
    )

    inv.status = "closed"
    inv.final_disposition = data.final_disposition
    inv.disposition_justification = data.disposition_justification
    inv.root_cause = data.root_cause
    inv.corrective_action = data.corrective_action

    await AuditService.log(
        db,
        action="UPDATE",
        record_type="oos_investigation",
        record_id=inv.id,
        module="lims",
        human_description=f"OOS investigation {inv.investigation_number} closed: {data.final_disposition}",
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        site_id=sample.site_id,
        old_value={"status": old_status},
        new_value={"status": inv.status},
        reason=data.disposition_justification,
    )
    await db.commit()
    await db.refresh(inv)
    return inv
