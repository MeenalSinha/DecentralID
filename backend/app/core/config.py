from typing import List, Optional
import os
from pydantic import Field, field_validator, model_validator
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
    CREDENTIAL_ENCRYPTION_KEY: Optional[str] = Field(default=None) # AES-256-GCM master key
    SESSION_COOKIE_NAME: str = Field(default="decentralid_session")
    SESSION_EXPIRE_SECONDS: int = Field(default=86400) # 24 hours
    CHALLENGE_EXPIRE_SECONDS: int = Field(default=300) # 5 minutes
    SECURE_COOKIE: bool = Field(default=False) # True in production (HTTPS)
    SAME_SITE_COOKIE: str = Field(default="lax")

    # Allowed SIWE Domains
    ALLOWED_SIWE_DOMAINS: List[str] = Field(
        default=["localhost", "127.0.0.1", "decentralid.org", "app.decentralid.org"]
    )

    # Database
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./decentralid.db")

    # Blockchain
    CHAIN_ID: int = Field(default=31337) # Hardhat local default
    NETWORK_NAME: str = Field(default="hardhat")
    RPC_URL: str = Field(default="http://127.0.0.1:8545")
    ISSUER_REGISTRY_ADDRESS: Optional[str] = Field(default=None)
    CREDENTIAL_REGISTRY_ADDRESS: Optional[str] = Field(default=None)
    CREDENTIAL_STATUS_REGISTRY_ADDRESS: Optional[str] = Field(default=None)

    # Storage & IPFS Network
    PINATA_JWT: Optional[str] = Field(default=None)
    PINATA_GATEWAY: str = Field(default="https://gateway.pinata.cloud/ipfs")
    STORAGE_DIR: str = Field(default="storage")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:3000",
        ]
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

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.ENVIRONMENT.lower() == "production":
            insecure_placeholders = [
                "default-development",
                "change-in-prod",
                "decentralid_dev_secret",
                "decentralid_secure_dev",
                "your_32_byte_hex",
                "your_wallet_private_key",
            ]
            for placeholder in insecure_placeholders:
                if placeholder in self.SECRET_KEY.lower():
                    raise ValueError(f"In production, SECRET_KEY must be a cryptographically secure random value and cannot contain development placeholder '{placeholder}'.")
            if len(self.SECRET_KEY) < 32:
                raise ValueError("In production, SECRET_KEY must be a cryptographically secure random value with at least 32 characters.")
            if not self.SECURE_COOKIE:
                raise ValueError("In production, SECURE_COOKIE must be enabled (True) for HTTPS security.")
            if self.CREDENTIAL_ENCRYPTION_KEY:
                for placeholder in insecure_placeholders:
                    if placeholder in self.CREDENTIAL_ENCRYPTION_KEY.lower():
                        raise ValueError(f"In production, CREDENTIAL_ENCRYPTION_KEY cannot contain development placeholder '{placeholder}'.")
                if len(self.CREDENTIAL_ENCRYPTION_KEY) < 32:
                    raise ValueError("In production, CREDENTIAL_ENCRYPTION_KEY must be at least 32 characters.")
            if "decentralid_secure_dev_password" in self.DATABASE_URL:
                raise ValueError("In production, DATABASE_URL must not use the development fallback password.")
        return self

settings = Settings()
