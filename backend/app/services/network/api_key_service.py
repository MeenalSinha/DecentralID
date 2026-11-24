import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Header, HTTPException, status, Depends
from backend.app.core.database import get_db
from backend.app.models.network import ApiKey


class ApiKeyService:
    @staticmethod
    def hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @classmethod
    async def generate_api_key(
        cls,
        db: AsyncSession,
        organization_id: UUID,
        name: str,
        scopes: Optional[List[str]] = None,
        rate_limit_per_minute: int = 60,
        expires_in_days: Optional[int] = 90
    ) -> Tuple[ApiKey, str]:
        """
        Generates a new API key.
        Returns: (ApiKey model record, raw_secret_key)
        """
        if scopes is None:
            scopes = ["verify", "status"]

        prefix = "did_live_"
        random_token = secrets.token_urlsafe(32)
        raw_key = f"{prefix}{random_token}"
        hashed = cls.hash_key(raw_key)

        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        api_key = ApiKey(
            organization_id=str(organization_id),
            name=name,
            key_prefix=prefix,
            hashed_key=hashed,
            scopes=scopes,
            rate_limit_per_minute=rate_limit_per_minute,
            is_active=True,
            expires_at=expires_at
        )
        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)
        return api_key, raw_key

    @classmethod
    async def verify_api_key(
        cls,
        db: AsyncSession,
        raw_key: str,
        required_scope: Optional[str] = None
    ) -> ApiKey:
        """
        Authenticates a raw API key and checks permissions.
        """
        if not raw_key or not raw_key.startswith("did_live_"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="INVALID_API_KEY_FORMAT"
            )

        hashed = cls.hash_key(raw_key)
        stmt = select(ApiKey).where(ApiKey.hashed_key == hashed)
        res = await db.execute(stmt)
        api_key = res.scalar_one_or_none()

        if not api_key or not api_key.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API_KEY_REVOKED_OR_INVALID"
            )

        if api_key.expires_at:
            now_utc = datetime.now(timezone.utc)
            expires_at = api_key.expires_at if api_key.expires_at.tzinfo else api_key.expires_at.replace(tzinfo=timezone.utc)
            if expires_at < now_utc:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API_KEY_EXPIRED"
                )

        if required_scope and required_scope not in api_key.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"INSUFFICIENT_SCOPE: requires {required_scope}"
            )

        api_key.last_used_at = datetime.now(timezone.utc)
        await db.commit()
        return api_key


async def get_api_key_auth(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db)
) -> ApiKey:
    """
    Dependency to authenticate external requests via X-API-Key header.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MISSING_API_KEY_HEADER"
        )
    return await ApiKeyService.verify_api_key(db=db, raw_key=x_api_key)
