from typing import Dict, Any, Tuple

class EnterpriseSSOService:
    """
    Enterprise SSO & Identity Provider Integration Service (OIDC / SAML).
    Enforces the fundamental architectural separation:
    SSO authenticates institutional personnel, but cryptographic signing strictly
    requires the holder/officer's client-side cryptographic key.
    """
    @staticmethod
    def map_idp_claims_to_membership(
        token_claims: Dict[str, Any],
        organization_domain: str
    ) -> Tuple[bool, Dict[str, Any]]:
        email = token_claims.get("email", "")
        if not email or "@" not in email:
            return False, {"error": "INVALID_EMAIL", "reason": "IdP claims missing valid email"}

        email_domain = email.split("@")[1].lower()
        if email_domain != organization_domain.lower():
            return False, {
                "error": "DOMAIN_MISMATCH",
                "reason": f"Email domain '{email_domain}' does not match organization domain '{organization_domain}'"
            }

        # Role mapping from IdP groups
        groups = token_claims.get("groups", []) or token_claims.get("roles", [])
        assigned_role = "HOLDER"
        if "AcademicRegistrar" in groups or "Dean" in groups:
            assigned_role = "ISSUER_ADMIN"
        elif "Faculty" in groups or "Officer" in groups:
            assigned_role = "ISSUER_OFFICER"

        return True, {
            "email": email,
            "full_name": token_claims.get("name") or token_claims.get("preferred_username", email),
            "assigned_role": assigned_role,
            "idp_subject": token_claims.get("sub"),
            "signing_capability": "CLIENT_KEY_REQUIRED" # Cryptographic signing cannot be delegated to SSO
        }
