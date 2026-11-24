# CredentialRegistry Contract Specification

**Contract:** `contracts/CredentialRegistry.sol`  
**Dependencies:** `contracts/interfaces/IIssuerRegistry.sol`  
**Solidity:** `^0.8.20`  

---

## 1. Contract Overview
Acts as the immutable on-chain reference and integrity layer for privacy-preserving verifiable credentials.

---

## 2. Commitment Scheme

Rather than storing plain text attributes or predictable hashes, `CredentialRegistry` records:

$$C = \text{keccak256}(\text{canonicalJSON}(S) \mathbin{\Vert} \text{salt})$$

Where:
- $S$ is the credential subject claims object.
- $\text{salt}$ is a 32-byte cryptographically secure random value.
- $C$ is a 32-byte commitment.

---

## 3. Function Interface

### `registerCredential`
```solidity
function registerCredential(
    bytes32 credentialId,
    bytes32 commitment,
    address issuer
) external whenNotPaused;
```
- **Validation Checks:**
  1. `credentialId != bytes32(0)` & `commitment != bytes32(0)`.
  2. Uniqueness: `_credentials[credentialId].issuedAt == 0`.
  3. Issuer Authorization: `issuerRegistry.isIssuerAuthorized(issuer) == true`.
  4. Caller Authority: `issuerRegistry.isSigningKeyValid(issuer, msg.sender) == true`.
- **State Changes:** Records `CredentialRecord(commitment, issuer, block.timestamp)`.
- **Emits:** `CredentialRegistered(credentialId, commitment, issuer, timestamp)`.

### Query Methods
- `getCredential(bytes32 credentialId) external view returns (bytes32 commitment, address issuer, uint256 issuedAt)`
- `credentialExists(bytes32 credentialId) external view returns (bool)`
