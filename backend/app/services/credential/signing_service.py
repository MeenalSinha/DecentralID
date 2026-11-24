import hashlib
import datetime
from typing import Dict, Any, Tuple
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import keccak
from backend.app.services.credential.canonicalization import CanonicalizationService

class SigningService:
    """
    W3C Verifiable Credentials Data Model 2.0 & Data Integrity 1.0 Proof Signing Engine.
    Implements standards-compliant ecdsa-jcs-2019 (SHA-256 + RFC 8785 JCS)
    along with backward-compatible verification for legacy profiles.
    """

    CRYPTOSUITE_STANDARD = "ecdsa-jcs-2019"
    CRYPTOSUITE_LEGACY = "ecdsa-jcs-2019-keccak"
    PROOF_TYPE = "DataIntegrityProof"
    PROOF_PURPOSE = "assertionMethod"

    @classmethod
    def create_proof_payload(
        cls,
        document_without_proof: Dict[str, Any],
        verification_method: str,
        created_at: datetime.datetime = None,
        cryptosuite: str = "ecdsa-jcs-2019",
    ) -> Tuple[Dict[str, Any], bytes]:
        """
        Builds the proof options and calculates the preimage digest for signing.
        Uses SHA-256 for standard W3C ecdsa-jcs-2019, or Keccak-256 for legacy.
        Returns (proof_options_dict, digest_bytes).
        """
        if not created_at:
            created_at = datetime.datetime.now(datetime.timezone.utc)

        # Standard ISO-8601 UTC timestamp
        created_str = created_at.strftime("%Y-%m-%dT%H:%M:%SZ")

        proof_options = {
            "type": cls.PROOF_TYPE,
            "cryptosuite": cryptosuite,
            "created": created_str,
            "verificationMethod": verification_method,
            "proofPurpose": cls.PROOF_PURPOSE,
        }

        # Canonicalize document and proof options according to RFC 8785 JCS
        canonical_doc = CanonicalizationService.canonicalize(document_without_proof)
        canonical_options = CanonicalizationService.canonicalize(proof_options)

        if cryptosuite == cls.CRYPTOSUITE_STANDARD:
            # W3C Data Integrity 1.0 ecdsa-jcs-2019: SHA-256(SHA-256(options) || SHA-256(doc))
            h_options = hashlib.sha256(canonical_options).digest()
            h_doc = hashlib.sha256(canonical_doc).digest()
            digest = hashlib.sha256(h_options + h_doc).digest()
        else:
            # Legacy Keccak-256 profile
            preimage = keccak(canonical_options) + keccak(canonical_doc)
            digest = keccak(preimage)

        return proof_options, digest

    @classmethod
    def assemble_signed_credential(
        cls,
        credential_doc: Dict[str, Any],
        proof_options: Dict[str, Any],
        signature: str,
    ) -> Dict[str, Any]:
        """
        Assembles a complete W3C VC from a client-side wallet or KMS signature.
        Never requires the private key to reach the backend application server.
        """
        doc_copy = {k: v for k, v in credential_doc.items() if k != "proof"}
        sig = signature if signature.startswith("0x") else f"0x{signature}"

        complete_proof = {
            **proof_options,
            "proofValue": sig,
        }
        return {
            **doc_copy,
            "proof": complete_proof,
        }

    @classmethod
    def sign_credential(
        cls,
        credential_doc: Dict[str, Any],
        private_key: str,
        verification_method: str,
        created_at: datetime.datetime = None,
        cryptosuite: str = "ecdsa-jcs-2019",
    ) -> Dict[str, Any]:
        """
        Signs a W3C credential document using an operational signing key.
        Returns a complete W3C Verifiable Credential with cryptographic proof attached.
        """
        doc_copy = {k: v for k, v in credential_doc.items() if k != "proof"}
        proof_options, digest = cls.create_proof_payload(
            document_without_proof=doc_copy,
            verification_method=verification_method,
            created_at=created_at,
            cryptosuite=cryptosuite,
        )

        account = Account.from_key(private_key)
        signable = encode_defunct(primitive=digest)
        signed = account.sign_message(signable)
        proof_value = "0x" + signed.signature.hex()

        return cls.assemble_signed_credential(doc_copy, proof_options, proof_value)

    @classmethod
    def verify_credential_proof(
        cls,
        credential: Dict[str, Any],
    ) -> Tuple[bool, str, str]:
        """
        Independently verifies the W3C Data Integrity proof on a credential.
        Supports both standard SHA-256 ecdsa-jcs-2019 and legacy Keccak-256 profiles.
        Returns (is_valid, recovered_signer_address, error_reason).
        """
        if not isinstance(credential, dict):
            return False, "", "Malformed credential payload; expected JSON object."

        proof = credential.get("proof")
        if not proof or not isinstance(proof, dict):
            return False, "", "Credential is missing a cryptographic 'proof' property."

        proof_type = proof.get("type")
        if proof_type != cls.PROOF_TYPE:
            return False, "", f"Unsupported proof type '{proof_type}'. Expected '{cls.PROOF_TYPE}'."

        cryptosuite = proof.get("cryptosuite")
        if cryptosuite not in (cls.CRYPTOSUITE_STANDARD, cls.CRYPTOSUITE_LEGACY):
            return False, "", f"Unsupported cryptosuite '{cryptosuite}'."

        verification_method = proof.get("verificationMethod", "")
        if not verification_method:
            return False, "", "Proof is missing 'verificationMethod'."

        proof_value = proof.get("proofValue", "")
        if not proof_value or not proof_value.startswith("0x"):
            return False, "", "Proof is missing a valid 'proofValue' signature."

        doc_copy = {k: v for k, v in credential.items() if k != "proof"}
        proof_options = {k: v for k, v in proof.items() if k != "proofValue"}

        canonical_doc = CanonicalizationService.canonicalize(doc_copy)
        canonical_options = CanonicalizationService.canonicalize(proof_options)

        # Parse expected address from verificationMethod
        expected_address = ""
        if "did:pkh:eip155:" in verification_method:
            parts = verification_method.split(":")
            if len(parts) >= 5:
                expected_address = parts[4].split("#")[0]
            elif len(parts) >= 4:
                expected_address = parts[3].split("#")[0]
        elif verification_method.startswith("0x"):
            expected_address = verification_method.split("#")[0]

        # 1. Standard SHA-256 verification
        h_options = hashlib.sha256(canonical_options).digest()
        h_doc = hashlib.sha256(canonical_doc).digest()
        std_digest = hashlib.sha256(h_options + h_doc).digest()

        try:
            signable_std = encode_defunct(primitive=std_digest)
            recovered_signer = Account.recover_message(signable_std, signature=proof_value)
            if not expected_address or recovered_signer.lower() == expected_address.lower():
                return True, recovered_signer, ""
        except Exception:
            pass

        # 2. Backward compatibility: Keccak-256 verification
        preimage_legacy = keccak(canonical_options) + keccak(canonical_doc)
        legacy_digest = keccak(preimage_legacy)

        try:
            signable_legacy = encode_defunct(primitive=legacy_digest)
            recovered_signer = Account.recover_message(signable_legacy, signature=proof_value)
            if not expected_address or recovered_signer.lower() == expected_address.lower():
                return True, recovered_signer, ""
            return False, recovered_signer, f"Signer address '{recovered_signer}' does not match verificationMethod '{expected_address}'."
        except Exception as e:
            return False, "", f"Signature recovery failed: {str(e)}"
