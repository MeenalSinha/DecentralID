# API Architecture Specification

**Project:** DecentralID  
**Date:** November 2026  
**Target:** Version 1.0.0 (`/api/v1/`)  

---

## 1. API Design Principles

1. **RESTful Resource Orientation:** Consistent resource naming, standard HTTP verbs (`GET`, `POST`, `PUT`, `DELETE`), and predictable JSON envelopes.
2. **Strict Schema Validation:** All endpoints accept and return Pydantic models with strict typing and input sanitization.
3. **Defense-in-Depth Authentication:** Dual-mode authentication:
   - **Wallet Session:** Signed EIP-4361 challenge generating a secure HTTP-only session cookie.
   - **Bearer Tokens:** Optional API client tokens for institutional server-to-server integrations.
4. **Tenant-Scoped Context:** Organizational endpoints derive tenant authority from the authenticated session, preventing horizontal privilege escalation.

---

## 2. API Endpoint Catalog

```text
/api/v1/
├── authentication/
│   ├── POST /challenge             # Generate unique cryptographic SIWE challenge
│   ├── POST /verify-wallet         # Verify wallet signature and establish session
│   ├── POST /logout                # Invalidate session
│   └── GET  /session               # Return current session and user profile
│
├── users/
│   ├── GET  /me                    # Current user profile
│   └── PUT  /me                    # Update profile details
│
├── organizations/
│   ├── POST /                      # Register new institutional organization
│   ├── GET  /                      # List organizations (Platform Admin / public directory)
│   ├── GET  /{org_id}              # Organization details
│   ├── GET  /{org_id}/members      # List members (tenant-scoped)
│   ├── POST /{org_id}/members      # Invite member
│   └── DELETE /{org_id}/members/{id} # Remove member
│
├── credentials/
│   ├── POST /prepare               # Prepare & validate credential schema payload
│   ├── POST /issue                 # Issue credential & register on-chain commitment
│   ├── GET  /{id}                  # Retrieve credential metadata & proof package
│   ├── POST /{id}/suspend          # Suspend credential
│   ├── POST /{id}/reinstate        # Reinstate credential
│   └── POST /{id}/revoke           # Revoke credential
│
├── verification/
│   ├── POST /verify                # Verify credential signature, issuer & status
│   └── GET  /status/{id}           # Quick status lookup on status registry
│
├── blockchain/
│   ├── GET  /config                # Public non-sensitive contract addresses & chain ID
│   └── GET  /issuers/{address}     # On-chain issuer authorization status
│
└── health/
    ├── GET  /live                  # Liveness probe (returns 200 OK)
    └── GET  /ready                 # Readiness probe (probes DB and RPC connectivity)
```

---

## 3. Standard Error Envelope

All API errors return a standardized JSON structure with request correlation ID:

```json
{
  "error": {
    "code": "UNAUTHORIZED_TENANT_ACCESS",
    "message": "User does not hold required permissions within the requested organization.",
    "correlation_id": "req_01hgb78y9q12z34x",
    "timestamp": "2026-11-24T07:44:00Z",
    "details": []
  }
}
```
