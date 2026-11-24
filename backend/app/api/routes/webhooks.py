from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.core.constants import UserRole
from backend.app.models.user import User
from backend.app.models.network import WebhookSubscription, WebhookDelivery
from backend.app.schemas.network import (
    WebhookSubscriptionCreateRequest,
    WebhookSubscriptionResponse,
    WebhookDeliveryResponse,
)
from backend.app.api.dependencies.auth import get_current_user
from backend.app.services.authorization_service import AuthorizationService
from backend.app.services.network.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["DecentralID Webhooks"])


@router.post("/subscriptions", response_model=WebhookSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook_subscription(
    payload: WebhookSubscriptionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_memberships = await AuthorizationService.get_user_organizations(db, current_user.id)
    if not user_memberships:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="USER_NOT_AFFILIATED_WITH_ORGANIZATION")

    org_id = user_memberships[0]["organization_id"]
    is_admin = await AuthorizationService.has_organization_role(
        db, current_user.id, org_id, [UserRole.INSTITUTION_ADMIN.value, "ADMIN"]
    )
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS_FOR_WEBHOOKS")

    sub = await WebhookService.create_subscription(
        db=db,
        organization_id=org_id,
        target_url=payload.target_url,
        event_types=payload.event_types
    )
    return sub


@router.get("/subscriptions", response_model=List[WebhookSubscriptionResponse], status_code=status.HTTP_200_OK)
async def list_webhook_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_memberships = await AuthorizationService.get_user_organizations(db, current_user.id)
    if not user_memberships:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="USER_NOT_AFFILIATED_WITH_ORGANIZATION")

    org_id = user_memberships[0]["organization_id"]
    stmt = select(WebhookSubscription).where(
        WebhookSubscription.organization_id == org_id,
        WebhookSubscription.is_active == True
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.delete("/subscriptions/{id}", status_code=status.HTTP_200_OK)
async def delete_webhook_subscription(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_memberships = await AuthorizationService.get_user_organizations(db, current_user.id)
    if not user_memberships:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="USER_NOT_AFFILIATED_WITH_ORGANIZATION")

    org_id = user_memberships[0]["organization_id"]
    stmt = select(WebhookSubscription).where(
        WebhookSubscription.id == id,
        WebhookSubscription.organization_id == org_id
    )
    res = await db.execute(stmt)
    sub = res.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WEBHOOK_SUBSCRIPTION_NOT_FOUND")

    sub.is_active = False
    await db.commit()
    return {"message": "WEBHOOK_SUBSCRIPTION_DEACTIVATED", "id": str(id)}


@router.get("/subscriptions/{id}/deliveries", response_model=List[WebhookDeliveryResponse], status_code=status.HTTP_200_OK)
async def list_webhook_deliveries(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_memberships = await AuthorizationService.get_user_organizations(db, current_user.id)
    if not user_memberships:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="USER_NOT_AFFILIATED_WITH_ORGANIZATION")

    org_id = user_memberships[0]["organization_id"]
    # Verify sub belongs to caller org
    stmt = select(WebhookSubscription).where(
        WebhookSubscription.id == id,
        WebhookSubscription.organization_id == org_id
    )
    res = await db.execute(stmt)
    sub = res.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WEBHOOK_SUBSCRIPTION_NOT_FOUND")

    deliv_stmt = select(WebhookDelivery).where(
        WebhookDelivery.subscription_id == id
    ).order_by(WebhookDelivery.created_at.desc()).limit(50)
    deliv_res = await db.execute(deliv_stmt)
    return deliv_res.scalars().all()


@router.post("/subscriptions/{id}/test", status_code=status.HTTP_200_OK)
async def trigger_test_webhook(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_memberships = await AuthorizationService.get_user_organizations(db, current_user.id)
    if not user_memberships:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="USER_NOT_AFFILIATED_WITH_ORGANIZATION")

    org_id = user_memberships[0]["organization_id"]
    stmt = select(WebhookSubscription).where(
        WebhookSubscription.id == id,
        WebhookSubscription.organization_id == org_id
    )
    res = await db.execute(stmt)
    sub = res.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WEBHOOK_SUBSCRIPTION_NOT_FOUND")

    test_payload = {
        "event": "test.ping",
        "organization_id": str(org_id),
        "message": "DecentralID test webhook delivery"
    }
    deliveries = await WebhookService.dispatch_event(
        db=db,
        organization_id=org_id,
        event_type="test.ping",
        payload=test_payload
    )

    return {
        "dispatched": len(deliveries),
        "deliveries": [
            {
                "id": str(d.id),
                "status": d.status,
                "status_code": d.status_code,
                "attempt_count": d.attempt_count
            }
            for d in deliveries
        ]
    }
