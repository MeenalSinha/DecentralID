import datetime
from fastapi import Request
from fastapi.responses import JSONResponse
from backend.app.core.exceptions import DecentralIDException
from backend.app.core.logging import logger

async def decentralid_exception_handler(request: Request, exc: DecentralIDException) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.warning(
        f"API Exception: {exc.code} - {exc.message}",
        extra={
            "correlation_id": correlation_id,
            "status_code": exc.status_code,
            "code": exc.code,
            "details": exc.details
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "correlation_id": correlation_id,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "details": exc.details,
            }
        },
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.error(
        f"Unhandled Server Error: {str(exc)}",
        exc_info=True,
        extra={"correlation_id": correlation_id}
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred.",
                "correlation_id": correlation_id,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
        },
    )
