import secrets
import datetime
import hashlib
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from backend.app.models.user import User, Wallet
from backend.app.models.session import Session, AuthChallenge
from backend.app.core.config import settings
from backend.app.core.constants import UserRole
from backend.app.core.exceptions import (
    AuthenticationFailedException,
    NonceExpiredOrInvalidException,
    InvalidSignatureException,
)
from backend.app.services.wallet_verification_service import WalletVerificationService
from backend.app.core.logging import logger

class AuthenticationService:
    @staticmethod
    async def create_challenge(
        db: AsyncSession,
        wallet_address: str,
        chain_id: int,
        domain: str,
        uri: str,
    ) -> Tuple[str, str, str]:
        # Validate domain against whitelist to prevent phishing attacks (EIP-4361 requirement)
        if domain not in settings.ALLOWED_SIWE_DOMAINS:
            logger.warning(
                f"Unauthorized domain in challenge request: {domain}",
                extra={"event": "AUTH_INVALID_DOMAIN", "domain": domain}
            )
            raise AuthenticationFailedException(f"Domain '{domain}' is not authorized for authentication.")

        if not (uri.startswith("http://") or uri.startswith("https://")):
            raise AuthenticationFailedException("Authentication URI must use http or https protocol.")

        # Generate cryptographically secure 32-hex-char nonce
        nonce = secrets.token_hex(16)
        now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = now + datetime.timedelta(seconds=settings.CHALLENGE_EXPIRE_SECONDS)

        # Build EIP-4361 standard message
        message = WalletVerificationService.construct_siwe_message(
            domain=domain,
            address=wallet_address,
            uri=uri,
            version="1",
            chain_id=chain_id,
            nonce=nonce,
            issued_at=now,
            expiration_time=expires_at,
        )

        challenge = AuthChallenge(
            nonce=nonce,
            wallet_address=wallet_address.lower(),
            chain_id=chain_id,
            domain=domain,
            uri=uri,
            expires_at=expires_at,
            is_used=False,
        )
        db.add(challenge)
        await db.commit()

        logger.info(
            f"Generated auth challenge for wallet {wallet_address}",
            extra={"event": "AUTH_CHALLENGE_CREATED", "wallet": wallet_address}
        )
        return nonce, message, expires_at.isoformat()

    @staticmethod
    async def verify_wallet_and_create_session(
        db: AsyncSession,
        wallet_address: str,
        nonce: str,
        signature: str,
    ) -> Tuple[User, str, str]:
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # 1. Fetch challenge
        stmt = select(AuthChallenge).where(
            AuthChallenge.nonce == nonce,
            AuthChallenge.wallet_address == wallet_address.lower()
        )
        res = await db.execute(stmt)
        challenge = res.scalar_one_or_none()

        if not challenge:
            logger.warning(f"Nonce not found: {nonce}", extra={"event": "AUTH_NONCE_NOT_FOUND"})
            raise NonceExpiredOrInvalidException("Challenge nonce was not found.")

        # 2. Check if already used
        if challenge.is_used:
            logger.warning(
                f"Replay attack detected for nonce {nonce} from wallet {wallet_address}",
                extra={"event": "AUTH_REPLAY_ATTEMPT", "wallet": wallet_address}
            )
            raise NonceExpiredOrInvalidException("Challenge nonce has already been consumed (replay prevention).")

        # 3. Check expiration
        exp = challenge.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=datetime.timezone.utc)

        if now > exp:
            logger.warning(f"Expired nonce {nonce}", extra={"event": "AUTH_NONCE_EXPIRED"})
            await db.execute(
                update(AuthChallenge)
                .where(AuthChallenge.nonce == nonce)
                .values(is_used=True)
            )
            await db.commit()
            raise NonceExpiredOrInvalidException("Authentication challenge has expired.")

        # 4. Atomically consume nonce to eliminate concurrent replay race conditions
        consume_stmt = (
            update(AuthChallenge)
            .where(
                AuthChallenge.nonce == nonce,
                AuthChallenge.wallet_address == wallet_address.lower(),
                AuthChallenge.is_used == False,
            )
            .values(is_used=True)
        )
        consume_res = await db.execute(consume_stmt)
        if consume_res.rowcount != 1:
            logger.warning(
                f"Concurrent nonce consumption race detected for nonce {nonce}",
                extra={"event": "AUTH_CONCURRENCY_RACE_DETECTED", "wallet": wallet_address}
            )
            raise NonceExpiredOrInvalidException("Challenge nonce has already been consumed (replay prevention).")

        # 5. Reconstruct message and verify cryptographic signature
        message = WalletVerificationService.construct_siwe_message(
            domain=challenge.domain,
            address=wallet_address,
            uri=challenge.uri,
            version="1",
            chain_id=challenge.chain_id,
            nonce=challenge.nonce,
            issued_at=challenge.created_at if challenge.created_at.tzinfo else challenge.created_at.replace(tzinfo=datetime.timezone.utc),
            expiration_time=exp,
        )

        is_valid = WalletVerificationService.verify_signature(
            message=message,
            signature=signature,
            expected_address=wallet_address,
        )

        if not is_valid:
            await db.commit()
            logger.warning(
                f"Invalid signature submitted for wallet {wallet_address}",
                extra={"event": "AUTH_INVALID_SIGNATURE", "wallet": wallet_address}
            )
            raise InvalidSignatureException("Signature recovery failed; signer does not match expected address.")

        # 6. Find or create User and Wallet
        wallet_stmt = select(Wallet).where(Wallet.address == wallet_address.lower())
        wallet_res = await db.execute(wallet_stmt)
        wallet = wallet_res.scalar_one_or_none()

        if wallet:
            user_stmt = select(User).where(User.id == wallet.user_id)
            user_res = await db.execute(user_stmt)
            user = user_res.scalar_one()
        else:
            user = User(
                full_name=None,
                role=UserRole.HOLDER.value,
                is_active=True,
            )
            db.add(user)
            await db.flush()

            wallet = Wallet(
                user_id=user.id,
                address=wallet_address.lower(),
                chain_id=challenge.chain_id,
                is_primary=True,
            )
            db.add(wallet)

        # 7. Generate session token and store its cryptographic SHA-256 hash in DB
        raw_session_token = secrets.token_urlsafe(32)
        session_token_hash = hashlib.sha256(raw_session_token.encode("utf-8")).hexdigest()
        session_expires = now + datetime.timedelta(seconds=settings.SESSION_EXPIRE_SECONDS)

        session = Session(
            id=session_token_hash,
            user_id=user.id,
            wallet_address=wallet_address.lower(),
            expires_at=session_expires,
            is_revoked=False,
        )
        db.add(session)
        await db.commit()

        logger.info(
            f"Successful authentication for user {user.id} (wallet: {wallet_address})",
            extra={"event": "AUTH_SUCCESS", "user_id": user.id, "wallet": wallet_address}
        )
        return user, raw_session_token, session_expires.isoformat()

    @staticmethod
    async def invalidate_session(db: AsyncSession, raw_session_token: str) -> None:
        token_hash = hashlib.sha256(raw_session_token.encode("utf-8")).hexdigest()
        await AuthenticationService.invalidate_session_by_hash(db, token_hash)

    @staticmethod
    async def invalidate_session_by_hash(db: AsyncSession, session_id_hash: str) -> None:
        stmt = update(Session).where(Session.id == session_id_hash).values(is_revoked=True)
        await db.execute(stmt)
        await db.commit()
        logger.info("Invalidated session successfully.", extra={"event": "SESSION_REVOKED"})
