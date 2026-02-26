"""
Agent OS Intake Dock
=====================

Backend for the file staging area. Handles file upload, storage,
auto-detection of file types, tagging, and distribution to proper
directories when processing.
"""

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

# Keyword lists for auto-detection of file categories
DETECTION_KEYWORDS: dict[str, list[str]] = {
    "standards": [
        "coding conventions", "style guide", "architecture pattern",
        "naming convention", "file organization", "design system",
        "component library", "linter", "formatter",
    ],
    "product": [
        "vision", "target user", "use case", "roadmap", "problem we solve",
        "competitive", "constraint", "success criteria", "mvp",
    ],
    "spec": [
        "requirement", "acceptance criteria", "user story", "as a user",
        "endpoint", "data model", "api spec", "feature spec",
    ],
    "reference": [
        "competitor", "research", "analysis", "reference", "benchmark",
        "comparison", "case study", "example",
    ],
}

VALID_TAGS = {"standards", "product", "spec", "reference", "intake"}

# Where each tag's files get distributed during processing
TAG_DESTINATIONS: dict[str, str] = {
    "standards": "agent-os/standards",
    "product": ".agent/product",
    "spec": ".agent/specs",
    "reference": ".agent/knowledge",
    "intake": ".agent/intake",
}


class AgentOSIntakeDock:
    """
    File staging area for Agent OS project intake.

    Manages upload, auto-detection, tagging, and distribution of
    user-provided files into the appropriate Agent OS directories.
    """

    def __init__(self, project_dir: Path, file_utils: Any = None):
        self.project_dir = project_dir
        self.file_utils = file_utils
        self.staging_dir = project_dir / ".agent" / "intake_staging"
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self._manifest_path = self.staging_dir / "manifest.json"
        self._manifest: list[dict[str, Any]] = self._load_manifest()

    # ========================================================================
    # Public API
    # ========================================================================

    def stage_file(
        self, filename: str, content: bytes, mime_type: str = ""
    ) -> dict[str, Any]:
        """Save a file to the staging directory with a UUID. Returns StagedFile dict."""
        file_id = str(uuid4())
        safe_name = Path(filename).name  # strip any directory traversal
        dest = self.staging_dir / f"{file_id}_{safe_name}"
        dest.write_bytes(content)

        # Attempt auto-detection on text content
        auto_tag: Optional[str] = None
        try:
            text = content.decode("utf-8", errors="ignore")
            auto_tag = self.auto_detect_tag(safe_name, text)
        except Exception:
            pass

        entry: dict[str, Any] = {
            "id": file_id,
            "name": safe_name,
            "size": len(content),
            "type": mime_type or "application/octet-stream",
            "tag": None,
            "auto_tag": auto_tag,
            "processed": False,
            "destination_path": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._manifest.append(entry)
        self._save_manifest()
        logger.info("Staged file %s (%s) as %s", safe_name, file_id, auto_tag or "untagged")
        return entry

    def stage_text(self, filename: str, text: str) -> dict[str, Any]:
        """Create a .md file from pasted text and stage it."""
        if not filename.endswith(".md"):
            filename = filename + ".md"
        return self.stage_file(filename, text.encode("utf-8"), "text/markdown")

    def auto_detect_tag(self, filename: str, content: str) -> Optional[str]:
        """Content-based tag suggestion using keyword matching."""
        lower = content.lower()
        scores: dict[str, int] = {}

        for tag, keywords in DETECTION_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in lower)
            if score > 0:
                scores[tag] = score

        if scores:
            return max(scores, key=scores.get)  # type: ignore[arg-type]

        # No keyword match — default to intake
        return "intake"

    def tag_file(self, file_id: str, tag: str) -> Optional[dict[str, Any]]:
        """Set the tag for a staged file. Returns updated entry or None."""
        if tag not in VALID_TAGS:
            return None

        for entry in self._manifest:
            if entry["id"] == file_id:
                entry["tag"] = tag
                self._save_manifest()
                return entry
        return None

    def remove_file(self, file_id: str) -> bool:
        """Remove a file from staging and manifest."""
        for i, entry in enumerate(self._manifest):
            if entry["id"] == file_id:
                # Remove the physical file
                pattern = f"{file_id}_*"
                for f in self.staging_dir.glob(pattern):
                    f.unlink(missing_ok=True)
                self._manifest.pop(i)
                self._save_manifest()
                return True
        return False

    def get_staged_files(self) -> list[dict[str, Any]]:
        """Return all staged files from manifest."""
        return list(self._manifest)

    def get_readiness(self) -> dict[str, Any]:
        """Return readiness status per category + overall can_proceed."""
        counts: dict[str, int] = {tag: 0 for tag in VALID_TAGS}
        untagged = 0

        for entry in self._manifest:
            if entry.get("processed"):
                continue
            tag = entry.get("tag")
            if tag and tag in counts:
                counts[tag] += 1
            else:
                untagged += 1

        result: dict[str, Any] = {}
        for tag in VALID_TAGS:
            result[tag] = {
                "count": counts[tag],
                "ready": counts[tag] > 0,
            }

        # Can proceed if there is at least one product or intake file
        can_proceed = counts["product"] > 0 or counts["intake"] > 0
        result["untagged"] = untagged
        result["can_proceed"] = can_proceed and untagged == 0
        return result

    def process_files(self) -> dict[str, Any]:
        """Distribute tagged files to proper directories. Mark as processed."""
        processed_count = 0
        destinations: dict[str, list[str]] = {}

        for entry in self._manifest:
            if entry.get("processed"):
                continue

            tag = entry.get("tag")
            if not tag or tag not in TAG_DESTINATIONS:
                continue

            # Resolve destination directory
            dest_rel = TAG_DESTINATIONS[tag]
            dest_dir = self.project_dir / dest_rel
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Find the staged file
            source_files = list(self.staging_dir.glob(f"{entry['id']}_*"))
            if not source_files:
                logger.warning("Staged file %s not found on disk", entry["id"])
                continue

            source = source_files[0]
            dest_path = dest_dir / entry["name"]
            shutil.copy2(str(source), str(dest_path))

            entry["processed"] = True
            entry["destination_path"] = str(dest_path.relative_to(self.project_dir))
            processed_count += 1
            destinations.setdefault(tag, []).append(entry["name"])

        self._save_manifest()
        logger.info("Processed %d files across %d categories", processed_count, len(destinations))
        return {"processed": processed_count, "destinations": destinations}

    # ========================================================================
    # Internal
    # ========================================================================

    def _load_manifest(self) -> list[dict[str, Any]]:
        """Load manifest.json from staging dir. Returns empty list if not found."""
        if self._manifest_path.is_file():
            try:
                return json.loads(self._manifest_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load intake manifest: %s", e)
        return []

    def _save_manifest(self) -> None:
        """Save manifest to staging dir."""
        self._manifest_path.write_text(
            json.dumps(self._manifest, indent=2, default=str),
            encoding="utf-8",
        )
