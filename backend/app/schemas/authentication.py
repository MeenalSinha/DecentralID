import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class ChallengeRequest(BaseModel):
    wallet_address: str = Field(..., pattern="^0x[a-fA-F0-9]{40}$")
    chain_id: int
    domain: str = Field(default="localhost")
    uri: str = Field(default="http://localhost:5173")

class ChallengeResponse(BaseModel):
    nonce: str
    wallet_address: str
    message: str
    expires_at: str

class VerifyWalletRequest(BaseModel):
    wallet_address: str = Field(..., pattern="^0x[a-fA-F0-9]{40}$")
    nonce: str = Field(..., min_length=16)
    signature: str = Field(..., pattern="^0x[a-fA-F0-9]{130}$")

class AuthResponse(BaseModel):
    user_id: str
    wallet_address: str
    role: str
    expires_at: str

class SessionResponse(BaseModel):
    is_authenticated: bool
    user_id: Optional[str] = None
    wallet_address: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
