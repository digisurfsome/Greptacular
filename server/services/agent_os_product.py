"""
Agent OS Product Discovery
===========================

Adaptive question flow that builds the Product layer from user input.
Generates the 6 product documents (vision, target-users, use-cases,
roadmap, constraints, competitive-context).
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .agent_os_file_utils import AgentOSFileUtils

logger = logging.getLogger(__name__)

# ── Question flow ────────────────────────────────────────────────────

PRODUCT_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "vision",
        "question": "In one sentence, what does this product do for the user?",
        "purpose": "Forces clarity on the core value proposition",
        "maps_to_file": "vision.md",
        "maps_to_section": "Core Purpose",
        "skip_if_entity": "product_description",
        "required": True,
    },
    {
        "id": "target_users",
        "question": "Who specifically uses this? Give me a real person or role.",
        "purpose": "Prevents vague 'everyone' answers",
        "maps_to_file": "target-users.md",
        "maps_to_section": "Primary Users",
        "skip_if_entity": "target_users",
        "required": True,
    },
    {
        "id": "core_problem",
        "question": "What's the #1 pain point this solves?",
        "purpose": "Forces prioritization of the core problem",
        "maps_to_file": "vision.md",
        "maps_to_section": "Problem Statement",
        "skip_if_entity": "problem_statement",
        "required": True,
    },
    {
        "id": "competitive_context",
        "question": "What do people use today instead? What's wrong with it?",
        "purpose": "Establishes differentiation",
        "maps_to_file": "competitive-context.md",
        "maps_to_section": "Current Alternatives",
        "skip_if_entity": "competitive_refs",
        "required": False,
    },
    {
        "id": "constraints",
        "question": "Any hard constraints? Budget, timeline, technology, regulatory?",
        "purpose": "Prevents impossible specs",
        "maps_to_file": "constraints.md",
        "maps_to_section": "Hard Constraints",
        "skip_if_entity": "constraints",
        "required": False,
    },
    {
        "id": "success_definition",
        "question": "If this works perfectly, what happens? What does success look like?",
        "purpose": "Establishes acceptance criteria at the product level",
        "maps_to_file": "vision.md",
        "maps_to_section": "Success Definition",
        "skip_if_entity": None,
        "required": True,
    },
]

# The 6 product document specs
_PRODUCT_DOCS: dict[str, dict[str, Any]] = {
    "vision.md": {
        "title": "Product Vision",
        "sections": ["Core Purpose", "Problem Statement", "Success Definition"],
    },
    "target-users.md": {
        "title": "Target Users",
        "sections": ["Primary Users", "User Needs", "User Context"],
    },
    "use-cases.md": {
        "title": "Use Cases",
        "sections": ["Core Use Cases", "Secondary Use Cases"],
    },
    "roadmap.md": {
        "title": "Roadmap",
        "sections": ["MVP Features", "v1.1 Features", "Future"],
    },
    "constraints.md": {
        "title": "Constraints",
        "sections": ["Hard Constraints", "Technical Constraints", "Timeline"],
    },
    "competitive-context.md": {
        "title": "Competitive Context",
        "sections": ["Current Alternatives", "Differentiators", "Opportunities"],
    },
}

# Map of question id → entity key for auto-fill
_ENTITY_MAP: dict[str, str] = {
    "vision": "product_description",
    "target_users": "target_users",
    "core_problem": "problem_statement",
    "competitive_context": "competitive_refs",
    "constraints": "constraints",
}

# ── Document generation prompts ──────────────────────────────────────

_DOC_GENERATION_PROMPT = """Generate the content for a product document called "{doc_title}".

The document has these sections: {sections}

Here is everything we know about this product:

## Extracted Entities
{entities_text}

## User Answers
{answers_text}

{summary_section}

Write the document in clean markdown format. For each section, write substantive content based on what's known.
If information for a section is not available, write "[Needs further discussion]" for that section.

Output ONLY the markdown content (no code fences).
"""

_SUMMARY_PROMPT = """Based on all the information gathered so far, provide a brief "here's what I understand" summary.

## Extracted Entities
{entities_text}

## User Answers
{answers_text}

Summarize in 3-5 sentences what this product is, who it's for, and what makes it unique.
Be direct and specific — avoid filler.
"""


def _entity_to_str(value: Any) -> str:
    """Convert an entity value to a display string."""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else ""
    return str(value) if value else ""


def _is_non_empty_entity(value: Any) -> bool:
    """Check whether an entity value is meaningfully non-empty."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len(value) > 0
    return bool(value)


class AgentOSProduct:
    """Adaptive question flow that builds the Product layer documents."""

    def __init__(self, project_dir: Path, file_utils: AgentOSFileUtils, entities: dict[str, Any]):
        self.project_dir = project_dir
        self.file_utils = file_utils
        self.entities = entities
        self._answers: dict[str, str] = {}
        self._auto_filled: dict[str, str] = {}
        self._summary: str = ""
        self._generated_files: list[str] = []

    # ── Question flow ────────────────────────────────────────────────

    def get_next_question(self) -> Optional[dict[str, Any]]:
        """Return the next unanswered question, skipping where entity exists."""
        for q in PRODUCT_QUESTIONS:
            qid = q["id"]
            if qid in self._answers:
                continue

            # Skip if the entity for this question is already filled
            skip_entity = q.get("skip_if_entity")
            if skip_entity and _is_non_empty_entity(self.entities.get(skip_entity)):
                continue

            return {"id": q["id"], "question": q["question"], "purpose": q["purpose"]}

        return None

    def process_answer(self, question_id: str, answer: str) -> dict[str, Any]:
        """Store an answer. Returns status with remaining count."""
        self._answers[question_id] = answer
        remaining = self._count_remaining()
        return {"stored": True, "remaining": remaining}

    def auto_fill_from_entities(self) -> dict[str, str]:
        """Auto-fill answers from extracted entities. Returns the auto-filled map."""
        filled: dict[str, str] = {}
        for q in PRODUCT_QUESTIONS:
            qid = q["id"]
            if qid in self._answers:
                continue

            skip_entity = q.get("skip_if_entity")
            if skip_entity:
                val = self.entities.get(skip_entity)
                if _is_non_empty_entity(val):
                    display = _entity_to_str(val)
                    self._answers[qid] = display
                    self._auto_filled[qid] = display
                    filled[qid] = display

        return filled

    # ── Summary ──────────────────────────────────────────────────────

    def get_summary_prompt(self) -> str:
        """Return a prompt for Claude to produce a summary of what's known so far."""
        return _SUMMARY_PROMPT.format(
            entities_text=self._format_entities(),
            answers_text=self._format_answers(),
        )

    def process_summary(self, summary: str) -> None:
        """Store the summary for reference in document generation."""
        self._summary = summary

    # ── Document generation ──────────────────────────────────────────

    def get_doc_generation_prompt(self, doc_name: str) -> str:
        """Return a prompt for Claude to generate one product document."""
        doc_spec = _PRODUCT_DOCS.get(doc_name)
        if doc_spec is None:
            raise ValueError(f"Unknown product doc: {doc_name!r}. Valid: {list(_PRODUCT_DOCS)}")

        summary_section = ""
        if self._summary:
            summary_section = f"## Summary So Far\n{self._summary}"

        return _DOC_GENERATION_PROMPT.format(
            doc_title=doc_spec["title"],
            sections=", ".join(doc_spec["sections"]),
            entities_text=self._format_entities(),
            answers_text=self._format_answers(),
            summary_section=summary_section,
        )

    def process_generated_doc(self, doc_name: str, content: str) -> Path:
        """Write Claude's generated content to the product file."""
        path = self.file_utils.write_product_file(doc_name, content)
        if doc_name not in self._generated_files:
            self._generated_files.append(doc_name)
        logger.info("Generated product doc: %s", doc_name)
        return path

    def generate_product_docs(self) -> list[Path]:
        """Generate all 6 product docs from answers + entities (without Claude).

        This creates basic documents from what's directly available. For richer
        content, the caller should use get_doc_generation_prompt() + process_generated_doc()
        to have Claude generate each document.
        """
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        product_name = self.entities.get("product_name", "Unnamed Project")

        written: list[Path] = []

        for doc_name, doc_spec in _PRODUCT_DOCS.items():
            lines = [
                f"# {doc_spec['title']}",
                f"Generated: {timestamp}",
                f"Project: {product_name}",
                "",
            ]

            for section in doc_spec["sections"]:
                lines.append(f"## {section}")
                content = self._get_content_for_section(doc_name, section)
                lines.append(content)
                lines.append("")

            path = self.file_utils.write_product_file(doc_name, "\n".join(lines))
            written.append(path)
            if doc_name not in self._generated_files:
                self._generated_files.append(doc_name)

        logger.info("Generated %d product docs", len(written))
        return written

    # ── Status / accessors ───────────────────────────────────────────

    def get_product_summary(self) -> str:
        """Return a text summary of the current product layer state."""
        parts: list[str] = []

        if self._summary:
            parts.append(self._summary)

        if self.entities.get("product_name"):
            parts.append(f"Product: {self.entities['product_name']}")

        if self.entities.get("product_description"):
            parts.append(f"Description: {self.entities['product_description']}")

        if self._answers:
            parts.append("Key answers:")
            for q in PRODUCT_QUESTIONS:
                if q["id"] in self._answers:
                    parts.append(f"  - {q['question']}: {self._answers[q['id']]}")

        if self._generated_files:
            parts.append(f"Generated docs: {', '.join(self._generated_files)}")

        return "\n".join(parts) if parts else "No product information gathered yet."

    def get_progress(self) -> dict[str, Any]:
        """Return progress through the question flow."""
        total = len(PRODUCT_QUESTIONS)
        auto_filled = len(self._auto_filled)
        answered = len(self._answers)
        remaining = self._count_remaining()
        return {
            "total_questions": total,
            "answered": answered,
            "auto_filled": auto_filled,
            "remaining": remaining,
        }

    # ── Private helpers ──────────────────────────────────────────────

    def _count_remaining(self) -> int:
        """Count questions that are neither answered nor auto-skippable."""
        count = 0
        for q in PRODUCT_QUESTIONS:
            qid = q["id"]
            if qid in self._answers:
                continue
            skip_entity = q.get("skip_if_entity")
            if skip_entity and _is_non_empty_entity(self.entities.get(skip_entity)):
                continue
            count += 1
        return count

    def _format_entities(self) -> str:
        """Format entities for prompt inclusion."""
        lines: list[str] = []
        for key, val in self.entities.items():
            display = _entity_to_str(val)
            if display:
                label = key.replace("_", " ").title()
                lines.append(f"- {label}: {display}")
        return "\n".join(lines) if lines else "(No entities extracted yet)"

    def _format_answers(self) -> str:
        """Format answers for prompt inclusion."""
        lines: list[str] = []
        for q in PRODUCT_QUESTIONS:
            if q["id"] in self._answers:
                lines.append(f"- Q: {q['question']}")
                lines.append(f"  A: {self._answers[q['id']]}")
        return "\n".join(lines) if lines else "(No answers yet)"

    def _get_content_for_section(self, doc_name: str, section: str) -> str:
        """Get the best available content for a document section."""
        # Map sections to answers/entities
        section_sources: dict[str, dict[str, list[str]]] = {
            "vision.md": {
                "Core Purpose": ["vision"],
                "Problem Statement": ["core_problem"],
                "Success Definition": ["success_definition"],
            },
            "target-users.md": {
                "Primary Users": ["target_users"],
                "User Needs": [],
                "User Context": [],
            },
            "use-cases.md": {
                "Core Use Cases": [],
                "Secondary Use Cases": [],
            },
            "roadmap.md": {
                "MVP Features": [],
                "v1.1 Features": [],
                "Future": [],
            },
            "constraints.md": {
                "Hard Constraints": ["constraints"],
                "Technical Constraints": [],
                "Timeline": [],
            },
            "competitive-context.md": {
                "Current Alternatives": ["competitive_context"],
                "Differentiators": [],
                "Opportunities": [],
            },
        }

        # Look up answer keys for this section
        answer_keys = section_sources.get(doc_name, {}).get(section, [])

        # Try answers first
        for key in answer_keys:
            if key in self._answers and self._answers[key].strip():
                return self._answers[key]

        # Try mapped entities
        entity_map_reverse: dict[str, str] = {
            "Core Purpose": "product_description",
            "Problem Statement": "problem_statement",
            "Primary Users": "target_users",
            "Hard Constraints": "constraints",
            "Current Alternatives": "competitive_refs",
            "MVP Features": "core_features",
        }

        entity_key = entity_map_reverse.get(section)
        if entity_key:
            val = self.entities.get(entity_key)
            if _is_non_empty_entity(val):
                return _entity_to_str(val)

        return "[Not yet defined]"
