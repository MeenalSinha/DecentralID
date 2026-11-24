from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.core.constants import UserRole
from backend.app.models.user import User
from backend.app.models.organization import Organization, SigningKey
from backend.app.models.credential import Credential
from backend.app.models.network import ApiKey
from backend.app.schemas.network import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyResponse,
    DeveloperVerifyRequest,
    DeveloperVerifyResponse,
    EncryptedStorageResponse,
)
from backend.app.api.dependencies.auth import get_current_user
from backend.app.services.authorization_service import AuthorizationService
from backend.app.services.network.api_key_service import ApiKeyService, get_api_key_auth
from backend.app.services.network.ipfs_service import IpfsStorageService
from backend.app.services.credential.verification_service import VerificationService

router = APIRouter(prefix="/network", tags=["DecentralID Network Developer APIs"])


# ---------------------------------------------------------
# Public Developer Verification & Query APIs (API Key Auth)
# ---------------------------------------------------------

@router.post("/verify", response_model=DeveloperVerifyResponse, status_code=status.HTTP_200_OK)
async def network_verify(
    payload: DeveloperVerifyRequest,
    api_key: ApiKey = Depends(get_api_key_auth),
    db: AsyncSession = Depends(get_db)
):
    target = payload.presentation if payload.presentation else payload.credential
    if not target:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either 'presentation' or 'credential' must be provided"
        )

    result = await VerificationService.verify_credential(credential=target, db=db)
    res_dict = result.to_dict()

    return DeveloperVerifyResponse(
        outcome=result.outcome,
        checks=res_dict.get("checks", {}),
        issuer_address=result.issuer_address,
        credential_id=result.credential_id,
        details=res_dict
    )


@router.get("/issuers/{address}", status_code=status.HTTP_200_OK)
async def get_issuer_status(
    address: str,
    api_key: ApiKey = Depends(get_api_key_auth),
    db: AsyncSession = Depends(get_db)
):
    clean_addr = address.lower()
    stmt = select(Organization).where(Organization.on_chain_address.ilike(clean_addr))
    res = await db.execute(stmt)
    org = res.scalar_one_or_none()

    if not org:
        return {
            "address": address,
            "is_authorized": False,
            "status": "UNREGISTERED",
            "name": None,
            "verification_status": "NONE"
        }

    keys_stmt = select(SigningKey).where(
        SigningKey.organization_id == org.id,
        SigningKey.status == "ACTIVE"
    )
    keys_res = await db.execute(keys_stmt)
    active_keys = keys_res.scalars().all()

    is_authorized = (org.status == "ACTIVE")

    return {
        "address": address,
        "is_authorized": is_authorized,
        "status": org.status,
        "name": org.name,
        "domain": org.domain,
        "active_keys_count": len(active_keys),
        "keys": [
            {
                "key_id": k.id,
                "public_key": k.public_key_address,
                "valid_until": k.valid_until
            }
            for k in active_keys
        ]
    }


@router.get("/credentials/{id}/status", status_code=status.HTTP_200_OK)
async def get_credential_status(
    id: str,
    api_key: ApiKey = Depends(get_api_key_auth),
    db: AsyncSession = Depends(get_db)
):
    try:
        cred_uuid = UUID(id)
        stmt = select(Credential).where(Credential.id == cred_uuid)
    except ValueError:
        stmt = select(Credential).where(Credential.on_chain_commitment == id)

    res = await db.execute(stmt)
    cred = res.scalar_one_or_none()
    if not cred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CREDENTIAL_NOT_FOUND")

    return {
        "credential_id": str(cred.id),
        "status": cred.status,
        "on_chain_commitment": cred.on_chain_commitment,
        "schema_type": cred.schema_type,
        "issuer_id": str(cred.organization_id),
        "issuance_date": cred.issuance_date.isoformat() if cred.issuance_date else None,
        "expiration_date": cred.expiration_date.isoformat() if cred.expiration_date else None,
        "revoked_at": cred.revoked_at.isoformat() if cred.revoked_at else None,
        "revocation_reason": cred.revocation_reason
    }


@router.post("/storage/encrypt-and-store", response_model=EncryptedStorageResponse, status_code=status.HTTP_201_CREATED)
async def encrypt_and_store_payload(
    payload: Dict[str, Any],
    api_key: ApiKey = Depends(get_api_key_auth),
    db: AsyncSession = Depends(get_db)
):
    record, key = await IpfsStorageService.store_encrypted_credential(
        data=payload,
        db=db,
        organization_id=api_key.organization_id
    )
    return EncryptedStorageResponse(
        cid=record.cid,
        size_bytes=record.size_bytes,
        provider=record.provider,
        encryption_algorithm=record.encryption_algorithm
    )


# ---------------------------------------------------------
# Institutional API Key Management (Cookie/Session Auth)
# ---------------------------------------------------------

@router.post("/api-keys", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: ApiKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify user is an organization admin
    user_memberships = await AuthorizationService.get_user_organizations(db, current_user.id)
    if not user_memberships:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="USER_NOT_AFFILIATED_WITH_ORGANIZATION")

    org_id = user_memberships[0]["organization_id"]
    is_admin = await AuthorizationService.has_organization_role(
        db, current_user.id, org_id, [UserRole.INSTITUTION_ADMIN.value, "ADMIN"]
    )
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS_FOR_API_KEYS")

    api_key_obj, raw_key = await ApiKeyService.generate_api_key(
        db=db,
        organization_id=org_id,
        name=payload.name,
        scopes=payload.scopes,
        rate_limit_per_minute=payload.rate_limit_per_minute,
        expires_in_days=payload.expires_in_days
    )

    return ApiKeyCreateResponse(
        id=api_key_obj.id,
        name=api_key_obj.name,
        key_prefix=api_key_obj.key_prefix,
        api_key=raw_key,
        scopes=api_key_obj.scopes,
        rate_limit_per_minute=api_key_obj.rate_limit_per_minute,
        expires_at=api_key_obj.expires_at,
        created_at=api_key_obj.created_at
    )


@router.get("/api-keys", response_model=List[ApiKeyResponse], status_code=status.HTTP_200_OK)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_memberships = await AuthorizationService.get_user_organizations(db, current_user.id)
    if not user_memberships:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="USER_NOT_AFFILIATED_WITH_ORGANIZATION")

    org_id = user_memberships[0]["organization_id"]
    stmt = select(ApiKey).where(ApiKey.organization_id == org_id, ApiKey.is_active == True)
    res = await db.execute(stmt)
    keys = res.scalars().all()
    return keys


@router.delete("/api-keys/{id}", status_code=status.HTTP_200_OK)
async def revoke_api_key(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_memberships = await AuthorizationService.get_user_organizations(db, current_user.id)
    if not user_memberships:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="USER_NOT_AFFILIATED_WITH_ORGANIZATION")

    org_id = user_memberships[0]["organization_id"]
    stmt = select(ApiKey).where(ApiKey.id == id, ApiKey.organization_id == org_id)
    res = await db.execute(stmt)
    api_key_obj = res.scalar_one_or_none()
    if not api_key_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API_KEY_NOT_FOUND")

    api_key_obj.is_active = False
    await db.commit()
    return {"message": "API_KEY_REVOKED", "id": str(id)}
