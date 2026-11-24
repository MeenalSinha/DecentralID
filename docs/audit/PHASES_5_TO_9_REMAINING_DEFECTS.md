# DecentralID — Phases 5–9 Remaining Limitations and Roadmap

**Date:** 2026-11-24  
**Status:** No blocking critical or high severity defects remain. Known architectural limitations are cataloged below with designated target phases for resolution.

---

## Catalog of Known Limitations

| ID | Category | Summary | Current Mitigation | Target Phase |
|---|---|---|---|---|
| **LIM-001** | Cryptography / Standards | `ecdsa-jcs-2019` implementation uses Keccak-256 rather than SHA-256 specified by W3C Data Integrity. | Verifiable within DecentralID ecosystem; marked with legacy profile identifier. | **Phase 11** (Standards-compliant profile & versioned migration) |
| **LIM-002** | Key Custody / Security | Institutional signing key transport via HTTP request body in `/credentials/{id}/sign`. | Key is never persisted in DB or browser storage; handled only in-memory at signing time. | **Phase 11** (Client-side EIP-712 / KMS signing abstraction) |
| **LIM-003** | Privacy | Selective disclosure operates via JSON field masking rather than cryptographic zero-knowledge or BBS+ proofs. | Salt stripped; undocumented claims masked; labeled as attribute-level disclosure. | **Phase 11** (BBS+ / ZK cryptographic selective disclosure) |
| **LIM-004** | Storage | Credential documents stored solely in PostgreSQL; no decentralized IPFS integration active. | Subject data is strongly encrypted with AES-256-GCM. | **Phase 12** (Encrypted IPFS / Pinata content-addressed storage) |
| **LIM-005** | API / Integration | External platforms currently lack dedicated third-party API keys, webhook feeds, and an external TypeScript SDK. | Core endpoints exist under `/api/v1/credentials` and `/api/v1/verification`. | **Phase 12** (Developer API, TypeScript SDK & Webhooks) |
| **LIM-006** | Operations | Administrative analytics, system-wide audit export, and health telemetry are basic. | Standard health check and database models present. | **Phase 13** (Platform Admin, Institutional Analytics & Observability) |

---

## Conclusion
All blocking vulnerabilities and data exposures from Phases 0–9 have been eliminated. Development can proceed immediately to Phase 10 (DecentralID Intelligence).
