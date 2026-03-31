"""
WebSocket TCP_NODELAY and Flush Utilities
==========================================

Fixes for WebSocket message delivery on Windows.

PROBLEM:
Neither the ``websockets`` library nor ``uvicorn`` set ``TCP_NODELAY``
on WebSocket connections. This means Nagle's algorithm is active, which
coalesces small TCP writes (like individual WebSocket frames). Combined
with Windows' Delayed ACK (~200ms), this causes WebSocket responses to
appear "stuck" until the next incoming packet triggers a flush.

FIX:
1. Monkey-patch uvicorn's WebSocket protocol handler to set TCP_NODELAY
   on every new connection.
2. Provide ``set_tcp_nodelay()`` for direct use in WebSocket handlers.
3. Provide ``ws_send_and_flush()`` to ensure data reaches the network.

This module MUST be imported early in ``server/main.py`` (before any
connections are accepted) so the monkey-patch takes effect.
"""

import asyncio
import logging
import socket
import time
from typing import Any

logger = logging.getLogger(__name__)

# Track whether the patch has been applied
_patch_applied = False


def set_tcp_nodelay(transport: asyncio.Transport) -> bool:
    """Set TCP_NODELAY on the socket underlying an asyncio transport.

    Returns True if successfully set, False otherwise.
    """
    try:
        sock = transport.get_extra_info("socket")
        if sock and hasattr(sock, "setsockopt"):
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            return True
    except Exception as e:
        logger.debug("Could not set TCP_NODELAY: %s", e)
    return False


def set_tcp_nodelay_on_websocket(websocket: Any) -> bool:
    """Try to set TCP_NODELAY on a Starlette WebSocket object.

    Starlette doesn't expose the raw transport directly, but we can
    try to access it through the internal state chain.
    """
    # Path 1: Try scope → server tuple → find socket by server address
    # This is fragile and not recommended

    # Path 2: Try internal _send/_receive chains
    # In uvicorn's websockets impl, the ASGI scope is set on the protocol
    # object which has .transport

    # For now, this is handled by the monkey-patch below.
    # This function is a no-op placeholder for future direct access.
    return False


def _apply_uvicorn_tcp_nodelay_patch() -> None:
    """Monkey-patch uvicorn's WebSocket protocols to set TCP_NODELAY.

    This patches ``connection_made()`` on all uvicorn WebSocket protocol
    handlers. Each new connection will have TCP_NODELAY set before any
    data is exchanged.
    """
    global _patch_applied
    if _patch_applied:
        return
    _patch_applied = True

    patched = []

    # Patch the websockets-based protocol (used with uvicorn[standard])
    try:
        from uvicorn.protocols.websockets.websockets_impl import WebSocketProtocol

        _orig_ws_connection_made = WebSocketProtocol.connection_made

        def _patched_ws_connection_made(self: Any, transport: asyncio.Transport) -> None:
            _orig_ws_connection_made(self, transport)
            if set_tcp_nodelay(transport):
                logger.debug("TCP_NODELAY set on WebSocket connection (websockets impl)")

        WebSocketProtocol.connection_made = _patched_ws_connection_made  # type: ignore[assignment]
        patched.append("websockets_impl.WebSocketProtocol")
    except ImportError:
        pass

    # Patch the wsproto-based protocol
    try:
        from uvicorn.protocols.websockets.wsproto_impl import WSProtocol

        _orig_wsp_connection_made = WSProtocol.connection_made

        def _patched_wsp_connection_made(self: Any, transport: asyncio.Transport) -> None:
            _orig_wsp_connection_made(self, transport)
            if set_tcp_nodelay(transport):
                logger.debug("TCP_NODELAY set on WebSocket connection (wsproto impl)")

        WSProtocol.connection_made = _patched_wsp_connection_made  # type: ignore[assignment]
        patched.append("wsproto_impl.WSProtocol")
    except ImportError:
        pass

    # Patch the sans-io websockets protocol
    try:
        from uvicorn.protocols.websockets.websockets_sansio_impl import WebSocketProtocol as SansIOProtocol

        _orig_sansio_connection_made = SansIOProtocol.connection_made

        def _patched_sansio_connection_made(self: Any, transport: asyncio.Transport) -> None:
            _orig_sansio_connection_made(self, transport)
            if set_tcp_nodelay(transport):
                logger.debug("TCP_NODELAY set on WebSocket connection (sansio impl)")

        SansIOProtocol.connection_made = _patched_sansio_connection_made  # type: ignore[assignment]
        patched.append("websockets_sansio_impl.WebSocketProtocol")
    except ImportError:
        pass

    # Also patch HTTP protocols (WebSocket starts as HTTP upgrade)
    try:
        from uvicorn.protocols.http.h11_impl import H11Protocol

        _orig_h11_connection_made = H11Protocol.connection_made

        def _patched_h11_connection_made(self: Any, transport: asyncio.Transport) -> None:
            _orig_h11_connection_made(self, transport)
            if set_tcp_nodelay(transport):
                logger.debug("TCP_NODELAY set on HTTP connection (h11)")

        H11Protocol.connection_made = _patched_h11_connection_made  # type: ignore[assignment]
        patched.append("h11_impl.H11Protocol")
    except ImportError:
        pass

    try:
        from uvicorn.protocols.http.httptools_impl import HttpToolsProtocol

        _orig_httptools_connection_made = HttpToolsProtocol.connection_made

        def _patched_httptools_connection_made(self: Any, transport: asyncio.Transport) -> None:
            _orig_httptools_connection_made(self, transport)
            if set_tcp_nodelay(transport):
                logger.debug("TCP_NODELAY set on HTTP connection (httptools)")

        HttpToolsProtocol.connection_made = _patched_httptools_connection_made  # type: ignore[assignment]
        patched.append("httptools_impl.HttpToolsProtocol")
    except ImportError:
        pass

    if patched:
        logger.info("TCP_NODELAY patch applied to: %s", ", ".join(patched))
    else:
        logger.warning("TCP_NODELAY patch: no uvicorn protocols found to patch")


async def ws_send_and_flush(
    websocket: Any,
    data: dict,
    *,
    flush_delay: float = 0.001,
    label: str = "",
) -> None:
    """Send a WebSocket JSON message and ensure it's flushed to the network.

    Unlike plain ``websocket.send_json()`` + ``asyncio.sleep(0)``, this
    function:
    1. Sends the JSON data
    2. Sleeps for ``flush_delay`` seconds (default 1ms) to allow the
       ProactorEventLoop to process IOCP write completions
    3. Logs a diagnostic timestamp for debugging delivery issues

    Args:
        websocket: Starlette WebSocket instance.
        data: Dict to serialize and send as JSON.
        flush_delay: Seconds to sleep after send (0.001 = 1ms).
        label: Optional label for diagnostic logging.
    """
    t0 = time.perf_counter()
    await websocket.send_json(data)
    # Non-zero sleep to ensure the ProactorEventLoop processes IOCP
    # write completions. asyncio.sleep(0) only yields control but
    # doesn't guarantee I/O processing on Windows.
    await asyncio.sleep(flush_delay)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    if elapsed_ms > 50:  # Only log if notably slow
        logger.warning(
            "[WS-FLUSH] %s type=%s took %.1fms",
            label, data.get("type", "?"), elapsed_ms,
        )


# Apply the patch on module import
_apply_uvicorn_tcp_nodelay_patch()
