# Role-Based Access Control (RBAC) Matrix

**Project:** DecentralID  
**Date:** November 2026  
**Implementation:** `backend/app/services/authorization_service.py` & `api/dependencies/auth.py`  

---

## 1. Role Definitions

| Role Identifier | Role Scope | Description |
|---|---|---|
| `PLATFORM_SUPER_ADMIN` | Global Platform | Foundation operator; governs institutional accreditations and contract emergency controls. |
| `INSTITUTION_ADMIN` | Tenant Organization | University Registrar or institutional IT lead; manages organizational profile, signing keys, and staff operators. |
| `AUTHORIZED_ISSUER` | Tenant Organization | Departmental issuance operator; prepares and signs credentials adhering to approved schemas. |
| `HOLDER` | Personal Account | Individual student or professional; owns wallet DID and manages personal credential vault. |
| `VERIFIER` | Global / Public | Employer, background checker, or admissions officer; verifies credentials independently. |
| `AUDITOR` | Tenant or Global | Compliance inspector; read-only access to issuance volumes and on-chain status logs. |

---

## 2. Granular Permissions Matrix

| API Operation | Endpoint | Super Admin | Institution Admin | Authorized Issuer | Holder | Verifier | Auditor |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Request SIWE Challenge | `POST /authentication/challenge` | Any | Any | Any | Any | Any | Any |
| Verify Wallet | `POST /authentication/verify-wallet` | Any | Any | Any | Any | Any | Any |
| Read Own Profile | `GET /users/me` | Yes | Yes | Yes | Yes | Yes | Yes |
| Update Own Profile | `PUT /users/me` | Yes | Yes | Yes | Yes | Yes | Yes |
| Register Organization | `POST /organizations` | Yes | Yes | No | No | No | No |
| View Organization Details | `GET /organizations/{id}` | Yes | Own Org | Own Org | No | No | Own Org |
| Invite Tenant Member | `POST /organizations/{id}/members` | Yes | Own Org | No | No | No | No |
| List Tenant Members | `GET /organizations/{id}/members` | Yes | Own Org | Own Org | No | No | Own Org |
| Revoke Tenant Member | `DELETE /organizations/{id}/members/{m_id}` | Yes | Own Org | No | No | No | No |
| Prepare Credential | `POST /credentials/prepare` | Yes | Own Org | Own Org | No | No | No |
| Issue Credential | `POST /credentials/issue` | Yes | Own Org | Own Org | No | No | No |
| Revoke Credential | `POST /credentials/{id}/revoke` | Yes | Own Org | Own Org | No | No | No |
| Independent Verification | `POST /verification/verify` | Yes | Yes | Yes | Yes | Yes | Yes |
| Public Blockchain Config | `GET /blockchain/config` | Public | Public | Public | Public | Public | Public |
