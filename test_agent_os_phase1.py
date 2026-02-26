"""
Agent OS Phase 1 Tests
======================

Tests for AgentOSFileUtils and AgentOSStandards.
"""

import json
from pathlib import Path

import pytest

from server.services.agent_os_file_utils import AgentOSFileUtils
from server.services.agent_os_standards import AgentOSStandards

# ── AgentOSFileUtils ─────────────────────────────────────────────────


class TestFileUtils:
    def test_ensure_dirs_creates_all_directories(self, tmp_path: Path) -> None:
        """All expected directories are created."""
        utils = AgentOSFileUtils(tmp_path, global_standards_dir=tmp_path / "global_std")
        utils.ensure_agent_os_dirs()

        assert (tmp_path / "agent-os" / "standards").is_dir()
        assert (tmp_path / ".agent" / "product").is_dir()
        assert (tmp_path / ".agent" / "specs").is_dir()
        assert (tmp_path / ".agent" / "intake").is_dir()
        assert (tmp_path / ".agent" / "knowledge").is_dir()
        assert (tmp_path / ".agent" / "progress").is_dir()
        assert (tmp_path / ".agent" / "settings").is_dir()
        assert (tmp_path / ".agent" / "comms").is_dir()
        assert (tmp_path / ".agent" / "output").is_dir()
        assert (tmp_path / ".agent" / "analytics").is_dir()
        assert (tmp_path / ".agent" / "analytics" / "reports").is_dir()

    def test_read_standards_falls_back_to_global(self, tmp_path: Path) -> None:
        """If project standards don't exist, reads from global dir."""
        global_dir = tmp_path / "global_std"
        global_dir.mkdir(parents=True)
        (global_dir / "technology-stack.md").write_text("# Global Tech Stack", encoding="utf-8")

        utils = AgentOSFileUtils(tmp_path, global_standards_dir=global_dir)
        content = utils.read_standards_file("technology-stack.md")
        assert content == "# Global Tech Stack"

    def test_read_standards_prefers_project(self, tmp_path: Path) -> None:
        """Project-level standards take priority over global."""
        global_dir = tmp_path / "global_std"
        global_dir.mkdir(parents=True)
        (global_dir / "technology-stack.md").write_text("# Global", encoding="utf-8")

        project_std = tmp_path / "agent-os" / "standards"
        project_std.mkdir(parents=True)
        (project_std / "technology-stack.md").write_text("# Project", encoding="utf-8")

        utils = AgentOSFileUtils(tmp_path, global_standards_dir=global_dir)
        content = utils.read_standards_file("technology-stack.md")
        assert content == "# Project"

    def test_write_standards_to_project(self, tmp_path: Path) -> None:
        """Writing with location='project' goes to agent-os/standards/."""
        utils = AgentOSFileUtils(tmp_path, global_standards_dir=tmp_path / "global_std")
        path = utils.write_standards_file("test.md", "# Test", location="project")
        assert path == tmp_path / "agent-os" / "standards" / "test.md"
        assert path.read_text(encoding="utf-8") == "# Test"

    def test_write_standards_to_global(self, tmp_path: Path) -> None:
        """Writing with location='global' goes to global standards dir."""
        global_dir = tmp_path / "global_std"
        utils = AgentOSFileUtils(tmp_path, global_standards_dir=global_dir)
        path = utils.write_standards_file("test.md", "# Global Test", location="global")
        assert path == global_dir / "test.md"
        assert path.read_text(encoding="utf-8") == "# Global Test"

    def test_list_files_includes_both_project_and_global(self, tmp_path: Path) -> None:
        """list_files_in_layer('standards') includes files from both locations."""
        global_dir = tmp_path / "global_std"
        global_dir.mkdir(parents=True)
        (global_dir / "global-only.md").write_text("global", encoding="utf-8")

        project_std = tmp_path / "agent-os" / "standards"
        project_std.mkdir(parents=True)
        (project_std / "project-only.md").write_text("project", encoding="utf-8")

        utils = AgentOSFileUtils(tmp_path, global_standards_dir=global_dir)
        files = utils.list_files_in_layer("standards")
        names = [f["name"] for f in files]
        assert "project-only.md" in names
        assert "global-only.md" in names

        # Check location tags
        project_file = next(f for f in files if f["name"] == "project-only.md")
        global_file = next(f for f in files if f["name"] == "global-only.md")
        assert project_file["location"] == "project"
        assert global_file["location"] == "global"

    def test_read_write_product_file(self, tmp_path: Path) -> None:
        """Read/write product files at .agent/product/."""
        utils = AgentOSFileUtils(tmp_path, global_standards_dir=tmp_path / "global_std")
        path = utils.write_product_file("vision.md", "# Vision")
        assert path == tmp_path / ".agent" / "product" / "vision.md"

        content = utils.read_product_file("vision.md")
        assert content == "# Vision"

    def test_read_write_spec_file(self, tmp_path: Path) -> None:
        """Read/write spec files at .agent/specs/."""
        utils = AgentOSFileUtils(tmp_path, global_standards_dir=tmp_path / "global_std")
        path = utils.write_spec_file("feature-1.md", "# Feature 1")
        assert path == tmp_path / ".agent" / "specs" / "feature-1.md"

        content = utils.read_spec_file("feature-1.md")
        assert content == "# Feature 1"

    def test_standards_exist_false_when_empty(self, tmp_path: Path) -> None:
        """standards_exist() returns False when no files present."""
        utils = AgentOSFileUtils(tmp_path, global_standards_dir=tmp_path / "global_std")
        assert utils.standards_exist() is False

    def test_standards_exist_true_with_files(self, tmp_path: Path) -> None:
        """standards_exist() returns True when files present."""
        project_std = tmp_path / "agent-os" / "standards"
        project_std.mkdir(parents=True)
        (project_std / "test.md").write_text("content", encoding="utf-8")

        utils = AgentOSFileUtils(tmp_path, global_standards_dir=tmp_path / "global_std")
        assert utils.standards_exist() is True

    def test_product_exists(self, tmp_path: Path) -> None:
        """product_exists() returns correct state."""
        utils = AgentOSFileUtils(tmp_path, global_standards_dir=tmp_path / "global_std")
        assert utils.product_exists() is False

        utils.write_product_file("vision.md", "# Vision")
        assert utils.product_exists() is True

    def test_generic_read_write_dispatcher(self, tmp_path: Path) -> None:
        """read_file() and write_file() dispatch correctly."""
        utils = AgentOSFileUtils(tmp_path, global_standards_dir=tmp_path / "global_std")
        utils.write_file("product", "test.md", "# Test Product")
        content = utils.read_file("product", "test.md")
        assert content == "# Test Product"

    def test_get_layer_path(self, tmp_path: Path) -> None:
        """get_layer_path() returns correct paths."""
        utils = AgentOSFileUtils(tmp_path, global_standards_dir=tmp_path / "global_std")
        assert utils.get_layer_path("standards") == tmp_path / "agent-os" / "standards"
        assert utils.get_layer_path("product") == tmp_path / ".agent" / "product"
        assert utils.get_layer_path("specs") == tmp_path / ".agent" / "specs"

    def test_get_layer_path_invalid(self, tmp_path: Path) -> None:
        """get_layer_path() raises ValueError for unknown layers."""
        utils = AgentOSFileUtils(tmp_path, global_standards_dir=tmp_path / "global_std")
        with pytest.raises(ValueError, match="Unknown layer"):
            utils.get_layer_path("nonexistent")

    def test_read_nonexistent_returns_none(self, tmp_path: Path) -> None:
        """Reading a non-existent file returns None."""
        utils = AgentOSFileUtils(tmp_path, global_standards_dir=tmp_path / "global_std")
        assert utils.read_standards_file("nope.md") is None
        assert utils.read_product_file("nope.md") is None
        assert utils.read_spec_file("nope.md") is None

    def test_path_traversal_absolute_stripped(self, tmp_path: Path) -> None:
        """Absolute paths in filenames are sanitized to just the filename."""
        utils = AgentOSFileUtils(tmp_path, global_standards_dir=tmp_path / "global_std")
        # /etc/passwd should be sanitized to just "passwd" in the safe directory
        path = utils.write_product_file("/etc/passwd", "safe content")
        assert path.name == "passwd"
        assert ".agent/product" in str(path)
        assert "/etc/" not in str(path)

    def test_path_traversal_dotdot_stripped(self, tmp_path: Path) -> None:
        """../ components are stripped from filenames."""
        utils = AgentOSFileUtils(tmp_path, global_standards_dir=tmp_path / "global_std")
        # ../../etc/passwd should be sanitized to just "passwd"
        path = utils.write_product_file("../../etc/passwd", "safe content")
        assert path.name == "passwd"
        assert ".agent/product" in str(path)
        assert "/etc/" not in str(path)

    def test_path_traversal_backslash_blocked(self, tmp_path: Path) -> None:
        """Backslash path traversal is also handled."""
        utils = AgentOSFileUtils(tmp_path, global_standards_dir=tmp_path / "global_std")
        path = utils.write_spec_file("..\\..\\etc\\passwd", "safe")
        assert path.name == "passwd"
        assert ".agent/specs" in str(path)

    def test_empty_filename_rejected(self, tmp_path: Path) -> None:
        """Empty filenames are rejected."""
        utils = AgentOSFileUtils(tmp_path, global_standards_dir=tmp_path / "global_std")
        with pytest.raises(ValueError, match="Invalid filename"):
            utils.write_product_file("", "content")
        with pytest.raises(ValueError, match="Invalid filename"):
            utils.write_product_file(".", "content")


# ── AgentOSStandards ─────────────────────────────────────────────────


class TestStandards:
    def _make(self, tmp_path: Path) -> AgentOSStandards:
        utils = AgentOSFileUtils(tmp_path, global_standards_dir=tmp_path / "global_std")
        return AgentOSStandards(tmp_path, utils)

    def test_get_next_question_returns_first(self, tmp_path: Path) -> None:
        """First call returns the first question."""
        standards = self._make(tmp_path)
        q = standards.get_next_question()
        assert q is not None
        assert q["id"] == "tech_languages"

    def test_process_answer_stores_and_decrements(self, tmp_path: Path) -> None:
        """Processing an answer stores it and decrements remaining count."""
        standards = self._make(tmp_path)
        result = standards.process_answer("tech_languages", "Python")
        assert result["stored"] is True
        assert isinstance(result["remaining"], int)
        assert result["remaining"] < 16  # Less than total (some may be skipped)

    def test_skip_logic_skips_frontend_when_no_frontend(self, tmp_path: Path) -> None:
        """Questions with skip_if are skipped when condition is met."""
        standards = self._make(tmp_path)

        # Answer tech_languages as Python (not JS/TS)
        standards.process_answer("tech_languages", "Python")
        # Set frontend to None
        standards.process_answer("tech_frontend", "None")

        # Questions that depend on frontend should be skipped
        seen_ids: list[str] = []
        while True:
            q = standards.get_next_question()
            if q is None:
                break
            seen_ids.append(q["id"])
            standards.process_answer(q["id"], "test_value")

        # style_components, ui_design_system, ui_responsive, arch_state should be skipped
        assert "style_components" not in seen_ids
        assert "ui_design_system" not in seen_ids
        assert "ui_responsive" not in seen_ids
        assert "arch_state" not in seen_ids

    def test_generate_standards_files_creates_all(self, tmp_path: Path) -> None:
        """With answers provided, all 6 standards files are created."""
        standards = self._make(tmp_path)

        # Provide minimum answers
        standards.process_answer("tech_languages", "TypeScript")
        standards.process_answer("tech_frontend", "React")
        standards.process_answer("tech_backend", "FastAPI")
        standards.process_answer("tech_database", "PostgreSQL")
        standards.process_answer("style_guide", "Airbnb")
        standards.process_answer("arch_api_style", "REST")

        paths = standards.generate_standards_files()
        assert len(paths) == 6

        for p in paths:
            assert p.is_file()
            content = p.read_text(encoding="utf-8")
            assert content.startswith("#")

    def test_infer_from_package_json(self, tmp_path: Path) -> None:
        """Detects React, TypeScript from package.json."""
        pkg = {
            "dependencies": {"react": "^18.0.0"},
            "devDependencies": {"typescript": "^5.0.0", "tailwindcss": "^4.0.0"},
        }
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

        standards = self._make(tmp_path)
        inferred = standards.infer_standards_from_codebase()

        assert inferred.get("tech_languages") == "TypeScript"
        assert inferred.get("tech_frontend") == "React"
        assert inferred.get("ui_design_system") == "Tailwind"

    def test_infer_from_requirements_txt(self, tmp_path: Path) -> None:
        """Detects FastAPI, SQLAlchemy from requirements.txt."""
        (tmp_path / "requirements.txt").write_text("fastapi>=0.100\nsqlalchemy>=2.0\nruff\n", encoding="utf-8")

        standards = self._make(tmp_path)
        inferred = standards.infer_standards_from_codebase()

        assert inferred.get("tech_languages") == "Python"
        assert inferred.get("tech_backend") == "FastAPI"
        assert inferred.get("tech_database") == "SQLite"
        assert inferred.get("style_guide") == "PEP 8"

    def test_get_progress_accurate(self, tmp_path: Path) -> None:
        """Progress reflects answered, skipped, and remaining counts."""
        standards = self._make(tmp_path)
        progress = standards.get_progress()
        assert progress["total_questions"] == 17
        assert progress["answered"] == 0
        assert progress["remaining"] > 0

        standards.process_answer("tech_languages", "Python")
        progress = standards.get_progress()
        assert progress["answered"] == 1

    def test_validate_standards_detects_pep8_mismatch(self, tmp_path: Path) -> None:
        """Validation catches PEP 8 with non-Python language."""
        standards = self._make(tmp_path)
        standards.process_answer("tech_languages", "JavaScript")
        standards.process_answer("style_guide", "PEP 8")

        issues = standards.validate_standards()
        assert len(issues) > 0
        assert any("PEP 8" in issue["message"] for issue in issues)

    def test_get_standards_summary(self, tmp_path: Path) -> None:
        """Summary is non-empty after providing answers."""
        standards = self._make(tmp_path)
        standards.process_answer("tech_languages", "Python")
        standards.process_answer("tech_backend", "FastAPI")

        summary = standards.get_standards_summary()
        assert "Standards Summary:" in summary
        # With no files written yet, falls back to answers
        assert "Python" in summary or "FastAPI" in summary

    def test_question_serialization_strips_skip_if(self, tmp_path: Path) -> None:
        """Returned question dicts do not contain skip_if lambdas."""
        standards = self._make(tmp_path)
        q = standards.get_next_question()
        assert q is not None
        assert "skip_if" not in q

    def test_get_next_question_returns_none_when_done(self, tmp_path: Path) -> None:
        """Returns None when all questions are answered."""
        standards = self._make(tmp_path)
        while True:
            q = standards.get_next_question()
            if q is None:
                break
            standards.process_answer(q["id"], "test")
        assert standards.get_next_question() is None
