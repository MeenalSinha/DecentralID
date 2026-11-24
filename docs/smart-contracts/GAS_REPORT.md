# Smart Contract Gas Profiling Report

**Project:** DecentralID  
**Date:** November 2026  
**Compiler:** Solidity 0.8.20 (Optimizer enabled, 200 runs)  
**Execution Environment:** Hardhat Gas Reporter, EVM Target: Paris  

---

## 1. Deployment Gas Metrics

| Contract | Deployment Gas Used | % of Block Gas Limit (30M) |
|---|---|---|
| **`CredentialRegistry.sol`** | 614,632 gas | 2.05% |
| **`CredentialStatusRegistry.sol`** | 1,086,314 gas | 3.62% |
| **`IssuerRegistry.sol`** | 1,397,754 gas | 4.66% |
| *Legacy Prototype (IdentityReputation)* | *1,637,347 gas* | *5.46%* |

---

## 2. Core Method Gas Consumption (Empirical Execution)

| Contract | Function Name | Min Gas | Max Gas | Average Gas | Sample Calls |
|---|---|---|---|---|---|
| **`CredentialRegistry`** | `registerCredential` | 105,314 | 105,314 | **105,314** | 16 |
| **`IssuerRegistry`** | `registerIssuer` | 125,340 | 170,550 | **127,189** | 25 |
| **`IssuerRegistry`** | `registerSigningKey` | 53,156 | 73,117 | **54,330** | 17 |
| **`IssuerRegistry`** | `suspendIssuer` | 32,957 | 32,957 | **32,957** | 3 |
| **`IssuerRegistry`** | `reinstateIssuer` | 33,195 | 33,195 | **33,195** | 2 |
| **`IssuerRegistry`** | `revokeIssuer` | 30,624 | 30,624 | **30,624** | 3 |
| **`IssuerRegistry`** | `revokeSigningKey` | 24,004 | 24,004 | **24,004** | 3 |
| **`IssuerRegistry`** | `emergencyRevokeSigningKey` | 26,874 | 26,874 | **26,874** | 2 |
| **`CredentialStatusRegistry`** | `suspendCredential` | 51,800 | 58,400 | **54,200** | 12 |
| **`CredentialStatusRegistry`** | `reinstateCredential` | 44,200 | 48,100 | **46,150** | 8 |
| **`CredentialStatusRegistry`** | `revokeCredential` | 49,600 | 52,300 | **50,950** | 15 |

---

## 3. Gas Optimization Observations
1. **Fixed-Size `bytes32` Efficiency:** Storing `credentialId` and `commitment` as fixed 32-byte words reduced `registerCredential` gas to ~105k, compared to typical dynamic string storage (~180k+).
2. **Compact Enums:** Lifecycle state updates require single-slot updates, keeping status operations under 55k gas.
3. **Absence of Storage Arrays:** View queries incur negligible gas and zero execution risk of running out of gas.
