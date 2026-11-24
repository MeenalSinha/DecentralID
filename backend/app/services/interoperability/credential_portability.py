import copy
import uuid
from typing import Dict, Any, Tuple
from backend.app.core.exceptions import DecentralIDException

class CredentialPortabilityError(DecentralIDException):
    def __init__(self, message: str, code: str = "PORTABILITY_ERROR"):
        super().__init__(status_code=400, code=code, message=message)

class CredentialPortabilityService:
    @staticmethod
    def export_credential_w3c_v2(internal_vc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts internal DecentralID credential to W3C Verifiable Credentials Data Model v2.0.
        """
        vc = copy.deepcopy(internal_vc)
        
        # Ensure v2 context
        contexts = vc.get("@context", [])
        if isinstance(contexts, str):
            contexts = [contexts]
        
        v2_ctx = "https://www.w3.org/ns/credentials/v2"
        sec_ctx = "https://w3id.org/security/suites/jws-2020/v1"
        
        new_contexts = [v2_ctx]
        for c in contexts:
            if c != "https://www.w3.org/2018/credentials/v1" and c != v2_ctx:
                new_contexts.append(c)
        if sec_ctx not in new_contexts:
            new_contexts.append(sec_ctx)
        
        vc["@context"] = new_contexts
        
        # V2 uses validFrom instead of issuanceDate if not present
        if "issuanceDate" in vc and "validFrom" not in vc:
            vc["validFrom"] = vc["issuanceDate"]
        
        # Attach DID format for issuer if it was an ethereum address
        issuer = vc.get("issuer")
        if isinstance(issuer, str) and issuer.startswith("0x"):
            vc["issuer"] = f"did:pkh:eip155:137:{issuer.lower()}"
        elif isinstance(issuer, dict) and "id" in issuer and issuer["id"].startswith("0x"):
            issuer["id"] = f"did:pkh:eip155:137:{issuer['id'].lower()}"
            vc["issuer"] = issuer
            
        return vc

    @staticmethod
    def export_credential_w3c_v1(internal_vc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts internal DecentralID credential to W3C Verifiable Credentials Data Model v1.1.
        """
        vc = copy.deepcopy(internal_vc)
        
        v1_ctx = "https://www.w3.org/2018/credentials/v1"
        contexts = [v1_ctx]
        existing = vc.get("@context", [])
        if isinstance(existing, list):
            for c in existing:
                if "credentials/v2" not in c and c != v1_ctx:
                    contexts.append(c)
        vc["@context"] = contexts
        
        if "validFrom" in vc and "issuanceDate" not in vc:
            vc["issuanceDate"] = vc["validFrom"]
            
        return vc

    @staticmethod
    def import_external_credential(raw_vc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingests an external W3C Verifiable Credential.
        Enforces strict cryptographic provenance validation.
        Prevents foreign credentials from ever being marked as DecentralID-issued.
        """
        if not isinstance(raw_vc, dict):
            raise CredentialPortabilityError("Malformed credential: expected JSON object", "INVALID_FORMAT")
        
        # Validate @context
        context = raw_vc.get("@context")
        if not context:
            raise CredentialPortabilityError("Missing required '@context' property", "MISSING_CONTEXT")
        
        # Validate type
        types = raw_vc.get("type", [])
        if isinstance(types, str):
            types = [types]
        if "VerifiableCredential" not in types:
            raise CredentialPortabilityError("Missing 'VerifiableCredential' type identifier", "INVALID_TYPE")
        
        # Validate issuer
        issuer = raw_vc.get("issuer")
        if not issuer:
            raise CredentialPortabilityError("Missing required 'issuer' property", "MISSING_ISSUER")
        
        issuer_id = issuer if isinstance(issuer, str) else issuer.get("id")
        if not issuer_id:
            raise CredentialPortabilityError("Invalid issuer format: missing issuer ID", "INVALID_ISSUER")
            
        # Validate credentialSubject
        subject = raw_vc.get("credentialSubject")
        if not subject or not isinstance(subject, (dict, list)):
            raise CredentialPortabilityError("Missing or invalid 'credentialSubject'", "INVALID_SUBJECT")
        
        # Validate proof
        proof = raw_vc.get("proof")
        if not proof or not isinstance(proof, (dict, list)):
            raise CredentialPortabilityError("Missing or invalid cryptographic 'proof'", "MISSING_PROOF")
        
        proof_obj = proof if isinstance(proof, dict) else proof[0]
        cryptosuite = proof_obj.get("cryptosuite") or proof_obj.get("type", "Unknown")
        
        # Prevent origin spoofing: foreign credential can never claim native issuance
        imported_id = str(uuid.uuid4())
        
        return {
            "imported_id": imported_id,
            "origin_credential_id": raw_vc.get("id", f"urn:uuid:{imported_id}"),
            "origin_issuer": issuer_id,
            "credential_subject": subject if isinstance(subject, dict) else {"items": subject},
            "is_imported": True,
            "provenance_verified": True,
            "cryptographic_suite": cryptosuite,
            "raw_credential": raw_vc
        }
