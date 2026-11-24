# Functional Requirements Specification

**Project:** DecentralID  
**Date:** November 2026  
**Baseline:** Phases 0–4 Architecture  

---

## 1. System Feature Requirements (Phases 0–4)

### 1.1 Authentication & Identity (FR-AUTH)
- **FR-AUTH-01 (SIWE Wallet Authentication):** The system MUST implement EIP-4361 Sign-In with Ethereum using cryptographically random nonces.
- **FR-AUTH-02 (Nonce Expiration & Replay Defense):** Nonces MUST expire within 5 minutes and MUST be invalidated immediately upon first verification or failure.
- **FR-AUTH-03 (Session Security):** Sessions MUST be tracked server-side and identified through secure, HTTP-only, SameSite cookies.
- **FR-AUTH-04 (Role-Based Access Control):** The system MUST enforce the following distinct roles:
  - `PLATFORM_SUPER_ADMIN`
  - `INSTITUTION_ADMIN`
  - `AUTHORIZED_ISSUER`
  - `HOLDER`
  - `VERIFIER`
  - `AUDITOR`
- **FR-AUTH-05 (Tenant Isolation):** Every institution-scoped resource (memberships, keys, schemas, issuance records) MUST be scoped to an `organization_id` derived exclusively from server-side session authentication. Client-provided tenant IDs MUST NOT be trusted.

---

### 1.2 Institutional Organization Management (FR-ORG)
- **FR-ORG-01 (Organization Registration):** Users MUST be able to submit institutional registration requests with legal metadata.
- **FR-ORG-02 (Invitation & Member Management):** Institution Admins MUST be able to invite team members and assign institutional roles (`INSTITUTION_ADMIN`, `AUTHORIZED_ISSUER`, `AUDITOR`).
- **FR-ORG-03 (Suspension & Termination):** Organization Admins or Platform Admins MUST be able to deactivate memberships with immediate session invalidation.

---

### 1.3 Smart Contract Infrastructure: IssuerRegistry (FR-SC-ISSUER)
- **FR-SC-ISSUER-01 (Issuer Registration):** Platform Admins MUST be able to register institutional issuers on-chain.
- **FR-SC-ISSUER-02 (Role Assignment):** IssuerRegistry MUST support distinct institutional tiers (`Individual`, `Organization`, `VerifiedInstitution`).
- **FR-SC-ISSUER-03 (Signing Key Lifecycle):** Issuers MUST be able to register, rotate, and revoke authorized signing keys with optional validity timestamps.
- **FR-SC-ISSUER-04 (Issuer Suspension & Revocation):** Authorized admins MUST be able to suspend or permanently revoke an issuer. Revocation MUST be irreversible.
- **FR-SC-ISSUER-05 (Query Functions):** Any caller MUST be able to query `isIssuerAuthorized(address)` and `isSigningKeyValid(issuer, key)`.

---

### 1.4 Smart Contract Infrastructure: CredentialRegistry (FR-SC-CRED)
- **FR-SC-CRED-01 (Commitment Registration):** Authorized issuers MUST be able to register credential commitments (`bytes32`).
- **FR-SC-CRED-02 (Duplicate Prevention):** Credential IDs MUST be unique. Duplicate registrations MUST revert with `CredentialAlreadyExists`.
- **FR-SC-CRED-03 (Caller Authorization Check):** CredentialRegistry MUST verify against IssuerRegistry that the caller is an active, authorized issuer.
- **FR-SC-CRED-04 (Privacy Protection):** CredentialRegistry MUST NOT accept or store plain text personal information.

---

### 1.5 Smart Contract Infrastructure: CredentialStatusRegistry (FR-SC-STATUS)
- **FR-SC-STATUS-01 (Lifecycle States):** Contract MUST support status states: `Active` (0), `Suspended` (1), `Revoked` (2).
- **FR-SC-STATUS-02 (State Transitions):**
  - An `Active` credential MAY transition to `Suspended` or `Revoked`.
  - A `Suspended` credential MAY be reinstated to `Active` or transitioned to `Revoked`.
  - A `Revoked` credential MUST NEVER transition back to `Active` or `Suspended`.
- **FR-SC-STATUS-03 (Caller Authorization):** Only the original issuer (or designated governance admin) MAY update credential status.

---

### 1.6 Verification Engine (FR-VERIFY)
- **FR-VERIFY-01 (Signature Validation):** The verification service MUST independently verify cryptographic signatures over the credential subject.
- **FR-VERIFY-02 (Issuer Authorization Check):** The system MUST verify on-chain that the signing authority was authorized at issuance time.
- **FR-VERIFY-03 (Status Check):** The system MUST verify on-chain that the credential has not been suspended or revoked.
- **FR-VERIFY-04 (No Wallet Required):** Independent verification MUST be accessible to third-party verifiers without requiring wallet connection or authentication.
