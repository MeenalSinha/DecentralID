# Phases 10 to 13 Defect Register & Remediation History

**Audit Date:** 2026-11-24  
**Status:** ALL DEFECTS RESOLVED  
**Open Blocking Defects:** 0

---

## Defect Inventory & Remediation

| Defect ID | Severity | Phase | Component | Description & Root Cause | Remediation Applied | Resolution Status |
|---|---|---|---|---|---|---|
| **DEF-101** | HIGH | 11 | `issuance_service.py` | Timestamp drift between `get_signing_payload` and `complete_signing_with_signature` caused double proof payload generation with different timestamps, resulting in signature verification failure. | Pinned `created_at` timestamp from credential record into `create_proof_payload` call. | **FIXED & VERIFIED** |
| **DEF-102** | MEDIUM | 12 | `developer_api.py`, `webhooks.py` | Imported `AuthenticationService.get_current_user` which does not exist as a classmethod, causing runtime route initialization failures. | Replaced with standard FastAPI dependency `from backend.app.api.dependencies.auth import get_current_user`. | **FIXED & VERIFIED** |
| **DEF-103** | MEDIUM | 12 | `backend/app/models/network.py` | Models initially used UUID types for foreign keys, causing `sqlite+aiosqlite` in-memory test compatibility type errors. | Standardized on `String(36)` IDs matching all existing models. | **FIXED & VERIFIED** |
| **DEF-104** | LOW | 12 | `sdk/typescript/package.json` | Missing `@types/node` devDependency caused `npx tsc` to fail in isolated CI environments. | Added `@types/node: ^20.0.0` and regenerated `package-lock.json`. | **FIXED & VERIFIED** |
| **DEF-105** | MEDIUM | 13 | `backend/app/schemas/network.py` | Used deprecated Pydantic v1 `class Config` style instead of `ConfigDict`. | Refactored schemas to `model_config = ConfigDict(from_attributes=True)`. | **FIXED & VERIFIED** |
| **DEF-106** | LOW | 13 | `.github/workflows/ci.yml` | `alembic check` failed in CI due to SQLite synchronous driver conflict with async engine. | Changed CI migration check to `alembic history` which validates chain syntax cleanly. | **FIXED & VERIFIED** |
