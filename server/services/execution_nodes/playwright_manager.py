"""
Playwright Manager — Singleton Browser Instance Management
============================================================

Manages a shared Playwright browser instance to prevent resource leaks.
Creates isolated browser contexts for each operation.

IMPORTANT: Playwright is lazily imported to avoid breaking servers
where it's not installed.
"""

import asyncio
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Singleton state
_playwright_instance: Any = None
_browser_instance: Any = None
_manager_lock = asyncio.Lock()

DEFAULT_TIMEOUT_MS = 30_000  # 30 seconds per operation


async def get_browser():
    """Get or create the shared browser instance.

    Returns a Playwright browser. Creates one if it doesn't exist.
    Thread-safe via asyncio.Lock.
    """
    global _playwright_instance, _browser_instance

    async with _manager_lock:
        if _browser_instance is not None:
            # Verify browser is still connected
            try:
                if _browser_instance.is_connected():
                    return _browser_instance
            except Exception:
                pass
            # Browser disconnected, recreate
            _browser_instance = None

        # Lazy import to avoid import-time errors
        from playwright.async_api import async_playwright

        if _playwright_instance is None:
            _playwright_instance = await async_playwright().start()

        _browser_instance = await _playwright_instance.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        logger.info("Playwright browser launched (headless)")
        return _browser_instance


async def create_context(timeout_ms: int = DEFAULT_TIMEOUT_MS) -> Any:
    """Create an isolated browser context with timeout.

    The caller is responsible for closing the context when done.
    Use as:
        context = await create_context()
        try:
            page = await context.new_page()
            # ... do work ...
        finally:
            await context.close()
    """
    browser = await get_browser()
    context = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    )
    context.set_default_timeout(timeout_ms)
    return context


async def shutdown() -> None:
    """Close the browser and Playwright instances. Call on app shutdown."""
    global _playwright_instance, _browser_instance

    async with _manager_lock:
        if _browser_instance is not None:
            try:
                await _browser_instance.close()
            except Exception as e:
                logger.warning("Browser close error during shutdown: %s", e)
            _browser_instance = None

        if _playwright_instance is not None:
            try:
                await _playwright_instance.stop()
            except Exception as e:
                logger.warning("Playwright stop error during shutdown: %s", e)
            _playwright_instance = None

    logger.info("Playwright manager shut down")
