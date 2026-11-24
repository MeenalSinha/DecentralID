import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.organization import Organization, SigningKey
from backend.app.models.governance import InstitutionAccreditation
from backend.app.schemas.governance import TrustPolicyEvaluationResponse

class TrustPolicyService:
    @staticmethod
    async def evaluate_trust(
        db: AsyncSession,
        institution_address: str,
        credential_schema: str,
        signing_key_address: Optional[str] = None
    ) -> TrustPolicyEvaluationResponse:
        """
        Multi-dimensional Trust Policy Evaluation Engine.
        Evaluates institution status, accreditation lifecycle, schema permissions, and signing key authorization.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        normalized_inst = institution_address.lower()
        
        # 1. Lookup Organization
        result = await db.execute(
            select(Organization).where(Organization.on_chain_address.ilike(normalized_inst))
        )
        org = result.scalars().first()
        if not org:
            return TrustPolicyEvaluationResponse(
                is_trusted=False,
                verdict="INSTITUTION_UNKNOWN",
                accreditation_status="NONE",
                policy_reason=f"Institution with address '{institution_address}' is not registered on DecentralID"
            )
            
        if org.status != "ACTIVE":
            return TrustPolicyEvaluationResponse(
                is_trusted=False,
                verdict="INSTITUTION_INACTIVE",
                accreditation_status="SUSPENDED" if org.status == "SUSPENDED" else "INACTIVE",
                policy_reason=f"Institutional entity is in '{org.status}' status"
            )

        # 2. Lookup Accreditation Record
        acc_result = await db.execute(
            select(InstitutionAccreditation).where(InstitutionAccreditation.organization_id == org.id)
        )
        accreditation = acc_result.scalars().first()
        if not accreditation:
            return TrustPolicyEvaluationResponse(
                is_trusted=False,
                verdict="NOT_ACCREDITED",
                accreditation_status="NONE",
                policy_reason="Institution has no formal accreditation record on file"
            )

        if accreditation.status == "SUSPENDED":
            return TrustPolicyEvaluationResponse(
                is_trusted=False,
                verdict="ACCREDITATION_SUSPENDED",
                category=accreditation.category,
                accreditation_status="SUSPENDED",
                policy_reason="Institutional accreditation is currently suspended by governance"
            )
            
        if accreditation.status != "APPROVED":
            return TrustPolicyEvaluationResponse(
                is_trusted=False,
                verdict="ACCREDITATION_PENDING",
                category=accreditation.category,
                accreditation_status=accreditation.status,
                policy_reason=f"Institutional accreditation is not approved (status: {accreditation.status})"
            )

        # 3. Check Expiry
        if accreditation.valid_until and accreditation.valid_until < now:
            return TrustPolicyEvaluationResponse(
                is_trusted=False,
                verdict="ACCREDITATION_EXPIRED",
                category=accreditation.category,
                accreditation_status="EXPIRED",
                expires_at=accreditation.valid_until,
                policy_reason=f"Accreditation expired on {accreditation.valid_until.isoformat()}"
            )

        # 4. Check Authorized Schema
        auth_schemas = accreditation.authorized_schemas or []
        if credential_schema not in auth_schemas:
            return TrustPolicyEvaluationResponse(
                is_trusted=False,
                verdict="SCHEMA_UNAUTHORIZED",
                category=accreditation.category,
                accreditation_status="APPROVED",
                authorized_schemas=auth_schemas,
                expires_at=accreditation.valid_until,
                policy_reason=f"Schema '{credential_schema}' is outside institution's approved scope {auth_schemas}"
            )

        # 5. Check Signing Key Authorization (if provided)
        if signing_key_address:
            normalized_key = signing_key_address.lower()
            if normalized_key != normalized_inst:
                # Must be an active registered signing key for this org
                key_result = await db.execute(
                    select(SigningKey).where(
                        SigningKey.organization_id == org.id,
                        SigningKey.public_key.ilike(normalized_key),
                        SigningKey.is_active == True
                    )
                )
                active_key = key_result.scalars().first()
                if not active_key:
                    return TrustPolicyEvaluationResponse(
                        is_trusted=False,
                        verdict="KEY_UNAUTHORIZED",
                        category=accreditation.category,
                        accreditation_status="APPROVED",
                        authorized_schemas=auth_schemas,
                        expires_at=accreditation.valid_until,
                        policy_reason=f"Key '{signing_key_address}' is not an authorized active operational signing key"
                    )

        # All checks passed
        return TrustPolicyEvaluationResponse(
            is_trusted=True,
            verdict="TRUSTED",
            category=accreditation.category,
            accreditation_status="APPROVED",
            authorized_schemas=auth_schemas,
            expires_at=accreditation.valid_until,
            policy_reason="Institution and credential type satisfy all active governance trust policies"
        )
