"""
API Routers
===========

FastAPI routers for different API endpoints.
"""

from .agent import router as agent_router
from .assistant_chat import router as assistant_chat_router
from .design_guide import router as design_guide_router
from .devserver import router as devserver_router
from .expand_project import router as expand_project_router
from .features import router as features_router
from .filesystem import router as filesystem_router
from .projects import boilerplate_router, styles_router
from .projects import router as projects_router
from .schedules import router as schedules_router
from .settings import router as settings_router
from .spec_creation import router as spec_creation_router
from .terminal import router as terminal_router
from .workspace import router as workspace_router

__all__ = [
    "projects_router",
    "features_router",
    "agent_router",
    "schedules_router",
    "devserver_router",
    "design_guide_router",
    "spec_creation_router",
    "expand_project_router",
    "filesystem_router",
    "assistant_chat_router",
    "settings_router",
    "terminal_router",
    "boilerplate_router",
    "styles_router",
    "workspace_router",
]
