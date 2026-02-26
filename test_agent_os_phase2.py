"""
Agent OS Phase 2 Tests
======================

Tests for AgentOSIntake and AgentOSProduct.
"""

from pathlib import Path

import pytest

from server.services.agent_os_file_utils import AgentOSFileUtils
from server.services.agent_os_intake import AgentOSIntake
from server.services.agent_os_product import PRODUCT_QUESTIONS, AgentOSProduct

# ── AgentOSIntake ────────────────────────────────────────────────────


class TestIntake:
    def test_classification_prompt_includes_input(self) -> None:
        """get_classification_prompt() includes the user input in the prompt."""
        intake = AgentOSIntake()
        prompt = intake.get_classification_prompt("I want to build a task tracker")
        assert "I want to build a task tracker" in prompt
        assert "casual_description" in prompt  # Contains valid types

    def test_process_classification_stores_type(self) -> None:
        """process_classification() stores the classification."""
        intake = AgentOSIntake()
        intake.process_classification({"type": "casual_description", "confidence": 0.9, "reasoning": "test"})
        assert intake.get_classification() == "casual_description"

    def test_process_classification_defaults_to_mixed(self) -> None:
        """process_classification() defaults to 'mixed' for unknown types."""
        intake = AgentOSIntake()
        intake.process_classification({"type": "unknown_type", "confidence": 0.5})
        assert intake.get_classification() == "mixed"

    def test_extraction_prompt_includes_input(self) -> None:
        """get_extraction_prompt() includes the user input in the prompt."""
        intake = AgentOSIntake()
        prompt = intake.get_extraction_prompt("Build a recipe sharing app for home cooks")
        assert "Build a recipe sharing app for home cooks" in prompt
        assert "product_name" in prompt  # Contains entity schema fields

    def test_process_extraction_stores_entities(self) -> None:
        """process_extraction() stores all entity fields."""
        intake = AgentOSIntake()
        entities = {
            "product_name": "RecipeShare",
            "product_description": "A recipe sharing platform",
            "target_users": ["home cooks", "food bloggers"],
            "core_features": ["recipe upload", "social feed"],
            "constraints": [],
            "tech_preferences": ["React", "Node.js"],
            "problem_statement": "Hard to share recipes with friends",
            "competitive_refs": ["AllRecipes"],
        }
        intake.process_extraction(entities)
        result = intake.get_entities()

        assert result["product_name"] == "RecipeShare"
        assert result["product_description"] == "A recipe sharing platform"
        assert "home cooks" in result["target_users"]
        assert "food bloggers" in result["target_users"]
        assert "recipe upload" in result["core_features"]

    def test_process_extraction_merges_multiple(self) -> None:
        """Multiple calls to process_extraction() merge entities."""
        intake = AgentOSIntake()

        # First extraction
        intake.process_extraction({
            "product_name": "TaskApp",
            "target_users": ["developers"],
            "core_features": ["task creation"],
        })

        # Second extraction (from additional input)
        intake.process_extraction({
            "product_name": "TaskMaster",  # Overwrites string
            "target_users": ["developers", "managers"],  # Extends & deduplicates
            "core_features": ["task creation", "notifications"],  # Extends & deduplicates
        })

        result = intake.get_entities()
        assert result["product_name"] == "TaskMaster"  # Overwritten
        assert "developers" in result["target_users"]
        assert "managers" in result["target_users"]
        assert len(result["target_users"]) == 2  # No duplicates
        assert "task creation" in result["core_features"]
        assert "notifications" in result["core_features"]

    def test_detect_gaps_finds_missing_required(self) -> None:
        """detect_gaps() identifies blocking gaps for missing required fields."""
        intake = AgentOSIntake()
        # No entities at all → should find blocking gaps
        gaps = intake.detect_gaps()
        assert len(gaps) > 0

        blocking = [g for g in gaps if g["severity"] == "blocking"]
        assert len(blocking) > 0

        blocking_fields = [g["field"] for g in blocking]
        assert "product_description" in blocking_fields
        assert "problem_statement" in blocking_fields

    def test_detect_gaps_fewer_with_entities(self) -> None:
        """detect_gaps() finds fewer gaps when entities are populated."""
        intake = AgentOSIntake()
        intake.process_extraction({
            "product_description": "A task management app",
            "problem_statement": "Existing tools are too complex",
            "target_users": ["developers"],
        })
        gaps = intake.detect_gaps()
        blocking = [g for g in gaps if g["severity"] == "blocking"]
        assert len(blocking) == 0  # All blocking fields filled

    def test_has_minimum_input_false_when_empty(self) -> None:
        """has_minimum_input() returns False with no entities."""
        intake = AgentOSIntake()
        assert intake.has_minimum_input() is False

    def test_has_minimum_input_true_with_description(self) -> None:
        """has_minimum_input() returns True with product_description."""
        intake = AgentOSIntake()
        intake.process_extraction({"product_description": "A task management app"})
        assert intake.has_minimum_input() is True

    def test_has_minimum_input_true_with_problem(self) -> None:
        """has_minimum_input() returns True with problem_statement."""
        intake = AgentOSIntake()
        intake.process_extraction({"problem_statement": "People can't organize tasks"})
        assert intake.has_minimum_input() is True

    def test_add_input_concatenates(self) -> None:
        """Multiple add_input() calls are concatenated by get_all_input()."""
        intake = AgentOSIntake()
        intake.add_input("I want to build a task app.")
        intake.add_input("It should have drag and drop.")
        intake.add_input("Target audience is project managers.")

        combined = intake.get_all_input()
        assert "task app" in combined
        assert "drag and drop" in combined
        assert "project managers" in combined
        assert combined.count("\n") == 2  # Three lines, two newlines


# ── AgentOSProduct ───────────────────────────────────────────────────


class TestProduct:
    def _make(self, tmp_path: Path, entities: dict | None = None) -> AgentOSProduct:
        utils = AgentOSFileUtils(tmp_path, global_standards_dir=tmp_path / "global_std")
        return AgentOSProduct(tmp_path, utils, entities or {})

    def test_get_next_question_returns_first(self, tmp_path: Path) -> None:
        """First call returns the first question."""
        product = self._make(tmp_path)
        q = product.get_next_question()
        assert q is not None
        assert q["id"] == "vision"
        assert "question" in q
        assert "purpose" in q

    def test_get_next_question_has_no_internal_keys(self, tmp_path: Path) -> None:
        """Returned question dict only has id, question, purpose."""
        product = self._make(tmp_path)
        q = product.get_next_question()
        assert q is not None
        assert set(q.keys()) == {"id", "question", "purpose"}

    def test_skip_if_entity_skips_answered(self, tmp_path: Path) -> None:
        """Questions are skipped when their entity is already extracted."""
        entities = {
            "product_description": "A task app for developers",
            "target_users": ["developers", "PMs"],
            "problem_statement": "Hard to manage tasks",
        }
        product = self._make(tmp_path, entities)

        # Collect all question IDs that come up
        seen_ids: list[str] = []
        while True:
            q = product.get_next_question()
            if q is None:
                break
            seen_ids.append(q["id"])
            product.process_answer(q["id"], "test answer")

        # vision, target_users, and core_problem should be skipped
        assert "vision" not in seen_ids
        assert "target_users" not in seen_ids
        assert "core_problem" not in seen_ids
        # success_definition should always appear (skip_if_entity is None)
        assert "success_definition" in seen_ids

    def test_auto_fill_from_entities(self, tmp_path: Path) -> None:
        """auto_fill_from_entities() fills answers from extracted entities."""
        entities = {
            "product_description": "A recipe sharing platform",
            "target_users": ["home cooks", "food bloggers"],
            "problem_statement": "Hard to share recipes",
        }
        product = self._make(tmp_path, entities)
        filled = product.auto_fill_from_entities()

        assert "vision" in filled
        assert "A recipe sharing platform" in filled["vision"]
        assert "target_users" in filled
        assert "core_problem" in filled

    def test_process_answer_stores(self, tmp_path: Path) -> None:
        """process_answer() stores the answer and returns remaining count."""
        product = self._make(tmp_path)
        result = product.process_answer("vision", "It helps people manage tasks efficiently")
        assert result["stored"] is True
        assert isinstance(result["remaining"], int)
        assert result["remaining"] < len(PRODUCT_QUESTIONS)

    def test_generate_product_docs_creates_files(self, tmp_path: Path) -> None:
        """generate_product_docs() creates all 6 files in .agent/product/."""
        entities = {
            "product_name": "TaskMaster",
            "product_description": "A task management tool",
            "target_users": ["developers"],
            "core_features": ["task boards", "notifications"],
            "problem_statement": "Existing tools are bloated",
        }
        product = self._make(tmp_path, entities)
        product.process_answer("success_definition", "Users complete 90% of their tasks")

        paths = product.generate_product_docs()
        assert len(paths) == 6

        for p in paths:
            assert p.is_file()
            content = p.read_text(encoding="utf-8")
            assert "TaskMaster" in content

        # Check specific file content
        vision = (tmp_path / ".agent" / "product" / "vision.md").read_text(encoding="utf-8")
        assert "Product Vision" in vision
        assert "Core Purpose" in vision

    def test_get_progress_accurate(self, tmp_path: Path) -> None:
        """Progress reflects answered, auto-filled, and remaining counts."""
        product = self._make(tmp_path)
        progress = product.get_progress()
        assert progress["total_questions"] == len(PRODUCT_QUESTIONS)
        assert progress["answered"] == 0
        assert progress["remaining"] == len(PRODUCT_QUESTIONS)

        product.process_answer("vision", "task management")
        progress = product.get_progress()
        assert progress["answered"] == 1
        assert progress["remaining"] == len(PRODUCT_QUESTIONS) - 1

    def test_get_product_summary_non_empty(self, tmp_path: Path) -> None:
        """get_product_summary() returns non-empty string after answers provided."""
        entities = {"product_name": "TaskMaster", "product_description": "Task manager"}
        product = self._make(tmp_path, entities)
        product.process_answer("success_definition", "All tasks completed on time")

        summary = product.get_product_summary()
        assert len(summary) > 0
        assert "TaskMaster" in summary

    def test_get_product_summary_empty_state(self, tmp_path: Path) -> None:
        """get_product_summary() returns fallback when nothing is gathered."""
        product = self._make(tmp_path)
        summary = product.get_product_summary()
        assert "No product information" in summary

    def test_get_summary_prompt(self, tmp_path: Path) -> None:
        """get_summary_prompt() returns a prompt with entities and answers."""
        entities = {"product_name": "TestApp"}
        product = self._make(tmp_path, entities)
        product.process_answer("vision", "Helps with testing")

        prompt = product.get_summary_prompt()
        assert "TestApp" in prompt or "Product Name" in prompt
        assert "Helps with testing" in prompt

    def test_get_doc_generation_prompt(self, tmp_path: Path) -> None:
        """get_doc_generation_prompt() returns prompt for a specific document."""
        entities = {"product_name": "TestApp"}
        product = self._make(tmp_path, entities)

        prompt = product.get_doc_generation_prompt("vision.md")
        assert "Product Vision" in prompt
        assert "Core Purpose" in prompt

    def test_get_doc_generation_prompt_invalid(self, tmp_path: Path) -> None:
        """get_doc_generation_prompt() raises ValueError for unknown doc."""
        product = self._make(tmp_path)
        with pytest.raises(ValueError, match="Unknown product doc"):
            product.get_doc_generation_prompt("nonexistent.md")

    def test_process_generated_doc(self, tmp_path: Path) -> None:
        """process_generated_doc() writes content and returns path."""
        product = self._make(tmp_path)
        path = product.process_generated_doc("vision.md", "# Product Vision\n\nGenerated content here")
        assert path.is_file()
        assert "Generated content here" in path.read_text(encoding="utf-8")

    def test_auto_fill_plus_manual_answers(self, tmp_path: Path) -> None:
        """Auto-fill and manual answers both contribute to progress."""
        entities = {
            "product_description": "A task app",
            "problem_statement": "Tasks are messy",
        }
        product = self._make(tmp_path, entities)

        # Auto-fill first
        filled = product.auto_fill_from_entities()
        assert len(filled) > 0

        progress_after_fill = product.get_progress()

        # Then answer remaining manually
        product.process_answer("success_definition", "Clean task management")
        progress_after_manual = product.get_progress()

        assert progress_after_manual["answered"] > progress_after_fill["answered"]
