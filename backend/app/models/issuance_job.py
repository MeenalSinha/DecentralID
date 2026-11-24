import uuid
from typing import Optional
from sqlalchemy import String, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin
from backend.app.core.constants import IssuanceJobStatus

class IssuanceJob(Base, TimestampMixin):
    """
    Transactional outbox & reconciliation job for reliable blockchain issuance.
    Handles network timeouts, gas repricing, and multi-system consistency.
    """
    __tablename__ = "issuance_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    credential_id: Mapped[str] = mapped_column(String(36), ForeignKey("credentials.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status: Mapped[str] = mapped_column(String(50), default=IssuanceJobStatus.PENDING.value, nullable=False, index=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    
    tx_hash: Mapped[Optional[str]] = mapped_column(String(66), nullable=True)
    confirmed_block: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    credential: Mapped["Credential"] = relationship("Credential", back_populates="issuance_jobs")
