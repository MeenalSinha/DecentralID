import json
import time
import hmac
import hashlib
import secrets
import urllib.request
import urllib.error
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.network import WebhookSubscription, WebhookDelivery


class WebhookService:
    @staticmethod
    def compute_signature(payload_bytes: bytes, secret_key: str, timestamp: int) -> str:
        """
        Generates HMAC-SHA256 signature header:
        X-DecentralID-Signature: t={timestamp},v1={hmac_hex}
        Signed message: f"{timestamp}.".encode() + payload_bytes
        """
        signed_payload = f"{timestamp}.".encode("utf-8") + payload_bytes
        mac = hmac.new(secret_key.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
        return f"t={timestamp},v1={mac}"

    @staticmethod
    def verify_signature(payload_bytes: bytes, signature_header: str, secret_key: str, tolerance_seconds: int = 300) -> bool:
        """
        Validates incoming X-DecentralID-Signature against secret key with replay tolerance.
        """
        try:
            parts = dict(item.split("=", 1) for item in signature_header.split(","))
            timestamp_str = parts.get("t")
            v1_signature = parts.get("v1")
            if not timestamp_str or not v1_signature:
                return False

            timestamp = int(timestamp_str)
            now = int(time.time())
            if abs(now - timestamp) > tolerance_seconds:
                return False

            signed_payload = f"{timestamp}.".encode("utf-8") + payload_bytes
            expected_mac = hmac.new(secret_key.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected_mac, v1_signature)
        except Exception:
            return False

    @classmethod
    async def create_subscription(
        cls,
        db: AsyncSession,
        organization_id: UUID,
        target_url: str,
        event_types: Optional[List[str]] = None
    ) -> WebhookSubscription:
        if event_types is None:
            event_types = ["credential.issued", "credential.revoked", "credential.suspended"]

        secret_key = secrets.token_hex(32)
        sub = WebhookSubscription(
            organization_id=str(organization_id),
            target_url=target_url,
            secret_key=secret_key,
            event_types=event_types,
            is_active=True
        )
        db.add(sub)
        await db.commit()
        await db.refresh(sub)
        return sub

    @classmethod
    async def dispatch_event(
        cls,
        db: AsyncSession,
        organization_id: UUID,
        event_type: str,
        payload: dict
    ) -> List[WebhookDelivery]:
        """
        Dispatches an event payload to all active subscribers for the given organization and event type.
        """
        stmt = select(WebhookSubscription).where(
            WebhookSubscription.organization_id == organization_id,
            WebhookSubscription.is_active == True
        )
        res = await db.execute(stmt)
        subscriptions = res.scalars().all()

        deliveries = []
        payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

        for sub in subscriptions:
            if event_type not in (sub.event_types or []):
                continue

            delivery = WebhookDelivery(
                subscription_id=sub.id,
                event_type=event_type,
                payload=payload,
                status="PENDING",
                attempt_count=1
            )
            db.add(delivery)
            await db.commit()
            await db.refresh(delivery)

            timestamp = int(time.time())
            sig_header = cls.compute_signature(payload_bytes, sub.secret_key, timestamp)

            req = urllib.request.Request(
                sub.target_url,
                data=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "DecentralID-Webhook-Dispatcher/1.0",
                    "X-DecentralID-Event": event_type,
                    "X-DecentralID-Signature": sig_header,
                },
                method="POST"
            )

            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    delivery.status = "DELIVERED"
                    delivery.status_code = response.getcode()
                    delivery.delivered_at = datetime.now(timezone.utc)
                    delivery.response_body = response.read(1024).decode("utf-8", errors="replace")
            except urllib.error.HTTPError as e:
                delivery.status = "FAILED"
                delivery.status_code = e.code
                delivery.response_body = e.read(1024).decode("utf-8", errors="replace")
            except Exception as e:
                delivery.status = "FAILED"
                delivery.status_code = 0
                delivery.response_body = str(e)[:1000]

            await db.commit()
            deliveries.append(delivery)

        return deliveries
