# Phase 0: Initial Project Audit

**Project:** DecentralID  
**Date:** November 2026  
**Auditor:** Automated Trust & Security Engineering Pipeline  
**Repository Baseline:** https://github.com/MeenalSinha/DecentralID (Commit `dfe9bfd`)

---

## 1. Executive Summary

DecentralID was initiated as a hackathon/demonstration prototype combining an Ethereum smart contract (`IdentityReputation.sol`) and a monolithic React frontend (`frontend/src/App.jsx`).

While the repository provides a compelling conceptual vision of decentralized identity and reputation, the initial code inspection reveals that it is not yet a secure, production-grade verifiable credential infrastructure. Several critical security vulnerabilities, architectural defects, and mock implementations were uncovered:

1. **Exposed Third-Party Credentials:** Hardcoded Pinata API keys were directly embedded into client-side JavaScript (`frontend/src/App.jsx`).
2. **Fabricated Fallback Data (Fake IPFS Hashes):** When IPFS upload requests fail, the application generates a pseudo-random hash (`Qm...`) and reports a successful upload.
3. **Sham Verifiable Credentials:** The exported "Verifiable Credential" JSON asserts compliance with `EthereumEip712Signature2021`, but contains no cryptographic signature whatsoever—only a raw transaction hash and block number.
4. **Superficial Verification:** The verification tab performs no cryptographic signature check, issuer authorization check, or revocation check; it merely fetches public JSON from IPFS if an identity exists.
5. **Vulnerable Smart Contract Logic:**
   - **Reputation Manipulation:** Any identity can mint unlimited endorsements for another identity, trivially inflating reputation scores to 100%.
   - **Misleading Sybil Resistance:** Wallet age is computed from the contract's `createdAt` timestamp rather than independent on-chain wallet history.
   - **Unbounded Gas Loops:** Array iteration over all user endorsements in view functions poses gas and scaling limits.
6. **Inconsistent Contract Deployments:** Discrepancies exist between `.env.example`, `frontend/src/App.jsx`, and `deployments/sepolia-deployment.json`.
7. **Complete Absence of Automated Tests and Backend:** Zero automated tests were present; no backend server existed.

---

## 2. Repository Inventory

The codebase at audit start comprises the following 17 tracked files:

| Path | Language / Type | Size | Purpose / Observations |
|---|---|---|---|
| `contracts/IdentityReputation.sol` | Solidity 0.8.19 | 11,831 B | Core smart contract implementing identity, reputation, endorsements, and basic issuer verification. |
| `frontend/src/App.jsx` | React (JSX) | 104,811 B (2,312 lines) | Monolithic frontend containing all UI components, wallet connection, mock VC generation, and IPFS calls. |
| `frontend/src/main.jsx` | React (JSX) | 243 B | React entry point mounting `App.jsx`. |
| `frontend/src/index.css` | CSS | 60 B | Tailwind directives. |
| `frontend/src/abi/IdentityReputation.json` | JSON | 44,060 B | Contract ABI copied from Hardhat compilation artifacts. |
| `frontend/package.json` | JSON | 840 B | Frontend dependencies (React 18, Vite 5, Tailwind 3, ethers 6.16). |
| `frontend/vite.config.js` | JavaScript | 279 B | Vite configuration. |
| `frontend/tailwind.config.js` | JavaScript | 191 B | Tailwind configuration. |
| `frontend/postcss.config.js` | JavaScript | 84 B | PostCSS configuration. |
| `frontend/index.html` | HTML | 533 B | HTML root. |
| `hardhat.config.js` | JavaScript | 1,559 B | Hardhat configuration for Sepolia, Mumbai, and local networks. |
| `package.json` | JSON | 1,919 B | Root dependencies (Hardhat 2.19, OpenZeppelin 5.0.1, ethers 6.9). |
| `scripts/deploy.js` | JavaScript | 5,111 B | Deployment script deploying `IdentityReputation` and writing deployment JSON. |
| `deployments/sepolia-deployment.json` | JSON | 255 B | Historical Sepolia deployment record (`0x4F9b33C607e54A8b87023ce4d837431F682E88e4`). |
| `.env.example` | Config | 3,224 B | Sample configuration containing malformed address `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb`. |
| `.gitignore` | Git | 702 B | Git ignore rules. |
| `LICENSE` | Text | 1,089 B | MIT License. |
| `README.md` | Markdown | 10,168 B | Project documentation. |

---

## 3. Preliminary Risk Classification

| Risk Area | Severity | Impact |
|---|---|---|
| Client-Exposed API Keys | Critical | Unauthorized third parties can hijack Pinata storage quota and upload malicious content. |
| Fake IPFS Hash Generation | Critical | Data loss and fraudulent claims of persistent storage. |
| Unsigned "Verifiable" Credentials | High | Zero cryptographic guarantee of credential integrity or issuer provenance. |
| Sybil / Reputation Gameability | High | Trivial inflation of reputation scores removes trust in ratings. |
| Address Inconsistencies | Medium | Confusion over active contract deployments across environments. |
| Lack of Automated Tests | High | High risk of undetected regressions and security vulnerabilities. |
