# DecentralID Holder Wallet Architecture & Guide

## 1. Executive Summary

The **DecentralID Holder Wallet** is a self-sovereign digital credential vault designed for students, graduates, and professionals. It adheres to the W3C Verifiable Credentials Data Model 2.0 and W3C Data Integrity 1.0, enabling users to receive, hold, selectively disclose, and share their qualifications without sacrificing personal privacy or exposing raw PII.

---

## 2. Core Architectural Pillars

### 2.1 Self-Sovereign Identity DID
Every credential in the holder's wallet is bound to their decentralized identifier using the `did:pkh` method:
$$\text{did:pkh:eip155:}\{\text{chainId}\}\text{:}\{\text{recipient\_address}\}$$
This eliminates dependence on centralized identity providers or proprietary account silos.

### 2.2 Client-Side Encrypted Vault Backup
To ensure privacy and resilience against data loss or device migration:
- **Encryption Algorithm:** AES-256-GCM.
- **Key Derivation Function:** PBKDF2 with 100,000 iterations of SHA-256 and a cryptographically secure 16-byte random salt.
- **Zero-Knowledge Architecture:** The user's master password is used strictly inside the browser via the W3C Web Crypto API (`window.crypto.subtle`). It is never transmitted to the server or stored in cookies/localStorage.

### 2.3 Selective Disclosure & Verifiable Presentations
Holders frequently need to prove specific qualifications (e.g. holding a degree from an accredited institution) without disclosing sensitive personal attributes (such as GPA, student registration numbers, or caste/demographic data).

The Holder Wallet provides a granular **Claims Disclosure Matrix**:
1. The holder selects the exact attributes to share.
2. Unselected attributes are masked.
3. A W3C Verifiable Presentation (VP) 2.0 document is constructed containing the original commitment $C = \text{keccak256}(\text{canonicalSubject} \parallel R)$.
4. An opaque high-entropy presentation token (`pr_<base64url>`) is generated with a configurable expiration window (e.g., 24 hours) and rate-limiting limits.

### 2.4 QR Code Verification Without PII
Unlike naive systems that encode raw JSON or PII inside QR codes, DecentralID encodes only an opaque reference URI:
```
https://app.decentralid.org/verify?token=pr_k9f8d...
```
Verifiers can resolve the presentation through authorized endpoints, preventing shoulder surfing, optical scanning interception, and persistent physical tracking.

---

## 3. API Specification

| Endpoint | Method | Authorization | Description |
|---|---|---|---|
| `/api/v1/credentials/holder/{wallet_address}` | GET | Session / Bearer | Retrieves all credentials issued to the wallet with decrypted claims. |
| `/api/v1/credentials/presentations` | POST | Session / Bearer | Generates a W3C Verifiable Presentation with selective disclosure. |
| `/api/v1/credentials/presentations/{token}` | GET | Public | Resolves an opaque presentation token for verifiers. |

---

## 4. Security & Compliance Measures

1. **Strict Ownership Check:** Holders can only query credentials matching their authenticated wallet address (HTTP 403 otherwise).
2. **Pre-Display Verification:** Holders can run real-time verification of cryptographic signatures and commitments before presenting credentials.
3. **Auditability:** Verifiable presentations track access counts and strictly enforce token expiration.
