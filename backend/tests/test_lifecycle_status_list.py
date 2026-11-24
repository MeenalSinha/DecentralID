import pytest
import datetime
from backend.app.main import app
from backend.app.services.lifecycle.status_list_service import BitstringStatusListService
from backend.app.services.lifecycle.lifecycle_service import CredentialLifecycleService
from backend.app.services.credential.preparation_service import PreparationService
from backend.app.services.credential.issuance_service import IssuanceService
from backend.app.models.user import User, Wallet
from backend.app.models.organization import Organization, OrganizationMembership, SigningKey
from backend.app.core.exceptions import InvalidStatusTransitionException, TenantAccessDeniedException
from eth_account import Account

def test_w3c_bitstring_status_list_encoding_and_bit_operations():
    # 1. Initialize a 16,384-bit list
    bit_length = 16384
    raw_bits = bytearray(bit_length // 8)

    # Initial bits must all be 0
    assert BitstringStatusListService.get_bit(raw_bits, 0) == 0
    assert BitstringStatusListService.get_bit(raw_bits, 42) == 0
    assert BitstringStatusListService.get_bit(raw_bits, 16383) == 0

    # 2. Set specific bits to 1
    BitstringStatusListService.set_bit(raw_bits, 42, 1)
    BitstringStatusListService.set_bit(raw_bits, 1042, 1)
    assert BitstringStatusListService.get_bit(raw_bits, 42) == 1
    assert BitstringStatusListService.get_bit(raw_bits, 1042) == 1
    assert BitstringStatusListService.get_bit(raw_bits, 43) == 0

    # 3. Compress and Multibase encode
    encoded = BitstringStatusListService.encode_bitstring(raw_bits)
    assert encoded.startswith("u")

    # 4. Decode and verify lossless roundtrip
    decoded = BitstringStatusListService.decode_bitstring(encoded)
    assert decoded == raw_bits
    assert BitstringStatusListService.get_bit(decoded, 42) == 1
    assert BitstringStatusListService.get_bit(decoded, 1042) == 1
    assert BitstringStatusListService.get_bit(decoded, 43) == 0

    # 5. Reset bit to 0 (reinstatement)
    BitstringStatusListService.set_bit(raw_bits, 42, 0)
    assert BitstringStatusListService.get_bit(raw_bits, 42) == 0
    encoded_reset = BitstringStatusListService.encode_bitstring(raw_bits)
    decoded_reset = BitstringStatusListService.decode_bitstring(encoded_reset)
    assert BitstringStatusListService.get_bit(decoded_reset, 42) == 0

@pytest.mark.asyncio
async def test_credential_lifecycle_state_machine_and_status_list_sync(client, test_db):
    # Setup Issuer and Admin
    admin_user = User(email="lifecycle-admin@test.org", role="ADMIN")
    unauth_user = User(email="random-user@test.org", role="USER")
    holder_acc = Account.create()
    holder_addr = holder_acc.address.lower()
    test_db.add_all([admin_user, unauth_user])
    await test_db.flush()

    org = Organization(
        name="State Tech University",
        legal_entity_id="EDU-STU-001",
        domain="stu.edu",
        status="AUTHORIZED",
        on_chain_address="0x" + "ee" * 20,
    )
    test_db.add(org)
    await test_db.flush()

    mem = OrganizationMembership(
        user_id=admin_user.id,
        organization_id=org.id,
        role="ADMIN",
        status="ACTIVE",
    )
    test_db.add(mem)

    signing_key = SigningKey(
        organization_id=org.id,
        public_key_address="0x" + "ee" * 20,
        status="ACTIVE",
    )
    test_db.add(signing_key)
    await test_db.commit()

    # Prepare and map credential to Bitstring Status List
    slist, allocated_idx = await BitstringStatusListService.get_or_create_status_list(
        test_db, org.id, purpose="revocation"
    )

    claims = {
        "studentName": "Rohan Gupta",
        "degree": "Bachelor of Engineering",
        "major": "Electrical Engineering",
        "institutionName": "State Tech University",
        "graduationDate": "2026-06-30",
        "gpa": 8.7,
    }
    cred, _ = await PreparationService.prepare_credential(
        db=test_db,
        operator_user_id=admin_user.id,
        organization_id=org.id,
        recipient_address=holder_addr,
        schema_type="UniversityDegreeCredential",
        claims=claims,
    )
    cred.status_list_id = slist.id
    cred.status_list_index = allocated_idx
    cred.workflow_status = "ISSUED"
    cred.status = "ACTIVE"
    await test_db.commit()

    from backend.app.api.dependencies.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: admin_user

    # 1. Suspend Credential
    suspend_resp = await client.post(
        f"/api/v1/credentials/{cred.credential_id}/suspend",
        json={"reason": "Pending fee clearance review"},
    )
    assert suspend_resp.status_code == 200
    suspend_data = suspend_resp.json()
    assert suspend_data["status"] == "SUSPENDED"
    assert suspend_data["revocation_reason"] == "Pending fee clearance review"

    # Status bit on list must now be 1
    slist_updated = await test_db.get(type(slist), slist.id)
    bits = bytearray(slist_updated.raw_bits)
    assert BitstringStatusListService.get_bit(bits, allocated_idx) == 1

    # 2. Reinstate Credential
    reinstate_resp = await client.post(
        f"/api/v1/credentials/{cred.credential_id}/reinstate",
        json={"reason": "Fee cleared, account verified"},
    )
    assert reinstate_resp.status_code == 200
    reinstate_data = reinstate_resp.json()
    assert reinstate_data["status"] == "ACTIVE"

    # Status bit on list must now be 0
    await test_db.refresh(slist)
    bits = bytearray(slist.raw_bits)
    assert BitstringStatusListService.get_bit(bits, allocated_idx) == 0

    # 3. Permanent Revocation
    revoke_resp = await client.post(
        f"/api/v1/credentials/{cred.credential_id}/revoke",
        json={"reason": "Disciplinary expulsion"},
    )
    assert revoke_resp.status_code == 200
    revoke_data = revoke_resp.json()
    assert revoke_data["status"] == "REVOKED"
    assert revoke_data["workflow_status"] == "REVOKED"

    # Status bit on list must now be 1
    await test_db.refresh(slist)
    bits = bytearray(slist.raw_bits)
    assert BitstringStatusListService.get_bit(bits, allocated_idx) == 1

    # 4. Terminal Revocation Invariant: CANNOT reinstate a revoked credential
    reinstate_revoked_resp = await client.post(
        f"/api/v1/credentials/{cred.credential_id}/reinstate",
        json={"reason": "Attempting illegal reinstatement"},
    )
    assert reinstate_revoked_resp.status_code == 400

    # 5. Public Status List Credential endpoint
    app.dependency_overrides.pop(get_current_user, None)
    status_list_resp = await client.get(f"/api/v1/status-lists/{slist.list_number}")
    assert status_list_resp.status_code == 200
    slist_doc = status_list_resp.json()
    assert "BitstringStatusListCredential" in slist_doc["type"]
    assert slist_doc["credentialSubject"]["type"] == "BitstringStatusList"
    assert slist_doc["credentialSubject"]["encodedList"].startswith("u")
