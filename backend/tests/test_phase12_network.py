import os
import json
import uuid
import time
import pytest
from datetime import datetime, timezone, timedelta
from eth_account import Account
from backend.app.models.organization import Organization
from backend.app.models.network import ApiKey, StorageRecord
from backend.app.services.network.ipfs_service import IpfsStorageService, compute_ipfs_cidv1_raw
from backend.app.services.network.api_key_service import ApiKeyService
from backend.app.services.network.webhook_service import WebhookService
from backend.app.services.credential.signing_service import SigningService


@pytest.mark.asyncio
async def test_ipfs_encryption_storage_and_tamper_detection(test_db):
    org_id = str(uuid.uuid4())
    credential_data = {
        "id": "urn:uuid:test-cred-1234",
        "student": "Vikram Seth",
        "ssn": "000-11-2222", # Sensitive PII
        "degree": "B.Tech Computer Science",
        "gpa": 9.8
    }

    # 1. Encrypt and store
    record, aes_key = await IpfsStorageService.store_encrypted_credential(
        data=credential_data,
        db=test_db,
        organization_id=org_id
    )

    assert record.cid.startswith("b") # CIDv1 multibase 'b'
    assert record.size_bytes > 0
    assert record.encryption_algorithm == "AES-256-GCM"

    # 2. Verify stored bytes on disk are ciphertext, NOT plaintext
    storage_path = os.path.join("storage", "ipfs", record.cid)
    assert os.path.exists(storage_path)
    with open(storage_path, "rb") as f:
        stored_bytes = f.read()

    assert b"000-11-2222" not in stored_bytes
    assert b"Vikram Seth" not in stored_bytes

    # 3. Retrieve and decrypt with valid key
    decrypted = await IpfsStorageService.retrieve_and_decrypt(
        cid=record.cid,
        key=aes_key,
        db=test_db
    )
    assert decrypted["student"] == "Vikram Seth"
    assert decrypted["ssn"] == "000-11-2222"
    assert decrypted["gpa"] == 9.8

    # 4. Tamper detection: alter 1 byte in storage
    tampered_bytes = bytearray(stored_bytes)
    tampered_bytes[-1] ^= 0x01
    with open(storage_path, "wb") as f:
        f.write(tampered_bytes)

    # Retrieval must fail integrity / decrypt check
    with pytest.raises(Exception):
        await IpfsStorageService.retrieve_and_decrypt(
            cid=record.cid,
            key=aes_key,
            db=test_db
        )

    # Restore valid bytes and cleanup
    if os.path.exists(storage_path):
        os.remove(storage_path)


@pytest.mark.asyncio
async def test_api_key_lifecycle_and_developer_authentication(test_db):
    org = Organization(
        id=str(uuid.uuid4()),
        name="Developer Test Univ",
        legal_entity_id="DEV-TEST-UNIV-01",
        domain="devtest.edu",
        on_chain_address="0x1111222233334444555566667777888899990000",
        status="ACTIVE"
    )
    test_db.add(org)
    await test_db.commit()

    # 1. Generate API key
    api_key_obj, raw_key = await ApiKeyService.generate_api_key(
        db=test_db,
        organization_id=org.id,
        name="Production Verifier Integration",
        scopes=["verify", "status"],
        expires_in_days=30
    )

    assert raw_key.startswith("did_live_")
    assert api_key_obj.hashed_key == ApiKeyService.hash_key(raw_key)
    assert api_key_obj.is_active is True

    # 2. Authenticate with valid key
    auth_key = await ApiKeyService.verify_api_key(
        db=test_db,
        raw_key=raw_key,
        required_scope="verify"
    )
    assert auth_key.id == api_key_obj.id
    assert auth_key.last_used_at is not None

    # 3. Invalid prefix fails
    with pytest.raises(Exception):
        await ApiKeyService.verify_api_key(db=test_db, raw_key="invalid_prefix_123")

    # 4. Nonexistent key fails
    with pytest.raises(Exception):
        await ApiKeyService.verify_api_key(db=test_db, raw_key="did_live_nonexistentkey999999999999999999999")

    # 5. Revoked key fails
    api_key_obj.is_active = False
    await test_db.commit()
    with pytest.raises(Exception):
        await ApiKeyService.verify_api_key(db=test_db, raw_key=raw_key)

    # 6. Expired key fails
    api_key_obj.is_active = True
    api_key_obj.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    await test_db.commit()
    with pytest.raises(Exception):
        await ApiKeyService.verify_api_key(db=test_db, raw_key=raw_key)


@pytest.mark.asyncio
async def test_webhook_signature_and_replay_defense(test_db):
    org_id = str(uuid.uuid4())
    sub = await WebhookService.create_subscription(
        db=test_db,
        organization_id=org_id,
        target_url="https://example.com/webhook",
        event_types=["credential.issued"]
    )
    assert len(sub.secret_key) == 64

    payload = {"event": "credential.issued", "credential_id": "test-uuid-123"}
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    now_ts = int(time.time())

    # 1. Compute valid signature
    sig_header = WebhookService.compute_signature(payload_bytes, sub.secret_key, now_ts)
    assert sig_header.startswith(f"t={now_ts},v1=")

    # 2. Verify signature
    assert WebhookService.verify_signature(payload_bytes, sig_header, sub.secret_key) is True

    # 3. Tampered payload fails verification
    tampered_bytes = json.dumps({"event": "credential.issued", "credential_id": "tampered"}, separators=(",", ":")).encode("utf-8")
    assert WebhookService.verify_signature(tampered_bytes, sig_header, sub.secret_key) is False

    # 4. Tampered secret key fails verification
    assert WebhookService.verify_signature(payload_bytes, sig_header, "wrong_secret_key") is False

    # 5. Expired timestamp (> tolerance of 300s) fails replay check
    expired_ts = now_ts - 500
    expired_sig = WebhookService.compute_signature(payload_bytes, sub.secret_key, expired_ts)
    assert WebhookService.verify_signature(payload_bytes, expired_sig, sub.secret_key, tolerance_seconds=300) is False


@pytest.mark.asyncio
async def test_developer_api_routes(client, test_db):
    account = Account.create()
    org = Organization(
        id=str(uuid.uuid4()),
        name="Developer API Testing Org",
        legal_entity_id="DEV-API-TEST-ORG-02",
        domain="dev-api.org",
        on_chain_address=account.address.lower(),
        status="ACTIVE"
    )
    test_db.add(org)
    await test_db.commit()

    # Generate API key
    _, raw_key = await ApiKeyService.generate_api_key(
        db=test_db,
        organization_id=org.id,
        name="Test Dev Key",
        scopes=["verify", "status"]
    )

    headers = {"X-API-Key": raw_key}

    # 1. Missing API Key fails
    res_no_auth = await client.get(f"/api/v1/network/issuers/{account.address}")
    assert res_no_auth.status_code == 401

    # 2. Query issuer status with valid API Key
    res_issuer = await client.get(f"/api/v1/network/issuers/{account.address}", headers=headers)
    assert res_issuer.status_code == 200
    data = res_issuer.json()
    assert data["is_authorized"] is True
    assert data["name"] == "Developer API Testing Org"

    # 3. Unregistered issuer
    res_unreg = await client.get("/api/v1/network/issuers/0x0000000000000000000000000000000000000000", headers=headers)
    assert res_unreg.status_code == 200
    assert res_unreg.json()["is_authorized"] is False

    # 4. Test Developer Verify Endpoint with Signed VC
    doc = {
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "id": "urn:uuid:88888888-9999-aaaa-bbbb-cccccccccccc",
        "type": ["VerifiableCredential", "SkillCertificateCredential"],
        "issuer": {
            "id": f"did:pkh:eip155:31337:{account.address.lower()}",
            "name": "Developer API Testing Org",
        },
        "validFrom": "2026-01-01T00:00:00Z",
        "credentialSubject": {
            "recipientName": "Pooja Hegde",
            "skill": "Solidity Security Auditing"
        }
    }
    signed_vc = SigningService.sign_credential(
        credential_doc=doc,
        private_key=account.key.hex(),
        verification_method=f"did:pkh:eip155:31337:{account.address.lower()}#key-1"
    )

    res_verify = await client.post(
        "/api/v1/network/verify",
        json={"credential": signed_vc},
        headers=headers
    )
    assert res_verify.status_code == 200
    verify_data = res_verify.json()
    assert verify_data["checks"]["signature"] is True
    assert verify_data["checks"]["structural"] is True
