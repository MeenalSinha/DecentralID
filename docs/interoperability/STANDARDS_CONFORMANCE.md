# DecentralID: Standards Conformance Framework (Phase 14)

## 1. Supported Standards & Specifications

DecentralID conforms strictly to normative W3C and IETF digital identity specifications:

| Specification | Supported Version | Implementation Component | Conformance Scope & Test Evidence |
|---|---|---|---|
| **W3C Verifiable Credentials Data Model** | 2.0 / 1.1 | `credential_portability.py`, `signing_service.py` | Full JSON-LD representation with `@context`, `type`, `issuer`, `validFrom`, `credentialSubject`, and `proof` |
| **W3C Data Integrity 1.0** | Candidate Rec 2024 | `signing_service.py`, `verification_service.py` | Cryptographic suite `ecdsa-jcs-2019`, `DataIntegrityProof` with double-SHA256 digest |
| **RFC 8785 JSON Canonicalization Scheme (JCS)** | IETF RFC 8785 | `canonicalization.py` | Deterministic, whitespace-stripped UTF-8 representation with lexicographical Unicode code-point sorting |
| **W3C DID Core 1.0 & DID Resolution** | Recommendation | `did_resolver.py` | `UniversalDIDResolver` supporting `did:pkh` (EIP-155), `did:key` (Secp256k1/Ed25519), and `did:web` |
| **W3C Bitstring Status List v1.0** | W3C Draft | `status_list_service.py` | Gzip-compressed multibase-encoded bitstrings with bit operations for revocation/suspension |
| **OpenID for Verifiable Credential Issuance (OID4VCI)** | Draft 13 | `interoperability.py` | Discovery metadata at `/.well-known/openid-credential-issuer` |

---

## 2. Cryptographic Suites & DID Method Resolution

### 2.1 Supported Cryptographic Suites
1. **`ecdsa-jcs-2019` (Primary Standard):**
   - Preimage calculation: $\text{SHA-256}(\text{SHA-256}(\text{canonicalOptions}) \parallel \text{SHA-256}(\text{canonicalDoc}))$
   - Signing curve: `secp256k1` ECDSA with Ethereum personal message prefix
   - Verification Method: `did:pkh:eip155:137:<address>#blockchainAccountId`
2. **`ecdsa-jcs-2019-keccak` (Legacy Backward Compatibility):**
   - Keccak-256 digest fallback for earlier testnet credentials.

### 2.2 DID Resolution Engine
- `did:pkh:eip155:<chainId>:<address>`: Resolves on-chain EVM address into standardized DID document exposing `EcdsaSecp256k1RecoveryMethod2020` verification method.
- `did:key:<multibaseKey>`: Resolves self-describing cryptographic public keys into `JsonWebKey2020` verification methods.
- `did:web:<domain>`: Resolves institutional web domains into verification methods.

---

## 3. Credential Portability & Foreign Provenance Rules

### Rule of Non-Reissuance
DecentralID wallet supports importing external W3C Verifiable Credentials issued by foreign institutions. However:
1. Imported credentials strictly retain their original `issuer` and `proof`.
2. Imported credentials are flagged as `is_imported: True`.
3. DecentralID will **NEVER** sign, reissue, or wrap a foreign credential as a DecentralID-issued credential.
