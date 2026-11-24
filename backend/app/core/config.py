from typing import List, Optional
import os
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    API_V1_STR: str = Field(default="/api/v1")
    PROJECT_NAME: str = Field(default="DecentralID Trust Infrastructure")

    # Security & Sessions
    SECRET_KEY: str = Field(default="decentralid-default-development-secret-key-change-in-prod-32bytes")
    SESSION_COOKIE_NAME: str = Field(default="decentralid_session")
    SESSION_EXPIRE_SECONDS: int = Field(default=86400) # 24 hours
    CHALLENGE_EXPIRE_SECONDS: int = Field(default=300) # 5 minutes
    SECURE_COOKIE: bool = Field(default=False) # True in production (HTTPS)
    SAME_SITE_COOKIE: str = Field(default="lax")

    # Database
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./decentralid.db")

    # Blockchain
    CHAIN_ID: int = Field(default=31337) # Hardhat local default
    NETWORK_NAME: str = Field(default="hardhat")
    RPC_URL: str = Field(default="http://127.0.0.1:8545")
    ISSUER_REGISTRY_ADDRESS: Optional[str] = Field(default=None)
    CREDENTIAL_REGISTRY_ADDRESS: Optional[str] = Field(default=None)
    CREDENTIAL_STATUS_REGISTRY_ADDRESS: Optional[str] = Field(default=None)

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    )

    @field_validator("DATABASE_URL", mode="before")
    def validate_database_url(cls, v: str) -> str:
        if not v:
            return "sqlite+aiosqlite:///./decentralid.db"
        # Map postgres:// to postgresql+asyncpg:// if needed
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

settings = Settings()
