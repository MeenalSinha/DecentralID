# 🔐 DecentralID — Digital Trust & Verifiable Credential Infrastructure

**Initiative:** BUILD 2036 — Frontier 03: Digital Infrastructure  
**Phases Implemented:** Phases 0–4 (Audit, System Design, Full-Stack Foundation, Auth & RBAC, On-Chain Registries)  
**Standard Compliance:** W3C Verifiable Credentials Data Model 2.0 • W3C Data Integrity 1.0 • EIP-4361 SIWE • EIP-712  

---

## 🌟 Executive Overview

DecentralID is a privacy-preserving, decentralized digital trust infrastructure connecting educational institutions, licensing organizations, students, professionals, employers, and independent verifiers.

Rather than relying on easily faked PDF certificates, gameable reputation points, or centralized transcript silos, DecentralID anchors trust in **cryptographic signatures from accredited institutions registered on Ethereum/EVM smart contracts**, keeping personal data completely off-chain through high-entropy salted commitments.

---

## 🏗️ Six Core Product Modules

| Module | Purpose | Status |
|---|---|---|
| **DecentralID Trust** | Authoritative on-chain registries: `IssuerRegistry`, `CredentialRegistry`, `CredentialStatusRegistry`. | **Implemented (Phase 4)** |
| **DecentralID Issuer** | Multi-tenant institutional portal for managing signing keys and issuing credentials. | **Foundation Active (Phases 2–3)** |
| **DecentralID Wallet** | Personal credential wallet for students and professionals to hold and selectively disclose qualifications. | **Foundation Active (Phases 2–3)** |
| **DecentralID Verify** | Independent verification portal checking cryptographic proofs and on-chain revocation status. | **Foundation Active (Phases 2–3)** |
| **DecentralID Intelligence**| AI-assisted document extraction and anomaly detection. | *Planned (Phase 10)* |
| **DecentralID Network** | Developer REST/GraphQL APIs and webhooks for external HRIS/ATS systems. | *Planned (Phase 9)* |

---

## 🛡️ Core Engineering & Security Principles

1. **Nothing Hardcoded:** Zero private keys, API secrets, or fixed contract addresses in client source code. Dynamic configuration is fetched at runtime from `/api/v1/blockchain/config`.
2. **Zero Fake Functionality:** No fake IPFS hashes, simulated signatures, or mocked successes. Operations succeed or fail deterministically.
3. **Privacy First (Zero On-Chain PII):** No names, dates of birth, or marks on-chain. On-chain commitments use 256-bit salted hashes: $C = \text{keccak256}(S \parallel \text{salt})$.
4. **EIP-4361 SIWE Authentication:** Cryptographic wallet signature verification with atomic nonce consumption preventing replay attacks.
5. **Strict Multi-Tenant Isolation:** Institutional queries and actions are strictly scoped to verified memberships in PostgreSQL.
6. **Irreversible Revocation State Machine:** Credentials and institutional accreditations marked as `Revoked` can never be reactivated.

---

## 🛠️ Technology Stack

- **Smart Contracts:** Solidity `^0.8.20`, OpenZeppelin Contracts v5, Hardhat.
- **Backend Gateway:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (asyncio), Uvicorn.
- **Persistence:** PostgreSQL 16 (production) / aiosqlite (isolated testing).
- **Frontend Portal:** React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router v6, ethers.js v6.
- **Containerization & CI:** Docker, Docker Compose, GitHub Actions.

---

## 🚀 Quickstart & Local Development

### 1. Smart Contracts
```bash
# Install dependencies
npm install

# Compile contracts (dual-compiler 0.8.20 & 0.8.19)
npx hardhat compile

# Run Hardhat test suite (39 tests: unit, integration, invariant)
npx hardhat test

# Deploy registries locally
npx hardhat run scripts/deploy/deploy_registries.js --network hardhat
```

### 2. Backend Gateway
```bash
# Set up Python virtual environment
python -m venv backend/venv
.\backend\venv\Scripts\activate   # Windows
# source backend/venv/bin/activate # Linux/macOS

# Install dependencies
pip install -r backend/requirements.txt

# Run backend test suite (9 tests)
python -m pytest backend/tests

# Start development server
uvicorn backend.app.main:app --reload --port 8000
```
API Documentation live at `http://localhost:8000/docs`

### 3. Frontend Portal
```bash
cd frontend
npm install
npx tsc --noEmit
npm run dev
```
Portal live at `http://localhost:5173`

### 4. Docker Compose (Full Stack)
```bash
docker compose up --build
```

---

## 📚 Documentation Index

- **Phase 0 Audits:** [`docs/audit/`](docs/audit/)
  - [`INITIAL_AUDIT.md`](docs/audit/INITIAL_AUDIT.md)
  - [`SECURITY_AUDIT.md`](docs/audit/SECURITY_AUDIT.md)
  - [`BASELINE_TEST_REPORT.md`](docs/audit/BASELINE_TEST_REPORT.md)
- **Phase 1 System Design:** [`docs/product/`](docs/product/) & [`docs/architecture/`](docs/architecture/)
  - [`PRD.md`](docs/product/PRD.md)
  - [`SYSTEM_ARCHITECTURE.md`](docs/architecture/SYSTEM_ARCHITECTURE.md)
  - [`DATA_ARCHITECTURE.md`](docs/architecture/DATA_ARCHITECTURE.md)
  - [`SMART_CONTRACT_ARCHITECTURE.md`](docs/architecture/SMART_CONTRACT_ARCHITECTURE.md)
  - [`THREAT_MODEL.md`](docs/architecture/THREAT_MODEL.md)
- **Phase 2 & 3 Foundations:** [`docs/security/`](docs/security/)
  - [`AUTHENTICATION_DESIGN.md`](docs/security/AUTHENTICATION_DESIGN.md)
  - [`AUTHORIZATION_MATRIX.md`](docs/security/AUTHORIZATION_MATRIX.md)
  - [`TENANT_ISOLATION.md`](docs/security/TENANT_ISOLATION.md)
- **Phase 4 Smart Contracts:** [`docs/smart-contracts/`](docs/smart-contracts/)
  - [`CONTRACT_DESIGN.md`](docs/smart-contracts/CONTRACT_DESIGN.md)
  - [`ISSUER_REGISTRY.md`](docs/smart-contracts/ISSUER_REGISTRY.md)
  - [`CREDENTIAL_REGISTRY.md`](docs/smart-contracts/CREDENTIAL_REGISTRY.md)
  - [`CREDENTIAL_STATUS_REGISTRY.md`](docs/smart-contracts/CREDENTIAL_STATUS_REGISTRY.md)
  - [`GAS_REPORT.md`](docs/smart-contracts/GAS_REPORT.md)
- **Milestone Progress Reports:** [`docs/progress/`](docs/progress/)
  - [`PHASE_0_REPORT.md`](docs/progress/PHASE_0_REPORT.md)
  - [`PHASE_1_REPORT.md`](docs/progress/PHASE_1_REPORT.md)
  - [`PHASE_2_REPORT.md`](docs/progress/PHASE_2_REPORT.md)
  - [`PHASE_3_REPORT.md`](docs/progress/PHASE_3_REPORT.md)
  - [`PHASE_4_REPORT.md`](docs/progress/PHASE_4_REPORT.md)
