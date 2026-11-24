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
    
    # SECURITY AUDIT VALIDATION: Raw session token must NOT be exposed in JSON response body
    assert "session_token" not in verify_data
    assert "decentralid_session" in verify_res.cookies

    # 4. Access protected session endpoint using session cookie automatically preserved by client
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

@pytest.mark.asyncio
async def test_unapproved_domain_rejection(client):
    account = Account.create()
    res = await client.post(
        "/api/v1/authentication/challenge",
        json={
            "wallet_address": account.address,
            "chain_id": 31337,
            "domain": "malicious-phishing-attacker.com",
            "uri": "https://malicious-phishing-attacker.com/login",
        },
    )
    assert res.status_code == 401
    assert "not authorized" in res.json()["error"]["message"]

@pytest.mark.asyncio
async def test_atomic_concurrent_nonce_consumption(client):
    import asyncio
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
    assert challenge_res.status_code == 201
    challenge_data = challenge_res.json()
    message = challenge_data["message"]
    nonce = challenge_data["nonce"]

    signable_message = encode_defunct(text=message)
    signed = account.sign_message(signable_message)
    signature = f"0x{signed.signature.hex()}" if not signed.signature.hex().startswith("0x") else signed.signature.hex()

    payload = {
        "wallet_address": account.address,
        "nonce": nonce,
        "signature": signature,
    }

    # Execute concurrent requests simultaneously
    res1, res2 = await asyncio.gather(
        client.post("/api/v1/authentication/verify-wallet", json=payload),
        client.post("/api/v1/authentication/verify-wallet", json=payload),
    )

    statuses = sorted([res1.status_code, res2.status_code])
    # Exactly one request must succeed (200), and the second must be rejected (401)
    assert statuses == [200, 401]

def test_production_security_validation():
    from backend.app.core.config import Settings
    with pytest.raises(ValueError, match="SECRET_KEY must be a cryptographically secure random value"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="decentralid-default-development-secret-key-change-in-prod-32bytes",
            SECURE_COOKIE=True,
        )

    with pytest.raises(ValueError, match="SECURE_COOKIE must be enabled"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a" * 32,
            SECURE_COOKIE=False,
        )
