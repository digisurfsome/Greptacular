"""File creation adapter — writes AI-generated content to disk."""

from __future__ import annotations

import logging
from pathlib import Path

from .base import APIAdapter, register_adapter

logger = logging.getLogger(__name__)

# Map expected_output keywords to file extensions
_FORMAT_MAP = {
    "html": ".html",
    "css": ".css",
    "markdown": ".md",
    "csv": ".csv",
    "json": ".json",
    "yaml": ".yaml",
    "yml": ".yml",
    "pdf": ".pdf",  # PDF requires additional rendering
    "txt": ".txt",
    "text": ".txt",
}


def _detect_extension(expected_output: str, content: str) -> str:
    lower = expected_output.lower()
    for keyword, ext in _FORMAT_MAP.items():
        if keyword in lower:
            return ext
    # Sniff content
    stripped = content.strip()
    if stripped.startswith("<!DOCTYPE") or stripped.startswith("<html"):
        return ".html"
    if stripped.startswith("{") or stripped.startswith("["):
        return ".json"
    return ".txt"


class FileCreatorAdapter(APIAdapter):
    """Creates a file on disk from AI-generated content.

    Writes to ~/.autoforge/tool_outputs/ by default.
    """

    def __init__(self, api_key: str = "", variables: dict | None = None, **kwargs: object) -> None:
        super().__init__(api_key=api_key)
        self.variables = variables or {}

    async def execute(self, action: str, payload: dict) -> dict:
        content = payload.get("content", "")
        expected_output = payload.get("expected_output", "")
        title = payload.get("title", "output")

        if not content:
            return {"output": "", "error": "No content to write"}

        ext = _detect_extension(expected_output, content)

        # Sanitize filename
        safe_title = "".join(c if c.isalnum() or c in "-_ " else "_" for c in title)[:60].strip()
        filename = f"{safe_title}{ext}"

        output_dir = Path.home() / ".autoforge" / "tool_outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename

        # Avoid overwrites
        counter = 1
        while output_path.exists():
            output_path = output_dir / f"{safe_title}_{counter}{ext}"
            counter += 1

        try:
            output_path.write_text(content, encoding="utf-8")
            logger.info("File created: %s", output_path)
            return {
                "output": content,
                "file_path": str(output_path),
                "filename": filename,
                "note": f"Saved to {output_path}",
            }
        except Exception as exc:
            logger.warning("File creation failed: %s", exc)
            return {"output": content, "error": f"File write failed: {exc}"}


register_adapter("file_create", FileCreatorAdapter)
