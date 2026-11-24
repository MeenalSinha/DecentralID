from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.core.constants import UserRole, OrganizationStatus, MembershipStatus
from backend.app.core.exceptions import ResourceNotFoundException, DuplicateResourceException
from backend.app.schemas.organization import (
    OrganizationCreateRequest,
    OrganizationResponse,
    MemberInviteRequest,
    MemberResponse,
)
from backend.app.api.dependencies.auth import get_current_user, require_role
from backend.app.models.user import User, Wallet
from backend.app.models.organization import Organization, OrganizationMembership
from backend.app.services.authorization_service import AuthorizationService

router = APIRouter(prefix="/organizations", tags=["Organizations & Tenant Management"])

@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def register_organization(
    payload: OrganizationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrganizationResponse:
    # Check duplicate legal entity id if provided
    if payload.legal_entity_id:
        existing = await db.execute(
            select(Organization).where(Organization.legal_entity_id == payload.legal_entity_id)
        )
        if existing.scalar_one_or_none():
            raise DuplicateResourceException("Organization", payload.legal_entity_id)

    org = Organization(
        name=payload.name,
        legal_entity_id=payload.legal_entity_id,
        domain=payload.domain,
        status=OrganizationStatus.PENDING_REVIEW.value,
        on_chain_address=payload.on_chain_address.lower() if payload.on_chain_address else None,
    )
    db.add(org)
    await db.flush()

    # Assign creator as INSTITUTION_ADMIN of this tenant
    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=current_user.id,
        role=UserRole.INSTITUTION_ADMIN.value,
        status=MembershipStatus.ACTIVE.value,
    )
    db.add(membership)
    await db.commit()

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        legal_entity_id=org.legal_entity_id,
        domain=org.domain,
        status=org.status,
        on_chain_address=org.on_chain_address,
        created_at=org.created_at.isoformat() if org.created_at else "",
    )

@router.get("/{org_id}", response_model=OrganizationResponse, status_code=status.HTTP_200_OK)
async def get_organization(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrganizationResponse:
    # Enforce tenant isolation: user must be member of org or super admin
    await AuthorizationService.verify_tenant_access(
        db, current_user, org_id, [UserRole.INSTITUTION_ADMIN.value, UserRole.AUTHORIZED_ISSUER.value, UserRole.AUDITOR.value]
    )

    stmt = select(Organization).where(Organization.id == org_id)
    res = await db.execute(stmt)
    org = res.scalar_one_or_none()
    if not org:
        raise ResourceNotFoundException("Organization", org_id)

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        legal_entity_id=org.legal_entity_id,
        domain=org.domain,
        status=org.status,
        on_chain_address=org.on_chain_address,
        created_at=org.created_at.isoformat() if org.created_at else "",
    )

@router.post("/{org_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    org_id: str,
    payload: MemberInviteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MemberResponse:
    # Only INSTITUTION_ADMIN of this specific tenant can invite members
    await AuthorizationService.verify_tenant_access(
        db, current_user, org_id, [UserRole.INSTITUTION_ADMIN.value]
    )

    # Find or create user for the invited wallet
    wallet_stmt = select(Wallet).where(Wallet.address == payload.user_address.lower())
    wallet_res = await db.execute(wallet_stmt)
    wallet = wallet_res.scalar_one_or_none()

    if not wallet:
        new_user = User(role=UserRole.AUTHORIZED_ISSUER.value, is_active=True)
        db.add(new_user)
        await db.flush()
        wallet = Wallet(user_id=new_user.id, address=payload.user_address.lower(), chain_id=31337, is_primary=True)
        db.add(wallet)
        await db.flush()
        invited_user_id = new_user.id
    else:
        invited_user_id = wallet.user_id

    # Check duplicate membership
    existing = await db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == invited_user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise DuplicateResourceException("OrganizationMembership", payload.user_address)

    membership = OrganizationMembership(
        organization_id=org_id,
        user_id=invited_user_id,
        role=payload.role.value,
        status=MembershipStatus.ACTIVE.value,
    )
    db.add(membership)
    await db.commit()

    return MemberResponse(
        id=membership.id,
        user_id=invited_user_id,
        wallet_address=payload.user_address.lower(),
        role=membership.role,
        status=membership.status,
        created_at=membership.created_at.isoformat() if membership.created_at else "",
    )

@router.get("/{org_id}/members", response_model=List[MemberResponse], status_code=status.HTTP_200_OK)
async def list_members(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[MemberResponse]:
    await AuthorizationService.verify_tenant_access(
        db, current_user, org_id, [UserRole.INSTITUTION_ADMIN.value, UserRole.AUTHORIZED_ISSUER.value, UserRole.AUDITOR.value]
    )

    stmt = select(OrganizationMembership).where(OrganizationMembership.organization_id == org_id)
    res = await db.execute(stmt)
    memberships = res.scalars().all()

    output = []
    for m in memberships:
        # Get primary wallet address for user
        w_stmt = select(Wallet).where(Wallet.user_id == m.user_id)
        w_res = await db.execute(w_stmt)
        w = w_res.scalars().first()
        output.append(
            MemberResponse(
                id=m.id,
                user_id=m.user_id,
                wallet_address=w.address if w else "",
                role=m.role,
                status=m.status,
                created_at=m.created_at.isoformat() if m.created_at else "",
            )
        )
    return output

@router.delete("/{org_id}/members/{membership_id}", status_code=status.HTTP_200_OK)
async def remove_member(
    org_id: str,
    membership_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await AuthorizationService.verify_tenant_access(
        db, current_user, org_id, [UserRole.INSTITUTION_ADMIN.value]
    )

    stmt = select(OrganizationMembership).where(
        OrganizationMembership.id == membership_id,
        OrganizationMembership.organization_id == org_id,
    )
    res = await db.execute(stmt)
    membership = res.scalar_one_or_none()
    if not membership:
        raise ResourceNotFoundException("OrganizationMembership", membership_id)

    membership.status = MembershipStatus.REVOKED.value
    await db.commit()
    return {"status": "success", "message": "Membership successfully revoked."}
