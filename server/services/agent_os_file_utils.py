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


def _safe_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal attacks.

    Strips directory components so only the bare filename remains.
    Rejects absolute paths, parent references (..), and empty names.
    """
    # Use PurePosixPath to handle both / and \ separators
    from pathlib import PurePosixPath

    name = PurePosixPath(filename.replace("\\", "/")).name
    if not name or name in (".", ".."):
        raise ValueError(f"Invalid filename: {filename!r}")
    return name


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

# Universal DunkStack template files: (template_relative_path, dest_relative_path)
_UNIVERSAL_TEMPLATES = [
    ("system_prompt.md", "system_prompt.md"),
    ("index.md", "index.md"),
    ("working_memory.md", "working_memory.md"),
    ("bridge.md", "bridge.md"),
    ("comms/to_human.md", "comms/to_human.md"),
    ("comms/from_human.md", "comms/from_human.md"),
    ("comms/control.md", "comms/control.md"),
    ("settings/config.yml", "settings/config.yml"),
    ("progress/build_log.md", "progress/build_log.md"),
]


def copy_universal_templates(agent_dir: Path) -> int:
    """Copy universal DunkStack template files into a project's .agent/ directory.

    Only copies files that don't already exist (never overwrites).
    Returns the number of files copied.
    """
    universal_dir = _TEMPLATES_DIR / "universal"
    if not universal_dir.is_dir():
        logger.warning("Universal templates directory not found: %s", universal_dir)
        return 0

    copied = 0
    for tmpl_rel, dest_rel in _UNIVERSAL_TEMPLATES:
        dest = agent_dir / dest_rel
        if dest.exists():
            continue
        src = universal_dir / tmpl_rel
        if not src.is_file():
            logger.warning("Universal template not found: %s", src)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        copied += 1
        logger.debug("Copied universal template: %s → %s", tmpl_rel, dest)

    if copied:
        logger.info("Copied %d universal DunkStack template(s) to %s", copied, agent_dir)
    return copied


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

        # Copy standards templates if project standards dir has no .md files
        project_standards = self.project_dir / "agent-os" / "standards"
        if not any(project_standards.glob("*.md")):
            templates_dir = _TEMPLATES_DIR / "standards"
            if templates_dir.is_dir():
                for tmpl in templates_dir.glob("*.md"):
                    dest = project_standards / tmpl.name
                    dest.write_text(tmpl.read_text(encoding="utf-8"), encoding="utf-8")
                    logger.debug("Copied standards template: %s", tmpl.name)

        # Copy product templates if product dir has no .md files
        product_dir = self.project_dir / ".agent" / "product"
        if not any(product_dir.glob("*.md")):
            templates_dir = _TEMPLATES_DIR / "product"
            if templates_dir.is_dir():
                for tmpl in templates_dir.glob("*.md"):
                    dest = product_dir / tmpl.name
                    dest.write_text(tmpl.read_text(encoding="utf-8"), encoding="utf-8")
                    logger.debug("Copied product template: %s", tmpl.name)

        # Copy universal DunkStack templates (system_prompt, index, working_memory, etc.)
        copy_universal_templates(self.project_dir / ".agent")

        logger.info("Agent OS directories ensured for: %s", self.project_dir)

    # ── Standards layer ──────────────────────────────────────────────

    def read_standards_file(self, filename: str) -> Optional[str]:
        """Read a standards file. Falls back to global if project-level doesn't exist."""
        safe = _safe_filename(filename)
        project_path = self.project_dir / "agent-os" / "standards" / safe
        if project_path.is_file():
            return project_path.read_text(encoding="utf-8")

        global_path = self.global_standards_dir / safe
        if global_path.is_file():
            return global_path.read_text(encoding="utf-8")

        return None

    def write_standards_file(self, filename: str, content: str, location: str = "project") -> Path:
        """Write a standards file to project or global location."""
        safe = _safe_filename(filename)
        if location == "global":
            path = self.global_standards_dir / safe
        else:
            path = self.project_dir / "agent-os" / "standards" / safe

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.debug("Wrote standards file: %s (location=%s)", safe, location)
        return path

    # ── Product layer ────────────────────────────────────────────────

    def read_product_file(self, filename: str) -> Optional[str]:
        """Read a product file from .agent/product/."""
        safe = _safe_filename(filename)
        path = self.project_dir / ".agent" / "product" / safe
        if path.is_file():
            return path.read_text(encoding="utf-8")
        return None

    def write_product_file(self, filename: str, content: str) -> Path:
        """Write a product file to .agent/product/."""
        safe = _safe_filename(filename)
        path = self.project_dir / ".agent" / "product" / safe
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.debug("Wrote product file: %s", safe)
        return path

    # ── Specs layer ──────────────────────────────────────────────────

    def read_spec_file(self, filename: str) -> Optional[str]:
        """Read a spec file from .agent/specs/."""
        safe = _safe_filename(filename)
        path = self.project_dir / ".agent" / "specs" / safe
        if path.is_file():
            return path.read_text(encoding="utf-8")
        return None

    def write_spec_file(self, filename: str, content: str) -> Path:
        """Write a spec file to .agent/specs/."""
        safe = _safe_filename(filename)
        path = self.project_dir / ".agent" / "specs" / safe
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.debug("Wrote spec file: %s", safe)
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
        safe = _safe_filename(filename)
        path = self.get_layer_path(layer) / safe
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
        safe = _safe_filename(filename)
        path = self.get_layer_path(layer) / safe
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
        """Return True if any standards .md files exist (project or global)."""
        project_dir = self.project_dir / "agent-os" / "standards"
        if project_dir.is_dir() and any(project_dir.glob("*.md")):
            return True
        if self.global_standards_dir.is_dir() and any(self.global_standards_dir.glob("*.md")):
            return True
        return False

    def product_exists(self) -> bool:
        """Return True if any product .md files exist."""
        product_dir = self.project_dir / ".agent" / "product"
        return product_dir.is_dir() and any(product_dir.glob("*.md"))

    def specs_exist(self) -> bool:
        """Return True if any spec .md files exist."""
        specs_dir = self.project_dir / ".agent" / "specs"
        return specs_dir.is_dir() and any(specs_dir.glob("*.md"))
