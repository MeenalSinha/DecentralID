from enum import Enum

class UserRole(str, Enum):
    PLATFORM_SUPER_ADMIN = "PLATFORM_SUPER_ADMIN"
    INSTITUTION_ADMIN = "INSTITUTION_ADMIN"
    AUTHORIZED_ISSUER = "AUTHORIZED_ISSUER"
    HOLDER = "HOLDER"
    VERIFIER = "VERIFIER"
    AUDITOR = "AUDITOR"

class OrganizationStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    VERIFIED = "VERIFIED"
    AUTHORIZED = "AUTHORIZED"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"

class MembershipStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INVITED = "INVITED"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"

class CredentialLifecycleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"

class SigningKeyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ROTATED = "ROTATED"
    REVOKED = "REVOKED"
