# 🔐 DecentralID — Digital Trust & Verifiable Credential Infrastructure

**Initiative:** BUILD 2036 — Frontier 03: Digital Infrastructure  
**Phases Implemented:** **Phases 0–18 (Complete Digital Trust Infrastructure)**  
**Standard Compliance:** W3C Verifiable Credentials 2.0/1.1 • W3C Data Integrity 1.0 (`ecdsa-jcs-2019`) • RFC 8785 JCS • W3C DID Core & Resolution (`did:pkh`, `did:key`, `did:web`) • W3C Bitstring Status List v1.0 • EIP-4361 SIWE  

---

## 🌟 Executive Overview

DecentralID is an open, privacy-preserving, decentralized digital trust infrastructure connecting educational institutions, licensing bodies, students, professionals, employers, and independent verifiers across Digital India.

Rather than relying on easily faked PDF certificates, gameable reputation points, or centralized transcript silos, DecentralID anchors trust in **cryptographic signatures from accredited institutions registered on Ethereum/Polygon smart contracts**, keeping personal data completely off-chain through high-entropy salted commitments, encrypted content-addressed storage (AES-256-GCM + IPFS), client-side encrypted vaults, and privacy-preserving selective disclosure.

---

## 🏗️ Core Architectural Modules (Phases 0–18)

| Module | Scope & Phase | Status | Key Capabilities |
|---|---|---|---|
| **DecentralID Trust** | Smart Contracts (Phase 4) | **Production-Ready** | `IssuerRegistry`, `CredentialRegistry`, `CredentialStatusRegistry` on EVM. Irreversible revocation state machine. |
| **DecentralID Engine** | W3C Data Integrity (Phase 5 & 11) | **Production-Ready** | RFC 8785 JSON Canonicalization Scheme, `ecdsa-jcs-2019` double-SHA256 proofs, zero key custody. |
| **DecentralID Issuer** | Institutional Portal (Phase 6) | **Production-Ready** | Key delegation, separation of duties across preparation & approval, tenant isolation. |
| **DecentralID Wallet** | Personal Wallet & PWA (Phase 7 & 16) | **Production-Ready** | Installable mobile PWA, Web Crypto encrypted IndexedDB vault (`PBKDF2 + AES-GCM`), encrypted backup/restore. |
| **DecentralID Verify** | Independent Verification (Phase 8) | **Production-Ready** | Standalone cryptographic verification without session requirements. |
| **DecentralID Lifecycle** | W3C Bitstring Status (Phase 9) | **Production-Ready** | Dynamic status lists, compressed bitstrings, real-time revocation & suspension tracking. |
| **DecentralID Intelligence**| Document Ingestion & AI (Phase 10) | **Production-Ready** | Pure-Python PDF/image stream extraction, magic-byte validation, heuristic regex parsing, anomaly detection. |
| **DecentralID Cryptography**| Selective Disclosure (Phase 11) | **Production-Ready** | Salted Merkle claim commitments; holders selectively disclose attributes while keeping unshared data blinded. |
| **DecentralID Network** | Developer Platform & SDK (Phase 12) | **Production-Ready** | Encrypted IPFS storage, API keys with SHA-256 hashing, HMAC-SHA256 signed webhooks, official `@decentralid/sdk`. |
| **DecentralID Operations**| Enterprise Reliability (Phase 13) | **Production-Ready** | Dynamic database analytics, deep `/health/live` & `/health/ready` probes, production security validator. |
| **DecentralID Interop** | Standards & Portability (Phase 14) | **Production-Ready** | Universal DID Resolver (`did:pkh`, `did:key`, `did:web`), W3C v1/v2 export, foreign credential import (strict non-reissuance). |
| **DecentralID Governance**| Institutional Accreditation (Phase 15)| **Production-Ready** | Multi-level accreditation review, separation of duties (Reviewer != Approver), trust policy engine, public trust directory. |
| **DecentralID Mobile** | Offline Verification (Phase 16) | **Production-Ready** | Offline verification with the **Critical Freshness Rule**: stale snapshots evaluate strictly to `INDETERMINATE`. |
| **DecentralID Ecosystem** | Integrations & Connectors (Phase 17) | **Production-Ready** | Canvas/Moodle LMS adapter, Banner SIS ingestion, Workday HRIS verifier with data minimization, bulk CSV/JSON migration. |
| **DecentralID Scale** | Pilot & Release Assurance (Phase 18) | **Production-Ready** | Performance load benchmarks (70 ops/sec signing, 92 ops/sec verify), failover resilience, incident response runbooks. |

---

## 🛡️ Core Engineering & Security Principles

1. **Zero Hardcoded Data or Secrets:** No hardcoded credentials, institutions, private keys, or mock blockchain transaction hashes. All operations are dynamically validated and cryptographically verified.
2. **Zero Plaintext PII on Blockchains or Public IPFS:** Only 256-bit salted commitments are anchored on-chain. Off-chain payloads are encrypted with AES-256-GCM before distribution.
3. **The Critical Freshness Rule:** Offline verification cannot guarantee non-revocation after the last sync. Snapshots exceeding the freshness window strictly return `INDETERMINATE`.
4. **Strict Separation of Duties:** Individuals cannot approve their own credential preparation drafts or institutional accreditation applications.
5. **EIP-4361 SIWE & Client-Side Zero Key Custody:** Private signing keys remain exclusively in client-side Web3 hardware wallets or institutional KMS. The backend never accepts raw private keys.

---

## 🧪 Quality Gates & Verification Evidence

- **Smart Contracts:** 43/43 Hardhat tests passing (`npx hardhat test`)
- **Backend Services:** 48/48 Pytest tests passing (`pytest backend/tests`)
- **Frontend Quality:** 0 TypeScript errors (`tsc --noEmit`), 0 ESLint warnings (`npm run lint`), clean Vite build (`npm run build`)
- **TypeScript SDK:** Clean compilation (`@decentralid/sdk`)
- **Database Migrations:** Clean linear Alembic migration graph to head `a38bc19d45e2`
- **End-to-End Integration:** Full 34-step automated lifecycle verified in `test_e2e_lifecycle.py`

---

## 🚀 Quickstart & Local Execution

### 1. Smart Contracts
```bash
# Install dependencies
npm install

# Compile contracts
npx hardhat compile

# Run tests
npx hardhat test
```

### 2. Backend Services
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Run all 48 tests across Phases 0–18
PYTHONPATH=. pytest backend/tests -v

# Start FastAPI server
uvicorn backend.app.main:app --reload --port 8000
```

### 3. Frontend Web Application & PWA
```bash
cd frontend
npm install
npm run typecheck
npm run lint
npm run build
npm run dev
```

### 4. TypeScript SDK
```bash
cd sdk/typescript
npm install
npm run build
```
