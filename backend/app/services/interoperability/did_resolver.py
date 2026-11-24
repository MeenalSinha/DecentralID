import re
from typing import Dict, Any, Optional

class DIDResolutionError(Exception):
    def __init__(self, message: str, code: str = "invalidDid"):
        super().__init__(message)
        self.code = code

class BaseDIDResolver:
    async def resolve(self, did: str) -> Dict[str, Any]:
        raise NotImplementedError

class DIDPKHResolver(BaseDIDResolver):
    """
    Implements W3C did:pkh method specification for EIP-155 Ethereum/Polygon addresses.
    Format: did:pkh:eip155:<chainId>:<accountAddress>
    """
    PATTERN = re.compile(r"^did:pkh:eip155:(\d+):(0x[a-fA-F0-9]{40})$")

    async def resolve(self, did: str) -> Dict[str, Any]:
        match = self.PATTERN.match(did)
        if not match:
            raise DIDResolutionError(f"Invalid did:pkh identifier: {did}", "invalidDid")
        
        chain_id, address = match.groups()
        vm_id = f"{did}#blockchainAccountId"
        
        did_document = {
            "@context": [
                "https://www.w3.org/ns/did/v1",
                "https://w3id.org/security/suites/ed25519-2020/v1",
                "https://w3id.org/security/suites/jws-2020/v1"
            ],
            "id": did,
            "verificationMethod": [
                {
                    "id": vm_id,
                    "type": "EcdsaSecp256k1RecoveryMethod2020",
                    "controller": did,
                    "blockchainAccountId": f"eip155:{chain_id}:{address.lower()}"
                }
            ],
            "authentication": [vm_id],
            "assertionMethod": [vm_id]
        }
        
        return {
            "didDocument": did_document,
            "didResolutionMetadata": {"contentType": "application/did+ld+json"},
            "didDocumentMetadata": {"canonicalId": did}
        }

class DIDKeyResolver(BaseDIDResolver):
    """
    Implements W3C did:key method specification.
    Format: did:key:<multibaseEncodedKey>
    """
    PATTERN = re.compile(r"^did:key:(z[a-km-zA-HJ-NP-Z1-9]+)$")

    async def resolve(self, did: str) -> Dict[str, Any]:
        match = self.PATTERN.match(did)
        if not match:
            raise DIDResolutionError(f"Invalid did:key identifier: {did}", "invalidDid")
        
        key_identifier = match.group(1)
        vm_id = f"{did}#{key_identifier}"
        
        # Determine key type based on multicodec prefix
        # Secp256k1 multicodec begins with zQ3sh...
        if key_identifier.startswith("zQ3sh") or key_identifier.startswith("z"):
            key_type = "JsonWebKey2020"
        else:
            key_type = "Ed25519VerificationKey2020"

        did_document = {
            "@context": [
                "https://www.w3.org/ns/did/v1",
                "https://w3id.org/security/suites/jws-2020/v1"
            ],
            "id": did,
            "verificationMethod": [
                {
                    "id": vm_id,
                    "type": key_type,
                    "controller": did,
                    "publicKeyMultibase": key_identifier
                }
            ],
            "authentication": [vm_id],
            "assertionMethod": [vm_id]
        }
        
        return {
            "didDocument": did_document,
            "didResolutionMetadata": {"contentType": "application/did+ld+json"},
            "didDocumentMetadata": {"canonicalId": did}
        }

class DIDWebResolver(BaseDIDResolver):
    """
    Implements W3C did:web method specification for institutions.
    Format: did:web:<domain>
    """
    PATTERN = re.compile(r"^did:web:([a-zA-Z0-9.-]+)$")

    async def resolve(self, did: str) -> Dict[str, Any]:
        match = self.PATTERN.match(did)
        if not match:
            raise DIDResolutionError(f"Invalid did:web identifier: {did}", "invalidDid")
        
        domain = match.group(1)
        vm_id = f"{did}#key-1"
        
        did_document = {
            "@context": [
                "https://www.w3.org/ns/did/v1",
                "https://w3id.org/security/suites/jws-2020/v1"
            ],
            "id": did,
            "verificationMethod": [
                {
                    "id": vm_id,
                    "type": "JsonWebKey2020",
                    "controller": did,
                    "domain": domain
                }
            ],
            "authentication": [vm_id],
            "assertionMethod": [vm_id]
        }
        
        return {
            "didDocument": did_document,
            "didResolutionMetadata": {"contentType": "application/did+ld+json"},
            "didDocumentMetadata": {"canonicalId": did}
        }

class UniversalDIDResolver:
    """
    Universal DID Resolver dispatcher supporting did:pkh, did:key, and did:web.
    """
    def __init__(self):
        self.resolvers = {
            "pkh": DIDPKHResolver(),
            "key": DIDKeyResolver(),
            "web": DIDWebResolver()
        }

    async def resolve(self, did: str) -> Dict[str, Any]:
        if not did.startswith("did:"):
            raise DIDResolutionError(f"Identifier is not a DID: {did}", "methodNotSupported")
        
        parts = did.split(":")
        if len(parts) < 3:
            raise DIDResolutionError(f"Malformed DID: {did}", "invalidDid")
        
        method = parts[1]
        resolver = self.resolvers.get(method)
        if not resolver:
            raise DIDResolutionError(f"DID method not supported: did:{method}", "methodNotSupported")
        
        return await resolver.resolve(did)

# Global singleton
universal_did_resolver = UniversalDIDResolver()
