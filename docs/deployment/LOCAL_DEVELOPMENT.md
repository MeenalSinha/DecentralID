# Local Development Guide

**Project:** DecentralID  
**Date:** November 2026  

---

## 1. Prerequisites

- **Node.js:** v18.0.0+ (Tested on v20 and v22)
- **Python:** 3.11+ (Tested on 3.14)
- **Docker & Docker Compose:** Optional for containerized local orchestration.

---

## 2. Quickstart with Local Services

### Step 1: Smart Contracts
```bash
# Install root dependencies
npm install

# Compile contracts
npx hardhat compile

# Run contract tests
npx hardhat test

# (Optional) Start local Hardhat node
npx hardhat node
```

### Step 2: Backend Gateway
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

# Run backend tests
python -m pytest backend/tests

# Start development server
uvicorn backend.app.main:app --reload --port 8000
```
API Documentation will be live at: `http://localhost:8000/docs`

### Step 3: Modernized Frontend
```bash
cd frontend

# Install dependencies
npm install

# Type-check
npx tsc --noEmit

# Run development server
npm run dev
```
Frontend will be accessible at: `http://localhost:5173`

---

## 3. Quickstart with Docker Compose

To spin up PostgreSQL, the FastAPI backend, and the Nginx-served frontend in isolated containers:

```bash
docker compose up --build
```

- **Frontend:** `http://localhost`
- **Backend API:** `http://localhost:8000/api/v1`
- **PostgreSQL:** `localhost:5432`
