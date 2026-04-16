"""
Web Scraper Node — Tiered Web Content Extraction
==================================================

Tier 1: httpx (fast, lightweight — works for most static pages)
Tier 2: Headless Playwright (for JS-rendered content)
Tier 3: Full Playwright with scrolling/interaction (heavy dynamic pages)

Each tier is attempted in order; escalation happens on failure.
"""

import logging
import time
from typing import Any

from . import register_node
from .base_node import BaseExecutionNode, ExecutionResult

logger = logging.getLogger(__name__)


class WebScraperNode(BaseExecutionNode):
    """Tiered web scraper: httpx -> headless Playwright -> full Playwright."""

    async def validate(self, task: dict) -> tuple[bool, str]:
        url = task.get("url", "")
        if not url:
            return False, "Missing required field: url"
        if not url.startswith(("http://", "https://")):
            return False, f"Invalid URL scheme: {url}"
        return True, ""

    async def execute(self, task: dict) -> ExecutionResult:
        url = task.get("url", "")
        selector = task.get("selector")  # Optional CSS selector to extract
        tier = task.get("tier", "auto")  # "auto", "httpx", "playwright", "full"
        start = time.time()

        # Try tiers in order if auto
        if tier in ("auto", "httpx"):
            result = await self._tier1_httpx(url, selector)
            if result.status == "success":
                result.duration = time.time() - start
                result.metadata["tier"] = "httpx"
                return result
            if tier == "httpx":
                result.duration = time.time() - start
                return result

        if tier in ("auto", "playwright"):
            result = await self._tier2_headless(url, selector)
            if result.status == "success":
                result.duration = time.time() - start
                result.metadata["tier"] = "headless_playwright"
                return result
            if tier == "playwright":
                result.duration = time.time() - start
                return result

        if tier in ("auto", "full"):
            result = await self._tier3_full(url, selector)
            result.duration = time.time() - start
            result.metadata["tier"] = "full_playwright"
            return result

        return self._failure(
            f"All scraping tiers failed for {url}",
            node_type="web_scraper",
            url=url,
        )

    async def _tier1_httpx(self, url: str, selector: str | None) -> ExecutionResult:
        """Tier 1: Simple HTTP GET with httpx."""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; AutoForge/1.0)"
                })
                resp.raise_for_status()
                content = resp.text

                # If a selector is specified, try basic extraction
                extracted = content
                if selector:
                    try:
                        from html.parser import HTMLParser
                        # Basic extraction — full selector support requires lxml/bs4
                        extracted = content  # Fallback to full content
                    except Exception:
                        pass

                return self._success(
                    data={"content": extracted[:50000], "status_code": resp.status_code, "content_length": len(content)},
                    url=url,
                )
        except Exception as e:
            return self._failure(
                f"httpx scrape failed: {e}",
                node_type="web_scraper",
                url=url,
                attempted_tier="httpx",
            )

    async def _tier2_headless(self, url: str, selector: str | None) -> ExecutionResult:
        """Tier 2: Headless Playwright for JS-rendered pages."""
        try:
            from . import playwright_manager

            context = await playwright_manager.create_context()
            try:
                page = await context.new_page()
                await page.goto(url, wait_until="networkidle", timeout=20000)

                if selector:
                    element = await page.query_selector(selector)
                    content = await element.inner_text() if element else await page.content()
                else:
                    content = await page.content()

                return self._success(
                    data={"content": content[:50000], "content_length": len(content)},
                    url=url,
                )
            finally:
                await context.close()
        except Exception as e:
            return self._failure(
                f"Headless Playwright scrape failed: {e}",
                node_type="web_scraper",
                url=url,
                attempted_tier="headless_playwright",
            )

    async def _tier3_full(self, url: str, selector: str | None) -> ExecutionResult:
        """Tier 3: Full Playwright with scroll and wait for dynamic content."""
        try:
            from . import playwright_manager

            context = await playwright_manager.create_context(timeout_ms=45000)
            try:
                page = await context.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # Scroll to load lazy content
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await page.wait_for_timeout(1000)

                if selector:
                    await page.wait_for_selector(selector, timeout=10000)
                    element = await page.query_selector(selector)
                    content = await element.inner_text() if element else await page.content()
                else:
                    content = await page.content()

                return self._success(
                    data={"content": content[:50000], "content_length": len(content)},
                    url=url,
                )
            finally:
                await context.close()
        except Exception as e:
            return self._failure(
                f"Full Playwright scrape failed: {e}",
                node_type="web_scraper",
                url=url,
                attempted_tier="full_playwright",
            )


# Register at import time
register_node("scrape", WebScraperNode)
