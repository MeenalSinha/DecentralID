# Authentication Design Specification (EIP-4361 SIWE)

**Project:** DecentralID  
**Date:** November 2026  
**Implementation:** `backend/app/services/authentication_service.py` & `wallet_verification_service.py`  

---

## 1. Cryptographic Challenge-Response Protocol

DecentralID authenticates all individual holders and institutional operators using EIP-4361 Sign-In with Ethereum (SIWE):

```mermaid
sequenceDiagram
    autonumber
    actor User as Wallet Owner
    participant FE as Frontend Client
    participant API as FastAPI Backend
    participant DB as PostgreSQL

    User->>FE: Click "Connect Wallet"
    FE->>API: POST /api/v1/authentication/challenge (address, chainId, domain)
    API->>API: Generate 16-byte random hex nonce (32 chars)
    API->>API: Compute expiration (issued_at + 300 seconds)
    API->>DB: Store AuthChallenge (is_used=false)
    API-->>FE: Return EIP-4361 standard formatted message & nonce

    User->>FE: Inspect & sign message in MetaMask (personal_sign)
    FE->>API: POST /api/v1/authentication/verify-wallet (address, nonce, signature)
    
    API->>DB: Fetch AuthChallenge by nonce & address
    alt Nonce missing or expired
        API-->>FE: 401 NonceExpiredOrInvalidException
    else Nonce already consumed (is_used=true)
        API-->>FE: 401 ReplayAttackDetected
    else Valid & Active
        API->>DB: Mark AuthChallenge.is_used = true (Atomic consumption)
        API->>API: Reconstruct standard message
        API->>API: Recover address from signature via ECDSA secp256k1
        alt Recovered address != claimed address
            API-->>FE: 401 InvalidSignatureException
        else Signature Matches
            API->>DB: Get or create User & Wallet
            API->>DB: Generate 32-byte secure session token & insert Session
            API-->>FE: 200 OK + Set-Cookie: decentralid_session (HTTP-only)
        end
    end
```

---

## 2. Replay & Expiration Defenses
1. **Atomic Nonce Invalidation:** Nonces are consumed upon first evaluation. Even if an attacker intercepts a signature, resubmission results in immediate rejection (`401 Unauthorized`).
2. **Short-Lived Challenges:** Nonce time-to-live is enforced at 300 seconds (5 minutes). Stale challenges cannot be activated.
3. **Domain & URI Binding:** Messages include the host domain (`domain: localhost`) and origin URI (`uri: http://localhost:5173`), preventing phishing relay across rogue origins.
