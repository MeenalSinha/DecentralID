# DecentralID: Release Management & Staging Deployment Runbook (Phase 18)

## 1. Environment Separation & Secret Isolation

DecentralID isolates execution environments:

| Environment | Purpose | Database | Blockchain Registry | Storage |
|---|---|---|---|---|
| **Development** | Local engineering | SQLite `local.db` | Local Hardhat node (`31337`) | Local CAS `storage/ipfs/` |
| **Testing / CI** | Automated quality gates | In-memory `sqlite+aiosqlite` | Ephemeral Hardhat EVM | Ephemeral test storage |
| **Staging** | Pre-production validation | Managed PostgreSQL | Polygon Amoy Testnet (`80002`) | Pinata IPFS (Test bucket) |
| **Production** | Multi-institution trust network | High-availability PostgreSQL | Polygon Mainnet (`137`) / Ethereum | Pinata IPFS + Dedicated IPFS Nodes |

---

## 2. Quality Gate Promotion Criteria

Before any release artifact is promoted from Staging to Production, it must satisfy:
1. **Smart Contracts Gate:** `npx hardhat test` passing 100% (43/43 tests, including invariant and defect proofs).
2. **Backend Services Gate:** `pytest backend/tests` passing 100% (45/45 tests across all phases).
3. **Frontend Gate:** `npm run typecheck`, `npm run lint`, `npm run build` clean with 0 warnings and 0 errors.
4. **TypeScript SDK Gate:** `@decentralid/sdk` compiles cleanly with reproducible lockfile.
5. **Database Migration Gate:** `alembic history` validates forward/backward migration graph.
6. **Security Gate:** `validate_production_security()` halts deployment if default passwords, weak keys, or insecure cookies exist.

---

## 3. Rollback Procedures

If an operational anomaly occurs during release deployment:
1. **Backend Rollback:** Revert container image tag to previous stable digest; run `alembic downgrade -1` if schema change was applied.
2. **Smart Contract Emergency:** If an operational signing key is compromised, governance invokes `emergencyRevokeKey(keyAddress)` on `IssuerRegistry` to immediately halt signing authorization.
3. **Frontend Rollback:** Redeploy previous static asset bundle from CDN origin.
