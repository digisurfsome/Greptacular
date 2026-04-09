"""
API Routers
===========

FastAPI routers for different API endpoints.
"""

from .actions import commits_router
from .actions import router as actions_router
from .agent import router as agent_router
from .agent_os import router as agent_os_router
from .approvals import router as approvals_router
from .assistant_chat import router as assistant_chat_router
from .captures import router as captures_router
from .checkpoints import router as checkpoints_router
from .ci_status import router as ci_status_router
from .cli_scripter import router as cli_scripter_router
from .design_guide import router as design_guide_router
from .devserver import router as devserver_router
from .dunkstack import router as dunkstack_router
from .execution import execution_websocket
from .execution import router as execution_router
from .expand_project import router as expand_project_router
from .factory import presets_router as factory_presets_router
from .factory import router as factory_router
from .features import router as features_router
from .filesystem import router as filesystem_router
from .github import router as github_router
from .ingestion_sequences import router as ingestion_sequences_router
from .meta_training import router as meta_training_router
from .notifications import router as notifications_router
from .pipeline import router as pipeline_router
from .pipeline_chat import router as pipeline_chat_router
from .pipeline_proxy import router as pipeline_proxy_router
from .prd_shredder import router as prd_shredder_router
from .projects import boilerplate_router, styles_router
from .projects import router as projects_router
from .role_library import router as role_library_router
from .schedules import router as schedules_router
from .seo_tools import router as seo_tools_router
from .settings import router as settings_router
from .spec_creation import router as spec_creation_router
from .swarm import router as swarm_router
from .terminal import router as terminal_router
from .token_budget import router as token_budget_router
from .tool_analyzer import router as tool_analyzer_router
from .tool_factory import router as tool_factory_router
from .tool_runner import router as tool_runner_router
from .tool_themes import router as tool_themes_router
from .verifications import router as verifications_router
from .workspace import router as workspace_router
from .yt_batch import router as yt_batch_router
from .yt_ingestion import router as yt_ingestion_router
from .market_scraper import router as market_scraper_router
from .yt_processing import router as yt_processing_router
from .pipeline_proxy import router as pipeline_proxy_router

__all__ = [
    "actions_router",
    "approvals_router",
    "cli_scripter_router",
    "checkpoints_router",
    "commits_router",
    "ci_status_router",
    "projects_router",
    "features_router",
    "agent_router",
    "schedules_router",
    "devserver_router",
    "design_guide_router",
    "spec_creation_router",
    "expand_project_router",
    "filesystem_router",
    "github_router",
    "assistant_chat_router",
    "settings_router",
    "terminal_router",
    "boilerplate_router",
    "styles_router",
    "workspace_router",
    "notifications_router",
    "role_library_router",
    "seo_tools_router",
    "swarm_router",
    "dunkstack_router",
    "agent_os_router",
    "yt_ingestion_router",
    "yt_processing_router",
    "captures_router",
    "yt_batch_router",
    "execution_router",
    "execution_websocket",
    "token_budget_router",
    "pipeline_chat_router",
    "pipeline_router",
    "pipeline_proxy_router",
    "prd_shredder_router",
    "tool_analyzer_router",
    "tool_factory_router",
    "tool_runner_router",
    "factory_router",
    "factory_presets_router",
    "verifications_router",
    "tool_themes_router",
    "ingestion_sequences_router",
    "market_scraper_router",
    "meta_training_router",
    "pipeline_proxy_router",
]
