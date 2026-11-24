# QR Code & Presentation Link Verification Specification

## 1. Problem Definition: The Naive QR Anti-Pattern

Most legacy credential systems encode raw JSON payloads directly into QR codes. This pattern introduces severe privacy and security vulnerabilities:
1. **Uncontrolled PII Exposure:** Anyone with a smartphone camera can scan the code and harvest student names, identification numbers, and grades without authorization.
2. **Shoulder Surfing:** QR codes displayed on phone screens or projected during interviews can be photographed and decoded from afar.
3. **Payload Truncation:** Complete verifiable credentials with cryptographic proofs often exceed standard QR capacity (typically 2-3 KB max), forcing implementations into non-standard compression or omitting critical signatures.

---

## 2. DecentralID Architecture: Privacy-Preserving Opaque Tokens

DecentralID resolves this using high-entropy, short-lived opaque presentation tokens:
1. **Holder-Initiated Creation:** The holder selects which fields to reveal and clicks "Generate Verifiable Presentation".
2. **Opaque Token Generation:**
   $$\text{Token} = \text{"pr\_"} \parallel \text{Base64URL}(\text{SecureRandom}(32))$$
3. **QR Encoded Payload:**
   Only the presentation URI is encoded:
   `https://verify.decentralid.org/verify?token=pr_8xLk29Z...`
4. **Access Control & Expiration:**
   - Tokens expire automatically after the designated window (e.g. 24 hours).
   - Presentation shares have rate limits (e.g., maximum 50 or 100 queries) to prevent persistent scraping.
   - Verifiers only receive the selectively disclosed claims.
