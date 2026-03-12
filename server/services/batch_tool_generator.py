"""Batch Tool Generator — sequential batch generation of tools from projects.

All functions are [ROBOT] — pure Python orchestration, no LLM calls.
Sequential processing to stay within Google Sheets API quota (100 req/100 sec).
Per-tool error isolation: one failure doesn't stop the batch.
"""

import logging
import time
import uuid
from typing import Callable, Optional

from pydantic import BaseModel, Field

from ..models.tool_factory import ToolStatus
from .sheet_blueprint import generate_blueprint
from .sheet_deployer import deploy_sheet
from .tool_registry import ToolRegistryService

logger = logging.getLogger(__name__)

MAX_BATCH_SIZE = 50


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class BatchToolResult(BaseModel):
    """Result for a single tool in a batch."""
    project_id: str
    tool_id: Optional[str] = None
    tool_name: str = ""
    status: str = "success"  # success | error | skipped
    error: Optional[str] = None
    sheet_url: Optional[str] = None
    duration_seconds: float = 0.0


class BatchStatus(BaseModel):
    """Overall batch state."""
    batch_id: str
    total: int
    completed: int = 0
    failed: int = 0
    current_tool: Optional[str] = None
    status: str = "running"  # running | completed | cancelled | error
    results: list[BatchToolResult] = Field(default_factory=list)
    started_at: str = ""
    completed_at: Optional[str] = None


# ---------------------------------------------------------------------------
# In-memory state (same pattern as yt_batch.py)
# ---------------------------------------------------------------------------

_batches: dict[str, BatchStatus] = {}


class BatchToolGenerator:
    """[ROBOT] Generate tools from multiple projects in sequence.

    Sequential processing to avoid Google Sheets API quota issues.
    One failure doesn't stop the batch — errors are logged per-tool.
    """

    def __init__(
        self,
        registry: Optional[ToolRegistryService] = None,
    ):
        self.registry = registry or ToolRegistryService()
        self._cancel_flags: dict[str, bool] = {}

    async def generate_batch(
        self,
        project_ids: list[str],
        default_theme_id: Optional[str] = None,
        auto_deploy: bool = False,
        on_progress: Optional[Callable[[str, int, int], None]] = None,
        credentials=None,
    ) -> BatchStatus:
        """[ROBOT] Main entry. Loops through projects, generates tool for each.

        Args:
            project_ids: List of YT Lab project IDs (or names).
            default_theme_id: Theme preset ID to apply to all tools.
            auto_deploy: If True, deploy each tool to Google Sheets after generation.
            on_progress: Callback(message, completed, total) after each tool.
            credentials: Google OAuth credentials (required if auto_deploy=True).

        Returns:
            BatchStatus with per-tool results.
        """
        batch_id = f"batch_{uuid.uuid4().hex[:12]}"
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        batch = BatchStatus(
            batch_id=batch_id,
            total=len(project_ids),
            started_at=now,
        )
        _batches[batch_id] = batch
        self._cancel_flags[batch_id] = False

        # Resolve theme if specified
        theme = None
        if default_theme_id:
            try:
                from .sheet_theme_engine import preset_theme_to_theme_config
                theme = preset_theme_to_theme_config(default_theme_id)
            except Exception as e:
                logger.warning("Failed to resolve theme %s, using None: %s", default_theme_id, e)

        for i, project_id in enumerate(project_ids):
            # Check for cancellation
            if self._cancel_flags.get(batch_id, False):
                # Mark remaining as skipped
                for remaining_id in project_ids[i:]:
                    batch.results.append(BatchToolResult(
                        project_id=remaining_id,
                        status="skipped",
                        error="Batch cancelled",
                    ))
                batch.status = "cancelled"
                break

            batch.current_tool = project_id
            result = await self._process_single(
                project_id=project_id,
                theme=theme,
                auto_deploy=auto_deploy,
                credentials=credentials,
            )
            batch.results.append(result)

            if result.status == "success":
                batch.completed += 1
            else:
                batch.failed += 1

            if on_progress:
                on_progress(
                    f"Completed {batch.completed + batch.failed}/{batch.total}: {result.tool_name or project_id}",
                    batch.completed + batch.failed,
                    batch.total,
                )

        batch.current_tool = None
        if batch.status == "running":
            batch.status = "completed"
        batch.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Clean up cancel flag
        self._cancel_flags.pop(batch_id, None)

        return batch

    async def _process_single(
        self,
        project_id: str,
        theme=None,
        auto_deploy: bool = False,
        credentials=None,
    ) -> BatchToolResult:
        """[ROBOT] Generate blueprint + optionally deploy for one project.

        Catches errors per-tool so one failure doesn't stop the batch.
        """
        start = time.time()

        try:
            # Load project data from YT Lab
            project_data = await self._load_project_data(project_id)
            if not project_data:
                return BatchToolResult(
                    project_id=project_id,
                    status="error",
                    error=f"Project not found: {project_id}",
                    duration_seconds=round(time.time() - start, 2),
                )

            # Generate blueprint
            blueprint = await generate_blueprint(
                project_name=project_data.get("name", project_id),
                project_description=project_data.get("description", ""),
                steps=project_data.get("steps", []),
                source_video_id=project_data.get("video_id", ""),
                source_video_title=project_data.get("video_title", ""),
                source_video_channel=project_data.get("video_channel", ""),
                source_project_id=project_id,
                theme=theme,
                skip_prompt_conversion=True,  # Batch mode skips prompt conversion for speed
            )

            # Register tool
            tool = await self.registry.create_tool(blueprint)
            tool_name = blueprint.tool_name

            sheet_url = None
            if auto_deploy and credentials:
                try:
                    from .sheet_theme_engine import preset_theme_to_theme_config
                    deploy_theme = theme or preset_theme_to_theme_config("modern-minimalist")
                    result = await deploy_sheet(
                        blueprint=blueprint,
                        theme=deploy_theme,
                        credentials=credentials,
                    )
                    sheet_url = result.get("sheet_url")
                    await self.registry.update_tool(
                        tool.tool_id,
                        status=ToolStatus.ACTIVE,
                        sheet_id=result["sheet_id"],
                        sheet_url=result["sheet_url"],
                        sheet_title=result["sheet_title"],
                        active_theme=deploy_theme,
                    )
                except Exception as deploy_err:
                    logger.warning("Deploy failed for %s (tool still created as draft): %s", project_id, deploy_err)
                    await self.registry.update_tool(tool.tool_id, status=ToolStatus.ERROR)

            return BatchToolResult(
                project_id=project_id,
                tool_id=tool.tool_id,
                tool_name=tool_name,
                status="success",
                sheet_url=sheet_url,
                duration_seconds=round(time.time() - start, 2),
            )

        except Exception as e:
            logger.warning("Batch processing failed for project %s: %s", project_id, e)
            return BatchToolResult(
                project_id=project_id,
                status="error",
                error=str(e),
                duration_seconds=round(time.time() - start, 2),
            )

    async def _load_project_data(self, project_id: str) -> Optional[dict]:
        """[ROBOT] Load project data for blueprint generation.

        Looks up YT Lab project by ID and returns the steps + metadata
        needed by generate_blueprint().
        """
        try:
            from ..services.yt_processor import YTProcessor
            processor = YTProcessor()
            project = processor.get_project(project_id)
            if not project:
                return None

            return {
                "name": project.get("title", project_id),
                "description": project.get("description", ""),
                "steps": project.get("steps", []),
                "video_id": project.get("video_id", ""),
                "video_title": project.get("title", ""),
                "video_channel": project.get("channel", ""),
            }
        except Exception as e:
            logger.warning("Failed to load project data for %s: %s", project_id, e)
            return None

    def get_batch_status(self, batch_id: str) -> Optional[BatchStatus]:
        """[ROBOT] Returns current progress of a running batch."""
        return _batches.get(batch_id)

    def cancel_batch(self, batch_id: str) -> bool:
        """[ROBOT] Sets cancel flag. Current tool finishes but no more start."""
        if batch_id not in _batches:
            return False
        self._cancel_flags[batch_id] = True
        return True
