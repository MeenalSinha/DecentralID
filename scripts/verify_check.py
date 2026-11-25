import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
from backend.app.core.database import AsyncSessionLocal
from backend.app.services.credential.verification_service import VerificationService
from backend.app.services.credential.presentation_service import PresentationService

async def test_v():
    async with AsyncSessionLocal() as db:
        vp = await PresentationService.resolve_presentation(db, "pr_7f9b23ad81e94022a182746b9a84210e")
        print("Resolved VP:", bool(vp))
        res = await VerificationService.verify_credential(vp, db=db)
        print("Is Valid:", res.is_valid)
        print("Checks:", res.to_dict()["checks"])
        print("Errors:", res.errors)
        print("Warnings:", res.warnings)

if __name__ == "__main__":
    asyncio.run(test_v())
