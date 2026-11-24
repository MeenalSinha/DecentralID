# Phase 0: Existing Feature Inventory

**Project:** DecentralID  
**Date:** November 2026  

Every feature in the repository has been evaluated against source code behavior and classified into one of the eight standard lifecycle states.

---

## 1. Feature Classification Matrix

| Feature | Category | Source Location | Actual Behavior & Findings |
|---|---|---|---|
| **Identity Creation (Smart Contract)** | Implemented but requires improvement | `contracts/IdentityReputation.sol:102` | Stores IPFS hash, sets timestamp and reputation to 0. Emits event. Stores plain text IPFS hash of unencrypted profile. |
| **Identity Retrieval (Smart Contract)** | Fully implemented and verified | `contracts/IdentityReputation.sol:146` | Returns 6-tuple: IPFS hash, reputation, timestamps, count, existence. |
| **Endorsement Minting (Smart Contract)** | Insecure and requiring replacement | `contracts/IdentityReputation.sol:172` | Allows unrestricted repeated endorsements between identical addresses. Reputation can be spammed to 100 with zero cost or cooldown. |
| **Issuer Verification (Smart Contract)** | Partially implemented | `contracts/IdentityReputation.sol:231` | Centralized `onlyOwner` can flag an address as verified and assign an enum role. No multisig, no institutional registry, no cryptographic signing key management. |
| **Sybil Resistance Calculation** | Broken / Misleading | `contracts/IdentityReputation.sol:294` | `walletAge` relies on contract registration timestamp (`createdAt`), not wallet transaction history. Easily spoofed. |
| **Endorsement Breakdown Query** | Implemented but requires improvement | `contracts/IdentityReputation.sol:256` | Loops over unbounded dynamic storage array `userEndorsements`, subject to potential gas limits. |
| **MetaMask Wallet Connection** | Fully implemented and verified | `frontend/src/App.jsx:32` | Standard `window.ethereum` detection, `eth_requestAccounts`, event listeners for `accountsChanged` and `chainChanged`. |
| **Contract Initialization** | Hardcoded | `frontend/src/App.jsx:20, 106` | Hardcodes contract address `0xeB75C0d729AB514f4887440AA45BAc23F9fF1f89`. No runtime configuration or backend provider. |
| **IPFS Profile Upload** | Insecure and requiring replacement | `frontend/src/App.jsx:116` | Embedded client-side Pinata API key and secret. Fallback returns fake `Qm...` hash on failure. |
| **IPFS Profile Retrieval** | Implemented but requires improvement | `frontend/src/App.jsx:138` | Fetches JSON via public Pinata gateway. No schema validation, no decryption, no fallback gateways. |
| **Verifiable Credential Download** | Simulated or mocked | `frontend/src/App.jsx:600` | Generates a JSON file claiming to be an `EthereumEip712Signature2021` verifiable credential, but contains no signature or proof cryptographic data. |
| **Verification Tab / Flow** | Simulated or mocked | `frontend/src/App.jsx:1478` | Resolves IPFS profile data from address via smart contract. Does not perform signature verification, issuer validity check, or revocation check. |
| **Endorsement Submission UI** | Implemented but requires improvement | `frontend/src/App.jsx:148` | Calls `mintEndorsement` on contract. Does not enforce server-side validation or prevent duplicate endorsement spam. |
| **Institutional Issuer Dashboard** | Not implemented | None | No institutional credential creation, template management, or issuance portal exists. |
| **Cryptographic Credential Revocation** | Not implemented | None | No on-chain revocation registry, bitstring status list, or revocation management exists. |
| **Backend API Services** | Not implemented | None | No backend server, authentication API, database, or proxy services existed in the repository. |
| **Automated Test Suite** | Not implemented | None | No tests existed in `test/` or `frontend/`. |

---

## 2. Summary Breakdown

- **Fully implemented and verified:** 2
- **Implemented but requires improvement:** 4
- **Partially implemented:** 1
- **Broken / Misleading:** 1
- **Simulated or mocked:** 2
- **Hardcoded:** 1
- **Insecure and requiring replacement:** 2
- **Not implemented:** 4
