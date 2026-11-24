# DecentralID Intelligence Architecture

**Module:** DecentralID Intelligence (Phase 10)  
**Purpose:** AI-Assisted Document Intake, Text Extraction, Schema Matching, and Credential Anomaly Detection

---

## 1. Design Principles & Governance Boundaries

1. **Non-Bypass Rule**: AI extraction is strictly an ingestion accelerator. It **never** automatically signs, approves, or issues a verifiable credential.
2. **Separation of Duties**: Extracted credentials enter the standard `PREPARED` state, requiring independent review by an Institutional Administrator before cryptographic signing.
3. **No Fabricated Data**: If a field cannot be detected with sufficient confidence, it remains absent. Missing fields are never synthesized.
4. **Tenant Isolation**: Uploaded documents, extracted records, and anomaly logs are strictly scoped to the authenticated organization.

---

## 2. Ingestion & Security Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ Uploaded File (Multipart/form-data)                         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                [1. File Magic Byte Inspection]
                ├── PDF: %PDF- (0x25 0x50 0x44 0x46 0x2D)
                ├── PNG: \x89PNG\r\n\x1a\n
                └── JPEG: \xFF\xD8\xFF
                               │ (Rejects executables / unknown formats)
                [2. SHA-256 Fingerprinting]
                ├── Computes content hash
                └── Detects duplicate upload collisions
                               │
                [3. Pure-Python Stream / OCR Extraction]
                ├── PDF: Deflate stream decomp & BT/ET Tj parsing
                └── Image: Local Tesseract / Provider OCR
                               │
                [4. Field & Schema Matching]
                ├── UniversityDegreeCredential
                ├── SkillCertificateCredential
                └── EmploymentCredential
                               │
                [5. Anomaly Detection Engine]
                ├── Future date inconsistencies
                ├── Mismatched institution metadata
                ├── Duplicate credential reference numbers
                └── Low-confidence / missing identity flags
                               │
                [6. Human Review & Correction UI]
                └── [7. Preparation Gateway -> PREPARED Credential]
```

---

## 3. Database Entities

- `document_uploads`: Tracks raw files, MIME types, SHA-256 fingerprints, storage paths, and processing states (`PENDING`, `PROCESSING`, `PROCESSED`, `FAILED`).
- `extracted_credential_data`: Persists raw text, field-level dictionary (`value`, `confidence`, `evidence_snippet`, `human_corrected`), anomaly findings array, review status (`PENDING_REVIEW`, `APPROVED`, `REJECTED`), and linked `credential_id`.

---

## 4. API Specification

| Endpoint | Method | Role | Description |
|---|---|---|---|
| `/api/v1/intelligence/upload` | POST | Operator / Admin | Uploads document, parses text, matches schema, runs anomaly checks. |
| `/api/v1/intelligence/documents` | GET | Operator / Admin | Lists processed intake documents for the organization. |
| `/api/v1/intelligence/documents/{id}` | GET | Operator / Admin | Fetches extraction details, confidence scores, and anomaly report. |
| `/api/v1/intelligence/documents/{id}/review` | POST | Issuer / Admin | Updates extracted fields and marks review as `APPROVED` or `REJECTED`. |
| `/api/v1/intelligence/documents/{id}/prepare-credential` | POST | Operator / Admin | Submits approved extraction into the standard credential issuance engine. |
