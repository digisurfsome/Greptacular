"""
Agent OS Phase 5 — Router & Session Integration Tests
======================================================

Tests for:
- AgentOSSession lifecycle (create, stage progression, messages)
- Session registry (create, get, list, remove)
- AgentOSFileUtils integration
- Stage handler logic

Run with: python -m pytest test_agent_os_phase5.py -v
"""

import asyncio
from pathlib import Path

import pytest

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture()
def tmp_project(tmp_path: Path):
    """Create a temporary project directory with Agent OS structure."""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    # Create minimal Agent OS directory structure
    (project_dir / "agent-os" / "standards").mkdir(parents=True)
    (project_dir / ".agent" / "product").mkdir(parents=True)
    (project_dir / ".agent" / "specs").mkdir(parents=True)
    (project_dir / ".agent" / "settings").mkdir(parents=True)
    (project_dir / ".agent" / "knowledge").mkdir(parents=True)
    return project_dir


# ============================================================================
# AgentOSFileUtils Tests
# ============================================================================


class TestFileUtils:
    def test_ensure_agent_os_dirs(self, tmp_project: Path):
        """ensure_agent_os_dirs creates all required directories."""
        from server.services.agent_os_file_utils import AgentOSFileUtils

        fu = AgentOSFileUtils(tmp_project)
        fu.ensure_agent_os_dirs()

        assert (tmp_project / "agent-os" / "standards").is_dir()
        assert (tmp_project / ".agent" / "product").is_dir()
        assert (tmp_project / ".agent" / "specs").is_dir()

    def test_write_and_read_standards_file(self, tmp_project: Path):
        """Write then read a standards file."""
        from server.services.agent_os_file_utils import AgentOSFileUtils

        fu = AgentOSFileUtils(tmp_project)
        fu.ensure_agent_os_dirs()

        fu.write_standards_file("tech.md", "# Tech Stack\nPython 3.11")
        content = fu.read_standards_file("tech.md")
        assert content is not None
        assert "Python 3.11" in content

    def test_write_and_read_product_file(self, tmp_project: Path):
        """Write then read a product file."""
        from server.services.agent_os_file_utils import AgentOSFileUtils

        fu = AgentOSFileUtils(tmp_project)
        fu.ensure_agent_os_dirs()

        fu.write_product_file("vision.md", "# Vision\nBuild great things")
        content = fu.read_product_file("vision.md")
        assert content is not None
        assert "great things" in content

    def test_list_files_in_layer(self, tmp_project: Path):
        """List files returns entries for written files."""
        from server.services.agent_os_file_utils import AgentOSFileUtils

        fu = AgentOSFileUtils(tmp_project)
        fu.ensure_agent_os_dirs()

        fu.write_standards_file("naming.md", "# Naming\nUse snake_case")
        files = fu.list_files_in_layer("standards")
        names = [f["name"] for f in files]
        assert "naming.md" in names

    def test_read_nonexistent_file_returns_none(self, tmp_project: Path):
        """Reading a nonexistent file returns None."""
        from server.services.agent_os_file_utils import AgentOSFileUtils

        fu = AgentOSFileUtils(tmp_project)
        assert fu.read_standards_file("nope.md") is None
        assert fu.read_product_file("nope.md") is None


# ============================================================================
# AgentOSSession Tests
# ============================================================================


class TestSessionLifecycle:
    def test_session_creation(self, tmp_project: Path):
        """Session initializes with correct defaults."""
        from server.services.agent_os_session import AgentOSSession

        session = AgentOSSession("test-project", tmp_project)
        assert session.current_stage == "intake"
        assert session.current_stage_index == 0
        assert session.is_complete() is False
        assert session.get_messages() == []

    def test_advance_stage(self, tmp_project: Path):
        """advance_stage moves through stages sequentially."""
        from server.services.agent_os_session import AgentOSSession

        session = AgentOSSession("test-project", tmp_project)
        assert session.current_stage == "intake"

        session.advance_stage()
        assert session.current_stage == "standards"
        assert session.current_stage_index == 1

        session.advance_stage()
        assert session.current_stage == "product_discovery"
        assert session.current_stage_index == 2

    def test_advance_stage_stops_at_end(self, tmp_project: Path):
        """advance_stage doesn't go past the last stage."""
        from server.services.agent_os_session import AgentOSSession

        session = AgentOSSession("test-project", tmp_project)
        # Advance through all stages
        for _ in range(20):
            session.advance_stage()
        assert session.current_stage == "handoff"
        assert session.current_stage_index == 7

    def test_get_progress(self, tmp_project: Path):
        """get_progress returns correct state."""
        from server.services.agent_os_session import AgentOSSession

        session = AgentOSSession("test-project", tmp_project)
        progress = session.get_progress()
        assert progress["current_stage"] == "intake"
        assert progress["stage_index"] == 0
        assert progress["total_stages"] == 8

    def test_stages_list(self, tmp_project: Path):
        """STAGES constant is the 8-stage pipeline."""
        from server.services.agent_os_session import AgentOSSession

        assert len(AgentOSSession.STAGES) == 8
        assert AgentOSSession.STAGES[0] == "intake"
        assert AgentOSSession.STAGES[-1] == "handoff"

    def test_process_message_intake(self, tmp_project: Path):
        """process_message on intake stage returns events."""
        from server.services.agent_os_session import AgentOSSession

        session = AgentOSSession("test-project", tmp_project)

        events = []
        async def collect():
            async for event in session.process_message("I want to build a task app"):
                events.append(event)

        asyncio.get_event_loop().run_until_complete(collect())

        assert len(events) > 0
        # Should have at least a message event
        types = [e["type"] for e in events]
        assert "message" in types or "progress" in types

    def test_process_message_records_user_message(self, tmp_project: Path):
        """User messages are recorded in session history."""
        from server.services.agent_os_session import AgentOSSession

        session = AgentOSSession("test-project", tmp_project)

        async def send():
            async for _ in session.process_message("test input"):
                pass

        asyncio.get_event_loop().run_until_complete(send())

        messages = session.get_messages()
        user_msgs = [m for m in messages if m["role"] == "user"]
        assert len(user_msgs) >= 1
        assert user_msgs[0]["content"] == "test input"

    def test_approve_advances_intake_to_standards(self, tmp_project: Path):
        """Sending __approve__ in intake stage advances to standards."""
        from server.services.agent_os_session import AgentOSSession

        session = AgentOSSession("test-project", tmp_project)
        assert session.current_stage == "intake"

        events = []
        async def approve():
            async for event in session.process_message("__approve__"):
                events.append(event)

        asyncio.get_event_loop().run_until_complete(approve())

        stage_changes = [e for e in events if e["type"] == "stage_change"]
        assert len(stage_changes) == 1
        assert stage_changes[0]["stage"] == "standards"


# ============================================================================
# Session Registry Tests
# ============================================================================


class TestSessionRegistry:
    def test_create_and_get_session(self, tmp_project: Path):
        """Create a session then retrieve it."""
        from server.services.agent_os_session import (
            _sessions,
            create_session,
            get_session,
        )

        # Clean up any leftover sessions
        _sessions.clear()

        session = create_session("test-proj", tmp_project)
        assert session is not None
        assert session.project_name == "test-proj"

        retrieved = get_session("test-proj")
        assert retrieved is session

        _sessions.clear()

    def test_list_sessions(self, tmp_project: Path):
        """List returns active session names."""
        from server.services.agent_os_session import (
            _sessions,
            create_session,
            list_sessions,
        )

        _sessions.clear()

        create_session("proj-a", tmp_project)
        create_session("proj-b", tmp_project)

        names = list_sessions()
        assert "proj-a" in names
        assert "proj-b" in names
        assert len(names) == 2

        _sessions.clear()

    def test_remove_session(self, tmp_project: Path):
        """Remove deletes the session."""
        from server.services.agent_os_session import (
            _sessions,
            create_session,
            get_session,
            remove_session,
        )

        _sessions.clear()

        create_session("remove-me", tmp_project)
        assert get_session("remove-me") is not None

        asyncio.get_event_loop().run_until_complete(remove_session("remove-me"))
        assert get_session("remove-me") is None

        _sessions.clear()

    def test_create_session_replaces_existing(self, tmp_project: Path):
        """Creating a session for an existing project replaces it."""
        from server.services.agent_os_session import (
            _sessions,
            create_session,
            get_session,
        )

        _sessions.clear()

        s1 = create_session("replace-me", tmp_project)
        s2 = create_session("replace-me", tmp_project)
        assert s1 is not s2
        assert get_session("replace-me") is s2

        _sessions.clear()

    def test_get_nonexistent_session_returns_none(self):
        """Getting a nonexistent session returns None."""
        from server.services.agent_os_session import _sessions, get_session

        _sessions.clear()
        assert get_session("doesnt-exist") is None

    def test_cleanup_all(self, tmp_project: Path):
        """cleanup_all_agent_os_sessions clears everything."""
        from server.services.agent_os_session import (
            _sessions,
            cleanup_all_agent_os_sessions,
            create_session,
            list_sessions,
        )

        _sessions.clear()

        create_session("a", tmp_project)
        create_session("b", tmp_project)
        assert len(list_sessions()) == 2

        asyncio.get_event_loop().run_until_complete(cleanup_all_agent_os_sessions())
        assert len(list_sessions()) == 0


# ============================================================================
# Feature Service Integration
# ============================================================================


class TestFeaturesIntegration:
    def test_add_and_list_features(self, tmp_project: Path):
        """AgentOSFeatures add_feature and get_feature_list work."""
        from server.services.agent_os_features import AgentOSFeatures
        from server.services.agent_os_file_utils import AgentOSFileUtils

        fu = AgentOSFileUtils(tmp_project)
        features = AgentOSFeatures(tmp_project, fu, entities={}, config={})

        features.add_feature({
            "name": "User Auth",
            "description": "Login and registration",
            "priority": "must_have",
        })
        features.add_feature({
            "name": "Dashboard",
            "description": "Main dashboard view",
            "priority": "should_have",
        })

        feature_list = features.get_feature_list()
        assert len(feature_list) == 2
        # must_have sorted first
        assert feature_list[0]["name"] == "User Auth"

    def test_remove_feature(self, tmp_project: Path):
        """remove_feature deletes and cleans dependencies."""
        from server.services.agent_os_features import AgentOSFeatures
        from server.services.agent_os_file_utils import AgentOSFileUtils

        fu = AgentOSFileUtils(tmp_project)
        features = AgentOSFeatures(tmp_project, fu, entities={}, config={})

        features.add_feature({"name": "Base", "description": "Base layer"})
        features.add_feature({"name": "Dep", "description": "Depends on base", "dependencies": [1]})

        assert features.remove_feature(1) is True
        remaining = features.get_feature_list()
        assert len(remaining) == 1
        # Dependency reference should be cleaned
        assert 1 not in remaining[0].get("dependencies", [])

    def test_update_feature(self, tmp_project: Path):
        """update_feature modifies fields."""
        from server.services.agent_os_features import AgentOSFeatures
        from server.services.agent_os_file_utils import AgentOSFileUtils

        fu = AgentOSFileUtils(tmp_project)
        features = AgentOSFeatures(tmp_project, fu, entities={}, config={})

        features.add_feature({"name": "Auth", "description": "Login"})
        updated = features.update_feature(1, {"name": "Authentication"})
        assert updated is not None
        assert updated["name"] == "Authentication"


# ============================================================================
# Router Module Syntax Check
# ============================================================================


class TestRouterSyntax:
    def test_router_module_compiles(self):
        """agent_os.py router module compiles without syntax errors."""
        import py_compile
        py_compile.compile(
            "server/routers/agent_os.py",
            doraise=True,
        )

    def test_session_module_compiles(self):
        """agent_os_session.py compiles without syntax errors."""
        import py_compile
        py_compile.compile(
            "server/services/agent_os_session.py",
            doraise=True,
        )
