"""
Agent OS File Utilities
=======================

File I/O for the Agent OS 3-layer context system.
Handles reading, writing, and managing files across:
- Standards layer (agent-os/standards/)
- Product layer (.agent/product/)
- Specs layer (.agent/specs/)
- Intake layer (.agent/intake/)
- Knowledge layer (.agent/knowledge/)
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Layer name to relative path mapping
_LAYER_PATHS: dict[str, str] = {
    "standards": "agent-os/standards",
    "product": ".agent/product",
    "specs": ".agent/specs",
    "intake": ".agent/intake",
    "knowledge": ".agent/knowledge",
}

# All .agent subdirectories to create
_AGENT_SUBDIRS = [
    ".agent/product",
    ".agent/specs",
    ".agent/intake",
    ".agent/knowledge",
    ".agent/progress",
    ".agent/settings",
    ".agent/comms",
    ".agent/output",
    ".agent/analytics",
    ".agent/analytics/reports",
]

# Templates directory (relative to this file)
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "agent-os"


class AgentOSFileUtils:
    """Universal file I/O layer for the Agent OS 3-layer context system."""

    def __init__(self, project_dir: Path, global_standards_dir: Optional[Path] = None):
        self.project_dir = project_dir
        self.global_standards_dir = global_standards_dir or Path.home() / ".autoforge" / "agent-os" / "standards"

    def ensure_agent_os_dirs(self) -> None:
        """Create the full Agent OS directory tree."""
        # Standards at project level
        (self.project_dir / "agent-os" / "standards").mkdir(parents=True, exist_ok=True)

        # All .agent subdirectories
        for subdir in _AGENT_SUBDIRS:
            (self.project_dir / subdir).mkdir(parents=True, exist_ok=True)

        # Copy standards templates if project standards dir is empty
        project_standards = self.project_dir / "agent-os" / "standards"
        if not any(project_standards.iterdir()):
            templates_dir = _TEMPLATES_DIR / "standards"
            if templates_dir.is_dir():
                for tmpl in templates_dir.glob("*.md"):
                    dest = project_standards / tmpl.name
                    dest.write_text(tmpl.read_text(encoding="utf-8"), encoding="utf-8")
                    logger.debug("Copied standards template: %s", tmpl.name)

        # Copy product templates if product dir is empty
        product_dir = self.project_dir / ".agent" / "product"
        if not any(product_dir.iterdir()):
            templates_dir = _TEMPLATES_DIR / "product"
            if templates_dir.is_dir():
                for tmpl in templates_dir.glob("*.md"):
                    dest = product_dir / tmpl.name
                    dest.write_text(tmpl.read_text(encoding="utf-8"), encoding="utf-8")
                    logger.debug("Copied product template: %s", tmpl.name)

        logger.info("Agent OS directories ensured for: %s", self.project_dir)

    # ── Standards layer ──────────────────────────────────────────────

    def read_standards_file(self, filename: str) -> Optional[str]:
        """Read a standards file. Falls back to global if project-level doesn't exist."""
        project_path = self.project_dir / "agent-os" / "standards" / filename
        if project_path.is_file():
            return project_path.read_text(encoding="utf-8")

        global_path = self.global_standards_dir / filename
        if global_path.is_file():
            return global_path.read_text(encoding="utf-8")

        return None

    def write_standards_file(self, filename: str, content: str, location: str = "project") -> Path:
        """Write a standards file to project or global location."""
        if location == "global":
            path = self.global_standards_dir / filename
        else:
            path = self.project_dir / "agent-os" / "standards" / filename

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.debug("Wrote standards file: %s (location=%s)", filename, location)
        return path

    # ── Product layer ────────────────────────────────────────────────

    def read_product_file(self, filename: str) -> Optional[str]:
        """Read a product file from .agent/product/."""
        path = self.project_dir / ".agent" / "product" / filename
        if path.is_file():
            return path.read_text(encoding="utf-8")
        return None

    def write_product_file(self, filename: str, content: str) -> Path:
        """Write a product file to .agent/product/."""
        path = self.project_dir / ".agent" / "product" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.debug("Wrote product file: %s", filename)
        return path

    # ── Specs layer ──────────────────────────────────────────────────

    def read_spec_file(self, filename: str) -> Optional[str]:
        """Read a spec file from .agent/specs/."""
        path = self.project_dir / ".agent" / "specs" / filename
        if path.is_file():
            return path.read_text(encoding="utf-8")
        return None

    def write_spec_file(self, filename: str, content: str) -> Path:
        """Write a spec file to .agent/specs/."""
        path = self.project_dir / ".agent" / "specs" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.debug("Wrote spec file: %s", filename)
        return path

    # ── Generic dispatchers ──────────────────────────────────────────

    def get_layer_path(self, layer: str) -> Path:
        """Return the absolute path for a layer directory."""
        if layer == "standards":
            return self.project_dir / "agent-os" / "standards"
        rel = _LAYER_PATHS.get(layer)
        if rel is None:
            raise ValueError(f"Unknown layer: {layer!r}. Valid: {list(_LAYER_PATHS)}")
        return self.project_dir / rel

    def read_file(self, layer: str, filename: str) -> Optional[str]:
        """Generic read dispatcher by layer name."""
        if layer == "standards":
            return self.read_standards_file(filename)
        if layer == "product":
            return self.read_product_file(filename)
        if layer == "specs":
            return self.read_spec_file(filename)
        # Fallback for intake/knowledge
        path = self.get_layer_path(layer) / filename
        if path.is_file():
            return path.read_text(encoding="utf-8")
        return None

    def write_file(self, layer: str, filename: str, content: str) -> Path:
        """Generic write dispatcher by layer name."""
        if layer == "standards":
            return self.write_standards_file(filename, content)
        if layer == "product":
            return self.write_product_file(filename, content)
        if layer == "specs":
            return self.write_spec_file(filename, content)
        # Fallback for intake/knowledge
        path = self.get_layer_path(layer) / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def list_files_in_layer(self, layer: str) -> list[dict]:
        """List all files in a layer with metadata."""
        results: list[dict] = []

        if layer == "standards":
            # Include both project-level and global files
            seen: set[str] = set()

            project_dir = self.project_dir / "agent-os" / "standards"
            if project_dir.is_dir():
                for f in sorted(project_dir.iterdir()):
                    if f.is_file():
                        stat = f.stat()
                        results.append({
                            "name": f.name,
                            "path": str(f),
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                            "location": "project",
                        })
                        seen.add(f.name)

            if self.global_standards_dir.is_dir():
                for f in sorted(self.global_standards_dir.iterdir()):
                    if f.is_file() and f.name not in seen:
                        stat = f.stat()
                        results.append({
                            "name": f.name,
                            "path": str(f),
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                            "location": "global",
                        })
        else:
            layer_path = self.get_layer_path(layer)
            if layer_path.is_dir():
                for f in sorted(layer_path.iterdir()):
                    if f.is_file():
                        stat = f.stat()
                        results.append({
                            "name": f.name,
                            "path": str(f),
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                        })

        return results

    # ── Existence checks ─────────────────────────────────────────────

    def standards_exist(self) -> bool:
        """Return True if any standards files exist (project or global)."""
        project_dir = self.project_dir / "agent-os" / "standards"
        if project_dir.is_dir() and any(project_dir.iterdir()):
            return True
        if self.global_standards_dir.is_dir() and any(self.global_standards_dir.iterdir()):
            return True
        return False

    def product_exists(self) -> bool:
        """Return True if any product files exist."""
        product_dir = self.project_dir / ".agent" / "product"
        return product_dir.is_dir() and any(product_dir.iterdir())

    def specs_exist(self) -> bool:
        """Return True if any spec files exist."""
        specs_dir = self.project_dir / ".agent" / "specs"
        return specs_dir.is_dir() and any(specs_dir.iterdir())
