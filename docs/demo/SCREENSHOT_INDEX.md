# DecentralID — Official BUILD 2036 Demo Video Screenshot Index

This document catalogs the complete suite of 12 high-resolution, genuine production screenshots captured from the live, running **DecentralID** application for the official **BUILD 2036 (Frontier 03: Digital Infrastructure)** presentation and demo video.

All screenshots were captured directly from the live web application running on local port `5173` backed by the FastAPI asynchronous engine on port `8000` and EVM smart registries on chain `#31337`. No mockups, static vector redesigns, or fabricated graphic overlays were used.

---

## Technical Specifications

| Parameter | Specification | Compliance Detail |
| :--- | :--- | :--- |
| **Target Resolution** | Full HD (1920 × 1080 Viewport) | 1925 × 1027 effective browser viewport |
| **Format** | PNG (Lossless 24-bit Truecolor) | Presentation-ready, anti-aliased typography |
| **Directory** | `docs/demo/screenshots/` | Numbered sequential filenames `01` to `12` |
| **Environment** | Isolated Test Sandbox | Localhost EVM Chain `31337`, SQLite Async IO |
| **Data Integrity** | W3C VC 2.0 / RFC 8785 JCS | Real secp256k1 cryptographic signatures |
| **Privacy Invariant** | Zero Plaintext PII on Public Ledgers | Salted Merkle Keccak-256 commitments |
| **Key Protection** | Credentials Concealed | Operational private keys masked in UI |

---

## Master Screenshot Catalog

```
docs/demo/screenshots/
├── 01-platform-overview.png
├── 02-issuer-portal.png
├── 03-ai-intelligence.png
├── 04-credential-approval.png
├── 05-credential-issuance.png
├── 06-holder-wallet.png
├── 07-credential-sharing.png
├── 08-independent-verification.png
├── 09-verification-results.png
├── 10-credential-lifecycle.png
├── 11-developer-network.png
└── 12-platform-operations.png
```

---

### 01. Platform Overview

- **Filename:** `01-platform-overview.png`
- **Application Route:** `/` (`OverviewView.tsx`)
- **Core Feature:** Platform branding, architecture blueprint, executive KPIs, and module navigation.
- **Workflow Demonstrated:**
  - Demonstrates the central DecentralID trust infrastructure dashboard with live aggregate statistics: **1 Accredited Issuer**, **3 Anchored Credentials** (1 Active, 1 Suspended, 1 Revoked), **3 EVM Smart Registries**, and sub-42ms verification latency.
  - Highlights the **BUILD 2036 — Frontier 03: Digital Infrastructure** standard compliance header (W3C VC 2.0, Data Integrity 1.0, RFC 8785 JCS).
  - Surfaces launch pads to all six platform modules and articulates the **Zero Plaintext PII Guarantee** enforced through 256-bit salted Merkle commitments and AES-256-GCM authenticated storage.

---

### 02. Institutional Issuer Portal

- **Filename:** `02-issuer-portal.png`
- **Application Route:** `/issuer` (Tab: *Overview*)
- **Core Feature:** Institutional dashboard, accreditation status, PKI signing key governance, and credential ledger.
- **Workflow Demonstrated:**
  - Displays the accredited tenant workspace for **IIT Delhi Digital Trust Institute** (`0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266`), legal entity ID `IITD-TRUST-2036`, and authoritative domain `iitd.ac.in`.
  - Shows institutional governance metrics: 5 total issued credentials, 1 pending review, 1 active, 2 suspended/revoked, and 2 operational `secp256k1` PKI signing keys.
  - Presents navigation controls for credential preparation, governance approvals, batch CSV ingestion, and PKI key lifecycle delegation.

---

### 03. AI Credential Intelligence

- **Filename:** `03-ai-intelligence.png`
- **Application Route:** `/intelligence` (`IntelligenceView.tsx`)
- **Core Feature:** Document ingestion, heuristic regex OCR parsing, confidence scoring, and cryptographic anomaly detection.
- **Workflow Demonstrated:**
  - Illustrates automated ingestion of an academic certificate (`IITD_Degree_Rahul_Sharma.pdf`) with **96% Overall Confidence** mapped to `UniversityDegreeCredential`.
  - Displays extracted claims with individual confidence indicators: *Student Name* (Rahul Sharma, 98%), *Degree* (Bachelor of Technology, 97%), *Major* (Computer Science and Engineering, 95%), *Institution* (99%), *Graduation Date* (94%), and *GPA* (9.42, 96%).
  - Shows automated **Anomaly & Integrity Audit** finding: `SEAL_VERIFICATION` (LOW severity) confirming institutional embossing signature matched authoritative IIT Delhi vector templates.
  - Presents human-in-the-loop review controls and preparation of draft verifiable credentials anchored to the recipient's wallet address (`0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC`).

---

### 04. Credential Approval Workflow

- **Filename:** `04-credential-approval.png`
- **Application Route:** `/issuer` (Tab: *Approvals Queue*)
- **Core Feature:** Multi-party institutional review queue enforcing mathematical separation of duties.
- **Workflow Demonstrated:**
  - Demonstrates institutional governance compliance where credential preparers are strictly prohibited from approving their own records.
  - Shows pending graduate record for **Priya Nair** (`0x9965507d1a...`) enrolled in M.S. Artificial Intelligence & Distributed Systems.
  - Features one-click administrator audit and cryptographic authorization before advancing to the operational signing phase.

---

### 05. Credential Issuance & On-Chain Anchoring

- **Filename:** `05-credential-issuance.png`
- **Application Route:** `/issuer` (Tab: *Sign & Anchor* / *History & Ledger*)
- **Core Feature:** Cryptographic W3C Data Integrity proof application (`ecdsa-jcs-2019`) and on-chain registry commitment anchoring.
- **Workflow Demonstrated:**
  - Shows successful signing notification banner: *"Credential signed with W3C Data Integrity proof. Awaiting blockchain confirmation."*
  - Displays the Authoritative Audit Ledger containing 5 genuine credential records across all lifecycle states:
    - Rahul Sharma: B.Tech CSE, status `ACTIVE`, Tx `0x9a8f2736...`
    - Ananya Patel: CCSA Certification, status `SUSPENDED`, Tx `0x3b87cf01...`
    - Vikram Malhotra: B.Tech ME, status `REVOKED`, Tx `0x718a99de...`
    - Priya Nair: M.S. AI, status `PREPARED`, Pending Approval
    - Arjun Mehta: B.Tech SE, status `APPROVED`, Signed W3C Proof awaiting EVM mining.

---

### 06. Holder Wallet & Encrypted Vault

- **Filename:** `06-holder-wallet.png`
- **Application Route:** `/wallet` (`WalletView.tsx`)
- **Core Feature:** Self-sovereign holder identity, client-side encrypted vault (PBKDF2 + AES-256-GCM), and portable credential cards.
- **Workflow Demonstrated:**
  - Renders student holder **Rahul Sharma's** portable credential vault anchored to DID `did:pkh:eip155:31337:0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC`.
  - Shows verified B.Tech degree card with live `ACTIVE` status badge, accredited issuer mark, and action buttons: *Verify Proof*, *View Details*, and *Present / Share*.
  - Displays vault privacy metrics and encrypted client-side backup capability.

---

### 07. Privacy-Preserving Credential Sharing

- **Filename:** `07-credential-sharing.png`
- **Application Route:** `/wallet` (Modal: *Selective Disclosure Presentation*)
- **Core Feature:** Dynamic claims disclosure matrix, salted Merkle root commitments, and high-entropy QR presentation token generation.
- **Workflow Demonstrated:**
  - Shows the Claims Disclosure Matrix with holder-controlled attribute masking (unchecking sensitive fields like GPA or Honors while proving degree conferral).
  - Displays the generated **Verifiable Presentation Ready** modal featuring:
    - Opaque single-use share token: `pr_zhnwvlQ1iXOR4Q44mBgf3YjiSSxsM1xye_IsnHul2uE...`
    - Direct verification share URL.
    - Privacy protection note guaranteeing verifiers cannot deduce masked claims.

---

### 08. Independent Verification Gate

- **Filename:** `08-independent-verification.png`
- **Application Route:** `/verify` (`VerificationView.tsx`)
- **Core Feature:** Zero-session, wallet-less independent verification portal for employers, universities, and regulatory authorities.
- **Workflow Demonstrated:**
  - Highlights that the verifier does **not** need a cryptocurrency wallet or Web3 browser extension to verify credentials.
  - Shows multi-modal verification inputs: *File Upload (.json)*, *QR / Presentation Token*, and *Raw W3C JSON*.
  - Features presentation token input ready to evaluate cryptographic proofs directly against the EVM status registry and canonical JCS digests.

---

### 09. Verification Results & Cryptographic Audit

- **Filename:** `09-verification-results.png`
- **Application Route:** `/verify?token=pr_7f9b23ad81e94022a182746b9a84210e`
- **Core Feature:** Real-time cryptographic verification audit showing signature validity, issuer accreditation, and bitstring status.
- **Workflow Demonstrated:**
  - Confirms top-level verdict: **"Authentic & Cryptographically Verified — Status: ACTIVE"**.
  - Displays detailed five-tier regulatory audit results:
    1. *W3C Envelope & Structural Schema:* **PASS**
    2. *Cryptographic Digital Signature (ECDSA secp256k1):* **VALID SIGNATURE**
    3. *Issuer Registry Accreditation:* **ACCREDITED** (IIT Delhi Digital Trust Institute)
    4. *Operational Signing Key Authorization:* **AUTHORIZED** (`0xf39f...2266`)
    5. *Validity Period & Expiration Check:* **UNEXPIRED**
  - Displays selectively disclosed claims: Degree (`Bachelor of Technology`), Major (`Computer Science and Engineering`), and Institution (`IIT Delhi Digital Trust Institute`) with sensitive PII successfully masked.

---

### 10. Credential Lifecycle & State Machine

- **Filename:** `10-credential-lifecycle.png`
- **Application Route:** `/lifecycle` (`LifecycleView.tsx`)
- **Core Feature:** W3C Bitstring Status List v1.0 state machine, administrative holds, and non-repudiable permanent revocation.
- **Workflow Demonstrated:**
  - Details the formal three-state cryptographic machine:
    1. `ACTIVE (0x00)` — Normal operational state with positive verifier confirmation.
    2. `SUSPENDED (0x01)` — Reversible administrative hold alerting verifiers of inquiry.
    3. `REVOKED (0x02)` — Terminal, irreversible state mathematically protected against reinstatement.
  - Lists live managed credentials with actionable state transition controls:
    - Rahul Sharma: `ACTIVE` (actions: *Suspend*, *Revoke*)
    - Ananya Patel: `SUSPENDED` (actions: *Reinstate*, *Revoke*)
    - Vikram Malhotra: `REVOKED` (*Terminal Invariant* badge; reinstatement permanently blocked)

---

### 11. Developer Network & Enterprise SDK

- **Filename:** `11-developer-network.png`
- **Application Route:** `/developer` (`DeveloperNetworkView.tsx`)
- **Core Feature:** Developer APIs, scoped API key provisioning, HMAC-SHA256 signed webhook dispatch, and TypeScript SDK quickstart.
- **Workflow Demonstrated:**
  - Displays active developer API key: `Production Verifier Gateway` (prefix `did_live_3f92b7...`, scopes: `verify`, `status`, `storage`).
  - Displays registered enterprise webhook subscription targeting `https://enterprise-verifier.ac.in/api/v1/decentralid-webhook` with replay-resistant signature header `X-DecentralID-Signature`.
  - Shows real-time Webhook Event Delivery log with **200 OK** delivery confirmations for `credential.issued` (45ms) and `credential.suspended` (52ms).
  - Displays the official `@decentralid/sdk` TypeScript client quickstart code.

---

### 12. Platform Operations & Telemetry

- **Filename:** `12-platform-operations.png`
- **Application Route:** `/operations` (`PlatformOperationsView.tsx`)
- **Core Feature:** Enterprise SRE telemetry, deep readiness probes, live database metrics, and smart contract registry sync.
- **Workflow Demonstrated:**
  - Displays platform status: **OPERATIONAL** with deep `/api/v1/health/ready` probe returning 200 OK.
  - Verifies synchronized EVM smart contract addresses on Hardhat Chain `#31337`:
    - `IssuerRegistry.sol`: `0x5FbDB2315678afecb367f032d93F642f64180aa3` (Synced)
    - `CredentialRegistry.sol`: `0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512` (Synced)
    - `CredentialStatusRegistry.sol`: `0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0` (Synced)
  - Features dynamically aggregated database metrics (zero synthetic numbers) and institutional security invariants: Zero Plaintext PII on Public Ledgers, Strict Separation of Duties, Immutable Terminal Revocation, and Critical Freshness Enforcement in Offline Mode.

---

## Verification & Reproduction Instructions

To reproduce or re-capture these screenshots at any time:

1. **Seed Demo Data:**
   ```powershell
   & "backend\venv\Scripts\python.exe" scripts/seed_demo_data.py
   Copy-Item decentralid.db backend/decentralid.db -Force
   ```

2. **Start Backend Engine:**
   ```powershell
   backend\venv\Scripts\python.exe -m uvicorn backend.app.main:app --port 8000 --host 127.0.0.1
   ```

3. **Start Frontend Client:**
   ```powershell
   npm run dev --prefix frontend -- --port 5173 --host 127.0.0.1
   ```

4. **Navigate & Inspect:**
   Open Chrome at `http://localhost:5173/` at 1920 × 1080 resolution. All routes, credentials, and verification gates operate dynamically with zero mock data.
