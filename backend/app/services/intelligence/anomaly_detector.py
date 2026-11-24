import datetime
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.intelligence import DocumentUpload
from backend.app.models.organization import Organization
from backend.app.models.credential import Credential

class AnomalyDetector:
    """
    Credential anomaly and integrity verification service.
    Detects suspicious metadata inconsistencies, duplicate fingerprints, and mismatched identities.
    Never declares a document fraudulent automatically; generates explainable audit findings.
    """

    @classmethod
    async def analyze_document_anomalies(
        cls,
        db: AsyncSession,
        organization_id: str,
        file_hash: str,
        current_doc_id: str,
        extracted_fields: Dict[str, Dict[str, Any]],
        overall_confidence: float
    ) -> List[Dict[str, str]]:
        findings: List[Dict[str, str]] = []

        # 1. Duplicate Document Fingerprint Check (SHA-256 Collision)
        dup_stmt = select(DocumentUpload).where(
            DocumentUpload.file_hash == file_hash,
            DocumentUpload.id != current_doc_id
        )
        dup_res = await db.execute(dup_stmt)
        prior_upload = dup_res.scalar_one_or_none()
        if prior_upload:
            findings.append({
                "rule": "DUPLICATE_DOCUMENT_FINGERPRINT",
                "severity": "CRITICAL",
                "description": f"Identical document file hash ({file_hash[:12]}...) was previously uploaded (Doc ID: {prior_upload.id[:8]}...).",
                "evidence": f"Duplicate SHA-256: {file_hash}",
            })

        # 2. Institution Metadata Consistency Check
        org_stmt = select(Organization).where(Organization.id == organization_id)
        org_res = await db.execute(org_stmt)
        org = org_res.scalar_one_or_none()

        extracted_inst = extracted_fields.get("institutionName", {}).get("value")
        if org and extracted_inst:
            org_tokens = set(org.name.lower().split())
            doc_tokens = set(extracted_inst.lower().split())
            overlap = org_tokens.intersection(doc_tokens)
            # If there's no word overlap between document institution name and authorized org name
            if not overlap and len(org_tokens) > 1 and len(doc_tokens) > 1:
                findings.append({
                    "rule": "INCONSISTENT_INSTITUTION_METADATA",
                    "severity": "HIGH",
                    "description": f"Document claims issuing institution '{extracted_inst}', but uploading organization is registered as '{org.name}'.",
                    "evidence": f"Document: '{extracted_inst}' vs Tenant: '{org.name}'",
                })

        # 3. Future Date Anomaly Check
        date_field = extracted_fields.get("graduationDate") or extracted_fields.get("issueDate")
        if date_field and date_field.get("value"):
            try:
                date_val = str(date_field["value"])
                dt = datetime.datetime.strptime(date_val[:10], "%Y-%m-%d").date()
                today = datetime.datetime.now(datetime.timezone.utc).date()
                if dt > today:
                    findings.append({
                        "rule": "FUTURE_DATE_INCONSISTENCY",
                        "severity": "HIGH",
                        "description": f"Document completion/issue date '{date_val}' is in the future (current UTC date: {today}).",
                        "evidence": f"Extracted date: {date_val}",
                    })
            except Exception:
                pass

        # 4. Duplicate Credential Reference Check
        cert_num = (
            extracted_fields.get("certificateNumber", {}).get("value")
            or extracted_fields.get("studentId", {}).get("value")
        )
        if cert_num and org:
            # Query existing credentials under this org to detect reference reuse
            cred_stmt = select(Credential).where(
                Credential.organization_id == organization_id,
                Credential.credential_id.ilike(f"%{cert_num}%")
            )
            cred_res = await db.execute(cred_stmt)
            colliding_cred = cred_res.scalar_one_or_none()
            if colliding_cred:
                findings.append({
                    "rule": "DUPLICATE_CREDENTIAL_REFERENCE",
                    "severity": "HIGH",
                    "description": f"Reference number '{cert_num}' is already associated with issued credential {colliding_cred.credential_id[:12]}...",
                    "evidence": f"Collision on reference: {cert_num}",
                })

        # 5. Low Overall Confidence / Missing Critical Attributes
        if overall_confidence < 0.60:
            findings.append({
                "rule": "LOW_EXTRACTION_CONFIDENCE",
                "severity": "MEDIUM",
                "description": f"Overall extraction confidence score ({overall_confidence}) is below the institutional review threshold (0.60).",
                "evidence": f"Confidence: {overall_confidence}",
            })

        name_present = any(k in extracted_fields for k in ["studentName", "recipientName", "employeeName"])
        if not name_present:
            findings.append({
                "rule": "MISSING_RECIPIENT_IDENTITY",
                "severity": "MEDIUM",
                "description": "Recipient full legal name could not be extracted with sufficient confidence.",
                "evidence": "No matching name token in document text",
            })

        return findings
