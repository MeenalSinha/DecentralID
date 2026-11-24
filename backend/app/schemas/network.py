from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    scopes: Optional[List[str]] = Field(default=["verify", "status"])
    rate_limit_per_minute: Optional[int] = Field(default=60, ge=1, le=1000)
    expires_in_days: Optional[int] = Field(default=90, ge=1, le=365)


class ApiKeyCreateResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    api_key: str  # ONLY returned once upon creation!
    scopes: List[str]
    rate_limit_per_minute: int
    expires_at: Optional[datetime]
    created_at: datetime


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    key_prefix: str
    scopes: List[str]
    rate_limit_per_minute: int
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime


class WebhookSubscriptionCreateRequest(BaseModel):
    target_url: str = Field(..., min_length=8, max_length=512)
    event_types: Optional[List[str]] = Field(default=["credential.issued", "credential.revoked", "credential.suspended"])


class WebhookSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    target_url: str
    secret_key: str
    event_types: List[str]
    is_active: bool
    created_at: datetime


class WebhookDeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    subscription_id: str
    event_type: str
    payload: Dict[str, Any]
    status: str
    status_code: Optional[int] = None
    attempt_count: int
    created_at: datetime
    delivered_at: Optional[datetime] = None


class DeveloperVerifyRequest(BaseModel):
    presentation: Optional[Dict[str, Any]] = None
    credential: Optional[Dict[str, Any]] = None


class DeveloperVerifyResponse(BaseModel):
    outcome: str = Field(..., description="VALID, INVALID, or INDETERMINATE")
    checks: Dict[str, Any]
    issuer_address: Optional[str] = None
    credential_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class EncryptedStorageResponse(BaseModel):
    cid: str
    size_bytes: int
    provider: str
    encryption_algorithm: str = "AES-256-GCM"
