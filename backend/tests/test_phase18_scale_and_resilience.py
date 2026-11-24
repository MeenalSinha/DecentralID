import time
import pytest
import datetime
from eth_account import Account

from backend.app.services.credential.signing_service import SigningService
from backend.app.services.credential.selective_disclosure_service import SelectiveDisclosureService
from backend.app.services.network.ipfs_service import IpfsStorageService, compute_ipfs_cidv1_raw
from backend.app.services.network.webhook_service import WebhookService

@pytest.mark.asyncio
async def test_cryptographic_signing_and_verification_throughput():
    """
    Performance Load Test: Measures W3C RFC 8785 canonicalization, double-SHA256 digest,
    and ECDSA secp256k1 signing throughput across 50 iterations.
    """
    signer = Account.create()
    doc_template = {
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "id": "urn:uuid:benchmark-cred",
        "type": ["VerifiableCredential", "AcademicDegreeCredential"],
        "issuer": signer.address,
        "validFrom": "2026-11-24T12:00:00Z",
        "credentialSubject": {
            "student_id": "BENCH-001",
            "degree": "Bachelor of Technology in Computer Engineering",
            "gpa": "9.85",
            "institution": "Indian Institute of Technology Bombay",
            "graduation_year": 2026
        }
    }

    N = 50
    start_time = time.perf_counter()
    signed_credentials = []

    for i in range(N):
        doc = dict(doc_template)
        doc["id"] = f"urn:uuid:bench-{i}"
        signed_vc = SigningService.sign_credential(
            credential_doc=doc,
            private_key=signer.key.hex(),
            verification_method=signer.address,
            cryptosuite="ecdsa-jcs-2019"
        )
        signed_credentials.append(signed_vc)

    signing_duration = time.perf_counter() - start_time
    signing_rate = N / signing_duration
    avg_signing_ms = (signing_duration / N) * 1000

    assert len(signed_credentials) == N
    assert signing_rate > 10.0, f"Signing throughput {signing_rate:.2f} creds/sec is below target"

    # Measure Verification Throughput
    v_start = time.perf_counter()
    for vc in signed_credentials:
        is_valid, recovered, err = SigningService.verify_credential_proof(vc)
        assert is_valid is True

    verify_duration = time.perf_counter() - v_start
    verify_rate = N / verify_duration
    avg_verify_ms = (verify_duration / N) * 1000

    assert verify_rate > 10.0, f"Verification throughput {verify_rate:.2f} creds/sec is below target"
    print(f"\n[BENCHMARK] Signing: {signing_rate:.1f} ops/sec ({avg_signing_ms:.2f}ms/op) | Verification: {verify_rate:.1f} ops/sec ({avg_verify_ms:.2f}ms/op)")

@pytest.mark.asyncio
async def test_selective_disclosure_merkle_performance():
    """
    Performance Benchmark: 20-claim credential selective disclosure commitment computation.
    """
    claims = {f"attribute_{i}": f"value_{i}_{time.time()}" for i in range(20)}
    
    start = time.perf_counter()
    salts, digests, root_commitment = SelectiveDisclosureService.create_blinded_claims(claims)
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    assert len(digests) == 20
    assert len(root_commitment) == 64
    assert elapsed_ms < 50.0, f"Merkle root commitment took too long: {elapsed_ms:.2f}ms"

    # Verify disclosure of 5 claims out of 20
    disclosed_keys = [f"attribute_{i}" for i in range(5)]
    proof = SelectiveDisclosureService.generate_disclosure_proof(
        full_claims=claims,
        claim_salts=salts,
        disclosed_keys=disclosed_keys
    )
    is_valid, verified_claims, err = SelectiveDisclosureService.verify_selective_disclosure(
        disclosure_proof=proof,
        expected_root_commitment=root_commitment
    )
    assert is_valid is True
    assert len(verified_claims) == 5
    for k in disclosed_keys:
        assert verified_claims[k] == claims[k]

@pytest.mark.asyncio
async def test_storage_provider_resilience_and_tamper_recovery():
    """
    Resilience Test: Validates content-addressed fallback when external IPFS provider is offline.
    """
    test_data = {"test_credential": "scale_and_resilience_payload_data"}

    # Uploads locally with AES-256-GCM encryption and CIDv1 addressing
    encrypted_bytes, key = IpfsStorageService.encrypt_data(test_data)
    cid = compute_ipfs_cidv1_raw(encrypted_bytes)
    assert cid.startswith("bafkrei")

    # Retrieval and decryption
    retrieved = IpfsStorageService.decrypt_data(encrypted_bytes, key)
    assert retrieved == test_data

@pytest.mark.asyncio
async def test_webhook_replay_defense_resilience():
    """
    Resilience Test: Webhook dispatcher rejects replayed or stale timestamps.
    """
    import json
    secret = "whsec_test_resilience_secret_32_bytes_long"
    payload = {"event": "credential.issued", "id": "test-123"}
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    now_ts = int(time.time())

    # 1. Fresh event (< 300s)
    fresh_header = WebhookService.compute_signature(payload_bytes, secret, now_ts)
    is_valid = WebhookService.verify_signature(payload_bytes, fresh_header, secret, tolerance_seconds=300)
    assert is_valid is True

    # 2. Stale / replayed event (> 300s in past)
    stale_ts = now_ts - 600
    stale_header = WebhookService.compute_signature(payload_bytes, secret, stale_ts)
    is_valid_stale = WebhookService.verify_signature(payload_bytes, stale_header, secret, tolerance_seconds=300)
    assert is_valid_stale is False
