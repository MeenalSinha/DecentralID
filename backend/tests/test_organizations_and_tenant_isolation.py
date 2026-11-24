import pytest
from eth_account import Account
from eth_account.messages import encode_defunct
from backend.app.core.constants import UserRole

async def authenticate_user(client, account=None):
    if not account:
        account = Account.create()
    
    challenge_res = await client.post(
        "/api/v1/authentication/challenge",
        json={
            "wallet_address": account.address,
            "chain_id": 31337,
            "domain": "localhost",
            "uri": "http://localhost:5173",
        },
    )
    challenge_data = challenge_res.json()
    message = challenge_data["message"]
    nonce = challenge_data["nonce"]

    signable_message = encode_defunct(text=message)
    signed = account.sign_message(signable_message)
    signature = f"0x{signed.signature.hex()}" if not signed.signature.hex().startswith("0x") else signed.signature.hex()

    verify_res = await client.post(
        "/api/v1/authentication/verify-wallet",
        json={
            "wallet_address": account.address,
            "nonce": nonce,
            "signature": signature,
        },
    )
    session_token = verify_res.json()["session_token"]
    user_id = verify_res.json()["user_id"]
    return account, session_token, user_id

@pytest.mark.asyncio
async def test_organization_registration_and_membership(client):
    admin_account, session_token, user_id = await authenticate_user(client)
    client.cookies.set("decentralid_session", session_token)

    # Register Metro University
    create_res = await client.post(
        "/api/v1/organizations",
        json={
            "name": "Metro University",
            "legal_entity_id": "EDU-METRO-001",
            "domain": "metro.edu",
            "on_chain_address": admin_account.address,
        },
    )
    assert create_res.status_code == 201
    org_data = create_res.json()
    assert org_data["name"] == "Metro University"
    assert org_data["status"] == "PENDING_REVIEW"
    org_id = org_data["id"]

    # Fetch organization details as institution admin
    get_res = await client.get(f"/api/v1/organizations/{org_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == org_id

    # Invite an Authorized Issuer to the organization
    issuer_account = Account.create()
    invite_res = await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={
            "user_address": issuer_account.address,
            "role": UserRole.AUTHORIZED_ISSUER.value,
        },
    )
    assert invite_res.status_code == 201
    member_data = invite_res.json()
    assert member_data["wallet_address"].lower() == issuer_account.address.lower()
    assert member_data["role"] == UserRole.AUTHORIZED_ISSUER.value

    # List members
    list_res = await client.get(f"/api/v1/organizations/{org_id}/members")
    assert list_res.status_code == 200
    members = list_res.json()
    assert len(members) == 2 # Admin + Invited Issuer

@pytest.mark.asyncio
async def test_tenant_isolation_cross_tenant_access_rejection(client):
    # Admin 1 creates Org A (Metro University)
    admin_a, session_a, _ = await authenticate_user(client)
    client.cookies.set("decentralid_session", session_a)

    org_a_res = await client.post(
        "/api/v1/organizations",
        json={"name": "Org A (Metro)", "legal_entity_id": "ORG-A-100"},
    )
    org_a_id = org_a_res.json()["id"]

    # Admin 2 creates Org B (Tech Institute)
    admin_b, session_b, _ = await authenticate_user(client)
    client.cookies.set("decentralid_session", session_b)

    org_b_res = await client.post(
        "/api/v1/organizations",
        json={"name": "Org B (Tech)", "legal_entity_id": "ORG-B-200"},
    )
    org_b_id = org_b_res.json()["id"]

    # TENANT ISOLATION CHECK: Admin B attempts to read Org A's private details
    # Must fail with 403 Forbidden!
    cross_access_res = await client.get(f"/api/v1/organizations/{org_a_id}")
    assert cross_access_res.status_code == 403
    assert "membership" in cross_access_res.json()["error"]["message"]

    # TENANT ISOLATION CHECK: Admin B attempts to list Org A's members
    cross_list_res = await client.get(f"/api/v1/organizations/{org_a_id}/members")
    assert cross_list_res.status_code == 403

    # TENANT ISOLATION CHECK: Admin B attempts to invite someone into Org A
    some_account = Account.create()
    cross_invite_res = await client.post(
        f"/api/v1/organizations/{org_a_id}/members",
        json={"user_address": some_account.address, "role": UserRole.AUTHORIZED_ISSUER.value},
    )
    assert cross_invite_res.status_code == 403
