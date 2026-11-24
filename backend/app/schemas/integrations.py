from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class EducationRecordSyncRequest(BaseModel):
    system_type: str = Field(..., description="CANVAS, MOODLE, BANNER, PEOPLESOFT")
    schema_type: str = Field("ACADEMIC_DEGREE", description="Target credential schema")
    records: List[Dict[str, Any]] = Field(..., description="List of student course/degree records")

class EducationRecordSyncResponse(BaseModel):
    total_received: int
    valid_drafts_created: int
    duplicates_rejected: int
    validation_failures: int
    draft_ids: List[str]
    errors: List[Dict[str, Any]] = Field(default_factory=list)

class HRCandidateVerificationRequest(BaseModel):
    candidate_id: str
    employer_name: str
    required_claims: List[str] = Field(default=["degree", "institution", "graduation_year"])
    verifiable_presentation: Dict[str, Any]

class HRCandidateVerificationResponse(BaseModel):
    verification_id: str
    candidate_id: str
    employer_name: str
    is_verified: bool
    status: str
    verified_claims: Dict[str, Any] = Field(default_factory=dict)
    unauthorized_data_exposed: bool = False
    verified_at: datetime

class BulkMigrationPreviewRequest(BaseModel):
    schema_type: str
    field_mappings: Dict[str, str] # e.g. {"Roll_No": "student_id", "Course_Name": "degree"}
    raw_records: List[Dict[str, Any]]

class BulkMigrationPreviewResponse(BaseModel):
    total_records: int
    valid_records: int
    duplicate_records: int
    invalid_records: int
    preview_sample: List[Dict[str, Any]]
    field_errors: List[Dict[str, Any]] = Field(default_factory=list)

class BulkMigrationExecuteRequest(BaseModel):
    schema_type: str
    field_mappings: Dict[str, str]
    records: List[Dict[str, Any]]

class BulkMigrationExecuteResponse(BaseModel):
    batch_id: str
    imported_count: int
    skipped_count: int
    status: str
    next_step: str = "Awaiting institutional officer preparation and separation-of-duties review"

class ConnectorHealthStatus(BaseModel):
    connector_name: str
    system_type: str
    is_healthy: bool
    last_sync: Optional[datetime] = None
    successful_syncs: int
    failed_syncs: int
    status_message: str
