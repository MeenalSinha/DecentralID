# Independent Verification Engine & Architecture

## 1. Overview

The **DecentralID Independent Verification Engine** enables employers, educational organizations, and third-party auditors to independently verify credentials and presentations.

### Fundamental Security Posture
- **Zero Crypto Wallet Barrier:** Verifiers do NOT need a crypto wallet, MetaMask extension, or native tokens to verify credentials. Verification is an open, stateless cryptographic check against the decentralized trust network.
- **Multi-Tier Cryptographic Pipeline:** The engine evaluates 6 separate orthogonal verification criteria.
- **Honest Diagnostic Feedback:** DecentralID strictly avoids subjective or deceptive numerical "trust scores". A credential is either authentic or invalid, with clear root causes identified for any failure.

---

## 2. Multi-Tier Verification Pipeline

$$\begin{array}{|l|l|l|}
\hline
\textbf{Tier} & \textbf{Quality Gate} & \textbf{Mechanism} \\ \hline
\text{Tier 1} & \text{Envelope \& Schema Structure} & \text{Validates W3C VC 2.0 top-level context, type arrays, and registered claim types} \\ \hline
\text{Tier 2} & \text{ECDSA Cryptographic Signature} & \text{Reconstructs RFC 8785 canonical bytes and recovers signer address via secp256k1} \\ \hline
\text{Tier 3} & \text{Issuer Accreditation} & \text{Queries on-chain \texttt{IssuerRegistry.sol} to verify institutional authorization} \\ \hline
\text{Tier 4} & \text{Operational Signing Key} & \text{Verifies recovered signer matches an active, unexpired signing key of the issuer} \\ \hline
\text{Tier 5} & \text{Commitment Integrity} & \text{Verifies subject claims against $C = \text{keccak256}(\text{canonicalSubject} \parallel R)$} \\ \hline
\text{Tier 6} & \text{Lifecycle Status} & \text{Checks real-time revocation/suspension on \texttt{CredentialStatusRegistry.sol}} \\ \hline
\text{Tier 7} & \text{Validity Period} & \text{Checks \texttt{validUntil} timestamp against network clock} \\ \hline
\end{array}$$

---

## 3. Supported Ingestion Channels

1. **Direct File Ingestion:** Verifiers upload `.json` files containing a W3C Verifiable Credential or Verifiable Presentation.
2. **Opaque Token Resolution:** Optical QR code scanners or URLs with `?token=pr_...` query the `/verification/presentation/{token}` endpoint to fetch presentations without exposing PII in transit.
3. **Raw JSON Ingestion:** Verifiers can paste raw W3C VC payloads and optionally provide a 32-byte private salt for commitment verification.
4. **Enterprise Audit Trail:** Every verification produces an exportable audit certificate in standard JSON or CSV format.
