# Non-Functional Requirements Specification

**Project:** DecentralID  
**Date:** November 2026  

---

## 1. Security Requirements (NFR-SEC)
- **NFR-SEC-01 (Zero Hardcoded Secrets):** No private keys, database passwords, API tokens, or secrets shall ever exist in source code or client distributions.
- **NFR-SEC-02 (No Client-Side Authority):** Client applications shall never be trusted for identity claims, roles, or verification states. All state changes require authenticated, server-side and/or on-chain validation.
- **NFR-SEC-03 (Defense in Depth):** All API inputs must be validated with strict Pydantic schemas. Unrecognized fields must be rejected (`extra = "forbid"`).
- **NFR-SEC-04 (Cryptographic Standards):** Signatures must utilize industry-standard cryptographic algorithms: ECDSA with `secp256k1` (EIP-712 / EIP-191) for EVM compatibility.
- **NFR-SEC-05 (Secret Scanning & Auditing):** CI/CD pipelines must include automated static analysis and secret detection to prevent accidental credential leakage.

---

## 2. Privacy & Data Protection (NFR-PRIV)
- **NFR-PRIV-01 (No On-Chain PII):** Personally Identifiable Information (names, dates of birth, emails, grades, student IDs) must NEVER be written to public blockchains or unencrypted public storage.
- **NFR-PRIV-02 (High-Entropy Commitments):** On-chain commitments must include a 256-bit cryptographically secure random salt to prevent rainbow table or dictionary attacks against low-entropy data fields.
- **NFR-PRIV-03 (Data Minimization):** Verification endpoints and audit records shall log only cryptographic hashes and identifier references, not sensitive subject metadata.

---

## 3. Reliability & Availability (NFR-REL)
- **NFR-REL-01 (Deterministic Failure):** Failed operations must fail explicitly with structured error messages. Silent fallbacks, fake hashes, or fabricated responses are strictly prohibited.
- **NFR-REL-02 (Idempotency):** Critical write operations (credential registration, status updates) must support idempotency keys to prevent duplicate actions under network retry conditions.
- **NFR-REL-03 (Database Resilience):** Connection pooling must be configured with sensible timeouts and automatic reconnection. Health checks must probe actual database responsiveness (`SELECT 1`).

---

## 4. Performance & Scalability (NFR-PERF)
- **NFR-PERF-01 (Verification Latency):** Offline cryptographic verification must execute in under 50ms. Online verification (including RPC reads) must complete within 500ms under standard network conditions.
- **NFR-PERF-02 (Gas Optimization):** Smart contract registry designs must minimize storage operations. Status tracking must utilize compact representations (enums / future bitstrings) rather than arbitrary strings.
- **NFR-PERF-03 (Backend Concurrency):** FastAPI backend must utilize asynchronous I/O (`async`/`await`) for all database queries and external RPC calls.

---

## 5. Maintainability & Code Quality (NFR-MAINT)
- **NFR-MAINT-01 (Modular Monolith):** Backend and frontend codebases must maintain clear boundary separation between layers (api, core, models, schemas, repositories, services).
- **NFR-MAINT-02 (100% Type Safety):** Frontend must enforce TypeScript across all components, hooks, and services. Backend must enforce Python type annotations and strict validation.
- **NFR-MAINT-03 (Automated Test Coverage):** Unit and integration tests must validate all authentication, authorization, registry access control, and state machine transitions.
