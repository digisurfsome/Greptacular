"""
Notification Sender Node — Email, Desktop, and Webhook Notifications
=====================================================================

Three channels:
  - email: SMTP-based email delivery
  - desktop: OS-native notifications (Windows toast / plyer)
  - webhook: HTTP POST to arbitrary URLs
"""

import logging
import time

from . import register_node
from .base_node import BaseExecutionNode, ExecutionResult

logger = logging.getLogger(__name__)


class NotificationSenderNode(BaseExecutionNode):
    """Dispatch notifications via email, desktop, or webhook."""

    async def validate(self, task: dict) -> tuple[bool, str]:
        channel = task.get("channel", "")
        if not channel:
            return False, "Missing required field: channel ('email', 'desktop', 'webhook')"
        if channel not in ("email", "desktop", "webhook"):
            return False, f"Invalid channel: {channel}. Must be 'email', 'desktop', or 'webhook'"

        if channel == "email":
            if not task.get("to"):
                return False, "Email requires 'to' field"
            if not task.get("subject"):
                return False, "Email requires 'subject' field"
            if not task.get("body"):
                return False, "Email requires 'body' field"

        elif channel == "desktop":
            if not task.get("title"):
                return False, "Desktop notification requires 'title' field"
            if not task.get("body"):
                return False, "Desktop notification requires 'body' field"

        elif channel == "webhook":
            if not task.get("url"):
                return False, "Webhook requires 'url' field"

        return True, ""

    async def execute(self, task: dict) -> ExecutionResult:
        channel = task.get("channel", "")
        start = time.time()

        try:
            if channel == "email":
                return await self._send_email(task, start)
            elif channel == "desktop":
                return await self._send_desktop(task, start)
            elif channel == "webhook":
                return await self._send_webhook(task, start)
            else:
                return self._failure(
                    f"Unknown notification channel: {channel}",
                    node_type="notification_sender",
                    channel=channel,
                )
        except Exception as e:
            return self._failure(
                f"Notification failed ({channel}): {e}",
                node_type="notification_sender",
                channel=channel,
            )

    async def _send_email(self, task: dict, start: float) -> ExecutionResult:
        """Send email via SMTP."""
        import smtplib
        from email.mime.text import MIMEText

        to_addr = task["to"]
        subject = task["subject"]
        body = task["body"]
        smtp_host = task.get("smtp_host", "localhost")
        smtp_port = task.get("smtp_port", 587)
        smtp_user = task.get("smtp_user", "")
        smtp_pass = task.get("smtp_pass", "")
        from_addr = task.get("from", smtp_user or "autoforge@localhost")

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr

        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                if smtp_port == 587:
                    server.starttls()
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)

            return ExecutionResult(
                status="success",
                data={"to": to_addr, "subject": subject},
                metadata={"node_type": "notification_sender", "channel": "email"},
                duration=time.time() - start,
            )
        except Exception as e:
            return self._failure(
                f"Email send failed: {e}",
                node_type="notification_sender",
                channel="email",
                to=to_addr,
            )

    async def _send_desktop(self, task: dict, start: float) -> ExecutionResult:
        """Send OS-native desktop notification."""
        title = task["title"]
        body = task["body"]

        try:
            # Try plyer first (cross-platform)
            from plyer import notification as plyer_notification
            plyer_notification.notify(
                title=title,
                message=body[:256],
                timeout=10,
            )
            return ExecutionResult(
                status="success",
                data={"title": title},
                metadata={"node_type": "notification_sender", "channel": "desktop", "library": "plyer"},
                duration=time.time() - start,
            )
        except ImportError:
            pass

        # Fallback: just log the notification
        logger.info("Desktop notification (no library): %s — %s", title, body[:100])
        return ExecutionResult(
            status="partial",
            data={"title": title, "note": "No desktop notification library installed (plyer)"},
            metadata={"node_type": "notification_sender", "channel": "desktop"},
            error="Desktop notification library not available — notification logged only",
            duration=time.time() - start,
        )

    async def _send_webhook(self, task: dict, start: float) -> ExecutionResult:
        """Send HTTP POST to a webhook URL."""
        import httpx

        url = task["url"]
        payload = task.get("payload", {})
        headers = task.get("headers", {"Content-Type": "application/json"})

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()

            return ExecutionResult(
                status="success",
                data={"url": url, "status_code": resp.status_code},
                metadata={"node_type": "notification_sender", "channel": "webhook"},
                duration=time.time() - start,
            )
        except Exception as e:
            return self._failure(
                f"Webhook POST failed: {e}",
                node_type="notification_sender",
                channel="webhook",
                url=url,
            )


# Register at import time
register_node("notify", NotificationSenderNode)
