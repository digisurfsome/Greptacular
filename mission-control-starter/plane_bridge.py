"""
Plane Bridge
=============
Webhook listener that connects Plane (project management) to Claude AI agents.

How it will work:
1. Plane sends a webhook when an issue is assigned to AI
2. This server receives the webhook and extracts the issue details
3. It calls Claude via sdk_wrapper.call_claude() to do the work
4. It posts the results back to Plane via the Plane API

Status: PLACEHOLDER — the FastAPI skeleton is here, but the handlers are TODO.
"""

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException

# TODO: Uncomment when sdk_wrapper dependencies are installed
# from sdk_wrapper import call_claude

load_dotenv()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mission Control — Plane Bridge",
    description="Receives webhooks from Plane and triggers Claude AI agents",
)


# --- Configuration ---
# These will come from .env once Plane is set up
PLANE_API_URL = os.getenv("PLANE_API_URL", "http://localhost:8080")
PLANE_API_TOKEN = os.getenv("PLANE_API_TOKEN", "")
PLANE_WEBHOOK_SECRET = os.getenv("PLANE_WEBHOOK_SECRET", "")


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "mission-control"}


@app.post("/webhook/plane")
async def receive_plane_webhook(request: Request):
    """
    Receive webhook events from Plane.

    TODO:
    - Verify webhook signature using PLANE_WEBHOOK_SECRET
    - Parse the event type (issue.created, issue.updated, etc.)
    - Check if the issue is assigned to the AI label/user
    - Extract issue title, description, and context
    - Call sdk_wrapper.call_claude() with the issue details
    - Post Claude's response back to Plane as a comment
    - Update issue status in Plane
    """
    # TODO: Verify webhook signature
    body = await request.json()
    logger.info(f"Received webhook event: {body.get('event', 'unknown')}")

    # TODO: Process the event
    # event_type = body.get("event")
    # if event_type == "issue.updated":
    #     issue = body.get("data", {})
    #     # Check if assigned to AI
    #     # Build prompt from issue details
    #     # result = await call_claude(system_prompt=..., user_message=...)
    #     # Post result back to Plane

    return {"status": "received"}


# TODO: Add these endpoints as needed:
#
# POST /webhook/plane — receives Plane webhooks (done above, needs implementation)
#
# GET /issues — list issues currently being processed by AI
#
# POST /issues/{id}/retry — retry a failed AI task
#
# GET /status — show connection status for Plane + Claude


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
