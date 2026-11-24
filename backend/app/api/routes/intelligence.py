import os
import json
import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.api.dependencies.auth import get_current_user
from backend.app.models.user import User
from backend.app.models.intelligence import DocumentUpload, ExtractedCredentialData
from backend.app.schemas.intelligence import (
    DocumentUploadResponse,
    ExtractionDetailResponse,
    ExtractedFieldDetail,
    AnomalyFinding,
    ReviewExtractionRequest,
    PrepareFromExtractionRequest,
)
from backend.app.core.constants import UserRole
from backend.app.services.authorization_service import AuthorizationService
from backend.app.services.intelligence.document_processor import DocumentProcessor
from backend.app.services.intelligence.extraction_engine import ExtractionEngine
from backend.app.services.intelligence.anomaly_detector import AnomalyDetector
from backend.app.services.credential.preparation_service import PreparationService
from backend.app.core.exceptions import (
    TenantAccessDeniedException,
    ResourceNotFoundException,
    ValidationException,
    InvalidStatusTransitionException,
)

router = APIRouter(prefix="/intelligence", tags=["DecentralID Intelligence"])

UPLOAD_DIR = os.path.join(os.getcwd(), "storage", "document_intake")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=ExtractionDetailResponse, status_code=status.HTTP_201_CREATED)
async def upload_document_for_extraction(
    file: UploadFile = File(...),
    organization_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExtractionDetailResponse:
    # 1. Tenant Authorization Check
    has_perm = await AuthorizationService.has_organization_role(
        db, current_user.id, organization_id, [UserRole.INSTITUTION_ADMIN.value, UserRole.AUTHORIZED_ISSUER.value, "ADMIN"]
    )
    if not has_perm:
        raise TenantAccessDeniedException("Not authorized to upload documents for this organization.")

    # 2. Read and validate content
    content = await file.read()
    detected_mime, file_hash, sanitized_filename = DocumentProcessor.validate_and_fingerprint(
        content=content,
        original_filename=file.filename or "uploaded_document",
        declared_content_type=file.content_type,
    )

    doc_id = str(uuid.uuid4())
    ext = os.path.splitext(sanitized_filename)[1] or ".bin"
    storage_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{file_hash[:12]}{ext}")
    with open(storage_path, "wb") as f:
        f.write(content)

    # 3. Create DocumentUpload record
    doc_record = DocumentUpload(
        id=doc_id,
        organization_id=organization_id,
        uploaded_by=current_user.id,
        filename=sanitized_filename,
        file_hash=file_hash,
        mime_type=detected_mime,
        file_size=len(content),
        storage_path=storage_path,
        status="PROCESSING",
    )
    db.add(doc_record)
    await db.flush()

    # 4. Text Extraction
    try:
        raw_text = DocumentProcessor.extract_text_from_content(content, detected_mime)
    except Exception as e:
        doc_record.status = "FAILED"
        doc_record.error_message = str(e)
        await db.commit()
        raise ValidationException(f"Document processing failed: {str(e)}")

    # 5. Field Extraction & Schema Matching
    schema_type, extracted_fields, overall_conf = ExtractionEngine.process_document_text(raw_text)

    # 6. Anomaly Detection
    anomalies = await AnomalyDetector.analyze_document_anomalies(
        db=db,
        organization_id=organization_id,
        file_hash=file_hash,
        current_doc_id=doc_id,
        extracted_fields=extracted_fields,
        overall_confidence=overall_conf,
    )

    doc_record.status = "PROCESSED"

    # 7. Persist Extracted Data
    extracted_record = ExtractedCredentialData(
        document_id=doc_id,
        schema_type=schema_type,
        raw_text=raw_text,
        extracted_fields_json=json.dumps(extracted_fields),
        anomaly_findings_json=json.dumps(anomalies),
        overall_confidence=overall_conf,
        review_status="PENDING_REVIEW",
    )
    db.add(extracted_record)
    await db.commit()
    await db.refresh(doc_record)
    await db.refresh(extracted_record)

    field_details = {
        k: ExtractedFieldDetail(**v) for k, v in extracted_fields.items()
    }
    anomaly_items = [AnomalyFinding(**a) for a in anomalies]

    return ExtractionDetailResponse(
        id=extracted_record.id,
        document_id=doc_record.id,
        filename=doc_record.filename,
        mime_type=doc_record.mime_type,
        status=doc_record.status,
        schema_type=extracted_record.schema_type,
        raw_text=extracted_record.raw_text,
        extracted_fields=field_details,
        anomaly_findings=anomaly_items,
        overall_confidence=extracted_record.overall_confidence,
        review_status=extracted_record.review_status,
        reviewed_by=extracted_record.reviewed_by,
        reviewed_at=extracted_record.reviewed_at,
        credential_id=extracted_record.credential_id,
        created_at=doc_record.created_at,
    )

@router.get("/documents", response_model=List[DocumentUploadResponse], status_code=status.HTTP_200_OK)
async def list_documents(
    organization_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DocumentUploadResponse]:
    has_perm = await AuthorizationService.has_organization_role(
        db, current_user.id, organization_id, [UserRole.INSTITUTION_ADMIN.value, UserRole.AUTHORIZED_ISSUER.value, "ADMIN"]
    )
    if not has_perm:
        raise TenantAccessDeniedException("Not authorized to access documents for this organization.")

    stmt = select(DocumentUpload).where(DocumentUpload.organization_id == organization_id).order_by(DocumentUpload.created_at.desc())
    res = await db.execute(stmt)
    docs = res.scalars().all()

    return [
        DocumentUploadResponse(
            id=d.id,
            organization_id=d.organization_id,
            filename=d.filename,
            file_hash=d.file_hash,
            mime_type=d.mime_type,
            file_size=d.file_size,
            status=d.status,
            created_at=d.created_at,
        )
        for d in docs
    ]

@router.get("/documents/{document_id}", response_model=ExtractionDetailResponse, status_code=status.HTTP_200_OK)
async def get_document_extraction(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExtractionDetailResponse:
    doc_stmt = select(DocumentUpload).where(DocumentUpload.id == document_id)
    doc_res = await db.execute(doc_stmt)
    doc = doc_res.scalar_one_or_none()
    if not doc:
        raise ResourceNotFoundException("Document upload record not found.")

    has_perm = await AuthorizationService.has_organization_role(
        db, current_user.id, doc.organization_id, [UserRole.INSTITUTION_ADMIN.value, UserRole.AUTHORIZED_ISSUER.value, "ADMIN"]
    )
    if not has_perm:
        raise TenantAccessDeniedException("Not authorized to access this document.")

    ext_stmt = select(ExtractedCredentialData).where(ExtractedCredentialData.document_id == document_id)
    ext_res = await db.execute(ext_stmt)
    ext = ext_res.scalar_one_or_none()
    if not ext:
        raise ResourceNotFoundException("Extracted data record not found for this document.")

    extracted_dict = json.loads(ext.extracted_fields_json)
    anomalies_list = json.loads(ext.anomaly_findings_json)

    field_details = {
        k: ExtractedFieldDetail(**v) for k, v in extracted_dict.items()
    }
    anomaly_items = [AnomalyFinding(**a) for a in anomalies_list]

    return ExtractionDetailResponse(
        id=ext.id,
        document_id=doc.id,
        filename=doc.filename,
        mime_type=doc.mime_type,
        status=doc.status,
        schema_type=ext.schema_type,
        raw_text=ext.raw_text,
        extracted_fields=field_details,
        anomaly_findings=anomaly_items,
        overall_confidence=ext.overall_confidence,
        review_status=ext.review_status,
        reviewed_by=ext.reviewed_by,
        reviewed_at=ext.reviewed_at,
        credential_id=ext.credential_id,
        created_at=doc.created_at,
    )

@router.post("/documents/{document_id}/review", response_model=ExtractionDetailResponse, status_code=status.HTTP_200_OK)
async def review_extracted_data(
    document_id: str,
    payload: ReviewExtractionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExtractionDetailResponse:
    doc_stmt = select(DocumentUpload).where(DocumentUpload.id == document_id)
    doc_res = await db.execute(doc_stmt)
    doc = doc_res.scalar_one_or_none()
    if not doc:
        raise ResourceNotFoundException("Document upload record not found.")

    has_perm = await AuthorizationService.has_organization_role(
        db, current_user.id, doc.organization_id, [UserRole.INSTITUTION_ADMIN.value, UserRole.AUTHORIZED_ISSUER.value, "ADMIN"]
    )
    if not has_perm:
        raise TenantAccessDeniedException("Institutional Administrator or Authorized Issuer permission required to review extractions.")

    ext_stmt = select(ExtractedCredentialData).where(ExtractedCredentialData.document_id == document_id)
    ext_res = await db.execute(ext_stmt)
    ext = ext_res.scalar_one_or_none()
    if not ext:
        raise ResourceNotFoundException("Extracted data record not found.")

    extracted_dict = json.loads(ext.extracted_fields_json)

    if payload.corrected_fields:
        for k, v in payload.corrected_fields.items():
            if k in extracted_dict:
                extracted_dict[k]["value"] = v
                extracted_dict[k]["human_corrected"] = True
                extracted_dict[k]["confidence"] = 1.0
            else:
                extracted_dict[k] = {
                    "value": v,
                    "confidence": 1.0,
                    "evidence_snippet": "Manual human entry",
                    "is_valid": True,
                    "human_corrected": True,
                }

    if payload.schema_type:
        ext.schema_type = payload.schema_type

    action = payload.review_action.upper()
    if action == "APPROVE":
        ext.review_status = "APPROVED"
    elif action == "REJECT":
        ext.review_status = "REJECTED"
    elif action == "UPDATE":
        ext.review_status = "PENDING_REVIEW"
    else:
        raise ValidationException("review_action must be 'APPROVE', 'REJECT', or 'UPDATE'.")

    ext.extracted_fields_json = json.dumps(extracted_dict)
    ext.reviewed_by = current_user.id
    ext.reviewed_at = datetime.datetime.now(datetime.timezone.utc)

    await db.commit()
    await db.refresh(ext)

    anomalies_list = json.loads(ext.anomaly_findings_json)
    field_details = {k: ExtractedFieldDetail(**v) for k, v in extracted_dict.items()}
    anomaly_items = [AnomalyFinding(**a) for a in anomalies_list]

    return ExtractionDetailResponse(
        id=ext.id,
        document_id=doc.id,
        filename=doc.filename,
        mime_type=doc.mime_type,
        status=doc.status,
        schema_type=ext.schema_type,
        raw_text=ext.raw_text,
        extracted_fields=field_details,
        anomaly_findings=anomaly_items,
        overall_confidence=ext.overall_confidence,
        review_status=ext.review_status,
        reviewed_by=ext.reviewed_by,
        reviewed_at=ext.reviewed_at,
        credential_id=ext.credential_id,
        created_at=doc.created_at,
    )

@router.post("/documents/{document_id}/prepare-credential", status_code=status.HTTP_201_CREATED)
async def prepare_credential_from_intelligence(
    document_id: str,
    payload: PrepareFromExtractionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submits verified extracted data into the credential preparation workflow.
    MANDATORY RULE: AI extraction never signs or issues credentials directly.
    Enters PREPARED state, subject to subsequent administrator approval.
    """
    doc_stmt = select(DocumentUpload).where(DocumentUpload.id == document_id)
    doc_res = await db.execute(doc_stmt)
    doc = doc_res.scalar_one_or_none()
    if not doc:
        raise ResourceNotFoundException("Document upload record not found.")

    ext_stmt = select(ExtractedCredentialData).where(ExtractedCredentialData.document_id == document_id)
    ext_res = await db.execute(ext_stmt)
    ext = ext_res.scalar_one_or_none()
    if not ext:
        raise ResourceNotFoundException("Extracted data record not found.")

    if ext.review_status != "APPROVED":
        raise InvalidStatusTransitionException("Cannot prepare credential: Document extraction has not been human-reviewed and APPROVED.")

    if ext.credential_id:
        raise InvalidStatusTransitionException(f"Credential has already been prepared from this extraction (ID: {ext.credential_id}).")

    extracted_dict = json.loads(ext.extracted_fields_json)
    claims = {k: v["value"] for k, v in extracted_dict.items()}

    # Call PreparationService (enforces schema validation, AES-256 encryption, commitment generation)
    cred_record, w3c_doc = await PreparationService.prepare_credential(
        db=db,
        operator_user_id=current_user.id,
        organization_id=doc.organization_id,
        recipient_address=payload.recipient_address,
        schema_type=ext.schema_type,
        claims=claims,
        valid_until=payload.valid_until,
    )

    ext.credential_id = cred_record.id
    await db.commit()

    return {
        "status": "PREPARED",
        "credential_id": cred_record.credential_id,
        "w3c_id": cred_record.w3c_id,
        "commitment": cred_record.commitment,
        "document_id": doc.id,
        "workflow_status": cred_record.workflow_status,
        "notice": "Credential prepared successfully from AI-assisted extraction. It must now be submitted for administrator approval before signing."
    }
