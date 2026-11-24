from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class DecentralIDException(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details or {}

class AuthenticationFailedException(DecentralIDException):
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTHENTICATION_FAILED",
            message=message,
            details=details,
        )

class InvalidSignatureException(DecentralIDException):
    def __init__(self, message: str = "Invalid cryptographic signature"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="INVALID_SIGNATURE",
            message=message,
        )

class NonceExpiredOrInvalidException(DecentralIDException):
    def __init__(self, message: str = "Authentication challenge nonce is expired or invalid"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="NONCE_EXPIRED_OR_INVALID",
            message=message,
        )

class TenantAccessDeniedException(DecentralIDException):
    def __init__(self, message: str = "Access denied: insufficient tenant permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="TENANT_ACCESS_DENIED",
            message=message,
        )

class ResourceNotFoundException(DecentralIDException):
    def __init__(self, resource_or_message: str, identifier: Optional[str] = None):
        if identifier is not None:
            msg = f"{resource_or_message} with identifier '{identifier}' was not found"
            details = {"resource": resource_or_message, "identifier": identifier}
        else:
            msg = resource_or_message
            details = {}
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=msg,
            details=details,
        )

class DuplicateResourceException(DecentralIDException):
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="DUPLICATE_RESOURCE",
            message=f"{resource} with identifier '{identifier}' already exists",
            details={"resource": resource, "identifier": identifier},
        )

class ValidationException(DecentralIDException):
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="VALIDATION_ERROR",
            message=message,
            details=details,
        )

class InvalidStatusTransitionException(DecentralIDException):
    def __init__(self, message: str = "Invalid status transition"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_STATUS_TRANSITION",
            message=message,
        )
