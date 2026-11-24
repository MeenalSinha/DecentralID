import pytest
import datetime
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.services.credential.preparation_service import PreparationService
from backend.app.services.credential.issuance_service import IssuanceService
from backend.app.models.user import User, Wallet
from backend.app.models.organization import Organization, OrganizationMembership, SigningKey
from eth_account import Account

@pytest.mark.asyncio
async def test_holder_wallet_and_verifiable_presentation_lifecycle(client, test_db):
    # Create Issuer Admin and Operator
    issuer_admin = User(
        email="admin@test.org",
        role="ADMIN"
    )
    operator = User(
        email="operator@test.org",
        role="USER"
    )
    # Holder
    holder_acc = Account.create()
    holder_address = holder_acc.address.lower()
    holder_user = User(
        email="holder@test.org",
        role="USER"
    )
    test_db.add_all([issuer_admin, operator, holder_user])
    await test_db.flush()

    holder_wallet = Wallet(
        user_id=holder_user.id,
        address=holder_address,
        chain_id=1337,
        is_primary=True
    )
    test_db.add(holder_wallet)

    org = Organization(
        name="Test University",
        legal_entity_id="LEI-TEST-HOLDER",
        domain="test.edu",
        status="APPROVED",
        on_chain_address="0x" + "bb" * 20
    )
    test_db.add(org)
    await test_db.flush()

    mem_admin = OrganizationMembership(
        user_id=issuer_admin.id,
        organization_id=org.id,
        role="ADMIN",
        status="ACTIVE"
    )
    mem_op = OrganizationMembership(
        user_id=operator.id,
        organization_id=org.id,
        role="AUTHORIZED_ISSUER",
        status="ACTIVE"
    )
    test_db.add_all([mem_admin, mem_op])

    issuer_key_acc = Account.create()
    signing_key = SigningKey(
        organization_id=org.id,
        public_key_address=issuer_key_acc.address.lower(),
        status="ACTIVE"
    )
    test_db.add(signing_key)
    await test_db.commit()

    # Prepare credential
    claims = {
        "studentName": "Aarav Sharma",
        "degree": "Bachelor of Technology",
        "major": "Computer Science & Engineering",
        "institutionName": "Test University",
        "graduationDate": "2026-06-15",
        "gpa": 9.2,
    }
    cred, _ = await PreparationService.prepare_credential(
        db=test_db,
        operator_user_id=operator.id,
        organization_id=org.id,
        recipient_address=holder_address,
        schema_type="UniversityDegreeCredential",
        claims=claims,
        valid_until=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
    )

    # Submit and approve
    await IssuanceService.submit_for_approval(test_db, cred.credential_id, operator.id)
    await IssuanceService.approve_credential(test_db, cred.credential_id, issuer_admin.id)
    await IssuanceService.sign_credential(test_db, cred.credential_id, issuer_key_acc.key.hex(), issuer_admin.id)
    await IssuanceService.confirm_blockchain_registration(test_db, cred.credential_id, "0x" + "aa" * 32)

    # 1. Holder fetches credentials
    from backend.app.api.dependencies.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: holder_user

    resp = await client.get(f"/api/v1/credentials/holder/{holder_address}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["recipient_address"] == holder_address
    assert data["items"][0]["claims"]["studentName"] == "Aarav Sharma"
    assert data["items"][0]["workflow_status"] == "ISSUED"

    # 2. Unauthorized holder query fails
    other_holder = "0x3333333333333333333333333333333333333333"
    resp_unauth = await client.get(f"/api/v1/credentials/holder/{other_holder}")
    assert resp_unauth.status_code == 403

    # 3. Create Verifiable Presentation with selective disclosure (masking GPA)
    vp_payload = {
        "credential_id": cred.credential_id,
        "disclosed_attributes": ["degree", "institutionName", "graduationDate"],
        "expires_in_hours": 12
    }
    vp_resp = await client.post("/api/v1/credentials/presentations", json=vp_payload)
    assert vp_resp.status_code == 201
    vp_data = vp_resp.json()
    assert "token" in vp_data
    assert vp_data["token"].startswith("pr_")
    assert "gpa" in vp_data["masked_claims"]
    assert "degree" in vp_data["disclosed_claims"]
    assert "gpa" not in vp_data["disclosed_claims"]

    # Check standard W3C VP format
    vp_doc = vp_data["presentation_document"]
    assert "VerifiablePresentation" in vp_doc["type"]
    assert len(vp_doc["verifiableCredential"]) == 1
    inner_subject = vp_doc["verifiableCredential"][0]["credentialSubject"]
    assert "degree" in inner_subject
    assert "gpa" not in inner_subject

    # 4. Resolve presentation token anonymously
    app.dependency_overrides.pop(get_current_user, None)
    resolve_resp = await client.get(f"/api/v1/credentials/presentations/{vp_data['token']}")
    assert resolve_resp.status_code == 200
    resolved_doc = resolve_resp.json()
    assert resolved_doc["id"] == vp_doc["id"]
