import uuid
import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, Text, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin
from backend.app.core.constants import CredentialWorkflowStatus, CredentialLifecycleStatus

class Credential(Base, TimestampMixin):
    """
    Privacy-preserving verifiable credential entity.
    Subject claims and random salts are encrypted at rest using AES-256-GCM.
    Zero plaintext PII or commitment secrets are exposed in table storage.
    """
    __tablename__ = "credentials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # W3C Standards Identifiers
    w3c_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True) # urn:uuid:...
    credential_id: Mapped[str] = mapped_column(String(66), unique=True, nullable=False, index=True) # 32-byte hex for blockchain
    recipient_address: Mapped[str] = mapped_column(String(42), nullable=False, index=True)
    schema_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Privacy-Preserving Cryptographic Anchors
    commitment: Mapped[str] = mapped_column(String(66), unique=True, nullable=False, index=True) # 32-byte hex commitment
    encrypted_salt: Mapped[str] = mapped_column(Text, nullable=False) # AES-256-GCM ciphertext
    encrypted_subject: Mapped[str] = mapped_column(Text, nullable=False) # AES-256-GCM ciphertext
    key_id: Mapped[str] = mapped_column(String(50), default="master-v1", nullable=False)

    # W3C Data Integrity Proof (JSON)
    proof_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Workflow & Lifecycle State Machines
    workflow_status: Mapped[str] = mapped_column(String(50), default=CredentialWorkflowStatus.PREPARED.value, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=CredentialLifecycleStatus.ACTIVE.value, nullable=False) # On-chain lifecycle status
    status_list_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    status_list_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    revocation_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    revoked_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    supersedes_id: Mapped[Optional[str]] = mapped_column(String(66), nullable=True)

    # Provenance & Audit Trails
    tx_hash: Mapped[Optional[str]] = mapped_column(String(66), nullable=True)
    prepared_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    issued_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="credentials")
    issuance_jobs: Mapped[list["IssuanceJob"]] = relationship("IssuanceJob", back_populates="credential", cascade="all, delete-orphan")
