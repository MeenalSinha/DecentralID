# Repository Structure Specification

**Project:** DecentralID  
**Date:** November 2026  
**Status:** Phase 2 Modular Monolith Baseline  

---

```text
DecentralID/
├── backend/                               # FastAPI Modular Monolith Gateway
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── health.py              # Diagnostic liveness/readiness probes
│   │   │       └── blockchain.py          # Public blockchain configuration
│   │   ├── core/
│   │   │   ├── config.py                  # Pydantic v2 application settings
│   │   │   ├── constants.py               # Enums for roles, statuses, and tiers
│   │   │   ├── database.py                # Async SQLAlchemy engine & session factory
│   │   │   ├── exceptions.py              # Centralized application exceptions
│   │   │   └── logging.py                 # Structured JSON logger with correlation IDs
│   │   ├── middleware/
│   │   │   ├── correlation.py             # X-Correlation-ID & timing middleware
│   │   │   └── exceptions.py              # Global exception interceptor
│   │   ├── models/
│   │   │   ├── base.py                    # TimestampMixin and Base declarative model
│   │   │   ├── user.py                    # User & Wallet entities
│   │   │   ├── organization.py            # Organization, Membership, SigningKey entities
│   │   │   ├── credential.py              # Credential commitment entity
│   │   │   └── session.py                 # Session & AuthChallenge entities
│   │   ├── schemas/
│   │   │   ├── health.py                  # Health check request/response schemas
│   │   │   └── blockchain.py              # Blockchain config response schemas
│   │   └── main.py                        # FastAPI application instance & lifespan
│   ├── tests/
│   │   ├── conftest.py                    # Async SQLite test engine fixtures
│   │   ├── test_health.py                 # Liveness & readiness probe tests
│   │   └── test_blockchain_config.py      # Dynamic config endpoint tests
│   ├── Dockerfile                         # Container build for backend
│   └── requirements.txt                   # Pinned backend dependencies
│
├── frontend/                              # Modernized React + TypeScript + Vite
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   │   ├── config/api.ts              # Centralized API fetch helper
│   │   │   ├── providers/QueryProvider.tsx # TanStack Query Provider
│   │   │   └── router/index.tsx           # React Router v6 route configuration
│   │   ├── components/
│   │   │   └── layout/
│   │   │       ├── Header.tsx             # Responsive global navigation
│   │   │       ├── Footer.tsx             # Standard footer
│   │   │       └── AppLayout.tsx          # Master layout with wallet state
│   │   ├── features/
│   │   │   ├── authentication/
│   │   │   │   └── hooks/useWallet.ts     # Ethers.js v6 wallet state management
│   │   │   ├── blockchain/
│   │   │   │   └── services/              # Blockchain config service
│   │   │   ├── issuers/
│   │   │   │   └── components/IssuerView.tsx # Institutional portal view
│   │   │   ├── verification/
│   │   │   │   └── components/VerificationView.tsx # Verification portal view
│   │   │   └── wallet/
│   │   │       └── components/WalletView.tsx # Holder wallet credential view
│   │   ├── types/
│   │   │   ├── auth.ts                    # User, Session & Challenge types
│   │   │   └── credential.ts              # Credential & Blockchain types
│   │   ├── index.css                      # Tailwind directives
│   │   ├── main.tsx                       # React application entry point
│   │   └── vite-env.d.ts                  # Vite client type references
│   ├── Dockerfile                         # Multi-stage Nginx build for frontend
│   ├── nginx.conf                         # Reverse proxy config for container
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.js
│
├── contracts/                             # Smart Contracts
│   └── IdentityReputation.sol             # Preserved legacy baseline
│
├── test/                                  # Smart Contract Tests
│   └── IdentityReputation.test.js         # 14 baseline tests & defect proofs
│
├── docs/                                  # Project Documentation
│   ├── audit/                             # Phase 0 audit reports
│   ├── product/                           # Phase 1 product specs
│   ├── architecture/                      # System architecture & ADRs
│   ├── deployment/                        # Local & cloud deployment guides
│   └── progress/                          # Cross-phase milestone acceptance reports
│
├── .github/
│   └── workflows/
│       └── ci.yml                         # Automated Continuous Integration
│
├── docker-compose.yml                     # Local orchestration (Postgres + Backend + Frontend)
├── hardhat.config.js
└── package.json
```
