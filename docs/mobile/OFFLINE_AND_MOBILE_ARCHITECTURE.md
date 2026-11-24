# DecentralID: Mobile PWA, Encrypted Vault & Offline Verification Architecture (Phase 16)

## 1. Overview and Objectives

Phase 16 transforms the DecentralID holder experience into an installable, mobile-responsive Progressive Web Application (PWA) with client-side encrypted credential storage and offline cryptographic verification capabilities.

---

## 2. Progressive Web Application Architecture

1. **Web App Manifest (`frontend/public/manifest.json`):**
   - Configured with `display: standalone`, mobile orientations, theme color `#1e293b`.
2. **Service Worker (`frontend/public/sw.js`):**
   - Implements cache-first strategy for UI static application shell (`index.html`, assets).
   - **STRICT SECURITY RULE:** Service worker explicitly bypasses `/api/` network requests to prevent caching sensitive authenticated credentials or private personal data in browser caches.

---

## 3. Client-Side Encrypted Local Vault (`LocalVaultService`)

- **Web Crypto API Standard:**
  - Key derivation: PBKDF2 with 100,000 iterations of SHA-256 and a 128-bit CSPRNG salt.
  - Encryption cipher: AES-256-GCM with 96-bit unique IV and 128-bit authentication tag.
- **Data Protection:**
  - Raw credentials are never stored in plaintext `localStorage`.
  - Credentials remain encrypted in client-side storage and are only decrypted into transient memory upon explicit holder passphrase entry.
  - Supports portable encrypted backup export and import with integrity checks.

---

## 4. Offline Verification & The Critical Freshness Rule

Offline verification enables verification in connectivity-constrained settings (e.g., transit gates, field audits, offline recruitment checks).

### The Critical Freshness Rule
Offline verification **cannot guarantee** that a credential has not been revoked or suspended after the last synchronization event.

Therefore, the engine enforces:
1. **Time-Bounded Status Snapshots:** Every offline package includes an authority-signed status snapshot timestamp (`snapshot_timestamp`).
2. **Maximum Permitted Offline Age:** The verifier configures a maximum allowable age window (`max_offline_age_seconds`, default 86,400 seconds / 24 hours).
3. **Mandatory INDETERMINATE State:**
   - If the status snapshot is older than the configured window: the engine strictly returns `status = "INDETERMINATE"`.
   - **Under no circumstances does DecentralID convert a stale offline status into a definitive VALID result.**
   - The verifier is notified that re-synchronization is required for definitive validity determination.
