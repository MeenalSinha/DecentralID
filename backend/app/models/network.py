import uuid
import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, ForeignKey, Text, DateTime, Integer, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin


class ApiKey(Base, TimestampMixin):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    hashed_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    scopes: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=lambda: ["verify", "status"])
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class WebhookSubscription(Base, TimestampMixin):
    __tablename__ = "webhook_subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    target_url: Mapped[str] = mapped_column(String(512), nullable=False)
    secret_key: Mapped[str] = mapped_column(String(128), nullable=False)
    event_types: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=lambda: ["credential.issued", "credential.revoked", "credential.suspended"])
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id: Mapped[str] = mapped_column(String(36), ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING", index=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    delivered_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class StorageRecord(Base):
    __tablename__ = "storage_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    cid: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False, default="application/json+encrypted")
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    encryption_algorithm: Mapped[str] = mapped_column(String(32), nullable=False, default="AES-256-GCM")
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="local")
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
