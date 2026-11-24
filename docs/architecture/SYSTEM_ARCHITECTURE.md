# System Architecture Specification

**Project:** DecentralID  
**Date:** November 2026  
**Target:** Phases 0–4 Foundation (Production-Oriented)  

---

## 1. High-Level Architecture Overview

DecentralID adopts a **modular full-stack architecture** with strict boundary separation between client presentation, authenticated API gateway, persistence, and decentralized blockchain registries:

```mermaid
graph TB
    subgraph ClientLayer["Client Layer (Frontend)"]
        HolderUI["Holder Portal / Wallet"]
        IssuerUI["Institutional Issuer Portal"]
        VerifyUI["Independent Verifier Portal"]
        Web3Provider["EVM Wallet / Signer (MetaMask)"]
    end

    subgraph APILayer["Backend Gateway (FastAPI)"]
        AuthMiddleware["Auth & Session Middleware (SIWE)"]
        TenantGuard["Tenant Isolation & RBAC Guard"]
        APIRouter["Versioned API (/api/v1)"]
        Services["Domain Services (Issuance, Verification, Org)"]
    end

    subgraph DataLayer["Persistence Layer"]
        PostgresDB[(PostgreSQL 16)]
        Alembic["Alembic Migrations"]
    end

    subgraph BlockchainLayer["Blockchain Trust Layer (EVM)"]
        IssuerReg["IssuerRegistry.sol (PKI & Roles)"]
        CredReg["CredentialRegistry.sol (Commitments)"]
        StatusReg["CredentialStatusRegistry.sol (Lifecycle)"]
    end

    HolderUI -->|HTTPS / REST| AuthMiddleware
    IssuerUI -->|HTTPS / REST| AuthMiddleware
    VerifyUI -->|HTTPS / REST| APIRouter
    Web3Provider -->|EIP-712 Signatures| HolderUI
    Web3Provider -->|EIP-712 Signatures| IssuerUI

    AuthMiddleware --> TenantGuard
    TenantGuard --> APIRouter
    APIRouter --> Services

    Services -->|SQLAlchemy Async ORM| PostgresDB
    Services -->|JSON-RPC via Provider| BlockchainLayer
    VerifyUI -.->|Direct RPC Read (Optional Offline)| BlockchainLayer
```

---

## 2. Layer Responsibilities & Isolation Boundaries

### 2.1 Frontend Client Layer
- **Tech Stack:** React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router v6, ethers.js v6.
- **Responsibilities:**
  - Wallet connection via standard EVM providers.
  - Interactive user journeys for Holders, Institutional Operators, and Verifiers.
  - State management, form validation (Zod + React Hook Form), and accessible UI feedback.
  - Consuming non-sensitive public configuration from backend (`/api/v1/blockchain/config`).
- **Security Boundary:** Browser client is treated as an untrusted environment. Zero secrets or sensitive signing keys are ever stored client-side.

### 2.2 Backend Gateway Layer
- **Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (asyncio), Uvicorn.
- **Responsibilities:**
  - Wallet challenge generation, EIP-4361 signature verification, and secure session management.
  - Enforcing strict tenant isolation based on authenticated session context.
  - High-entropy salt generation and privacy-preserving credential commitment calculation.
  - Serving OpenAPI / Swagger documentation and health monitoring (`/health/live`, `/health/ready`).

### 2.3 Persistence Layer
- **Tech Stack:** PostgreSQL 16, Alembic database migration framework.
- **Responsibilities:**
  - Relational storage for users, wallets, organizations, memberships, schemas, and credential records.
  - Foreign key constraints, unique indexes, and tenant-scoped queries.
  - Immutable audit logging for security-sensitive operations.

### 2.4 Blockchain Trust Layer
- **Tech Stack:** Solidity 0.8.20+, OpenZeppelin Contracts v5, Hardhat.
- **Responsibilities:**
  - `IssuerRegistry`: Authoritative on-chain registry of accredited institutions and authorized public signing keys.
  - `CredentialRegistry`: Tamper-proof log of privacy commitments associating credentials with authorized issuers.
  - `CredentialStatusRegistry`: Non-repudiable credential lifecycle state machine (`Active`, `Suspended`, `Revoked`).
