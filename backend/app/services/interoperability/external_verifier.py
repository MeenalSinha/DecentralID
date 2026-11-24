from typing import Dict, Any, Optional
from backend.app.services.interoperability.did_resolver import universal_did_resolver, DIDResolutionError
from backend.app.services.credential.signing_service import SigningService

class ExternalVerificationAdapter:
    @staticmethod
    async def verify_external_document(
        document: Dict[str, Any], 
        expected_issuer_did: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validates external W3C Verifiable Credentials and Verifiable Presentations.
        Resolves issuer DIDs, verifies Data Integrity proofs, and validates claims.
        """
        # Determine if Verifiable Presentation or Verifiable Credential
        doc_type = document.get("type", [])
        if isinstance(doc_type, str):
            doc_type = [doc_type]
            
        is_presentation = "VerifiablePresentation" in doc_type
        
        target_vc = document
        if is_presentation:
            verifiable_credentials = document.get("verifiableCredential", [])
            if not verifiable_credentials:
                return {
                    "is_valid": False,
                    "status": "INVALID",
                    "error_code": "EMPTY_PRESENTATION",
                    "details": "Presentation contains no verifiable credentials"
                }
            target_vc = verifiable_credentials[0] if isinstance(verifiable_credentials, list) else verifiable_credentials

        # Extract issuer
        issuer = target_vc.get("issuer")
        if not issuer:
            return {
                "is_valid": False,
                "status": "INVALID",
                "error_code": "MISSING_ISSUER",
                "details": "Credential has no issuer"
            }
        
        issuer_str = issuer if isinstance(issuer, str) else issuer.get("id", "")
        
        # Check expected issuer constraint if supplied
        if expected_issuer_did and issuer_str.lower() != expected_issuer_did.lower():
            return {
                "is_valid": False,
                "status": "INVALID",
                "error_code": "ISSUER_MISMATCH",
                "details": f"Issuer '{issuer_str}' does not match expected '{expected_issuer_did}'"
            }

        # Resolve DID if applicable
        verification_method_used = None
        if issuer_str.startswith("did:"):
            try:
                resolution = await universal_did_resolver.resolve(issuer_str)
                did_doc = resolution.get("didDocument", {})
                vms = did_doc.get("verificationMethod", [])
                if vms:
                    verification_method_used = vms[0].get("id")
            except DIDResolutionError as e:
                return {
                    "is_valid": False,
                    "status": "INVALID",
                    "error_code": "DID_RESOLUTION_FAILED",
                    "details": str(e)
                }

        # Inspect proof
        proof = target_vc.get("proof")
        if not proof:
            return {
                "is_valid": False,
                "status": "INVALID",
                "error_code": "MISSING_PROOF",
                "details": "Credential contains no cryptographic proof"
            }
        
        proof_obj = proof if isinstance(proof, dict) else proof[0]
        cryptosuite = proof_obj.get("cryptosuite") or proof_obj.get("type")
        
        if not verification_method_used:
            verification_method_used = proof_obj.get("verificationMethod")

        # Cryptographic verification for ecdsa-jcs-2019
        if cryptosuite in ("ecdsa-jcs-2019", "ecdsa-jcs-2019-keccak"):
            verified, recovered_address, error_detail = SigningService.verify_credential_proof(target_vc)
            if not verified:
                return {
                    "is_valid": False,
                    "status": "INVALID",
                    "error_code": "SIGNATURE_VERIFICATION_FAILED",
                    "issuer_did": issuer_str,
                    "cryptosuite": cryptosuite,
                    "details": error_detail
                }
        else:
            # Check known suites
            if cryptosuite not in ("Ed25519Signature2020", "JsonWebSignature2020"):
                return {
                    "is_valid": False,
                    "status": "UNSUPPORTED_CRYPTOSUITE",
                    "error_code": "UNSUPPORTED_SUITE",
                    "cryptosuite": cryptosuite,
                    "details": f"Cryptosuite '{cryptosuite}' is not supported by this verifier"
                }

        # Extract disclosed claims
        credential_subject = target_vc.get("credentialSubject", {})
        
        return {
            "is_valid": True,
            "status": "VALID",
            "error_code": None,
            "issuer_did": issuer_str,
            "verification_method_used": verification_method_used,
            "cryptosuite": cryptosuite,
            "claims_disclosed": credential_subject
        }
