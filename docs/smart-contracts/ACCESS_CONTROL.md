# Smart Contract Access Control Specification

**Project:** DecentralID  
**Date:** November 2026  
**Contracts:** `IssuerRegistry`, `CredentialRegistry`, `CredentialStatusRegistry`  

---

## 1. Role Hierarchy & Separation of Powers

DecentralID contracts implement OpenZeppelin v5 `AccessControl` and `Pausable` to enforce strict least-privilege boundaries:

```mermaid
graph TD
    subgraph MultiSigGovernance["Governance / Multi-Signature"]
        AdminRole[DEFAULT_ADMIN_ROLE]
        GovRole[GOVERNANCE_ROLE]
        StatusOpRole[STATUS_OPERATOR_ROLE]
    end

    subgraph InstitutionalSigners["Institutional Key Hierarchy"]
        InstPrimary[Institutional Primary Address]
        OpKey1[Operational Signing Key A]
        OpKey2[Operational Signing Key B]
    end

    AdminRole -->|Manages Roles & Pausing| GovRole
    GovRole -->|Registers / Revokes Institutions| IssuerReg[IssuerRegistry.sol]
    InstPrimary -->|Registers Operational Keys| IssuerReg
    OpKey1 -->|Registers Salted Commitments| CredReg[CredentialRegistry.sol]
    OpKey2 -->|Updates Suspension / Revocation| StatusReg[CredentialStatusRegistry.sol]
```

---

## 2. Granular Contract Permissions

| Function | Contract | Required Role / Authority | Notes |
|---|---|---|---|
| `pause()` / `unpause()` | All | `DEFAULT_ADMIN_ROLE` | Circuit breaker for emergency freezing. |
| `registerIssuer()` | `IssuerRegistry` | `GOVERNANCE_ROLE` | Accredit institutional organizations. |
| `suspendIssuer()` | `IssuerRegistry` | `GOVERNANCE_ROLE` | Temporary institutional freeze. |
| `revokeIssuer()` | `IssuerRegistry` | `GOVERNANCE_ROLE` | Irreversible institutional revocation. |
| `registerSigningKey()` | `IssuerRegistry` | Active Issuer Address (`msg.sender`) | Authorize operational signing keys. |
| `revokeSigningKey()` | `IssuerRegistry` | Issuer Address or `GOVERNANCE_ROLE` | Deauthorize compromised or departed keys. |
| `registerCredential()` | `CredentialRegistry` | Authorized Issuer or Operational Key | Enforces commitment integrity & uniqueness. |
| `suspendCredential()` | `CredentialStatusRegistry` | Authorized Issuer Key or `STATUS_OPERATOR_ROLE` | Temporary suspension with reason string. |
| `reinstateCredential()` | `CredentialStatusRegistry` | Authorized Issuer Key or `STATUS_OPERATOR_ROLE` | Reinstates suspended credentials. |
| `revokeCredential()` | `CredentialStatusRegistry` | Authorized Issuer Key or `STATUS_OPERATOR_ROLE` | **Terminal Revocation:** Cannot be reactivated. |
