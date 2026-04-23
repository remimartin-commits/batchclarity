"""Document Control API — version-controlled GMP documents."""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.auth.dependencies import get_current_user, get_client_ip
from app.core.auth.models import User
from app.core.audit.service import AuditService
from app.core.esig.service import ESignatureService
from app.core.documents.models import Document, DocumentVersion, DocumentType
from app.core.documents.schemas import (
    DocumentCreate, DocumentOut, DocumentVersionCreate,
    DocumentVersionOut, DocumentVersionSignRequest, DocumentTypeOut,
)

router = APIRouter(prefix="/documents", tags=["Document Control"])


@router.get("/types", response_model=list[DocumentTypeOut])
async def list_document_types(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DocumentType))
    return result.scalars().all()


@router.post("", response_model=DocumentOut, status_code=201)
async def create_document(
    body: DocumentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Get document type for prefix + auto-numbering
    type_result = await db.execute(
        select(DocumentType).where(DocumentType.id == body.document_type_id)
    )
    doc_type = type_result.scalar_one_or_none()
    if not doc_type:
        raise HTTPException(status_code=404, detail="Document type not found.")

    count_result = await db.execute(
        select(func.count()).select_from(Document).where(
            Document.document_type_id == body.document_type_id
        )
    )
    count = (count_result.scalar() or 0) + 1
    doc_number = f"{doc_type.prefix}-{count:04d}"

    doc = Document(
        document_number=doc_number,
        title=body.title,
        document_type_id=body.document_type_id,
        department=body.department,
        site_id=body.site_id,
        owner_id=current_user.id,
    )
    db.add(doc)
    await db.flush([doc])

    await AuditService.log(
        db, action="CREATE", record_type="document", record_id=doc.id,
        module="documents",
        human_description=f"Document {doc_number} '{body.title}' created by {current_user.full_name}",
        user_id=current_user.id, username=current_user.username, full_name=current_user.full_name,
        ip_address=get_client_ip(request),
    )
    await db.refresh(doc)
    return doc


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    type_id: str | None = None,
    search: str | None = None,
    include_obsolete: bool = False,
    skip: int = 0, limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Document)
    if not include_obsolete:
        query = query.where(Document.is_obsolete == False)
    if type_id:
        query = query.where(Document.document_type_id == type_id)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            Document.title.ilike(pattern) | Document.document_number.ilike(pattern)
        )
    result = await db.execute(query.order_by(Document.document_number).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{doc_id}", response_model=DocumentOut)
async def get_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


@router.post("/{doc_id}/versions", response_model=DocumentVersionOut, status_code=201)
async def create_version(
    doc_id: str,
    body: DocumentVersionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc.is_obsolete:
        raise HTTPException(status_code=400, detail="Cannot create a version for an obsolete document.")

    existing_version = await db.execute(
        select(DocumentVersion).where(
            DocumentVersion.document_id == doc_id,
            DocumentVersion.version_number == body.version_number,
        )
    )
    if existing_version.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Version '{body.version_number}' already exists.")

    current_count_result = await db.execute(
        select(func.count()).select_from(DocumentVersion).where(DocumentVersion.document_id == doc_id)
    )
    current_count = current_count_result.scalar() or 0
    if current_count > 0 and not (body.change_reason and body.change_reason.strip()):
        raise HTTPException(status_code=400, detail="Change reason is required for version revisions.")

    version = DocumentVersion(
        document_id=doc_id,
        version_number=body.version_number,
        status="draft",
        content=body.content,
        change_summary=body.change_summary,
        change_reason=body.change_reason,
        authored_by_id=current_user.id,
        authored_date=datetime.now(timezone.utc),
    )
    db.add(version)
    await db.flush([version])

    await AuditService.log(
        db, action="CREATE", record_type="document_version", record_id=version.id,
        module="documents",
        human_description=f"Version {body.version_number} created for document {doc.document_number}",
        user_id=current_user.id, username=current_user.username, full_name=current_user.full_name,
        ip_address=get_client_ip(request),
    )
    await db.refresh(version)
    return version


@router.get("/{doc_id}/versions", response_model=list[DocumentVersionOut])
async def list_versions(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DocumentVersion).where(DocumentVersion.document_id == doc_id)
        .order_by(DocumentVersion.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{doc_id}/versions/{version_id}/sign")
async def sign_version(
    doc_id: str,
    version_id: str,
    body: DocumentVersionSignRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DocumentVersion).where(
            DocumentVersion.id == version_id,
            DocumentVersion.document_id == doc_id,
        )
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Document version not found.")
    old_status = version.status

    sig = await ESignatureService.sign(
        db,
        user_id=current_user.id,
        password=body.password,
        record_type="document_version",
        record_id=version_id,
        record_version=version.version_number,
        record_data={"id": version_id, "version_number": version.version_number, "status": version.status},
        meaning=body.meaning,
        meaning_display=body.meaning.title(),
        ip_address=get_client_ip(request),
        comments=body.comments,
    )

    now = datetime.now(timezone.utc)
    if body.meaning == "reviewed":
        version.reviewed_by_id = current_user.id
        version.reviewed_date = now
        version.status = "under_review"
    elif body.meaning == "approved":
        version.approved_by_id = current_user.id
        version.approved_date = now
        version.status = "approved"
    elif body.meaning == "effective":
        prior_effective_result = await db.execute(
            select(DocumentVersion).where(
                DocumentVersion.document_id == doc_id,
                DocumentVersion.status == "effective",
                DocumentVersion.id != version_id,
            )
        )
        prior_effective = prior_effective_result.scalar_one_or_none()
        if prior_effective:
            prior_effective.status = "superseded"
            prior_effective.superseded_date = now
        version.status = "effective"
        version.effective_date = now
        doc_result = await db.execute(select(Document).where(Document.id == doc_id))
        doc = doc_result.scalar_one_or_none()
        if doc:
            doc.current_version_id = version.id
    elif body.meaning == "obsolete":
        version.status = "obsolete"
        doc_result = await db.execute(select(Document).where(Document.id == doc_id))
        doc = doc_result.scalar_one_or_none()
        if doc:
            doc.is_obsolete = True
    else:
        raise HTTPException(status_code=400, detail="Unsupported signature meaning.")

    await AuditService.log(
        db,
        action="TRANSITION",
        record_type="document_version",
        record_id=version_id,
        module="documents",
        human_description=(
            f"Document version {version.version_number} transitioned {old_status} -> {version.status}"
        ),
        user_id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        ip_address=get_client_ip(request),
        old_value={"status": old_status},
        new_value={"status": version.status, "signature_id": str(sig.id)},
        reason=body.comments,
    )

    return {"signature_id": sig.id, "signed_at": sig.signed_at, "new_status": version.status}
