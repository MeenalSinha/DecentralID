from typing import Dict, Any, Optional, List
import datetime
from pydantic import BaseModel, Field

class PrepareCredentialRequest(BaseModel):
    organization_id: str
    recipient_address: str = Field(..., pattern="^0x[a-fA-F0-9]{40}$")
    schema_type: str = Field(..., description="Registered schema type, e.g. UniversityDegreeCredential")
    claims: Dict[str, Any]
    valid_until: Optional[datetime.datetime] = None

class PrepareCredentialResponse(BaseModel):
    id: str
    w3c_id: str
    credential_id: str
    recipient_address: str
    schema_type: str
    commitment: str
    workflow_status: str
    credential_document: Dict[str, Any]

class SignCredentialRequest(BaseModel):
    private_key: str = Field(..., description="Issuer operational signing key private key (hex)")

class CompleteSigningRequest(BaseModel):
    signature: str = Field(..., description="Cryptographic ECDSA signature (0x...) from client wallet or KMS")
    signer_address: str = Field(..., pattern="^0x[a-fA-F0-9]{40}$", description="Public address of the authorized operational signer")
    cryptosuite: Optional[str] = Field(default="ecdsa-jcs-2019", description="Cryptographic suite: 'ecdsa-jcs-2019' or 'ecdsa-jcs-2019-keccak'")

class ConfirmIssuanceRequest(BaseModel):
    tx_hash: str = Field(..., pattern="^0x[a-fA-F0-9]{64}$")

class CredentialSummary(BaseModel):
    id: str
    w3c_id: str
    credential_id: str
    recipient_address: str
    schema_type: str
    commitment: str
    workflow_status: str
    status: str
    tx_hash: Optional[str] = None
    created_at: datetime.datetime
    issued_at: Optional[datetime.datetime] = None
    valid_until: Optional[datetime.datetime] = None

class CredentialListResponse(BaseModel):
    total: int
    items: List[CredentialSummary]

class BatchCredentialItem(BaseModel):
    recipient_address: str = Field(..., pattern="^0x[a-fA-F0-9]{40}$")
    claims: Dict[str, Any]
    valid_until: Optional[datetime.datetime] = None

class BatchPrepareRequest(BaseModel):
    organization_id: str
    schema_type: str
    items: List[BatchCredentialItem]

class BatchItemResult(BaseModel):
    index: int
    recipient_address: str
    success: bool
    credential_id: Optional[str] = None
    commitment: Optional[str] = None
    error: Optional[str] = None

class BatchPrepareResponse(BaseModel):
    total: int
    successful_count: int
    failed_count: int
    results: List[BatchItemResult]
