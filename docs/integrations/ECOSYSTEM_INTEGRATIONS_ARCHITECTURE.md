# DecentralID: Enterprise Ecosystem Integrations Architecture (Phase 17)

## 1. Overview and Objectives

Phase 17 connects DecentralID with real institutional and enterprise applications through modular adapters:
1. **Education Systems (LMS/SIS):** Ingests course completions and student graduation records from Canvas, Moodle, Banner, and PeopleSoft.
2. **Enterprise HR & Recruitment (ATS/HRIS):** Verifies candidates' credentials with strict data minimization without exposing the candidate's full wallet.
3. **Bulk Historical Migration Toolkit:** Validates, maps, and stages legacy paper/database credentials with duplicate detection.
4. **Enterprise SSO & IdP Federation:** Connects university and corporate identity providers (OIDC/SAML) while preserving the separation between IdP session authentication and cryptographic key signing.

---

## 2. Core Security & Architectural Principles

### 2.1 The Ingestion-Without-Bypass Principle
Bulk data ingestion (whether via LMS API, SIS feed, or CSV migration) **never automatically signs or issues credentials**.
All ingested records enter a structured preparation draft status (`PENDING_APPROVAL`) and must proceed through the standard institutional review, separation-of-duties approval, and client-side cryptographic key signing workflow.

### 2.2 The Candidate Privacy Principle (HR Verifications)
In HR/ATS workflows:
- The candidate selectively discloses only the claims requested by the employer (e.g. `degree` and `institution`).
- The employer receives a cryptographically authenticated verification receipt confirming the claims.
- The employer is strictly prohibited from viewing unrequested claims or browsing other credentials in the candidate's wallet.

### 2.3 The SSO vs. Cryptographic Key Separation Principle
Institutional SSO (e.g., Google Workspace, Microsoft Entra, Shibboleth/SAML) authenticates the user into the institutional portal. However, DecentralID **never** allows SSO to sign credentials. Cryptographic W3C Data Integrity signing strictly requires the user's client-side cryptographic key (Web3 wallet or Hardware Security Module).
