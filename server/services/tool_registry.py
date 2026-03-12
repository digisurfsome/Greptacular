"""Tool Registry Service — CRUD operations on the tool registry JSON file.

All methods are [ROBOT] — pure Python file I/O, no LLM calls.
Storage: ~/.autoforge/tool_registry.json
Atomic writes: .tmp file → os.replace() for crash safety.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..models.tool_factory import (
    GeneratedTool,
    SheetBlueprint,
    ThemeConfig,
    ToolRegistry,
    ToolStatus,
)

logger = logging.getLogger(__name__)


def _default_registry_path() -> Path:
    return Path.home() / ".autoforge" / "tool_registry.json"


class ToolRegistryService:
    """CRUD service for the tool registry.

    All operations are synchronous file I/O. Methods are async for
    router compatibility but contain no awaits (can be called from sync too).
    """

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or _default_registry_path()

    def _load(self) -> ToolRegistry:
        """Read JSON, parse to ToolRegistry. Returns empty registry on any failure."""
        if not self.registry_path.exists():
            return ToolRegistry()
        try:
            raw = self.registry_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            return ToolRegistry.model_validate(data)
        except (json.JSONDecodeError, OSError, Exception) as e:
            logger.warning("Failed to load tool registry, starting fresh: %s", e)
            return ToolRegistry()

    def _save(self, registry: ToolRegistry) -> None:
        """Atomic write: .tmp → os.replace()."""
        try:
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self.registry_path.with_suffix(".tmp")
            tmp_path.write_text(
                registry.model_dump_json(indent=2),
                encoding="utf-8",
            )
            os.replace(str(tmp_path), str(self.registry_path))
        except OSError as e:
            logger.error("Failed to save tool registry: %s", e)

    async def create_tool(self, blueprint: SheetBlueprint) -> GeneratedTool:
        """Generate ID, add to registry, save."""
        registry = self._load()
        now = datetime.now(timezone.utc).isoformat()
        tool = GeneratedTool(
            tool_id=f"tool_{uuid.uuid4().hex[:12]}",
            blueprint=blueprint,
            status=ToolStatus.DRAFT,
            created_at=now,
            updated_at=now,
        )
        registry.tools.append(tool)
        registry.total_tools_created += 1
        self._save(registry)
        logger.info("Created tool %s from blueprint %s", tool.tool_id, blueprint.blueprint_id)
        return tool

    async def get_tool(self, tool_id: str) -> Optional[GeneratedTool]:
        """Lookup by ID."""
        registry = self._load()
        for tool in registry.tools:
            if tool.tool_id == tool_id:
                return tool
        return None

    async def list_tools(
        self,
        status: Optional[ToolStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[GeneratedTool]:
        """Filter and paginate."""
        registry = self._load()
        tools = registry.tools
        if status is not None:
            tools = [t for t in tools if t.status == status]
        return tools[offset: offset + limit]

    async def update_tool(self, tool_id: str, **updates) -> Optional[GeneratedTool]:
        """Partial update, save."""
        registry = self._load()
        for tool in registry.tools:
            if tool.tool_id == tool_id:
                for key, value in updates.items():
                    if hasattr(tool, key):
                        setattr(tool, key, value)
                tool.updated_at = datetime.now(timezone.utc).isoformat()
                self._save(registry)
                return tool
        return None

    async def update_theme(self, tool_id: str, theme: ThemeConfig) -> Optional[GeneratedTool]:
        """Swap theme on tool."""
        return await self.update_tool(tool_id, active_theme=theme)

    async def archive_tool(self, tool_id: str) -> Optional[GeneratedTool]:
        """Set status=archived."""
        return await self.update_tool(tool_id, status=ToolStatus.ARCHIVED)

    async def record_run(self, tool_id: str, tokens_used: int) -> None:
        """Increment run counters."""
        registry = self._load()
        for tool in registry.tools:
            if tool.tool_id == tool_id:
                tool.times_run += 1
                tool.total_tokens_used += tokens_used
                tool.last_run_at = datetime.now(timezone.utc).isoformat()
                tool.updated_at = tool.last_run_at
                self._save(registry)
                return

    async def get_stats(self) -> dict:
        """Aggregate counts."""
        registry = self._load()
        by_status: dict[str, int] = {}
        total_runs = 0
        total_tokens = 0
        for tool in registry.tools:
            by_status[tool.status.value] = by_status.get(tool.status.value, 0) + 1
            total_runs += tool.times_run
            total_tokens += tool.total_tokens_used
        return {
            "total_tools": len(registry.tools),
            "total_tools_created": registry.total_tools_created,
            "total_tools_deployed": registry.total_tools_deployed,
            "by_status": by_status,
            "total_runs": total_runs,
            "total_tokens": total_tokens,
        }
