"""
Slack API Adapter
==================

Send messages and interact with Slack channels via the Web API.
Requires SLACK_API_KEY (Bot Token).
"""

import logging

from .base import APIAdapter, register_adapter

logger = logging.getLogger(__name__)


class SlackAdapter(APIAdapter):
    """Slack Web API adapter."""

    async def execute(self, action: str, payload: dict) -> dict:
        """Execute a Slack API action.

        Supported actions:
            - send_message: Post a message to a channel
            - list_channels: List public channels
        """
        import httpx

        if not self.validate_key():
            return {"output": "Error: Slack API key not configured", "error": True}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            if action == "send_message":
                channel = payload.get("channel", "")
                text = payload.get("text", "")
                if not channel or not text:
                    return {"output": "Error: channel and text are required", "error": True}

                resp = await client.post(
                    "https://slack.com/api/chat.postMessage",
                    headers=headers,
                    json={"channel": channel, "text": text},
                )
                data = resp.json()
                if data.get("ok"):
                    return {"output": f"Message sent to {channel}", "ts": data.get("ts")}
                return {"output": f"Slack error: {data.get('error', 'unknown')}", "error": True}

            elif action == "list_channels":
                resp = await client.get(
                    "https://slack.com/api/conversations.list",
                    headers=headers,
                    params={"types": "public_channel", "limit": payload.get("limit", 100)},
                )
                data = resp.json()
                if data.get("ok"):
                    channels = [{"id": c["id"], "name": c["name"]} for c in data.get("channels", [])]
                    return {"output": f"Found {len(channels)} channels", "channels": channels}
                return {"output": f"Slack error: {data.get('error', 'unknown')}", "error": True}

            else:
                return {"output": f"Unknown Slack action: {action}", "error": True}


register_adapter("slack", SlackAdapter)
