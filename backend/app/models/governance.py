import uuid
import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, ForeignKey
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin

class InstitutionAccreditation(Base, TimestampMixin):
    __tablename__ = "institution_accreditations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    category = Column(String(64), nullable=False) # UNIVERSITY, COLLEGE, VOCATIONAL, REGULATORY_BODY, ENTERPRISE
    status = Column(String(32), nullable=False, default="APPLIED") # APPLIED, UNDER_REVIEW, EVIDENCE_REQUESTED, APPROVED, REJECTED, SUSPENDED, EXPIRED
    authorized_schemas = Column(JSON, nullable=False, default=list) # e.g. ["ACADEMIC_DEGREE", "SKILL_CERTIFICATE"]
    evidence_urls = Column(JSON, nullable=False, default=list) # CIDs or storage hashes of accreditation documents
    
    reviewer_id = Column(String(36), nullable=True) # First-stage review officer
    senior_approver_id = Column(String(36), nullable=True) # Second-stage senior governance approver
    
    rejection_reason = Column(String(256), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    risk_score = Column(Integer, default=0, nullable=False) # 0 to 100 risk assessment

class GovernanceAuditLog(Base):
    __tablename__ = "governance_audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    accreditation_id = Column(String(36), ForeignKey("institution_accreditations.id", ondelete="CASCADE"), nullable=False)
    actor_id = Column(String(36), nullable=False)
    action = Column(String(64), nullable=False) # SUBMIT, ASSIGN_REVIEWER, REQUEST_EVIDENCE, APPROVE, REJECT, SUSPEND, REINSTATE
    details = Column(JSON, nullable=False, default=dict)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
