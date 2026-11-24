import datetime
import hashlib
from typing import Optional, List
from fastapi import Request, Depends, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.core.exceptions import AuthenticationFailedException, TenantAccessDeniedException
from backend.app.models.user import User
from backend.app.models.session import Session
from backend.app.services.authorization_service import AuthorizationService

async def get_current_session(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Session:
    # 1. Check HTTP-only cookie first
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)

    # 2. Check Authorization Bearer header as fallback
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()

    if not token:
        raise AuthenticationFailedException("Authentication required: no active session token found.")

    # 3. Query DB using cryptographic SHA-256 hash of the token
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    stmt = select(Session).where(Session.id == token_hash)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()

    if not session or session.is_revoked:
        raise AuthenticationFailedException("Session is invalid or has been revoked.")

    now = datetime.datetime.now(datetime.timezone.utc)
    exp = session.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=datetime.timezone.utc)

    if now > exp:
        session.is_revoked = True
        await db.commit()
        raise AuthenticationFailedException("Session has expired. Please log in again.")

    return session

async def get_current_user(
    session: Session = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> User:
    stmt = select(User).where(User.id == session.user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not user.is_active:
        raise AuthenticationFailedException("User account does not exist or has been suspended.")

    return user

def require_role(allowed_roles: List[str]):
    async def role_dependency(user: User = Depends(get_current_user)) -> User:
        if not AuthorizationService.check_user_role(user, allowed_roles):
            raise TenantAccessDeniedException(
                f"Action requires one of the following roles: {', '.join(allowed_roles)}"
            )
        return user
    return role_dependency
