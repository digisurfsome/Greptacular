"""Component Registry — tracks available execution components for tool readiness checks.

Each component represents a capability the system can use when executing tool steps
(e.g., Claude API access, Playwright browser automation, Google Sheets deployment).

The registry auto-detects availability on startup and persists state to JSON.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

REGISTRY_PATH = Path.home() / ".autoforge" / "component_registry.json"


class ComponentStatus(str, Enum):
    AVAILABLE = "available"
    NOT_BUILT = "not_built"
    AVAILABLE_IF_CONFIGURED = "available_if_configured"


class ComponentType(str, Enum):
    API = "api"
    BROWSER = "browser"
    OUTPUT = "output"
    EXECUTION = "execution"
    COMMUNICATION = "communication"


class ComponentDefinition(BaseModel):
    """A single capability component in the registry."""
    name: str
    component_type: ComponentType
    description: str
    handles: list[str] = Field(default_factory=list, description="Keywords this component handles")
    requirements: list[str] = Field(default_factory=list, description="What's needed for this component")
    status: ComponentStatus = ComponentStatus.NOT_BUILT
    status_detail: str = ""


class ComponentMatch(BaseModel):
    """Result of matching a step to a component."""
    component_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    matched_keywords: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Default component definitions
# ---------------------------------------------------------------------------

_DEFAULT_COMPONENTS: list[dict] = [
    {
        "name": "claude_api",
        "component_type": "api",
        "description": "Claude AI model access for text generation, analysis, and reasoning",
        "handles": [
            "claude", "anthropic", "ai generate", "ai write", "ai analyze",
            "generate text", "write content", "analyze", "research", "summarize",
            "create content", "draft", "brainstorm", "evaluate",
        ],
        "requirements": ["Claude CLI or ANTHROPIC_API_KEY"],
    },
    {
        "name": "openai_api",
        "component_type": "api",
        "description": "OpenAI GPT models for text generation and DALL-E for images",
        "handles": [
            "openai", "gpt", "chatgpt", "dall-e", "whisper",
            "gpt-4", "gpt-3", "image generation",
        ],
        "requirements": ["OPENAI_API_KEY environment variable"],
    },
    {
        "name": "google_sheets_deploy",
        "component_type": "output",
        "description": "Deploy tools as interactive Google Sheets",
        "handles": [
            "google sheet", "spreadsheet", "deploy to sheet",
            "google docs", "sheets api",
        ],
        "requirements": ["Google OAuth credentials", "google-api-python-client"],
    },
    {
        "name": "playwright_browser",
        "component_type": "browser",
        "description": "Browser automation for web scraping and interaction",
        "handles": [
            "browser", "playwright", "web scrape", "screenshot",
            "navigate to", "click", "fill form", "web page",
            "scrape", "crawl", "extract from website",
        ],
        "requirements": ["playwright Python package", "Browser binaries installed"],
    },
    {
        "name": "computer_use",
        "component_type": "browser",
        "description": "Claude Computer Use for GUI interaction and screen reading",
        "handles": [
            "computer use", "screen", "gui", "desktop",
            "click button", "type text", "mouse",
        ],
        "requirements": ["Claude Computer Use API access"],
    },
    {
        "name": "webhook_output",
        "component_type": "output",
        "description": "Send results to external webhooks (Zapier, Make, custom)",
        "handles": [
            "webhook", "zapier", "make.com", "integromat",
            "send to", "post to", "notify", "trigger",
        ],
        "requirements": ["Target webhook URL"],
    },
    {
        "name": "file_creation",
        "component_type": "output",
        "description": "Create and save files locally (CSV, JSON, Markdown, etc.)",
        "handles": [
            "save file", "create file", "export csv", "export json",
            "download", "write to file", "save as", "output file",
        ],
        "requirements": ["Write access to output directory"],
    },
    {
        "name": "cli_execution",
        "component_type": "execution",
        "description": "Execute CLI commands and scripts",
        "handles": [
            "run command", "execute script", "cli", "terminal",
            "bash", "shell", "command line", "npm", "python script",
        ],
        "requirements": ["Allowed commands in security.py"],
    },
    {
        "name": "email_send",
        "component_type": "communication",
        "description": "Send emails via SendGrid, SMTP, or other providers",
        "handles": [
            "send email", "email", "sendgrid", "smtp",
            "mail", "newsletter", "cold email", "instantly",
        ],
        "requirements": ["Email service API key (SendGrid, etc.)"],
    },
    {
        "name": "web_search",
        "component_type": "api",
        "description": "Search the web for information",
        "handles": [
            "search", "google search", "web search", "find online",
            "look up", "search for", "research online",
        ],
        "requirements": ["Search API access or Claude with web search"],
    },
]


def _detect_component_status(comp: dict) -> tuple[ComponentStatus, str]:
    """Auto-detect whether a component is available based on environment."""
    name = comp["name"]

    if name == "claude_api":
        # Check for Claude CLI or credentials
        has_cli = shutil.which("claude") is not None
        has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
        creds_path = Path.home() / ".claude" / ".credentials.json"
        has_creds = creds_path.exists()
        if has_cli or has_key or has_creds:
            return ComponentStatus.AVAILABLE, "Claude CLI detected"
        return ComponentStatus.AVAILABLE_IF_CONFIGURED, "Install Claude CLI or set ANTHROPIC_API_KEY"

    if name == "openai_api":
        if os.environ.get("OPENAI_API_KEY"):
            return ComponentStatus.AVAILABLE, "OPENAI_API_KEY set"
        return ComponentStatus.AVAILABLE_IF_CONFIGURED, "Set OPENAI_API_KEY environment variable"

    if name == "google_sheets_deploy":
        token_path = Path.home() / ".autoforge" / "google_token.json"
        if token_path.exists():
            return ComponentStatus.AVAILABLE, "Google OAuth token found"
        return ComponentStatus.AVAILABLE_IF_CONFIGURED, "Connect Google account via Tool Factory"

    if name == "playwright_browser":
        try:
            import playwright  # noqa: F401
            return ComponentStatus.AVAILABLE, "playwright package installed"
        except ImportError:
            return ComponentStatus.NOT_BUILT, "Install playwright: pip install playwright && playwright install"

    if name == "computer_use":
        # Computer Use requires specific API access — mark as not built for now
        return ComponentStatus.NOT_BUILT, "Computer Use agent not yet integrated into tool execution"

    if name == "webhook_output":
        return ComponentStatus.AVAILABLE, "Webhook sending is built-in (HTTP POST)"

    if name == "file_creation":
        return ComponentStatus.AVAILABLE, "File I/O is always available"

    if name == "cli_execution":
        return ComponentStatus.AVAILABLE, "CLI execution available via security.py allowlist"

    if name == "email_send":
        if os.environ.get("SENDGRID_API_KEY"):
            return ComponentStatus.AVAILABLE, "SENDGRID_API_KEY set"
        if os.environ.get("INSTANTLY_API_KEY"):
            return ComponentStatus.AVAILABLE, "INSTANTLY_API_KEY set"
        return ComponentStatus.AVAILABLE_IF_CONFIGURED, "Set SENDGRID_API_KEY or configure email provider"

    if name == "web_search":
        # Web search is available through Claude's built-in capability
        has_cli = shutil.which("claude") is not None
        if has_cli:
            return ComponentStatus.AVAILABLE, "Available via Claude CLI web search"
        return ComponentStatus.AVAILABLE_IF_CONFIGURED, "Requires Claude CLI with web search"

    return ComponentStatus.NOT_BUILT, "Unknown component"


class ComponentRegistry:
    """Manages the component registry with auto-detection and persistence."""

    def __init__(self) -> None:
        self._components: dict[str, ComponentDefinition] = {}
        self._load_or_initialize()

    def _load_or_initialize(self) -> None:
        """Load from disk or initialize with defaults and auto-detect."""
        if REGISTRY_PATH.exists():
            try:
                data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
                for item in data.get("components", []):
                    comp = ComponentDefinition(**item)
                    self._components[comp.name] = comp
                logger.info("Loaded %d components from registry", len(self._components))
            except Exception as e:
                logger.warning("Failed to load component registry, reinitializing: %s", e)
                self._initialize_defaults()
        else:
            self._initialize_defaults()

        # Always re-detect status on startup
        self._detect_all()
        self._save()

    def _initialize_defaults(self) -> None:
        """Set up default component definitions."""
        for comp_data in _DEFAULT_COMPONENTS:
            status, detail = _detect_component_status(comp_data)
            comp = ComponentDefinition(
                name=comp_data["name"],
                component_type=ComponentType(comp_data["component_type"]),
                description=comp_data["description"],
                handles=comp_data["handles"],
                requirements=comp_data["requirements"],
                status=status,
                status_detail=detail,
            )
            self._components[comp.name] = comp

    def _detect_all(self) -> None:
        """Re-detect availability of all components."""
        defaults_map = {c["name"]: c for c in _DEFAULT_COMPONENTS}
        for name, comp in self._components.items():
            if name in defaults_map:
                status, detail = _detect_component_status(defaults_map[name])
                comp.status = status
                comp.status_detail = detail

    def _save(self) -> None:
        """Persist to disk."""
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {"components": [c.model_dump() for c in self._components.values()]}
        REGISTRY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_all(self) -> list[ComponentDefinition]:
        """Return all components."""
        return list(self._components.values())

    def get_available(self) -> list[ComponentDefinition]:
        """Return only available components."""
        return [c for c in self._components.values() if c.status == ComponentStatus.AVAILABLE]

    def get_by_name(self, name: str) -> Optional[ComponentDefinition]:
        """Get a component by name."""
        return self._components.get(name)

    def match_step(self, step_text: str) -> list[ComponentMatch]:
        """Match step text against component keywords. Returns matches sorted by confidence."""
        lower = step_text.lower()
        matches: list[ComponentMatch] = []

        for comp in self._components.values():
            matched_kw: list[str] = []
            for kw in comp.handles:
                if kw in lower:
                    matched_kw.append(kw)

            if matched_kw:
                # Confidence based on how many keywords matched relative to total
                confidence = min(1.0, len(matched_kw) / max(len(comp.handles) * 0.3, 1))
                matches.append(ComponentMatch(
                    component_name=comp.name,
                    confidence=round(confidence, 2),
                    matched_keywords=matched_kw,
                ))

        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches

    def refresh(self) -> None:
        """Re-detect all components and save."""
        self._detect_all()
        self._save()


# Singleton
_registry: Optional[ComponentRegistry] = None


def get_component_registry() -> ComponentRegistry:
    """Get or create the singleton component registry."""
    global _registry
    if _registry is None:
        _registry = ComponentRegistry()
    return _registry
