# User Personas

**Project:** DecentralID  
**Date:** November 2026  

---

## 1. Persona Taxonomy

```text
DecentralID Platform
├── Individual Stakeholders
│   └── Individual Holder (Student / Alumnus / Professional)
├── Institutional Stakeholders
│   ├── Institutional Administrator (University Registrar / CTO)
│   └── Authorized Issuer (Department Clerk / Certification Operator)
├── Commercial & Regulatory Stakeholders
│   ├── Independent Verifier (HR Recruiter / Admissions Officer)
│   └── Auditor (Accreditation Inspector / Compliance Officer)
└── Governance
    └── Platform Super Admin (Trust Network Operator)
```

---

## 2. Detailed Persona Profiles

### Persona A: Individual Holder
- **Name:** Maya Lin (Graduate Student & Software Engineer)
- **Primary Goal:** Securely receive, store, and selectively share academic degrees, hackathon awards, and professional licenses with prospective employers without disclosing her home address, full transcript grades, or date of birth.
- **Pain Points:** 
  - Having to pay \$20-\$50 to request official university transcripts every time she applies for a job.
  - Waiting 2–3 weeks for registrar verification.
  - Losing access to school email/portal post-graduation.
- **Capabilities & Permissions:**
  - Owns self-sovereign cryptographic key pairs (EVM wallet / DID).
  - Can accept and inspect issued credentials.
  - Can export verifiable presentations and generate time-bound verification QR codes.
  - Can initiate wallet recovery or key rotation.

### Persona B: Institutional Administrator
- **Name:** Dr. Arthur Vance (Registrar & Director of Academic Systems, Metro University)
- **Primary Goal:** Onboard his university onto DecentralID, establish verified organization status, register authorized cryptographic signing keys, and manage staff operator permissions.
- **Pain Points:**
  - Flooded with manual transcript verification phone calls and emails from employers.
  - High risk of fraudulent diplomas issued under the university's name.
  - Strict compliance obligations under FERPA and GDPR.
- **Capabilities & Permissions:**
  - Registers the organization profile and legal metadata.
  - Submits institutional verification proofs to Platform Admins.
  - Invites and deactivates Authorized Issuers.
  - Manages on-chain authorized signing keys (`addSigningKey`, `rotateSigningKey`, `revokeSigningKey`).

### Persona C: Authorized Issuer
- **Name:** Sarah Jenkins (Credential Issuance Specialist, Department of Engineering)
- **Primary Goal:** Prepare, validate, and issue batch or individual degree credentials to graduating students securely.
- **Pain Points:**
  - Manual, error-prone credential data entry.
  - Unclear revocation mechanisms when an award is rescinded or updated.
- **Capabilities & Permissions:**
  - Prepares credentials according to validated schemas.
  - Signs credentials using delegated institutional signing keys.
  - Commits privacy-preserving hashes/commitments to `CredentialRegistry`.
  - Submits suspension or revocation requests to `CredentialStatusRegistry`.

### Persona D: Independent Verifier
- **Name:** Marcus Reed (Senior Technical Recruiter, CloudScale Inc.)
- **Primary Goal:** Verify within 5 seconds whether an applicant's claimed Master's Degree from Metro University was actually issued by the institution, has not been tampered with, and is currently in active (unrevoked) status.
- **Pain Points:**
  - Candidate onboarding delays caused by waiting for third-party background checks.
  - Exposure to counterfeit or fabricated PDF certificates.
- **Capabilities & Permissions:**
  - Can verify credentials online or offline without requiring an account.
  - Queries `IssuerRegistry` to confirm issuer accreditation and key authorization.
  - Queries `CredentialStatusRegistry` to verify active/suspended/revoked status.
  - Generates verifiable audit records of verification outcomes.

### Persona E: Platform Super Admin
- **Name:** Elena Rostova (Lead Security Officer, DecentralID Foundation)
- **Primary Goal:** Oversee protocol integrity, review and approve institutional verifications, manage contract emergency controls, and maintain system health.
- **Capabilities & Permissions:**
  - Approves or rejects institutional issuer registration applications.
  - Manages on-chain administrative role assignments via multi-signature governance.
  - Invokes emergency pauses in case of security anomalies.
  - Audits global platform security events.

### Persona F: Auditor
- **Name:** David Sterling (Accreditation & Regulatory Inspector)
- **Primary Goal:** Review the cryptographic audit logs of institutions to ensure that issued credentials adhere to accreditation standards without accessing unauthorized student PII.
- **Capabilities & Permissions:**
  - Read-only access to tenant-scoped audit logs and on-chain event streams.
  - Validates issuance volume, revocation history, and signing key lifecycle compliance.
