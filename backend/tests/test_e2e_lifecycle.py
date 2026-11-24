import os
import json
import uuid
import time
import pytest
from datetime import datetime, timezone
from eth_account import Account
from eth_account.messages import encode_defunct

from backend.app.core.constants import UserRole, CredentialLifecycleStatus
from backend.app.models.user import User
from backend.app.models.organization import Organization, OrganizationMembership, SigningKey
from backend.app.models.credential import Credential
from backend.app.services.intelligence.extraction_engine import ExtractionEngine
from backend.app.services.credential.preparation_service import PreparationService
from backend.app.services.credential.issuance_service import IssuanceService
from backend.app.services.credential.signing_service import SigningService
from backend.app.services.credential.selective_disclosure_service import SelectiveDisclosureService
from backend.app.services.network.ipfs_service import IpfsStorageService
from backend.app.services.network.api_key_service import ApiKeyService
from backend.app.services.network.webhook_service import WebhookService
from backend.app.services.credential.verification_service import VerificationService


@pytest.mark.asyncio
async def test_full_platform_end_to_end_lifecycle(client, test_db):
    """
    Comprehensive End-to-End Test covering Phases 0 through 13.
    """
    issuer_wallet = Account.create()
    preparer_wallet = Account.create()
    approver_wallet = Account.create()
    holder_wallet = Account.create()

    # 1. Onboard Institution
    org_id = str(uuid.uuid4())
    org = Organization(
        id=org_id,
        name="IIT Delhi Digital Trust Institute",
        legal_entity_id="IITD-TRUST-2036",
        domain="iitd.ac.in",
        on_chain_address=issuer_wallet.address.lower(),
        status="ACTIVE"
    )
    test_db.add(org)

    # Register Signing Key
    key_id = str(uuid.uuid4())
    signing_key = SigningKey(
        id=key_id,
        organization_id=org_id,
        public_key_address=issuer_wallet.address.lower(),
        key_type="secp256k1",
        status="ACTIVE",
        valid_until=int(time.time()) + 86400 * 365
    )
    test_db.add(signing_key)

    # Register Officers (Separation of Duties)
    user_preparer = User(id=str(uuid.uuid4()), email="preparer@iitd.ac.in", full_name="Preparer Officer", role=UserRole.AUTHORIZED_ISSUER.value)
    user_approver = User(id=str(uuid.uuid4()), email="approver@iitd.ac.in", full_name="Approver Dean", role=UserRole.INSTITUTION_ADMIN.value)
    test_db.add_all([user_preparer, user_approver])

    test_db.add(OrganizationMembership(organization_id=org_id, user_id=user_preparer.id, role=UserRole.AUTHORIZED_ISSUER.value))
    test_db.add(OrganizationMembership(organization_id=org_id, user_id=user_approver.id, role=UserRole.INSTITUTION_ADMIN.value))
    await test_db.commit()

    # 2. Phase 10 Intelligence: Document Intake & Extraction
    sample_certificate_text = """
    DELHI TECHNOLOGICAL UNIVERSITY
    OFFICIAL DEGREE CERTIFICATE

    This is to certify that Rahul Sharma
    Student ID: DTU/2022/CS/1042
    has successfully completed the Degree of Bachelor of Technology
    in Computer Science and Engineering
    Conferred on: 2025-06-15
    Cumulative Grade: 9.20 / 10.0
    """
    schema_type, extracted_fields, overall_conf = ExtractionEngine.process_document_text(sample_certificate_text)
    assert schema_type == "UniversityDegreeCredential"
    assert extracted_fields["studentName"]["value"] == "Rahul Sharma"
    assert extracted_fields["degree"]["value"] == "Bachelor Of Technology"
    assert extracted_fields["gpa"]["value"] == 9.2
    assert overall_conf > 0.70

    # 3. Preparation Service: Schema Validation & Draft Credential
    claims_payload = {
        "studentName": extracted_fields["studentName"]["value"],
        "degree": extracted_fields["degree"]["value"],
        "gpa": extracted_fields["gpa"]["value"],
        "major": "Computer Science and Engineering",
        "institutionName": "Delhi Technological University",
        "graduationDate": "2025-06-15"
    }
    cred, salt = await PreparationService.prepare_credential(
        db=test_db,
        operator_user_id=user_preparer.id,
        organization_id=org_id,
        recipient_address=holder_wallet.address.lower(),
        schema_type="UniversityDegreeCredential",
        claims=claims_payload
    )
    assert cred.workflow_status == "PREPARED"
    assert cred.w3c_id.startswith("urn:uuid:")

    # 4. Separation of Duties: Submit & Approve
    await IssuanceService.submit_for_approval(
        db=test_db,
        credential_record_id=cred.id,
        user_id=user_preparer.id
    )
    
    # Preparer cannot self-approve
    with pytest.raises(Exception):
        await IssuanceService.approve_credential(
            db=test_db,
            credential_record_id=cred.id,
            approver_user_id=user_preparer.id
        )

    # Authorized Approver approves
    approved_cred = await IssuanceService.approve_credential(
        db=test_db,
        credential_record_id=cred.id,
        approver_user_id=user_approver.id
    )
    assert approved_cred.workflow_status == "APPROVED"

    # 5. Phase 11 Cryptography: Standards-Compliant W3C Signing (ecdsa-jcs-2019)
    payload_info = await IssuanceService.get_signing_payload(
        db=test_db,
        credential_record_id=cred.id,
        operator_user_id=user_approver.id,
        signer_address=issuer_wallet.address.lower()
    )
    digest_hex = payload_info["signing_digest"]
    digest_bytes = bytes.fromhex(digest_hex[2:])
    assert len(digest_bytes) == 32

    # Institutional officer signs digest locally via client wallet
    local_signable = encode_defunct(primitive=digest_bytes)
    sig = issuer_wallet.sign_message(local_signable)
    sig_hex = f"0x{sig.signature.hex()}" if not sig.signature.hex().startswith("0x") else sig.signature.hex()

    issued_cred, signed_vc = await IssuanceService.complete_signing_with_signature(
        db=test_db,
        credential_record_id=cred.id,
        signature=sig_hex,
        signer_address=issuer_wallet.address.lower(),
        operator_user_id=user_approver.id
    )
    assert signed_vc["proof"]["cryptosuite"] == "ecdsa-jcs-2019"

    # Transition to ACTIVE status in lifecycle table
    issued_cred.status = CredentialLifecycleStatus.ACTIVE.value
    await test_db.commit()

    # 6. Phase 12 Network: Encrypt and archive to IPFS
    storage_rec, aes_key = await IpfsStorageService.store_encrypted_credential(
        data=signed_vc,
        db=test_db,
        organization_id=org_id
    )
    assert storage_rec.cid.startswith("b")
    retrieved_vc = await IpfsStorageService.retrieve_and_decrypt(
        cid=storage_rec.cid,
        key=aes_key,
        db=test_db
    )
    assert retrieved_vc["credentialSubject"]["studentName"] == "Rahul Sharma"

    # 7. Salted Merkle Selective Disclosure Verifiable Presentation
    claims = signed_vc["credentialSubject"]
    claim_salts, claim_digests, root_commit = SelectiveDisclosureService.create_blinded_claims(claims)
    proof = SelectiveDisclosureService.generate_disclosure_proof(
        full_claims=claims,
        claim_salts=claim_salts,
        disclosed_keys=["degree"]
    )
    is_sd_valid, disclosed, _ = SelectiveDisclosureService.verify_selective_disclosure(
        disclosure_proof=proof,
        expected_root_commitment=root_commit
    )
    assert is_sd_valid is True
    assert "degree" in disclosed
    assert "studentName" not in disclosed

    # 8. Phase 12 Developer API Verification
    api_key_obj, raw_api_key = await ApiKeyService.generate_api_key(
        db=test_db,
        organization_id=org_id,
        name="Third Party Verifier Corp",
        scopes=["verify", "status"]
    )
    headers = {"X-API-Key": raw_api_key}

    res_verify = await client.post(
        "/api/v1/network/verify",
        json={"credential": signed_vc},
        headers=headers
    )
    assert res_verify.status_code == 200
    assert res_verify.json()["checks"]["signature"] is True

    # 9. Webhook Delivery Infrastructure
    webhook_sub = await WebhookService.create_subscription(
        db=test_db,
        organization_id=org_id,
        target_url="https://mock-verifier.org/webhooks",
        event_types=["credential.issued", "credential.revoked"]
    )
    issued_event = {"event": "credential.issued", "credential_id": str(cred.id)}
    sig_header = WebhookService.compute_signature(
        payload_bytes=json.dumps(issued_event, separators=(",", ":"), sort_keys=True).encode("utf-8"),
        secret_key=webhook_sub.secret_key,
        timestamp=int(time.time())
    )
    assert WebhookService.verify_signature(
        payload_bytes=json.dumps(issued_event, separators=(",", ":"), sort_keys=True).encode("utf-8"),
        signature_header=sig_header,
        secret_key=webhook_sub.secret_key
    ) is True

    # 10. Credential Revocation Lifecycle
    issued_cred.status = CredentialLifecycleStatus.REVOKED.value
    issued_cred.revocation_reason = "Administrative error"
    issued_cred.revoked_at = datetime.now(timezone.utc)
    await test_db.commit()

    # Re-verify through VerificationService
    revoked_check = await VerificationService.verify_credential(credential=signed_vc, db=test_db)
    assert revoked_check.lifecycle_status == "REVOKED"
    assert revoked_check.is_valid is False

    # 11. Phase 13 Platform Analytics
    res_analytics = await client.get("/api/v1/analytics/platform")
    assert res_analytics.status_code == 200
    analytics_data = res_analytics.json()
    assert analytics_data["platform_status"] == "OPERATIONAL"
    assert analytics_data["organizations"]["total"] >= 1
    assert analytics_data["credentials"]["revoked"] >= 1
    assert analytics_data["signing_keys"]["active_authorized_keys"] >= 1
