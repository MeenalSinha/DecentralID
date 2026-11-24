# Smart Contract Deployment Guide

**Project:** DecentralID  
**Date:** November 2026  
**Script:** `scripts/deploy/deploy_registries.js`  

---

## 1. Local Deployment (Hardhat)

```bash
npx hardhat run scripts/deploy/deploy_registries.js --network hardhat
```

### Execution Output:
1. Deploys `IssuerRegistry.sol`.
2. Deploys `CredentialRegistry.sol` (injecting `IssuerRegistry` address).
3. Deploys `CredentialStatusRegistry.sol` (injecting both registry addresses).
4. Generates standardized deployment manifest: `deployments/local/manifest.json`.
5. Executes automated post-deployment smoke verification checks.

---

## 2. Sepolia Testnet Deployment

### Prerequisites:
1. Valid `.env` configuration:
   ```ini
   PRIVATE_KEY=0x...
   SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_KEY
   ETHERSCAN_API_KEY=YOUR_ETHERSCAN_KEY
   ```
2. Deployer wallet funded with Sepolia testnet ETH.

### Execution:
```bash
npx hardhat run scripts/deploy/deploy_registries.js --network sepolia
```

Deployment metadata is automatically written to `deployments/sepolia/manifest.json`, and backend services immediately consume the new addresses on restart without requiring source code modification.
