from typing import Optional, Dict
from pydantic import BaseModel, Field

class BlockchainPublicConfig(BaseModel):
    chain_id: int
    network_name: str
    rpc_url: str
    contracts: Dict[str, Optional[str]] = Field(
        default_factory=lambda: {
            "IssuerRegistry": None,
            "CredentialRegistry": None,
            "CredentialStatusRegistry": None
        }
    )
