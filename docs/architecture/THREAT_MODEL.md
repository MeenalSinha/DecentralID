# Threat Modeling & Security Analysis

**Project:** DecentralID  
**Date:** November 2026  
**Framework:** STRIDE Threat Analysis  

---

## 1. STRIDE Threat Matrix

| Threat Category | Threat Description | Attack Vector | Mitigation Strategy |
|---|---|---|---|
| **Spoofing** | Malicious actor impersonates an accredited university or authorized issuer. | Submitting credentials signed by an arbitrary key claiming to be from "Harvard University". | Trust is rooted strictly in on-chain `IssuerRegistry`. Verifier checks that the signing key is registered under the authorized institution's on-chain profile. |
| **Tampering** | Recipient modifies credential fields (e.g., changes GPA from 2.5 to 3.9). | Altering the JSON subject payload. | Cryptographic signature over EIP-712 typed structure invalidates immediately upon single-byte modification; recomputed commitment $C'$ will not match on-chain commitment $C$. |
| **Repudiation** | Institution issues a fraudulent degree and denies having issued it. | Issuing without audit trails. | Non-repudiable ECDSA signature from the institution's authorized operational key, accompanied by on-chain timestamped registration event. |
| **Information Disclosure** | Public exposure of personal academic or health records on-chain. | Inspecting public blockchain blocks or IPFS gateways. | **Zero on-chain PII.** Data is committed as high-entropy salted hashes ($C = \text{keccak256}(S \parallel R)$). Unsalted hashes are strictly prohibited. |
| **Denial of Service** | Gas exhaustion or API resource exhaustion. | Spreading thousands of fake endorsements or spamming issuance endpoints. | Deprecation of open endorsement minting. Rate-limiting API endpoints, pagination, and bounded fixed-size contract storage (`bytes32`). |
| **Elevation of Privilege** | Institutional clerk grants themselves global platform administrative permissions. | Manipulating client request parameters (`org_id`, `role`). | Backend derives role permissions and tenant scope exclusively from verified session tokens in PostgreSQL. Client-supplied IDs are ignored. |

---

## 2. Specific Attack Scenarios & Mitigations

### 2.1 Replay Attack on Wallet Authentication
- **Attack:** Attacker intercepts a signed SIWE message from a user and resubmits it to establish an unauthorized session.
- **Mitigation:**
  - Nonces are generated server-side with cryptographic entropy.
  - Nonces are stored with a 5-minute time-to-live (TTL).
  - Nonces are consumed atomically upon first presentation (`used = True`). Subsequent submissions of the same nonce immediately fail.

### 2.2 Rainbow Table Attack on Low-Entropy On-Chain Commitments
- **Attack:** Attacker notices an on-chain commitment for a degree from a small cohort. Knowing the possible degree names and years, the attacker precomputes hashes to identify the student.
- **Mitigation:**
  - Every credential subject is concatenated with a 256-bit cryptographically secure pseudorandom salt before hashing: $\text{keccak256}(S \parallel R)$.
  - A 256-bit salt renders dictionary and rainbow table attacks mathematically infeasible.

### 2.3 Compromised Institutional Operational Signing Key
- **Attack:** An institutional operational key is leaked or compromised.
- **Mitigation:**
  - Institutional Admin immediately invokes `IssuerRegistry.revokeSigningKey(keyAddress)`.
  - The key is deactivated on-chain in real-time.
  - Any subsequent credential presented with a signature from that key fails the `isSigningKeyValid` check, neutralizing the rogue key.
