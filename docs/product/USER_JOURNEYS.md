# End-to-End User Journeys

**Project:** DecentralID  
**Date:** November 2026  

---

## 1. Journey Overview

This document specifies the step-by-step user journeys across all 17 critical system workflows:

1. Individual Onboarding & Wallet Connection
2. Institutional Registration
3. Institutional Verification & Platform Vetting
4. Issuer Signing Key Authorization & Registration
5. Credential Preparation & Schema Validation
6. Credential Cryptographic Issuance & On-Chain Registration
7. Credential Receipt & Storage in Holder Wallet
8. Credential Sharing & Selective Disclosure
9. Independent Verifier Verification
10. Credential Expiration Handling
11. Authorized Credential Suspension
12. Authorized Credential Revocation
13. Institutional Key Rotation
14. Compromised Key Deauthorization (Emergency)
15. Institutional Issuer Suspension
16. Institutional Issuer Revocation
17. Holder Wallet Key Migration / Recovery

---

## 2. Core User Journey Specifications

### Journey 1: Individual Onboarding & SIWE Authentication
- **Actor:** Individual Holder
- **Preconditions:** Holder has an EVM-compatible wallet (e.g., MetaMask).
- **Steps:**
  1. Holder navigates to DecentralID portal and clicks "Connect Wallet".
  2. Frontend sends request to `POST /api/v1/authentication/challenge` with wallet address and chain ID.
  3. Backend generates cryptographically secure, random nonce (TTL = 5 minutes) bound to domain and IP address.
  4. Frontend constructs EIP-4361 compliant Sign-In with Ethereum (SIWE) message and prompts wallet signature.
  5. User signs message with private key.
  6. Frontend submits signature to `POST /api/v1/authentication/verify-wallet`.
  7. Backend verifies signature matches address, ensures nonce was not previously used, consumes nonce, and creates an HTTP-only, secure session cookie.
  8. Holder profile is created or loaded in PostgreSQL.
- **Failure Modes:** Malformed signature, expired nonce, domain mismatch, or replayed nonce; returns `401 Unauthorized`.

---

### Journey 2: Institutional Registration & Onboarding
- **Actor:** Institutional Administrator
- **Preconditions:** Admin has authenticated their personal wallet via SIWE.
- **Steps:**
  1. Admin navigates to `/institution/register`.
  2. Submits organization legal name, jurisdiction, D-U-N-S or accreditation number, domain name, and administrative contact email.
  3. Backend creates `Organization` entity with status `PENDING_REVIEW` and associates user as `INSTITUTION_ADMIN` in `OrganizationMembership`.
  4. Platform administrators are notified via audit webhook.
- **Security Constraint:** Registration does NOT grant on-chain issuance privileges.

---

### Journey 3: Institutional Vetting & On-Chain Authorization
- **Actor:** Platform Super Admin & Institutional Administrator
- **Preconditions:** Organization has submitted verification documents; Organization is in `PENDING_REVIEW`.
- **Steps:**
  1. Platform Super Admin inspects accreditation proof and legal documentation.
  2. Super Admin approves institution in platform database (`status = VERIFIED`).
  3. Super Admin executes on-chain transaction: `IssuerRegistry.authorizeIssuer(orgAddress, IssuerRole.VerifiedInstitution)`.
  4. Contract emits `IssuerAuthorized(orgAddress, role)`.
  5. Backend transaction indexer detects event and synchronizes organization state to `AUTHORIZED`.

---

### Journey 4: Issuer Signing Key Authorization
- **Actor:** Institutional Administrator
- **Preconditions:** Organization is authorized on `IssuerRegistry`.
- **Steps:**
  1. Institutional Admin generates an institutional operational signing key pair (cold storage or HSM).
  2. Admin executes `IssuerRegistry.registerSigningKey(orgAddress, signingKeyAddress, validUntil)`.
  3. Contract verifies caller has `ADMIN_ROLE` for the institution and records signing key in active set.
  4. Emits `SigningKeyRegistered(orgAddress, signingKeyAddress, validUntil)`.

---

### Journey 5: Credential Preparation & Issuance
- **Actor:** Authorized Issuer
- **Preconditions:** Issuer is an active member with role `AUTHORIZED_ISSUER`; institutional signing key is active on `IssuerRegistry`.
- **Steps:**
  1. Issuer prepares credential payload adhering to W3C schema (e.g., Degree Credential: recipient DID, degree name, graduation year).
  2. Backend validates payload against Pydantic schema and generates high-entropy salt (`salt = crypto.randomBytes(32)`).
  3. Backend computes privacy-preserving commitment:
     $$\text{commitment} = \text{keccak256}(\text{canonicalJSON}(\text{credentialSubject}) \parallel \text{salt})$$
  4. Operational signing key signs the EIP-712 credential structure.
  5. Authorized Issuer submits commitment to `CredentialRegistry.registerCredential(credentialId, commitment, issuerAddress)`.
  6. Contract verifies issuer is authorized and key is active; stores commitment and emits `CredentialRegistered(credentialId, commitment, issuerAddress)`.
  7. Holder receives signed credential package (including the salt and on-chain transaction reference) through encrypted transport.

---

### Journey 6: Independent Verifier Verification
- **Actor:** Independent Verifier (e.g., HR Recruiter)
- **Preconditions:** Verifier has received a credential JSON or scanned a verification QR code. No login required.
- **Steps:**
  1. Verifier submits credential package to verification engine.
  2. Engine decodes issuer DID (`did:ethr:{chainId}:{issuerAddress}`) and retrieves signing key.
  3. **Cryptographic Check:** Verifies EIP-712 digital signature matches the claimed issuer signing key.
  4. **Issuer Registry Check:** Queries `IssuerRegistry.isIssuerAuthorized(issuerAddress)` and `IssuerRegistry.isSigningKeyValid(issuerAddress, signingKeyAddress)`.
  5. **Integrity & Commitment Check:** Recomputes `keccak256(canonicalSubject || salt)` and verifies it matches on-chain `CredentialRegistry.getCredentialCommitment(credentialId)`.
  6. **Status & Revocation Check:** Queries `CredentialStatusRegistry.getCredentialStatus(credentialId)`. Asserts status is `Active` (0).
  7. Returns verified badge: "Verified: Authentic, Unmodified, Active Credential issued by Metro University".
- **Failure Modes:** Signature mismatch, unregistered issuer, revoked key, tampered fields, or revoked credential status.
