# Cryptographic Profile v2: Standards-Compliant W3C VCs, Client-Side Signing & Merkle Selective Disclosure

**DecentralID — Portable, Privacy-Preserving Verifiable Credentials for Digital India**  
**Specification Version:** 2.0.0 (Phases 10–11 Architecture)  
**Status:** Active / Production-Ready  
**Standard Compliance:** W3C Verifiable Credentials Data Model v2.0, RFC 8785 (JCS), RFC 6979, EIP-712 / personal_sign, W3C ECDSA Cryptosuite v2019

---

## 1. Executive Summary

DecentralID Cryptographic Profile v2 upgrades the cryptographic architecture of DecentralID to full compliance with global W3C Verifiable Credentials standards and introduces zero-knowledge, mathematically sound privacy enhancements:

1. **Standards-Compliant W3C Proof Profile (`ecdsa-jcs-2019`)**:
   - Uses RFC 8785 JSON Canonicalization Scheme (JCS) deterministically.
   - Signs over standard double-SHA-256 digest: `SHA-256(SHA-256(canonical(proofOptions)) || SHA-256(canonical(docWithoutProof)))`.
   - Backward-compatible verification for legacy Keccak-256 signatures (`ecdsa-jcs-2019-keccak`).
2. **Client-Side Wallet & Key Custody Architecture**:
   - Eliminates institutional private key custody from the web application state.
   - Implements two-phase signing: payload retrieval (`GET /credentials/{id}/signing-payload`) and external signature submission (`POST /credentials/{id}/complete-signing`).
   - Supports Hardware Security Modules (HSMs), KMS (AWS/GCP), Vault, and client-side Web3 wallets (MetaMask, Ledger) via standard `personal_sign` or EIP-712.
3. **Cryptographic Selective Disclosure via Merkle Claim Commitments**:
   - Every individual claim in `credentialSubject` is committed to using a cryptographically secure 256-bit random salt: `commitment_i = SHA-256(salt_i || key_i || value_i)`.
   - The Root Commitment is derived as the root of the sorted claim commitments: `rootCommitment = SHA-256(sorted(commitments))`.
   - The Root Commitment is anchored in the W3C credential and on-chain status registry.
   - In a Verifiable Presentation, holders disclose only authorized attributes alongside their salts; undisclosed attributes remain completely hidden without compromising the mathematical proof of authenticity.

---

## 2. Standards-Compliant W3C Proof Format (`ecdsa-jcs-2019`)

### 2.1 Canonicalization & Hashing Specification

The standard proof representation in DecentralID follows the W3C ECDSA JCS 2019 Cryptosuite:

```json
{
  "type": "ecdsa-jcs-2019",
  "created": "2026-11-24T12:00:00Z",
  "verificationMethod": "did:ethr:0x5B38Da6a701c568545dCfcB03FcB875f56beddC4#key-1",
  "proofPurpose": "assertionMethod",
  "proofValue": "0x..."
}
```

#### Deterministic Canonicalization (RFC 8785)
All whitespace is stripped, object keys are sorted lexicographically by Unicode code point, numbers are rendered in standardized IEEE 754 format without redundant exponents or decimal points, and string escapes follow strict UTF-8 rules.

#### Double-SHA-256 Digest Calculation
```python
def compute_document_hash_standard(doc_without_proof: dict, proof_options: dict) -> bytes:
    canonical_options = canonicalize(proof_options)
    canonical_doc = canonicalize(doc_without_proof)
    options_digest = hashlib.sha256(canonical_options).digest()
    doc_digest = hashlib.sha256(canonical_doc).digest()
    return hashlib.sha256(options_digest + doc_digest).digest()
```

### 2.2 Backward Compatibility
Verification services accept both `ecdsa-jcs-2019` (SHA-256) and `ecdsa-jcs-2019-keccak` (Keccak-256) to ensure credentials issued under earlier pilot iterations remain verifiable without migration friction.

---

## 3. Client-Side Signing & Institutional Custody Architecture

DecentralID enforces strict separation of duties and zero key custody:

```
+------------------------+          +-----------------------+          +---------------------+
| DecentralID Backend    |          | Institutional Officer |          | Hardware Key /      |
| (API / DB)             |          | (DecentralID Portal)  |          | Web3 Wallet (Signer)|
+------------------------+          +-----------------------+          +---------------------+
           |                                   |                                  |
           | 1. GET /credentials/{id}/signing-payload                             |
           |<----------------------------------|                                  |
           |                                   |                                  |
           | 2. Returns digest & canonical payload                                |
           |---------------------------------->|                                  |
           |                                   | 3. Request signature on digest   |
           |                                   |--------------------------------->|
           |                                   |                                  |
           |                                   | 4. Returns 65-byte ECDSA signature|
           |                                   |<---------------------------------|
           | 5. POST /credentials/{id}/complete-signing                           |
           |    { signature, verificationMethod }                                 |
           |<----------------------------------|                                  |
           |                                   |                                  |
           | 6. Verifies recovered signer == authorized on-chain key              |
           |    Transitions status to ISSUED                                      |
           |---------------------------------->|                                  |
```

### Security Benefits:
- **Zero Key Exfiltration**: Private keys never touch DecentralID network boundaries, memory heaps, or log streams.
- **Auditable Hardware Attestation**: Signatures can be generated by YubiKey, AWS CloudHSM, or institutional Ledger hardware wallets.
- **Enforced Multi-Role Governance**: Credential preparation requires an authorized preparer; credential signing requires an authorized signer with verified on-chain authorization.

---

## 4. Cryptographic Selective Disclosure Mechanism

### 4.1 Merkle Claim Commitment Construction

Given a `credentialSubject` with claims $C = \{ (k_1, v_1), (k_2, v_2), \dots, (k_n, v_n) \}$:

1. **Per-Claim Salt Generation**:
   For each claim $(k_i, v_i)$, a high-entropy 256-bit random salt $s_i \leftarrow \{0,1\}^{256}$ is generated via CSPRNG (`os.urandom(32)`).
2. **Claim Commitment Calculation**:
   $$c_i = \text{SHA-256}(\text{Hex}(s_i) \parallel \text{canonical}(k_i) \parallel \text{canonical}(v_i))$$
3. **Sorted Root Commitment Derivation**:
   $$L = \text{sort}([c_1, c_2, \dots, c_n])$$
   $$\text{rootCommitment} = \text{SHA-256}(L_1 \parallel L_2 \parallel \dots \parallel L_n)$$

### 4.2 Verifiable Presentation Selective Disclosure

When presenting to a verifier requesting only attribute $k_j$:
1. The holder discloses:
   - Disclosed claims: $\{ (k_j, v_j) \}$
   - Disclosed salts: $\{ (k_j, s_j) \}$
   - Undisclosed commitments: $\{ c_i \mid i \neq j \}$
2. The verifier:
   - Computes $c_j = \text{SHA-256}(\text{Hex}(s_j) \parallel \text{canonical}(k_j) \parallel \text{canonical}(v_j))$.
   - Reassembles the full list of commitments $L' = \text{sort}(\{ c_j \} \cup \{ c_i \mid i \neq j \})$.
   - Calculates $\text{rootCommitment}' = \text{SHA-256}(L'_1 \parallel L'_2 \parallel \dots \parallel L'_n)$.
   - Verifies that $\text{rootCommitment}' == \text{credential.selectiveDisclosure.rootCommitment}$.
   - Verifies the credential's issuer proof over the credential containing `rootCommitment`.

### 4.3 Mathematical Privacy Guarantee
The adversary (verifier) learns strictly $(k_j, v_j)$. Since $s_i$ for $i \neq j$ is never disclosed and SHA-256 is collision-resistant and preimage-resistant under the Random Oracle Model (ROM), the verifier cannot infer any undisclosed claim or value.

---

## 5. Security & Verification Audit Checklist

| Security Property | Implementation Mechanism | Verification Status |
|---|---|---|
| Nonce/Salt Entropy | `secrets.token_hex(32)` (256-bit CSPRNG) | PASS |
| Canonicalization | RFC 8785 JSON Canonicalization Scheme | PASS |
| Digest Standard | Double-SHA-256 per W3C ECDSA JCS 2019 | PASS |
| Legacy Interoperability | Keccak-256 fallback verification | PASS |
| Replay Protection | On-chain commitment uniqueness check | PASS |
| Tamper Resistance | Any single-bit change invalidates proof | PASS |
