import datetime
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.schemas.health import HealthStatus, ReadinessStatus
from backend.app.core.logging import logger

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])

@router.get("/live", response_model=HealthStatus, status_code=status.HTTP_200_OK)
async def liveness_probe() -> HealthStatus:
    return HealthStatus(
        status="ok",
        environment=settings.ENVIRONMENT,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        version="1.0.0",
    )

@router.get("/ready", response_model=ReadinessStatus, status_code=status.HTTP_200_OK)
async def readiness_probe(db: AsyncSession = Depends(get_db)) -> ReadinessStatus:
    # 1. Probe database
    db_status = {"status": "healthy"}
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Readiness probe: Database check failed: {e}")
        db_status = {"status": "unhealthy", "error": str(e)}

    # 2. Blockchain configuration readiness
    blockchain_status = {
        "network": settings.NETWORK_NAME,
        "chain_id": settings.CHAIN_ID,
        "contracts_configured": bool(
            settings.ISSUER_REGISTRY_ADDRESS
            and settings.CREDENTIAL_REGISTRY_ADDRESS
            and settings.CREDENTIAL_STATUS_REGISTRY_ADDRESS
        ),
    }

    # 3. Storage readiness
    storage_status = {"status": "healthy"}
    try:
        import os
        test_path = os.path.join(settings.STORAGE_DIR, ".health_check")
        os.makedirs(settings.STORAGE_DIR, exist_ok=True)
        with open(test_path, "w") as f:
            f.write("ok")
        if os.path.exists(test_path):
            os.remove(test_path)
    except Exception as e:
        logger.error(f"Readiness probe: Storage check failed: {e}")
        storage_status = {"status": "unhealthy", "error": str(e)}

    is_ready = db_status["status"] == "healthy" and storage_status["status"] == "healthy"
    return ReadinessStatus(
        status="ready" if is_ready else "not_ready",
        environment=settings.ENVIRONMENT,
        database=db_status,
        blockchain=blockchain_status,
        storage=storage_status,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )
