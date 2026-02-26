"""
Agent OS Intake Processing
==========================

Classifies raw user input (ideas, rants, formal specs, reference docs)
and extracts structured entities (product name, target users, features,
constraints) for downstream processing.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Input classification types
INPUT_TYPES = [
    "casual_description",   # "I want to build a task app"
    "formal_spec",          # Structured PRD or spec document
    "reference_material",   # Competitor analysis, research, etc.
    "rant",                 # Stream-of-consciousness about the problem
    "mixed",                # Combination of the above
]

# Entity types we extract
ENTITY_SCHEMA: dict[str, type] = {
    "product_name": str,
    "product_description": str,
    "target_users": list,
    "core_features": list,
    "constraints": list,
    "tech_preferences": list,
    "problem_statement": str,
    "competitive_refs": list,
}

# Fields that block product discovery if missing
_BLOCKING_FIELDS = {"product_description", "problem_statement"}

# Fields that improve quality if present
_IMPORTANT_FIELDS = {"target_users", "core_features"}

# ── Prompt templates ─────────────────────────────────────────────────

CLASSIFICATION_PROMPT = """Analyze the following user input and classify its type.

User input:
---
{user_input}
---

Classify as one of: casual_description, formal_spec, reference_material, rant, mixed

Return ONLY valid JSON:
{{"type": "<classification>", "confidence": <0.0-1.0>, "reasoning": "<brief explanation>"}}
"""

EXTRACTION_PROMPT = """Extract structured entities from the following user input about a software project.

User input:
---
{user_input}
---

Extract as many of these fields as you can find (leave empty array [] or empty string "" for fields not mentioned):

Return ONLY valid JSON:
{{
  "product_name": "<name or empty string if not mentioned>",
  "product_description": "<1-2 sentence summary>",
  "target_users": ["<user type 1>", "<user type 2>"],
  "core_features": ["<feature idea 1>", "<feature idea 2>"],
  "constraints": ["<constraint 1>", "<constraint 2>"],
  "tech_preferences": ["<technology 1>", "<technology 2>"],
  "problem_statement": "<what problem this solves>",
  "competitive_refs": ["<competitor or alternative 1>"]
}}
"""


def _is_non_empty(value: Any) -> bool:
    """Check whether an entity value is meaningfully non-empty."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len(value) > 0
    return bool(value)


class AgentOSIntake:
    """Classifies user input and extracts structured entities for product discovery."""

    def __init__(self) -> None:
        self._classification: Optional[str] = None
        self._entities: dict[str, Any] = {}
        self._gaps: list[dict[str, str]] = []
        self._raw_inputs: list[str] = []

    # ── Prompt generation ────────────────────────────────────────────

    def get_classification_prompt(self, user_input: str) -> str:
        """Return the prompt string for Claude to classify the input."""
        return CLASSIFICATION_PROMPT.format(user_input=user_input)

    def get_extraction_prompt(self, user_input: str) -> str:
        """Return the prompt string for Claude to extract entities."""
        return EXTRACTION_PROMPT.format(user_input=user_input)

    # ── Processing Claude responses ──────────────────────────────────

    def process_classification(self, classification_json: dict[str, Any]) -> None:
        """Store the classification result from Claude."""
        input_type = classification_json.get("type", "mixed")
        if input_type in INPUT_TYPES:
            self._classification = input_type
        else:
            self._classification = "mixed"
        logger.debug("Input classified as: %s", self._classification)

    def process_extraction(self, entities_json: dict[str, Any]) -> None:
        """Store extracted entities, merging with any previously extracted ones."""
        for key, expected_type in ENTITY_SCHEMA.items():
            new_val = entities_json.get(key)
            if new_val is None:
                continue

            existing = self._entities.get(key)

            # For list fields: extend (deduplicate)
            if expected_type is list:
                if isinstance(new_val, list) and new_val:
                    prev = existing if isinstance(existing, list) else []
                    merged = list(dict.fromkeys(prev + new_val))  # Preserve order, dedup
                    self._entities[key] = merged
            # For string fields: overwrite if new value is non-empty
            elif expected_type is str:
                if isinstance(new_val, str) and new_val.strip():
                    self._entities[key] = new_val.strip()

        logger.debug("Entities updated: %d fields populated", sum(1 for v in self._entities.values() if _is_non_empty(v)))

    # ── Gap detection ────────────────────────────────────────────────

    def detect_gaps(self) -> list[dict[str, str]]:
        """Analyze entities for gaps. Returns list of gap dicts with severity."""
        gaps: list[dict[str, str]] = []

        for field in ENTITY_SCHEMA:
            value = self._entities.get(field)
            if _is_non_empty(value):
                continue

            if field in _BLOCKING_FIELDS:
                severity = "blocking"
            elif field in _IMPORTANT_FIELDS:
                severity = "important"
            else:
                severity = "minor"

            label = field.replace("_", " ").title()
            gaps.append({
                "field": field,
                "severity": severity,
                "message": f"No {label.lower()} identified",
            })

        self._gaps = gaps
        return gaps

    # ── Input accumulation ───────────────────────────────────────────

    def add_input(self, user_input: str) -> None:
        """Append raw user input for later processing."""
        self._raw_inputs.append(user_input)

    def get_all_input(self) -> str:
        """Return all raw inputs concatenated with newlines."""
        return "\n".join(self._raw_inputs)

    # ── Accessors ────────────────────────────────────────────────────

    def get_entities(self) -> dict[str, Any]:
        """Return the current extracted entities."""
        return dict(self._entities)

    def get_classification(self) -> Optional[str]:
        """Return the input type classification."""
        return self._classification

    def has_minimum_input(self) -> bool:
        """Return True if enough entities exist to proceed to product discovery."""
        return (
            _is_non_empty(self._entities.get("product_description"))
            or _is_non_empty(self._entities.get("problem_statement"))
        )
