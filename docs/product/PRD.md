# Product Requirements Document (PRD) — DecentralID

**Product Name:** DecentralID  
**Initiative:** BUILD 2036 — Frontier 03: Digital Infrastructure  
**Phases Implemented:** Phases 0–18 (Complete Digital Trust Infrastructure)  
**Version:** 3.0.0-ENTERPRISE  
**Status:** Approved & Verified Architecture  

---

## 1. Executive Summary & Vision

DecentralID transforms the paradigm of educational and professional qualification management from fragmented, paper-heavy, and easily forged credentials into a privacy-preserving, decentralized digital trust infrastructure for Digital India.

Rather than relying on unverified PDF resumes, easily manipulated LinkedIn profiles, or centralized databases vulnerable to single points of failure, DecentralID provides:
- **Institutions:** A cryptographically sound issuance portal with multi-party authorization, verifiable key management, and instant lifecycle control (issuance, suspension, revocation).
- **Holders (Students/Professionals):** Self-sovereign control over digital credentials stored locally and privately in an installable PWA wallet, with selective disclosure and offline presentation capabilities.
- **Verifiers (Employers/Universities):** Independent, sub-second verification of credential authenticity, issuer accreditation, and revocation status without contacting the issuing institution or exposing private data.
- **Developers & Enterprises:** Universal DID resolution, TypeScript SDK, webhooks, LMS/SIS/HRIS connectors, and bulk migration tools.

---

## 2. Integrated Product Modules (Phases 0–18)

| Module | Scope | Phase | Purpose |
|---|---|---|---|
| **DecentralID Trust** | Smart Contracts & PKI | Phase 4 | On-chain authoritative registries: `IssuerRegistry`, `CredentialRegistry`, `CredentialStatusRegistry`. |
| **DecentralID Engine** | W3C Data Integrity | Phase 5 & 11 | RFC 8785 JSON Canonicalization Scheme, `ecdsa-jcs-2019` double-SHA256 proofs, zero key custody. |
| **DecentralID Issuer** | Institutional Portal | Phase 6 | Multi-tenant organization dashboard for preparing, signing, and managing credential lifecycles with separation of duties. |
| **DecentralID Wallet** | Personal Credential Portal | Phase 7 & 16 | Self-sovereign PWA wallet with client-side encrypted local vault (`PBKDF2 + AES-GCM`) and offline QR presentations. |
| **DecentralID Verify** | Independent Verification | Phase 8 | Standalone cryptographic verification portal checking on-chain commitments and revocation status. |
| **DecentralID Lifecycle** | W3C Bitstring Status Lists | Phase 9 | Dynamic multibase bitstrings, bitwise operations, suspension, and irreversible revocation. |
| **DecentralID Intelligence**| AI Extraction & Heuristics | Phase 10 | Pure-Python PDF/image stream extraction, magic-byte validation, regex heuristic parsing, and anomaly detection. |
| **DecentralID Cryptography**| Selective Disclosure | Phase 11 | Salted Merkle claim commitments enabling holders to disclose subsets of attributes while keeping unshared data blinded. |
| **DecentralID Network** | Developer Platform & SDK | Phase 12 | Encrypted IPFS storage, API keys with SHA-256 hashing, HMAC-SHA256 signed webhooks, official `@decentralid/sdk`. |
| **DecentralID Operations**| Enterprise SRE & Metrics | Phase 13 | Real-time database analytics, deep liveness/readiness probes, production security hardening. |
| **DecentralID Interop** | Standards & Portability | Phase 14 | Universal DID Resolver (`did:pkh`, `did:key`, `did:web`), W3C v1/v2 export, foreign credential import with strict non-reissuance. |
| **DecentralID Governance**| Institutional Accreditation | Phase 15 | Multi-stage accreditation review, separation of duties (Reviewer != Approver), trust policy engine, public trust directory. |
| **DecentralID Mobile** | Offline Verification | Phase 16 | Offline verification with the **Critical Freshness Rule**: stale snapshots evaluate strictly to `INDETERMINATE`. |
| **DecentralID Ecosystem** | Enterprise Connectors | Phase 17 | Canvas/Moodle LMS adapter, Banner SIS ingestion, Workday HRIS verifier with data minimization, bulk CSV/JSON migration. |
| **DecentralID Scale** | Pilot & Release Assurance | Phase 18 | Performance load benchmarks (70 ops/sec signing, 92 ops/sec verify), failover resilience, incident response runbooks. |
