import datetime
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.credential import Credential
from backend.app.models.organization import Organization
from backend.app.core.constants import CredentialLifecycleStatus, CredentialWorkflowStatus
from backend.app.core.exceptions import (
    ResourceNotFoundException,
    TenantAccessDeniedException,
    InvalidStatusTransitionException,
    ValidationException,
)
from backend.app.services.authorization_service import AuthorizationService
from backend.app.services.lifecycle.status_list_service import BitstringStatusListService
from backend.app.services.credential.preparation_service import PreparationService

class CredentialLifecycleService:
    """
    Manages non-repudiable credential lifecycle transitions,
    status list synchronization, and on-chain coordination.
    Enforces terminal revocation: Revoked credentials can NEVER be reinstated.
    """

    @classmethod
    async def suspend_credential(
        cls,
        db: AsyncSession,
        credential_identifier: str,
        reason: str,
        user_id: str,
    ) -> Credential:
        stmt = select(Credential).where(
            (Credential.id == credential_identifier) | (Credential.credential_id == credential_identifier)
        )
        res = await db.execute(stmt)
        cred = res.scalar_one_or_none()

        if not cred:
            raise ResourceNotFoundException("Credential not found.")

        # Institutional Admin authorization check
        has_perm = await AuthorizationService.has_organization_role(
            db, user_id, cred.organization_id, ["ADMIN"]
        )
        if not has_perm:
            raise TenantAccessDeniedException("Institutional Administrator authorization required for suspension.")

        if cred.status == CredentialLifecycleStatus.REVOKED.value:
            raise InvalidStatusTransitionException("Cannot suspend a credential that has already been permanently revoked.")

        if cred.status == CredentialLifecycleStatus.SUSPENDED.value:
            raise InvalidStatusTransitionException("Credential is already suspended.")

        cred.status = CredentialLifecycleStatus.SUSPENDED.value
        cred.revocation_reason = reason

        # Update bitstring status list if mapped
        if cred.status_list_id and cred.status_list_index is not None:
            await BitstringStatusListService.update_status_bit(
                db, cred.status_list_id, cred.status_list_index, 1
            )

        await db.commit()
        await db.refresh(cred)
        return cred

    @classmethod
    async def reinstate_credential(
        cls,
        db: AsyncSession,
        credential_identifier: str,
        reason: str,
        user_id: str,
    ) -> Credential:
        stmt = select(Credential).where(
            (Credential.id == credential_identifier) | (Credential.credential_id == credential_identifier)
        )
        res = await db.execute(stmt)
        cred = res.scalar_one_or_none()

        if not cred:
            raise ResourceNotFoundException("Credential not found.")

        # Institutional Admin authorization check
        has_perm = await AuthorizationService.has_organization_role(
            db, user_id, cred.organization_id, ["ADMIN"]
        )
        if not has_perm:
            raise TenantAccessDeniedException("Institutional Administrator authorization required for reinstatement.")

        if cred.status == CredentialLifecycleStatus.REVOKED.value:
            raise InvalidStatusTransitionException(
                "Revocation is permanent and terminal. Revoked credentials can NEVER be reinstated under any circumstance."
            )

        if cred.status != CredentialLifecycleStatus.SUSPENDED.value:
            raise InvalidStatusTransitionException(
                f"Cannot reinstate credential with status '{cred.status}'. Only suspended credentials can be reinstated."
            )

        cred.status = CredentialLifecycleStatus.ACTIVE.value
        cred.revocation_reason = None

        # Reset status list bit to 0 (Active)
        if cred.status_list_id and cred.status_list_index is not None:
            await BitstringStatusListService.update_status_bit(
                db, cred.status_list_id, cred.status_list_index, 0
            )

        await db.commit()
        await db.refresh(cred)
        return cred

    @classmethod
    async def revoke_credential(
        cls,
        db: AsyncSession,
        credential_identifier: str,
        reason: str,
        user_id: str,
    ) -> Credential:
        stmt = select(Credential).where(
            (Credential.id == credential_identifier) | (Credential.credential_id == credential_identifier)
        )
        res = await db.execute(stmt)
        cred = res.scalar_one_or_none()

        if not cred:
            raise ResourceNotFoundException("Credential not found.")

        # Institutional Admin authorization check
        has_perm = await AuthorizationService.has_organization_role(
            db, user_id, cred.organization_id, ["ADMIN"]
        )
        if not has_perm:
            raise TenantAccessDeniedException("Institutional Administrator authorization required for permanent revocation.")

        if cred.status == CredentialLifecycleStatus.REVOKED.value:
            raise InvalidStatusTransitionException("Credential has already been permanently revoked.")

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        cred.status = CredentialLifecycleStatus.REVOKED.value
        cred.workflow_status = CredentialWorkflowStatus.REVOKED.value
        cred.revocation_reason = reason
        cred.revoked_at = now_utc

        # Update status list bit to 1 (Revoked)
        if cred.status_list_id and cred.status_list_index is not None:
            await BitstringStatusListService.update_status_bit(
                db, cred.status_list_id, cred.status_list_index, 1
            )

        await db.commit()
        await db.refresh(cred)
        return cred

    @classmethod
    async def renew_or_replace_credential(
        cls,
        db: AsyncSession,
        old_credential_identifier: str,
        operator_user_id: str,
        updated_claims: Dict[str, Any],
        reason: str,
        valid_until: Optional[datetime.datetime] = None,
    ) -> Tuple[Credential, Credential]:
        """
        Issues a new replacement credential that explicitly supersedes the old credential.
        Revokes the old credential and anchors the supersedes relationship.
        """
        # Revoke old credential
        old_cred = await cls.revoke_credential(
            db=db,
            credential_identifier=old_credential_identifier,
            reason=f"Superseded by renewal: {reason}",
            user_id=operator_user_id,
        )

        # Prepare new replacement credential
        new_cred, _ = await PreparationService.prepare_credential(
            db=db,
            operator_user_id=operator_user_id,
            organization_id=old_cred.organization_id,
            recipient_address=old_cred.recipient_address,
            schema_type=old_cred.schema_type,
            claims=updated_claims,
            valid_until=valid_until,
        )

        new_cred.supersedes_id = old_cred.credential_id
        await db.commit()
        await db.refresh(new_cred)

        return old_cred, new_cred
