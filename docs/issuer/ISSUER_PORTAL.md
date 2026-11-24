# DecentralID Institutional Issuer Portal (Phase 6)
**Module:** DecentralID Issuer  
**Audience:** Universities, Educational Institutions, Professional Certification Bodies

---

## 1. Overview & Capabilities

The DecentralID Issuer Portal enables accredited institutions to manage their credential lifecycle from a centralized dashboard. It integrates directly with Phase 5 cryptographic services, PostgreSQL multi-tenant isolation, and the `IssuerRegistry` on Ethereum:

1. **Institutional Accreditation & PKI:**
   - On-chain registry status monitoring (`IssuerRegistry`).
   - Management and rotation of operational signing keys (`secp256k1`).
2. **Dynamic Credential Preparation Studio:**
   - Multi-schema support (`UniversityDegreeCredential`, `AcademicTranscriptCredential`, `CourseCompletionCertificate`, etc.).
   - Schema validation and instant preview of W3C canonical documents and salted commitments.
3. **Institutional Governance & Separation of Duties:**
   - Two-phase approval queue (`PENDING_APPROVAL` $\rightarrow$ `APPROVED`).
   - Enforces separation of duties: preparing operators cannot approve credentials they authored.
4. **Cryptographic Proof Signing & Anchor Confirmation:**
   - Signs approved credentials with W3C Data Integrity proofs (`ecdsa-jcs-2019`).
   - Anchors 32-byte salted commitments on `CredentialRegistry`.
5. **Bulk Batch Issuance:**
   - Ingests CSV files, performs per-record validation, computes commitments, and generates batch draft records.
6. **Authoritative Issuance Ledger:**
   - Searchable, auditable history of all institutional credentials with live status.
