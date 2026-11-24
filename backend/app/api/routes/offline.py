from fastapi import APIRouter
from backend.app.schemas.offline import OfflineVerificationRequest, OfflineVerificationResponse
from backend.app.services.offline.offline_verifier import OfflineVerificationService

router = APIRouter(prefix="/offline", tags=["Mobile & Offline Verification"])

@router.post("/verify", response_model=OfflineVerificationResponse)
async def verify_offline_credential(request: OfflineVerificationRequest):
    """
    Offline Verification Endpoint.
    Validates cryptographic proofs and strictly enforces the Critical Freshness Rule:
    Stale status snapshots return INDETERMINATE, never a false VALID.
    """
    outcome = OfflineVerificationService.verify_offline_package(
        package=request.offline_package,
        max_offline_age_seconds=request.max_offline_age_seconds
    )
    return OfflineVerificationResponse(**outcome)
