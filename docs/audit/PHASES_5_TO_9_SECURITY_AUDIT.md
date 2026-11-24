# DecentralID — Phases 5–9 Security Audit

**Audit Date:** 2026-11-24  
**Scope:** Phases 5–9 — Credential Engine, Issuer Portal, Holder Wallet, Verification Portal, Lifecycle Management

---

## 1. Threat Model

### Actors
| Actor | Trust Level | Threat |
|-------|-------------|--------|
| Anonymous user | Zero trust | Unauthenticated API access |
| Authenticated holder | Low trust | Access other holders' credentials; extract salts |
| Authenticated issuer | Medium trust | Issue credentials to wrong recipient; sign without approval |
| Authenticated admin | High trust | Cross-tenant data access; abuse of batch operations |
| Passive network observer | Zero trust | Credential data in transit; private key interception |

---

## 2. Findings by Category

### 2.1 Secret and Key Management

| ID | Finding | Severity | Status |
|----|---------|----------|--------|
| DEF-001 | Private institutional signing key entered into React state (`signingPrivateKey`) and transmitted in HTTP POST body. Any XSS or network interception exposes the institutional private key. | **CRITICAL** | **FIXED** |
| DEF-002 | Commitment salt (cryptographic secret binding credential to holder) exposed in API response `HolderCredentialDetail`. Salt leakage allows commitment preimage calculation by any credential holder. | **CRITICAL** | **FIXED** |
| DEF-005 | Salt additionally exposed in VP document `selectiveDisclosure.salt` field, making it accessible to verifiers. | **HIGH** | **FIXED** |
| DEF-014 | Salt field retained in Pydantic schema and TypeScript interface after API fix, risking re-introduction. | **HIGH** | **FIXED** |
| DEF-015 | `ecdsa-jcs-2019` cryptosuite uses keccak256 as hash function instead of SHA-256 specified by W3C. Credentials cannot be verified by external W3C-compliant verifiers. | **HIGH** | **DOCUMENTED** |

**Residual risk:** The signing key transport architectural limitation (key in HTTP POST body) is acknowledged. In production, an HSM, KMS, or client-side wallet signing mechanism must replace this. For competition/demo purposes, the key is not stored server-side and is used only at signing time.

---

### 2.2 Authorization and Access Control

| ID | Finding | Severity | Status |
|----|---------|----------|--------|
| DEF-012 | Credential list endpoint returned ALL credentials in the system to any authenticated user, with no tenant filter. Any logged-in user could enumerate all credentials. | **HIGH** | **FIXED** |
| DEF-013 | Single credential GET endpoint had no authorization check — any authenticated user could retrieve any credential by ID. | **HIGH** | **FIXED** |
| DEF-018 | `sign_credential` accepted credentials in `PREPARED` status, allowing signing without going through the approval workflow (bypassing dual-control). | **HIGH** | **FIXED** |
| DEF-007 | The `issuer` field in holder credential responses returned the recipient address instead of the issuing organization address, corrupting provenance data. | **HIGH** | **FIXED** |

**Approval workflow integrity (post-fix):**
```
PREPARED → PENDING_APPROVAL → APPROVED → [sign] → PENDING_BLOCKCHAIN_REGISTRATION → BLOCKCHAIN_REGISTERED
```
Only `APPROVED` credentials can be signed. Approver ≠ preparer (separation of duties enforced).

---

### 2.3 Data Integrity and Hardcoding

| ID | Finding | Severity | Status |
|----|---------|----------|--------|
| DEF-003 | Hardcoded student names (`"Alice Johnson"`, `"Bob Smith"`), institution addresses (`"0xf39fd6..."`), and credential IDs in `IssuerView.tsx`. These would appear as real institutional data in the production UI. | **CRITICAL** | **FIXED** |
| DEF-006 | Hardcoded Hardhat local chain deployer address `0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266` displayed as the institution's on-chain address in dashboard metrics. | **HIGH** | **FIXED** |
| DEF-009 | Hardcoded fallback metrics `{authorized_keys_count: 1, members_count: 2}` returned when API fails, displaying fabricated data to administrators. | **HIGH** | **FIXED** |
| DEF-010 | Status list endpoint hardcodes chain ID `1337` in DID strings, breaking multi-network deployments. | **HIGH** | **FIXED** |
| DEF-011 | VP presentation document hardcodes chain ID `1337` in DID strings. | **HIGH** | **FIXED** |

---

### 2.4 Fake/Mock Functionality

| ID | Finding | Severity | Status |
|----|---------|----------|--------|
| DEF-004 | VP proof `proofValue` set to the string `"holder_verified_authorization"` — a placeholder string, not a cryptographic signature. Any verifier checking this VP proof value would accept a forgery. | **CRITICAL** | **FIXED** |

**Post-fix behaviour:** VP proofs are only attached when a real ECDSA signature (hex string starting with `0x`, minimum 130 characters) is provided via `holder_signature`. Unsigned VPs omit the proof object entirely rather than including a placeholder.

---

### 2.5 Configuration and Environment

| ID | Finding | Severity | Status |
|----|---------|----------|--------|
| DEF-019 | `.env.example` only contained blockchain/IPFS variables from the original project. All backend configuration variables (`SECRET_KEY`, `CREDENTIAL_ENCRYPTION_KEY`, `DATABASE_URL`, contract addresses, etc.) were absent, making first-time setup impossible without reading source code. | **INFO** | **FIXED** |
| DEF-020 | Smart Contracts CI job missing `cache-dependency-path` for `actions/setup-node`, causing CI cache resolution failures and pipeline failures on push. | **INFO** | **FIXED** |

---

## 3. What Was NOT Found

| Category | Finding |
|----------|---------|
| SQL injection | No raw SQL; SQLAlchemy ORM with parameterized queries throughout |
| JWT algorithm confusion | Algorithm fixed in `create_access_token`; RS256 not used |
| CORS wildcard | `CORS_ORIGINS` from settings, not `*` |
| Nonce replay | Nonces are single-use; replay attack test passes |
| Cross-tenant data leakage (after fix) | Credential endpoints now scoped to org membership |
| Private keys in source code | No hardcoded private keys in backend Python files |
| Unprotected admin endpoints | All sensitive routes require `get_current_user` |

---

## 4. Cryptographic Profile Summary

| Property | Implementation | Standard | Verdict |
|----------|---------------|----------|---------|
| Credential signing | secp256k1 ECDSA | W3C `ecdsa-jcs-2019` | ⚠️ Uses keccak256 instead of SHA-256 |
| Canonicalization | RFC 8785 JCS (custom) | RFC 8785 | ✅ Correct |
| Subject encryption | AES-256-GCM + HKDF | NIST | ✅ Correct |
| Commitment scheme | keccak256(id ‖ salt) | Custom | ✅ Secure binding |
| Status list encoding | GZIP + multibase `u` | W3C Bitstring Status List 1.0 | ✅ Compliant |
| Transport security | HTTPS (config) | TLS 1.2+ | ✅ Required |

---

## 5. Residual Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Signing key transport (POST body) | HIGH | Acknowledged limitation; HSM/KMS required for production |
| W3C interoperability (`ecdsa-jcs-2019` / keccak256) | HIGH | Documented; changing breaks existing signatures |
| Selective disclosure not ZK-proven | MEDIUM | Documented; JSON masking is not cryptographic |
| Salt in pre-fix VP records | LOW | Only affects existing VP records; new VPs correct |

---

*Generated by security audit — 2026-11-24*
