import uuid
from typing import Optional
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin
from backend.app.core.constants import CredentialLifecycleStatus

class Credential(Base, TimestampMixin):
    __tablename__ = "credentials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    credential_id: Mapped[str] = mapped_column(String(66), unique=True, nullable=False, index=True) # bytes32 hex string
    recipient_address: Mapped[str] = mapped_column(String(42), nullable=False, index=True)
    schema_type: Mapped[str] = mapped_column(String(100), nullable=False)
    commitment: Mapped[str] = mapped_column(String(66), unique=True, nullable=False, index=True) # bytes32 hex string
    salt: Mapped[str] = mapped_column(String(66), nullable=False) # 32-byte hex salt
    subject_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=CredentialLifecycleStatus.ACTIVE.value, nullable=False)
    tx_hash: Mapped[Optional[str]] = mapped_column(String(66), nullable=True)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="credentials")
