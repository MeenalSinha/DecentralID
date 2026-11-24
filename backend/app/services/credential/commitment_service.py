import secrets
import hmac
from typing import Tuple, Dict, Any
from eth_account import Account
from eth_utils import keccak
from backend.app.services.credential.canonicalization import CanonicalizationService

class CommitmentService:
    """
    High-entropy salted cryptographic commitment engine.
    Anchors privacy-preserving zero-PII commitments on-chain:
    C = keccak256( canonicalJSON(S) || R )
    where S is the canonicalized credential subject claims and R is a 256-bit random salt.
    """

    @staticmethod
    def generate_salt() -> bytes:
        """Generates a cryptographically secure 256-bit (32-byte) random salt."""
        return secrets.token_bytes(32)

    @staticmethod
    def compute_commitment(subject: Dict[str, Any], salt: bytes) -> str:
        """
        Computes the 32-byte keccak256 salted commitment over the canonicalized subject claims.
        Returns a '0x'-prefixed 66-character hex string.
        """
        if not isinstance(salt, (bytes, bytearray)) or len(salt) != 32:
            raise ValueError("Salt must be exactly 32 cryptographically secure bytes.")

        canonical_subject_bytes = CanonicalizationService.canonicalize(subject)
        preimage = canonical_subject_bytes + salt
        commitment_bytes = keccak(preimage)
        return "0x" + commitment_bytes.hex()

    @staticmethod
    def generate_subject_commitment(subject: Dict[str, Any]) -> Tuple[str, bytes]:
        """
        Helper that generates a fresh salt and computes its commitment.
        Returns (commitment_hex, salt_bytes).
        """
        salt = CommitmentService.generate_salt()
        commitment = CommitmentService.compute_commitment(subject, salt)
        return commitment, salt

    @staticmethod
    def verify_commitment(subject: Dict[str, Any], salt: bytes, expected_commitment: str) -> bool:
        """
        Verifies that a given subject and salt reproduce the expected commitment in constant time.
        """
        try:
            computed = CommitmentService.compute_commitment(subject, salt)
            return hmac.compare_digest(computed.lower(), expected_commitment.lower())
        except Exception:
            return False
