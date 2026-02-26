"""
Tests for Agent OS Phase 7 — Feature Expansion & Codebase Reality Engine.
"""

import json
from pathlib import Path

import pytest

from server.services.agent_os_codebase import AgentOSCodebaseAnalyzer
from server.services.agent_os_expand import AgentOSExpand
from server.services.agent_os_features import AgentOSFeatures
from server.services.agent_os_file_utils import AgentOSFileUtils
from server.services.agent_os_handoff import AgentOSHandoff
from server.services.agent_os_specs import AgentOSSpecs

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a minimal project directory with Agent OS structure."""
    (tmp_path / "agent-os" / "standards").mkdir(parents=True)
    (tmp_path / ".agent" / "product").mkdir(parents=True)
    (tmp_path / ".agent" / "specs").mkdir(parents=True)
    (tmp_path / ".agent" / "knowledge").mkdir(parents=True)

    # Write a standards file
    (tmp_path / "agent-os" / "standards" / "technology-stack.md").write_text(
        "# Tech Stack\n- React 19\n- TypeScript\n- Tailwind CSS v4\n"
    )

    # Write a product file
    (tmp_path / ".agent" / "product" / "vision.md").write_text(
        "# Vision\nBuild a task management app for small teams.\n"
    )

    return tmp_path


@pytest.fixture
def file_utils(project_dir: Path) -> AgentOSFileUtils:
    return AgentOSFileUtils(project_dir)


@pytest.fixture
def features(project_dir: Path, file_utils: AgentOSFileUtils) -> AgentOSFeatures:
    f = AgentOSFeatures(project_dir, file_utils, entities={}, config={})
    # Pre-populate some features
    f.add_feature({"name": "User Login", "description": "Basic auth", "priority": "must_have", "category": "auth"})
    f.add_feature({"name": "Task Board", "description": "Kanban view", "priority": "must_have", "category": "ui"})
    f.add_feature({"name": "Settings Page", "description": "User prefs", "priority": "should_have", "category": "ui"})
    return f


@pytest.fixture
def specs(project_dir: Path, file_utils: AgentOSFileUtils, features: AgentOSFeatures) -> AgentOSSpecs:
    return AgentOSSpecs(project_dir, file_utils, features, mechanism=None)


@pytest.fixture
def handoff(project_dir: Path, file_utils: AgentOSFileUtils, features: AgentOSFeatures, specs: AgentOSSpecs) -> AgentOSHandoff:
    return AgentOSHandoff(project_dir, file_utils, features, specs)


@pytest.fixture
def expand(project_dir: Path, file_utils: AgentOSFileUtils, features: AgentOSFeatures, specs: AgentOSSpecs, handoff: AgentOSHandoff) -> AgentOSExpand:
    return AgentOSExpand(project_dir, file_utils, features, specs, handoff, config={})


# ============================================================================
# Tests: AgentOSExpand
# ============================================================================


class TestExpandPrompts:
    """Test prompt generation methods."""

    def test_expansion_prompt_includes_existing_features(self, expand: AgentOSExpand) -> None:
        prompt = expand.get_expansion_prompt("Add email notifications")
        assert "User Login" in prompt
        assert "Task Board" in prompt
        assert "Settings Page" in prompt
        assert "email notifications" in prompt

    def test_expansion_prompt_includes_standards(self, expand: AgentOSExpand) -> None:
        prompt = expand.get_expansion_prompt("New feature")
        assert "Tech Stack" in prompt or "technology-stack.md" in prompt

    def test_expansion_prompt_includes_product(self, expand: AgentOSExpand) -> None:
        prompt = expand.get_expansion_prompt("New feature")
        assert "Vision" in prompt or "vision.md" in prompt

    def test_conflict_check_prompt_format(self, expand: AgentOSExpand) -> None:
        new_features = [{"name": "Email Alerts", "description": "Send emails"}]
        prompt = expand.get_conflict_check_prompt(new_features)
        assert "Existing Features" in prompt
        assert "Email Alerts" in prompt
        assert "User Login" in prompt


class TestExpandProcessing:
    """Test feature validation and conflict detection."""

    def test_process_expansion_accepts_valid_features(self, expand: AgentOSExpand) -> None:
        result = expand.process_expansion([
            {"name": "Email Alerts", "description": "Send emails"},
            {"name": "Push Notifications", "description": "Mobile push"},
        ])
        assert len(result["added"]) == 2
        assert len(result["conflicts"]) == 0

    def test_process_expansion_detects_name_conflict(self, expand: AgentOSExpand) -> None:
        result = expand.process_expansion([
            {"name": "User Login", "description": "Duplicate!"},
        ])
        assert len(result["added"]) == 0
        assert len(result["conflicts"]) == 1
        assert result["conflicts"][0]["type"] == "duplicate_name"

    def test_process_expansion_enforces_max_features(self, expand: AgentOSExpand) -> None:
        # Default max is 5
        many_features = [{"name": f"Feature {i}", "description": f"Desc {i}"} for i in range(8)]
        result = expand.process_expansion(many_features)
        assert len(result["added"]) <= 5
        assert len(result["warnings"]) >= 1

    def test_process_expansion_skips_empty_names(self, expand: AgentOSExpand) -> None:
        result = expand.process_expansion([
            {"name": "", "description": "No name"},
            {"name": "Valid Feature", "description": "Has name"},
        ])
        assert len(result["added"]) == 1
        assert len(result["warnings"]) >= 1

    def test_process_expansion_detects_intra_batch_duplicates(self, expand: AgentOSExpand) -> None:
        result = expand.process_expansion([
            {"name": "Same Name", "description": "First"},
            {"name": "Same Name", "description": "Second"},
        ])
        # First one is valid, second conflicts with it
        assert len(result["added"]) == 1
        assert len(result["conflicts"]) == 1

    def test_process_conflict_check_flags_built_features(self, expand: AgentOSExpand, features: AgentOSFeatures) -> None:
        # Mark a feature as built
        features.update_feature(1, {"passes": "passing"})

        conflict_json = {
            "conflicts": [],
            "required_changes": [
                {"existing_feature": "User Login", "change": "Add OAuth", "reason": "New auth method"}
            ],
            "new_dependencies": [],
        }
        result = expand.process_conflict_check(conflict_json)
        assert len(result["flagged_built_feature_changes"]) == 1
        assert result["flagged_built_feature_changes"][0]["severity"] == "critical"


class TestExpandAddFeatures:
    """Test actual feature addition."""

    def test_add_features_assigns_ids(self, expand: AgentOSExpand) -> None:
        added = expand.add_features([
            {"name": "Notifications", "description": "Push notifs"},
        ])
        assert len(added) == 1
        assert added[0]["id"] == 4  # Next after 3 existing features
        assert added[0]["name"] == "Notifications"

    def test_add_features_resolves_named_dependencies(self, expand: AgentOSExpand) -> None:
        added = expand.add_features([
            {"name": "Profile Page", "description": "User profile", "dependencies": ["User Login"]},
        ])
        assert len(added) == 1
        assert 1 in added[0]["dependencies"]  # User Login has id=1

    def test_add_features_resolves_int_dependencies(self, expand: AgentOSExpand) -> None:
        added = expand.add_features([
            {"name": "Profile Page", "description": "User profile", "dependencies": [1, 2]},
        ])
        assert added[0]["dependencies"] == [1, 2]


class TestExpandSummary:
    """Test summary generation."""

    def test_summary_before_expansion(self, expand: AgentOSExpand) -> None:
        summary = expand.get_expansion_summary()
        assert "No expansion" in summary

    def test_summary_after_expansion(self, expand: AgentOSExpand) -> None:
        expand.add_features([
            {"name": "Notifications", "description": "Push"},
            {"name": "Reports", "description": "Analytics"},
        ])
        summary = expand.get_expansion_summary()
        assert "2 new feature" in summary
        assert "Notifications" in summary
        assert "Reports" in summary


# ============================================================================
# Tests: AgentOSCodebaseAnalyzer
# ============================================================================


class TestCodebaseScan:
    """Test codebase scanning and detection."""

    def test_detect_tech_stack_node(self, project_dir: Path, file_utils: AgentOSFileUtils) -> None:
        # Write a package.json
        (project_dir / "package.json").write_text(json.dumps({
            "dependencies": {"react": "^19.0.0", "express": "^4.18.0"},
            "devDependencies": {"typescript": "^5.0.0", "eslint": "^9.0.0"},
        }))

        analyzer = AgentOSCodebaseAnalyzer(project_dir, file_utils)
        result = analyzer.detect_tech_stack()
        assert "TypeScript" in result["languages"]
        assert "React" in result["frameworks"]
        assert "Express" in result["frameworks"]
        assert "ESLint" in result["tools"]

    def test_detect_tech_stack_python(self, project_dir: Path, file_utils: AgentOSFileUtils) -> None:
        (project_dir / "requirements.txt").write_text("fastapi==0.100.0\nsqlalchemy==2.0\npytest\n")

        analyzer = AgentOSCodebaseAnalyzer(project_dir, file_utils)
        result = analyzer.detect_tech_stack()
        assert "Python" in result["languages"]
        assert "FastAPI" in result["frameworks"]
        assert "SQLAlchemy" in result["frameworks"]
        assert "pytest" in result["tools"]

    def test_detect_tech_stack_rust(self, project_dir: Path, file_utils: AgentOSFileUtils) -> None:
        (project_dir / "Cargo.toml").write_text("[package]\nname = 'test'\nversion = '0.1.0'\n")

        analyzer = AgentOSCodebaseAnalyzer(project_dir, file_utils)
        result = analyzer.detect_tech_stack()
        assert "Rust" in result["languages"]

    def test_detect_file_structure_by_type(self, project_dir: Path, file_utils: AgentOSFileUtils) -> None:
        for d in ("src/components", "src/hooks", "src/utils", "src/services"):
            (project_dir / d).mkdir(parents=True, exist_ok=True)
            (project_dir / d / "index.ts").write_text("export {}")

        analyzer = AgentOSCodebaseAnalyzer(project_dir, file_utils)
        result = analyzer.detect_file_structure()
        assert result["pattern"] == "by-type"

    def test_detect_file_structure_flat(self, project_dir: Path, file_utils: AgentOSFileUtils) -> None:
        # Only root-level files, no deep dirs
        (project_dir / "app.py").write_text("print('hi')")
        (project_dir / "config.py").write_text("DEBUG = True")

        analyzer = AgentOSCodebaseAnalyzer(project_dir, file_utils)
        result = analyzer.detect_file_structure()
        assert result["file_count"] >= 2

    def test_detect_code_patterns(self, project_dir: Path, file_utils: AgentOSFileUtils) -> None:
        (project_dir / "src").mkdir(exist_ok=True)
        (project_dir / "src" / "main.py").write_text(
            "def my_function():\n    my_var = 1\n    another_thing = 2\n"
            "def yet_another():\n    pass\n"
        )

        analyzer = AgentOSCodebaseAnalyzer(project_dir, file_utils)
        result = analyzer.detect_code_patterns()
        # The enhanced version uses "naming_convention" key
        naming_key = "naming_convention" if "naming_convention" in result else "naming"
        assert result[naming_key] == "snake_case"
        assert result["files_sampled"] >= 1

    def test_detect_linter_config(self, project_dir: Path, file_utils: AgentOSFileUtils) -> None:
        (project_dir / "tsconfig.json").write_text('{}')
        (project_dir / ".eslintrc.json").write_text('{}')
        (project_dir / ".prettierrc").write_text('{}')

        analyzer = AgentOSCodebaseAnalyzer(project_dir, file_utils)
        result = analyzer.detect_linter_config()
        # The enhanced version uses "configs" as list of dicts with "tool" key
        if "detected_configs" in result:
            assert "typescript" in result["detected_configs"]
            assert "eslint" in result["detected_configs"]
            assert "prettier" in result["detected_configs"]
        else:
            config_tools = [c.get("tool", "").lower() for c in result.get("configs", [])]
            assert any("typescript" in t for t in config_tools)
            assert any("eslint" in t for t in config_tools)
            assert any("prettier" in t for t in config_tools)

    def test_detect_test_patterns(self, project_dir: Path, file_utils: AgentOSFileUtils) -> None:
        (project_dir / "tests").mkdir(exist_ok=True)
        (project_dir / "tests" / "test_auth.py").write_text("def test_login(): pass")
        (project_dir / "tests" / "test_utils.py").write_text("def test_helper(): pass")

        analyzer = AgentOSCodebaseAnalyzer(project_dir, file_utils)
        result = analyzer.detect_test_patterns()
        assert result["test_file_count"] >= 2
        # Pattern string varies between original and enhanced version
        assert "test_" in result["pattern"].lower() or "test" in result["pattern"].lower()

    def test_full_scan(self, project_dir: Path, file_utils: AgentOSFileUtils) -> None:
        (project_dir / "package.json").write_text(json.dumps({
            "dependencies": {"react": "^19.0.0"},
            "devDependencies": {"typescript": "^5.0.0"},
        }))

        analyzer = AgentOSCodebaseAnalyzer(project_dir, file_utils)
        result = analyzer.scan_codebase()
        assert "tech_stack" in result
        assert "file_structure" in result
        assert "code_patterns" in result
        assert "linter_config" in result
        assert "test_patterns" in result


class TestCodebaseInference:
    """Test inference prompt generation."""

    def test_standards_inference_prompt(self, project_dir: Path, file_utils: AgentOSFileUtils) -> None:
        analyzer = AgentOSCodebaseAnalyzer(project_dir, file_utils)
        prompt = analyzer.get_standards_inference_prompt()
        assert "technology-stack.md" in prompt
        assert "coding-conventions.md" in prompt

    def test_product_inference_prompt(self, project_dir: Path, file_utils: AgentOSFileUtils) -> None:
        (project_dir / "README.md").write_text("# My App\nA great app for tasks.\n")

        analyzer = AgentOSCodebaseAnalyzer(project_dir, file_utils)
        prompt = analyzer.get_product_inference_prompt()
        assert "vision.md" in prompt
        assert "My App" in prompt

    def test_process_standards_inference(self, project_dir: Path, file_utils: AgentOSFileUtils) -> None:
        analyzer = AgentOSCodebaseAnalyzer(project_dir, file_utils)
        paths = analyzer.process_standards_inference({
            "technology-stack.md": "# Tech\nReact + TypeScript",
            "coding-conventions.md": "# Conventions\nUse camelCase",
        })
        assert len(paths) == 2
        for p in paths:
            assert p.exists()

    def test_process_product_inference(self, project_dir: Path, file_utils: AgentOSFileUtils) -> None:
        analyzer = AgentOSCodebaseAnalyzer(project_dir, file_utils)
        paths = analyzer.process_product_inference({
            "vision.md": "# Vision\nTask app for teams",
            "target-users.md": "# Target Users\nSmall teams",
        })
        assert len(paths) == 2
        for p in paths:
            assert p.exists()

    def test_process_feature_inference(self, project_dir: Path, file_utils: AgentOSFileUtils) -> None:
        analyzer = AgentOSCodebaseAnalyzer(project_dir, file_utils)
        features = analyzer.process_feature_inference([
            {"name": "Auth", "description": "Login system", "priority": "must_have", "category": "auth"},
            {"name": "Dashboard", "description": "Main view", "priority": "must_have", "category": "ui"},
        ])
        assert len(features) == 2
        assert features[0]["passes"] == "passing"
        assert features[0]["source"] in ("cre_inference", "codebase_inference")

    def test_analysis_summary(self, project_dir: Path, file_utils: AgentOSFileUtils) -> None:
        (project_dir / "package.json").write_text(json.dumps({
            "dependencies": {"react": "^19.0.0"},
        }))

        analyzer = AgentOSCodebaseAnalyzer(project_dir, file_utils)
        analyzer.scan_codebase()
        summary = analyzer.get_analysis_summary()
        assert "Codebase Analysis Summary" in summary
        assert "Languages" in summary

    def test_summary_before_scan(self, project_dir: Path, file_utils: AgentOSFileUtils) -> None:
        analyzer = AgentOSCodebaseAnalyzer(project_dir, file_utils)
        summary = analyzer.get_analysis_summary()
        assert "No" in summary and "analysis" in summary.lower()
