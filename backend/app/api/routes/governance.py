import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.organization import Organization, OrganizationMembership
from backend.app.models.governance import InstitutionAccreditation, GovernanceAuditLog
from backend.app.api.dependencies.auth import get_current_user, require_role
from backend.app.schemas.governance import (
    AccreditationApplicationRequest,
    AccreditationReviewRequest,
    AccreditationApprovalRequest,
    TrustPolicyEvaluationRequest,
    TrustPolicyEvaluationResponse,
    PublicDirectoryEntry
)
from backend.app.services.governance.trust_policy_service import TrustPolicyService

router = APIRouter(prefix="/governance", tags=["Trust Governance & Accreditation"])

async def get_user_org_id(db: AsyncSession, user_id: str) -> Optional[str]:
    res = await db.execute(
        select(OrganizationMembership.organization_id).where(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.status == "ACTIVE"
        )
    )
    return res.scalars().first()

@router.post("/accreditations/apply")
async def apply_for_accreditation(
    request: AccreditationApplicationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits an accreditation application for the authenticated user's institution.
    """
    org_id = getattr(current_user, "organization_id", None) or await get_user_org_id(db, current_user.id)
    if not org_id:
        raise HTTPException(status_code=400, detail="User is not affiliated with an institution")
    
    # Check for existing accreditation
    existing_res = await db.execute(
        select(InstitutionAccreditation).where(InstitutionAccreditation.organization_id == org_id)
    )
    existing = existing_res.scalars().first()
    if existing and existing.status in ("APPLIED", "UNDER_REVIEW", "APPROVED"):
        raise HTTPException(
            status_code=400, 
            detail=f"An accreditation record already exists in '{existing.status}' status"
        )

    accreditation = InstitutionAccreditation(
        organization_id=org_id,
        category=request.category.upper(),
        status="APPLIED",
        authorized_schemas=request.requested_schemas,
        evidence_urls=request.evidence_urls
    )
    db.add(accreditation)
    await db.flush()

    audit = GovernanceAuditLog(
        accreditation_id=accreditation.id,
        actor_id=current_user.id,
        action="SUBMIT_APPLICATION",
        details={"category": request.category, "requested_schemas": request.requested_schemas}
    )
    db.add(audit)
    await db.commit()
    await db.refresh(accreditation)
    
    return {
        "accreditation_id": accreditation.id,
        "status": accreditation.status,
        "category": accreditation.category,
        "message": "Accreditation application submitted for governance review"
    }

@router.get("/accreditations/my")
async def get_my_accreditation(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves current institution's accreditation status and authorized scopes.
    """
    org_id = getattr(current_user, "organization_id", None) or await get_user_org_id(db, current_user.id)
    if not org_id:
        raise HTTPException(status_code=400, detail="User is not affiliated with an institution")
        
    result = await db.execute(
        select(InstitutionAccreditation).where(InstitutionAccreditation.organization_id == org_id)
    )
    acc = result.scalars().first()
    if not acc:
        raise HTTPException(status_code=404, detail="No accreditation application found")
    return acc

@router.post("/accreditations/{accreditation_id}/review")
async def review_accreditation(
    accreditation_id: str,
    request: AccreditationReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["PLATFORM_ADMIN", "GOVERNANCE_OFFICER"]))
):
    """
    First-stage governance review: performs document verification and forwards or requests evidence.
    """
    result = await db.execute(
        select(InstitutionAccreditation).where(InstitutionAccreditation.id == accreditation_id)
    )
    acc = result.scalars().first()
    if not acc:
        raise HTTPException(status_code=404, detail="Accreditation application not found")
        
    # Applications cannot review themselves
    if acc.organization_id == current_user.organization_id:
        raise HTTPException(status_code=403, detail="Separation of duties violation: cannot review your own institution")

    acc.reviewer_id = current_user.id
    if request.action == "REQUEST_EVIDENCE":
        acc.status = "EVIDENCE_REQUESTED"
    elif request.action == "FORWARD_SENIOR":
        acc.status = "UNDER_REVIEW"
    elif request.action == "REJECT":
        acc.status = "REJECTED"
        acc.rejection_reason = request.rejection_reason
    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {request.action}")

    acc.review_notes = request.notes
    
    audit = GovernanceAuditLog(
        accreditation_id=acc.id,
        actor_id=current_user.id,
        action=f"REVIEW_{request.action}",
        details={"notes": request.notes, "rejection_reason": request.rejection_reason}
    )
    db.add(audit)
    await db.commit()
    await db.refresh(acc)
    
    return {"accreditation_id": acc.id, "status": acc.status, "reviewer_id": acc.reviewer_id}

@router.post("/accreditations/{accreditation_id}/decide")
async def decide_accreditation(
    accreditation_id: str,
    request: AccreditationApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["PLATFORM_ADMIN"]))
):
    """
    Senior approval stage: enforces multi-stage separation of duties (reviewer != senior approver).
    """
    result = await db.execute(
        select(InstitutionAccreditation).where(InstitutionAccreditation.id == accreditation_id)
    )
    acc = result.scalars().first()
    if not acc:
        raise HTTPException(status_code=404, detail="Accreditation application not found")
        
    if acc.organization_id == current_user.organization_id:
        raise HTTPException(status_code=403, detail="Separation of duties violation: cannot approve your own institution")
        
    # Enforce separation of duties: reviewer cannot be the senior approver
    if acc.reviewer_id and acc.reviewer_id == current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Separation of duties violation: first-stage reviewer cannot act as second-stage senior approver"
        )

    acc.senior_approver_id = current_user.id
    now = datetime.datetime.now(datetime.timezone.utc)
    
    if request.approved:
        acc.status = "APPROVED"
        acc.authorized_schemas = request.authorized_schemas
        acc.valid_from = now
        acc.valid_until = now + datetime.timedelta(days=request.valid_days)
    else:
        acc.status = "REJECTED"
        acc.rejection_reason = request.rejection_reason

    audit = GovernanceAuditLog(
        accreditation_id=acc.id,
        actor_id=current_user.id,
        action="DECIDE_APPROVE" if request.approved else "DECIDE_REJECT",
        details={
            "approved": request.approved,
            "authorized_schemas": request.authorized_schemas,
            "valid_days": request.valid_days,
            "rejection_reason": request.rejection_reason
        }
    )
    db.add(audit)
    await db.commit()
    await db.refresh(acc)
    
    return {
        "accreditation_id": acc.id,
        "status": acc.status,
        "authorized_schemas": acc.authorized_schemas,
        "valid_until": acc.valid_until
    }

@router.post("/evaluate-trust", response_model=TrustPolicyEvaluationResponse)
async def evaluate_trust_policy(
    request: TrustPolicyEvaluationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Multi-dimensional Trust Policy Evaluation Endpoint.
    """
    return await TrustPolicyService.evaluate_trust(
        db=db,
        institution_address=request.institution_address,
        credential_schema=request.credential_schema,
        signing_key_address=request.signing_key_address
    )

@router.get("/directory", response_model=List[PublicDirectoryEntry])
async def get_public_trust_directory(
    db: AsyncSession = Depends(get_db)
):
    """
    Public, privacy-preserving directory of verified accredited institutions.
    Excludes private application evidence and officer PII.
    """
    query = (
        select(Organization.name, InstitutionAccreditation.category, Organization.on_chain_address,
               InstitutionAccreditation.status, InstitutionAccreditation.authorized_schemas,
               InstitutionAccreditation.valid_until)
        .join(InstitutionAccreditation, Organization.id == InstitutionAccreditation.organization_id)
        .where(InstitutionAccreditation.status == "APPROVED", Organization.status == "ACTIVE")
    )
    result = await db.execute(query)
    entries = []
    for row in result.all():
        name, cat, addr, stat, schemas, valid_until = row
        entries.append(PublicDirectoryEntry(
            institution_name=name,
            category=cat,
            verification_identity=addr or "0x0000000000000000000000000000000000000000",
            accreditation_status=stat,
            authorized_schemas=schemas or [],
            valid_until=valid_until
        ))
    return entries
