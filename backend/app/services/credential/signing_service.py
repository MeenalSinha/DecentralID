import datetime
from typing import Dict, Any, Tuple
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import keccak
from backend.app.services.credential.canonicalization import CanonicalizationService

class SigningService:
    """
    W3C Verifiable Credentials Data Model 2.0 & Data Integrity 1.0 Proof Signing Engine.
    Implements the ecdsa-jcs-2019 cryptosuite using secp256k1 curves.
    Produces and independently validates tamper-evident cryptographic proofs.
    """

    CRYPTOSUITE = "ecdsa-jcs-2019"
    PROOF_TYPE = "DataIntegrityProof"
    PROOF_PURPOSE = "assertionMethod"

    @classmethod
    def create_proof_payload(
        cls,
        document_without_proof: Dict[str, Any],
        verification_method: str,
        created_at: datetime.datetime = None,
    ) -> Tuple[Dict[str, Any], bytes]:
        """
        Builds the proof options and calculates the preimage hash for signing.
        Returns (proof_options_dict, digest_bytes).
        """
        if not created_at:
            created_at = datetime.datetime.now(datetime.timezone.utc)

        # Standard ISO-8601 UTC timestamp
        created_str = created_at.strftime("%Y-%m-%dT%H:%M:%SZ")

        proof_options = {
            "type": cls.PROOF_TYPE,
            "cryptosuite": cls.CRYPTOSUITE,
            "created": created_str,
            "verificationMethod": verification_method,
            "proofPurpose": cls.PROOF_PURPOSE,
        }

        # Canonicalize document and proof options according to RFC 8785 JCS
        canonical_doc = CanonicalizationService.canonicalize(document_without_proof)
        canonical_options = CanonicalizationService.canonicalize(proof_options)

        # Preimage is proof options hash + document hash
        preimage = keccak(canonical_options) + keccak(canonical_doc)
        digest = keccak(preimage)
        return proof_options, digest

    @classmethod
    def sign_credential(
        cls,
        credential_doc: Dict[str, Any],
        private_key: str,
        verification_method: str,
        created_at: datetime.datetime = None,
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
        )

        account = Account.from_key(private_key)
        # Sign digest using Ethereum signable message wrapper for compatibility
        signable = encode_defunct(primitive=digest)
        signed = account.sign_message(signable)
        proof_value = "0x" + signed.signature.hex()

        complete_proof = {
            **proof_options,
            "proofValue": proof_value,
        }

        signed_credential = {
            **doc_copy,
            "proof": complete_proof,
        }
        return signed_credential

    @classmethod
    def verify_credential_proof(
        cls,
        credential: Dict[str, Any],
    ) -> Tuple[bool, str, str]:
        """
        Independently verifies the W3C Data Integrity proof on a credential.
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
        if cryptosuite != cls.CRYPTOSUITE:
            return False, "", f"Unsupported cryptosuite '{cryptosuite}'. Expected '{cls.CRYPTOSUITE}'."

        verification_method = proof.get("verificationMethod", "")
        if not verification_method:
            return False, "", "Proof is missing 'verificationMethod'."

        proof_value = proof.get("proofValue", "")
        if not proof_value or not proof_value.startswith("0x"):
            return False, "", "Proof is missing a valid 'proofValue' signature."

        # Reconstruct canonical doc and proof options
        doc_copy = {k: v for k, v in credential.items() if k != "proof"}
        proof_options = {k: v for k, v in proof.items() if k != "proofValue"}

        canonical_doc = CanonicalizationService.canonicalize(doc_copy)
        canonical_options = CanonicalizationService.canonicalize(proof_options)

        preimage = keccak(canonical_options) + keccak(canonical_doc)
        digest = keccak(preimage)

        try:
            signable = encode_defunct(primitive=digest)
            recovered_signer = Account.recover_message(signable, signature=proof_value)
        except Exception as e:
            return False, "", f"Signature recovery failed: {str(e)}"

        # Parse expected address from verificationMethod (did:pkh:eip155:<chainId>:<address>#key-1)
        expected_address = ""
        if "did:pkh:eip155:" in verification_method:
            parts = verification_method.split(":")
            if len(parts) >= 5:
                expected_address = parts[4].split("#")[0]
            elif len(parts) >= 4:
                expected_address = parts[3].split("#")[0]
        elif verification_method.startswith("0x"):
            expected_address = verification_method.split("#")[0]

        if expected_address and recovered_signer.lower() != expected_address.lower():
            return False, recovered_signer, f"Signer address '{recovered_signer}' does not match verificationMethod '{expected_address}'."

        return True, recovered_signer, ""
