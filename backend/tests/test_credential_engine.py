import pytest
import json
import datetime
from eth_account import Account
from eth_account.messages import encode_defunct
from backend.app.models.organization import Organization, OrganizationMembership, SigningKey
from backend.app.models.user import User, Wallet
from backend.app.core.constants import UserRole, CredentialWorkflowStatus, CredentialLifecycleStatus
from backend.app.services.credential.canonicalization import CanonicalizationService
from backend.app.services.credential.encryption_service import EncryptionService
from backend.app.services.credential.commitment_service import CommitmentService
from backend.app.services.credential.signing_service import SigningService
from backend.app.services.credential.preparation_service import PreparationService
from backend.app.services.credential.issuance_service import IssuanceService
from backend.app.services.credential.verification_service import VerificationService
from backend.app.schemas.credential_schemas.registry import CredentialSchemaRegistry

def test_rfc8785_canonicalization():
    # Unordered dict with nested objects and lists
    data = {
        "zeta": 1,
        "alpha": "hello",
        "nested": {
            "b": [3, 2, 1],
            "a": True,
        },
    }
    canonical = CanonicalizationService.canonicalize(data)
    expected = b'{"alpha":"hello","nested":{"a":true,"b":[3,2,1]},"zeta":1}'
    assert canonical == expected

def test_aes_gcm_storage_encryption_and_decryption():
    secret_payload = {"studentName": "Aarav Sharma", "gpa": 3.95, "aadhaarHash": "0x1234567890abcdef"}
    encrypted_b64 = EncryptionService.encrypt_json(secret_payload)
    
    # Must not contain plaintext in base64 string
    assert "Aarav Sharma" not in encrypted_b64
    
    # Decrypt and verify
    decrypted = EncryptionService.decrypt_json(encrypted_b64)
    assert decrypted == secret_payload

    # Tampering with ciphertext MUST fail authentication
    raw_tampered = list(encrypted_b64)
    raw_tampered[20] = "A" if raw_tampered[20] != "A" else "B"
    with pytest.raises(Exception):
        EncryptionService.decrypt_json("".join(raw_tampered))

def test_commitment_generation_and_constant_time_verification():
    subject = {"studentName": "Aarav Sharma", "degree": "B.Tech"}
    commitment, salt = CommitmentService.generate_subject_commitment(subject)
    
    assert commitment.startswith("0x")
    assert len(commitment) == 66
    assert len(salt) == 32

    # Verification with correct salt succeeds
    assert CommitmentService.verify_commitment(subject, salt, commitment) is True

    # Verification with wrong salt fails
    wrong_salt = b"0" * 32
    assert CommitmentService.verify_commitment(subject, wrong_salt, commitment) is False

    # Verification with tampered claim fails
    tampered_subject = {"studentName": "Malicious Attacker", "degree": "B.Tech"}
    assert CommitmentService.verify_commitment(tampered_subject, salt, commitment) is False

def test_schema_registry_validation():
    # Valid degree claims
    valid_claims = {
        "studentName": "Priya Patel",
        "degree": "Bachelor of Science",
        "major": "Computer Science",
        "institutionName": "National Institute of Technology",
        "graduationDate": "2026-05-15",
    }
    is_ok, errors = CredentialSchemaRegistry.validate_claims("UniversityDegreeCredential", valid_claims)
    assert is_ok is True
    assert len(errors) == 0

    # Missing required field
    invalid_claims = {
        "studentName": "Priya Patel",
        "degree": "Bachelor of Science",
    }
    is_ok, errors = CredentialSchemaRegistry.validate_claims("UniversityDegreeCredential", invalid_claims)
    assert is_ok is False
    assert any("major" in err for err in errors)

@pytest.mark.asyncio
async def test_w3c_proof_signing_and_independent_verification():
    issuer_acc = Account.create()
    subject_acc = Account.create()

    doc = {
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "id": "urn:uuid:12345678-1234-5678-1234-567812345678",
        "type": ["VerifiableCredential", "UniversityDegreeCredential"],
        "issuer": f"did:pkh:eip155:31337:{issuer_acc.address.lower()}",
        "credentialSubject": {
            "id": f"did:pkh:eip155:31337:{subject_acc.address.lower()}",
            "studentName": "Priya Patel",
            "degree": "B.Tech",
        },
    }

    verification_method = f"did:pkh:eip155:31337:{issuer_acc.address.lower()}#key-1"

    # Sign credential
    signed_vc = SigningService.sign_credential(
        credential_doc=doc,
        private_key=issuer_acc.key.hex(),
        verification_method=verification_method,
    )

    assert "proof" in signed_vc
    assert signed_vc["proof"]["type"] == "DataIntegrityProof"
    assert signed_vc["proof"]["cryptosuite"] == "ecdsa-jcs-2019"
    assert signed_vc["proof"]["proofValue"].startswith("0x")

    # Verify signature independently
    is_valid, recovered_signer, err = SigningService.verify_credential_proof(signed_vc)
    assert is_valid is True
    assert recovered_signer.lower() == issuer_acc.address.lower()

    # Tampering with claims MUST cause signature verification failure
    tampered_vc = json.loads(json.dumps(signed_vc))
    tampered_vc["credentialSubject"]["degree"] = "PhD (Fabricated)"
    is_valid_t, _, err_t = SigningService.verify_credential_proof(tampered_vc)
    assert is_valid_t is False
    assert "does not match" in err_t or "failed" in err_t

@pytest.mark.asyncio
async def test_full_credential_preparation_approval_and_issuance_workflow(client, test_db):
    # Setup test users and institution
    operator = User(full_name="Operator User", role=UserRole.AUTHORIZED_ISSUER.value)
    approver = User(full_name="Admin Approver", role=UserRole.INSTITUTION_ADMIN.value)
    test_db.add_all([operator, approver])
    await test_db.flush()

    org_address = Account.create().address.lower()
    org = Organization(
        name="IIT Bombay",
        legal_entity_id="EDU-IITB-001",
        on_chain_address=org_address,
        status="AUTHORIZED",
    )
    test_db.add(org)
    await test_db.flush()

    # Assign memberships (Operator is also an Admin in the org, but cannot approve their own credential)
    m1 = OrganizationMembership(organization_id=org.id, user_id=operator.id, role="ADMIN", status="ACTIVE")
    m2 = OrganizationMembership(organization_id=org.id, user_id=approver.id, role="ADMIN", status="ACTIVE")
    test_db.add_all([m1, m2])
    await test_db.commit()

    recipient_acc = Account.create()
    claims = {
        "studentName": "Aarav Sharma",
        "degree": "Bachelor of Technology",
        "major": "Computer Science & Engineering",
        "institutionName": "IIT Bombay",
        "graduationDate": "2026-06-15",
    }

    # 1. Preparation by Operator
    cred_record, w3c_doc = await PreparationService.prepare_credential(
        db=test_db,
        operator_user_id=operator.id,
        organization_id=org.id,
        recipient_address=recipient_acc.address,
        schema_type="UniversityDegreeCredential",
        claims=claims,
    )
    assert cred_record.workflow_status == CredentialWorkflowStatus.PREPARED.value
    assert cred_record.commitment.startswith("0x")

    # 2. Submit for Approval
    submitted = await IssuanceService.submit_for_approval(test_db, cred_record.id, operator.id)
    assert submitted.workflow_status == CredentialWorkflowStatus.PENDING_APPROVAL.value

    # 3. Separation of Duties: Operator cannot approve their own credential
    with pytest.raises(Exception, match="Separation of duties violation"):
        await IssuanceService.approve_credential(test_db, cred_record.id, operator.id)

    # 4. Admin Approver Approves
    approved = await IssuanceService.approve_credential(test_db, cred_record.id, approver.id)
    assert approved.workflow_status == CredentialWorkflowStatus.APPROVED.value
    assert approved.approved_by == approver.id

    # 5. Cryptographic Signing with Issuer Key
    issuer_signing_acc = Account.create()
    # Register signing key in org
    sk = SigningKey(
        organization_id=org.id,
        public_key_address=issuer_signing_acc.address.lower(),
        key_type="secp256k1",
        status="ACTIVE",
    )
    test_db.add(sk)
    await test_db.commit()

    signed_cred, signed_vc = await IssuanceService.sign_credential(
        db=test_db,
        credential_record_id=cred_record.id,
        signing_key_private_key=issuer_signing_acc.key.hex(),
        operator_user_id=operator.id,
    )
    assert signed_cred.workflow_status == CredentialWorkflowStatus.PENDING_BLOCKCHAIN_REGISTRATION.value
    assert "proof" in signed_vc

    # 6. Blockchain Confirmation
    tx_hash = "0x" + "a" * 64
    confirmed = await IssuanceService.confirm_blockchain_registration(test_db, cred_record.id, tx_hash)
    assert confirmed.workflow_status == CredentialWorkflowStatus.ISSUED.value
    assert confirmed.tx_hash == tx_hash

    # 7. Independent Verification Service validates the issued credential
    verification = await VerificationService.verify_credential(signed_vc, db=test_db)
    assert verification.is_valid is True
    assert verification.signature_valid is True
    assert verification.issuer_authorized is True
    assert verification.signing_key_valid is True
    assert verification.lifecycle_status == "ACTIVE"
    assert len(verification.errors) == 0
