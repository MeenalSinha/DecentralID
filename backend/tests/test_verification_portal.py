import pytest
import datetime
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.services.credential.preparation_service import PreparationService
from backend.app.services.credential.issuance_service import IssuanceService
from backend.app.services.credential.presentation_service import PresentationService
from backend.app.models.user import User, Wallet
from backend.app.models.organization import Organization, OrganizationMembership, SigningKey
from eth_account import Account

@pytest.mark.asyncio
async def test_independent_verification_portal_pipeline(client, test_db):
    # Setup Issuer and Recipient
    issuer_admin = User(email="verifier-test-admin@test.org", role="ADMIN")
    recipient_acc = Account.create()
    recipient_addr = recipient_acc.address.lower()
    recipient_user = User(email="student@test.org", role="USER")
    test_db.add_all([issuer_admin, recipient_user])
    await test_db.flush()

    recipient_wallet = Wallet(user_id=recipient_user.id, address=recipient_addr, chain_id=1337)
    test_db.add(recipient_wallet)

    issuer_key_acc = Account.create()
    org = Organization(
        name="IIT Delhi",
        legal_entity_id="EDU-IITD-001",
        domain="iitd.ac.in",
        status="AUTHORIZED",
        on_chain_address=issuer_key_acc.address.lower(),
    )
    test_db.add(org)
    await test_db.flush()

    mem = OrganizationMembership(
        user_id=issuer_admin.id,
        organization_id=org.id,
        role="ADMIN",
        status="ACTIVE",
    )
    test_db.add(mem)

    signing_key = SigningKey(
        organization_id=org.id,
        public_key_address=issuer_key_acc.address.lower(),
        status="ACTIVE",
    )
    test_db.add(signing_key)
    await test_db.commit()

    # Issue credential
    claims = {
        "studentName": "Kavya Verma",
        "degree": "Master of Technology",
        "major": "Artificial Intelligence",
        "institutionName": "IIT Delhi",
        "graduationDate": "2026-05-20",
        "gpa": 9.8,
    }
    cred, _ = await PreparationService.prepare_credential(
        db=test_db,
        operator_user_id=issuer_admin.id,
        organization_id=org.id,
        recipient_address=recipient_addr,
        schema_type="UniversityDegreeCredential",
        claims=claims,
    )
    await IssuanceService.submit_for_approval(test_db, cred.id, issuer_admin.id)
    # Admin approval
    cred.workflow_status = "APPROVED"
    await test_db.commit()
    _, signed_vc = await IssuanceService.sign_credential(
        test_db, cred.id, issuer_key_acc.key.hex(), issuer_admin.id
    )
    await IssuanceService.confirm_blockchain_registration(test_db, cred.id, "0x" + "11" * 32)

    # 1. Public verification of raw VC without wallet/auth
    verify_resp = await client.post("/api/v1/verification/verify", json={"credential": signed_vc})
    assert verify_resp.status_code == 200
    res_data = verify_resp.json()
    assert res_data["is_valid"] is True
    assert res_data["checks"]["structural"] is True
    assert res_data["checks"]["signature"] is True
    assert res_data["checks"]["issuer_authorized"] is True
    assert res_data["checks"]["signing_key_authorized"] is True
    assert res_data["lifecycle_status"] == "ACTIVE"

    # 2. Tampered signature fails honestly
    tampered_vc = dict(signed_vc)
    tampered_vc["credentialSubject"] = dict(tampered_vc["credentialSubject"])
    tampered_vc["credentialSubject"]["gpa"] = 10.0
    tamper_resp = await client.post("/api/v1/verification/verify", json={"credential": tampered_vc})
    assert tamper_resp.status_code == 200
    tamper_data = tamper_resp.json()
    assert tamper_data["is_valid"] is False
    assert tamper_data["checks"]["signature"] is False
    assert len(tamper_data["errors"]) > 0

    # 3. Verification of Selective Disclosure Presentation via token
    vp = await PresentationService.create_presentation(
        db=test_db,
        holder_address=recipient_addr,
        credential_id=cred.credential_id,
        disclosed_attributes=["degree", "institutionName", "graduationDate"],
    )

    token_verify_resp = await client.post(
        "/api/v1/verification/verify", json={"token": vp.token}
    )
    assert token_verify_resp.status_code == 200
    token_res = token_verify_resp.json()
    assert token_res["is_valid"] is True
    assert token_res["is_selective_disclosure"] is True
    assert "degree" in token_res["disclosed_claims"]
    assert "gpa" not in token_res["disclosed_claims"]
