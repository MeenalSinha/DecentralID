from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.core.exceptions import ValidationException
from backend.app.schemas.verification import (
    VerifyCredentialRequest,
    VerifyCredentialResponse,
    VerificationChecks,
    VerificationIssuerInfo,
)
from backend.app.services.credential.verification_service import VerificationService
from backend.app.services.credential.presentation_service import PresentationService

router = APIRouter(prefix="/verification", tags=["Independent Verification Engine"])

@router.post("/verify", response_model=VerifyCredentialResponse, status_code=status.HTTP_200_OK)
async def verify_credential(
    payload: VerifyCredentialRequest,
    db: AsyncSession = Depends(get_db),
) -> VerifyCredentialResponse:
    target_cred = payload.credential
    salt_bytes = bytes.fromhex(payload.salt[2:] if payload.salt.startswith("0x") else payload.salt) if payload.salt else None

    # Resolve presentation token if provided
    if not target_cred and payload.token:
        target_cred = await PresentationService.resolve_presentation(db, payload.token)

    if not target_cred:
        raise ValidationException("Either 'credential' or 'token' must be provided for verification.")

    result = await VerificationService.verify_credential(
        credential=target_cred,
        db=db,
        salt=salt_bytes,
    )

    return VerifyCredentialResponse(
        is_valid=result.is_valid,
        checks=VerificationChecks(**result.to_dict()["checks"]),
        lifecycle_status=result.lifecycle_status,
        issuer=VerificationIssuerInfo(**result.to_dict()["issuer"]),
        signer_address=result.signer_address,
        credential_id=result.credential_id,
        schema_type=result.schema_type,
        disclosed_claims=result.disclosed_claims,
        is_selective_disclosure=result.is_selective_disclosure,
        errors=result.errors,
        warnings=result.warnings,
        verified_at=result.to_dict()["verified_at"],
    )

@router.get("/presentation/{token}", status_code=status.HTTP_200_OK)
async def resolve_presentation(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Public QR code presentation link resolver."""
    return await PresentationService.resolve_presentation(db, token)
