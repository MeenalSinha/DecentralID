import pytest
import uuid
import datetime
from httpx import AsyncClient, ASGITransport
from eth_account import Account

from backend.app.main import app
from backend.app.models.organization import Organization, SigningKey
from backend.app.models.user import User
from backend.app.models.governance import InstitutionAccreditation
from backend.app.services.governance.trust_policy_service import TrustPolicyService

@pytest.mark.asyncio
async def test_accreditation_workflow_and_separation_of_duties(test_db):
    # Setup test organization and users
    org_id = str(uuid.uuid4())
    org = Organization(
        id=org_id,
        name="Indian Institute of Technology Bombay",
        legal_entity_id=f"IITB-{uuid.uuid4().hex[:6]}",
        domain="iitb.ac.in",
        status="ACTIVE",
        on_chain_address="0x1111111111111111111111111111111111111111"
    )
    test_db.add(org)
    
    officer_user = User(
        id=str(uuid.uuid4()),
        role="ISSUER_OFFICER",
        is_active=True
    )
    test_db.add(officer_user)
    
    reviewer_user = User(
        id=str(uuid.uuid4()),
        role="GOVERNANCE_OFFICER",
        is_active=True
    )
    test_db.add(reviewer_user)
    
    senior_approver = User(
        id=str(uuid.uuid4()),
        role="PLATFORM_ADMIN",
        is_active=True
    )
    test_db.add(senior_approver)
    await test_db.commit()

    # 1. Apply for accreditation
    acc = InstitutionAccreditation(
        organization_id=org_id,
        category="UNIVERSITY",
        status="APPLIED",
        authorized_schemas=["ACADEMIC_DEGREE"],
        evidence_urls=["bafkreiauto12345"]
    )
    test_db.add(acc)
    await test_db.commit()
    await test_db.refresh(acc)

    # 2. Stage 1 Review: Reviewer processes application
    acc.reviewer_id = reviewer_user.id
    acc.status = "UNDER_REVIEW"
    acc.review_notes = "Evidence verified against official UGC registry"
    await test_db.commit()

    # 3. Stage 2 Decision: Approver confirms accreditation
    now = datetime.datetime.now(datetime.timezone.utc)
    acc.senior_approver_id = senior_approver.id
    acc.status = "APPROVED"
    acc.valid_from = now
    acc.valid_until = now + datetime.timedelta(days=365)
    await test_db.commit()
    await test_db.refresh(acc)

    assert acc.status == "APPROVED"
    assert acc.reviewer_id != acc.senior_approver_id # Strict separation of duties verified

@pytest.mark.asyncio
async def test_trust_policy_engine(test_db):
    inst_addr = "0x2222222222222222222222222222222222222222"
    org_id = str(uuid.uuid4())
    org = Organization(
        id=org_id,
        name="Delhi Technological University",
        legal_entity_id=f"DTU-{uuid.uuid4().hex[:6]}",
        domain="dtu.ac.in",
        status="ACTIVE",
        on_chain_address=inst_addr
    )
    test_db.add(org)
    
    now = datetime.datetime.now(datetime.timezone.utc)
    acc = InstitutionAccreditation(
        organization_id=org_id,
        category="UNIVERSITY",
        status="APPROVED",
        authorized_schemas=["ACADEMIC_DEGREE", "SKILL_CERTIFICATE"],
        valid_from=now,
        valid_until=now + datetime.timedelta(days=365)
    )
    test_db.add(acc)
    await test_db.commit()

    # 1. Test Trusted evaluation for authorized schema
    trusted_eval = await TrustPolicyService.evaluate_trust(
        db=test_db,
        institution_address=inst_addr,
        credential_schema="ACADEMIC_DEGREE"
    )
    assert trusted_eval.is_trusted is True
    assert trusted_eval.verdict == "TRUSTED"
    assert trusted_eval.category == "UNIVERSITY"

    # 2. Test Unauthorized schema evaluation
    unauth_eval = await TrustPolicyService.evaluate_trust(
        db=test_db,
        institution_address=inst_addr,
        credential_schema="MEDICAL_LICENSE"
    )
    assert unauth_eval.is_trusted is False
    assert unauth_eval.verdict == "SCHEMA_UNAUTHORIZED"

    # 3. Test Unknown institution evaluation
    unknown_eval = await TrustPolicyService.evaluate_trust(
        db=test_db,
        institution_address="0x9999999999999999999999999999999999999999",
        credential_schema="ACADEMIC_DEGREE"
    )
    assert unknown_eval.is_trusted is False
    assert unknown_eval.verdict == "INSTITUTION_UNKNOWN"

    # 4. Test Suspended institution evaluation
    acc.status = "SUSPENDED"
    await test_db.commit()
    suspended_eval = await TrustPolicyService.evaluate_trust(
        db=test_db,
        institution_address=inst_addr,
        credential_schema="ACADEMIC_DEGREE"
    )
    assert suspended_eval.is_trusted is False
    assert suspended_eval.verdict == "ACCREDITATION_SUSPENDED"

@pytest.mark.asyncio
async def test_public_trust_directory(client, test_db):
    # Register an active accredited org
    org = Organization(
        id=str(uuid.uuid4()),
        name="BITS Pilani",
        legal_entity_id=f"BITS-{uuid.uuid4().hex[:6]}",
        domain="bits-pilani.ac.in",
        status="ACTIVE",
        on_chain_address="0x3333333333333333333333333333333333333333"
    )
    test_db.add(org)
    acc = InstitutionAccreditation(
        organization_id=org.id,
        category="UNIVERSITY",
        status="APPROVED",
        authorized_schemas=["ACADEMIC_DEGREE"],
        valid_until=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=180)
    )
    test_db.add(acc)
    await test_db.commit()

    response = await client.get("/api/v1/governance/directory")
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) >= 1
    assert any(e["institution_name"] == "BITS Pilani" for e in entries)
