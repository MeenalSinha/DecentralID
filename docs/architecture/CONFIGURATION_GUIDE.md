# Application Configuration Guide

**Project:** DecentralID  
**Date:** November 2026  

---

## 1. Centralized Configuration Philosophy

DecentralID adheres strictly to **Rule 2.1: Nothing Hardcoded**.

- **Zero Client-Side Secrets:** The frontend contains no private keys, database passwords, or write-privileged third-party API tokens.
- **Dynamic Configuration Injection:** The frontend fetches its public network metadata, RPC endpoint, and contract registry addresses dynamically at runtime from `GET /api/v1/blockchain/config`.
- **Fail-Fast Backend Validation:** The FastAPI backend utilizes Pydantic Settings to validate environment parameters during startup. Missing required parameters in production abort execution immediately.

---

## 2. Environment Variables Reference

### Backend Settings

| Variable | Description | Default (Dev) | Production Requirement |
|---|---|---|---|
| `ENVIRONMENT` | Deployment environment name | `development` | Set to `production` |
| `DEBUG` | Enable verbose logging | `false` | Must be `false` |
| `DATABASE_URL` | PostgreSQL connection string | `sqlite+aiosqlite:///./decentralid.db` | Required (PostgreSQL async URL) |
| `SECRET_KEY` | HMAC key for session encryption | Dev fallback key | **Required:** Cryptographically secure 32+ char secret |
| `SESSION_COOKIE_NAME` | Name of the session cookie | `decentralid_session` | Standard string |
| `SECURE_COOKIE` | Require HTTPS for cookies | `false` | Must be `true` in production |
| `SAME_SITE_COOKIE` | SameSite cookie policy | `lax` | `lax` or `strict` |
| `CHAIN_ID` | EVM Chain ID | `31337` (Hardhat) | Target network ID (e.g., `11155111` for Sepolia) |
| `NETWORK_NAME` | EVM network name | `hardhat` | Target network name |
| `RPC_URL` | JSON-RPC Provider endpoint | `http://127.0.0.1:8545` | Secure RPC endpoint (Alchemy/Infura) |
| `ISSUER_REGISTRY_ADDRESS` | Deployed `IssuerRegistry` contract | Auto-loaded from manifest | Target contract address |
| `CREDENTIAL_REGISTRY_ADDRESS` | Deployed `CredentialRegistry` contract | Auto-loaded from manifest | Target contract address |
| `CREDENTIAL_STATUS_REGISTRY_ADDRESS` | Deployed `CredentialStatusRegistry` contract | Auto-loaded from manifest | Target contract address |
| `CORS_ORIGINS` | Permitted browser origins | `["http://localhost:5173", ...]` | Strict domain whitelist |

---

## 3. Deployment Manifest Loading

Rather than manually copying contract addresses across source files, deployment scripts write a standardized manifest:

```json
{
  "network": "sepolia",
  "chainId": 11155111,
  "contracts": {
    "IssuerRegistry": "0x...",
    "CredentialRegistry": "0x...",
    "CredentialStatusRegistry": "0x..."
  },
  "deployedAt": "2026-11-24T08:00:00Z"
}
```

The backend automatically checks for this manifest in `deployments/{network}/manifest.json` and serves the validated addresses to the frontend.
