import pytest
from httpx import AsyncClient, ASGITransport
from eth_account import Account

from backend.app.main import app
from backend.app.services.integrations.education_connector import EducationConnector
from backend.app.services.integrations.hr_connector import HREcosystemConnector
from backend.app.services.integrations.bulk_migration import BulkMigrationToolkit
from backend.app.services.integrations.sso_service import EnterpriseSSOService
from backend.app.services.credential.signing_service import SigningService

@pytest.mark.asyncio
async def test_education_connector_batch_processing():
    connector = EducationConnector(system_type="CANVAS")
    
    raw_records = [
        {"roll_no": "2024-CS-001", "name": "Aarav Patel", "course_name": "Data Structures", "grade": "A"},
        {"roll_no": "2024-CS-002", "name": "Diya Sen", "course_name": "Algorithms", "grade": "A+"},
        # Duplicate record
        {"roll_no": "2024-CS-001", "name": "Aarav Patel", "course_name": "Data Structures", "grade": "A"},
        # Malformed record (missing course)
        {"roll_no": "2024-CS-003", "name": "Kabir"}
    ]
    
    outcome = await connector.process_sync_batch(raw_records, "ACADEMIC_DEGREE")
    assert outcome["total_received"] == 4
    assert outcome["valid_drafts_created"] == 2
    assert outcome["duplicates_rejected"] == 1
    assert outcome["validation_failures"] == 1
    assert len(outcome["draft_ids"]) == 2

@pytest.mark.asyncio
async def test_hr_connector_data_minimization():
    issuer = Account.create()
    
    doc = {
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "id": "urn:uuid:test-cred-hr",
        "type": ["VerifiableCredential", "AcademicDegreeCredential"],
        "issuer": issuer.address,
        "validFrom": "2026-11-24T12:00:00Z",
        "credentialSubject": {
            "candidate_name": "Priya Nair",
            "degree": "Master of Computer Applications",
            "gpa": "9.4",
            "confidential_health_record": "DO_NOT_EXPOSE" # Sensitive unrequested claim
        }
    }
    
    signed_vc = SigningService.sign_credential(
        credential_doc=doc,
        private_key=issuer.key.hex(),
        verification_method=issuer.address,
        cryptosuite="ecdsa-jcs-2019"
    )
    
    presentation = {
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "type": ["VerifiablePresentation"],
        "verifiableCredential": [signed_vc]
    }
    
    # Employer only requests degree and institution
    outcome = await HREcosystemConnector.verify_candidate_presentation(
        candidate_id="CAND-789",
        employer_name="Infosys Technologies",
        required_claims=["degree", "institution"],
        verifiable_presentation=presentation
    )
    
    assert outcome["is_verified"] is True
    assert outcome["status"] == "VERIFIED"
    assert "degree" in outcome["verified_claims"]
    assert "confidential_health_record" not in outcome["verified_claims"] # Strict data minimization verified
    assert outcome["unauthorized_data_exposed"] is False

@pytest.mark.asyncio
async def test_bulk_migration_toolkit():
    raw_csv_rows = [
        {"StudentID": "STU001", "FullName": "Rohan Mehra", "DegreeTitle": "B.Sc Physics"},
        {"StudentID": "STU002", "FullName": "Sneha Roy", "DegreeTitle": "B.Sc Chemistry"},
        {"StudentID": "STU001", "FullName": "Rohan Mehra", "DegreeTitle": "B.Sc Physics"} # Duplicate
    ]
    
    mappings = {
        "StudentID": "student_id",
        "FullName": "student_name",
        "DegreeTitle": "degree"
    }
    
    preview = BulkMigrationToolkit.preview_migration("ACADEMIC_DEGREE", mappings, raw_csv_rows)
    assert preview["total_records"] == 3
    assert preview["valid_records"] == 2
    assert preview["duplicate_records"] == 1
    
    executed = BulkMigrationToolkit.execute_migration_batch("ACADEMIC_DEGREE", mappings, raw_csv_rows)
    assert executed["imported_count"] == 2
    assert executed["skipped_count"] == 1
    assert executed["status"] == "STAGED_FOR_APPROVAL"

@pytest.mark.asyncio
async def test_enterprise_sso_service():
    # 1. Matching domain
    claims_valid = {
        "sub": "idp-user-123",
        "email": "dean@iitb.ac.in",
        "name": "Prof. S. Sharma",
        "groups": ["Dean", "Faculty"]
    }
    ok, details = EnterpriseSSOService.map_idp_claims_to_membership(claims_valid, "iitb.ac.in")
    assert ok is True
    assert details["assigned_role"] == "ISSUER_ADMIN"
    assert details["signing_capability"] == "CLIENT_KEY_REQUIRED"

    # 2. Mismatched domain
    claims_mismatch = {
        "sub": "idp-user-456",
        "email": "infiltrator@external.com",
        "name": "Unknown"
    }
    ok_mismatch, err = EnterpriseSSOService.map_idp_claims_to_membership(claims_mismatch, "iitb.ac.in")
    assert ok_mismatch is False
    assert err["error"] == "DOMAIN_MISMATCH"

@pytest.mark.asyncio
async def test_connectors_status_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/integrations/connectors/status")
        assert resp.status_code == 200
        statuses = resp.json()
        assert len(statuses) >= 3
        assert any(s["system_type"] == "EDUCATION_LMS" for s in statuses)
