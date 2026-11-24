import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from eth_utils import keccak
from backend.app.schemas.credential_schemas.registry import CredentialSchemaRegistry
from backend.app.services.credential.signing_service import SigningService
from backend.app.services.credential.commitment_service import CommitmentService
from backend.app.models.organization import Organization, SigningKey
from backend.app.models.credential import Credential
from backend.app.core.constants import CredentialLifecycleStatus, SigningKeyStatus

class VerificationResult:
    def __init__(self):
        self.is_valid: bool = False
        self.structural_valid: bool = False
        self.signature_valid: bool = False
        self.issuer_authorized: bool = False
        self.signing_key_valid: bool = False
        self.commitment_valid: Optional[bool] = None
        self.not_expired: bool = True
        self.lifecycle_status: str = "UNKNOWN"
        self.issuer_name: str = ""
        self.issuer_address: str = ""
        self.signer_address: str = ""
        self.credential_id: str = ""
        self.schema_type: str = ""
        self.disclosed_claims: Dict[str, Any] = {}
        self.is_selective_disclosure: bool = False
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "checks": {
                "structural": self.structural_valid,
                "signature": self.signature_valid,
                "issuer_authorized": self.issuer_authorized,
                "signing_key_authorized": self.signing_key_valid,
                "commitment_verified": self.commitment_valid,
                "not_expired": self.not_expired,
            },
            "lifecycle_status": self.lifecycle_status,
            "issuer": {
                "name": self.issuer_name,
                "address": self.issuer_address,
            },
            "signer_address": self.signer_address,
            "credential_id": self.credential_id,
            "schema_type": self.schema_type,
            "disclosed_claims": self.disclosed_claims,
            "is_selective_disclosure": self.is_selective_disclosure,
            "errors": self.errors,
            "warnings": self.warnings,
            "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

class VerificationService:
    """
    Independent Credential Verification Engine.
    Executes rigorous multi-tier verification without trusting browser claims.
    """

    @classmethod
    async def verify_credential(
        cls,
        credential: Dict[str, Any],
        db: Optional[AsyncSession] = None,
        salt: Optional[bytes] = None,
    ) -> VerificationResult:
        result = VerificationResult()

        # 1. Structural & Schema Validation
        if not isinstance(credential, dict):
            result.errors.append("Invalid format: Credential must be a JSON object.")
            return result

        target_doc = credential
        types = credential.get("type", [])
        if "VerifiablePresentation" in types or "verifiableCredential" in credential:
            vcs = credential.get("verifiableCredential", [])
            if not vcs or not isinstance(vcs, list):
                result.errors.append("Verifiable Presentation contains no credentials.")
                return result
            target_doc = vcs[0]
            if "selectiveDisclosure" in target_doc:
                result.is_selective_disclosure = True
                if not salt:
                    salt_hex = target_doc.get("selectiveDisclosure", {}).get("salt")
                    if salt_hex:
                        clean_hex = salt_hex[2:] if salt_hex.startswith("0x") else salt_hex
                        try:
                            salt = bytes.fromhex(clean_hex)
                        except Exception:
                            pass

        if not target_doc.get("@context") or not target_doc.get("id") or not target_doc.get("type"):
            result.errors.append("Missing required W3C top-level fields (@context, id, type).")
            return result

        doc_types = target_doc.get("type", [])
        if not isinstance(doc_types, list) or "VerifiableCredential" not in doc_types:
            result.errors.append("Credential type array must include 'VerifiableCredential'.")
            return result

        # Extract schema type (the second type in list)
        schema_types = [t for t in doc_types if t != "VerifiableCredential"]
        schema_type = schema_types[0] if schema_types else "Unknown"
        result.schema_type = schema_type

        subject = target_doc.get("credentialSubject", {})
        if not subject or not isinstance(subject, dict):
            result.errors.append("Missing or invalid 'credentialSubject'.")
            return result

        result.disclosed_claims = subject

        # Validate against schema (only if not selective disclosure, where some fields may be masked)
        if not result.is_selective_disclosure:
            is_schema_ok, schema_errors = CredentialSchemaRegistry.validate_claims(schema_type, subject)
            if not is_schema_ok:
                result.warnings.extend(schema_errors)

        result.structural_valid = True

        # Compute on-chain deterministic credential_id
        w3c_id = target_doc.get("id", "")
        result.credential_id = "0x" + keccak(w3c_id.encode("utf-8")).hex()

        # 2. Cryptographic Proof Verification
        if result.is_selective_disclosure and db:
            cred_stmt = select(Credential).where(Credential.w3c_id == w3c_id)
            cred_res = await db.execute(cred_stmt)
            cred = cred_res.scalar_one_or_none()
            if cred and cred.proof_json:
                from backend.app.services.credential.encryption_service import EncryptionService
                full_subj = EncryptionService.decrypt_json(cred.encrypted_subject)
                orig_doc = dict(target_doc)
                orig_doc["credentialSubject"] = full_subj
                orig_doc.pop("selectiveDisclosure", None)
                orig_doc.pop("credentialStatus", None)
                orig_doc.pop("commitment", None)
                is_sig_ok, recovered_signer, sig_err = SigningService.verify_credential_proof(orig_doc)
            else:
                is_sig_ok, recovered_signer, sig_err = SigningService.verify_credential_proof(target_doc)
        else:
            is_sig_ok, recovered_signer, sig_err = SigningService.verify_credential_proof(target_doc)

        if not is_sig_ok:
            result.errors.append(f"Cryptographic proof invalid: {sig_err}")
            return result

        result.signature_valid = True
        result.signer_address = recovered_signer.lower()

        # 3. Parse Issuer Identity
        issuer_raw = target_doc.get("issuer", {})
        issuer_id = issuer_raw.get("id", "") if isinstance(issuer_raw, dict) else str(issuer_raw)
        result.issuer_name = issuer_raw.get("name", "") if isinstance(issuer_raw, dict) else ""

        issuer_addr = ""
        if "did:pkh:eip155:" in issuer_id:
            parts = issuer_id.split(":")
            if len(parts) >= 5:
                issuer_addr = parts[4].lower()
            elif len(parts) >= 4:
                issuer_addr = parts[3].lower()
        elif issuer_id.startswith("0x"):
            issuer_addr = issuer_id.lower()

        result.issuer_address = issuer_addr

        if not issuer_addr:
            result.errors.append(f"Unable to parse issuer Ethereum address from '{issuer_id}'.")
            return result

        # 4. Expiration Check
        valid_until_str = target_doc.get("validUntil")
        if valid_until_str:
            try:
                # Handle ISO timestamps with Z or offset
                exp_clean = valid_until_str.replace("Z", "+00:00")
                exp_dt = datetime.datetime.fromisoformat(exp_clean)
                now_dt = datetime.datetime.now(datetime.timezone.utc)
                if now_dt > exp_dt:
                    result.not_expired = False
                    result.errors.append(f"Credential expired on {valid_until_str}.")
            except Exception:
                result.warnings.append(f"Could not parse validUntil timestamp: '{valid_until_str}'.")

        # 5. Database & On-Chain Trust Registry Verification (if DB session provided)
        if db:
            # Check Issuer authorization in database
            org_stmt = select(Organization).where(Organization.on_chain_address == issuer_addr)
            org_res = await db.execute(org_stmt)
            org = org_res.scalar_one_or_none()

            if org:
                result.issuer_name = result.issuer_name or org.name
                if org.status in ["VERIFIED", "AUTHORIZED"]:
                    result.issuer_authorized = True
                else:
                    result.errors.append(f"Issuing institution status is '{org.status}'.")
            else:
                result.warnings.append(f"Issuer address '{issuer_addr}' not found in local accredited directory.")

            # Check Signing Key validity
            # Key is authorized if it matches the institution's primary address OR an active SigningKey record
            if result.signer_address == issuer_addr:
                result.signing_key_valid = True
            elif org:
                key_stmt = select(SigningKey).where(
                    SigningKey.organization_id == org.id,
                    SigningKey.public_key_address == result.signer_address,
                    SigningKey.status == SigningKeyStatus.ACTIVE.value,
                )
                key_res = await db.execute(key_stmt)
                key = key_res.scalar_one_or_none()
                if key:
                    now = datetime.datetime.now(datetime.timezone.utc)
                    if key.valid_until and key.valid_until.tzinfo is None:
                        key_valid = key.valid_until.replace(tzinfo=datetime.timezone.utc)
                    else:
                        key_valid = key.valid_until

                    if key_valid and now > key_valid:
                        result.errors.append(f"Operational signing key '{result.signer_address}' has expired.")
                    else:
                        result.signing_key_valid = True
                else:
                    result.errors.append(f"Signer '{result.signer_address}' is not an authorized signing key of issuer '{issuer_addr}'.")
            else:
                result.errors.append(f"Signer '{result.signer_address}' authorization cannot be verified.")

            # Check Credential Status in database
            cred_stmt = select(Credential).where(Credential.w3c_id == w3c_id)
            cred_res = await db.execute(cred_stmt)
            cred = cred_res.scalar_one_or_none()

            if cred:
                result.lifecycle_status = cred.status
                if cred.status == CredentialLifecycleStatus.REVOKED.value:
                    result.errors.append("Credential has been permanently revoked by the issuing institution.")
                elif cred.status == CredentialLifecycleStatus.SUSPENDED.value:
                    result.errors.append("Credential is currently suspended by the issuing institution.")
                elif cred.status == CredentialLifecycleStatus.ACTIVE.value:
                    pass
            else:
                result.lifecycle_status = "ACTIVE" # Default if valid signature from authorized issuer

            # Commitment check if salt is provided
            if salt and cred:
                if result.is_selective_disclosure:
                    from backend.app.services.credential.encryption_service import EncryptionService
                    full_subj = EncryptionService.decrypt_json(cred.encrypted_subject)
                    is_commit_ok = CommitmentService.verify_commitment(full_subj, salt, cred.commitment)
                    for k, v in subject.items():
                        if k != "id" and (k not in full_subj or full_subj[k] != v):
                            is_commit_ok = False
                            break
                else:
                    is_commit_ok = CommitmentService.verify_commitment(subject, salt, cred.commitment)

                result.commitment_valid = is_commit_ok
                if not is_commit_ok:
                    result.errors.append("Subject claims do not match registered cryptographic commitment.")
        else:
            # Offline verification without DB: signature is valid and signer matches issuer
            result.issuer_authorized = True
            result.signing_key_valid = (result.signer_address == issuer_addr)
            result.lifecycle_status = "ACTIVE"

        # Final validity determination: No errors, structure valid, signature valid, issuer & key authorized, not expired
        result.is_valid = (
            result.structural_valid
            and result.signature_valid
            and result.issuer_authorized
            and result.signing_key_valid
            and result.not_expired
            and result.lifecycle_status == "ACTIVE"
            and len(result.errors) == 0
        )

        return result
