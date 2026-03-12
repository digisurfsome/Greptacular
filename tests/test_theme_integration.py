"""Integration tests for theme endpoints."""

import os

import pytest

# Allow remote access for test client to bypass localhost middleware
os.environ["AUTOFORGE_ALLOW_REMOTE"] = "1"

from fastapi.testclient import TestClient  # noqa: E402

from server.main import app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


class TestThemeEndpoints:
    def test_theme_endpoint_list(self, client):
        """GET /themes returns 10+ themes."""
        resp = client.get("/api/tool-factory/themes")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 10
        assert len(data["themes"]) >= 10

    def test_theme_endpoint_get(self, client):
        """GET /themes/ocean-depths returns valid ThemeConfig."""
        resp = client.get("/api/tool-factory/themes/ocean-depths")
        assert resp.status_code == 200
        data = resp.json()
        assert data["theme_name"] == "Ocean Depths"
        assert data["source"] == "preset"
        assert "colors" in data
        assert "typography" in data

    def test_theme_endpoint_get_with_prefix(self, client):
        """GET /themes/preset-ocean-depths also works."""
        resp = client.get("/api/tool-factory/themes/preset-ocean-depths")
        assert resp.status_code == 200
        assert resp.json()["theme_name"] == "Ocean Depths"

    def test_theme_endpoint_get_not_found(self, client):
        """GET /themes/nonexistent returns 404."""
        resp = client.get("/api/tool-factory/themes/nonexistent")
        assert resp.status_code == 404

    def test_theme_endpoint_preview(self, client):
        """POST /themes/preview returns sample cells + swatches."""
        resp = client.post("/api/tool-factory/themes/preview", json={"theme_id": "ocean-depths"})
        assert resp.status_code == 200
        data = resp.json()
        assert "sample_cells" in data
        assert "color_swatches" in data
        assert "font_preview" in data
        assert len(data["sample_cells"]) >= 3
        assert len(data["color_swatches"]) >= 5

    def test_theme_endpoint_preview_missing_id(self, client):
        """POST /themes/preview with no theme_id returns 400."""
        resp = client.post("/api/tool-factory/themes/preview", json={})
        assert resp.status_code == 400


class TestGoogleAuthEndpoints:
    def test_google_status_not_authed(self, client):
        """GET /google/status returns authenticated=false initially."""
        resp = client.get("/api/tool-factory/google/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["authenticated"] is False
