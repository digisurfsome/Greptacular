"""Webhook adapter — POST step output to any webhook URL."""

from __future__ import annotations

import logging

from .base import APIAdapter, register_adapter

logger = logging.getLogger(__name__)


class WebhookAdapter(APIAdapter):
    """Generic webhook adapter. POSTs payload as JSON to a configured URL.

    Works with Zapier, Make.com, n8n, or any HTTP endpoint.
    """

    def __init__(self, webhook_url: str = "", api_key: str = "", **kwargs: object) -> None:
        super().__init__(api_key=api_key)
        self.webhook_url = webhook_url or kwargs.get("variables", {}).get("WEBHOOK_URL", "")  # type: ignore[arg-type]

    async def execute(self, action: str, payload: dict) -> dict:
        if not self.webhook_url:
            return {"output": str(payload.get("content", "")), "error": "No webhook_url configured"}

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    status = resp.status
                    body = await resp.text()
                    if status >= 400:
                        return {
                            "output": str(payload.get("content", "")),
                            "error": f"Webhook returned HTTP {status}: {body[:200]}",
                            "http_status": status,
                        }
                    return {
                        "output": str(payload.get("content", "")),
                        "webhook_status": status,
                        "webhook_response": body[:500],
                        "note": f"Webhook delivered to {self.webhook_url}",
                    }
        except Exception as exc:
            logger.warning("Webhook delivery failed: %s", exc)
            return {
                "output": str(payload.get("content", "")),
                "error": f"Webhook delivery failed: {exc}",
            }


register_adapter("webhook", WebhookAdapter)
register_adapter("zapier", WebhookAdapter)
