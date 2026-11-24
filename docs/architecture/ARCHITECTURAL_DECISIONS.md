# Architectural Decision Records (ADRs)

**Project:** DecentralID  
**Date:** November 2026  

---

## ADR-001: Separation of Blockchain Concerns into Three Registries
- **Status:** Accepted
- **Context:** The legacy prototype combined identity metadata, reputation scoring, endorsements, and issuer checks in a single monolithic contract (`IdentityReputation.sol`). This made upgrading, auditing, and gas optimization difficult.
- **Decision:** Split on-chain logic into three modular OpenZeppelin-based contracts:
  1. `IssuerRegistry.sol`: Handles institutional verification, roles, and authorized public signing keys.
  2. `CredentialRegistry.sol`: Anchors privacy-preserving credential commitments.
  3. `CredentialStatusRegistry.sol`: Manages credential lifecycle states (`Active`, `Suspended`, `Revoked`).
- **Consequences:** Modular verification, independent auditability, and gas efficiency.

---

## ADR-002: High-Entropy Salted Commitments for Privacy Preservation
- **Status:** Accepted
- **Context:** Storing personal data or plain hashes on public blockchains violates privacy regulations (GDPR/FERPA) and exposes users to correlation attacks.
- **Decision:** Mandate that all credential commitments registered on-chain take the form:
  $$\text{commitment} = \text{keccak256}(\text{canonicalJSON}(S) \mathbin{\Vert} \text{salt})$$
  where $\text{salt}$ is a 32-byte cryptographically secure random value.
- **Consequences:** Verifiers possessing the credential and salt can prove on-chain existence, while observers of the blockchain learn nothing about personal data.

---

## ADR-003: EIP-4361 Sign-In with Ethereum (SIWE) for Authentication
- **Status:** Accepted
- **Context:** Relying solely on connected wallet addresses in the client frontend allows trivial spoofing.
- **Decision:** Implement EIP-4361 challenge-response authentication. The backend generates a short-lived nonce (5-minute TTL); the user signs the SIWE challenge; the backend verifies the signature and issues an HTTP-only secure cookie session.
- **Consequences:** Eliminates client-side address spoofing and ensures cryptographic proof of wallet ownership.

---

## ADR-004: Modular Monolith Backend with FastAPI and PostgreSQL
- **Status:** Accepted
- **Context:** The prototype had no backend, forcing client-side API credentials and untrusted state.
- **Decision:** Introduce a FastAPI (Python 3.11+) backend with PostgreSQL 16 and SQLAlchemy 2.0 async ORM. Structure it as a modular monolith with clear domain boundaries (`authentication`, `organizations`, `credentials`, `verification`, `blockchain`).
- **Consequences:** Centralized secret management, strict tenant isolation, asynchronous I/O, and automated OpenAPI documentation.

---

## ADR-005: Modernized React 18 + TypeScript + Tailwind Frontend
- **Status:** Accepted
- **Context:** The original frontend was a 2,312-line monolithic JavaScript file (`App.jsx`) with no type safety and hardcoded values.
- **Decision:** Migrate to a structured TypeScript architecture with Vite, Tailwind CSS, TanStack Query, and ethers.js v6, consuming configuration dynamically from the backend.
- **Consequences:** Type safety, maintainability, modular component hierarchy, and zero hardcoded secrets.
