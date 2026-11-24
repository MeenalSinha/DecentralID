import os
import json
import base64
import hashlib
from typing import Tuple, Optional
from uuid import UUID
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.config import settings
from backend.app.models.network import StorageRecord


def compute_ipfs_cidv1_raw(content_bytes: bytes) -> str:
    """
    Computes a deterministic IPFS CIDv1 with raw multicodec (0x55)
    and sha2-256 multihash (0x12, length 0x20) encoded in base32 (multibase 'b').
    Produces a standard 'bafkrei...' CID matching IPFS specification.
    """
    sha256_digest = hashlib.sha256(content_bytes).digest()
    # CIDv1 prefix: 0x01 (version 1), 0x55 (raw binary codec), 0x12 (sha2-256), 0x20 (32 bytes)
    header = bytes([0x01, 0x55, 0x12, 0x20])
    raw_cid = header + sha256_digest
    b32 = base64.b32encode(raw_cid).decode("ascii").lower().rstrip("=")
    return f"b{b32}"


class IpfsStorageService:
    @staticmethod
    def encrypt_data(data: dict, custom_key: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Encrypts dictionary payload using AES-256-GCM.
        Returns: (encrypted_bytes, 32_byte_aes_key)
        encrypted_bytes format: 12-byte nonce + 16-byte tag + ciphertext
        """
        raw_json = json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")
        key = custom_key if custom_key else AESGCM.generate_key(bit_length=256)
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)  # 96-bit standard nonce for GCM
        ciphertext = aesgcm.encrypt(nonce, raw_json, None)
        payload = nonce + ciphertext
        return payload, key

    @staticmethod
    def decrypt_data(payload: bytes, key: bytes) -> dict:
        """
        Decrypts AES-256-GCM encrypted payload.
        """
        if len(payload) < 28:
            raise ValueError("Payload too short for AES-GCM (must contain 12-byte nonce + 16-byte tag)")
        nonce = payload[:12]
        ciphertext = payload[12:]
        aesgcm = AESGCM(key)
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return json.loads(decrypted_bytes.decode("utf-8"))

    @classmethod
    async def store_encrypted_credential(
        cls,
        data: dict,
        db: AsyncSession,
        organization_id: Optional[UUID] = None,
        custom_key: Optional[bytes] = None
    ) -> Tuple[StorageRecord, bytes]:
        """
        Encrypts credential data, computes IPFS CIDv1, stores block, and registers StorageRecord.
        Returns: (StorageRecord, 32_byte_aes_key)
        """
        encrypted_bytes, key = cls.encrypt_data(data, custom_key=custom_key)
        cid = compute_ipfs_cidv1_raw(encrypted_bytes)
        
        provider = "local"
        if settings.PINATA_JWT:
            provider = "pinata"

        # Write to local content-addressed storage repository
        storage_dir = os.path.join(settings.STORAGE_DIR, "ipfs")
        os.makedirs(storage_dir, exist_ok=True)
        file_path = os.path.join(storage_dir, cid)
        with open(file_path, "wb") as f:
            f.write(encrypted_bytes)

        stmt = select(StorageRecord).where(StorageRecord.cid == cid)
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()

        if not record:
            record = StorageRecord(
                organization_id=str(organization_id) if organization_id else None,
                cid=cid,
                content_type="application/json+encrypted",
                size_bytes=len(encrypted_bytes),
                encryption_algorithm="AES-256-GCM",
                provider=provider,
                is_pinned=True
            )
            db.add(record)
            await db.commit()
            await db.refresh(record)

        return record, key

    @classmethod
    async def retrieve_and_decrypt(cls, cid: str, key: bytes, db: AsyncSession) -> dict:
        """
        Retrieves encrypted block by CID, verifies integrity, and decrypts.
        """
        stmt = select(StorageRecord).where(StorageRecord.cid == cid)
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            raise ValueError(f"Storage record for CID {cid} not found")

        storage_dir = os.path.join(settings.STORAGE_DIR, "ipfs")
        file_path = os.path.join(storage_dir, cid)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Content-addressed file for CID {cid} missing from storage")

        with open(file_path, "rb") as f:
            encrypted_bytes = f.read()

        # Verify content-addressing integrity: SHA256 of read bytes must match CID
        verified_cid = compute_ipfs_cidv1_raw(encrypted_bytes)
        if verified_cid != cid:
            raise ValueError(f"CID integrity mismatch: expected {cid}, computed {verified_cid}")

        return cls.decrypt_data(encrypted_bytes, key)
