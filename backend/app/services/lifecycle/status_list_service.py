import gzip
import base64
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.status_list import StatusList
from backend.app.core.exceptions import ResourceNotFoundException, ValidationException

class BitstringStatusListService:
    """
    W3C Bitstring Status List 1.0 Specification Implementation.
    Generates, compresses (GZIP), multibase encodes, and evaluates cryptographic status bitstrings.
    """

    DEFAULT_BIT_LENGTH = 16384 # 2 KB uncompressed = 16,384 credentials per list

    @classmethod
    def encode_bitstring(cls, raw_bits: bytearray) -> str:
        """
        Compresses a bitstring bytearray with GZIP (mtime=0 for deterministic reproducibility)
        and encodes as multibase base64url-no-pad (prefix 'u').
        """
        compressed = gzip.compress(raw_bits, mtime=0)
        b64 = base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")
        return f"u{b64}"

    @classmethod
    def decode_bitstring(cls, encoded: str) -> bytearray:
        """
        Decodes a multibase base64url-no-pad bitstring and decompresses via GZIP.
        """
        if not encoded.startswith("u"):
            raise ValidationException("Invalid multibase encoding: expected 'u' prefix for base64url.")
        raw_b64 = encoded[1:]
        # Pad base64
        padding = (4 - len(raw_b64) % 4) % 4
        padded = raw_b64 + ("=" * padding)
        compressed = base64.urlsafe_b64decode(padded)
        decompressed = gzip.decompress(compressed)
        return bytearray(decompressed)

    @classmethod
    def get_bit(cls, raw_bits: bytearray, index: int) -> int:
        """
        Retrieves the bit value (0 or 1) at a given index within the bitstring.
        Per W3C Bitstring Status List: MSB first within each byte.
        """
        byte_idx = index // 8
        bit_offset = 7 - (index % 8)
        if byte_idx >= len(raw_bits):
            raise IndexError("Bit index exceeds status list capacity.")
        return 1 if (raw_bits[byte_idx] & (1 << bit_offset)) else 0

    @classmethod
    def set_bit(cls, raw_bits: bytearray, index: int, value: int) -> bytearray:
        """
        Sets the bit value (0 or 1) at a given index within the bitstring.
        """
        byte_idx = index // 8
        bit_offset = 7 - (index % 8)
        if byte_idx >= len(raw_bits):
            raise IndexError("Bit index exceeds status list capacity.")
        if value:
            raw_bits[byte_idx] |= (1 << bit_offset)
        else:
            raw_bits[byte_idx] &= ~(1 << bit_offset)
        return raw_bits

    @classmethod
    async def get_or_create_status_list(
        cls,
        db: AsyncSession,
        organization_id: str,
        purpose: str = "revocation",
    ) -> Tuple[StatusList, int]:
        """
        Finds an existing status list for the organization with remaining capacity,
        or creates a new status list credential. Returns (StatusList, allocated_index).
        """
        stmt = select(StatusList).where(
            StatusList.organization_id == organization_id,
            StatusList.purpose == purpose,
            StatusList.current_index < StatusList.bit_length,
        ).order_by(StatusList.list_number.asc())

        res = await db.execute(stmt)
        slist = res.scalar_one_or_none()

        if not slist:
            # Count existing lists to assign next list_number
            count_stmt = select(StatusList.list_number).order_by(StatusList.list_number.desc())
            c_res = await db.execute(count_stmt)
            max_num = c_res.scalars().first() or 0
            new_num = max_num + 1

            num_bytes = cls.DEFAULT_BIT_LENGTH // 8
            initial_bits = bytearray(num_bytes)
            encoded = cls.encode_bitstring(initial_bits)

            slist = StatusList(
                list_number=new_num,
                organization_id=organization_id,
                purpose=purpose,
                bit_length=cls.DEFAULT_BIT_LENGTH,
                current_index=0,
                raw_bits=bytes(initial_bits),
                encoded_list=encoded,
            )
            db.add(slist)
            await db.flush()

        allocated_idx = slist.current_index
        slist.current_index += 1
        await db.commit()
        await db.refresh(slist)

        return slist, allocated_idx

    @classmethod
    async def update_status_bit(
        cls,
        db: AsyncSession,
        status_list_id: str,
        index: int,
        value: int,
    ) -> StatusList:
        stmt = select(StatusList).where(StatusList.id == status_list_id)
        res = await db.execute(stmt)
        slist = res.scalar_one_or_none()
        if not slist:
            raise ResourceNotFoundException("Status list record not found.")

        bits = bytearray(slist.raw_bits)
        cls.set_bit(bits, index, value)
        slist.raw_bits = bytes(bits)
        slist.encoded_list = cls.encode_bitstring(bits)

        await db.commit()
        await db.refresh(slist)
        return slist

    @classmethod
    def generate_status_list_credential(
        cls,
        slist: StatusList,
        issuer_did: str,
        base_url: str = "https://decentralid.org",
    ) -> Dict[str, Any]:
        """
        Constructs standard W3C BitstringStatusListCredential JSON document.
        """
        list_url = f"{base_url}/api/v1/status-lists/{slist.list_number}"
        return {
            "@context": [
                "https://www.w3.org/ns/credentials/v2"
            ],
            "id": list_url,
            "type": ["VerifiableCredential", "BitstringStatusListCredential"],
            "issuer": issuer_did,
            "validFrom": slist.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "credentialSubject": {
                "id": f"{list_url}#list",
                "type": "BitstringStatusList",
                "statusPurpose": slist.purpose,
                "encodedList": slist.encoded_list,
            }
        }
