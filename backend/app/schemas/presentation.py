from typing import Dict, Any, List, Optional
import datetime
from pydantic import BaseModel, Field

class CreatePresentationRequest(BaseModel):
    credential_id: str = Field(..., description="The ID of the credential being presented")
    disclosed_attributes: Optional[List[str]] = Field(
        default=None,
        description="List of claim keys to disclose. If omitted or empty, all claims are disclosed."
    )
    audience_did: Optional[str] = Field(
        default=None,
        description="Optional recipient verifier DID, e.g. did:pkh:eip155:1337:0x..."
    )
    expires_in_hours: int = Field(default=24, ge=1, le=168, description="Presentation link validity window")
    holder_signature: Optional[str] = Field(
        default=None,
        description="Optional holder signature over presentation challenge if client-side signing enabled"
    )

class VerifiablePresentationResponse(BaseModel):
    id: str
    token: str
    share_url: str
    credential_id: str
    holder_address: str
    expires_at: datetime.datetime
    disclosed_claims: Dict[str, Any]
    masked_claims: List[str]
    presentation_document: Dict[str, Any]

class HolderCredentialDetail(BaseModel):
    id: str
    w3c_id: str
    credential_id: str
    organization_id: str
    recipient_address: str
    schema_type: str
    commitment: str
    workflow_status: str
    status: str
    tx_hash: Optional[str] = None
    created_at: datetime.datetime
    issued_at: Optional[datetime.datetime] = None
    valid_until: Optional[datetime.datetime] = None
    claims: Dict[str, Any]
    w3c_document: Dict[str, Any]

class HolderCredentialsResponse(BaseModel):
    total: int
    items: List[HolderCredentialDetail]
