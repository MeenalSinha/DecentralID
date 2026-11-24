import pytest
import datetime
from httpx import AsyncClient, ASGITransport
from eth_account import Account

from backend.app.main import app
from backend.app.services.credential.signing_service import SigningService
from backend.app.services.offline.offline_verifier import OfflineVerificationService

@pytest.mark.asyncio
async def test_offline_verification_freshness_rules():
    issuer = Account.create()
    authority = Account.create()
    
    doc = {
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "id": "urn:uuid:test-cred-offline",
        "type": ["VerifiableCredential", "AcademicDegreeCredential"],
        "issuer": issuer.address,
        "validFrom": "2026-11-24T12:00:00Z",
        "credentialSubject": {
            "student_name": "Arjun Sharma",
            "degree": "B.Tech Electrical"
        }
    }
    
    # Sign credential with issuer key
    signed_vc = SigningService.sign_credential(
        credential_doc=doc,
        private_key=issuer.key.hex(),
        verification_method=issuer.address,
        cryptosuite="ecdsa-jcs-2019"
    )

    # 1. Test Fresh Offline Package (< 24h)
    package_fresh = OfflineVerificationService.create_offline_package(
        credential=signed_vc,
        status="ACTIVE",
        signing_key=authority.key.hex()
    )
    
    res_fresh = OfflineVerificationService.verify_offline_package(
        package=package_fresh,
        max_offline_age_seconds=86400
    )
    assert res_fresh["is_valid"] is True
    assert res_fresh["status"] == "VALID_OFFLINE"
    assert res_fresh["freshness"] == "FRESH"
    assert res_fresh["signer_address"].lower() == issuer.address.lower()

    # 2. Test CRITICAL FRESHNESS RULE: Stale Snapshot returns INDETERMINATE, never VALID
    now = datetime.datetime.now(datetime.timezone.utc)
    simulated_future_time = now + datetime.timedelta(days=2) # 48 hours later (stale snapshot)
    
    res_stale = OfflineVerificationService.verify_offline_package(
        package=package_fresh,
        max_offline_age_seconds=86400,
        current_time=simulated_future_time
    )
    assert res_stale["is_valid"] is False
    assert res_stale["status"] == "INDETERMINATE"
    assert res_stale["error_code"] == "STALE_STATUS_DATA"
    assert "stale" in res_stale["reason"].lower()

    # 3. Test Offline Revocation Detection
    package_revoked = OfflineVerificationService.create_offline_package(
        credential=signed_vc,
        status="REVOKED",
        signing_key=authority.key.hex()
    )
    res_revoked = OfflineVerificationService.verify_offline_package(package_revoked)
    assert res_revoked["is_valid"] is False
    assert res_revoked["status"] == "REVOKED"

    # 4. Test Credential Tampering Detection
    tampered_package = dict(package_fresh)
    tampered_package["credential"] = dict(signed_vc)
    tampered_package["credential"]["credentialSubject"] = {"student_name": "Tampered"}
    
    res_tampered = OfflineVerificationService.verify_offline_package(tampered_package)
    assert res_tampered["is_valid"] is False
    assert res_tampered["status"] == "INVALID"

@pytest.mark.asyncio
async def test_offline_verification_endpoint():
    issuer = Account.create()
    authority = Account.create()
    
    doc = {
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "id": "urn:uuid:test-cred-offline-api",
        "type": ["VerifiableCredential", "AcademicDegreeCredential"],
        "issuer": issuer.address,
        "validFrom": "2026-11-24T12:00:00Z",
        "credentialSubject": {"student_id": "STU-888"}
    }
    signed_vc = SigningService.sign_credential(
        credential_doc=doc,
        private_key=issuer.key.hex(),
        verification_method=issuer.address,
        cryptosuite="ecdsa-jcs-2019"
    )
    package = OfflineVerificationService.create_offline_package(
        credential=signed_vc,
        status="ACTIVE",
        signing_key=authority.key.hex()
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/offline/verify", json={
            "offline_package": package,
            "max_offline_age_seconds": 86400
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is True
        assert data["status"] == "VALID_OFFLINE"
