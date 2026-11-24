import json
import os
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.schemas.blockchain import BlockchainPublicConfig

router = APIRouter(prefix="/blockchain", tags=["Blockchain Configuration"])

@router.get("/config", response_model=BlockchainPublicConfig)
async def get_blockchain_config() -> BlockchainPublicConfig:
    # Check if local deployment manifest exists
    issuer_addr = settings.ISSUER_REGISTRY_ADDRESS
    cred_addr = settings.CREDENTIAL_REGISTRY_ADDRESS
    status_addr = settings.CREDENTIAL_STATUS_REGISTRY_ADDRESS

    manifest_path = os.path.join(os.path.dirname(__file__), "../../../../deployments/local/manifest.json")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
                contracts = manifest.get("contracts", {})
                issuer_addr = issuer_addr or contracts.get("IssuerRegistry")
                cred_addr = cred_addr or contracts.get("CredentialRegistry")
                status_addr = status_addr or contracts.get("CredentialStatusRegistry")
        except Exception:
            pass

    return BlockchainPublicConfig(
        chain_id=settings.CHAIN_ID,
        network_name=settings.NETWORK_NAME,
        rpc_url=settings.RPC_URL,
        contracts={
            "IssuerRegistry": issuer_addr,
            "CredentialRegistry": cred_addr,
            "CredentialStatusRegistry": status_addr,
        },
    )
