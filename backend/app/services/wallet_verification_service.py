import datetime
from eth_account.messages import encode_defunct
from eth_account import Account

class WalletVerificationService:
    @staticmethod
    def construct_siwe_message(
        domain: str,
        address: str,
        uri: str,
        version: str,
        chain_id: int,
        nonce: str,
        issued_at: datetime.datetime,
        expiration_time: datetime.datetime,
    ) -> str:
        """Construct standard EIP-4361 compliant message format."""
        formatted_issued = issued_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        formatted_expires = expiration_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        message = (
            f"{domain} wants you to sign in with your Ethereum account:\n"
            f"{address}\n\n"
            f"Sign in to DecentralID Trust Infrastructure.\n\n"
            f"URI: {uri}\n"
            f"Version: {version}\n"
            f"Chain ID: {chain_id}\n"
            f"Nonce: {nonce}\n"
            f"Issued At: {formatted_issued}\n"
            f"Expiration Time: {formatted_expires}"
        )
        return message

    @staticmethod
    def verify_signature(message: str, signature: str, expected_address: str) -> bool:
        """Cryptographically recover the signer address from ECDSA signature."""
        try:
            signable_message = encode_defunct(text=message)
            recovered_address = Account.recover_message(signable_message, signature=signature)
            return recovered_address.lower() == expected_address.lower()
        except Exception:
            return False
