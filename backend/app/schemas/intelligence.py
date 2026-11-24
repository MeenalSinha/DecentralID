import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class DocumentUploadResponse(BaseModel):
    id: str
    organization_id: str
    filename: str
    file_hash: str
    mime_type: str
    file_size: int
    status: str
    created_at: datetime.datetime

class ExtractedFieldDetail(BaseModel):
    value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_snippet: Optional[str] = None
    is_valid: bool = True
    human_corrected: bool = False

class AnomalyFinding(BaseModel):
    rule: str
    severity: str = Field(..., description="One of: LOW, MEDIUM, HIGH, CRITICAL")
    description: str
    evidence: Optional[str] = None

class ExtractionDetailResponse(BaseModel):
    id: str
    document_id: str
    filename: str
    mime_type: str
    status: str
    schema_type: str
    raw_text: str
    extracted_fields: Dict[str, ExtractedFieldDetail]
    anomaly_findings: List[AnomalyFinding]
    overall_confidence: float
    review_status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime.datetime] = None
    credential_id: Optional[str] = None
    created_at: datetime.datetime

class ReviewExtractionRequest(BaseModel):
    review_action: str = Field(..., description="'APPROVE', 'REJECT', or 'UPDATE'")
    schema_type: Optional[str] = None
    corrected_fields: Optional[Dict[str, Any]] = None

class PrepareFromExtractionRequest(BaseModel):
    recipient_address: str = Field(..., description="Holder Ethereum wallet address 0x...")
    valid_until: Optional[datetime.datetime] = None
