from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class VerifyCredentialRequest(BaseModel):
    credential: Optional[Dict[str, Any]] = Field(default=None, description="W3C Verifiable Credential or Verifiable Presentation JSON")
    token: Optional[str] = Field(default=None, description="Opaque Presentation Token from QR code or share link")
    salt: Optional[str] = Field(default=None, description="Optional 32-byte hex salt for commitment verification")

class VerificationChecks(BaseModel):
    structural: bool
    signature: bool
    issuer_authorized: bool
    signing_key_authorized: bool
    commitment_verified: Optional[bool] = None
    not_expired: bool

class VerificationIssuerInfo(BaseModel):
    name: str
    address: str

class VerifyCredentialResponse(BaseModel):
    is_valid: bool
    checks: VerificationChecks
    lifecycle_status: str
    issuer: VerificationIssuerInfo
    signer_address: str
    credential_id: str
    schema_type: Optional[str] = None
    disclosed_claims: Optional[Dict[str, Any]] = None
    is_selective_disclosure: bool = False
    errors: List[str]
    warnings: List[str]
    verified_at: str
