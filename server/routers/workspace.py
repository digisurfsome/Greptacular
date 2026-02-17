"""
Workspace Chat Router
=====================

WebSocket and REST endpoints for the workspace chat agent.
Unlike the assistant (read-only, per-project), the workspace is a global
read/write agent with a 1M-token context window.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


# ============================================================================
# Pydantic Models
# ============================================================================

class WorkspaceConversationSummary(BaseModel):
    """Summary of a workspace conversation."""
    id: int
    title: Optional[str]
    category: str
    working_directory: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    message_count: int


class WorkspaceMessageModel(BaseModel):
    """A message within a workspace conversation."""
    id: int
    role: str
    content: str
    token_estimate: int
    timestamp: Optional[str]


class WorkspaceConversationDetail(BaseModel):
    """Full workspace conversation with messages."""
    id: int
    title: Optional[str]
    category: str
    working_directory: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    message_count: int
    messages: list[WorkspaceMessageModel]


class ConversationCreateRequest(BaseModel):
    """Request body for creating a new workspace conversation."""
    category: str = "general"
    working_directory: Optional[str] = None


class ConversationUpdateRequest(BaseModel):
    """Request body for updating a workspace conversation."""
    title: Optional[str] = None
    category: Optional[str] = None


# ============================================================================
# REST Endpoints - Conversation Management
# ============================================================================

@router.get("/conversations", response_model=list[WorkspaceConversationSummary])
async def list_conversations():
    """List all workspace conversations."""
    from ..services.workspace_database import get_conversations

    conversations = get_conversations()
    return [WorkspaceConversationSummary(**c) for c in conversations]


@router.post("/conversations", response_model=WorkspaceConversationSummary)
async def create_new_conversation(body: ConversationCreateRequest):
    """Create a new workspace conversation."""
    from ..services.workspace_database import create_conversation

    conversation = create_conversation(
        category=body.category,
        working_directory=body.working_directory,
    )
    return WorkspaceConversationSummary(
        id=int(conversation.id),
        title=str(conversation.title) if conversation.title else None,
        category=str(conversation.category),
        working_directory=str(conversation.working_directory) if conversation.working_directory else None,
        created_at=conversation.created_at.isoformat() if conversation.created_at else None,
        updated_at=conversation.updated_at.isoformat() if conversation.updated_at else None,
        message_count=0,
    )


@router.get("/conversations/{conversation_id}", response_model=WorkspaceConversationDetail)
async def get_conversation_detail(conversation_id: int):
    """Get a specific workspace conversation with all messages."""
    from ..services.workspace_database import get_conversation

    conversation = get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return WorkspaceConversationDetail(
        id=conversation["id"],
        title=conversation["title"],
        category=conversation["category"],
        working_directory=conversation["working_directory"],
        created_at=conversation["created_at"],
        updated_at=conversation["updated_at"],
        message_count=len(conversation["messages"]),
        messages=[WorkspaceMessageModel(**m) for m in conversation["messages"]],
    )


@router.patch("/conversations/{conversation_id}", response_model=WorkspaceConversationSummary)
async def update_conversation(conversation_id: int, body: ConversationUpdateRequest):
    """Update a workspace conversation's title or category."""
    from ..services.workspace_database import update_conversation as db_update_conversation

    updated = db_update_conversation(
        conversation_id,
        title=body.title,
        category=body.category,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return WorkspaceConversationSummary(
        id=updated["id"],
        title=updated["title"],
        category=updated["category"],
        working_directory=updated["working_directory"],
        created_at=updated["created_at"],
        updated_at=updated["updated_at"],
        message_count=updated.get("message_count", 0),
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation_endpoint(conversation_id: int):
    """Delete a workspace conversation and all its messages."""
    from ..services.workspace_database import delete_conversation

    success = delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"success": True, "message": "Conversation deleted"}


@router.get("/conversations/{conversation_id}/tokens")
async def get_conversation_tokens(conversation_id: int):
    """Get the estimated token usage for a conversation."""
    from ..services.workspace_chat_session import CONTEXT_WINDOW_TOKENS
    from ..services.workspace_database import get_conversation_token_total

    total = get_conversation_token_total(conversation_id)
    return {
        "total_tokens": total,
        "context_window": CONTEXT_WINDOW_TOKENS,
        "usage_percent": round(total / CONTEXT_WINDOW_TOKENS * 100, 1) if CONTEXT_WINDOW_TOKENS > 0 else 0,
    }


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@router.websocket("/ws")
async def workspace_chat_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for workspace chat.

    Message protocol:

    Client -> Server:
    - {"type": "start", "conversation_id": int | null, "working_directory": "..."} - Start/resume session
    - {"type": "message", "content": "..."} - Send user message
    - {"type": "answer", "answers": {...}} - Answer to structured questions
    - {"type": "ping"} - Keep-alive ping

    Server -> Client:
    - {"type": "conversation_created", "conversation_id": int} - New conversation created
    - {"type": "text", "content": "..."} - Text chunk from Claude
    - {"type": "tool_call", "tool": "...", "input": {...}} - Tool being called
    - {"type": "token_usage", "total_tokens": int, "context_window": int} - Token usage update
    - {"type": "response_done"} - Response complete
    - {"type": "error", "content": "..."} - Error message
    - {"type": "pong"} - Keep-alive pong
    """
    # Always accept WebSocket first to avoid opaque 403 errors
    await websocket.accept()

    # Generate a unique session ID from the websocket object
    session_id = f"ws-{id(websocket)}"
    logger.info(f"Workspace WebSocket connected, session_id={session_id}")

    from ..services.workspace_chat_session import create_session as ws_create_session
    from ..services.workspace_chat_session import get_session as ws_get_session
    from ..services.workspace_chat_session import remove_session as ws_remove_session

    session = None

    try:
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                msg_type = message.get("type")
                logger.debug(f"Workspace received message type: {msg_type}")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                elif msg_type == "start":
                    # Get optional conversation_id and working_directory
                    conversation_id = message.get("conversation_id")
                    working_directory = message.get("working_directory")

                    # If resuming an existing conversation without an explicit working_directory,
                    # look it up from the database so the agent uses the same cwd.
                    if conversation_id is not None and working_directory is None:
                        from ..services.workspace_database import get_conversation
                        conv = get_conversation(conversation_id)
                        if conv:
                            working_directory = conv.get("working_directory")

                    logger.debug(
                        f"Processing start message with conversation_id={conversation_id}, "
                        f"working_directory={working_directory}"
                    )

                    try:
                        # Create a new workspace session
                        logger.debug(f"Creating workspace session {session_id}")
                        session = await ws_create_session(
                            session_id,
                            conversation_id=conversation_id,
                            working_directory=working_directory,
                        )
                        logger.debug("Workspace session created, starting...")

                        # Stream the initial greeting or resume acknowledgement
                        async for chunk in session.start():
                            if logger.isEnabledFor(logging.DEBUG):
                                logger.debug(f"Sending chunk: {chunk.get('type')}")
                            await websocket.send_json(chunk)
                        logger.debug("Workspace session start complete")
                    except Exception as e:
                        logger.exception(f"Error starting workspace session {session_id}")
                        await websocket.send_json({
                            "type": "error",
                            "content": f"Failed to start session: {str(e)}"
                        })

                elif msg_type == "message":
                    if not session:
                        session = ws_get_session(session_id)
                        if not session:
                            await websocket.send_json({
                                "type": "error",
                                "content": "No active session. Send 'start' first."
                            })
                            continue

                    user_content = message.get("content", "").strip()
                    if not user_content:
                        await websocket.send_json({
                            "type": "error",
                            "content": "Empty message"
                        })
                        continue

                    # Stream Claude's response
                    async for chunk in session.send_message(user_content):
                        await websocket.send_json(chunk)

                elif msg_type == "answer":
                    # User answered a structured question
                    if not session:
                        session = ws_get_session(session_id)
                        if not session:
                            await websocket.send_json({
                                "type": "error",
                                "content": "No active session. Send 'start' first."
                            })
                            continue

                    # Format the answers as a natural response
                    answers = message.get("answers", {})
                    if isinstance(answers, dict):
                        response_parts = []
                        for question_idx, answer_value in answers.items():
                            if isinstance(answer_value, list):
                                response_parts.append(", ".join(answer_value))
                            else:
                                response_parts.append(str(answer_value))
                        user_response = "; ".join(response_parts) if response_parts else "OK"
                    else:
                        user_response = str(answers)

                    # Stream Claude's response
                    async for chunk in session.send_message(user_response):
                        await websocket.send_json(chunk)

                else:
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Unknown message type: {msg_type}"
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid JSON"
                })

    except WebSocketDisconnect:
        logger.info(f"Workspace chat WebSocket disconnected for session {session_id}")

    except Exception as e:
        logger.exception(f"Workspace chat WebSocket error for session {session_id}")
        try:
            await websocket.send_json({
                "type": "error",
                "content": f"Server error: {str(e)}"
            })
        except Exception:
            pass

    finally:
        # Clean up the session on disconnect -- workspace sessions are not resumed
        # across WebSocket connections (unlike the assistant which keeps sessions alive).
        await ws_remove_session(session_id)
