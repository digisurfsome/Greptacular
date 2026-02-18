"""
Design Guide Router
===================

WebSocket endpoint for the AI Design Guide chat.

This powers the design style selection flow during project creation.
Unlike other chat endpoints, this does NOT require a project name
(the project hasn't been created yet) and uses a session_id instead.
"""

import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services.design_guide_session import (
    DesignGuideChatSession,
    create_session,
    get_session,
    remove_session,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/design-guide", tags=["design-guide"])


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@router.websocket("/ws")
async def design_guide_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for the AI design guide chat.

    No project name is required - this runs during project creation,
    before a project exists. Sessions are identified by a server-generated
    session ID returned in the ``started`` message.

    Message protocol:

    Client -> Server:
    - {"type": "start", "context": {...}} - Start session with design context
    - {"type": "message", "content": "...", "context": {...}} - Send user message
    - {"type": "ping"} - Keep-alive ping

    Server -> Client:
    - {"type": "started", "sessionId": "..."} - Session created
    - {"type": "text", "content": "..."} - Text chunk from Claude
    - {"type": "action", "action": {...}} - Structured action (select style, set color, etc.)
    - {"type": "response_done"} - Response complete
    - {"type": "error", "content": "..."} - Error message
    - {"type": "pong"} - Keep-alive pong
    """
    # Always accept WebSocket first to avoid opaque 403 errors
    await websocket.accept()

    session: Optional[DesignGuideChatSession] = None
    session_id: Optional[str] = None

    try:
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                msg_type = message.get("type")
                logger.debug(f"Design guide received message type: {msg_type}")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                elif msg_type == "start":
                    # Extract design context from the start message
                    context = message.get("context", {})

                    # Generate a unique session ID
                    session_id = str(uuid.uuid4())

                    try:
                        session = await create_session(session_id, context)

                        # Notify client of the session ID
                        await websocket.send_json({
                            "type": "started",
                            "sessionId": session_id,
                        })

                        # Stream the initial greeting from Claude
                        async for chunk in session.start():
                            await websocket.send_json(chunk)

                    except Exception as e:
                        logger.exception("Error starting design guide session")
                        await websocket.send_json({
                            "type": "error",
                            "content": f"Failed to start session: {str(e)}",
                        })

                elif msg_type == "message":
                    if not session:
                        # Try to recover session from registry if we have a session_id
                        if session_id:
                            session = get_session(session_id)
                        if not session:
                            await websocket.send_json({
                                "type": "error",
                                "content": "No active session. Send 'start' first.",
                            })
                            continue

                    user_content = message.get("content", "").strip()
                    if not user_content:
                        await websocket.send_json({
                            "type": "error",
                            "content": "Empty message",
                        })
                        continue

                    # Pass along any updated context (e.g., user changed selection in UI)
                    updated_context = message.get("context")

                    # Stream Claude's response with action parsing
                    async for chunk in session.send_message(user_content, context=updated_context):
                        await websocket.send_json(chunk)

                else:
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Unknown message type: {msg_type}",
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid JSON",
                })

    except WebSocketDisconnect:
        logger.info(f"Design guide WebSocket disconnected (session: {session_id})")

    except Exception as e:
        logger.exception(f"Design guide WebSocket error (session: {session_id})")
        try:
            await websocket.send_json({
                "type": "error",
                "content": f"Server error: {str(e)}",
            })
        except Exception:
            pass

    finally:
        # Clean up the session on disconnect since these are ephemeral
        if session_id:
            try:
                await remove_session(session_id)
            except Exception as e:
                logger.warning(f"Error cleaning up design guide session {session_id}: {e}")
