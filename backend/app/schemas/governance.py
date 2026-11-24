from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class AccreditationApplicationRequest(BaseModel):
    category: str = Field(..., description="UNIVERSITY, COLLEGE, VOCATIONAL, REGULATORY_BODY, ENTERPRISE")
    requested_schemas: List[str] = Field(..., description="List of credential schemas, e.g. ['ACADEMIC_DEGREE']")
    evidence_urls: List[str] = Field(default_factory=list, description="CIDs or storage hashes of accreditation documents")

class AccreditationReviewRequest(BaseModel):
    action: str = Field(..., description="REQUEST_EVIDENCE, FORWARD_SENIOR, REJECT")
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None

class AccreditationApprovalRequest(BaseModel):
    approved: bool
    authorized_schemas: List[str]
    valid_days: int = Field(365, description="Accreditation validity duration in days")
    rejection_reason: Optional[str] = None

class TrustPolicyEvaluationRequest(BaseModel):
    institution_address: str
    credential_schema: str
    signing_key_address: Optional[str] = None

class TrustPolicyEvaluationResponse(BaseModel):
    is_trusted: bool
    verdict: str # TRUSTED, ACCREDITATION_EXPIRED, ACCREDITATION_SUSPENDED, SCHEMA_UNAUTHORIZED, KEY_UNAUTHORIZED, INSTITUTION_UNKNOWN
    category: Optional[str] = None
    accreditation_status: str
    authorized_schemas: List[str] = Field(default_factory=list)
    policy_reason: str
    expires_at: Optional[datetime] = None

class PublicDirectoryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    institution_name: str
    category: str
    verification_identity: str # On-chain address or DID
    accreditation_status: str
    authorized_schemas: List[str]
    valid_until: Optional[datetime] = None
