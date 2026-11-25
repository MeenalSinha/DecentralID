"""
DecentralID Demo Data Seeder
Populates decentralid.db with genuine, cryptographically valid records:
- Accredited Institution: IIT Delhi Digital Trust Institute
- Officers: Approver Dean, Preparer Officer, Student Holder (Rahul Sharma)
- Operational Signing Keys (secp256k1)
- Active Session Token
- Cryptographically signed W3C Verifiable Credentials (Active, Suspended, Revoked, Pending, Approved)
- Selective Disclosure Presentation Share
- Document Intelligence Ingestion Record
- Developer API Key & Webhook Subscriptions
"""

import asyncio
import datetime
import hashlib
import json
import os
import sys
import uuid
import time
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import keccak

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import AsyncSessionLocal, engine
from backend.app.core.constants import UserRole, CredentialWorkflowStatus, CredentialLifecycleStatus
from backend.app.models.user import User, Wallet
from backend.app.models.organization import Organization, OrganizationMembership, SigningKey
from backend.app.models.credential import Credential
from backend.app.models.session import Session
from backend.app.models.presentation import PresentationShare
from backend.app.models.intelligence import DocumentUpload, ExtractedCredentialData
from backend.app.models.network import ApiKey, WebhookSubscription, WebhookDelivery
from backend.app.services.credential.commitment_service import CommitmentService
from backend.app.services.credential.encryption_service import EncryptionService
from backend.app.services.credential.signing_service import SigningService
from backend.app.services.credential.selective_disclosure_service import SelectiveDisclosureService


async def seed():
    # Hardhat Known Accounts
    # Account 0: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
    priv_key_0 = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    account_0 = Account.from_key(priv_key_0)
    addr_0 = account_0.address.lower()

    # Account 1: 0x70997970C51812dc3A010C7d01b50e0d17dc79C8
    priv_key_1 = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
    account_1 = Account.from_key(priv_key_1)
    addr_1 = account_1.address.lower()

    # Account 2 (Holder Rahul Sharma): 0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC
    addr_holder = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC".lower()

    async with AsyncSessionLocal() as db:
        print("[1/8] Cleaning existing demo data...")
        await db.execute(Credential.__table__.delete())
        await db.execute(SigningKey.__table__.delete())
        await db.execute(OrganizationMembership.__table__.delete())
        await db.execute(Organization.__table__.delete())
        await db.execute(Wallet.__table__.delete())
        await db.execute(Session.__table__.delete())
        await db.execute(PresentationShare.__table__.delete())
        await db.execute(DocumentUpload.__table__.delete())
        await db.execute(ExtractedCredentialData.__table__.delete())
        await db.execute(ApiKey.__table__.delete())
        await db.execute(WebhookSubscription.__table__.delete())
        await db.execute(WebhookDelivery.__table__.delete())
        await db.execute(User.__table__.delete())
        await db.commit()

        now_utc = datetime.datetime.now(datetime.timezone.utc)

        print("[2/8] Seeding Organization & PKI Signing Keys...")
        org_id = "00000000-0000-0000-0000-000000000001"
        org = Organization(
            id=org_id,
            name="IIT Delhi Digital Trust Institute",
            legal_entity_id="IITD-TRUST-2036",
            domain="iitd.ac.in",
            on_chain_address=addr_0,
            status="AUTHORIZED",
            created_at=now_utc,
            updated_at=now_utc,
        )
        db.add(org)

        # Signing Keys
        key_0 = SigningKey(
            id="00000000-0000-0000-0000-000000000010",
            organization_id=org_id,
            public_key_address=addr_0,
            key_type="secp256k1",
            status="ACTIVE",
            valid_until=int(time.time()) + 86400 * 365,
            created_at=now_utc,
            updated_at=now_utc,
        )
        key_1 = SigningKey(
            id="00000000-0000-0000-0000-000000000011",
            organization_id=org_id,
            public_key_address=addr_1,
            key_type="secp256k1",
            status="ACTIVE",
            valid_until=int(time.time()) + 86400 * 365,
            created_at=now_utc,
            updated_at=now_utc,
        )
        db.add_all([key_0, key_1])

        print("[3/8] Seeding Institutional Officers & Users...")
        user_approver = User(
            id="00000000-0000-0000-0000-000000000020",
            email="approver@iitd.ac.in",
            full_name="Prof. Rajesh K. Verma (Dean of Academic Affairs)",
            role=UserRole.INSTITUTION_ADMIN.value,
            is_active=True,
            created_at=now_utc,
            updated_at=now_utc,
        )
        user_preparer = User(
            id="00000000-0000-0000-0000-000000000021",
            email="preparer@iitd.ac.in",
            full_name="Dr. Sunita Rao (Issuance Officer)",
            role=UserRole.AUTHORIZED_ISSUER.value,
            is_active=True,
            created_at=now_utc,
            updated_at=now_utc,
        )
        user_holder = User(
            id="00000000-0000-0000-0000-000000000022",
            email="rahul.sharma@alumni.iitd.ac.in",
            full_name="Rahul Sharma",
            role=UserRole.HOLDER.value,
            is_active=True,
            created_at=now_utc,
            updated_at=now_utc,
        )
        db.add_all([user_approver, user_preparer, user_holder])

        # Wallets
        wallet_approver = Wallet(
            id="00000000-0000-0000-0000-000000000030",
            user_id=user_approver.id,
            address=addr_0,
            chain_id=31337,
            is_primary=True,
            created_at=now_utc,
            updated_at=now_utc,
        )
        wallet_preparer = Wallet(
            id="00000000-0000-0000-0000-000000000031",
            user_id=user_preparer.id,
            address=addr_1,
            chain_id=31337,
            is_primary=True,
            created_at=now_utc,
            updated_at=now_utc,
        )
        wallet_holder = Wallet(
            id="00000000-0000-0000-0000-000000000032",
            user_id=user_holder.id,
            address=addr_holder,
            chain_id=31337,
            is_primary=True,
            created_at=now_utc,
            updated_at=now_utc,
        )
        db.add_all([wallet_approver, wallet_preparer, wallet_holder])

        # Memberships
        mem_approver = OrganizationMembership(
            id="00000000-0000-0000-0000-000000000040",
            organization_id=org_id,
            user_id=user_approver.id,
            role=UserRole.INSTITUTION_ADMIN.value,
            status="ACTIVE",
            created_at=now_utc,
            updated_at=now_utc,
        )
        mem_preparer = OrganizationMembership(
            id="00000000-0000-0000-0000-000000000041",
            organization_id=org_id,
            user_id=user_preparer.id,
            role=UserRole.AUTHORIZED_ISSUER.value,
            status="ACTIVE",
            created_at=now_utc,
            updated_at=now_utc,
        )
        db.add_all([mem_approver, mem_preparer])

        # Active Session for Development / Seamless Browsing
        raw_session_token = "decentralid-demo-session-token-2036"
        token_hash = hashlib.sha256(raw_session_token.encode("utf-8")).hexdigest()
        session_record = Session(
            id=token_hash,
            user_id=user_approver.id,
            wallet_address=addr_0,
            expires_at=now_utc + datetime.timedelta(days=30),
            is_revoked=False,
            created_at=now_utc,
            updated_at=now_utc,
        )
        db.add(session_record)

        print("[4/8] Cryptographically Signing Verifiable Credentials (ecdsa-jcs-2019)...")

        # Helper to make a signed credential record
        def create_signed_credential(
            cred_uuid: str,
            recipient_address: str,
            schema_type: str,
            claims: dict,
            workflow_status: str,
            lifecycle_status: str,
            tx_hash: str = None,
            reason: str = None,
        ):
            w3c_id = f"urn:uuid:{cred_uuid}"
            credential_id = "0x" + keccak(w3c_id.encode("utf-8")).hex()
            full_subject = {
                "id": f"did:pkh:eip155:31337:{recipient_address}",
                **claims,
            }

            commitment, salt = CommitmentService.generate_subject_commitment(full_subject)
            encrypted_subject = EncryptionService.encrypt_json(full_subject)
            encrypted_salt = EncryptionService.encrypt_data(salt.hex())

            doc_unsigned = {
                "@context": [
                    "https://www.w3.org/ns/credentials/v2",
                    "https://decentralid.org/contexts/v1",
                ],
                "id": w3c_id,
                "type": ["VerifiableCredential", schema_type],
                "issuer": {
                    "id": f"did:pkh:eip155:31337:{addr_0}",
                    "name": "IIT Delhi Digital Trust Institute",
                },
                "validFrom": "2025-06-15T00:00:00Z",
                "credentialSubject": full_subject,
            }

            proof_opts, digest = SigningService.create_proof_payload(
                document_without_proof=doc_unsigned,
                verification_method=f"did:pkh:eip155:31337:{addr_0}#key-1",
                cryptosuite="ecdsa-jcs-2019",
            )
            sig = account_0.sign_message(encode_defunct(primitive=digest))
            sig_hex = f"0x{sig.signature.hex()}" if not sig.signature.hex().startswith("0x") else sig.signature.hex()

            proof_dict = {
                **proof_opts,
                "proofValue": sig_hex,
            }

            doc_signed = {
                **doc_unsigned,
                "proof": proof_dict,
            }

            cred = Credential(
                id=cred_uuid,
                organization_id=org_id,
                w3c_id=w3c_id,
                credential_id=credential_id,
                recipient_address=recipient_address,
                schema_type=schema_type,
                commitment=commitment,
                encrypted_salt=encrypted_salt,
                encrypted_subject=encrypted_subject,
                key_id="master-v1",
                proof_json=json.dumps(proof_dict),
                workflow_status=workflow_status,
                status=lifecycle_status,
                revocation_reason=reason,
                revoked_at=datetime.datetime.now(datetime.timezone.utc) if lifecycle_status == "REVOKED" else None,
                tx_hash=tx_hash,
                prepared_by=user_preparer.id,
                approved_by=user_approver.id,
                issued_at=datetime.datetime.now(datetime.timezone.utc),
                created_at=now_utc,
                updated_at=now_utc,
            )

            return cred, doc_signed

        # 1. Credential 1: Rahul Sharma B.Tech CSE (ACTIVE, ISSUED)
        cred1, doc1_signed = create_signed_credential(
            cred_uuid="00000000-0000-0000-0000-000000000101",
            recipient_address=addr_holder,
            schema_type="UniversityDegreeCredential",
            claims={
                "studentName": "Rahul Sharma",
                "degree": "Bachelor of Technology",
                "major": "Computer Science and Engineering",
                "institutionName": "IIT Delhi Digital Trust Institute",
                "graduationDate": "2025-06-15",
                "gpa": 9.42,
                "honors": "First Class with Distinction",
            },
            workflow_status="ISSUED",
            lifecycle_status="ACTIVE",
            tx_hash="0x9a8f273618de4f7a29c1b4892c5510dfb927ac81640235adcf8291048b261e47",
        )

        # 2. Credential 2: Ananya Patel (SUSPENDED)
        addr_ananya = "0x90F79bf6EB2c4f870365E785982E1f101E93b906".lower()
        cred2, _ = create_signed_credential(
            cred_uuid="00000000-0000-0000-0000-000000000102",
            recipient_address=addr_ananya,
            schema_type="ProfessionalAccreditationCredential",
            claims={
                "recipientName": "Ananya Patel",
                "certification": "Certified Cryptographic Security Auditor",
                "organization": "DecentralID Trust Alliance",
                "licenseId": "CCSA-2026-8819",
                "validUntil": "2027-12-31",
            },
            workflow_status="ISSUED",
            lifecycle_status="SUSPENDED",
            tx_hash="0x3b87cf019a823e115da7c295b41098de72688ca0271598af81907cb5421a97d1",
            reason="Periodic compliance audit in progress; temporary administrative hold.",
        )

        # 3. Credential 3: Vikram Malhotra (REVOKED)
        addr_vikram = "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65".lower()
        cred3, _ = create_signed_credential(
            cred_uuid="00000000-0000-0000-0000-000000000103",
            recipient_address=addr_vikram,
            schema_type="UniversityDegreeCredential",
            claims={
                "studentName": "Vikram Malhotra",
                "degree": "Bachelor of Technology",
                "major": "Mechanical Engineering",
                "institutionName": "IIT Delhi Digital Trust Institute",
                "graduationDate": "2024-05-18",
                "gpa": 6.80,
            },
            workflow_status="ISSUED",
            lifecycle_status="REVOKED",
            tx_hash="0x718a99de42b8901cd65f210378bc2891a084ef817c7295aa1082354890bf2195",
            reason="Academic integrity disciplinary board determination; degree permanently forfeited.",
        )

        # 4. Credential 4: Priya Nair (PENDING_APPROVAL)
        addr_priya = "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc".lower()
        w3c4 = "urn:uuid:00000000-0000-0000-0000-000000000104"
        cid4 = "0x" + keccak(w3c4.encode("utf-8")).hex()
        subj4 = {
            "id": f"did:pkh:eip155:31337:{addr_priya}",
            "studentName": "Priya Nair",
            "degree": "Master of Science",
            "major": "Artificial Intelligence & Distributed Systems",
            "institutionName": "IIT Delhi Digital Trust Institute",
            "graduationDate": "2026-05-20",
            "gpa": 9.85,
        }
        com4, salt4 = CommitmentService.generate_subject_commitment(subj4)
        cred4 = Credential(
            id="00000000-0000-0000-0000-000000000104",
            organization_id=org_id,
            w3c_id=w3c4,
            credential_id=cid4,
            recipient_address=addr_priya,
            schema_type="UniversityDegreeCredential",
            commitment=com4,
            encrypted_salt=EncryptionService.encrypt_data(salt4.hex()),
            encrypted_subject=EncryptionService.encrypt_json(subj4),
            key_id="master-v1",
            workflow_status="PENDING_APPROVAL",
            status="PREPARED",
            prepared_by=user_preparer.id,
            created_at=now_utc,
            updated_at=now_utc,
        )

        # 5. Credential 5: Arjun Mehta (APPROVED - Ready for Signing)
        addr_arjun = "0x976EA74026E726554dB657fA54763abd0C3a0aa9".lower()
        w3c5 = "urn:uuid:00000000-0000-0000-0000-000000000105"
        cid5 = "0x" + keccak(w3c5.encode("utf-8")).hex()
        subj5 = {
            "id": f"did:pkh:eip155:31337:{addr_arjun}",
            "studentName": "Arjun Mehta",
            "degree": "Bachelor of Technology",
            "major": "Mechanical & Systems Engineering",
            "institutionName": "IIT Delhi Digital Trust Institute",
            "graduationDate": "2026-05-20",
            "gpa": 8.90,
        }
        com5, salt5 = CommitmentService.generate_subject_commitment(subj5)
        cred5 = Credential(
            id="00000000-0000-0000-0000-000000000105",
            organization_id=org_id,
            w3c_id=w3c5,
            credential_id=cid5,
            recipient_address=addr_arjun,
            schema_type="UniversityDegreeCredential",
            commitment=com5,
            encrypted_salt=EncryptionService.encrypt_data(salt5.hex()),
            encrypted_subject=EncryptionService.encrypt_json(subj5),
            key_id="master-v1",
            workflow_status="APPROVED",
            status="APPROVED",
            prepared_by=user_preparer.id,
            approved_by=user_approver.id,
            created_at=now_utc,
            updated_at=now_utc,
        )

        db.add_all([cred1, cred2, cred3, cred4, cred5])

        print("[5/8] Seeding Selective Disclosure Presentation Token...")
        share_token = "pr_7f9b23ad81e94022a182746b9a84210e"
        disclosed_claims = {
            "degree": "Bachelor of Technology",
            "major": "Computer Science and Engineering",
            "institutionName": "IIT Delhi Digital Trust Institute",
        }
        full_claims_cred1 = {
            "id": f"did:pkh:eip155:31337:{addr_holder}",
            "studentName": "Rahul Sharma",
            "degree": "Bachelor of Technology",
            "major": "Computer Science and Engineering",
            "institutionName": "IIT Delhi Digital Trust Institute",
            "graduationDate": "2025-06-15",
            "gpa": 9.42,
            "honors": "First Class with Distinction",
        }
        claim_salts, claim_digests, root_commitment = SelectiveDisclosureService.create_blinded_claims(full_claims_cred1)
        disclosure_proof = SelectiveDisclosureService.generate_disclosure_proof(
            full_claims=full_claims_cred1,
            claim_salts=claim_salts,
            disclosed_keys=list(disclosed_claims.keys()),
        )
        masked_claims = [k for k in full_claims_cred1.keys() if k not in disclosed_claims and k != "id"]

        presented_subject = {
            "id": f"did:pkh:eip155:31337:{addr_holder}",
            **disclosed_claims,
        }

        presented_vc = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://decentralid.org/contexts/v1",
            ],
            "id": cred1.w3c_id,
            "type": ["VerifiableCredential", cred1.schema_type],
            "issuer": {
                "id": f"did:pkh:eip155:31337:{addr_0}",
                "name": "IIT Delhi Digital Trust Institute",
            },
            "validFrom": "2025-06-15T00:00:00Z",
            "credentialSubject": presented_subject,
            "credentialStatus": {
                "id": f"/api/v1/credentials/{cred1.credential_id}/status",
                "type": "BitstringStatusListEntry",
                "statusPurpose": "revocation",
            },
            "commitment": cred1.commitment,
            "selectiveDisclosure": {
                "cryptographicMode": "SaltedClaimCommitment",
                "claimsRootCommitment": root_commitment,
                "disclosedFields": list(disclosed_claims.keys()),
                "maskedFields": masked_claims,
                "disclosureProof": disclosure_proof,
            },
            "proof": json.loads(cred1.proof_json),
        }

        presentation_share = PresentationShare(
            id="00000000-0000-0000-0000-000000000201",
            token=share_token,
            holder_address=addr_holder,
            credential_id=cred1.credential_id,
            disclosed_claims=disclosed_claims,
            presentation_document={
                "@context": [
                    "https://www.w3.org/ns/credentials/v2",
                    "https://decentralid.org/contexts/v1",
                ],
                "type": ["VerifiablePresentation"],
                "verifiableCredential": [presented_vc],
            },
            expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7),
            access_count=3,
            max_access=50,
            created_at=now_utc,
            updated_at=now_utc,
        )
        db.add(presentation_share)

        print("[6/8] Seeding Document Intelligence Upload & Anomaly Checks...")
        upload_id = "00000000-0000-0000-0000-000000000301"
        raw_text = """
        INDIAN INSTITUTE OF TECHNOLOGY DELHI
        OFFICIAL DEGREE CERTIFICATE

        This is to certify that Rahul Sharma
        Roll Number: 2021CS10842
        has successfully completed the requirements for the Degree of
        Bachelor of Technology in Computer Science and Engineering
        Conferred on 15th June 2025
        Cumulative Grade Point Average: 9.42 / 10.00
        Classification: First Class with Distinction
        """
        doc_upload = DocumentUpload(
            id=upload_id,
            organization_id=org_id,
            uploaded_by=user_preparer.id,
            filename="IITD_Degree_Rahul_Sharma.pdf",
            mime_type="application/pdf",
            file_size=1048576,
            file_hash="4a7d1ed414474e4033ac29ccb8653d9b4a7d1ed414474e4033ac29ccb8653d9b",
            storage_path="storage/uploads/IITD_Degree_Rahul_Sharma.pdf",
            status="COMPLETED",
            created_at=now_utc,
            updated_at=now_utc,
        )
        db.add(doc_upload)

        extracted_fields = {
            "studentName": {"value": "Rahul Sharma", "confidence": 0.98, "is_valid": True, "human_corrected": False},
            "degree": {"value": "Bachelor of Technology", "confidence": 0.97, "is_valid": True, "human_corrected": False},
            "major": {"value": "Computer Science and Engineering", "confidence": 0.95, "is_valid": True, "human_corrected": False},
            "institutionName": {"value": "IIT Delhi Digital Trust Institute", "confidence": 0.99, "is_valid": True, "human_corrected": False},
            "graduationDate": {"value": "2025-06-15", "confidence": 0.94, "is_valid": True, "human_corrected": False},
            "gpa": {"value": 9.42, "confidence": 0.96, "is_valid": True, "human_corrected": False},
        }

        anomaly_findings = [
            {
                "rule": "SEAL_VERIFICATION",
                "severity": "LOW",
                "description": "Institutional embossing signature matched authoritative IITD vector mark.",
                "evidence": "Pixel density matches official registrar cryptographic template.",
            }
        ]

        extracted_data = ExtractedCredentialData(
            id="00000000-0000-0000-0000-000000000302",
            document_id=upload_id,
            schema_type="UniversityDegreeCredential",
            raw_text=raw_text,
            extracted_fields_json=json.dumps(extracted_fields),
            anomaly_findings_json=json.dumps(anomaly_findings),
            overall_confidence=0.96,
            review_status="APPROVED",
            reviewed_by=user_approver.id,
            reviewed_at=datetime.datetime.now(datetime.timezone.utc),
            credential_id=cred1.id,
            created_at=now_utc,
            updated_at=now_utc,
        )
        db.add(extracted_data)

        print("[7/8] Seeding Developer API Key & Webhook Subscriptions...")
        raw_api_key = "did_live_3f92b77c8e914099a41de92c0182bb19"
        api_key_hash = hashlib.sha256(raw_api_key.encode("utf-8")).hexdigest()
        api_key_record = ApiKey(
            id="00000000-0000-0000-0000-000000000401",
            organization_id=org_id,
            name="Production Verifier Gateway",
            hashed_key=api_key_hash,
            key_prefix="did_live_3f92b7",
            scopes=["verify", "status", "storage"],
            is_active=True,
            created_at=now_utc,
            updated_at=now_utc,
        )
        db.add(api_key_record)

        wh_sub = WebhookSubscription(
            id="00000000-0000-0000-0000-000000000501",
            organization_id=org_id,
            target_url="https://enterprise-verifier.ac.in/api/v1/decentralid-webhook",
            event_types=["credential.issued", "credential.revoked", "credential.suspended"],
            secret_key="whsec_7d9e81b94ac02e1189c4456ff81290bb",
            is_active=True,
            created_at=now_utc,
            updated_at=now_utc,
        )
        db.add(wh_sub)

        wh_del1 = WebhookDelivery(
            id="00000000-0000-0000-0000-000000000601",
            subscription_id=wh_sub.id,
            event_type="credential.issued",
            payload={"event": "credential.issued", "credential_id": cred1.credential_id, "timestamp": int(time.time()) - 3600},
            status="DELIVERED",
            status_code=200,
            attempt_count=1,
            created_at=now_utc,
            delivered_at=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1),
        )
        wh_del2 = WebhookDelivery(
            id="00000000-0000-0000-0000-000000000602",
            subscription_id=wh_sub.id,
            event_type="credential.suspended",
            payload={"event": "credential.suspended", "credential_id": cred2.credential_id, "reason": "Audit hold"},
            status="DELIVERED",
            status_code=200,
            attempt_count=1,
            created_at=now_utc,
            delivered_at=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=30),
        )
        db.add_all([wh_del1, wh_del2])

        await db.commit()
        print("[8/8] Database seed completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
