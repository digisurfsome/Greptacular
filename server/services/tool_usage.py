"""Tool Usage Tracker — per-user tool usage for SaaS tier limits.

All methods are [ROBOT] — pure Python file I/O, no LLM calls.
Storage: ~/.autoforge/tool_usage.json
Atomic writes: .tmp file → os.replace() for crash safety.
Same pattern as tool_registry.py and rate_limit_logger.py.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tier Definitions
# ---------------------------------------------------------------------------

TIER_LIMITS: dict[str, dict[str, Any]] = {
    "free": {"tools_per_month": 5, "themes": ["preset_only"], "batch": False, "api_access": False},
    "pro": {"tools_per_month": -1, "themes": ["all"], "batch": True, "api_access": False},
    "enterprise": {"tools_per_month": -1, "themes": ["all"], "batch": True, "api_access": True},
}

DEFAULT_USER_ID = "local"


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class MonthlyUsage(BaseModel):
    month: str = ""  # "2026-03"
    tools_generated: int = 0
    tools_deployed: int = 0
    chain_executions: int = 0
    tokens_used: int = 0
    themes_extracted: int = 0


class AllTimeUsage(BaseModel):
    total_tools_generated: int = 0
    total_tools_deployed: int = 0
    total_chain_executions: int = 0
    total_tokens_used: int = 0
    first_generation_at: Optional[str] = None
    last_generation_at: Optional[str] = None


class UsageRecord(BaseModel):
    user_id: str = DEFAULT_USER_ID
    tier: str = "free"
    monthly_history: list[MonthlyUsage] = Field(default_factory=list)
    all_time: AllTimeUsage = Field(default_factory=AllTimeUsage)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

def _default_usage_path() -> Path:
    return Path.home() / ".autoforge" / "tool_usage.json"


def _current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


class ToolUsageTracker:
    """[ROBOT] Track per-user tool usage for SaaS tier limits.

    Storage: ~/.autoforge/tool_usage.json
    Same atomic file pattern as tool_registry.py and rate_limit_logger.py.
    """

    def __init__(self, usage_path: Optional[Path] = None):
        self.usage_path = usage_path or _default_usage_path()

    def _load(self) -> dict[str, UsageRecord]:
        """Load all user records from JSON. Returns empty dict on failure."""
        if not self.usage_path.exists():
            return {}
        try:
            raw = self.usage_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            if not isinstance(data, dict):
                return {}
            result = {}
            for uid, record_data in data.items():
                try:
                    result[uid] = UsageRecord.model_validate(record_data)
                except Exception:
                    logger.warning("Skipping invalid usage record for user %s", uid)
            return result
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load tool usage, starting fresh: %s", e)
            return {}

    def _save(self, records: dict[str, UsageRecord]) -> None:
        """Atomic write: .tmp → os.replace()."""
        try:
            self.usage_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self.usage_path.with_suffix(".tmp")
            serialized = {uid: json.loads(r.model_dump_json()) for uid, r in records.items()}
            tmp_path.write_text(json.dumps(serialized, indent=2), encoding="utf-8")
            os.replace(str(tmp_path), str(self.usage_path))
        except OSError as e:
            logger.error("Failed to save tool usage: %s", e)

    def _get_or_create_record(self, records: dict[str, UsageRecord], user_id: str) -> UsageRecord:
        if user_id not in records:
            records[user_id] = UsageRecord(user_id=user_id)
        return records[user_id]

    def _get_or_create_month(self, record: UsageRecord, month: str) -> MonthlyUsage:
        for m in record.monthly_history:
            if m.month == month:
                return m
        new_month = MonthlyUsage(month=month)
        record.monthly_history.append(new_month)
        # Keep sorted, most recent last
        record.monthly_history.sort(key=lambda m: m.month)
        return new_month

    def record_generation(self, user_id: str = DEFAULT_USER_ID, tool_id: str = "") -> None:
        """[ROBOT] Increment monthly generation count."""
        records = self._load()
        record = self._get_or_create_record(records, user_id)
        month = _current_month()
        monthly = self._get_or_create_month(record, month)

        monthly.tools_generated += 1
        record.all_time.total_tools_generated += 1

        now = datetime.now(timezone.utc).isoformat()
        record.all_time.last_generation_at = now
        if not record.all_time.first_generation_at:
            record.all_time.first_generation_at = now

        self._save(records)

    def record_deployment(self, user_id: str = DEFAULT_USER_ID, tool_id: str = "") -> None:
        """[ROBOT] Increment monthly deployment count."""
        records = self._load()
        record = self._get_or_create_record(records, user_id)
        month = _current_month()
        monthly = self._get_or_create_month(record, month)

        monthly.tools_deployed += 1
        record.all_time.total_tools_deployed += 1
        self._save(records)

    def record_execution(self, user_id: str = DEFAULT_USER_ID, tool_id: str = "", tokens: int = 0) -> None:
        """[ROBOT] Increment execution count + token total."""
        records = self._load()
        record = self._get_or_create_record(records, user_id)
        month = _current_month()
        monthly = self._get_or_create_month(record, month)

        monthly.chain_executions += 1
        monthly.tokens_used += tokens
        record.all_time.total_chain_executions += 1
        record.all_time.total_tokens_used += tokens
        self._save(records)

    def record_theme_extraction(self, user_id: str = DEFAULT_USER_ID) -> None:
        """[ROBOT] Increment theme extraction count."""
        records = self._load()
        record = self._get_or_create_record(records, user_id)
        month = _current_month()
        monthly = self._get_or_create_month(record, month)

        monthly.themes_extracted += 1
        self._save(records)

    def get_monthly_usage(self, user_id: str = DEFAULT_USER_ID) -> MonthlyUsage:
        """[ROBOT] Returns current month's counts."""
        records = self._load()
        record = records.get(user_id)
        if not record:
            return MonthlyUsage(month=_current_month())

        month = _current_month()
        for m in record.monthly_history:
            if m.month == month:
                return m
        return MonthlyUsage(month=month)

    def get_all_time_usage(self, user_id: str = DEFAULT_USER_ID) -> AllTimeUsage:
        """[ROBOT] Returns lifetime totals."""
        records = self._load()
        record = records.get(user_id)
        if not record:
            return AllTimeUsage()
        return record.all_time

    def check_tier_limit(self, user_id: str = DEFAULT_USER_ID, tier: str = "free") -> bool:
        """[ROBOT] Returns True if user is under their tier limit for this month."""
        limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        max_tools = limits["tools_per_month"]

        # -1 means unlimited
        if max_tools == -1:
            return True

        monthly = self.get_monthly_usage(user_id)
        return monthly.tools_generated < max_tools

    def get_usage_history(self, user_id: str = DEFAULT_USER_ID, months: int = 6) -> list[MonthlyUsage]:
        """[ROBOT] Historical monthly data, most recent first."""
        records = self._load()
        record = records.get(user_id)
        if not record:
            return []

        # Return last N months, most recent first
        history = sorted(record.monthly_history, key=lambda m: m.month, reverse=True)
        return history[:months]

    def get_tier(self, user_id: str = DEFAULT_USER_ID) -> str:
        """[ROBOT] Get user's current tier."""
        records = self._load()
        record = records.get(user_id)
        if not record:
            return "free"
        return record.tier

    def get_tier_limits(self, tier: str = "free") -> dict[str, Any]:
        """[ROBOT] Get limits for a tier."""
        return TIER_LIMITS.get(tier, TIER_LIMITS["free"])
