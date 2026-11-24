import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class LifecycleActionRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=128, description="Audit reason for status change")

class RenewCredentialRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=128, description="Reason for renewal / replacement")
    updated_claims: Dict[str, Any] = Field(..., description="Updated claim set for replacement credential")
    valid_until: Optional[datetime.datetime] = None

class LifecycleActionResponse(BaseModel):
    credential_id: str
    status: str
    workflow_status: str
    revocation_reason: Optional[str] = None
    revoked_at: Optional[datetime.datetime] = None
    updated_at: datetime.datetime
