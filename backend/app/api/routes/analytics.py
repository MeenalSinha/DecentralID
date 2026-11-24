from typing import Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.app.core.database import get_db
from backend.app.core.constants import UserRole, CredentialLifecycleStatus
from backend.app.models.user import User
from backend.app.models.organization import Organization, SigningKey
from backend.app.models.credential import Credential
from backend.app.models.intelligence import DocumentUpload
from backend.app.models.network import ApiKey, WebhookSubscription
from backend.app.api.dependencies.auth import get_current_user
from backend.app.services.authorization_service import AuthorizationService

router = APIRouter(prefix="/analytics", tags=["Platform & Institutional Analytics"])


@router.get("/platform", status_code=status.HTTP_200_OK)
async def get_platform_analytics(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns platform-wide live aggregated operational metrics.
    Zero synthetic or hardcoded metrics - dynamically computed from current database records.
    """
    # 1. Organizations
    total_orgs_res = await db.execute(select(func.count(Organization.id)))
    total_orgs = total_orgs_res.scalar_one()

    active_orgs_res = await db.execute(select(func.count(Organization.id)).where(Organization.status == "ACTIVE"))
    active_orgs = active_orgs_res.scalar_one()

    # 2. Credentials
    active_creds_res = await db.execute(
        select(func.count(Credential.id)).where(Credential.status == CredentialLifecycleStatus.ACTIVE.value)
    )
    active_creds = active_creds_res.scalar_one()

    revoked_creds_res = await db.execute(
        select(func.count(Credential.id)).where(Credential.status == CredentialLifecycleStatus.REVOKED.value)
    )
    revoked_creds = revoked_creds_res.scalar_one()

    suspended_creds_res = await db.execute(
        select(func.count(Credential.id)).where(Credential.status == CredentialLifecycleStatus.SUSPENDED.value)
    )
    suspended_creds = suspended_creds_res.scalar_one()

    # 3. Active Signing Keys
    active_keys_res = await db.execute(
        select(func.count(SigningKey.id)).where(SigningKey.status == "ACTIVE")
    )
    active_keys = active_keys_res.scalar_one()

    # 4. Intelligence Document Uploads
    uploads_res = await db.execute(select(func.count(DocumentUpload.id)))
    uploads = uploads_res.scalar_one()

    return {
        "platform_status": "OPERATIONAL",
        "organizations": {
            "total": total_orgs,
            "active": active_orgs,
        },
        "credentials": {
            "total_active": active_creds,
            "active": active_creds,
            "revoked": revoked_creds,
            "suspended": suspended_creds,
            "total_processed": active_creds + revoked_creds + suspended_creds,
        },
        "signing_keys": {
            "active_authorized_keys": active_keys,
        },
        "intelligence": {
            "total_documents_ingested": uploads,
        }
    }


@router.get("/organizations/{org_id}", status_code=status.HTTP_200_OK)
async def get_organization_analytics(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns tenant-scoped live operational metrics for an authorized institutional officer.
    Strict tenant boundary enforced.
    """
    # Enforce tenant membership check
    has_role = await AuthorizationService.has_organization_role(
        db, current_user.id, org_id, [UserRole.INSTITUTION_ADMIN.value, UserRole.AUTHORIZED_ISSUER.value, "ADMIN"]
    )
    if not has_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="TENANT_ACCESS_DENIED: User is not authorized to view this organization's metrics"
        )

    org_stmt = select(Organization).where(Organization.id == str(org_id))
    org_res = await db.execute(org_stmt)
    org = org_res.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ORGANIZATION_NOT_FOUND")

    # Dynamic counts for this organization
    issued = (await db.execute(
        select(func.count(Credential.id)).where(
            Credential.organization_id == str(org_id),
            Credential.status == CredentialLifecycleStatus.ACTIVE.value
        )
    )).scalar_one()

    revoked = (await db.execute(
        select(func.count(Credential.id)).where(
            Credential.organization_id == str(org_id),
            Credential.status == CredentialLifecycleStatus.REVOKED.value
        )
    )).scalar_one()

    suspended = (await db.execute(
        select(func.count(Credential.id)).where(
            Credential.organization_id == str(org_id),
            Credential.status == CredentialLifecycleStatus.SUSPENDED.value
        )
    )).scalar_one()

    active_keys = (await db.execute(
        select(func.count(SigningKey.id)).where(
            SigningKey.organization_id == str(org_id),
            SigningKey.status == "ACTIVE"
        )
    )).scalar_one()

    docs = (await db.execute(
        select(func.count(DocumentUpload.id)).where(DocumentUpload.organization_id == str(org_id))
    )).scalar_one()

    active_api_keys = (await db.execute(
        select(func.count(ApiKey.id)).where(
            ApiKey.organization_id == str(org_id),
            ApiKey.is_active == True
        )
    )).scalar_one()

    active_webhooks = (await db.execute(
        select(func.count(WebhookSubscription.id)).where(
            WebhookSubscription.organization_id == str(org_id),
            WebhookSubscription.is_active == True
        )
    )).scalar_one()

    return {
        "organization_id": str(org_id),
        "organization_name": org.name,
        "domain": org.domain,
        "status": org.status,
        "credentials": {
            "issued": issued,
            "revoked": revoked,
            "suspended": suspended,
            "total": issued + revoked + suspended
        },
        "security": {
            "active_signing_keys": active_keys,
            "active_api_keys": active_api_keys,
            "active_webhooks": active_webhooks
        },
        "intelligence": {
            "documents_uploaded": docs
        }
    }
