import uuid
from typing import Optional
from sqlalchemy import String, Integer, LargeBinary, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TimestampMixin

class StatusList(Base, TimestampMixin):
    """
    W3C Bitstring Status List 1.0 entity.
    Maintains cryptographically verifiable, high-density revocation and suspension bitstrings.
    """
    __tablename__ = "status_lists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    list_number: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Purpose: "revocation" or "suspension"
    purpose: Mapped[str] = mapped_column(String(50), default="revocation", nullable=False)
    
    # Capacity: default 16,384 bits (2,048 bytes)
    bit_length: Mapped[int] = mapped_column(Integer, default=16384, nullable=False)
    current_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Raw uncompressed bitstring bytes
    raw_bits: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    
    # Compressed and multibase-encoded list (uH4sI...)
    encoded_list: Mapped[str] = mapped_column(Text, nullable=False)
