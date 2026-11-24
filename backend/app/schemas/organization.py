from typing import Optional, List
from pydantic import BaseModel, Field
from backend.app.core.constants import UserRole, OrganizationStatus, MembershipStatus

class OrganizationCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    legal_entity_id: Optional[str] = Field(default=None, max_length=100)
    domain: Optional[str] = Field(default=None, max_length=255)
    on_chain_address: Optional[str] = Field(default=None, pattern="^0x[a-fA-F0-9]{40}$")

class OrganizationResponse(BaseModel):
    id: str
    name: str
    legal_entity_id: Optional[str]
    domain: Optional[str]
    status: str
    on_chain_address: Optional[str]
    created_at: str

class MemberInviteRequest(BaseModel):
    user_address: str = Field(..., pattern="^0x[a-fA-F0-9]{40}$")
    role: UserRole = Field(default=UserRole.AUTHORIZED_ISSUER)

class MemberResponse(BaseModel):
    id: str
    user_id: str
    wallet_address: str
    role: str
    status: str
    created_at: str
