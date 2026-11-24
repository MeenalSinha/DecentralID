import pytest
import datetime
from eth_account import Account
from eth_account.messages import encode_defunct
from backend.app.models.session import AuthChallenge
from backend.app.services.wallet_verification_service import WalletVerificationService

@pytest.mark.asyncio
async def test_challenge_generation(client):
    account = Account.create()
    response = await client.post(
        "/api/v1/authentication/challenge",
        json={
            "wallet_address": account.address,
            "chain_id": 31337,
            "domain": "localhost",
            "uri": "http://localhost:5173",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "nonce" in data
    assert len(data["nonce"]) == 32
    assert data["wallet_address"].lower() == account.address.lower()
    assert "message" in data
    assert "DecentralID" in data["message"]

@pytest.mark.asyncio
async def test_successful_wallet_authentication_and_session(client):
    account = Account.create()
    # 1. Request challenge
    challenge_res = await client.post(
        "/api/v1/authentication/challenge",
        json={
            "wallet_address": account.address,
            "chain_id": 31337,
            "domain": "localhost",
            "uri": "http://localhost:5173",
        },
    )
    assert challenge_res.status_code == 201
    challenge_data = challenge_res.json()
    message = challenge_data["message"]
    nonce = challenge_data["nonce"]

    # 2. Sign message with private key
    signable_message = encode_defunct(text=message)
    signed = account.sign_message(signable_message)
    signature = signed.signature.hex()
    if not signature.startswith("0x"):
        signature = f"0x{signature}"

    # 3. Verify wallet
    verify_res = await client.post(
        "/api/v1/authentication/verify-wallet",
        json={
            "wallet_address": account.address,
            "nonce": nonce,
            "signature": signature,
        },
    )
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["wallet_address"].lower() == account.address.lower()
    assert "session_token" in verify_data
    session_token = verify_data["session_token"]

    # 4. Access protected session endpoint using session cookie
    client.cookies.set("decentralid_session", session_token)
    session_res = await client.get("/api/v1/authentication/session")
    assert session_res.status_code == 200
    session_info = session_res.json()
    assert session_info["is_authenticated"] is True
    assert session_info["wallet_address"].lower() == account.address.lower()

    # 5. Access profile endpoint
    profile_res = await client.get("/api/v1/users/me")
    assert profile_res.status_code == 200
    profile_data = profile_res.json()
    assert profile_data["id"] == session_info["user_id"]

    # 6. Logout
    logout_res = await client.post("/api/v1/authentication/logout")
    assert logout_res.status_code == 200

    # 7. Access after logout fails
    post_logout_res = await client.get("/api/v1/authentication/session")
    assert post_logout_res.status_code == 401

@pytest.mark.asyncio
async def test_replay_attack_prevention(client):
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

    # First attempt succeeds
    res1 = await client.post(
        "/api/v1/authentication/verify-wallet",
        json={
            "wallet_address": account.address,
            "nonce": nonce,
            "signature": signature,
        },
    )
    assert res1.status_code == 200

    # Replay attempt with same nonce MUST FAIL
    res2 = await client.post(
        "/api/v1/authentication/verify-wallet",
        json={
            "wallet_address": account.address,
            "nonce": nonce,
            "signature": signature,
        },
    )
    assert res2.status_code == 401
    assert "consumed" in res2.json()["error"]["message"]

@pytest.mark.asyncio
async def test_invalid_signature_rejection(client):
    account1 = Account.create()
    account2 = Account.create()

    challenge_res = await client.post(
        "/api/v1/authentication/challenge",
        json={
            "wallet_address": account1.address,
            "chain_id": 31337,
            "domain": "localhost",
            "uri": "http://localhost:5173",
        },
    )
    challenge_data = challenge_res.json()
    message = challenge_data["message"]
    nonce = challenge_data["nonce"]

    # Sign with WRONG account (account2 signing account1's challenge)
    signable_message = encode_defunct(text=message)
    signed = account2.sign_message(signable_message)
    signature = f"0x{signed.signature.hex()}" if not signed.signature.hex().startswith("0x") else signed.signature.hex()

    res = await client.post(
        "/api/v1/authentication/verify-wallet",
        json={
            "wallet_address": account1.address,
            "nonce": nonce,
            "signature": signature,
        },
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_SIGNATURE"
    assert "Signature recovery failed" in res.json()["error"]["message"]
