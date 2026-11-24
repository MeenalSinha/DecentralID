from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.api.dependencies.auth import get_current_user
from backend.app.models.user import User, Wallet
from backend.app.models.credential import Credential
from backend.app.models.organization import OrganizationMembership
from backend.app.core.exceptions import TenantAccessDeniedException, ResourceNotFoundException
from backend.app.schemas.credential import (
    PrepareCredentialRequest,
    PrepareCredentialResponse,
    SignCredentialRequest,
    ConfirmIssuanceRequest,
    CredentialSummary,
    CredentialListResponse,
    BatchPrepareRequest,
    BatchPrepareResponse,
    BatchItemResult,
)
from backend.app.schemas.presentation import (
    CreatePresentationRequest,
    VerifiablePresentationResponse,
    HolderCredentialDetail,
    HolderCredentialsResponse,
)
from backend.app.schemas.credential_schemas.registry import CredentialSchemaRegistry
from backend.app.services.credential.preparation_service import PreparationService
from backend.app.services.credential.issuance_service import IssuanceService
from backend.app.services.credential.presentation_service import PresentationService
from backend.app.services.credential.encryption_service import EncryptionService

router = APIRouter(prefix="/credentials", tags=["Credentials & Issuance Engine"])

@router.get("/schemas", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def list_available_schemas():
    """Returns all data-driven credential schemas supported by DecentralID."""
    schemas = CredentialSchemaRegistry.list_schemas()
    return [s.model_dump() for s in schemas]

@router.post("/batch-prepare", response_model=BatchPrepareResponse, status_code=status.HTTP_200_OK)
async def batch_prepare_credentials(
    payload: BatchPrepareRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchPrepareResponse:
    results = []
    success_count = 0
    fail_count = 0

    for idx, item in enumerate(payload.items):
        try:
            cred_record, _ = await PreparationService.prepare_credential(
                db=db,
                operator_user_id=current_user.id,
                organization_id=payload.organization_id,
                recipient_address=item.recipient_address,
                schema_type=payload.schema_type,
                claims=item.claims,
                valid_until=item.valid_until,
            )
            results.append(
                BatchItemResult(
                    index=idx,
                    recipient_address=item.recipient_address,
                    success=True,
                    credential_id=cred_record.credential_id,
                    commitment=cred_record.commitment,
                )
            )
            success_count += 1
        except Exception as e:
            results.append(
                BatchItemResult(
                    index=idx,
                    recipient_address=item.recipient_address,
                    success=False,
                    error=str(e),
                )
            )
            fail_count += 1

    return BatchPrepareResponse(
        total=len(payload.items),
        successful_count=success_count,
        failed_count=fail_count,
        results=results,
    )

@router.post("/prepare", response_model=PrepareCredentialResponse, status_code=status.HTTP_201_CREATED)
async def prepare_credential(
    payload: PrepareCredentialRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PrepareCredentialResponse:
    cred_record, w3c_doc = await PreparationService.prepare_credential(
        db=db,
        operator_user_id=current_user.id,
        organization_id=payload.organization_id,
        recipient_address=payload.recipient_address,
        schema_type=payload.schema_type,
        claims=payload.claims,
        valid_until=payload.valid_until,
    )
    return PrepareCredentialResponse(
        id=cred_record.id,
        w3c_id=cred_record.w3c_id,
        credential_id=cred_record.credential_id,
        recipient_address=cred_record.recipient_address,
        schema_type=cred_record.schema_type,
        commitment=cred_record.commitment,
        workflow_status=cred_record.workflow_status,
        credential_document=w3c_doc,
    )

@router.post("/{credential_id}/submit-approval", status_code=status.HTTP_200_OK)
async def submit_for_approval(
    credential_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cred = await IssuanceService.submit_for_approval(db, credential_id, current_user.id)
    return {"status": "submitted", "workflow_status": cred.workflow_status}

@router.post("/{credential_id}/approve", status_code=status.HTTP_200_OK)
async def approve_credential(
    credential_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cred = await IssuanceService.approve_credential(db, credential_id, current_user.id)
    return {"status": "approved", "workflow_status": cred.workflow_status, "approved_by": cred.approved_by}

@router.post("/{credential_id}/sign", status_code=status.HTTP_200_OK)
async def sign_credential(
    credential_id: str,
    payload: SignCredentialRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cred, signed_vc = await IssuanceService.sign_credential(
        db, credential_id, payload.private_key, current_user.id
    )
    return {
        "status": "signed",
        "workflow_status": cred.workflow_status,
        "credential": signed_vc,
    }

@router.post("/{credential_id}/confirm-issuance", status_code=status.HTTP_200_OK)
async def confirm_issuance(
    credential_id: str,
    payload: ConfirmIssuanceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cred = await IssuanceService.confirm_blockchain_registration(db, credential_id, payload.tx_hash)
    return {
        "status": "confirmed",
        "workflow_status": cred.workflow_status,
        "tx_hash": cred.tx_hash,
        "issued_at": cred.issued_at.isoformat() if cred.issued_at else None,
    }

async def _get_user_wallet_address(db: AsyncSession, user_id: str) -> Optional[str]:
    stmt = select(Wallet.address).where(Wallet.user_id == user_id)
    res = await db.execute(stmt)
    return res.scalars().first()

@router.get("/holder/{wallet_address}", response_model=HolderCredentialsResponse, status_code=status.HTTP_200_OK)
async def get_holder_credentials(
    wallet_address: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HolderCredentialsResponse:
    """
    Returns all verifiable credentials belonging to a holder wallet.
    Decrypts credential subjects and salts for authorized holders.
    """
    wallet_norm = wallet_address.lower()
    user_wallet = await _get_user_wallet_address(db, current_user.id)
    user_wallet_norm = (user_wallet or "").lower()

    if user_wallet_norm != wallet_norm and current_user.role != "ADMIN":
        raise TenantAccessDeniedException("Access denied: You can only view your own holder credentials.")

    stmt = select(Credential).where(
        Credential.recipient_address == wallet_norm,
        Credential.workflow_status.in_(["ISSUED", "SIGNED", "CONFIRMED", "REVOKED", "SUSPENDED"])
    ).order_by(Credential.created_at.desc())

    res = await db.execute(stmt)
    creds = res.scalars().all()

    items = []
    for c in creds:
        try:
            subject = EncryptionService.decrypt_subject(
                c.encrypted_subject, c.id, c.organization_id
            )
            salt_bytes = EncryptionService.decrypt_salt(
                c.encrypted_salt, c.id, c.organization_id
            )
            salt_hex = "0x" + salt_bytes.hex()
        except Exception:
            subject = {"error": "Decryption failed or invalid key"}
            salt_hex = "0x"

        w3c_doc = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://w3id.org/security/suites/jcs-eda2019/v1"
            ],
            "id": c.w3c_id,
            "type": ["VerifiableCredential", c.schema_type],
            "issuer": f"did:pkh:eip155:1337:{c.recipient_address}",
            "validFrom": c.issued_at.isoformat() if c.issued_at else c.created_at.isoformat(),
            "credentialSubject": subject,
            "credentialStatus": {
                "id": f"/api/v1/credentials/{c.credential_id}/status",
                "type": "BitstringStatusListEntry",
                "statusPurpose": "revocation"
            },
            "commitment": c.commitment,
            "proof": c.proof_json,
        }
        if c.valid_until:
            w3c_doc["validUntil"] = c.valid_until.isoformat()

        items.append(
            HolderCredentialDetail(
                id=c.id,
                w3c_id=c.w3c_id,
                credential_id=c.credential_id,
                organization_id=c.organization_id,
                recipient_address=c.recipient_address,
                schema_type=c.schema_type,
                commitment=c.commitment,
                workflow_status=c.workflow_status,
                status=c.status,
                tx_hash=c.tx_hash,
                created_at=c.created_at,
                issued_at=c.issued_at,
                valid_until=c.valid_until,
                claims=subject,
                salt=salt_hex,
                w3c_document=w3c_doc,
            )
        )

    return HolderCredentialsResponse(total=len(items), items=items)

@router.post("/presentations", response_model=VerifiablePresentationResponse, status_code=status.HTTP_201_CREATED)
async def create_presentation(
    payload: CreatePresentationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VerifiablePresentationResponse:
    """
    Generates a W3C Verifiable Presentation with selective disclosure and an opaque QR token.
    """
    user_wallet = await _get_user_wallet_address(db, current_user.id)
    user_wallet_norm = (user_wallet or "").lower()
    return await PresentationService.create_presentation(
        db=db,
        holder_address=user_wallet_norm,
        credential_id=payload.credential_id,
        disclosed_attributes=payload.disclosed_attributes,
        audience_did=payload.audience_did,
        expires_in_hours=payload.expires_in_hours,
        holder_signature=payload.holder_signature,
    )

@router.get("/presentations/{token}", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def resolve_presentation_token(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Public resolution endpoint for opaque presentation tokens generated for QR codes.
    """
    return await PresentationService.resolve_presentation(db, token)

@router.get("/{credential_id}", response_model=Dict[str, Any])
async def get_credential(
    credential_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    # Returns decrypted W3C credential for authorized user
    return await IssuanceService.get_verifiable_credential(db, credential_id)

@router.get("", response_model=CredentialListResponse)
async def list_credentials(
    organization_id: Optional[str] = Query(None),
    recipient_address: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CredentialListResponse:
    query = select(Credential)

    if organization_id:
        # Check membership
        mem_stmt = select(OrganizationMembership).where(
            OrganizationMembership.user_id == current_user.id,
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.status == "ACTIVE",
        )
        mem_res = await db.execute(mem_stmt)
        if not mem_res.scalar_one_or_none():
            raise TenantAccessDeniedException("Access denied: Not a member of this organization.")
        query = query.where(Credential.organization_id == organization_id)

    if recipient_address:
        query = query.where(Credential.recipient_address == recipient_address.lower())

    res = await db.execute(query)
    creds = res.scalars().all()

    items = [
        CredentialSummary(
            id=c.id,
            w3c_id=c.w3c_id,
            credential_id=c.credential_id,
            recipient_address=c.recipient_address,
            schema_type=c.schema_type,
            commitment=c.commitment,
            workflow_status=c.workflow_status,
            status=c.status,
            tx_hash=c.tx_hash,
            created_at=c.created_at,
            issued_at=c.issued_at,
            valid_until=c.valid_until,
        )
        for c in creds
    ]

    return CredentialListResponse(total=len(items), items=items)
