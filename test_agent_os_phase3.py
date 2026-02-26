"""
Tests for Phase 3: Feature Extraction & Gap Analysis + Mechanism Analysis
"""

from pathlib import Path

import pytest

from server.services.agent_os_features import AgentOSFeatures
from server.services.agent_os_file_utils import AgentOSFileUtils
from server.services.agent_os_mechanism import AgentOSMechanism

# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory with standards and product files."""
    # Standards
    standards_dir = tmp_path / "agent-os" / "standards"
    standards_dir.mkdir(parents=True)
    (standards_dir / "technology-stack.md").write_text("# Technology Stack\n\n## Languages\nTypeScript\n")

    # Product
    product_dir = tmp_path / ".agent" / "product"
    product_dir.mkdir(parents=True)
    (product_dir / "vision.md").write_text("# Vision\n\n## Core Purpose\nA task management app\n")
    (product_dir / "target-users.md").write_text("# Target Users\n\n## Primary Users\nDevelopers\n")

    # Specs dir
    (tmp_path / ".agent" / "specs").mkdir(parents=True, exist_ok=True)

    return tmp_path


@pytest.fixture
def file_utils(tmp_project: Path) -> AgentOSFileUtils:
    return AgentOSFileUtils(tmp_project)


@pytest.fixture
def sample_entities() -> dict:
    return {
        "product_name": "TaskFlow",
        "product_description": "A task management app for developers",
        "target_users": ["developers", "team leads"],
        "core_features": ["task creation", "task assignment", "notifications"],
        "constraints": ["must work offline"],
        "tech_preferences": ["TypeScript", "React"],
        "problem_statement": "Developers waste time switching between tools",
        "competitive_refs": ["Jira", "Linear"],
    }


@pytest.fixture
def default_config() -> dict:
    return {
        "auto_select_threshold": 85,
        "present_alternatives_gap": 15,
        "min_viable_score": 60,
    }


@pytest.fixture
def features_service(tmp_project: Path, file_utils: AgentOSFileUtils, sample_entities: dict, default_config: dict) -> AgentOSFeatures:
    return AgentOSFeatures(tmp_project, file_utils, sample_entities, default_config)


@pytest.fixture
def sample_features_json() -> list[dict]:
    """Claude-style extracted features (before processing)."""
    return [
        {
            "name": "User Authentication",
            "description": "Login and signup with email/password",
            "priority": "must_have",
            "complexity": "medium",
            "category": "auth",
            "dependencies": [],
            "source": "vision.md",
        },
        {
            "name": "Task CRUD",
            "description": "Create, read, update, delete tasks",
            "priority": "must_have",
            "complexity": "medium",
            "category": "data",
            "dependencies": ["User Authentication"],
            "source": "vision.md",
        },
        {
            "name": "Task Notifications",
            "description": "Email notifications for task updates",
            "priority": "should_have",
            "complexity": "small",
            "category": "integration",
            "dependencies": ["Task CRUD"],
            "source": "entities",
        },
        {
            "name": "Dark Mode",
            "description": "Toggle between light and dark themes",
            "priority": "nice_to_have",
            "complexity": "small",
            "category": "ui",
            "dependencies": [],
            "source": "competitive_refs",
        },
    ]


# ── TestFeatures ─────────────────────────────────────────────────────


class TestFeatures:
    def test_feature_extraction_prompt_includes_context(self, features_service: AgentOSFeatures) -> None:
        """Prompt includes product summary, entities, and standards."""
        prompt = features_service.get_feature_extraction_prompt()
        assert "TaskFlow" in prompt or "task management" in prompt.lower()
        assert "TypeScript" in prompt
        assert "vision.md" in prompt or "Core Purpose" in prompt

    def test_process_extracted_features_assigns_ids(self, features_service: AgentOSFeatures, sample_features_json: list[dict]) -> None:
        """Features get sequential IDs starting from 1."""
        result = features_service.process_extracted_features(sample_features_json)
        assert len(result) == 4
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2
        assert result[2]["id"] == 3
        assert result[3]["id"] == 4

    def test_process_extracted_features_resolves_dependencies(self, features_service: AgentOSFeatures, sample_features_json: list[dict]) -> None:
        """Named dependencies are resolved to IDs."""
        result = features_service.process_extracted_features(sample_features_json)
        # "Task CRUD" depends on "User Authentication" (id=1)
        assert result[1]["dependencies"] == [1]
        # "Task Notifications" depends on "Task CRUD" (id=2)
        assert result[2]["dependencies"] == [2]
        # "Dark Mode" has no deps
        assert result[3]["dependencies"] == []

    def test_process_extracted_features_validates_priority(self, features_service: AgentOSFeatures) -> None:
        """Invalid priority falls back to should_have."""
        result = features_service.process_extracted_features([
            {"name": "Foo", "description": "Bar", "priority": "invalid_priority"}
        ])
        assert result[0]["priority"] == "should_have"

    def test_process_extracted_features_validates_complexity(self, features_service: AgentOSFeatures) -> None:
        """Invalid complexity falls back to medium."""
        result = features_service.process_extracted_features([
            {"name": "Foo", "description": "Bar", "complexity": "huge"}
        ])
        assert result[0]["complexity"] == "medium"

    def test_add_feature_manual(self, features_service: AgentOSFeatures) -> None:
        """Manually added features get IDs and are stored."""
        f = features_service.add_feature({"name": "Manual Feature", "description": "Added by user"})
        assert f["id"] == 1
        assert f["name"] == "Manual Feature"
        assert f["source"] == "manual"
        assert features_service.get_feature_by_id(1) is not None

    def test_add_feature_increments_id(self, features_service: AgentOSFeatures) -> None:
        """Each added feature gets an incremented ID."""
        f1 = features_service.add_feature({"name": "First"})
        f2 = features_service.add_feature({"name": "Second"})
        assert f1["id"] == 1
        assert f2["id"] == 2

    def test_remove_feature_cleans_dependencies(self, features_service: AgentOSFeatures, sample_features_json: list[dict]) -> None:
        """Removing a feature also removes it from others' dependency lists."""
        features_service.process_extracted_features(sample_features_json)
        # Feature 2 (Task CRUD) depends on feature 1 (User Auth)
        assert 1 in features_service.get_feature_by_id(2)["dependencies"]

        # Remove feature 1
        assert features_service.remove_feature(1) is True
        # Feature 2 should no longer reference feature 1
        f2 = features_service.get_feature_by_id(2)
        assert 1 not in f2["dependencies"]

    def test_remove_feature_nonexistent(self, features_service: AgentOSFeatures) -> None:
        """Removing a nonexistent feature returns False."""
        assert features_service.remove_feature(999) is False

    def test_update_feature(self, features_service: AgentOSFeatures) -> None:
        """Updating a feature modifies only specified fields."""
        features_service.add_feature({"name": "Original", "description": "Before", "priority": "must_have"})
        result = features_service.update_feature(1, {"description": "After"})
        assert result is not None
        assert result["description"] == "After"
        assert result["name"] == "Original"  # Unchanged
        assert result["priority"] == "must_have"  # Unchanged

    def test_update_feature_rejects_invalid_priority(self, features_service: AgentOSFeatures) -> None:
        """Invalid priority in update is ignored."""
        features_service.add_feature({"name": "Test", "priority": "must_have"})
        result = features_service.update_feature(1, {"priority": "invalid"})
        assert result["priority"] == "must_have"

    def test_update_feature_nonexistent(self, features_service: AgentOSFeatures) -> None:
        """Updating a nonexistent feature returns None."""
        assert features_service.update_feature(999, {"name": "nope"}) is None

    def test_get_feature_list_sorted_by_priority(self, features_service: AgentOSFeatures, sample_features_json: list[dict]) -> None:
        """must_have features come before should_have and nice_to_have."""
        features_service.process_extracted_features(sample_features_json)
        result = features_service.get_feature_list()
        priorities = [f["priority"] for f in result]
        # All must_have first, then should_have, then nice_to_have
        assert priorities == ["must_have", "must_have", "should_have", "nice_to_have"]

    def test_get_feature_by_id(self, features_service: AgentOSFeatures) -> None:
        """Can retrieve a feature by ID."""
        features_service.add_feature({"name": "Findable"})
        assert features_service.get_feature_by_id(1)["name"] == "Findable"
        assert features_service.get_feature_by_id(999) is None

    def test_gap_analysis_prompt_includes_all_layers(self, features_service: AgentOSFeatures, sample_features_json: list[dict]) -> None:
        """Prompt includes standards, product, and features."""
        features_service.process_extracted_features(sample_features_json)
        prompt = features_service.get_gap_analysis_prompt()
        # Should include standards content
        assert "TypeScript" in prompt or "Technology Stack" in prompt
        # Should include product content
        assert "Vision" in prompt or "task management" in prompt.lower()
        # Should include features
        assert "User Authentication" in prompt
        assert "Task CRUD" in prompt

    def test_process_gap_analysis_applies_threshold(self, features_service: AgentOSFeatures) -> None:
        """Gaps with confidence > threshold are marked auto_fillable."""
        gaps = features_service.process_gap_analysis([
            {
                "type": "missing_detail",
                "severity": "important",
                "message": "Missing API spec",
                "layers": ["features"],
                "recommendation": "Add API endpoints",
                "confidence": 0.9,  # Above 0.85 threshold
            },
            {
                "type": "unstated_dep",
                "severity": "minor",
                "message": "Implicit database dep",
                "layers": ["features"],
                "recommendation": "Add DB feature",
                "confidence": 0.5,  # Below threshold
            },
        ])
        assert len(gaps) == 2
        assert gaps[0]["auto_fillable"] is True  # 0.9 >= 0.85
        assert gaps[1]["auto_fillable"] is False  # 0.5 < 0.85

    def test_process_gap_analysis_clamps_confidence(self, features_service: AgentOSFeatures) -> None:
        """Confidence values are clamped to 0.0-1.0."""
        gaps = features_service.process_gap_analysis([
            {"type": "missing_detail", "severity": "minor", "message": "Test", "layers": [], "recommendation": "Fix", "confidence": 1.5},
            {"type": "missing_detail", "severity": "minor", "message": "Test2", "layers": [], "recommendation": "Fix", "confidence": -0.5},
        ])
        assert gaps[0]["confidence"] == 1.0
        assert gaps[1]["confidence"] == 0.0

    def test_resolve_gap(self, features_service: AgentOSFeatures) -> None:
        """Resolving a gap marks it resolved with resolution text."""
        features_service.process_gap_analysis([
            {"type": "blocking", "severity": "blocking", "message": "Missing detail", "layers": [], "recommendation": "Add it", "confidence": 0.5}
        ])
        result = features_service.resolve_gap(1, "Added the missing detail")
        assert result is not None
        assert result["resolved"] is True
        assert result["resolution"] == "Added the missing detail"

    def test_resolve_gap_nonexistent(self, features_service: AgentOSFeatures) -> None:
        """Resolving a nonexistent gap returns None."""
        assert features_service.resolve_gap(999, "nope") is None

    def test_auto_resolve_gaps(self, features_service: AgentOSFeatures) -> None:
        """auto_resolve_gaps() resolves all auto_fillable gaps."""
        features_service.process_gap_analysis([
            {"type": "missing_detail", "severity": "minor", "message": "Gap 1", "layers": [], "recommendation": "Fix 1", "confidence": 0.9},
            {"type": "missing_detail", "severity": "minor", "message": "Gap 2", "layers": [], "recommendation": "Fix 2", "confidence": 0.9},
            {"type": "missing_detail", "severity": "blocking", "message": "Gap 3", "layers": [], "recommendation": "Fix 3", "confidence": 0.3},
        ])
        resolved = features_service.auto_resolve_gaps()
        assert len(resolved) == 2
        assert resolved[0]["resolution"] == "Fix 1"
        assert resolved[1]["resolution"] == "Fix 2"
        # Gap 3 should NOT be resolved
        all_gaps = features_service.get_all_gaps()
        gap3 = [g for g in all_gaps if g["message"] == "Gap 3"][0]
        assert gap3["resolved"] is False

    def test_has_blocking_gaps(self, features_service: AgentOSFeatures) -> None:
        """Returns True when unresolved blocking gaps exist."""
        features_service.process_gap_analysis([
            {"type": "missing_detail", "severity": "blocking", "message": "Blocker", "layers": [], "recommendation": "Fix", "confidence": 0.5},
        ])
        assert features_service.has_blocking_gaps() is True
        features_service.resolve_gap(1, "Fixed")
        assert features_service.has_blocking_gaps() is False

    def test_has_blocking_gaps_none(self, features_service: AgentOSFeatures) -> None:
        """Returns False when no gaps exist."""
        assert features_service.has_blocking_gaps() is False

    def test_get_blocking_gaps(self, features_service: AgentOSFeatures) -> None:
        """get_blocking_gaps returns only unresolved blocking gaps."""
        features_service.process_gap_analysis([
            {"type": "a", "severity": "blocking", "message": "B1", "layers": [], "recommendation": "Fix", "confidence": 0.5},
            {"type": "b", "severity": "important", "message": "I1", "layers": [], "recommendation": "Fix", "confidence": 0.5},
            {"type": "c", "severity": "blocking", "message": "B2", "layers": [], "recommendation": "Fix", "confidence": 0.5},
        ])
        blocking = features_service.get_blocking_gaps()
        assert len(blocking) == 2
        assert all(g["severity"] == "blocking" for g in blocking)

    def test_get_all_gaps_sorted(self, features_service: AgentOSFeatures) -> None:
        """get_all_gaps returns gaps sorted by severity (blocking first)."""
        features_service.process_gap_analysis([
            {"type": "a", "severity": "minor", "message": "M", "layers": [], "recommendation": "", "confidence": 0.5},
            {"type": "b", "severity": "blocking", "message": "B", "layers": [], "recommendation": "", "confidence": 0.5},
            {"type": "c", "severity": "important", "message": "I", "layers": [], "recommendation": "", "confidence": 0.5},
        ])
        gaps = features_service.get_all_gaps()
        severities = [g["severity"] for g in gaps]
        assert severities == ["blocking", "important", "minor"]

    def test_feature_count_by_priority(self, features_service: AgentOSFeatures, sample_features_json: list[dict]) -> None:
        """Correctly counts features per priority level."""
        features_service.process_extracted_features(sample_features_json)
        counts = features_service.get_feature_count_by_priority()
        assert counts == {"must_have": 2, "should_have": 1, "nice_to_have": 1}

    # ── Edge case tests ──────────────────────────────────────────────

    def test_process_empty_features(self, features_service: AgentOSFeatures) -> None:
        """Empty feature list is handled."""
        result = features_service.process_extracted_features([])
        assert result == []
        assert features_service.get_feature_list() == []

    def test_process_features_missing_all_fields(self, features_service: AgentOSFeatures) -> None:
        """Feature with no fields gets safe defaults."""
        result = features_service.process_extracted_features([{}])
        assert len(result) == 1
        assert result[0]["name"] == "Unnamed Feature"
        assert result[0]["priority"] == "should_have"
        assert result[0]["complexity"] == "medium"
        assert result[0]["dependencies"] == []

    def test_self_dependency_int_blocked(self, features_service: AgentOSFeatures) -> None:
        """Integer self-dependency is blocked."""
        result = features_service.process_extracted_features([
            {"name": "Self-ref", "dependencies": [1]},  # ID will be 1
        ])
        assert result[0]["dependencies"] == []

    def test_dependency_on_nonexistent_name_ignored(self, features_service: AgentOSFeatures) -> None:
        """Dependency on a name that doesn't match any feature is silently dropped."""
        result = features_service.process_extracted_features([
            {"name": "A", "dependencies": ["Nonexistent Feature"]},
        ])
        assert result[0]["dependencies"] == []

    def test_duplicate_feature_names(self, features_service: AgentOSFeatures) -> None:
        """Duplicate names map to the later feature's ID for dependencies."""
        result = features_service.process_extracted_features([
            {"name": "Widget", "dependencies": []},
            {"name": "Widget", "dependencies": []},  # Same name
            {"name": "Uses Widget", "dependencies": ["Widget"]},
        ])
        # "Widget" name maps to id=2 (the second one overwrites in name_to_id)
        assert result[2]["dependencies"] == [2]

    def test_gap_analysis_with_empty_features(self, features_service: AgentOSFeatures) -> None:
        """Gap analysis prompt works with no features."""
        prompt = features_service.get_gap_analysis_prompt()
        assert "[]" in prompt  # Empty feature list serializes to []

    def test_update_feature_id_ignored(self, features_service: AgentOSFeatures) -> None:
        """Attempting to update the 'id' field is silently ignored."""
        features_service.add_feature({"name": "Test"})
        result = features_service.update_feature(1, {"id": 999})
        assert result["id"] == 1  # ID unchanged

    def test_gap_severity_invalid_falls_back(self, features_service: AgentOSFeatures) -> None:
        """Invalid severity falls back to 'minor'."""
        gaps = features_service.process_gap_analysis([
            {"type": "test", "severity": "catastrophic", "message": "Bad", "layers": [], "recommendation": "", "confidence": 0.5}
        ])
        assert gaps[0]["severity"] == "minor"

    def test_prompt_survives_braces_in_content(self, tmp_project: Path) -> None:
        """Curly braces in user content don't crash .format() prompt generation."""
        file_utils = AgentOSFileUtils(tmp_project)
        # Write a standards file containing curly braces (common in code specs)
        (tmp_project / "agent-os" / "standards" / "technology-stack.md").write_text(
            "# Tech Stack\n\nUse {userId} as the path param\nConfig: {\"key\": \"value\"}\n"
        )
        # Write a product file with braces
        (tmp_project / ".agent" / "product" / "vision.md").write_text(
            "# Vision\n\nEndpoint format: /api/{resource}/{id}\n"
        )

        entities = {"product_name": "BraceTest", "product_description": "Tests {braces} in content"}
        service = AgentOSFeatures(tmp_project, file_utils, entities, {"auto_select_threshold": 85})

        # These should NOT raise KeyError
        prompt = service.get_feature_extraction_prompt()
        assert "userId" in prompt  # Content preserved (escaped)

        service.process_extracted_features([{"name": "A"}])
        gap_prompt = service.get_gap_analysis_prompt()
        assert "resource" in gap_prompt

    def test_process_extracted_features_resets_ids(self, features_service: AgentOSFeatures) -> None:
        """Calling process_extracted_features twice resets IDs to 1."""
        first = features_service.process_extracted_features([
            {"name": "Alpha"}, {"name": "Beta"},
        ])
        assert first[0]["id"] == 1
        assert first[1]["id"] == 2

        # Second call should reset IDs back to 1
        second = features_service.process_extracted_features([
            {"name": "Gamma"}, {"name": "Delta"}, {"name": "Epsilon"},
        ])
        assert second[0]["id"] == 1
        assert second[1]["id"] == 2
        assert second[2]["id"] == 3
        # Old features should be replaced
        assert len(features_service.get_feature_list()) == 3
        assert features_service.get_feature_by_id(1)["name"] == "Gamma"


# ── TestMechanism ────────────────────────────────────────────────────


class TestMechanism:
    @pytest.fixture
    def mechanism_config(self) -> dict:
        return {
            "mechanism_analysis": {
                "auto_select_threshold": 85,
                "present_alternatives_gap": 15,
                "min_viable_score": 60,
                "max_options_to_evaluate": 4,
            },
            "developers_choice": {
                "enabled": True,
                "bias_toward_standards": 0.3,
                "bias_toward_simplicity": 0.2,
                "bias_toward_adoption": 0.2,
                "bias_toward_docs": 0.1,
            },
        }

    @pytest.fixture
    def mechanism(self, mechanism_config: dict) -> AgentOSMechanism:
        return AgentOSMechanism(mechanism_config, standards_summary="TypeScript, React, REST API")

    def test_analysis_prompt_includes_options(self, mechanism: AgentOSMechanism) -> None:
        """Prompt includes all option names and context."""
        prompt = mechanism.get_analysis_prompt(
            decision_point="Real-time updates",
            options=["WebSocket", "SSE", "Polling"],
            context="Need real-time feature updates",
        )
        assert "WebSocket" in prompt
        assert "SSE" in prompt
        assert "Polling" in prompt
        assert "Real-time updates" in prompt
        assert "Need real-time feature updates" in prompt
        assert "TypeScript" in prompt  # standards_summary

    def test_process_analysis_determines_recommendation(self, mechanism: AgentOSMechanism) -> None:
        """Highest-scoring option becomes the recommendation."""
        analysis = mechanism.process_analysis({
            "options": [
                {"name": "WebSocket", "scores": {"complexity": 0.6, "standards_match": 0.8, "scalability": 0.9, "maintainability": 0.7}, "overall_score": 0.75, "pros": ["Fast"], "cons": ["Complex"]},
                {"name": "Polling", "scores": {"complexity": 0.9, "standards_match": 0.5, "scalability": 0.3, "maintainability": 0.8}, "overall_score": 0.625, "pros": ["Simple"], "cons": ["Slow"]},
            ],
            "reasoning": "WebSocket is better for real-time",
        })
        assert analysis["recommended"] == "WebSocket"
        assert analysis["confidence"] == 0.75

    def test_process_analysis_calculates_score_if_missing(self, mechanism: AgentOSMechanism) -> None:
        """If overall_score is 0, it's calculated from criteria averages."""
        analysis = mechanism.process_analysis({
            "options": [
                {"name": "A", "scores": {"complexity": 0.8, "standards_match": 0.8, "scalability": 0.8, "maintainability": 0.8}, "overall_score": 0, "pros": [], "cons": []},
            ],
            "reasoning": "test",
        })
        assert analysis["options"][0]["overall_score"] == pytest.approx(0.8)

    def test_process_analysis_clamps_scores(self, mechanism: AgentOSMechanism) -> None:
        """Scores are clamped to 0.0-1.0."""
        analysis = mechanism.process_analysis({
            "options": [
                {"name": "A", "scores": {"complexity": 1.5, "standards_match": -0.2, "scalability": 0.5, "maintainability": 0.5}, "overall_score": 0.9, "pros": [], "cons": []},
            ],
            "reasoning": "test",
        })
        scores = analysis["options"][0]["scores"]
        assert scores["complexity"] == 1.0
        assert scores["standards_match"] == 0.0

    def test_developers_choice_adjusts_scores(self, mechanism: AgentOSMechanism) -> None:
        """Developer's Choice modifies scores based on biases."""
        options = [
            {"name": "A", "scores": {"complexity": 0.5, "standards_match": 0.5, "scalability": 0.5, "maintainability": 0.5}, "overall_score": 0.5},
            {"name": "B", "scores": {"complexity": 0.9, "standards_match": 0.9, "scalability": 0.3, "maintainability": 0.9}, "overall_score": 0.5},
        ]
        result = mechanism.apply_developers_choice(options)
        # B should rank higher because it scores better on standards_match, complexity (simplicity), and maintainability
        assert result[0]["name"] == "B"
        assert "adjusted_score" in result[0]
        assert result[0]["adjusted_score"] > result[1]["adjusted_score"]

    def test_developers_choice_disabled_no_change(self, mechanism_config: dict) -> None:
        """When disabled, scores are not modified."""
        mechanism_config["developers_choice"]["enabled"] = False
        mechanism = AgentOSMechanism(mechanism_config)
        options = [
            {"name": "A", "scores": {"complexity": 0.5, "standards_match": 0.5, "scalability": 0.5, "maintainability": 0.5}, "overall_score": 0.7},
            {"name": "B", "scores": {"complexity": 0.9, "standards_match": 0.9, "scalability": 0.3, "maintainability": 0.9}, "overall_score": 0.5},
        ]
        result = mechanism.apply_developers_choice(options)
        # Order should not change
        assert result[0]["name"] == "A"
        assert "adjusted_score" not in result[0]

    def test_should_auto_select_above_threshold(self, mechanism: AgentOSMechanism) -> None:
        """Returns True when top score > auto_select_threshold."""
        assert mechanism.should_auto_select({"confidence": 0.9}) is True
        assert mechanism.should_auto_select({"confidence": 0.85}) is True
        assert mechanism.should_auto_select({"confidence": 0.5}) is False

    def test_should_present_alternatives_close_scores(self, mechanism: AgentOSMechanism) -> None:
        """Returns True when top two are within gap threshold."""
        # Gap of 0.05 is within 0.15 threshold
        assert mechanism.should_present_alternatives({
            "options": [{"overall_score": 0.8}, {"overall_score": 0.75}]
        }) is True
        # Gap of 0.3 exceeds threshold
        assert mechanism.should_present_alternatives({
            "options": [{"overall_score": 0.9}, {"overall_score": 0.6}]
        }) is False

    def test_should_present_alternatives_single_option(self, mechanism: AgentOSMechanism) -> None:
        """Returns False when only one option."""
        assert mechanism.should_present_alternatives({"options": [{"overall_score": 0.8}]}) is False

    def test_needs_human_input_all_low(self, mechanism: AgentOSMechanism) -> None:
        """Returns True when all options below min_viable_score."""
        assert mechanism.needs_human_input({
            "options": [{"overall_score": 0.3}, {"overall_score": 0.4}]
        }) is True
        assert mechanism.needs_human_input({
            "options": [{"overall_score": 0.7}, {"overall_score": 0.4}]
        }) is False

    def test_needs_human_input_no_options(self, mechanism: AgentOSMechanism) -> None:
        """Returns True when no options."""
        assert mechanism.needs_human_input({"options": []}) is True

    def test_record_decision_format(self, mechanism: AgentOSMechanism) -> None:
        """Decision log entry matches expected format."""
        analysis = {
            "decision_point": "Real-time mechanism",
            "feature_id": 5,
            "options": [{"name": "WebSocket"}, {"name": "SSE"}],
            "confidence": 0.85,
            "auto_selected": True,
            "reasoning": "Best for real-time",
        }
        decision = mechanism.record_decision(analysis, "WebSocket", "Industry standard")
        assert decision["chosen"] == "WebSocket"
        assert decision["confidence"] == 0.85
        assert decision["auto_selected"] is True
        assert decision["reason"] == "Industry standard"
        assert "SSE" in decision["alternatives"]
        assert "timestamp" in decision

    def test_record_decision_stored(self, mechanism: AgentOSMechanism) -> None:
        """Recorded decisions are stored and retrievable."""
        analysis = {"decision_point": "Test", "options": [], "confidence": 0.5, "auto_selected": False, "reasoning": ""}
        mechanism.record_decision(analysis, "Option A")
        decisions = mechanism.get_all_decisions()
        assert len(decisions) == 1
        assert decisions[0]["chosen"] == "Option A"

    def test_get_decision_log_entry_markdown(self, mechanism: AgentOSMechanism) -> None:
        """Produces valid markdown for decisions.log."""
        decision = {
            "decision_point": "Database choice",
            "feature_id": 3,
            "chosen": "PostgreSQL",
            "confidence": 0.9,
            "auto_selected": True,
            "reason": "Best for relational data",
            "alternatives": ["MongoDB", "SQLite"],
            "timestamp": "2024-01-15T10:00:00+00:00",
        }
        md = mechanism.get_decision_log_entry(decision)
        assert "## [2024-01-15T10:00:00+00:00] Database choice" in md
        assert "**Chosen:** PostgreSQL" in md
        assert "**Confidence:** 90%" in md
        assert "**Auto-selected:** Yes" in md
        assert "**Feature:** #3" in md
        assert "MongoDB, SQLite" in md

    def test_get_all_analyses(self, mechanism: AgentOSMechanism) -> None:
        """get_all_analyses returns all processed analyses."""
        mechanism.process_analysis({
            "options": [{"name": "A", "scores": {"complexity": 0.8, "standards_match": 0.8, "scalability": 0.8, "maintainability": 0.8}, "overall_score": 0.8, "pros": [], "cons": []}],
            "reasoning": "test",
        })
        assert len(mechanism.get_all_analyses()) == 1

    # ── Edge case tests ──────────────────────────────────────────────

    def test_process_analysis_empty_options(self, mechanism: AgentOSMechanism) -> None:
        """Empty options list returns 'None' as recommended."""
        analysis = mechanism.process_analysis({"options": [], "reasoning": "nothing"})
        assert analysis["recommended"] == "None"
        assert analysis["confidence"] == 0.0

    def test_process_analysis_missing_scores(self, mechanism: AgentOSMechanism) -> None:
        """Options with missing scores get defaults of 0.5."""
        analysis = mechanism.process_analysis({
            "options": [{"name": "A", "scores": {}, "overall_score": 0, "pros": [], "cons": []}],
            "reasoning": "test",
        })
        scores = analysis["options"][0]["scores"]
        assert all(v == 0.5 for v in scores.values())

    def test_developers_choice_biases_exceed_1(self) -> None:
        """When bias weights sum > 1, raw_weight is clamped to 0."""
        config = {
            "developers_choice": {
                "enabled": True,
                "bias_toward_standards": 0.5,
                "bias_toward_simplicity": 0.3,
                "bias_toward_adoption": 0.3,
                "bias_toward_docs": 0.2,
            },
        }
        mechanism = AgentOSMechanism(config)
        options = [
            {"name": "A", "scores": {"complexity": 0.5, "standards_match": 0.5, "scalability": 0.5, "maintainability": 0.5}, "overall_score": 0.9},
        ]
        result = mechanism.apply_developers_choice(options)
        # Should not crash even with biases summing to 1.3
        assert "adjusted_score" in result[0]
        assert result[0]["adjusted_score"] >= 0

    def test_record_decision_without_reason(self, mechanism: AgentOSMechanism) -> None:
        """Recording a decision with no reason uses analysis reasoning."""
        analysis = {"decision_point": "Test", "options": [], "confidence": 0.7, "auto_selected": False, "reasoning": "Fallback reason"}
        decision = mechanism.record_decision(analysis, "X")
        assert decision["reason"] == "Fallback reason"

    def test_decision_point_from_process_analysis(self, mechanism: AgentOSMechanism) -> None:
        """decision_point passed to process_analysis is preserved in result."""
        analysis = mechanism.process_analysis(
            {"options": [{"name": "A", "scores": {}, "overall_score": 0.8, "pros": [], "cons": []}], "reasoning": "test"},
            decision_point="Authentication method",
        )
        assert analysis["decision_point"] == "Authentication method"
        decision = mechanism.record_decision(analysis, "A")
        assert decision["decision_point"] == "Authentication method"
