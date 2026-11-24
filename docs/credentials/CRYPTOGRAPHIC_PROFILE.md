# DecentralID Cryptographic Profile & Standards Specification
**Standard Compliance:** W3C Verifiable Credentials Data Model v2.0 • W3C Data Integrity 1.0 • RFC 8785 (JCS) • secp256k1 ECDSA

---

## 1. Cryptographic Suite Selection (ADR-005)

### Status: APPROVED

### Context
DecentralID requires an interoperable, standards-compliant securing mechanism for verifiable credentials. In earlier prototypes, unstructured JSON files were hashed arbitrarily or coupled solely to Ethereum personal sign strings.

### Decision
DecentralID adopts **W3C Data Integrity 1.0** with the **`ecdsa-jcs-2019`** cryptosuite pattern using `secp256k1` curves:
1. **Canonicalization:** RFC 8785 JSON Canonicalization Scheme (JCS). Ensures consistent lexicographical key ordering and IEEE 754 number representation across heterogeneous platforms without relying on RDF dataset normalization.
2. **Digest Algorithm:** Keccak-256 / SHA-256 over `keccak256(canonicalProofOptions) || keccak256(canonicalDocumentWithoutProof)`.
3. **Signature Algorithm:** ECDSA over `secp256k1` generating 65-byte recoverable signatures `(r, s, v)` formatted as a `0x`-prefixed hex string.
4. **Verification Method:** `did:pkh:eip155:<chainId>:<issuerSigningAddress>#key-1`, enabling decentralized public key resolution from Ethereum/EVM addresses.

---

## 2. On-Chain Cryptographic Anchors (Salted Commitments)

To eliminate on-chain personal data (PII) while ensuring non-repudiation, DecentralID binds the canonicalized credential subject claims $S$ to a 256-bit high-entropy random salt $R$:

$$C = \text{keccak256}(\text{canonicalJSON}(S) \parallel R)$$

- **$S$:** Canonicalized JSON bytes of `credentialSubject` via RFC 8785 JCS.
- **$R$:** 32-byte cryptographically secure random value generated via `secrets.token_bytes(32)`.
- **$C$:** 32-byte hex string anchored in `CredentialRegistry.registerCredential(credentialId, commitment, issuer)`.

### Privacy Guarantees
- The salt $R$ is encrypted at rest using AES-256-GCM and stored only for the authorized issuer and holder.
- Zero plaintext subject data or salts are ever broadcast to the public blockchain or emitted in smart contract events.

---

## 3. Storage Security (Encryption at Rest)

The operational database stores:
- `encrypted_subject`: AES-256-GCM ciphertext containing the complete claims JSON.
- `encrypted_salt`: AES-256-GCM ciphertext containing the 256-bit salt.
- `key_id`: Active key identifier (default `master-v1`) enabling zero-downtime key rotation.
- `nonce`: Unique 12-byte random nonce generated per record (`os.urandom(12)`).
