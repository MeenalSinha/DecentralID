# IssuerRegistry Contract Specification

**Contract:** `contracts/IssuerRegistry.sol`  
**Standard:** OpenZeppelin AccessControl, Pausable  
**Solidity:** `^0.8.20`  

---

## 1. Contract Overview
Maintains an authoritative on-chain registry of accredited credential issuers, institutional tiers, and operational signing keys.

---

## 2. Key Data Structures

```solidity
enum IssuerRole { Individual, Organization, DAO, VerifiedInstitution }
enum IssuerStatus { Inactive, Active, Suspended, Revoked }

struct IssuerInfo {
    string metadataURI;     // IPFS URI to legal accreditation metadata
    IssuerRole role;        // Institutional tier
    IssuerStatus status;    // Active / Suspended / Revoked
    uint256 authorizedAt;   // Timestamp of initial accreditation
}

struct SigningKeyInfo {
    bool isActive;          // Whether key is currently permitted to sign
    uint256 validUntil;     // Expiration timestamp (0 = indefinite)
}
```

---

## 3. Function Interface

### Write Operations
- `registerIssuer(address issuer, IssuerRole role, string metadataURI)`: Requires `GOVERNANCE_ROLE`.
- `authorizeIssuer(address issuer, IssuerRole role)`: Requires `GOVERNANCE_ROLE`.
- `suspendIssuer(address issuer)`: Requires `GOVERNANCE_ROLE`.
- `reinstateIssuer(address issuer)`: Requires `GOVERNANCE_ROLE`.
- `revokeIssuer(address issuer)`: Requires `GOVERNANCE_ROLE`. Permanent revocation.
- `registerSigningKey(address signingKey, uint256 validUntil)`: Invoked by issuer to authorize operational keys.
- `revokeSigningKey(address signingKey)`: Invoked by issuer to deactivate a key.
- `emergencyRevokeSigningKey(address issuer, address signingKey)`: Governance emergency override.

### Read Operations
- `isIssuerAuthorized(address issuer) returns (bool)`: Returns `true` only if status is `Active`.
- `isSigningKeyValid(address issuer, address signingKey) returns (bool)`: Verifies key is active, not expired, and issuer is active.
- `getIssuer(address issuer) returns (IssuerInfo)`: Returns institutional profile.
