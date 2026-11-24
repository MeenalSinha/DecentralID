import json
import pytest
from eth_account import Account
from eth_account.messages import encode_defunct
from backend.app.services.credential.signing_service import SigningService
from backend.app.services.credential.selective_disclosure_service import SelectiveDisclosureService

@pytest.mark.asyncio
async def test_standards_compliant_w3c_proof_and_tampering():
    account = Account.create()
    doc = {
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "id": "urn:uuid:11111111-2222-3333-4444-555555555555",
        "type": ["VerifiableCredential", "UniversityDegreeCredential"],
        "issuer": {
            "id": f"did:pkh:eip155:31337:{account.address.lower()}",
            "name": "Standard Test University",
        },
        "validFrom": "2026-01-01T00:00:00Z",
        "credentialSubject": {
            "studentName": "Anita Desai",
            "degree": "Master of Science",
            "gpa": 9.5,
        },
    }
    verification_method = f"did:pkh:eip155:31337:{account.address.lower()}#key-1"

    # 1. Sign using standards-compliant SHA-256 ecdsa-jcs-2019
    signed_vc = SigningService.sign_credential(
        credential_doc=doc,
        private_key=account.key.hex(),
        verification_method=verification_method,
        cryptosuite="ecdsa-jcs-2019",
    )
    assert "proof" in signed_vc
    assert signed_vc["proof"]["cryptosuite"] == "ecdsa-jcs-2019"

    # Verify standard proof
    is_valid, recovered, err = SigningService.verify_credential_proof(signed_vc)
    assert is_valid is True
    assert recovered.lower() == account.address.lower()

    # 2. Tampering test: modify GPA
    tampered_vc = dict(signed_vc)
    tampered_vc["credentialSubject"] = {**doc["credentialSubject"], "gpa": 10.0}
    is_tampered_valid, _, _ = SigningService.verify_credential_proof(tampered_vc)
    assert is_tampered_valid is False

    # 3. Backward compatibility: verify legacy Keccak-signed credential
    legacy_vc = SigningService.sign_credential(
        credential_doc=doc,
        private_key=account.key.hex(),
        verification_method=verification_method,
        cryptosuite="ecdsa-jcs-2019-keccak",
    )
    assert legacy_vc["proof"]["cryptosuite"] == "ecdsa-jcs-2019-keccak"
    is_legacy_valid, rec_leg, _ = SigningService.verify_credential_proof(legacy_vc)
    assert is_legacy_valid is True
    assert rec_leg.lower() == account.address.lower()

@pytest.mark.asyncio
async def test_cryptographic_selective_disclosure():
    claims = {
        "studentName": "Priya Patel",
        "degree": "Bachelor of Technology",
        "major": "Computer Engineering",
        "gpa": 8.9,
        "dateOfBirth": "2002-05-14",
    }

    # 1. Generate blinded claim commitments
    salts, digests, root_commitment = SelectiveDisclosureService.create_blinded_claims(claims)
    assert len(salts) == 5
    assert len(digests) == 5
    assert len(root_commitment) == 64

    # 2. Disclose only studentName and degree (mask major, gpa, and dateOfBirth)
    disclosed_keys = ["studentName", "degree"]
    proof = SelectiveDisclosureService.generate_disclosure_proof(
        full_claims=claims,
        claim_salts=salts,
        disclosed_keys=disclosed_keys,
    )

    assert set(proof["disclosedClaims"].keys()) == {"studentName", "degree"}
    assert set(proof["blindedCommitments"].keys()) == {"major", "gpa", "dateOfBirth"}

    # 3. Verify valid selective disclosure
    is_valid, verified_claims, err = SelectiveDisclosureService.verify_selective_disclosure(
        proof, root_commitment
    )
    assert is_valid is True
    assert verified_claims["studentName"] == "Priya Patel"
    assert verified_claims["degree"] == "Bachelor of Technology"
    assert "dateOfBirth" not in verified_claims

    # 4. Tamper with disclosed claim value -> must be rejected
    tampered_proof = json.loads(json.dumps(proof))
    tampered_proof["disclosedClaims"]["studentName"]["value"] = "Priya FakeName"
    is_tamper_ok, _, _ = SelectiveDisclosureService.verify_selective_disclosure(
        tampered_proof, root_commitment
    )
    assert is_tamper_ok is False

@pytest.mark.asyncio
async def test_client_side_wallet_signing_workflow(client):
    issuer_acc = Account.create()
    # Authenticate issuer
    c_res = await client.post("/api/v1/authentication/challenge", json={
        "wallet_address": issuer_acc.address, "chain_id": 31337, "domain": "localhost", "uri": "http://localhost:5173"
    })
    msg = c_res.json()["message"]
    s = issuer_acc.sign_message(encode_defunct(text=msg))
    sig_hex = s.signature.hex() if s.signature.hex().startswith("0x") else f"0x{s.signature.hex()}"
    v_res = await client.post("/api/v1/authentication/verify-wallet", json={
        "wallet_address": issuer_acc.address, "nonce": c_res.json()["nonce"], "signature": sig_hex
    })
    assert v_res.status_code == 200

    # Register organization
    org_res = await client.post("/api/v1/organizations", json={
        "name": "Indian Institute of Science",
        "jurisdiction": "IN-KA",
        "on_chain_address": issuer_acc.address,
        "registration_number": "IISC-2026-01"
    })
    org_id = org_res.json()["id"]

    # Register operational signing key for organization
    signer_key_acc = Account.create()
    key_res = await client.post(f"/api/v1/organizations/{org_id}/signing-keys", json={
        "public_key_address": signer_key_acc.address,
        "key_type": "secp256k1",
        "valid_until": 1924991999
    })
    assert key_res.status_code == 201

    # Prepare credential
    holder_acc = Account.create()
    prep_res = await client.post("/api/v1/credentials/prepare", json={
        "organization_id": org_id,
        "recipient_address": holder_acc.address,
        "schema_type": "UniversityDegreeCredential",
        "claims": {
            "studentName": "Vikram Seth",
            "degree": "Doctor of Philosophy",
            "major": "Quantum Information",
            "institutionName": "Indian Institute of Science",
            "graduationDate": "2026-05-10"
        }
    })
    assert prep_res.status_code == 201
    cred_id = prep_res.json()["credential_id"]

    # Submit for approval & Approve credential (by admin)
    sub_res = await client.post(f"/api/v1/credentials/{cred_id}/submit-approval")
    assert sub_res.status_code == 200

    # For approval test, login as another admin or super admin to satisfy separation of duties
    admin2 = Account.create()
    c2 = await client.post("/api/v1/authentication/challenge", json={
        "wallet_address": admin2.address, "chain_id": 31337, "domain": "localhost", "uri": "http://localhost:5173"
    })
    s2 = admin2.sign_message(encode_defunct(text=c2.json()["message"]))
    await client.post("/api/v1/authentication/verify-wallet", json={
        "wallet_address": admin2.address, "nonce": c2.json()["nonce"], "signature": s2.signature.hex()
    })
    # Add admin2 as INSTITUTION_ADMIN
    client.cookies.set("decentralid_session", v_res.cookies.get("decentralid_session"))
    await client.post(f"/api/v1/organizations/{org_id}/members", json={
        "user_address": admin2.address,
        "role": "INSTITUTION_ADMIN"
    })

    # Switch session to admin2 to approve
    client.cookies.clear()
    c2_new = await client.post("/api/v1/authentication/challenge", json={
        "wallet_address": admin2.address, "chain_id": 31337, "domain": "localhost", "uri": "http://localhost:5173"
    })
    s2_new = admin2.sign_message(encode_defunct(text=c2_new.json()["message"]))
    s2_hex = f"0x{s2_new.signature.hex()}" if not s2_new.signature.hex().startswith("0x") else s2_new.signature.hex()
    v2_res = await client.post("/api/v1/authentication/verify-wallet", json={
        "wallet_address": admin2.address, "nonce": c2_new.json()["nonce"], "signature": s2_hex
    })
    assert v2_res.status_code == 200
    appr_res = await client.post(f"/api/v1/credentials/{cred_id}/approve")
    assert appr_res.status_code == 200

    # 1. Fetch signing payload (no private key sent)
    payload_res = await client.get(
        f"/api/v1/credentials/{cred_id}/signing-payload?signer_address={signer_key_acc.address}"
    )
    assert payload_res.status_code == 200
    signing_payload = payload_res.json()
    digest_hex = signing_payload["signing_digest"]
    assert digest_hex.startswith("0x")

    # 2. Local client-side wallet signs the digest (private key never sent to server)
    digest_bytes = bytes.fromhex(digest_hex[2:])
    local_signable = encode_defunct(primitive=digest_bytes)
    client_signature = signer_key_acc.sign_message(local_signable).signature.hex()

    # 3. Complete signing with signature only
    complete_res = await client.post(
        f"/api/v1/credentials/{cred_id}/complete-signing",
        json={
            "signature": f"0x{client_signature}",
            "signer_address": signer_key_acc.address,
            "cryptosuite": "ecdsa-jcs-2019"
        }
    )
    assert complete_res.status_code == 200
    signed_data = complete_res.json()
    assert signed_data["status"] == "signed"
    assert signed_data["workflow_status"] == "PENDING_BLOCKCHAIN_REGISTRATION"
    assert signed_data["credential"]["proof"]["cryptosuite"] == "ecdsa-jcs-2019"
