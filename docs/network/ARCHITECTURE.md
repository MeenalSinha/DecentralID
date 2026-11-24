# DecentralID Network Architecture: Encrypted Storage, Developer APIs, SDK & Webhooks

**Specification Version:** 1.0.0 (Phase 12 Architecture)  
**Status:** Active / Production-Ready  
**Components:** Encrypted Content-Addressed Storage (IPFS), Developer Network APIs, TypeScript SDK, Webhook Event Engine

---

## 1. Architecture Overview

DecentralID Network opens the decentralized trust infrastructure to external ecosystems, third-party verifiers, institutional portals, and developer applications while preserving zero-knowledge privacy and data ownership:

```
+---------------------------------------------------------------------------------------------+
|                                     DecentralID Network                                      |
+---------------------------------------------------------------------------------------------+
               |                                     |                                   |
               v                                     v                                   v
+-------------------------------+   +---------------------------------+   +--------------------+
|  Encrypted IPFS Storage        |   |  Developer Platform APIs        |   | Webhook Dispatcher |
|  - AES-256-GCM Payload Cipher  |   |  - POST /api/v1/network/verify  |   | - HMAC-SHA256 Sig  |
|  - Deterministic CIDv1 Hashes  |   |  - GET  /network/issuers/{addr} |   | - Replay Defense   |
|  - Pinata / Local Block Store  |   |  - GET  /network/creds/{id}/stat|   | - Auto Retries     |
+-------------------------------+   +---------------------------------+   +--------------------+
               ^                                     ^                                   |
               |                                     |                                   v
+---------------------------------------------------------------------+           +------------+
|                  Official TypeScript Developer SDK                  |           | Verifier / |
|                  `@decentralid/sdk` (Node / Browser)                |---------->| Employer   |
+---------------------------------------------------------------------+           | Webhook End|
                                                                                  +------------+
```

---

## 2. Encrypted Content-Addressed Storage (IPFS)

### 2.1 Threat Model & Security Posture
Storing credentials on public decentralized networks (such as IPFS or Filecoin) without strong encryption exposes sensitive Personal Identifiable Information (PII) to irreversible public archiving.
DecentralID mitigates this risk by enforcing client/service-side **AES-256-GCM authenticated encryption** prior to content addressing.

### 2.2 Cipher Specification
- **Algorithm**: AES-256-GCM (`cryptography.hazmat.primitives.ciphers.aead.AESGCM`).
- **Nonce**: 96-bit CSPRNG (`os.urandom(12)`).
- **Authentication Tag**: 128-bit authentication tag appended directly to ciphertext.
- **Envelope Format**: `Nonce (12B) || Ciphertext (variable) || AuthTag (16B)`.

### 2.3 Deterministic CIDv1 Derivation
The content address matches the standard IPFS CIDv1 raw multihash specification:
- Version: `0x01`
- Multicodec: `0x55` (raw binary)
- Hash Function: `0x12` (SHA-256)
- Length: `0x20` (32 bytes)
- Encoding: Base32 with multibase prefix `'b'` (e.g. `bafkrei...`).

---

## 3. Developer APIs & API Key Governance

### 3.1 Authentication & Scopes
External consumers authenticate via the `X-API-Key` HTTP header.
- **Key Format**: `did_live_<32-byte-base64-random-token>`
- **Storage**: Keys are stored hashed with SHA-256. Raw secret keys are revealed strictly once upon creation.
- **Granular Scopes**:
  - `verify`: Submit Verifiable Presentations/Credentials for cryptographic audit.
  - `status`: Check issuer registration and credential revocation status.
  - `storage`: Upload encrypted blocks to network storage.
- **Tenant Isolation**: Each API key is bound to a specific `organization_id` and cannot access cross-tenant records.

### 3.2 Endpoints Summary
| Endpoint | Method | Scope | Description |
|---|---|---|---|
| `/api/v1/network/verify` | POST | `verify` | Cryptographically verify credentials or presentations |
| `/api/v1/network/issuers/{address}` | GET | `status` | Query issuer authorization and active signing keys |
| `/api/v1/network/credentials/{id}/status` | GET | `status` | Query credential commitment and revocation status |
| `/api/v1/network/storage/encrypt-and-store` | POST | `storage` | Store encrypted JSON in content-addressed storage |
| `/api/v1/network/api-keys` | POST/GET | Admin | Manage institutional developer API keys |

---

## 4. Webhook Dispatcher & Replay Defense

### 4.1 Signature Header Specification
All webhook events are signed using HMAC-SHA256 and dispatched with:
```http
X-DecentralID-Event: credential.issued
X-DecentralID-Signature: t=1732435200,v1=5d41402abc4b2a76b9719d911017c592
```

### 4.2 Signature Verification Formula
$$\text{signedPayload} = \text{str}(t) \parallel "." \parallel \text{rawJsonBody}$$
$$\text{v1} = \text{HMAC-SHA256}(\text{secretKey}, \text{signedPayload})$$

### 4.3 Replay Protection
Verifiers must verify that $| \text{currentTime} - t | \le 300\text{ seconds}$ before accepting the payload.

---

## 5. TypeScript Developer SDK (`@decentralid/sdk`)

The SDK provides idiomatic TypeScript bindings for Node.js and modern browsers:

```typescript
import { DecentralIDClient } from "@decentralid/sdk";

const client = new DecentralIDClient({
  baseUrl: "https://api.decentralid.org",
  apiKey: "did_live_...",
});

// Verify a presentation
const result = await client.verifyPresentation(presentationPayload);
if (result.outcome === "VALID") {
  console.log("Verified Issuer:", result.issuer_address);
}

// Verify webhook signature
const isValidWebhook = DecentralIDClient.verifyWebhookSignature(
  req.rawBody,
  req.headers["x-decentralid-signature"],
  process.env.DECENTRALID_WEBHOOK_SECRET!
);
```
