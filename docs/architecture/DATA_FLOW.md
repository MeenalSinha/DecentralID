# End-to-End Data Flow Specification

**Project:** DecentralID  
**Date:** November 2026  

---

## 1. Sequence Diagram: Credential Issuance Flow

This sequence diagrams the complete interaction between the Institutional Issuer, DecentralID Backend, PostgreSQL, and Smart Contracts:

```mermaid
sequenceDiagram
    autonumber
    actor Issuer as Authorized Issuer
    participant FE as Frontend Portal
    participant API as FastAPI Backend
    participant DB as PostgreSQL
    participant BC as EVM Smart Contracts (Registries)
    actor Holder as Student / Holder

    Issuer->>FE: Input Credential Details (Degree, Student DID)
    FE->>API: POST /api/v1/credentials/prepare (Payload)
    API->>API: Validate Schema & Permissions
    API->>API: Generate 256-bit Random Salt (R)
    API->>API: Compute Commitment C = keccak256(Subject || R)
    API-->>FE: Return Typed EIP-712 Data Structure & Hash
    
    Issuer->>FE: Sign EIP-712 with Institutional Key
    FE->>API: POST /api/v1/credentials/issue (Signature, C, Salt)
    API->>BC: CredentialRegistry.registerCredential(id, C, issuer)
    BC->>BC: Verify Issuer Authorization via IssuerRegistry
    BC-->>API: Emit CredentialRegistered Event (txHash)
    API->>DB: Store Credential Record (Status = Active)
    API-->>FE: Return Complete Signed Credential Package
    FE->>Holder: Transmit Verifiable Credential (Encrypted Payload)
```

---

## 2. Sequence Diagram: Independent Credential Verification Flow

This sequence diagrams how an independent verifier verifies a credential without requiring an account or contacting the issuer:

```mermaid
sequenceDiagram
    autonumber
    actor Verifier as Employer / Verifier
    participant VerifyApp as Verification Engine (Web / CLI)
    participant BC as Blockchain Smart Contracts

    Verifier->>VerifyApp: Submit Credential JSON / Scan QR Code
    VerifyApp->>VerifyApp: Parse Subject (S), Salt (R), Signature, Issuer DID
    
    par Cryptographic Verification
        VerifyApp->>VerifyApp: Recover Signer Address from EIP-712 Signature
    and Issuer Accreditation Check
        VerifyApp->>BC: IssuerRegistry.isIssuerAuthorized(issuerAddress)
        BC-->>VerifyApp: Returns true / false
    and Signing Key Validity Check
        VerifyApp->>BC: IssuerRegistry.isSigningKeyValid(issuerAddress, recoveredSigner)
        BC-->>VerifyApp: Returns true / false
    and On-Chain Integrity Check
        VerifyApp->>VerifyApp: Compute C' = keccak256(S || R)
        VerifyApp->>BC: CredentialRegistry.getCredential(credentialId)
        BC-->>VerifyApp: Returns On-Chain Commitment (C)
        VerifyApp->>VerifyApp: Assert C' == C
    and Revocation Status Check
        VerifyApp->>BC: CredentialStatusRegistry.getCredentialStatus(credentialId)
        BC-->>VerifyApp: Returns Status (0=Active, 1=Suspended, 2=Revoked)
    end

    VerifyApp-->>Verifier: Display Trust Verdict: [AUTHENTIC & ACTIVE]
```
