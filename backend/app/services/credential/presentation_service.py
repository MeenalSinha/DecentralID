import uuid
import secrets
import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.credential import Credential
from backend.app.models.organization import Organization
from backend.app.models.presentation import PresentationShare
from backend.app.core.config import settings
from backend.app.core.exceptions import ResourceNotFoundException, ValidationException, TenantAccessDeniedException
from backend.app.services.credential.encryption_service import EncryptionService
from backend.app.services.credential.signing_service import SigningService
from backend.app.schemas.presentation import VerifiablePresentationResponse

class PresentationService:
    """
    Manages W3C Verifiable Presentation (VP) 2.0 generation,
    selective disclosure attribute masking, and privacy-preserving QR sharing.
    """

    @classmethod
    async def create_presentation(
        cls,
        db: AsyncSession,
        holder_address: str,
        credential_id: str,
        disclosed_attributes: Optional[List[str]] = None,
        audience_did: Optional[str] = None,
        expires_in_hours: int = 24,
        holder_signature: Optional[str] = None,
    ) -> VerifiablePresentationResponse:
        holder_norm = holder_address.lower()

        # Find credential
        stmt = select(Credential).where(
            (Credential.credential_id == credential_id) | (Credential.id == credential_id)
        )
        res = await db.execute(stmt)
        cred: Optional[Credential] = res.scalar_one_or_none()

        if not cred:
            raise ResourceNotFoundException("Credential not found.")

        if cred.recipient_address.lower() != holder_norm:
            raise TenantAccessDeniedException("You are not the designated holder of this credential.")

        if cred.workflow_status not in ("ISSUED", "SIGNED"):
            raise ValidationException(
                f"Cannot present unissued credential (current status: {cred.workflow_status})"
            )

        # Decrypt subject and salt
        full_subject = EncryptionService.decrypt_subject(
            cred.encrypted_subject, cred.id, cred.organization_id
        )
        salt_bytes = EncryptionService.decrypt_salt(
            cred.encrypted_salt, cred.id, cred.organization_id
        )

        # Process selective disclosure
        all_keys = [k for k in full_subject.keys() if k != "id"]
        if disclosed_attributes is not None and len(disclosed_attributes) > 0:
            target_keys = set(disclosed_attributes)
            disclosed_claims = {k: full_subject[k] for k in target_keys if k in full_subject}
            masked_claims = [k for k in all_keys if k not in target_keys]
        else:
            disclosed_claims = {k: full_subject[k] for k in all_keys}
            masked_claims = []

        presentation_id = f"urn:uuid:{uuid.uuid4()}"
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        expires_at = now_utc + datetime.timedelta(hours=expires_in_hours)

        # Fetch organization for issuer metadata
        org_stmt = select(Organization).where(Organization.id == cred.organization_id)
        org_res = await db.execute(org_stmt)
        org = org_res.scalar_one_or_none()
        issuer_addr = (org.on_chain_address if org and org.on_chain_address else "").lower()

        # Parse proof JSON
        proof_obj = cred.proof_json
        if isinstance(proof_obj, str):
            import json
            try:
                proof_obj = json.loads(proof_obj)
            except Exception:
                pass

        # Subject for presentation document includes holder DID and disclosed claims
        presented_subject = {"id": f"did:pkh:eip155:{settings.CHAIN_ID}:{holder_norm}"}
        presented_subject.update(disclosed_claims)

        # Construct Verifiable Credential item for the presentation
        presented_vc = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://decentralid.org/contexts/v1",
            ],
            "id": cred.w3c_id,
            "type": ["VerifiableCredential", cred.schema_type],
            "issuer": {
                "id": f"did:pkh:eip155:{settings.CHAIN_ID}:{issuer_addr}",
                "name": org.name if org else "Accredited Issuer",
            },
            "validFrom": cred.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "credentialSubject": presented_subject,
            "credentialStatus": {
                "id": f"/api/v1/credentials/{cred.credential_id}/status",
                "type": "BitstringStatusListEntry",
                "statusPurpose": "revocation"
            },
            "commitment": cred.commitment,
            "selectiveDisclosure": {
                "originalCommitment": cred.commitment,
                "disclosedFields": list(disclosed_claims.keys()),
                "maskedFields": masked_claims,
                # NOTE: salt is intentionally omitted from VP document.
                # It is a server-side commitment secret and must never be transmitted
                # to the verifier. The verifier uses the commitment hash directly.
            },
            "proof": proof_obj,
        }

        if cred.valid_until:
            presented_vc["validUntil"] = cred.valid_until.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Construct W3C Verifiable Presentation 2.0
        # NOTE: Holder binding proof requires the holder to sign with their private key.
        # The backend cannot produce this proof without the holder's key.
        # When holder_signature is not provided, the VP is UNSIGNED (no holder binding proof).
        # Verifiers MUST check for the absence of a VP-level proof and treat the presentation
        # as "credential presented, holder binding unverified" rather than "holder bound".
        vp_document: dict = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://decentralid.org/contexts/v1",
            ],
            "id": presentation_id,
            "type": ["VerifiablePresentation"],
            "holder": f"did:pkh:eip155:{settings.CHAIN_ID}:{holder_norm}",
            "verifiableCredential": [presented_vc],
        }

        # Only attach a VP-level proof when a genuine holder_signature is supplied
        if holder_signature and holder_signature.startswith("0x") and len(holder_signature) >= 130:
            vp_document["proof"] = {
                "type": "DataIntegrityProof",
                "cryptosuite": "ecdsa-jcs-2019",
                "created": now_utc.isoformat(),
                "verificationMethod": f"did:pkh:eip155:{settings.CHAIN_ID}:{holder_norm}#key-1",
                "proofPurpose": "authentication",
                "proofValue": holder_signature,
            }
            if audience_did:
                vp_document["proof"]["challenge"] = audience_did

        # Generate high-entropy opaque token for QR sharing
        token = f"pr_{secrets.token_urlsafe(32)}"

        share_record = PresentationShare(
            token=token,
            holder_address=holder_norm,
            credential_id=cred.credential_id,
            disclosed_claims=disclosed_claims,
            presentation_document=vp_document,
            expires_at=expires_at,
            access_count=0,
            max_access=100,
        )
        db.add(share_record)
        await db.commit()
        await db.refresh(share_record)

        share_url = f"/verify?token={token}"

        return VerifiablePresentationResponse(
            id=share_record.id,
            token=token,
            share_url=share_url,
            credential_id=cred.credential_id,
            holder_address=holder_norm,
            expires_at=expires_at,
            disclosed_claims=disclosed_claims,
            masked_claims=masked_claims,
            presentation_document=vp_document,
        )

    @classmethod
    async def resolve_presentation(cls, db: AsyncSession, token: str) -> Dict[str, Any]:
        stmt = select(PresentationShare).where(PresentationShare.token == token)
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()

        if not record:
            raise ResourceNotFoundException("Presentation token is invalid or has expired.")

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        exp = record.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=datetime.timezone.utc)
        if exp < now_utc:
            raise ValidationException("Presentation token has expired.")

        if record.access_count >= record.max_access:
            raise ValidationException("Presentation link access limit reached.")

        record.access_count += 1
        await db.commit()

        return record.presentation_document
