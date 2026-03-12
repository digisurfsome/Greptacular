"""Unit tests for BatchToolGenerator — Phase 7."""

from unittest.mock import AsyncMock, patch

import pytest

from server.services.batch_tool_generator import (
    BatchToolGenerator,
    _batches,
)
from server.services.tool_registry import ToolRegistryService


@pytest.fixture(autouse=True)
def clear_batches():
    """Clear in-memory batch state between tests."""
    _batches.clear()
    yield
    _batches.clear()


@pytest.fixture
def tmp_registry(tmp_path):
    """Create a registry service with a temp file."""
    return ToolRegistryService(registry_path=tmp_path / "registry.json")


@pytest.fixture
def generator(tmp_registry):
    return BatchToolGenerator(registry=tmp_registry)


def _make_mock_project(project_id: str) -> dict:
    return {
        "name": f"Tool-{project_id}",
        "description": f"Description for {project_id}",
        "steps": [
            {"title": "Step 1", "prompt": "Generate something", "expectedOutput": "Output 1"},
            {"title": "Step 2", "prompt": "Write something", "expectedOutput": "Output 2"},
        ],
        "video_id": "abc123",
        "video_title": f"Video {project_id}",
        "video_channel": "TestChannel",
    }


class TestBatchToolGenerator:
    @pytest.mark.asyncio
    async def test_batch_single_project(self, generator):
        """One project → one tool generated."""
        with patch.object(generator, "_load_project_data", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = _make_mock_project("proj1")

            result = await generator.generate_batch(project_ids=["proj1"])

            assert result.status == "completed"
            assert result.total == 1
            assert result.completed == 1
            assert result.failed == 0
            assert len(result.results) == 1
            assert result.results[0].status == "success"
            assert result.results[0].tool_id is not None

    @pytest.mark.asyncio
    async def test_batch_multiple_projects(self, generator):
        """3 projects → 3 tools, all in registry."""
        with patch.object(generator, "_load_project_data", new_callable=AsyncMock) as mock_load:
            mock_load.side_effect = [
                _make_mock_project("p1"),
                _make_mock_project("p2"),
                _make_mock_project("p3"),
            ]

            result = await generator.generate_batch(project_ids=["p1", "p2", "p3"])

            assert result.status == "completed"
            assert result.total == 3
            assert result.completed == 3
            assert len(result.results) == 3
            for r in result.results:
                assert r.status == "success"

    @pytest.mark.asyncio
    async def test_batch_with_error(self, generator):
        """1 of 3 projects fails → other 2 succeed, failed one logged."""
        async def mock_load(project_id):
            if project_id == "bad":
                return None
            return _make_mock_project(project_id)

        with patch.object(generator, "_load_project_data", side_effect=mock_load):
            result = await generator.generate_batch(project_ids=["p1", "bad", "p3"])

            assert result.status == "completed"
            assert result.completed == 2
            assert result.failed == 1
            assert result.results[1].status == "error"
            assert result.results[1].error is not None

    @pytest.mark.asyncio
    async def test_batch_cancel(self, generator):
        """Cancel mid-batch → remaining projects skipped."""
        call_count = 0

        async def mock_load(project_id):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # After first project, set cancel flag
                for bid in generator._cancel_flags:
                    generator._cancel_flags[bid] = True
            return _make_mock_project(project_id)

        with patch.object(generator, "_load_project_data", side_effect=mock_load):
            result = await generator.generate_batch(project_ids=["p1", "p2", "p3"])

            assert result.status == "cancelled"
            assert result.results[0].status == "success"
            # p2 and p3 should be skipped
            skipped = [r for r in result.results if r.status == "skipped"]
            assert len(skipped) >= 1

    @pytest.mark.asyncio
    async def test_batch_progress_callback(self, generator):
        """Progress callback fires after each tool."""
        progress_calls = []

        def on_progress(msg, completed, total):
            progress_calls.append((msg, completed, total))

        with patch.object(generator, "_load_project_data", new_callable=AsyncMock) as mock_load:
            mock_load.side_effect = [_make_mock_project("p1"), _make_mock_project("p2")]

            await generator.generate_batch(
                project_ids=["p1", "p2"],
                on_progress=on_progress,
            )

            assert len(progress_calls) == 2
            assert progress_calls[0][1] == 1  # completed=1
            assert progress_calls[1][1] == 2  # completed=2

    @pytest.mark.asyncio
    async def test_batch_default_theme(self, generator):
        """Default theme is resolved when theme_id is provided. Falls back gracefully."""
        with patch.object(generator, "_load_project_data", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = _make_mock_project("p1")

            # Even if theme resolution fails (no real theme engine in test),
            # batch should still succeed with theme=None fallback
            result = await generator.generate_batch(
                project_ids=["p1"],
                default_theme_id="nonexistent-theme",
            )

            assert result.completed == 1
            assert result.results[0].status == "success"

    @pytest.mark.asyncio
    async def test_batch_status(self, generator):
        """Status updates correctly: running → completed."""
        with patch.object(generator, "_load_project_data", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = _make_mock_project("p1")

            result = await generator.generate_batch(project_ids=["p1"])

            assert result.status == "completed"
            assert result.completed_at is not None

            # Should be accessible via get_batch_status
            stored = generator.get_batch_status(result.batch_id)
            assert stored is not None
            assert stored.status == "completed"

    def test_batch_get_status_not_found(self, generator):
        """Nonexistent batch returns None."""
        assert generator.get_batch_status("nonexistent") is None

    def test_batch_cancel_not_found(self, generator):
        """Cancel nonexistent batch returns False."""
        assert generator.cancel_batch("nonexistent") is False
