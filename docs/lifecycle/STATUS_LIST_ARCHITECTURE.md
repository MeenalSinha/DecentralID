# W3C Bitstring Status List 1.0 Architecture

## 1. Specification & Standards Conformance

DecentralID implements the **W3C Bitstring Status List 1.0** standard for credential suspension and revocation.

### High-Density Status Bitstrings
Traditional systems rely on monolithic lists of revoked identifiers or expensive single-credential queries that reveal user activity to verifiers and infrastructure operators.

The Bitstring Status List standard resolves these limitations:
1. **Bit Density:** Each credential maps to a single bit position within a dense bitstring:
   - Bit `0`: Active / Valid
   - Bit `1`: Revoked (for `statusPurpose: "revocation"`) or Suspended (for `statusPurpose: "suspension"`)
2. **Deterministic GZIP Compression:** Uncompressed bit arrays (e.g. 16,384 bits = 2,048 bytes) are compressed via GZIP with `mtime=0` to guarantee deterministic bytes and identical hashes across platforms.
3. **Multibase Encoding:** Encoded as base64url-no-pad prefixed with `u`.

---

## 2. Status List Verifiable Credential Data Model

Public verifiers query the status list credential published at:
`GET /api/v1/status-lists/{list_number}`

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2"
  ],
  "id": "https://decentralid.org/api/v1/status-lists/1",
  "type": ["VerifiableCredential", "BitstringStatusListCredential"],
  "issuer": "did:pkh:eip155:1337:0xee...",
  "validFrom": "2026-01-01T00:00:00Z",
  "credentialSubject": {
    "id": "https://decentralid.org/api/v1/status-lists/1#list",
    "type": "BitstringStatusList",
    "statusPurpose": "revocation",
    "encodedList": "uH4sIC..."
  }
}
```

Credentials embed an immutable link to their position in the status list:
```json
"credentialStatus": {
  "id": "https://decentralid.org/api/v1/status-lists/1#1042",
  "type": "BitstringStatusListEntry",
  "statusPurpose": "revocation",
  "statusListIndex": "1042",
  "statusListCredential": "https://decentralid.org/api/v1/status-lists/1"
}
```
Verifiers decompress the bitstring and check `Bitstring[1042]`:
- If `0`: The credential is valid and in good standing.
- If `1`: The credential is revoked.
