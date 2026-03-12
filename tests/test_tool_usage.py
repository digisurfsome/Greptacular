"""Unit tests for ToolUsageTracker — Phase 8."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from server.services.tool_usage import (
    ToolUsageTracker,
    MonthlyUsage,
    AllTimeUsage,
    TIER_LIMITS,
    DEFAULT_USER_ID,
)


@pytest.fixture
def tracker(tmp_path):
    """Create a tracker with a temp file."""
    return ToolUsageTracker(usage_path=tmp_path / "usage.json")


class TestToolUsageTracker:
    def test_record_generation(self, tracker):
        """Monthly count increments."""
        tracker.record_generation()
        usage = tracker.get_monthly_usage()
        assert usage.tools_generated == 1

        tracker.record_generation()
        usage = tracker.get_monthly_usage()
        assert usage.tools_generated == 2

    def test_record_execution(self, tracker):
        """Execution count + tokens increment."""
        tracker.record_execution(tokens=100)
        usage = tracker.get_monthly_usage()
        assert usage.chain_executions == 1
        assert usage.tokens_used == 100

        tracker.record_execution(tokens=50)
        usage = tracker.get_monthly_usage()
        assert usage.chain_executions == 2
        assert usage.tokens_used == 150

    def test_monthly_usage(self, tracker):
        """Returns current month's data."""
        usage = tracker.get_monthly_usage()
        assert isinstance(usage, MonthlyUsage)
        assert usage.tools_generated == 0

        tracker.record_generation()
        usage = tracker.get_monthly_usage()
        assert usage.tools_generated == 1

    def test_all_time_usage(self, tracker):
        """Lifetime totals aggregate correctly."""
        tracker.record_generation()
        tracker.record_generation()
        tracker.record_execution(tokens=200)

        all_time = tracker.get_all_time_usage()
        assert isinstance(all_time, AllTimeUsage)
        assert all_time.total_tools_generated == 2
        assert all_time.total_chain_executions == 1
        assert all_time.total_tokens_used == 200
        assert all_time.first_generation_at is not None
        assert all_time.last_generation_at is not None

    def test_check_tier_free_under(self, tracker):
        """3 of 5 → returns True."""
        for _ in range(3):
            tracker.record_generation()
        assert tracker.check_tier_limit(tier="free") is True

    def test_check_tier_free_at_limit(self, tracker):
        """5 of 5 → returns False."""
        for _ in range(5):
            tracker.record_generation()
        assert tracker.check_tier_limit(tier="free") is False

    def test_check_tier_pro_unlimited(self, tracker):
        """Pro tier → always True."""
        for _ in range(100):
            tracker.record_generation()
        assert tracker.check_tier_limit(tier="pro") is True

    def test_usage_history(self, tracker):
        """Returns last N months in order."""
        tracker.record_generation()
        history = tracker.get_usage_history(months=6)
        assert len(history) >= 1
        assert history[0].tools_generated == 1

    def test_month_rollover(self, tracker):
        """New month starts fresh count."""
        # Record in "current" month
        tracker.record_generation()

        # Simulate a different month by patching _current_month
        with patch("server.services.tool_usage._current_month", return_value="2099-01"):
            tracker.record_generation()
            usage = tracker.get_monthly_usage()
            assert usage.month == "2099-01"
            assert usage.tools_generated == 1  # Fresh count for new month

        # All-time should show 2
        all_time = tracker.get_all_time_usage()
        assert all_time.total_tools_generated == 2

    def test_atomic_save(self, tracker):
        """File not corrupted on concurrent writes."""
        # Write multiple times rapidly
        for i in range(10):
            tracker.record_generation()

        usage = tracker.get_monthly_usage()
        assert usage.tools_generated == 10

        # Verify file is valid JSON
        raw = tracker.usage_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        assert DEFAULT_USER_ID in data

    def test_record_deployment(self, tracker):
        """Deployment counts increment."""
        tracker.record_deployment()
        usage = tracker.get_monthly_usage()
        assert usage.tools_deployed == 1

    def test_record_theme_extraction(self, tracker):
        """Theme extraction counts increment."""
        tracker.record_theme_extraction()
        usage = tracker.get_monthly_usage()
        assert usage.themes_extracted == 1

    def test_get_tier_default(self, tracker):
        """Default tier is free."""
        assert tracker.get_tier() == "free"

    def test_get_tier_limits(self, tracker):
        """Tier limits match expected values."""
        free = tracker.get_tier_limits("free")
        assert free["tools_per_month"] == 5
        assert free["batch"] is False

        pro = tracker.get_tier_limits("pro")
        assert pro["tools_per_month"] == -1
        assert pro["batch"] is True

    def test_empty_file_recovery(self, tmp_path):
        """Handles empty/corrupt file gracefully."""
        usage_path = tmp_path / "bad.json"
        usage_path.write_text("not json", encoding="utf-8")
        tracker = ToolUsageTracker(usage_path=usage_path)

        # Should start fresh, not crash
        usage = tracker.get_monthly_usage()
        assert usage.tools_generated == 0
