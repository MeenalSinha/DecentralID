import datetime
import hashlib
from typing import Dict, Any, Optional
from eth_account import Account
from eth_account.messages import encode_defunct

from backend.app.services.credential.signing_service import SigningService

class OfflineVerificationService:
    DEFAULT_MAX_OFFLINE_AGE_SECONDS = 86400 # 24 hours

    @classmethod
    def create_offline_package(
        cls,
        credential: Dict[str, Any],
        status: str,
        signing_key: str,
        status_index: int = 0
    ) -> Dict[str, Any]:
        """
        Creates a time-bounded, cryptographically signed offline verification bundle.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        timestamp_str = now.isoformat()
        
        # Digest representing the status snapshot
        status_data = f"{credential.get('id')}:{status}:{status_index}:{timestamp_str}"
        digest = hashlib.sha256(status_data.encode("utf-8")).digest()
        
        account = Account.from_key(signing_key)
        signable = encode_defunct(primitive=digest)
        signature = account.sign_message(signable).signature.hex()

        return {
            "credential": credential,
            "status_snapshot": {
                "status": status,
                "status_index": status_index,
                "timestamp": timestamp_str,
                "authority_address": account.address,
                "signature": f"0x{signature}"
            }
        }

    @classmethod
    def verify_offline_package(
        cls,
        package: Dict[str, Any],
        max_offline_age_seconds: int = DEFAULT_MAX_OFFLINE_AGE_SECONDS,
        current_time: Optional[datetime.datetime] = None
    ) -> Dict[str, Any]:
        """
        Verifies offline credential presentation and enforces the Critical Freshness Rule.
        Never converts stale offline status into a definitive VALID result (returns INDETERMINATE).
        """
        if current_time is None:
            current_time = datetime.datetime.now(datetime.timezone.utc)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=datetime.timezone.utc)

        credential = package.get("credential")
        snapshot = package.get("status_snapshot")
        
        if not credential or not snapshot:
            return {
                "is_valid": False,
                "status": "INVALID",
                "error_code": "MALFORMED_OFFLINE_PACKAGE",
                "reason": "Missing 'credential' or 'status_snapshot' in offline package"
            }

        # 1. First Verify Cryptographic Signature on Credential
        is_sig_valid, signer_addr, err_reason = SigningService.verify_credential_proof(credential)
        if not is_sig_valid:
            return {
                "is_valid": False,
                "status": "INVALID",
                "error_code": "SIGNATURE_VERIFICATION_FAILED",
                "reason": f"Credential signature verification failed: {err_reason}"
            }

        # 2. Check Freshness Window (CRITICAL FRESHNESS RULE)
        snapshot_time_str = snapshot.get("timestamp")
        if not snapshot_time_str:
            return {
                "is_valid": False,
                "status": "INDETERMINATE",
                "error_code": "MISSING_SNAPSHOT_TIMESTAMP",
                "reason": "Status snapshot contains no timestamp; current revocation state is indeterminate."
            }

        try:
            snapshot_time = datetime.datetime.fromisoformat(snapshot_time_str)
            if snapshot_time.tzinfo is None:
                snapshot_time = snapshot_time.replace(tzinfo=datetime.timezone.utc)
        except Exception:
            return {
                "is_valid": False,
                "status": "INDETERMINATE",
                "error_code": "INVALID_SNAPSHOT_TIMESTAMP",
                "reason": "Corrupted timestamp in status snapshot; status is indeterminate."
            }

        age_seconds = (current_time - snapshot_time).total_seconds()
        if age_seconds < 0:
            age_seconds = 0 # Clock skew allowance

        if age_seconds > max_offline_age_seconds:
            return {
                "is_valid": False,
                "status": "INDETERMINATE",
                "error_code": "STALE_STATUS_DATA",
                "age_seconds": age_seconds,
                "max_allowed_age": max_offline_age_seconds,
                "reason": (
                    f"Offline status snapshot is stale ({int(age_seconds)}s old, "
                    f"exceeding max {max_offline_age_seconds}s). "
                    "Cannot guarantee non-revocation without re-synchronization."
                )
            }

        # 3. Verify Authority Signature on Status Snapshot
        status_val = snapshot.get("status")
        status_idx = snapshot.get("status_index", 0)
        auth_addr = snapshot.get("authority_address")
        sig_hex = snapshot.get("signature", "")
        
        status_data = f"{credential.get('id')}:{status_val}:{status_idx}:{snapshot_time_str}"
        digest = hashlib.sha256(status_data.encode("utf-8")).digest()
        
        try:
            signable = encode_defunct(primitive=digest)
            recovered_auth = Account.recover_message(signable, signature=sig_hex)
            if recovered_auth.lower() != auth_addr.lower():
                return {
                    "is_valid": False,
                    "status": "INVALID",
                    "error_code": "STATUS_AUTHORITY_TAMPERED",
                    "reason": "Status snapshot signature does not match authority address."
                }
        except Exception as e:
            return {
                "is_valid": False,
                "status": "INVALID",
                "error_code": "STATUS_SIGNATURE_FAILED",
                "reason": f"Status signature recovery failed: {str(e)}"
            }

        # 4. Check Status Value
        if status_val.upper() in ("REVOKED", "SUSPENDED"):
            return {
                "is_valid": False,
                "status": status_val.upper(),
                "error_code": f"CREDENTIAL_{status_val.upper()}",
                "age_seconds": age_seconds,
                "reason": f"Credential is confirmed {status_val.upper()} in offline snapshot."
            }

        # All conditions satisfied within valid offline freshness window
        return {
            "is_valid": True,
            "status": "VALID_OFFLINE",
            "signer_address": signer_addr,
            "age_seconds": age_seconds,
            "freshness": "FRESH",
            "disclosed_subject": credential.get("credentialSubject", {})
        }
