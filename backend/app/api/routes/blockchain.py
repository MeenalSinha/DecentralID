import json
import os
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.schemas.blockchain import BlockchainPublicConfig

router = APIRouter(prefix="/blockchain", tags=["Blockchain Configuration"])

@router.get("/config", response_model=BlockchainPublicConfig)
async def get_blockchain_config() -> BlockchainPublicConfig:
    # Check if network deployment manifest exists
    issuer_addr = settings.ISSUER_REGISTRY_ADDRESS
    cred_addr = settings.CREDENTIAL_REGISTRY_ADDRESS
    status_addr = settings.CREDENTIAL_STATUS_REGISTRY_ADDRESS

    network_dir = settings.NETWORK_NAME.lower()
    manifest_path = os.path.join(os.path.dirname(__file__), f"../../../../deployments/{network_dir}/manifest.json")
    if not os.path.exists(manifest_path):
        # Fallback to local manifest if exists
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

    # Never expose sensitive RPC credentials in production
    public_rpc = settings.RPC_URL
    if settings.ENVIRONMENT.lower() == "production" and ("@" in public_rpc or "key=" in public_rpc):
        public_rpc = ""

    return BlockchainPublicConfig(
        chain_id=settings.CHAIN_ID,
        network_name=settings.NETWORK_NAME,
        rpc_url=public_rpc,
        contracts={
            "IssuerRegistry": issuer_addr,
            "CredentialRegistry": cred_addr,
            "CredentialStatusRegistry": status_addr,
        },
    )
