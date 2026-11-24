from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.api.dependencies.auth import get_current_user
from backend.app.models.user import User
from backend.app.models.status_list import StatusList
from backend.app.models.organization import Organization
from backend.app.core.exceptions import ResourceNotFoundException
from backend.app.schemas.lifecycle import (
    LifecycleActionRequest,
    RenewCredentialRequest,
    LifecycleActionResponse,
)
from backend.app.services.lifecycle.lifecycle_service import CredentialLifecycleService
from backend.app.services.lifecycle.status_list_service import BitstringStatusListService
from backend.app.core.config import settings

router = APIRouter(tags=["Credential Lifecycle & Status Management"])

@router.post("/credentials/{credential_id}/suspend", response_model=LifecycleActionResponse, status_code=status.HTTP_200_OK)
async def suspend_credential(
    credential_id: str,
    payload: LifecycleActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LifecycleActionResponse:
    cred = await CredentialLifecycleService.suspend_credential(
        db=db,
        credential_identifier=credential_id,
        reason=payload.reason,
        user_id=current_user.id,
    )
    return LifecycleActionResponse(
        credential_id=cred.credential_id,
        status=cred.status,
        workflow_status=cred.workflow_status,
        revocation_reason=cred.revocation_reason,
        revoked_at=cred.revoked_at,
        updated_at=cred.updated_at,
    )

@router.post("/credentials/{credential_id}/reinstate", response_model=LifecycleActionResponse, status_code=status.HTTP_200_OK)
async def reinstate_credential(
    credential_id: str,
    payload: LifecycleActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LifecycleActionResponse:
    cred = await CredentialLifecycleService.reinstate_credential(
        db=db,
        credential_identifier=credential_id,
        reason=payload.reason,
        user_id=current_user.id,
    )
    return LifecycleActionResponse(
        credential_id=cred.credential_id,
        status=cred.status,
        workflow_status=cred.workflow_status,
        revocation_reason=cred.revocation_reason,
        revoked_at=cred.revoked_at,
        updated_at=cred.updated_at,
    )

@router.post("/credentials/{credential_id}/revoke", response_model=LifecycleActionResponse, status_code=status.HTTP_200_OK)
async def revoke_credential(
    credential_id: str,
    payload: LifecycleActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LifecycleActionResponse:
    cred = await CredentialLifecycleService.revoke_credential(
        db=db,
        credential_identifier=credential_id,
        reason=payload.reason,
        user_id=current_user.id,
    )
    return LifecycleActionResponse(
        credential_id=cred.credential_id,
        status=cred.status,
        workflow_status=cred.workflow_status,
        revocation_reason=cred.revocation_reason,
        revoked_at=cred.revoked_at,
        updated_at=cred.updated_at,
    )

@router.post("/credentials/{credential_id}/renew", status_code=status.HTTP_200_OK)
async def renew_credential(
    credential_id: str,
    payload: RenewCredentialRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    old_cred, new_cred = await CredentialLifecycleService.renew_or_replace_credential(
        db=db,
        old_credential_identifier=credential_id,
        operator_user_id=current_user.id,
        updated_claims=payload.updated_claims,
        reason=payload.reason,
        valid_until=payload.valid_until,
    )
    return {
        "status": "renewed",
        "old_credential": {
            "id": old_cred.id,
            "credential_id": old_cred.credential_id,
            "status": old_cred.status,
            "revocation_reason": old_cred.revocation_reason,
        },
        "new_credential": {
            "id": new_cred.id,
            "credential_id": new_cred.credential_id,
            "supersedes_id": new_cred.supersedes_id,
            "workflow_status": new_cred.workflow_status,
        }
    }

@router.get("/status-lists/{list_number}", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_status_list_credential(
    list_number: int,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Public resolution of W3C Bitstring Status List 1.0 Credential.
    """
    stmt = select(StatusList).where(StatusList.list_number == list_number)
    res = await db.execute(stmt)
    slist = res.scalar_one_or_none()
    if not slist:
        raise ResourceNotFoundException(f"Status list #{list_number} not found.")

    org_stmt = select(Organization).where(Organization.id == slist.organization_id)
    org_res = await db.execute(org_stmt)
    org = org_res.scalar_one_or_none()
    issuer_addr = (org.on_chain_address if org and org.on_chain_address else "").lower()
    issuer_did = f"did:pkh:eip155:{settings.CHAIN_ID}:{issuer_addr}"

    return BitstringStatusListService.generate_status_list_credential(slist, issuer_did)
