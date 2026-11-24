from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.schemas.authentication import (
    ChallengeRequest,
    ChallengeResponse,
    VerifyWalletRequest,
    AuthResponse,
    SessionResponse,
)
from backend.app.services.authentication_service import AuthenticationService
from backend.app.api.dependencies.auth import get_current_session, get_current_user
from backend.app.models.user import User
from backend.app.models.session import Session

router = APIRouter(prefix="/authentication", tags=["Authentication & Sessions"])

@router.post("/challenge", response_model=ChallengeResponse, status_code=status.HTTP_201_CREATED)
async def request_challenge(
    payload: ChallengeRequest,
    db: AsyncSession = Depends(get_db),
) -> ChallengeResponse:
    nonce, message, expires_at = await AuthenticationService.create_challenge(
        db=db,
        wallet_address=payload.wallet_address,
        chain_id=payload.chain_id,
        domain=payload.domain,
        uri=payload.uri,
    )
    return ChallengeResponse(
        nonce=nonce,
        wallet_address=payload.wallet_address,
        message=message,
        expires_at=expires_at,
    )

@router.post("/verify-wallet", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def verify_wallet(
    payload: VerifyWalletRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    user, session_token, expires_at = await AuthenticationService.verify_wallet_and_create_session(
        db=db,
        wallet_address=payload.wallet_address,
        nonce=payload.nonce,
        signature=payload.signature,
    )

    # Set secure HTTP-only cookie
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_token,
        max_age=settings.SESSION_EXPIRE_SECONDS,
        httponly=True,
        secure=settings.SECURE_COOKIE,
        samesite=settings.SAME_SITE_COOKIE,
        path="/",
    )

    return AuthResponse(
        user_id=user.id,
        wallet_address=payload.wallet_address,
        role=user.role,
        session_token=session_token,
        expires_at=expires_at,
    )

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    session: Session = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    await AuthenticationService.invalidate_session(db, session.id)
    response.delete_cookie(key=settings.SESSION_COOKIE_NAME, path="/")
    return {"status": "logged_out", "message": "Session successfully invalidated."}

@router.get("/session", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def get_session(
    session: Session = Depends(get_current_session),
    user: User = Depends(get_current_user),
) -> SessionResponse:
    return SessionResponse(
        is_authenticated=True,
        user_id=user.id,
        wallet_address=session.wallet_address,
        role=user.role,
        email=user.email,
        full_name=user.full_name,
    )
