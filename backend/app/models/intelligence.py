import uuid
import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, Text, DateTime, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin

class DocumentUpload(Base, TimestampMixin):
    """
    Secure document intake entity for institutional credential extraction.
    Tracks file lifecycle, content hashes, tenant isolation, and processing states.
    """
    __tablename__ = "document_uploads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True) # SHA-256 hex
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)

    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False) # PENDING, PROCESSING, COMPLETED, FAILED
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    extracted_data: Mapped[Optional["ExtractedCredentialData"]] = relationship(
        "ExtractedCredentialData", back_populates="document", uselist=False, cascade="all, delete-orphan"
    )

class ExtractedCredentialData(Base, TimestampMixin):
    """
    Structured OCR / AI extraction result associated with an uploaded document.
    Never bypasses human review or separation-of-duties workflows.
    """
    __tablename__ = "extracted_credential_data"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("document_uploads.id", ondelete="CASCADE"), unique=True, nullable=False)

    schema_type: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_fields_json: Mapped[str] = mapped_column(Text, nullable=False) # JSON: {field_name: {value, confidence, evidence}}
    anomaly_findings_json: Mapped[str] = mapped_column(Text, nullable=False) # JSON: [{rule, severity, description, evidence}]
    overall_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Human-in-the-loop review state
    review_status: Mapped[str] = mapped_column(String(50), default="PENDING_REVIEW", nullable=False) # PENDING_REVIEW, APPROVED, REJECTED
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    credential_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("credentials.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    document: Mapped["DocumentUpload"] = relationship("DocumentUpload", back_populates="extracted_data")
