from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.user import User
from backend.app.models.organization import OrganizationMembership
from backend.app.core.constants import UserRole, MembershipStatus
from backend.app.core.exceptions import TenantAccessDeniedException
from backend.app.core.logging import logger

class AuthorizationService:
    @staticmethod
    def check_user_role(user: User, allowed_roles: list[str]) -> bool:
        """Check if user has platform-level role."""
        if user.role == UserRole.PLATFORM_SUPER_ADMIN.value:
            return True
        return user.role in allowed_roles

    @staticmethod
    async def get_membership(
        db: AsyncSession,
        user_id: str,
        organization_id: str,
    ) -> OrganizationMembership | None:
        """Fetch active membership within specified organization."""
        stmt = select(OrganizationMembership).where(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.status == MembershipStatus.ACTIVE.value,
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def has_organization_role(
        db: AsyncSession,
        user_id: str,
        organization_id: str,
        required_roles: list[str],
    ) -> bool:
        """Check if user has an active membership with one of the required roles."""
        membership = await AuthorizationService.get_membership(db, user_id, organization_id)
        if not membership:
            return False
        normalized_roles = set(required_roles)
        if "ADMIN" in normalized_roles:
            normalized_roles.add(UserRole.INSTITUTION_ADMIN.value)
        return membership

    @staticmethod
    async def get_user_organizations(db: AsyncSession, user_id: str) -> list[dict]:
        """Return all active organization memberships for a user."""
        stmt = select(OrganizationMembership).where(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.status == MembershipStatus.ACTIVE.value,
        )
        res = await db.execute(stmt)
        memberships = res.scalars().all()
        return [{"organization_id": m.organization_id, "role": m.role} for m in memberships].role in normalized_roles

    @staticmethod
    async def verify_tenant_access(
        db: AsyncSession,
        user: User,
        organization_id: str,
        required_roles: list[str],
    ) -> OrganizationMembership:
        """
        Enforce strict tenant isolation:
        Verifies that the authenticated user belongs to the target organization
        and possesses the required organizational role.
        """
        # Super admin has global tenant oversight
        if user.role == UserRole.PLATFORM_SUPER_ADMIN.value:
            membership = await AuthorizationService.get_membership(db, user.id, organization_id)
            if not membership:
                membership = OrganizationMembership(
                    organization_id=organization_id,
                    user_id=user.id,
                    role=UserRole.PLATFORM_SUPER_ADMIN.value,
                    status=MembershipStatus.ACTIVE.value,
                )
            return membership

        membership = await AuthorizationService.get_membership(db, user.id, organization_id)
        if not membership:
            logger.warning(
                f"Unauthorized tenant access attempt by user {user.id} to org {organization_id}",
                extra={"event": "CROSS_TENANT_ACCESS_BLOCKED", "user_id": user.id, "org_id": organization_id}
            )
            raise TenantAccessDeniedException(
                "Access denied: You do not hold an active membership in this organization."
            )

        if membership.role not in required_roles:
            logger.warning(
                f"Insufficient role {membership.role} for user {user.id} in org {organization_id}. Required: {required_roles}",
                extra={"event": "INSUFFICIENT_TENANT_ROLE", "user_id": user.id, "org_id": organization_id}
            )
            raise TenantAccessDeniedException(
                f"Access denied: Requires one of the following roles: {', '.join(required_roles)}"
            )

        return membership

    @staticmethod
    async def get_user_organizations(db: AsyncSession, user_id: str) -> list[dict]:
        """Return all active organization memberships for a user."""
        stmt = select(OrganizationMembership).where(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.status == MembershipStatus.ACTIVE.value,
        )
        res = await db.execute(stmt)
        memberships = res.scalars().all()
        return [{"organization_id": m.organization_id, "role": m.role} for m in memberships]
