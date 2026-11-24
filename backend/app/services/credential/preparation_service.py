import uuid
import datetime
from typing import Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from eth_utils import keccak
from backend.app.core.config import settings
from backend.app.core.constants import CredentialWorkflowStatus, CredentialLifecycleStatus
from backend.app.core.exceptions import (
    TenantAccessDeniedException,
    ResourceNotFoundException,
    ValidationException,
)
from backend.app.models.organization import Organization
from backend.app.models.credential import Credential
from backend.app.services.authorization_service import AuthorizationService
from backend.app.services.credential.commitment_service import CommitmentService
from backend.app.services.credential.encryption_service import EncryptionService
from backend.app.schemas.credential_schemas.registry import CredentialSchemaRegistry

class PreparationService:
    """
    Credential Preparation Service.
    Validates institutional authorization, enforces data-driven schema conformance,
    generates standards-compliant W3C VC structures, computes salted commitments,
    and safely encrypts sensitive subject payloads at rest.
    """

    @staticmethod
    async def prepare_credential(
        db: AsyncSession,
        operator_user_id: str,
        organization_id: str,
        recipient_address: str,
        schema_type: str,
        claims: Dict[str, Any],
        valid_until: datetime.datetime = None,
    ) -> Tuple[Credential, Dict[str, Any]]:
        # 1. Verify operator membership and role in organization
        has_perm = await AuthorizationService.has_organization_role(
            db, operator_user_id, organization_id, ["ADMIN", "AUTHORIZED_ISSUER"]
        )
        if not has_perm:
            raise TenantAccessDeniedException("User is not authorized to prepare credentials for this institution.")

        # 2. Fetch organization details
        org_stmt = select(Organization).where(Organization.id == organization_id)
        org_res = await db.execute(org_stmt)
        org = org_res.scalar_one_or_none()
        if not org:
            raise ResourceNotFoundException("Issuing institution organization not found.")

        if not org.on_chain_address:
            raise ValidationException("Institution has no configured on-chain Ethereum address.")

        # 3. Validate claims against Schema Registry
        is_valid, errors = CredentialSchemaRegistry.validate_claims(schema_type, claims)
        if not is_valid:
            raise ValidationException(f"Schema validation failed: {'; '.join(errors)}")

        # 4. Construct W3C Verifiable Credential Document
        w3c_uuid = str(uuid.uuid4())
        w3c_id = f"urn:uuid:{w3c_uuid}"
        now = datetime.datetime.now(datetime.timezone.utc)
        now_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Deterministic 32-byte credential_id for on-chain indexing
        credential_id = "0x" + keccak(w3c_id.encode("utf-8")).hex()

        issuer_did = f"did:pkh:eip155:{settings.CHAIN_ID}:{org.on_chain_address.lower()}"
        subject_did = f"did:pkh:eip155:{settings.CHAIN_ID}:{recipient_address.lower()}"

        full_subject = {
            "id": subject_did,
            **claims,
        }

        credential_document = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://decentralid.org/contexts/v1",
            ],
            "id": w3c_id,
            "type": ["VerifiableCredential", schema_type],
            "issuer": {
                "id": issuer_did,
                "name": org.name,
            },
            "validFrom": now_str,
            "credentialSubject": full_subject,
        }

        if valid_until:
            credential_document["validUntil"] = valid_until.strftime("%Y-%m-%dT%H:%M:%SZ")

        # 5. Compute high-entropy salted commitment
        commitment, salt = CommitmentService.generate_subject_commitment(full_subject)

        # 6. Encrypt sensitive claims and salt at rest
        encrypted_subject = EncryptionService.encrypt_json(full_subject)
        encrypted_salt = EncryptionService.encrypt_data(salt.hex())

        # 7. Persist draft Credential in database
        credential_record = Credential(
            organization_id=organization_id,
            w3c_id=w3c_id,
            credential_id=credential_id,
            recipient_address=recipient_address.lower(),
            schema_type=schema_type,
            commitment=commitment,
            encrypted_salt=encrypted_salt,
            encrypted_subject=encrypted_subject,
            key_id="master-v1",
            workflow_status=CredentialWorkflowStatus.PREPARED.value,
            status=CredentialLifecycleStatus.ACTIVE.value,
            prepared_by=operator_user_id,
            valid_until=valid_until,
        )

        db.add(credential_record)
        await db.commit()
        await db.refresh(credential_record)

        return credential_record, credential_document
