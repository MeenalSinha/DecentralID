import uuid
from typing import Optional, List
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin
from backend.app.core.constants import OrganizationStatus, MembershipStatus, UserRole, SigningKeyStatus

class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_entity_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=OrganizationStatus.PENDING_REVIEW.value, nullable=False)
    on_chain_address: Mapped[Optional[str]] = mapped_column(String(42), unique=True, nullable=True, index=True)

    memberships: Mapped[List["OrganizationMembership"]] = relationship("OrganizationMembership", back_populates="organization", cascade="all, delete-orphan")
    signing_keys: Mapped[List["SigningKey"]] = relationship("SigningKey", back_populates="organization", cascade="all, delete-orphan")
    credentials: Mapped[List["Credential"]] = relationship("Credential", back_populates="organization")

class OrganizationMembership(Base, TimestampMixin):
    __tablename__ = "organization_memberships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), default=UserRole.AUTHORIZED_ISSUER.value, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=MembershipStatus.ACTIVE.value, nullable=False)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="memberships")
    user: Mapped["User"] = relationship("User", back_populates="memberships")

class SigningKey(Base, TimestampMixin):
    __tablename__ = "signing_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    public_key_address: Mapped[str] = mapped_column(String(42), nullable=False, index=True)
    key_type: Mapped[str] = mapped_column(String(50), default="secp256k1", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=SigningKeyStatus.ACTIVE.value, nullable=False)
    valid_until: Mapped[Optional[int]] = mapped_column(nullable=True)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="signing_keys")
