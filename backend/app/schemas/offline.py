from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class OfflineVerificationRequest(BaseModel):
    offline_package: Dict[str, Any]
    max_offline_age_seconds: int = Field(86400, description="Maximum permitted offline snapshot age in seconds")

class OfflineVerificationResponse(BaseModel):
    is_valid: bool
    status: str # VALID_OFFLINE, INDETERMINATE, REVOKED, SUSPENDED, INVALID
    signer_address: Optional[str] = None
    age_seconds: Optional[float] = None
    freshness: Optional[str] = None
    error_code: Optional[str] = None
    reason: Optional[str] = None
    disclosed_subject: Optional[Dict[str, Any]] = None
