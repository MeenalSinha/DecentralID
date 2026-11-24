# DecentralID: Incident Response & Disaster Recovery Runbook (Phase 18)

## 1. Incident Severity Classification

| Tier | Severity | Definition | Target RTO | Target RPO | Example Scenarios |
|---|---|---|---|---|---|
| **SEV-1** | Critical | Widespread platform outage or compromised signing key | $< 1$ hour | $< 15$ min | Operational signing key compromise; primary database corruption |
| **SEV-2** | High | Degraded functionality impacting one or more institutions | $< 4$ hours | $< 1$ hour | IPFS gateway unreachable; blockchain RPC provider timeout |
| **SEV-3** | Medium | Non-blocking functional defect or integration slowdown | $< 24$ hours | N/A | LMS sync retry backoff; analytics calculation delay |

---

## 2. Emergency Operational Key Revocation Runbook

When an operational signing key is suspected of compromise:
1. **Trigger Emergency Smart Contract Revocation:**
   Platform Governance invokes `emergencyRevokeKey(compromisedAddress)` on `IssuerRegistry.sol`.
   - Contract emits `SigningKeyRevoked` event.
   - Key is marked `validUntil = 0`.
   - All subsequent signature verifications for credentials signed after the revocation timestamp fail immediately.
2. **Deactivate Key in Application Database:**
   Update `SigningKey.status = "REVOKED"` and `is_active = False`.
3. **Dispatch Webhook Notifications:**
   Trigger `institution.key_revoked` to notify all subscribed relying parties.

---

## 3. Database Disaster Recovery & Backup Restoration

### Automated Backup Strategy
- Daily full database dumps with WAL archiving.
- Backups encrypted with AES-256 before upload to offsite secure cold storage.

### Recovery Execution
1. Provision clean target PostgreSQL database container.
2. Restore latest snapshot: `pg_restore -d decentralid_prod < backup.dump`.
3. Run `alembic upgrade head` to align schema version.
4. Verify data integrity: execute `/api/v1/health/ready` deep readiness probe.
