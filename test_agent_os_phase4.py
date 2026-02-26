"""
Tests for Phase 4: Spec Generation & Database Population (Handoff)
"""

from pathlib import Path

import pytest

from server.services.agent_os_features import AgentOSFeatures
from server.services.agent_os_file_utils import AgentOSFileUtils
from server.services.agent_os_handoff import AgentOSHandoff
from server.services.agent_os_mechanism import AgentOSMechanism
from server.services.agent_os_specs import AgentOSSpecs, _slugify

# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory with all layers populated."""
    # Standards
    standards_dir = tmp_path / "agent-os" / "standards"
    standards_dir.mkdir(parents=True)
    (standards_dir / "technology-stack.md").write_text("# Technology Stack\n\n## Languages\nTypeScript\n")

    # Product
    product_dir = tmp_path / ".agent" / "product"
    product_dir.mkdir(parents=True)
    (product_dir / "vision.md").write_text("# Vision\n\n## Core Purpose\nA task management app\n")

    # Specs dir
    (tmp_path / ".agent" / "specs").mkdir(parents=True, exist_ok=True)

    # .autoforge dir for features.db
    (tmp_path / ".autoforge").mkdir(parents=True, exist_ok=True)

    return tmp_path


@pytest.fixture
def file_utils(tmp_project: Path) -> AgentOSFileUtils:
    return AgentOSFileUtils(tmp_project)


@pytest.fixture
def features_service(tmp_project: Path, file_utils: AgentOSFileUtils) -> AgentOSFeatures:
    entities = {
        "product_name": "TaskFlow",
        "product_description": "A task management app",
        "core_features": ["task creation", "notifications"],
    }
    config = {"auto_select_threshold": 85}
    service = AgentOSFeatures(tmp_project, file_utils, entities, config)
    # Pre-populate features
    service.process_extracted_features([
        {"name": "User Auth", "description": "Login system", "priority": "must_have", "complexity": "medium", "category": "auth", "dependencies": [], "source": "vision.md"},
        {"name": "Task CRUD", "description": "Create and manage tasks", "priority": "must_have", "complexity": "medium", "category": "data", "dependencies": ["User Auth"], "source": "vision.md"},
        {"name": "Notifications", "description": "Email alerts", "priority": "should_have", "complexity": "small", "category": "integration", "dependencies": ["Task CRUD"], "source": "entities"},
        {"name": "Dark Mode", "description": "Theme toggle", "priority": "nice_to_have", "complexity": "small", "category": "ui", "dependencies": [], "source": "ux"},
    ])
    return service


@pytest.fixture
def mechanism_service() -> AgentOSMechanism:
    config = {
        "mechanism_analysis": {"auto_select_threshold": 85, "present_alternatives_gap": 15, "min_viable_score": 60},
        "developers_choice": {"enabled": True, "bias_toward_standards": 0.3, "bias_toward_simplicity": 0.2, "bias_toward_adoption": 0.2, "bias_toward_docs": 0.1},
    }
    return AgentOSMechanism(config, standards_summary="TypeScript, React")


@pytest.fixture
def specs_service(tmp_project: Path, file_utils: AgentOSFileUtils, features_service: AgentOSFeatures, mechanism_service: AgentOSMechanism) -> AgentOSSpecs:
    return AgentOSSpecs(
        tmp_project, file_utils, features_service, mechanism_service,
        standards_summary="TypeScript, React, REST API",
        product_summary="TaskFlow - a task management app for developers",
    )


@pytest.fixture
def sample_spec_content() -> str:
    return """# Feature 1: User Auth

## Overview
Login and signup system for user authentication.

## Requirements
### Functional
1. Users can sign up with email and password
2. Users can log in with credentials
3. Users can reset their password

### Technical
1. JWT-based authentication
2. Bcrypt password hashing
3. Rate limiting on login attempts

## User Stories
- As a developer, I want to create an account so that I can manage my tasks
- As a user, I want to log in securely so that my data is protected

## Acceptance Criteria
- [ ] Users can register with valid email and password
- [ ] Users can log in and receive a JWT token
- [ ] Invalid credentials return appropriate error
- [ ] Password reset via email works
- [ ] Rate limiting prevents brute force attacks

## Technical Specification
- **API Endpoints:** POST /auth/register, POST /auth/login, POST /auth/reset
- **Data Models:** User { id, email, password_hash, created_at }
- **Components:** LoginForm, RegisterForm, ResetPasswordForm
- **Dependencies:** None
- **Edge Cases:** Duplicate email, expired tokens, rate limit exceeded

## Standards References
- See technology-stack.md for TypeScript standards
- See architecture-patterns.md for JWT authentication pattern

## Success Metrics
Users can register, log in, and reset passwords without errors.
"""


# ── TestSpecs ────────────────────────────────────────────────────────


class TestSpecs:
    def test_spec_generation_prompt_includes_feature(self, specs_service: AgentOSSpecs, features_service: AgentOSFeatures) -> None:
        """Prompt includes feature name, description, and context."""
        feature = features_service.get_feature_by_id(1)
        prompt = specs_service.get_spec_generation_prompt(feature)
        assert "User Auth" in prompt
        assert "Login system" in prompt
        assert "must_have" in prompt
        assert "TaskFlow" in prompt  # product summary
        assert "TypeScript" in prompt  # standards

    def test_spec_generation_prompt_includes_all_features(self, specs_service: AgentOSSpecs, features_service: AgentOSFeatures) -> None:
        """Prompt includes all features for cross-referencing."""
        feature = features_service.get_feature_by_id(2)
        prompt = specs_service.get_spec_generation_prompt(feature)
        assert "User Auth" in prompt  # Other feature listed
        assert "Task CRUD" in prompt
        assert "Notifications" in prompt

    def test_spec_generation_prompt_includes_deps(self, specs_service: AgentOSSpecs, features_service: AgentOSFeatures) -> None:
        """Prompt includes dependency names."""
        feature = features_service.get_feature_by_id(2)  # Task CRUD depends on User Auth
        prompt = specs_service.get_spec_generation_prompt(feature)
        assert "#1 User Auth" in prompt

    def test_process_generated_spec_writes_file(self, specs_service: AgentOSSpecs, tmp_project: Path, sample_spec_content: str) -> None:
        """Spec is written to .agent/specs/ with correct filename."""
        path = specs_service.process_generated_spec(1, sample_spec_content)
        assert path.exists()
        assert path.name == "feature-001-user-auth.md"
        assert (tmp_project / ".agent" / "specs" / "feature-001-user-auth.md").exists()

    def test_spec_filename_format(self, specs_service: AgentOSSpecs) -> None:
        """Filename is feature-001-name-slug.md format."""
        assert specs_service.get_spec_filename(1, "User Auth") == "feature-001-user-auth.md"
        assert specs_service.get_spec_filename(12, "Real-Time Notifications") == "feature-012-real-time-notifications.md"
        assert specs_service.get_spec_filename(100, "Some Feature") == "feature-100-some-feature.md"

    def test_slugify_long_name(self) -> None:
        """Slug is truncated to 30 chars."""
        slug = _slugify("This Is A Very Long Feature Name That Exceeds The Limit")
        assert len(slug) <= 30
        assert slug == "this-is-a-very-long-feature-na"

    def test_slugify_special_chars(self) -> None:
        """Special characters are replaced with hyphens."""
        assert _slugify("Auth & Login (v2)") == "auth-login-v2"

    def test_validate_spec_passes(self, specs_service: AgentOSSpecs, sample_spec_content: str) -> None:
        """A valid spec passes all checks."""
        specs_service.process_generated_spec(1, sample_spec_content)
        report = specs_service.validate_spec(1)
        assert report["valid"] is True
        # May have minor issues but no errors
        error_issues = [i for i in report["issues"] if i["severity"] == "error"]
        assert len(error_issues) == 0

    def test_validate_spec_catches_missing_user_stories(self, specs_service: AgentOSSpecs) -> None:
        """Validation flags specs without user stories."""
        bare_spec = "# Feature 1: Test\n\n## Overview\nTest\n\n## Acceptance Criteria\n- [ ] Criterion 1\n- [ ] Criterion 2\n" + "\n".join(f"Line {i}" for i in range(20))
        specs_service.process_generated_spec(1, bare_spec)
        report = specs_service.validate_spec(1)
        messages = [i["message"] for i in report["issues"]]
        assert any("user stories" in m.lower() for m in messages)

    def test_validate_spec_catches_missing_acceptance_criteria(self, specs_service: AgentOSSpecs) -> None:
        """Validation flags specs with fewer than 2 acceptance criteria."""
        bare_spec = "# Feature 1: Test\n\n## Overview\nTest\n\n## User Stories\n- As a user, I want to test\n\n## Acceptance Criteria\n- [ ] Only one\n" + "\n".join(f"Line {i}" for i in range(20))
        specs_service.process_generated_spec(1, bare_spec)
        report = specs_service.validate_spec(1)
        messages = [i["message"] for i in report["issues"]]
        assert any("acceptance criteria" in m.lower() for m in messages)

    def test_validate_spec_catches_too_short(self, specs_service: AgentOSSpecs) -> None:
        """Validation flags specs shorter than 20 lines."""
        short_spec = "# Feature 1: Test\n\n## Overview\nShort\n\n- As a user, I want to test\n- [ ] A\n- [ ] B\n"
        specs_service.process_generated_spec(1, short_spec)
        report = specs_service.validate_spec(1)
        messages = [i["message"] for i in report["issues"]]
        assert any("too short" in m.lower() for m in messages)

    def test_validate_spec_no_content(self, specs_service: AgentOSSpecs) -> None:
        """Validation reports error when no spec content found."""
        report = specs_service.validate_spec(999)
        assert report["valid"] is False
        assert any(i["severity"] == "error" for i in report["issues"])

    def test_get_spec_content(self, specs_service: AgentOSSpecs, sample_spec_content: str) -> None:
        """Can retrieve spec content after generation."""
        specs_service.process_generated_spec(1, sample_spec_content)
        content = specs_service.get_spec_content(1)
        assert content == sample_spec_content
        assert specs_service.get_spec_content(999) is None

    def test_get_all_specs(self, specs_service: AgentOSSpecs, sample_spec_content: str) -> None:
        """get_all_specs returns feature_id → path mapping."""
        specs_service.process_generated_spec(1, sample_spec_content)
        specs_service.process_generated_spec(2, "# Feature 2: Task CRUD\n\nContent here")
        all_specs = specs_service.get_all_specs()
        assert 1 in all_specs
        assert 2 in all_specs

    def test_regenerate_prompt_includes_feedback(self, specs_service: AgentOSSpecs, sample_spec_content: str) -> None:
        """Regeneration prompt includes original spec and user feedback."""
        specs_service.process_generated_spec(1, sample_spec_content)
        prompt = specs_service.regenerate_spec(1, "Add OAuth support")
        assert "Add OAuth support" in prompt
        assert "User Auth" in prompt  # Original spec content

    def test_quality_report_stored(self, specs_service: AgentOSSpecs, sample_spec_content: str) -> None:
        """Quality report is stored and retrievable."""
        specs_service.process_generated_spec(1, sample_spec_content)
        specs_service.validate_spec(1)
        report = specs_service.get_quality_report(1)
        assert "valid" in report


# ── TestHandoff ──────────────────────────────────────────────────────


class TestHandoff:
    @pytest.fixture
    def handoff_service(self, tmp_project: Path, file_utils: AgentOSFileUtils, features_service: AgentOSFeatures, mechanism_service: AgentOSMechanism, specs_service: AgentOSSpecs, sample_spec_content: str) -> AgentOSHandoff:
        # Generate specs for all features
        specs_service.process_generated_spec(1, sample_spec_content)
        specs_service.process_generated_spec(2, "# Feature 2: Task CRUD\n\n## Acceptance Criteria\n- [ ] Create tasks\n- [ ] Read tasks\n- [ ] Update tasks\n")
        specs_service.process_generated_spec(3, "# Feature 3: Notifications\n\n## Acceptance Criteria\n- [ ] Send email\n")
        specs_service.process_generated_spec(4, "# Feature 4: Dark Mode\n\n## Acceptance Criteria\n- [ ] Toggle theme\n")
        return AgentOSHandoff(tmp_project, file_utils, features_service, specs_service, mechanism=mechanism_service)

    def test_populate_features_db_creates_rows(self, handoff_service: AgentOSHandoff, tmp_project: Path) -> None:
        """Features are created in the database with correct fields."""
        db_path = tmp_project / ".autoforge" / "features.db"
        count = handoff_service.populate_features_db(db_path=db_path)
        assert count == 4
        assert db_path.exists()

        # Verify database contents
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from api.database import Feature

        engine = create_engine(f"sqlite:///{db_path.as_posix()}")
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        features = session.query(Feature).all()
        assert len(features) == 4
        session.close()

    def test_populate_features_db_maps_priority(self, handoff_service: AgentOSHandoff, tmp_project: Path) -> None:
        """must_have=1, should_have=2, nice_to_have=3."""
        db_path = tmp_project / ".autoforge" / "features.db"
        handoff_service.populate_features_db(db_path=db_path)

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from api.database import Feature

        engine = create_engine(f"sqlite:///{db_path.as_posix()}")
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        auth = session.query(Feature).filter(Feature.name == "User Auth").first()
        assert auth.priority == 1  # must_have

        notif = session.query(Feature).filter(Feature.name == "Notifications").first()
        assert notif.priority == 2  # should_have

        dark = session.query(Feature).filter(Feature.name == "Dark Mode").first()
        assert dark.priority == 3  # nice_to_have

        session.close()

    def test_steps_extracted_from_spec(self, handoff_service: AgentOSHandoff, tmp_project: Path) -> None:
        """Acceptance criteria are parsed from spec markdown into steps field."""
        db_path = tmp_project / ".autoforge" / "features.db"
        handoff_service.populate_features_db(db_path=db_path)

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from api.database import Feature

        engine = create_engine(f"sqlite:///{db_path.as_posix()}")
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        auth = session.query(Feature).filter(Feature.name == "User Auth").first()
        # The sample_spec_content has 5 acceptance criteria
        assert isinstance(auth.steps, list)
        assert len(auth.steps) == 5

        task = session.query(Feature).filter(Feature.name == "Task CRUD").first()
        assert isinstance(task.steps, list)
        assert len(task.steps) == 3
        assert "Create tasks" in task.steps[0]

        session.close()

    def test_generate_dependency_graph_valid(self, handoff_service: AgentOSHandoff) -> None:
        """Valid acyclic graph is accepted."""
        result = handoff_service.generate_dependency_graph()
        assert result["valid"] is True
        assert result["cycle_info"] is None
        assert result["edges"] > 0

    def test_validate_dependency_graph(self, handoff_service: AgentOSHandoff) -> None:
        """validate_dependency_graph returns same result as generate."""
        result = handoff_service.validate_dependency_graph()
        assert result["valid"] is True

    def test_calculate_build_order_respects_deps(self, handoff_service: AgentOSHandoff) -> None:
        """Build order puts dependencies before dependents."""
        order = handoff_service.calculate_build_order()
        assert len(order) == 4
        # User Auth (1) must come before Task CRUD (2)
        assert order.index(1) < order.index(2)
        # Task CRUD (2) must come before Notifications (3)
        assert order.index(2) < order.index(3)

    def test_generate_scope_boundary(self, handoff_service: AgentOSHandoff, tmp_project: Path) -> None:
        """Scope boundary file is created with MVP/next/future sections."""
        path = handoff_service.generate_scope_boundary()
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "## IN SCOPE" in content
        assert "## NEXT PHASE" in content
        assert "## FUTURE" in content
        assert "User Auth" in content
        assert "Task CRUD" in content
        assert "Notifications" in content  # should_have → NEXT PHASE
        assert "Dark Mode" in content  # nice_to_have → FUTURE
        assert "## QUALITY BOUNDARY" in content
        assert "## STOP SIGNALS" in content

    def test_assemble_handoff_reports_missing(self, tmp_project: Path, file_utils: AgentOSFileUtils, features_service: AgentOSFeatures) -> None:
        """Handoff reports missing components."""
        # Create a handoff with no specs generated
        mech = AgentOSMechanism({})
        specs = AgentOSSpecs(tmp_project, file_utils, features_service, mech)
        handoff = AgentOSHandoff(tmp_project, file_utils, features_service, specs)

        result = handoff.assemble_handoff_package()
        assert result["ready"] is False
        assert "features.db" in result["missing"]

    def test_assemble_handoff_complete(self, handoff_service: AgentOSHandoff, tmp_project: Path) -> None:
        """With all pieces present, handoff reports ready."""
        # Populate DB
        db_path = tmp_project / ".autoforge" / "features.db"
        handoff_service.populate_features_db(db_path=db_path)
        # Generate scope boundary
        handoff_service.generate_scope_boundary()
        # Generate context primer
        handoff_service.generate_context_primer()

        result = handoff_service.assemble_handoff_package()
        assert result["ready"] is True
        assert result["missing"] == []
        assert result["feature_count"] == 4
        assert result["estimated_sessions"] == 2  # ceil(4/3) = 2

    def test_build_plan_summary_readable(self, handoff_service: AgentOSHandoff) -> None:
        """Build plan summary is non-empty human-readable text."""
        summary = handoff_service.get_build_plan_summary()
        assert len(summary) > 0
        assert "Build Plan Summary" in summary
        assert "User Auth" in summary
        assert "Total features" in summary
        assert "Estimated sessions" in summary
        assert "Must-have" in summary

    def test_build_plan_summary_empty(self, tmp_project: Path, file_utils: AgentOSFileUtils) -> None:
        """Empty feature list returns appropriate message."""
        empty_features = AgentOSFeatures(tmp_project, file_utils, {}, {})
        mech = AgentOSMechanism({})
        specs = AgentOSSpecs(tmp_project, file_utils, empty_features, mech)
        handoff = AgentOSHandoff(tmp_project, file_utils, empty_features, specs)
        summary = handoff.get_build_plan_summary()
        assert "No features" in summary

    def test_generate_context_primer_creates_file(self, handoff_service: AgentOSHandoff, tmp_project: Path) -> None:
        """Context primer is written to .agent/knowledge/context-primer.md."""
        path = handoff_service.generate_context_primer()
        assert path.exists()
        assert path.name == "context-primer.md"
        assert (tmp_project / ".agent" / "knowledge" / "context-primer.md").exists()

    def test_context_primer_includes_standards(self, handoff_service: AgentOSHandoff) -> None:
        """Context primer includes standards layer summary."""
        path = handoff_service.generate_context_primer()
        content = path.read_text(encoding="utf-8")
        assert "## Standards Summary" in content
        assert "TypeScript" in content

    def test_context_primer_includes_product(self, handoff_service: AgentOSHandoff) -> None:
        """Context primer includes product layer summary."""
        path = handoff_service.generate_context_primer()
        content = path.read_text(encoding="utf-8")
        assert "## Product Vision" in content
        assert "task management" in content.lower()

    def test_context_primer_includes_features(self, handoff_service: AgentOSHandoff) -> None:
        """Context primer includes feature overview with counts and names."""
        path = handoff_service.generate_context_primer()
        content = path.read_text(encoding="utf-8")
        assert "## Feature Overview" in content
        assert "User Auth" in content
        assert "Task CRUD" in content
        assert "must-have" in content
        assert "should-have" in content

    def test_context_primer_includes_build_order(self, handoff_service: AgentOSHandoff) -> None:
        """Context primer includes build order section."""
        path = handoff_service.generate_context_primer()
        content = path.read_text(encoding="utf-8")
        assert "## Build Order" in content
        # User Auth should appear in build order
        assert "User Auth" in content

    def test_context_primer_includes_spec_index(self, handoff_service: AgentOSHandoff) -> None:
        """Context primer includes an index of all generated specs."""
        path = handoff_service.generate_context_primer()
        content = path.read_text(encoding="utf-8")
        assert "## Spec Index" in content
        assert ".agent/specs/" in content

    def test_context_primer_includes_decisions(self, handoff_service: AgentOSHandoff, mechanism_service: AgentOSMechanism) -> None:
        """Context primer includes mechanism decisions when present."""
        # Record a decision on the mechanism service
        analysis = {
            "decision_point": "Authentication method",
            "feature_id": 1,
            "options": [{"name": "JWT"}, {"name": "Session cookies"}],
            "confidence": 0.9,
            "auto_selected": True,
            "reasoning": "JWT is standard for SPAs",
        }
        mechanism_service.record_decision(analysis, "JWT", "Industry standard for SPAs")

        path = handoff_service.generate_context_primer()
        content = path.read_text(encoding="utf-8")
        assert "## Key Decisions" in content
        assert "Authentication method" in content
        assert "JWT" in content
        assert "90%" in content

    def test_context_primer_no_decisions(self, tmp_project: Path, file_utils: AgentOSFileUtils, features_service: AgentOSFeatures) -> None:
        """Context primer handles no decisions gracefully."""
        mech = AgentOSMechanism({})
        specs = AgentOSSpecs(tmp_project, file_utils, features_service, mech)
        handoff = AgentOSHandoff(tmp_project, file_utils, features_service, specs, mechanism=mech)
        path = handoff.generate_context_primer()
        content = path.read_text(encoding="utf-8")
        assert "No mechanism decisions recorded" in content

    def test_context_primer_no_mechanism(self, tmp_project: Path, file_utils: AgentOSFileUtils, features_service: AgentOSFeatures) -> None:
        """Context primer handles missing mechanism service gracefully."""
        mech = AgentOSMechanism({})
        specs = AgentOSSpecs(tmp_project, file_utils, features_service, mech)
        handoff = AgentOSHandoff(tmp_project, file_utils, features_service, specs)  # No mechanism
        path = handoff.generate_context_primer()
        content = path.read_text(encoding="utf-8")
        assert "No mechanism decisions recorded" in content

    def test_assemble_handoff_reports_missing_primer(self, handoff_service: AgentOSHandoff, tmp_project: Path) -> None:
        """Handoff reports missing context primer when not generated."""
        db_path = tmp_project / ".autoforge" / "features.db"
        handoff_service.populate_features_db(db_path=db_path)
        handoff_service.generate_scope_boundary()
        # Don't generate context primer
        result = handoff_service.assemble_handoff_package()
        assert result["ready"] is False
        assert "context-primer.md" in result["missing"]

    def test_handoff_status(self, handoff_service: AgentOSHandoff, tmp_project: Path) -> None:
        """Handoff status tracks all steps."""
        status = handoff_service.get_handoff_status()
        assert status["features_db_populated"] is False
        assert status["context_primer_generated"] is False
        assert status["handoff_complete"] is False

        db_path = tmp_project / ".autoforge" / "features.db"
        handoff_service.populate_features_db(db_path=db_path)
        status = handoff_service.get_handoff_status()
        assert status["features_db_populated"] is True

        handoff_service.generate_scope_boundary()
        status = handoff_service.get_handoff_status()
        assert status["scope_boundary_generated"] is True

        handoff_service.generate_context_primer()
        status = handoff_service.get_handoff_status()
        assert status["context_primer_generated"] is True

    def test_feature_to_db_row_mapping(self, handoff_service: AgentOSHandoff) -> None:
        """Verify the feature → DB row mapping logic."""
        feature = {"id": 1, "name": "Test", "description": "Test desc", "priority": "must_have", "category": "auth"}
        row = handoff_service._feature_to_db_row(feature)
        assert row["priority"] == 1
        assert row["name"] == "Test"
        assert row["description"] == "Test desc"
        assert row["category"] == "auth"

    def test_feature_to_db_row_default_priority(self, handoff_service: AgentOSHandoff) -> None:
        """Unknown priority maps to 2."""
        feature = {"id": 1, "name": "Test", "description": "", "priority": "unknown", "category": "general"}
        row = handoff_service._feature_to_db_row(feature)
        assert row["priority"] == 2
