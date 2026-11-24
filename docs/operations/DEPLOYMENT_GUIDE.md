# DecentralID Production Deployment & Operations Guide

**System:** DecentralID — Verifiable Digital Trust Infrastructure for Digital India  
**Version:** 2.0.0 (Phases 0–13 Complete)  
**Classification:** Enterprise Production Operations  

---

## 1. System Architecture & Topology

DecentralID operates as a distributed, high-security digital trust network consisting of four core service tiers:

1. **DecentralID Trust (Smart Contracts Tier)**:
   - EVM-compatible contracts: `IssuerRegistry`, `CredentialRegistry`, `CredentialStatusRegistry`.
   - Hardhat deployment artifacts, upgradeable proxy architectures, and cryptographic authorization registries.
2. **DecentralID Engine (Application & Backend Tier)**:
   - Python FastAPI asynchronous backend.
   - W3C VC 2.0 credential preparation, canonicalization (RFC 8785), double-SHA256 signing (`ecdsa-jcs-2019`).
   - Pure-Python stream document intake and heuristic OCR / AI extraction.
   - Salted Merkle claim commitments and selective disclosure engine.
   - External Developer APIs (`/api/v1/network`) and HMAC-SHA256 webhook dispatch engine.
3. **DecentralID Data Tier**:
   - PostgreSQL 15+ database with strict tenant boundary foreign keys.
   - AES-256-GCM encrypted content-addressed block storage (Pinata IPFS or local immutable cache).
4. **DecentralID Portal (Presentation Tier)**:
   - React 18, Vite, TypeScript, TailwindCSS single-page application.
   - Zero institutional private keys in browser state; client-side Web3 wallet and hardware attestation signing.

---

## 2. Production Environment Hardening

DecentralID enforces strict production security gates at startup:

### 2.1 Required Production Variables
```bash
# Environment
ENVIRONMENT=production
DEBUG=false
PROJECT_NAME="DecentralID Trust Infrastructure"

# Security Secrets (Must be >= 32 characters, random hex/base64, no dev placeholders)
SECRET_KEY=9f8e7d6c5b4a3928170f1e2d3c4b5a69788796a5b4c3d2e1f001122334455667
CREDENTIAL_ENCRYPTION_KEY=a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0
SECURE_COOKIE=true
SAME_SITE_COOKIE=strict

# Database
DATABASE_URL=postgresql+asyncpg://decentralid_app_user:StrongProdPassword!@db.internal:5432/decentralid_prod

# Blockchain Connectivity
CHAIN_ID=137  # Polygon Mainnet or target EVM network
NETWORK_NAME=polygon
RPC_URL=https://polygon-rpc.com
ISSUER_REGISTRY_ADDRESS=0x...
CREDENTIAL_REGISTRY_ADDRESS=0x...
CREDENTIAL_STATUS_REGISTRY_ADDRESS=0x...

# Storage & IPFS
STORAGE_DIR=/var/data/decentralid/storage
PINATA_JWT=ey...
```

### 2.2 Security Gate Enforcement
If `ENVIRONMENT=production`, the application:
- Rejects all weak secrets containing substrings like `default-development`, `change-in-prod`, `decentralid_dev_secret`, `decentralid_secure_dev_password`.
- Requires `SECRET_KEY` length $\ge 32$ characters.
- Requires `CREDENTIAL_ENCRYPTION_KEY` length $\ge 32$ characters.
- Enforces `SECURE_COOKIE=true` for HTTPS-only cookie transmission.

---

## 3. Deployment Runbook

### 3.1 Smart Contracts Deployment
```bash
# 1. Compile contracts
npx hardhat compile

# 2. Deploy to target EVM network
npx hardhat run scripts/deploy.js --network polygon
```

### 3.2 Database Migration
```bash
# Run Alembic migrations up to latest head
alembic upgrade head
```

### 3.3 Backend Startup
```bash
# Start Gunicorn / Uvicorn workers
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3.4 Frontend Build
```bash
cd frontend
npm ci
npm run build
# Deploy frontend/dist/ to static CDN (Cloudflare Pages, S3/CloudFront, Nginx)
```

---

## 4. Health & Observability Monitoring

- **Liveness Probe**: `GET /api/v1/health/live` (checks process health).
- **Readiness Probe**: `GET /api/v1/health/ready` (probes DB connectivity `SELECT 1`, storage writeability, and RPC contracts configuration).
- **Platform Analytics**: `GET /api/v1/analytics/platform` (real-time platform counters).
