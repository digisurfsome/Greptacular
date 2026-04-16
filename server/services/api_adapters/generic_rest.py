"""
Generic REST API Adapter
==========================

Fallback adapter for arbitrary REST APIs.
Supports GET, POST, PUT, PATCH, DELETE with configurable headers and auth.
"""

import logging

from .base import APIAdapter, register_adapter

logger = logging.getLogger(__name__)


class GenericRestAdapter(APIAdapter):
    """Generic REST API adapter for arbitrary HTTP endpoints."""

    async def execute(self, action: str, payload: dict) -> dict:
        """Execute a generic REST API call.

        The 'action' parameter maps to HTTP methods: get, post, put, patch, delete.

        Payload fields:
            - url: Target URL (required)
            - headers: Custom headers (optional)
            - body: Request body for POST/PUT/PATCH (optional)
            - params: Query parameters (optional)
        """
        import httpx

        url = payload.get("url", "")
        if not url:
            return {"output": "Error: url is required", "error": True}

        method = action.upper()
        if method not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
            return {"output": f"Unknown HTTP method: {action}", "error": True}

        headers = payload.get("headers", {})
        if self.api_key:
            headers.setdefault("Authorization", f"Bearer {self.api_key}")

        params = payload.get("params", {})
        body = payload.get("body")

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            try:
                if method in ("POST", "PUT", "PATCH"):
                    resp = await client.request(
                        method, url, headers=headers, params=params, json=body
                    )
                else:
                    resp = await client.request(
                        method, url, headers=headers, params=params
                    )

                resp.raise_for_status()

                # Try to parse as JSON, fall back to text
                try:
                    response_data = resp.json()
                    return {"output": str(response_data)[:5000], "data": response_data, "status_code": resp.status_code}
                except Exception:
                    return {"output": resp.text[:5000], "status_code": resp.status_code}

            except httpx.HTTPStatusError as e:
                return {
                    "output": f"HTTP {e.response.status_code}: {e.response.text[:500]}",
                    "status_code": e.response.status_code,
                    "error": True,
                }
            except Exception as e:
                return {"output": f"Request failed: {e}", "error": True}


register_adapter("generic_rest", GenericRestAdapter)
