# Session Security & Cookie Protection

**Project:** DecentralID  
**Date:** November 2026  

---

## 1. Session Storage & Lifecycle

DecentralID rejects client-side storage of JWT tokens in browser `localStorage` or `sessionStorage` due to high vulnerability to Cross-Site Scripting (XSS) credential theft.

Instead, the system utilizes **Server-Side Session Storage with HTTP-Only Cookies**:

| Property | Configuration | Security Purpose |
|---|---|---|
| **Cookie Name** | `decentralid_session` | Standard session identifier. |
| **HttpOnly** | `True` | Prevents malicious JavaScript / XSS scripts from reading the session token. |
| **Secure** | `True` (Production) / `False` (Dev) | Restricts cookie transmission strictly to encrypted HTTPS connections. |
| **SameSite** | `Lax` (Default) or `Strict` | Defends against Cross-Site Request Forgery (CSRF) attacks. |
| **Path** | `/` | Session cookie valid across application paths. |
| **Max-Age** | 86,400 seconds (24 hours) | Automatic session expiry. |

---

## 2. Invalidation & Account Switching

1. **Explicit Logout:** Calling `POST /api/v1/authentication/logout` immediately marks the session row in PostgreSQL as `is_revoked = True` and sets the cookie expiration to `0`.
2. **Account Switching:** When a user switches wallets in MetaMask (`accountsChanged`), the frontend prompts the user to either authenticate the new wallet via SIWE or disconnects the previous session, preventing accidental session hijacking across accounts.
