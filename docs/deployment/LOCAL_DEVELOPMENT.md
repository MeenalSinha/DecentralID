# Local Development Guide

**Project:** DecentralID  
**Date:** November 2026  

---

## 1. Prerequisites

- **Node.js:** v18.0.0+ (Tested on v20 and v22)
- **Python:** 3.11+ (Tested on 3.11 and 3.14)
- **Docker & Docker Compose:** Optional for containerized local orchestration.

---

## 2. One-Click Quickstart (PowerShell)

To launch the complete DecentralID stack with a single command:

```powershell
.\scripts\start-all.ps1
```

This automatically orchestrates:
1. Local Hardhat Blockchain Node (`http://127.0.0.1:8545`, Chain ID: `31337`).
2. Smart contract registry verification and deployment.
3. Database migration execution up to head via Alembic (`decentralid.db`).
4. FastAPI Backend Gateway (`http://localhost:8000`).
5. Vite Frontend React Dashboard (`http://localhost:5173`).

To stop all services:
```powershell
.\scripts\stop-all.ps1
```

---

## 3. Manual Step-by-Step Setup

### Step 1: Smart Contracts & Local Node
```bash
# Install root dependencies
npm install

# Compile contracts
npx hardhat compile

# Run contract tests
npx hardhat test

# Start local Hardhat node
npx hardhat node

# In a separate terminal, deploy registries to localhost
npx hardhat run scripts/deploy/deploy_registries.js --network localhost
```

Deployed contract addresses on local network (Chain ID: 31337):
- `IssuerRegistry`: `0x5FbDB2315678afecb367f032d93F642f64180aa3`
- `CredentialRegistry`: `0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512`
- `CredentialStatusRegistry`: `0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0`

### Step 2: Backend Gateway (FastAPI)
```bash
# Set up virtual environment
python -m venv backend/venv

# Activate virtual environment
# Windows:
.\backend\venv\Scripts\activate
# Linux/macOS:
source backend/venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run migrations
cd backend
alembic upgrade head
cd ..

# Run backend tests
python -m pytest backend/tests

# Start development server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

- API Base: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- OpenAPI Specification: `http://localhost:8000/api/v1/openapi.json`
- Liveness Probe: `http://localhost:8000/api/v1/health/live`
- Readiness Probe: `http://localhost:8000/api/v1/health/ready`
- Blockchain Config: `http://localhost:8000/api/v1/blockchain/config`

### Step 3: Modernized Frontend (Vite + React)
```bash
cd frontend

# Install dependencies
npm install

# Type-check
npm run typecheck

# Run development server
npm run dev
```

Frontend application dashboard is accessible at: `http://localhost:5173`

### Step 4: TypeScript SDK
```bash
cd sdk/typescript

# Install dependencies
npm install

# Type-check without emit
npx tsc -p tsconfig.json --noEmit

# Build distribution bundle
npm run build
```

---

## 4. Quickstart with Docker Compose

To spin up PostgreSQL, the FastAPI backend, and the Nginx-served frontend in isolated containers:

```bash
docker compose up --build
```

- **Frontend:** `http://localhost`
- **Backend API:** `http://localhost:8000/api/v1`
- **PostgreSQL:** `localhost:5432`
