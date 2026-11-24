import io
import json
import pytest
from eth_account import Account
from eth_account.messages import encode_defunct

@pytest.mark.asyncio
async def test_intelligence_document_upload_and_extraction(client):
    # 1. Setup authenticated institutional operator via cookie session
    issuer_acc = Account.create()
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
        "name": "Delhi Technological University",
        "jurisdiction": "IN-DL",
        "on_chain_address": issuer_acc.address,
        "registration_number": "DTU-REG-2026-99"
    })
    assert org_res.status_code == 201
    org_id = org_res.json()["id"]

    # 2. Upload valid credential document content
    doc_text = """
    DELHI TECHNOLOGICAL UNIVERSITY
    OFFICIAL DEGREE CERTIFICATE
    
    This is to certify that Rahul Sharma
    Student ID: DTU/2022/CS/1042
    has successfully completed the Degree of Bachelor of Technology
    in Computer Science and Engineering
    Conferred on: 2025-06-15
    Cumulative Grade: 9.20 / 10.0
    """
    files = {
        "file": ("degree_rahul_sharma.txt", io.BytesIO(doc_text.encode("utf-8")), "text/plain")
    }
    data = {"organization_id": org_id}

    upload_res = await client.post("/api/v1/intelligence/upload", files=files, data=data)
    assert upload_res.status_code == 201
    upload_data = upload_res.json()

    assert upload_data["status"] == "PROCESSED"
    assert upload_data["schema_type"] == "UniversityDegreeCredential"
    assert upload_data["overall_confidence"] > 0.70
    assert "studentName" in upload_data["extracted_fields"]
    assert upload_data["extracted_fields"]["studentName"]["value"] == "Rahul Sharma"
    assert upload_data["extracted_fields"]["degree"]["value"] == "Bachelor Of Technology"
    assert upload_data["review_status"] == "PENDING_REVIEW"
    doc_id = upload_data["document_id"]

    # 3. Duplicate Document Upload check -> Anomaly Detection
    files_dup = {
        "file": ("degree_copy.txt", io.BytesIO(doc_text.encode("utf-8")), "text/plain")
    }
    dup_res = await client.post("/api/v1/intelligence/upload", files=files_dup, data=data)
    assert dup_res.status_code == 201
    dup_data = dup_res.json()
    rule_names = [a["rule"] for a in dup_data["anomaly_findings"]]
    assert "DUPLICATE_DOCUMENT_FINGERPRINT" in rule_names

    # 4. Human Review & Correction
    review_res = await client.post(
        f"/api/v1/intelligence/documents/{doc_id}/review",
        json={
            "review_action": "APPROVE",
            "corrected_fields": {
                "studentName": "Rahul K. Sharma",
                "department": "Computer Science"
            }
        }
    )
    assert review_res.status_code == 200
    rev_data = review_res.json()
    assert rev_data["review_status"] == "APPROVED"
    assert rev_data["extracted_fields"]["studentName"]["value"] == "Rahul K. Sharma"
    assert rev_data["extracted_fields"]["studentName"]["human_corrected"] is True

    # 5. Prepare Credential from Approved Intelligence
    recipient_acc = Account.create()
    prep_res = await client.post(
        f"/api/v1/intelligence/documents/{doc_id}/prepare-credential",
        json={
            "recipient_address": recipient_acc.address,
            "valid_until": "2035-12-31T23:59:59Z"
        }
    )
    assert prep_res.status_code == 201
    prep_data = prep_res.json()
    assert prep_data["status"] == "PREPARED"
    assert prep_data["workflow_status"] == "PREPARED"
    assert "credential_id" in prep_data

    # 6. Verify duplicate preparation rejection
    prep_dup = await client.post(
        f"/api/v1/intelligence/documents/{doc_id}/prepare-credential",
        json={"recipient_address": recipient_acc.address}
    )
    assert prep_dup.status_code == 400

    # 7. Untrusted file rejection (malformed / non-document bytes)
    bad_files = {
        "file": ("binary.bin", io.BytesIO(b"\x00\x01\x02\x03\x04\x05\x06"), "application/octet-stream")
    }
    bad_res = await client.post("/api/v1/intelligence/upload", files=bad_files, data=data)
    assert bad_res.status_code == 422
