"""Integration tests for batch + usage API endpoints — Phase 7+8.

Tests the usage endpoints (synchronous, no background tasks).
Batch endpoints are tested via unit tests since they use asyncio.create_task.
"""

import httpx
import pytest
from fastapi import FastAPI

from server.routers.tool_factory import router


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


class TestUsageEndpoints:
    @pytest.mark.asyncio
    async def test_usage_endpoint(self, app):
        """GET /usage returns valid usage stats."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/tool-factory/usage")
            assert response.status_code == 200
            data = response.json()
            assert "monthly" in data
            assert "all_time" in data
            assert "tier" in data
            assert "limits" in data

    @pytest.mark.asyncio
    async def test_usage_history_endpoint(self, app):
        """GET /usage/history returns monthly data."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/tool-factory/usage/history?months=3")
            assert response.status_code == 200
            data = response.json()
            assert "history" in data
            assert isinstance(data["history"], list)

    @pytest.mark.asyncio
    async def test_usage_history_invalid_months(self, app):
        """GET /usage/history rejects invalid months param."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/tool-factory/usage/history?months=0")
            assert response.status_code == 400

            response = await client.get("/api/tool-factory/usage/history?months=25")
            assert response.status_code == 400


class TestBatchEndpoints:
    @pytest.mark.asyncio
    async def test_batch_status_not_found(self, app):
        """GET /batch/{id} returns 404 for unknown batch."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/tool-factory/batch/nonexistent")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_batch_cancel_not_found(self, app):
        """POST /batch/cancel/{id} returns 404 for unknown batch."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/tool-factory/batch/cancel/nonexistent")
            assert response.status_code == 404
