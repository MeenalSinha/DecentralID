# Contract Event Specification

**Project:** DecentralID  
**Date:** November 2026  

---

## 1. Principles of Event Design

1. **Zero Personal Data:** In accordance with GDPR and FERPA privacy standards, event topics and data parameters contain zero subject personal information (names, grades, dates of birth).
2. **Sub-Graph & Indexer Friendly:** All primary identifiers (`issuer`, `credentialId`, `signingKey`) are indexed to allow performant WebSocket filtering and sub-graph synchronization.

---

## 2. Event Signatures

### `IssuerRegistry.sol`
- `event IssuerRegistered(address indexed issuer, IssuerRole role, string metadataURI)`
  - Emitted when an institution is accredited.
- `event IssuerAuthorized(address indexed issuer, IssuerRole role)`
  - Emitted when an issuer's tier is updated or active status established.
- `event IssuerSuspended(address indexed issuer)`
  - Emitted when an institution is placed on temporary administrative hold.
- `event IssuerReinstated(address indexed issuer)`
  - Emitted when an institution is returned to good standing.
- `event IssuerRevoked(address indexed issuer)`
  - Emitted when an institution's accreditation is permanently terminated.
- `event SigningKeyRegistered(address indexed issuer, address indexed signingKey, uint256 validUntil)`
  - Emitted when an operational key is authorized.
- `event SigningKeyRevoked(address indexed issuer, address indexed signingKey)`
  - Emitted when an operational key is deauthorized.

### `CredentialRegistry.sol`
- `event CredentialRegistered(bytes32 indexed credentialId, bytes32 indexed commitment, address indexed issuer, uint256 timestamp)`
  - Emitted when a salted commitment is anchored on-chain.

### `CredentialStatusRegistry.sol`
- `event CredentialStatusChanged(bytes32 indexed credentialId, CredentialStatus indexed previousStatus, CredentialStatus indexed newStatus, address updatedBy, string reason)`
  - Emitted when credential status transitions (`Active` $\leftrightarrow$ `Suspended` $\rightarrow$ `Revoked`).
