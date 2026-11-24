import os
import json
import secrets
import hashlib
from typing import Dict, Any, List, Tuple, Optional
from backend.app.services.credential.canonicalization import CanonicalizationService

class SelectiveDisclosureService:
    """
    Genuine Cryptographic Selective Disclosure Engine.
    Implements salted claim digest commitments, enabling holders to prove selected claims
    without revealing undisclosed attributes, while providing cryptographic tamper-evidence.
    """

    @staticmethod
    def generate_claim_salt() -> str:
        """Generates a 128-bit high-entropy blinding salt."""
        return secrets.token_hex(16)

    @classmethod
    def compute_claim_digest(cls, claim_key: str, claim_value: Any, salt: str) -> str:
        """
        Computes the cryptographic commitment for an individual claim:
        H_i = SHA-256( canonical(key) || ":" || canonical(value) || ":" || salt )
        """
        c_key = CanonicalizationService.canonicalize(claim_key).decode("utf-8")
        c_val = CanonicalizationService.canonicalize(claim_value).decode("utf-8")
        payload = f"{c_key}:{c_val}:{salt}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @classmethod
    def create_blinded_claims(
        cls,
        subject_claims: Dict[str, Any]
    ) -> Tuple[Dict[str, str], Dict[str, str], str]:
        """
        Generates blinded claim commitments for all claims.
        Returns:
            - claim_salts: {key: salt}
            - claim_digests: {key: digest}
            - root_commitment: SHA-256 hash over sorted digests
        """
        claim_salts: Dict[str, str] = {}
        claim_digests: Dict[str, str] = {}

        for k, v in subject_claims.items():
            if k == "id":
                continue
            salt = cls.generate_claim_salt()
            claim_salts[k] = salt
            claim_digests[k] = cls.compute_claim_digest(k, v, salt)

        # Root commitment is SHA-256 over canonical sorted digests
        sorted_pairs = sorted(claim_digests.items())
        serialized_digests = json.dumps(sorted_pairs, separators=(",", ":")).encode("utf-8")
        root_commitment = hashlib.sha256(serialized_digests).hexdigest()

        return claim_salts, claim_digests, root_commitment

    @classmethod
    def generate_disclosure_proof(
        cls,
        full_claims: Dict[str, Any],
        claim_salts: Dict[str, str],
        disclosed_keys: List[str],
    ) -> Dict[str, Any]:
        """
        Generates the selective disclosure proof package.
        Disclosed claims include their value and blinding salt.
        Undisclosed claims are represented only by their pre-computed cryptographic digest.
        """
        target_keys = set(disclosed_keys)
        disclosed_records: Dict[str, Any] = {}
        blinded_commitments: Dict[str, str] = {}

        for k, v in full_claims.items():
            if k == "id":
                continue
            salt = claim_salts.get(k, "")
            if k in target_keys:
                disclosed_records[k] = {
                    "value": v,
                    "salt": salt,
                }
            else:
                # Undisclosed: emit only the digest
                blinded_commitments[k] = cls.compute_claim_digest(k, v, salt)

        return {
            "disclosedClaims": disclosed_records,
            "blindedCommitments": blinded_commitments,
        }

    @classmethod
    def verify_selective_disclosure(
        cls,
        disclosure_proof: Dict[str, Any],
        expected_root_commitment: str,
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Verifies that disclosed claims along with blinded commitments reconstruct
        the expected issuer-anchored root commitment without tampering.
        Returns: (is_valid, verified_disclosed_claims, error_reason)
        """
        disclosed = disclosure_proof.get("disclosedClaims", {})
        blinded = disclosure_proof.get("blindedCommitments", {})

        reconstructed_digests: Dict[str, str] = {}
        verified_claims: Dict[str, Any] = {}

        # 1. Recompute digests for disclosed claims
        for k, item in disclosed.items():
            if not isinstance(item, dict) or "value" not in item or "salt" not in item:
                return False, {}, f"Malformed disclosed claim record for '{k}'."
            val = item["value"]
            salt = item["salt"]
            reconstructed_digests[k] = cls.compute_claim_digest(k, val, salt)
            verified_claims[k] = val

        # 2. Add blinded commitments of undisclosed claims
        for k, digest in blinded.items():
            if k in reconstructed_digests:
                return False, {}, f"Claim collision: '{k}' present in both disclosed and blinded sets."
            reconstructed_digests[k] = str(digest)

        # 3. Recompute root commitment
        sorted_pairs = sorted(reconstructed_digests.items())
        serialized_digests = json.dumps(sorted_pairs, separators=(",", ":")).encode("utf-8")
        calculated_root = hashlib.sha256(serialized_digests).hexdigest()

        if calculated_root.lower() != expected_root_commitment.lower():
            return False, {}, "Cryptographic selective disclosure verification failed: Reconstructed commitment does not match issuer root."

        return True, verified_claims, ""
