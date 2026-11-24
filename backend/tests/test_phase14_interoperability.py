import pytest
from httpx import AsyncClient, ASGITransport
from eth_account import Account
import uuid

from backend.app.main import app
from backend.app.services.interoperability.did_resolver import universal_did_resolver, DIDResolutionError
from backend.app.services.interoperability.credential_portability import CredentialPortabilityService, CredentialPortabilityError
from backend.app.services.credential.signing_service import SigningService

@pytest.mark.asyncio
async def test_did_resolution():
    # 1. Test did:pkh
    pkh_did = "did:pkh:eip155:137:0x71C836e2f1f0aF9b34371C790C9550D6f6581451"
    res = await universal_did_resolver.resolve(pkh_did)
    assert res["didDocument"]["id"] == pkh_did
    assert len(res["didDocument"]["verificationMethod"]) == 1
    assert res["didDocument"]["verificationMethod"][0]["blockchainAccountId"] == "eip155:137:0x71c836e2f1f0af9b34371c790c9550d6f6581451"
    
    # 2. Test did:key
    key_did = "did:key:zQ3shokFTS3vbcHcHyioSVdEGcrmRTCQTdUmQD251CsUV22oh"
    res_key = await universal_did_resolver.resolve(key_did)
    assert res_key["didDocument"]["id"] == key_did
    assert res_key["didDocument"]["verificationMethod"][0]["publicKeyMultibase"] == "zQ3shokFTS3vbcHcHyioSVdEGcrmRTCQTdUmQD251CsUV22oh"

    # 3. Test did:web
    web_did = "did:web:iitb.ac.in"
    res_web = await universal_did_resolver.resolve(web_did)
    assert res_web["didDocument"]["id"] == web_did
    assert res_web["didDocument"]["verificationMethod"][0]["domain"] == "iitb.ac.in"

    # 4. Invalid DID rejection
    with pytest.raises(DIDResolutionError):
        await universal_did_resolver.resolve("did:unknown:12345")

@pytest.mark.asyncio
async def test_credential_import_and_export():
    sample_vc = {
        "@context": ["https://www.w3.org/2018/credentials/v1"],
        "id": "urn:uuid:test-cred-123",
        "type": ["VerifiableCredential", "AcademicDegreeCredential"],
        "issuer": "0x71c836e2f1f0af9b34371c790c9550d6f6581451",
        "issuanceDate": "2026-11-24T12:00:00Z",
        "credentialSubject": {
            "id": "did:pkh:eip155:137:0x1111111111111111111111111111111111111111",
            "degree": "Bachelor of Technology"
        },
        "proof": {
            "type": "DataIntegrityProof",
            "cryptosuite": "ecdsa-jcs-2019",
            "verificationMethod": "did:pkh:eip155:137:0x71c836e2f1f0af9b34371c790c9550d6f6581451#blockchainAccountId",
            "proofValue": "0x1234"
        }
    }
    
    # Export to W3C v2
    exported_v2 = CredentialPortabilityService.export_credential_w3c_v2(sample_vc)
    assert "https://www.w3.org/ns/credentials/v2" in exported_v2["@context"]
    assert exported_v2["issuer"].startswith("did:pkh:eip155:137:")
    assert "validFrom" in exported_v2
    
    # Import external credential
    imported = CredentialPortabilityService.import_external_credential(sample_vc)
    assert imported["is_imported"] is True
    assert imported["provenance_verified"] is True
    assert imported["origin_issuer"] == "0x71c836e2f1f0af9b34371c790c9550d6f6581451"

    # Test rejection of malformed credentials
    with pytest.raises(CredentialPortabilityError):
        CredentialPortabilityService.import_external_credential({"invalid": "data"})

@pytest.mark.asyncio
async def test_external_verification_adapter():
    signer = Account.create()
    issuer_did = f"did:pkh:eip155:137:{signer.address.lower()}"
    
    doc = {
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "id": "urn:uuid:test-cred-interop",
        "type": ["VerifiableCredential", "AcademicDegreeCredential"],
        "issuer": issuer_did,
        "validFrom": "2026-11-24T12:00:00Z",
        "credentialSubject": {
            "student_id": "STUDENT-101",
            "degree": "Computer Science"
        }
    }
    
    # Sign using standard W3C Data Integrity proof
    signed_vc = SigningService.sign_credential(
        credential_doc=doc,
        private_key=signer.key.hex(),
        verification_method=f"{issuer_did}#blockchainAccountId",
        cryptosuite="ecdsa-jcs-2019"
    )
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Verify signed credential
        verify_resp = await ac.post("/api/v1/interop/verify-external", json={
            "credential_or_presentation": signed_vc,
            "expected_issuer_did": issuer_did
        })
        assert verify_resp.status_code == 200
        data = verify_resp.json()
        assert data["is_valid"] is True
        assert data["status"] == "VALID"
        assert data["issuer_did"] == issuer_did
        assert data["cryptosuite"] == "ecdsa-jcs-2019"

        # Test tampering detection
        tampered_vc = dict(signed_vc)
        tampered_vc["credentialSubject"] = {"student_id": "STUDENT-101", "degree": "Hacked"}
        tamper_resp = await ac.post("/api/v1/interop/verify-external", json={
            "credential_or_presentation": tampered_vc
        })
        assert tamper_resp.status_code == 200
        tamper_data = tamper_resp.json()
        assert tamper_data["is_valid"] is False
        assert tamper_data["error_code"] == "SIGNATURE_VERIFICATION_FAILED"

        # Test OID4VCI endpoint
        oid_resp = await ac.get("/api/v1/interop/well-known/openid-credential-issuer")
        assert oid_resp.status_code == 200
        assert "credentials_supported" in oid_resp.json()
