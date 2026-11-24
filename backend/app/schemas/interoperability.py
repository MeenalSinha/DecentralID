from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict

class DIDResolutionRequest(BaseModel):
    did: str = Field(..., description="The Decentralized Identifier to resolve")

class VerificationMethodSchema(BaseModel):
    id: str
    type: str
    controller: str
    publicKeyJwk: Optional[Dict[str, Any]] = None
    publicKeyMultibase: Optional[str] = None
    blockchainAccountId: Optional[str] = None

class DIDDocumentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: str
    alsoKnownAs: Optional[List[str]] = None
    verificationMethod: List[Dict[str, Any]] = Field(default_factory=list)
    authentication: List[str] = Field(default_factory=list)
    assertionMethod: List[str] = Field(default_factory=list)

class DIDResolutionResult(BaseModel):
    did_document: Optional[Dict[str, Any]] = Field(None, alias="didDocument")
    did_resolution_metadata: Dict[str, Any] = Field(default_factory=dict, alias="didResolutionMetadata")
    did_document_metadata: Dict[str, Any] = Field(default_factory=dict, alias="didDocumentMetadata")

    model_config = ConfigDict(populate_by_name=True)

class CredentialExportRequest(BaseModel):
    credential_id: str
    target_format: str = Field("w3c-v2", description="Target W3C format: 'w3c-v2' or 'w3c-v1'")

class CredentialExportResponse(BaseModel):
    credential_id: str
    format: str
    verifiable_credential: Dict[str, Any]

class CredentialImportRequest(BaseModel):
    raw_credential: Dict[str, Any] = Field(..., description="External W3C Verifiable Credential JSON")

class CredentialImportResponse(BaseModel):
    imported_id: str
    origin_issuer: str
    credential_subject: Dict[str, Any]
    is_imported: bool = True
    cryptographic_suite: str
    provenance_verified: bool

class ExternalVerificationRequest(BaseModel):
    credential_or_presentation: Dict[str, Any]
    expected_issuer_did: Optional[str] = None

class ExternalVerificationResponse(BaseModel):
    is_valid: bool
    status: str
    error_code: Optional[str] = None
    issuer_did: Optional[str] = None
    verification_method_used: Optional[str] = None
    cryptosuite: Optional[str] = None
    claims_disclosed: Optional[Dict[str, Any]] = None
