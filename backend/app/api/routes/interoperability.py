from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.credential import Credential
from backend.app.api.dependencies.auth import get_current_user
from backend.app.schemas.interoperability import (
    DIDResolutionResult,
    CredentialExportRequest,
    CredentialExportResponse,
    CredentialImportRequest,
    CredentialImportResponse,
    ExternalVerificationRequest,
    ExternalVerificationResponse
)
from backend.app.services.interoperability.did_resolver import universal_did_resolver, DIDResolutionError
from backend.app.services.interoperability.credential_portability import CredentialPortabilityService, CredentialPortabilityError
from backend.app.services.interoperability.external_verifier import ExternalVerificationAdapter

router = APIRouter(prefix="/interop", tags=["Interoperability & Standards"])

@router.get("/resolve/{did:path}", response_model=DIDResolutionResult)
async def resolve_did(did: str):
    """
    W3C Universal DID Resolution Endpoint.
    Supports did:pkh, did:key, and did:web methods.
    """
    try:
        result = await universal_did_resolver.resolve(did)
        return result
    except DIDResolutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": e.code, "message": str(e)}
        )

@router.post("/credentials/export", response_model=CredentialExportResponse)
async def export_credential(
    request: CredentialExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exports a DecentralID credential into standardized W3C Verifiable Credentials Data Model (v1.1 or v2.0).
    """
    result = await db.execute(
        select(Credential).where(Credential.id == request.credential_id)
    )
    cred = result.scalars().first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
        
    doc = cred.credential_document or {}
    
    if request.target_format.lower() in ("w3c-v2", "v2"):
        exported_vc = CredentialPortabilityService.export_credential_w3c_v2(doc)
    else:
        exported_vc = CredentialPortabilityService.export_credential_w3c_v1(doc)
        
    return CredentialExportResponse(
        credential_id=cred.id,
        format=request.target_format,
        verifiable_credential=exported_vc
    )

@router.post("/credentials/import", response_model=CredentialImportResponse)
async def import_credential(
    request: CredentialImportRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Imports an external W3C credential into the user's wallet space.
    Strictly preserves external provenance and prevents foreign credentials from claiming DecentralID issuance.
    """
    try:
        import_record = CredentialPortabilityService.import_external_credential(request.raw_credential)
        return CredentialImportResponse(**import_record)
    except CredentialPortabilityError as e:
        raise HTTPException(status_code=e.status_code, detail={"error": e.error_code, "message": str(e)})

@router.post("/verify-external", response_model=ExternalVerificationResponse)
async def verify_external(
    request: ExternalVerificationRequest
):
    """
    Cross-platform W3C Data Integrity verification adapter.
    Resolves external issuer DIDs, cryptographically validates signatures, and returns machine-readable outcomes.
    """
    outcome = await ExternalVerificationAdapter.verify_external_document(
        document=request.credential_or_presentation,
        expected_issuer_did=request.expected_issuer_did
    )
    return ExternalVerificationResponse(**outcome)

@router.get("/well-known/openid-credential-issuer")
async def openid_credential_issuer_metadata():
    """
    OpenID for Verifiable Credential Issuance (OID4VCI) Discovery Metadata.
    """
    return {
        "credential_issuer": "https://decentralid.digital",
        "credential_endpoint": "https://decentralid.digital/api/v1/credentials",
        "credential_response_encryption": {
            "alg_values_supported": ["ECDH-ES"],
            "enc_values_supported": ["A256GCM"]
        },
        "credentials_supported": [
            {
                "format": "ldp_vc",
                "id": "AcademicDegreeCredential",
                "types": ["VerifiableCredential", "AcademicDegreeCredential"],
                "cryptographic_suites_supported": ["ecdsa-jcs-2019"]
            },
            {
                "format": "ldp_vc",
                "id": "EmploymentCredential",
                "types": ["VerifiableCredential", "EmploymentCredential"],
                "cryptographic_suites_supported": ["ecdsa-jcs-2019"]
            }
        ]
    }
