import json
import datetime
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.config import settings
from backend.app.core.constants import CredentialWorkflowStatus, CredentialLifecycleStatus, IssuanceJobStatus
from backend.app.core.exceptions import (
    TenantAccessDeniedException,
    ResourceNotFoundException,
    ValidationException,
    InvalidStatusTransitionException,
)
from backend.app.models.organization import Organization, SigningKey
from backend.app.models.credential import Credential
from backend.app.models.issuance_job import IssuanceJob
from backend.app.services.authorization_service import AuthorizationService
from backend.app.services.credential.encryption_service import EncryptionService
from backend.app.services.credential.signing_service import SigningService

class IssuanceService:
    """
    Manages institutional approval workflows, cryptographic signing,
    and transactional outbox reconciliation for blockchain registration.
    """

    @staticmethod
    async def submit_for_approval(
        db: AsyncSession,
        credential_record_id: str,
        user_id: str,
    ) -> Credential:
        stmt = select(Credential).where((Credential.id == credential_record_id) | (Credential.credential_id == credential_record_id))
        res = await db.execute(stmt)
        cred = res.scalar_one_or_none()
        if not cred:
            raise ResourceNotFoundException("Credential record not found.")

        has_perm = await AuthorizationService.has_organization_role(
            db, user_id, cred.organization_id, ["ADMIN", "AUTHORIZED_ISSUER"]
        )
        if not has_perm:
            raise TenantAccessDeniedException("Not authorized to submit credentials for this organization.")

        if cred.workflow_status != CredentialWorkflowStatus.PREPARED.value:
            raise InvalidStatusTransitionException(f"Cannot submit credential with status '{cred.workflow_status}'.")

        cred.workflow_status = CredentialWorkflowStatus.PENDING_APPROVAL.value
        await db.commit()
        await db.refresh(cred)
        return cred

    @staticmethod
    async def approve_credential(
        db: AsyncSession,
        credential_record_id: str,
        approver_user_id: str,
    ) -> Credential:
        """
        Enforces separation of duties: An operator cannot approve credentials they prepared.
        Requires institution admin role.
        """
        stmt = select(Credential).where((Credential.id == credential_record_id) | (Credential.credential_id == credential_record_id))
        res = await db.execute(stmt)
        cred = res.scalar_one_or_none()
        if not cred:
            raise ResourceNotFoundException("Credential record not found.")

        # Admin role required for approval
        is_admin = await AuthorizationService.has_organization_role(
            db, approver_user_id, cred.organization_id, ["ADMIN"]
        )
        if not is_admin:
            raise TenantAccessDeniedException("Institutional Administrator approval required.")

        # Separation of duties check
        if cred.prepared_by and cred.prepared_by == approver_user_id:
            raise ValidationException("Separation of duties violation: Approver cannot be the same operator who prepared the credential.")

        if cred.workflow_status != CredentialWorkflowStatus.PENDING_APPROVAL.value:
            raise InvalidStatusTransitionException(f"Cannot approve credential with status '{cred.workflow_status}'. Expected 'PENDING_APPROVAL'.")

        cred.workflow_status = CredentialWorkflowStatus.APPROVED.value
        cred.approved_by = approver_user_id
        await db.commit()
        await db.refresh(cred)
        return cred

    @staticmethod
    async def sign_credential(
        db: AsyncSession,
        credential_record_id: str,
        signing_key_private_key: str,
        operator_user_id: str,
    ) -> Tuple[Credential, Dict[str, Any]]:
        stmt = select(Credential).where((Credential.id == credential_record_id) | (Credential.credential_id == credential_record_id))
        res = await db.execute(stmt)
        cred = res.scalar_one_or_none()
        if not cred:
            raise ResourceNotFoundException("Credential record not found.")

        has_perm = await AuthorizationService.has_organization_role(
            db, operator_user_id, cred.organization_id, ["ADMIN", "AUTHORIZED_ISSUER"]
        )
        if not has_perm:
            raise TenantAccessDeniedException("Not authorized to sign credentials for this organization.")

        if cred.workflow_status not in [CredentialWorkflowStatus.APPROVED.value]:
            raise InvalidStatusTransitionException(f"Cannot sign credential with status '{cred.workflow_status}'.")

        # Fetch organization
        org_stmt = select(Organization).where(Organization.id == cred.organization_id)
        org_res = await db.execute(org_stmt)
        org = org_res.scalar_one()

        # Decrypt subject
        full_subject = EncryptionService.decrypt_json(cred.encrypted_subject)

        # Build W3C Document
        w3c_doc = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://decentralid.org/contexts/v1",
            ],
            "id": cred.w3c_id,
            "type": ["VerifiableCredential", cred.schema_type],
            "issuer": {
                "id": f"did:pkh:eip155:{settings.CHAIN_ID}:{org.on_chain_address.lower()}",
                "name": org.name,
            },
            "validFrom": cred.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "credentialSubject": full_subject,
        }
        if cred.valid_until:
            w3c_doc["validUntil"] = cred.valid_until.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Derive signer address and verification method
        from eth_account import Account
        signer_acc = Account.from_key(signing_key_private_key)
        signer_addr = signer_acc.address.lower()

        verification_method = f"did:pkh:eip155:{settings.CHAIN_ID}:{signer_addr}#key-1"

        # Cryptographically sign credential per W3C Data Integrity 1.0 (ecdsa-jcs-2019)
        signed_vc = SigningService.sign_credential(
            credential_doc=w3c_doc,
            private_key=signing_key_private_key,
            verification_method=verification_method,
        )

        cred.proof_json = json.dumps(signed_vc["proof"])
        cred.workflow_status = CredentialWorkflowStatus.PENDING_BLOCKCHAIN_REGISTRATION.value

        # Create transactional outbox issuance job
        job = IssuanceJob(
            credential_id=cred.id,
            organization_id=cred.organization_id,
            status=IssuanceJobStatus.PENDING.value,
        )
        db.add(job)
        await db.commit()
        await db.refresh(cred)

        return cred, signed_vc

    @staticmethod
    async def get_signing_payload(
        db: AsyncSession,
        credential_record_id: str,
        operator_user_id: str,
        signer_address: str,
        cryptosuite: str = "ecdsa-jcs-2019",
    ) -> Dict[str, Any]:
        """
        Builds the canonical unsigned W3C document and signing digest for client-side wallet signing.
        Zero private key material is required on the backend.
        """
        stmt = select(Credential).where((Credential.id == credential_record_id) | (Credential.credential_id == credential_record_id))
        res = await db.execute(stmt)
        cred = res.scalar_one_or_none()
        if not cred:
            raise ResourceNotFoundException("Credential record not found.")

        has_perm = await AuthorizationService.has_organization_role(
            db, operator_user_id, cred.organization_id, ["ADMIN", "AUTHORIZED_ISSUER"]
        )
        if not has_perm:
            raise TenantAccessDeniedException("Not authorized to sign credentials for this organization.")

        if cred.workflow_status not in [CredentialWorkflowStatus.APPROVED.value]:
            raise InvalidStatusTransitionException(f"Cannot sign credential with status '{cred.workflow_status}'. Expected 'APPROVED'.")

        # Fetch organization
        org_stmt = select(Organization).where(Organization.id == cred.organization_id)
        org_res = await db.execute(org_stmt)
        org = org_res.scalar_one()

        # Decrypt subject
        full_subject = EncryptionService.decrypt_json(cred.encrypted_subject)

        w3c_doc = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://decentralid.org/contexts/v1",
            ],
            "id": cred.w3c_id,
            "type": ["VerifiableCredential", cred.schema_type],
            "issuer": {
                "id": f"did:pkh:eip155:{settings.CHAIN_ID}:{org.on_chain_address.lower()}",
                "name": org.name,
            },
            "validFrom": cred.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "credentialSubject": full_subject,
        }
        if cred.valid_until:
            w3c_doc["validUntil"] = cred.valid_until.strftime("%Y-%m-%dT%H:%M:%SZ")

        verification_method = f"did:pkh:eip155:{settings.CHAIN_ID}:{signer_address.lower()}#key-1"

        proof_options, digest = SigningService.create_proof_payload(
            document_without_proof=w3c_doc,
            verification_method=verification_method,
            created_at=cred.created_at,
            cryptosuite=cryptosuite,
        )

        return {
            "credential_id": cred.credential_id,
            "document": w3c_doc,
            "proof_options": proof_options,
            "verification_method": verification_method,
            "signing_digest": "0x" + digest.hex(),
            "cryptosuite": cryptosuite,
        }

    @staticmethod
    async def complete_signing_with_signature(
        db: AsyncSession,
        credential_record_id: str,
        signature: str,
        signer_address: str,
        operator_user_id: str,
        cryptosuite: str = "ecdsa-jcs-2019",
    ) -> Tuple[Credential, Dict[str, Any]]:
        """
        Receives an externally generated ECDSA signature (from MetaMask, Hardware Wallet, or KMS),
        authenticates the signer, and finalizes the verifiable credential.
        """
        stmt = select(Credential).where((Credential.id == credential_record_id) | (Credential.credential_id == credential_record_id))
        res = await db.execute(stmt)
        cred = res.scalar_one_or_none()
        if not cred:
            raise ResourceNotFoundException("Credential record not found.")

        has_perm = await AuthorizationService.has_organization_role(
            db, operator_user_id, cred.organization_id, ["ADMIN", "AUTHORIZED_ISSUER"]
        )
        if not has_perm:
            raise TenantAccessDeniedException("Not authorized to sign credentials for this organization.")

        if cred.workflow_status not in [CredentialWorkflowStatus.APPROVED.value]:
            raise InvalidStatusTransitionException(f"Cannot sign credential with status '{cred.workflow_status}'. Expected 'APPROVED'.")

        # Get payload
        payload = await IssuanceService.get_signing_payload(
            db, credential_record_id, operator_user_id, signer_address, cryptosuite
        )

        signed_vc = SigningService.assemble_signed_credential(
            credential_doc=payload["document"],
            proof_options=payload["proof_options"],
            signature=signature,
        )

        # Independently verify the assembled proof before persisting
        is_valid, recovered, error = SigningService.verify_credential_proof(signed_vc)
        if not is_valid:
            raise ValidationException(f"Cryptographic signature verification failed: {error}")

        cred.proof_json = json.dumps(signed_vc["proof"])
        cred.workflow_status = CredentialWorkflowStatus.PENDING_BLOCKCHAIN_REGISTRATION.value

        job = IssuanceJob(
            credential_id=cred.id,
            organization_id=cred.organization_id,
            status=IssuanceJobStatus.PENDING.value,
        )
        db.add(job)
        await db.commit()
        await db.refresh(cred)

        return cred, signed_vc

    @staticmethod
    async def confirm_blockchain_registration(
        db: AsyncSession,
        credential_record_id: str,
        tx_hash: str,
    ) -> Credential:
        stmt = select(Credential).where((Credential.id == credential_record_id) | (Credential.credential_id == credential_record_id))
        res = await db.execute(stmt)
        cred = res.scalar_one_or_none()
        if not cred:
            raise ResourceNotFoundException("Credential record not found.")

        cred.tx_hash = tx_hash
        cred.workflow_status = CredentialWorkflowStatus.ISSUED.value
        cred.issued_at = datetime.datetime.now(datetime.timezone.utc)

        # Update any pending outbox job
        job_stmt = select(IssuanceJob).where(
            IssuanceJob.credential_id == cred.id,
            IssuanceJob.status != IssuanceJobStatus.CONFIRMED.value
        )
        job_res = await db.execute(job_stmt)
        job = job_res.scalar_one_or_none()
        if job:
            job.status = IssuanceJobStatus.CONFIRMED.value
            job.tx_hash = tx_hash

        await db.commit()
        await db.refresh(cred)
        return cred

    @staticmethod
    async def get_verifiable_credential(
        db: AsyncSession,
        credential_record_id: str,
    ) -> Dict[str, Any]:
        """
        Reconstructs the full unencrypted W3C Verifiable Credential document with proof.
        """
        stmt = select(Credential).where((Credential.id == credential_record_id) | (Credential.credential_id == credential_record_id))
        res = await db.execute(stmt)
        cred = res.scalar_one_or_none()
        if not cred:
            raise ResourceNotFoundException("Credential record not found.")

        org_stmt = select(Organization).where(Organization.id == cred.organization_id)
        org_res = await db.execute(org_stmt)
        org = org_res.scalar_one()

        full_subject = EncryptionService.decrypt_json(cred.encrypted_subject)

        w3c_doc = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://decentralid.org/contexts/v1",
            ],
            "id": cred.w3c_id,
            "type": ["VerifiableCredential", cred.schema_type],
            "issuer": {
                "id": f"did:pkh:eip155:{settings.CHAIN_ID}:{org.on_chain_address.lower()}",
                "name": org.name,
            },
            "validFrom": cred.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "credentialSubject": full_subject,
        }
        if cred.valid_until:
            w3c_doc["validUntil"] = cred.valid_until.strftime("%Y-%m-%dT%H:%M:%SZ")

        if cred.proof_json:
            w3c_doc["proof"] = json.loads(cred.proof_json)

        return w3c_doc
