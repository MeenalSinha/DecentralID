import os
import base64
import json
from typing import Any, Tuple, Dict
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from backend.app.core.config import settings

class EncryptionService:
    """
    Cryptographic storage encryption service using AES-256-GCM authenticated encryption.
    Protects sensitive credential subject claims, PII, and salts at rest in the database.
    """

    _cached_key: bytes = None

    @classmethod
    def _get_master_key(cls) -> bytes:
        if cls._cached_key is not None:
            return cls._cached_key

        if settings.CREDENTIAL_ENCRYPTION_KEY:
            try:
                # If key is provided as base64 or hex
                raw = settings.CREDENTIAL_ENCRYPTION_KEY
                if len(raw) == 64: # hex
                    cls._cached_key = bytes.fromhex(raw)
                elif len(raw) == 44: # base64
                    cls._cached_key = base64.b64decode(raw)
                else:
                    cls._cached_key = raw.encode("utf-8")[:32].ljust(32, b"\0")
            except Exception:
                cls._cached_key = settings.CREDENTIAL_ENCRYPTION_KEY.encode("utf-8")[:32].ljust(32, b"\0")
        else:
            # Deterministically derive a dedicated 256-bit encryption key from SECRET_KEY via HKDF-SHA256
            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"decentralid-storage-encryption-salt-v1",
                info=b"decentralid-credential-storage-encryption-key",
            )
            cls._cached_key = hkdf.derive(settings.SECRET_KEY.encode("utf-8"))

        return cls._cached_key

    @classmethod
    def encrypt_data(cls, plaintext: str) -> str:
        """
        Encrypts a plaintext string with AES-256-GCM using a cryptographically random 12-byte nonce.
        Returns a base64 encoded string containing: nonce (12 bytes) + ciphertext + auth_tag (16 bytes).
        """
        key = cls._get_master_key()
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("utf-8")

    @classmethod
    def decrypt_data(cls, encrypted_b64: str) -> str:
        """
        Decrypts an AES-256-GCM ciphertext payload and verifies its cryptographic authentication tag.
        """
        key = cls._get_master_key()
        aesgcm = AESGCM(key)
        raw = base64.b64decode(encrypted_b64)
        if len(raw) < 28: # 12 bytes nonce + 16 bytes tag minimum
            raise ValueError("Invalid encrypted payload length.")

        nonce = raw[:12]
        ciphertext = raw[12:]
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted_bytes.decode("utf-8")

    @classmethod
    def encrypt_json(cls, data: Any) -> str:
        """Serializes and encrypts arbitrary Python dict/data."""
        return cls.encrypt_data(json.dumps(data, ensure_ascii=False))

    @classmethod
    def decrypt_json(cls, encrypted_b64: str) -> Any:
        """Decrypts and deserializes JSON data."""
        plaintext = cls.decrypt_data(encrypted_b64)
        return json.loads(plaintext)

    @classmethod
    def decrypt_subject(cls, encrypted_b64: str, *args, **kwargs) -> Dict[str, Any]:
        """Convenience helper to decrypt credential subject claims dictionary."""
        return cls.decrypt_json(encrypted_b64)

    @classmethod
    def decrypt_salt(cls, encrypted_b64: str, *args, **kwargs) -> bytes:
        """Convenience helper to decrypt 32-byte salt."""
        raw_hex = cls.decrypt_data(encrypted_b64)
        clean_hex = raw_hex[2:] if raw_hex.startswith("0x") else raw_hex
        return bytes.fromhex(clean_hex)
