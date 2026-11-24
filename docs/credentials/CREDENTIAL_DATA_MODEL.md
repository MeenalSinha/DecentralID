# DecentralID W3C Verifiable Credential Data Model 2.0
**Document Standard:** W3C Recommendation Candidate (VC-DATA-MODEL-2.0)

---

## 1. Top-Level Verifiable Credential Structure

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    "https://decentralid.org/contexts/v1"
  ],
  "id": "urn:uuid:6c36195a-3d28-4e89-948f-39580b0bb119",
  "type": [
    "VerifiableCredential",
    "UniversityDegreeCredential"
  ],
  "issuer": {
    "id": "did:pkh:eip155:31337:0x70997970c51812dc3a010c7d01b50e0d17dc79c8",
    "name": "Indian Institute of Technology Bombay"
  },
  "validFrom": "2026-11-24T00:00:00Z",
  "validUntil": "2036-11-24T00:00:00Z",
  "credentialSubject": {
    "id": "did:pkh:eip155:31337:0x3c44cdddb6a900fa2b585dd299e03d12fa4293bc",
    "studentName": "Aarav Sharma",
    "degree": "Bachelor of Technology",
    "major": "Computer Science & Engineering",
    "institutionName": "Indian Institute of Technology Bombay",
    "graduationDate": "2026-06-15"
  },
  "proof": {
    "type": "DataIntegrityProof",
    "cryptosuite": "ecdsa-jcs-2019",
    "created": "2026-11-24T09:15:00Z",
    "verificationMethod": "did:pkh:eip155:31337:0x9f77f83ecdf6295a5104df83dda4b6312a1f0da5#key-1",
    "proofPurpose": "assertionMethod",
    "proofValue": "0x534c0f8a8461..."
  }
}
```

---

## 2. Data-Driven Schemas

1. **`UniversityDegreeCredential` (v1.0.0):** Degree, major, institution, graduation date, honors, GPA.
2. **`AcademicTranscriptCredential` (v1.0.0):** Program, semester, courses, credits, grades, GPA.
3. **`CourseCompletionCertificate` (v1.0.0):** Course title, completion date, instructor, grade.
4. **`ProfessionalCertification` (v1.0.0):** Title, issuing body, license number, award date, renewal date.
5. **`EmploymentVerificationCredential` (v1.0.0):** Job title, employer, department, start date, end date, employment type.
