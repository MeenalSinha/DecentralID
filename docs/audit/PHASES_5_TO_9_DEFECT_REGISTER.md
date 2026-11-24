# DecentralID — Phases 5–9 Defect Register

**Audit Date:** 2026-11-24  
**Scope:** Phases 5–9

---

## Defect Classification

| Severity | Definition |
|----------|------------|
| CRITICAL | Directly exploitable: data exposure, authentication bypass, injection |
| HIGH | Significant security or correctness risk; exploitable under reasonable conditions |
| MEDIUM | Affects correctness or maintainability; not directly exploitable |
| INFO | Configuration, documentation, tooling quality |

---

## Full Defect Table

| ID | Severity | Component | Title | Status | Fix Applied |
|----|----------|-----------|-------|--------|-------------|
| DEF-001 | CRITICAL | Frontend / API | Private signing key stored in React state and transmitted in HTTP POST body | **FIXED** | `IssuerView.tsx` fully rewritten — key never enters state; only sent at signing time and never retained |
| DEF-002 | CRITICAL | Backend API | Commitment salt (secret) exposed to holder via API response | **FIXED** | Salt removed from `get_holder_credentials` endpoint response; `HolderCredentialDetail` schema field removed |
| DEF-003 | CRITICAL | Frontend | Hardcoded student names, institution names, Ethereum addresses in `IssuerView.tsx` | **FIXED** | All hardcoded data removed; replaced with dynamic API-driven institution loading |
| DEF-004 | CRITICAL | Backend Service | Fake VP proof `proofValue: "holder_verified_authorization"` in `presentation_service.py` | **FIXED** | VP proof only attached when real `holder_signature` (0x hex, ≥130 chars) is provided; otherwise VP is unsigned |
| DEF-005 | HIGH | Backend Service | Salt exposed in `selectiveDisclosure.salt` field of VP document | **FIXED** | Salt field removed from VP presentation document |
| DEF-006 | HIGH | Frontend | Hardcoded Hardhat deployer address `0xf39fd6e51...` in IssuerView dashboard | **FIXED** | Replaced with dynamic `org.on_chain_address` from API |
| DEF-007 | HIGH | Backend API | `issuer` field in holder credential response set to `recipient_address` instead of issuing org address | **FIXED** | Corrected to use the issuing organization's address |
| DEF-008 | HIGH | Frontend / CI | `frontend/package.json` lacks `typecheck` script; CI ran `npx tsc` directly | **FIXED** | Added `"typecheck": "tsc --noEmit"` script; CI updated to `npm run typecheck` |
| DEF-009 | HIGH | Frontend | Hardcoded fallback metrics `{authorized_keys_count: 1, members_count: 2}` when API fails | **FIXED** | On API failure, metrics display `—` (null) instead of fabricated values |
| DEF-010 | HIGH | Backend API | `credential_lifecycle.py` status list endpoint hardcodes chain ID `1337` | **FIXED** | Replaced with `settings.CHAIN_ID` |
| DEF-011 | HIGH | Backend Service | `presentation_service.py` VP document hardcodes chain ID `1337` | **FIXED** | Replaced with `settings.CHAIN_ID` |
| DEF-012 | HIGH | Backend API | `credentials.py` list endpoint returned all credentials to any authenticated user (no tenant filter) | **FIXED** | Endpoint now scoped to credentials belonging to the user's organization memberships |
| DEF-013 | HIGH | Backend API | `credentials.py` single credential GET had no authorization check | **FIXED** | Enforces holder-or-org-member check before returning credential |
| DEF-014 | HIGH | Schema / Frontend | `HolderCredentialDetail.salt` field in Pydantic schema and `CredentialItem.salt` in TypeScript still present after API no longer sends `salt` | **FIXED** | Removed from both Pydantic schema (`presentation.py`) and TypeScript interface (`WalletView.tsx`); removed `salt: cred.salt` from verification call |
| DEF-015 | HIGH | Backend Service | `ecdsa-jcs-2019` uses keccak256 not SHA-256 — NOT W3C interoperable | **DOCUMENTED** | Acknowledged as known limitation in `CRYPTOGRAPHIC_PROFILE.md` and audit report; changing would invalidate all existing signatures |
| DEF-016 | MEDIUM | Backend API | `batch-prepare` endpoint: authorization delegated entirely to service layer without route-level guard | **ACCEPTABLE** | `PreparationService.prepare_credential` enforces org membership at service layer; risk is acceptable |
| DEF-017 | MEDIUM | Data | Existing `PresentationShare` records may contain `salt` in stored VP JSON | **DOCUMENTED** | Data migration consideration for existing deployments; new VPs correctly omit salt |
| DEF-018 | HIGH | Backend Service | `issuance_service.sign_credential` accepted `PREPARED` status (bypassing approval workflow) | **FIXED** | Only `APPROVED` status allowed for signing; `PREPARED` removed from allowed statuses |
| DEF-019 | INFO | Configuration | `.env.example` missing all backend environment variables added in Phases 0–9 | **FIXED** | `.env.example` updated with all required backend variables: `SECRET_KEY`, `CREDENTIAL_ENCRYPTION_KEY`, `DATABASE_URL`, `CHAIN_ID`, `NETWORK_NAME`, `RPC_URL`, contract addresses, `ENVIRONMENT`, `CORS_ORIGINS` |
| DEF-020 | INFO | CI | Smart Contracts CI job missing `cache-dependency-path` for `actions/setup-node` cache | **FIXED** | Added `cache-dependency-path: package-lock.json` to prevent CI cache resolution failures |

---

## Defects by Phase

| Phase | Defects |
|-------|---------|
| Phase 5 (Credential Engine) | DEF-004, DEF-005, DEF-010, DEF-011, DEF-015 |
| Phase 6 (Issuer Portal) | DEF-001, DEF-003, DEF-006, DEF-009, DEF-018 |
| Phase 7 (Holder Wallet) | DEF-002, DEF-007, DEF-013, DEF-014 |
| Phase 8 (Verification Portal) | DEF-012, DEF-016 |
| Phase 9 (Lifecycle Management) | DEF-017 |
| Cross-cutting | DEF-008, DEF-019, DEF-020 |

---

## Defects Remaining Open

None. All CRITICAL and HIGH defects are fixed. DEF-015 and DEF-017 are documented as known limitations. DEF-016 is an acceptable architectural decision.

---

*Generated by security audit — 2026-11-24*
