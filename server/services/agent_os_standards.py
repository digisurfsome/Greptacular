"""
Agent OS Standards Management
==============================

Standards creation via questionnaire, inference from codebase,
validation, and summary generation.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

from .agent_os_file_utils import AgentOSFileUtils

logger = logging.getLogger(__name__)

# ── Questionnaire ────────────────────────────────────────────────────

STANDARDS_QUESTIONS: list[dict[str, Any]] = [
    # ── Technology Stack ─────────────────────────────────────────────
    {
        "id": "tech_languages",
        "category": "Technology Stack",
        "question": "What programming language(s) will this project use?",
        "type": "text",
        "standards_file": "technology-stack.md",
        "section": "Languages",
        "required": True,
    },
    {
        "id": "tech_frontend",
        "category": "Technology Stack",
        "question": "Frontend framework preference?",
        "type": "choice",
        "options": ["React", "Vue", "Svelte", "Next.js", "None", "Other"],
        "standards_file": "technology-stack.md",
        "section": "Frontend",
        "skip_if": lambda answers: (
            "frontend" not in answers.get("tech_languages", "").lower()
            and answers.get("tech_languages", "").lower() not in ["javascript", "typescript"]
        ),
        "required": False,
    },
    {
        "id": "tech_backend",
        "category": "Technology Stack",
        "question": "Backend framework?",
        "type": "choice",
        "options": ["Express", "FastAPI", "Django", "Rails", "None", "Other"],
        "standards_file": "technology-stack.md",
        "section": "Backend",
        "required": False,
    },
    {
        "id": "tech_database",
        "category": "Technology Stack",
        "question": "Database?",
        "type": "choice",
        "options": ["PostgreSQL", "SQLite", "MongoDB", "MySQL", "None yet", "Other"],
        "standards_file": "technology-stack.md",
        "section": "Database",
        "required": False,
    },
    {
        "id": "tech_other",
        "category": "Technology Stack",
        "question": "Any other tools or libraries you always use?",
        "type": "text",
        "standards_file": "technology-stack.md",
        "section": "Other Tools",
        "required": False,
    },
    # ── Coding Style ─────────────────────────────────────────────────
    {
        "id": "style_guide",
        "category": "Coding Style",
        "question": "Do you follow a specific style guide?",
        "type": "choice",
        "options": ["Airbnb", "PEP 8", "Google", "Standard", "Custom", "None"],
        "standards_file": "coding-conventions.md",
        "section": "Style Guide",
        "required": False,
    },
    {
        "id": "style_components",
        "category": "Coding Style",
        "question": "Functional or class-based components?",
        "type": "choice",
        "options": ["Functional", "Class-based", "Mixed", "N/A"],
        "standards_file": "coding-conventions.md",
        "section": "Component Style",
        "skip_if": lambda answers: answers.get("tech_frontend") == "None",
        "required": False,
    },
    {
        "id": "style_file_org",
        "category": "Coding Style",
        "question": "How do you organize files?",
        "type": "choice",
        "options": ["By feature", "By type", "Hybrid", "No preference"],
        "standards_file": "coding-conventions.md",
        "section": "File Organization",
        "required": False,
    },
    {
        "id": "style_naming",
        "category": "Coding Style",
        "question": "Naming conventions?",
        "type": "choice",
        "options": ["camelCase", "snake_case", "kebab-case for files", "Mixed by language convention"],
        "standards_file": "coding-conventions.md",
        "section": "Naming",
        "required": False,
    },
    # ── Quality ──────────────────────────────────────────────────────
    {
        "id": "quality_testing",
        "category": "Quality",
        "question": "Testing requirements?",
        "type": "multi_choice",
        "options": ["Unit tests", "Integration tests", "E2E tests", "None for MVP"],
        "standards_file": "quality-standards.md",
        "section": "Testing",
        "required": False,
    },
    {
        "id": "quality_docs",
        "category": "Quality",
        "question": "Documentation requirements?",
        "type": "multi_choice",
        "options": ["JSDoc/docstrings", "Inline comments", "README per module", "None for MVP"],
        "standards_file": "quality-standards.md",
        "section": "Documentation",
        "required": False,
    },
    # ── UI/UX ────────────────────────────────────────────────────────
    {
        "id": "ui_design_system",
        "category": "UI/UX",
        "question": "Design system or component library?",
        "type": "choice",
        "options": ["Tailwind", "MUI", "Shadcn/ui", "Custom", "None"],
        "standards_file": "ui-ux-standards.md",
        "section": "Design System",
        "skip_if": lambda answers: answers.get("tech_frontend") == "None",
        "required": False,
    },
    {
        "id": "ui_responsive",
        "category": "UI/UX",
        "question": "Mobile responsive required?",
        "type": "choice",
        "options": ["Yes", "No", "Mobile-first"],
        "standards_file": "ui-ux-standards.md",
        "section": "Responsive",
        "skip_if": lambda answers: answers.get("tech_frontend") == "None",
        "required": False,
    },
    # ── Architecture ─────────────────────────────────────────────────
    {
        "id": "arch_api_style",
        "category": "Architecture",
        "question": "API style?",
        "type": "choice",
        "options": ["REST", "GraphQL", "tRPC", "None/Not applicable"],
        "standards_file": "architecture-patterns.md",
        "section": "API Style",
        "required": False,
    },
    {
        "id": "arch_state",
        "category": "Architecture",
        "question": "State management?",
        "type": "choice",
        "options": ["Redux", "Zustand", "Context API", "None", "Other"],
        "standards_file": "architecture-patterns.md",
        "section": "State Management",
        "skip_if": lambda answers: answers.get("tech_frontend") == "None",
        "required": False,
    },
    {
        "id": "arch_auth",
        "category": "Architecture",
        "question": "Authentication pattern?",
        "type": "choice",
        "options": ["JWT", "Sessions", "OAuth", "None", "Other"],
        "standards_file": "architecture-patterns.md",
        "section": "Authentication",
        "required": False,
    },
    {
        "id": "arch_deploy",
        "category": "Architecture",
        "question": "Deployment target?",
        "type": "choice",
        "options": ["Vercel", "AWS", "Self-hosted", "Docker", "Don't know yet"],
        "standards_file": "architecture-patterns.md",
        "section": "Deployment",
        "required": False,
    },
]

# Standards files and their sections (for generation)
_STANDARDS_FILES: dict[str, list[str]] = {
    "technology-stack.md": ["Languages", "Frontend", "Backend", "Database", "Other Tools"],
    "coding-conventions.md": ["Style Guide", "Component Style", "File Organization", "Naming"],
    "quality-standards.md": ["Testing", "Documentation", "Performance"],
    "ui-ux-standards.md": ["Design System", "Responsive", "Accessibility", "Mandatory Patterns"],
    "security-requirements.md": ["Authentication", "Input Validation", "Data Protection"],
    "architecture-patterns.md": ["API Style", "State Management", "Authentication", "Deployment"],
}


def _should_skip(question: dict[str, Any], answers: dict[str, Any]) -> bool:
    """Evaluate whether a question should be skipped based on current answers."""
    skip_fn = question.get("skip_if")
    if skip_fn is None:
        return False
    if callable(skip_fn):
        return bool(skip_fn(answers))
    return False


def _serialize_question(question: dict[str, Any]) -> dict[str, Any]:
    """Return a question dict safe for JSON serialization (strip lambdas)."""
    return {k: v for k, v in question.items() if k != "skip_if"}


class AgentOSStandards:
    """Standards creation via questionnaire, inference, validation, and summary."""

    def __init__(self, project_dir: Path, file_utils: AgentOSFileUtils):
        self.project_dir = project_dir
        self.file_utils = file_utils
        self._answers: dict[str, Any] = {}

    def get_next_question(self) -> Optional[dict[str, Any]]:
        """Return the next unanswered, non-skipped question, or None if done."""
        for q in STANDARDS_QUESTIONS:
            qid = q["id"]
            if qid in self._answers:
                continue
            if _should_skip(q, self._answers):
                continue
            return _serialize_question(q)
        return None

    def process_answer(self, question_id: str, answer: str) -> dict[str, Any]:
        """Store an answer and return status with remaining count."""
        self._answers[question_id] = answer
        remaining = sum(
            1 for q in STANDARDS_QUESTIONS
            if q["id"] not in self._answers and not _should_skip(q, self._answers)
        )
        return {"stored": True, "remaining": remaining}

    def generate_standards_files(self) -> list[Path]:
        """Generate all 6 standards markdown files from accumulated answers."""
        # Build a mapping of standards_file -> {section: answer}
        file_sections: dict[str, dict[str, str]] = {}
        for q in STANDARDS_QUESTIONS:
            qid = q["id"]
            if qid not in self._answers:
                continue
            sf = q["standards_file"]
            section = q["section"]
            if sf not in file_sections:
                file_sections[sf] = {}
            file_sections[sf][section] = self._answers[qid]

        written: list[Path] = []
        for filename, sections in _STANDARDS_FILES.items():
            title = filename.replace(".md", "").replace("-", " ").title()
            lines = [f"# {title}", ""]
            for section in sections:
                lines.append(f"## {section}")
                answer = file_sections.get(filename, {}).get(section)
                if answer:
                    lines.append(answer)
                else:
                    lines.append("[Not yet defined]")
                lines.append("")
            content = "\n".join(lines)
            path = self.file_utils.write_standards_file(filename, content)
            written.append(path)

        logger.info("Generated %d standards files", len(written))
        return written

    def infer_standards_from_codebase(self) -> dict[str, Any]:
        """Scan the project directory to infer standards from existing files."""
        inferred: dict[str, Any] = {}

        # Detect from package.json
        pkg_json = self.project_dir / "package.json"
        if pkg_json.is_file():
            try:
                pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                # Language
                if "typescript" in deps:
                    inferred["tech_languages"] = "TypeScript"
                else:
                    inferred["tech_languages"] = "JavaScript"

                # Frontend framework
                if "react" in deps:
                    if "next" in deps:
                        inferred["tech_frontend"] = "Next.js"
                    else:
                        inferred["tech_frontend"] = "React"
                elif "vue" in deps:
                    inferred["tech_frontend"] = "Vue"
                elif "svelte" in deps:
                    inferred["tech_frontend"] = "Svelte"

                # Backend
                if "express" in deps:
                    inferred["tech_backend"] = "Express"

                # Design system
                if "tailwindcss" in deps:
                    inferred["ui_design_system"] = "Tailwind"
                elif "@mui/material" in deps:
                    inferred["ui_design_system"] = "MUI"

                # State management
                if "redux" in deps or "@reduxjs/toolkit" in deps:
                    inferred["arch_state"] = "Redux"
                elif "zustand" in deps:
                    inferred["arch_state"] = "Zustand"

                # Testing
                test_frameworks = []
                if "jest" in deps or "@jest/core" in deps:
                    test_frameworks.append("Unit tests")
                if "playwright" in deps or "@playwright/test" in deps:
                    test_frameworks.append("E2E tests")
                if test_frameworks:
                    inferred["quality_testing"] = ", ".join(test_frameworks)

                # Linting → style guide
                if "eslint-config-airbnb" in deps:
                    inferred["style_guide"] = "Airbnb"
                elif "@typescript-eslint/eslint-plugin" in deps:
                    inferred["style_guide"] = "Standard"

            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to parse package.json: %s", e)

        # Detect from requirements.txt
        req_txt = self.project_dir / "requirements.txt"
        if req_txt.is_file():
            try:
                reqs = req_txt.read_text(encoding="utf-8").lower()
                if not inferred.get("tech_languages"):
                    inferred["tech_languages"] = "Python"
                if "fastapi" in reqs:
                    inferred["tech_backend"] = "FastAPI"
                elif "django" in reqs:
                    inferred["tech_backend"] = "Django"
                elif "flask" in reqs:
                    inferred["tech_backend"] = "Express"  # closest match from options
                if "sqlalchemy" in reqs:
                    inferred["tech_database"] = "SQLite"
                elif "psycopg" in reqs:
                    inferred["tech_database"] = "PostgreSQL"
                if "ruff" in reqs:
                    inferred["style_guide"] = "PEP 8"
            except OSError as e:
                logger.warning("Failed to read requirements.txt: %s", e)

        # Detect from pyproject.toml
        pyproject = self.project_dir / "pyproject.toml"
        if pyproject.is_file():
            try:
                content = pyproject.read_text(encoding="utf-8").lower()
                if not inferred.get("tech_languages"):
                    inferred["tech_languages"] = "Python"
                if "fastapi" in content:
                    inferred["tech_backend"] = "FastAPI"
                elif "django" in content:
                    inferred["tech_backend"] = "Django"
                if "ruff" in content:
                    inferred["style_guide"] = "PEP 8"
            except OSError as e:
                logger.warning("Failed to read pyproject.toml: %s", e)

        # Detect tsconfig.json → TypeScript
        if (self.project_dir / "tsconfig.json").is_file():
            inferred["tech_languages"] = "TypeScript"

        # Detect Docker
        if (self.project_dir / "Dockerfile").is_file() or (self.project_dir / "docker-compose.yml").is_file():
            inferred["arch_deploy"] = "Docker"

        logger.info("Inferred %d standards from codebase", len(inferred))
        return inferred

    def validate_standards(self) -> list[dict[str, str]]:
        """Check generated standards for internal consistency."""
        issues: list[dict[str, str]] = []

        # Check: frontend-related answers without a frontend framework
        frontend = self._answers.get("tech_frontend")
        if frontend == "None":
            for key in ["style_components", "ui_design_system", "ui_responsive", "arch_state"]:
                if key in self._answers and self._answers[key] not in ("N/A", "None"):
                    q_label = next((q["question"] for q in STANDARDS_QUESTIONS if q["id"] == key), key)
                    issues.append({
                        "severity": "warning",
                        "message": f"'{q_label}' answered as '{self._answers[key]}' but no frontend framework selected",
                        "file": next(
                            (q["standards_file"] for q in STANDARDS_QUESTIONS if q["id"] == key),
                            "unknown",
                        ),
                    })

        # Check: PEP 8 style guide with non-Python language
        lang = self._answers.get("tech_languages", "").lower()
        if self._answers.get("style_guide") == "PEP 8" and "python" not in lang:
            issues.append({
                "severity": "warning",
                "message": "PEP 8 style guide selected but primary language is not Python",
                "file": "coding-conventions.md",
            })

        # Check: Airbnb style guide with non-JS language
        if self._answers.get("style_guide") == "Airbnb" and lang not in ("javascript", "typescript"):
            issues.append({
                "severity": "warning",
                "message": "Airbnb style guide selected but primary language is not JavaScript/TypeScript",
                "file": "coding-conventions.md",
            })

        return issues

    def get_standards_summary(self) -> str:
        """Return a brief text summary of all current standards."""
        lines: list[str] = ["Standards Summary:"]
        has_real_content = False

        for filename in _STANDARDS_FILES:
            content = self.file_utils.read_standards_file(filename)
            title = filename.replace(".md", "").replace("-", " ").title()
            if content and "[Not yet defined]" not in content:
                # Extract first non-header, non-empty line as summary
                for line in content.splitlines():
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#") and stripped != "[Not yet defined]":
                        lines.append(f"- {title}: {stripped[:100]}")
                        has_real_content = True
                        break

        # Fall back to answers if no real file content exists
        if not has_real_content and self._answers:
            lines = ["Standards Summary:"]
            for q in STANDARDS_QUESTIONS:
                if q["id"] in self._answers:
                    lines.append(f"- {q['category']} / {q['section']}: {self._answers[q['id']]}")
        elif not has_real_content:
            for filename in _STANDARDS_FILES:
                title = filename.replace(".md", "").replace("-", " ").title()
                lines.append(f"- {title}: [Not configured]")

        return "\n".join(lines)

    def get_progress(self) -> dict[str, Any]:
        """Return progress through the questionnaire."""
        total = len(STANDARDS_QUESTIONS)
        answered = len(self._answers)
        skipped = sum(
            1 for q in STANDARDS_QUESTIONS
            if q["id"] not in self._answers and _should_skip(q, self._answers)
        )
        remaining = total - answered - skipped

        # Determine current category
        current_category = ""
        for q in STANDARDS_QUESTIONS:
            if q["id"] not in self._answers and not _should_skip(q, self._answers):
                current_category = q["category"]
                break

        return {
            "total_questions": total,
            "answered": answered,
            "skipped": skipped,
            "remaining": remaining,
            "current_category": current_category,
        }
