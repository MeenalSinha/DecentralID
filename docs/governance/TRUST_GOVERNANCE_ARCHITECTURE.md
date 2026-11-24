# DecentralID: Trust Governance & Institutional Accreditation Architecture (Phase 15)

## 1. Overview and Objectives

Phase 15 establishes an auditable institutional trust and multi-level accreditation governance system for DecentralID.

### Key Capabilities
1. **Multi-Stage Institutional Accreditation:**
   - Categorized institutional onboarding (`UNIVERSITY`, `COLLEGE`, `VOCATIONAL`, `REGULATORY_BODY`, `ENTERPRISE`).
   - Evidentiary submission (regulatory certificates, university charters) stored via content-addressed digests.
   - Separation of duties across approval levels: first-stage review officers cannot serve as second-stage senior approvers, and institutions can never approve themselves.
2. **Multi-Dimensional Trust Policy Engine (`TrustPolicyService`):**
   - Evaluates:
     - Institutional entity state (`ACTIVE` vs `SUSPENDED`).
     - Accreditation lifecycle status (`APPROVED`, `UNDER_REVIEW`, `EXPIRED`, `SUSPENDED`).
     - Validity time boundary enforcement (`valid_until` timestamp).
     - Schema authorization: institutions are only trusted to issue approved credential types (e.g. universities cannot issue commercial driver licenses; enterprises cannot issue state medical degrees).
     - Operational signing key authorization: verified against registered `SigningKey` records.
3. **Privacy-Preserving Public Trust Directory:**
   - Provides public query access to accredited entities, their public verification identities, approved credential scopes, and validity periods without leaking internal review notes, officer identities, or confidential documents.

---

## 2. Accreditation Lifecycle State Transitions

```text
       [ Submit Application ]
                 │
                 ▼
             ( APPLIED )
                 │
         [ Stage 1 Review ] ────► ( EVIDENCE_REQUESTED ) ──► [ Re-submit ]
                 │
                 ▼
          ( UNDER_REVIEW )
                 │
         [ Stage 2 Senior ]
          [    Decision   ]
          ┌──────┴──────┐
          ▼             ▼
     ( APPROVED )  ( REJECTED )
          │
    [ Expiration / Suspension ]
          │
          ▼
  ( EXPIRED / SUSPENDED )
```
