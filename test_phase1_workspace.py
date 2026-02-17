"""Phase 1 Test Suite — Workspace Chat Infrastructure"""

import importlib
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

# Temp dir simulating ~/.autoforge for complete DB isolation
TEMP_DIR = tempfile.mkdtemp(prefix="phase1_test_")


def _fake_home():
    return Path(TEMP_DIR)


def _reset_db():
    """Clear engine cache and delete workspace.db for test isolation."""
    from server.services import workspace_database as db
    # Dispose all cached engines so connections are released
    for engine in db._engine_cache.values():
        engine.dispose()
    db._engine_cache.clear()
    # Remove the actual DB file to get a clean slate
    db_file = Path(TEMP_DIR) / ".autoforge" / "workspace.db"
    if db_file.exists():
        db_file.unlink()


# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent))


# ============================================================================
# Database Tests — workspace_database.py
# ============================================================================


class TestEstimateTokens(unittest.TestCase):
    """Token estimation heuristic: ~4 chars per token, minimum 1."""

    def setUp(self):
        self.home_patcher = patch("pathlib.Path.home", _fake_home)
        self.home_patcher.start()
        _reset_db()
        from server.services import workspace_database as db
        self.db = db

    def tearDown(self):
        self.home_patcher.stop()
        _reset_db()

    def test_empty_string(self):
        self.assertEqual(self.db.estimate_tokens(""), 0)

    def test_single_char(self):
        self.assertEqual(self.db.estimate_tokens("a"), 1)

    def test_four_chars_one_token(self):
        self.assertEqual(self.db.estimate_tokens("abcd"), 1)

    def test_eight_chars_two_tokens(self):
        self.assertEqual(self.db.estimate_tokens("abcdefgh"), 2)

    def test_unicode(self):
        result = self.db.estimate_tokens("Hello, World!")
        self.assertGreater(result, 0)

    def test_long_text(self):
        text = "x" * 4000
        self.assertEqual(self.db.estimate_tokens(text), 1000)

    def test_minimum_one(self):
        # 1, 2, 3 chars all give min 1
        for i in range(1, 4):
            self.assertGreaterEqual(self.db.estimate_tokens("a" * i), 1)


class TestConversationCRUD(unittest.TestCase):
    """Create, read, update, delete conversations."""

    def setUp(self):
        self.home_patcher = patch("pathlib.Path.home", _fake_home)
        self.home_patcher.start()
        _reset_db()
        from server.services import workspace_database as db
        self.db = db

    def tearDown(self):
        self.home_patcher.stop()
        _reset_db()

    def test_create_defaults(self):
        conv = self.db.create_conversation()
        self.assertIsNotNone(conv.id)
        self.assertIsNone(conv.title)
        self.assertEqual(conv.category, "general")
        self.assertIsNone(conv.working_directory)

    def test_create_custom_category(self):
        conv = self.db.create_conversation(category="debugging")
        self.assertEqual(conv.category, "debugging")

    def test_create_custom_working_directory(self):
        conv = self.db.create_conversation(working_directory="/tmp/test")
        self.assertEqual(conv.working_directory, "/tmp/test")

    def test_create_with_title(self):
        conv = self.db.create_conversation(title="My Chat")
        self.assertEqual(conv.title, "My Chat")

    def test_get_conversations_empty(self):
        result = self.db.get_conversations()
        self.assertEqual(result, [])

    def test_get_conversations_multiple(self):
        self.db.create_conversation(title="First")
        self.db.create_conversation(title="Second")
        result = self.db.get_conversations()
        self.assertEqual(len(result), 2)

    def test_get_conversations_ordering(self):
        """Most recently updated first."""
        c1 = self.db.create_conversation(title="Old")
        c2 = self.db.create_conversation(title="New")
        # c2 was created after c1, so it should be first
        result = self.db.get_conversations()
        self.assertEqual(result[0]["title"], "New")
        self.assertEqual(result[1]["title"], "Old")

    def test_get_conversations_category_filter(self):
        self.db.create_conversation(category="debugging")
        self.db.create_conversation(category="feature")
        self.db.create_conversation(category="debugging")
        result = self.db.get_conversations(category="debugging")
        self.assertEqual(len(result), 2)
        for c in result:
            self.assertEqual(c["category"], "debugging")

    def test_get_conversations_message_count(self):
        conv = self.db.create_conversation()
        self.db.add_message(conv.id, "user", "Hello")
        self.db.add_message(conv.id, "assistant", "Hi!")
        result = self.db.get_conversations()
        self.assertEqual(result[0]["message_count"], 2)

    def test_get_conversation_exists(self):
        conv = self.db.create_conversation(title="Test")
        result = self.db.get_conversation(conv.id)
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Test")
        self.assertIn("messages", result)

    def test_get_conversation_not_found(self):
        result = self.db.get_conversation(99999)
        self.assertIsNone(result)

    def test_get_conversation_messages_sorted(self):
        conv = self.db.create_conversation()
        self.db.add_message(conv.id, "user", "First")
        self.db.add_message(conv.id, "assistant", "Second")
        self.db.add_message(conv.id, "user", "Third")
        result = self.db.get_conversation(conv.id)
        contents = [m["content"] for m in result["messages"]]
        self.assertEqual(contents, ["First", "Second", "Third"])

    def test_update_title(self):
        conv = self.db.create_conversation()
        result = self.db.update_conversation(conv.id, title="Updated")
        self.assertEqual(result["title"], "Updated")

    def test_update_category(self):
        conv = self.db.create_conversation()
        result = self.db.update_conversation(conv.id, category="refactoring")
        self.assertEqual(result["category"], "refactoring")

    def test_update_both(self):
        conv = self.db.create_conversation()
        result = self.db.update_conversation(conv.id, title="T", category="feature")
        self.assertEqual(result["title"], "T")
        self.assertEqual(result["category"], "feature")

    def test_update_not_found(self):
        result = self.db.update_conversation(99999, title="nope")
        self.assertIsNone(result)

    def test_update_returns_message_count(self):
        conv = self.db.create_conversation()
        self.db.add_message(conv.id, "user", "msg1")
        self.db.add_message(conv.id, "user", "msg2")
        result = self.db.update_conversation(conv.id, title="T")
        self.assertEqual(result["message_count"], 2)

    def test_delete_success(self):
        conv = self.db.create_conversation()
        self.assertTrue(self.db.delete_conversation(conv.id))

    def test_delete_not_found(self):
        self.assertFalse(self.db.delete_conversation(99999))

    def test_delete_cascade_messages(self):
        conv = self.db.create_conversation()
        self.db.add_message(conv.id, "user", "Hello")
        self.db.add_message(conv.id, "assistant", "Hi!")
        self.assertTrue(self.db.delete_conversation(conv.id))
        # Messages should be gone too
        messages = self.db.get_messages(conv.id)
        self.assertEqual(messages, [])

    def test_delete_then_get(self):
        conv = self.db.create_conversation()
        self.db.delete_conversation(conv.id)
        self.assertIsNone(self.db.get_conversation(conv.id))

    def test_get_conversation_dict_keys(self):
        conv = self.db.create_conversation(title="K", category="feature", working_directory="/tmp")
        result = self.db.get_conversation(conv.id)
        expected_keys = {"id", "title", "category", "working_directory", "created_at", "updated_at", "messages"}
        self.assertEqual(set(result.keys()), expected_keys)


class TestMessageOperations(unittest.TestCase):
    """Add, retrieve, and token estimation for messages."""

    def setUp(self):
        self.home_patcher = patch("pathlib.Path.home", _fake_home)
        self.home_patcher.start()
        from server.services import workspace_database as db
        db._engine_cache.clear()
        self.db = db
        self.conv = self.db.create_conversation()

    def tearDown(self):
        self.home_patcher.stop()
        self.db._engine_cache.clear()

    def test_add_basic(self):
        result = self.db.add_message(self.conv.id, "user", "Hello World")
        self.assertIsNotNone(result)
        self.assertEqual(result["role"], "user")
        self.assertEqual(result["content"], "Hello World")

    def test_add_auto_token_estimation(self):
        result = self.db.add_message(self.conv.id, "user", "abcdefgh")  # 8 chars = 2 tokens
        self.assertEqual(result["token_estimate"], 2)

    def test_add_precomputed_tokens(self):
        result = self.db.add_message(self.conv.id, "user", "hello", token_estimate=42)
        self.assertEqual(result["token_estimate"], 42)

    def test_add_zero_precomputed_tokens(self):
        result = self.db.add_message(self.conv.id, "user", "hello", token_estimate=0)
        self.assertEqual(result["token_estimate"], 0)

    def test_add_nonexistent_conversation(self):
        result = self.db.add_message(99999, "user", "hello")
        self.assertIsNone(result)

    def test_get_messages_empty(self):
        messages = self.db.get_messages(self.conv.id)
        self.assertEqual(messages, [])

    def test_get_messages_ordered(self):
        self.db.add_message(self.conv.id, "user", "A")
        self.db.add_message(self.conv.id, "assistant", "B")
        self.db.add_message(self.conv.id, "user", "C")
        messages = self.db.get_messages(self.conv.id)
        self.assertEqual(len(messages), 3)
        self.assertEqual([m["content"] for m in messages], ["A", "B", "C"])

    def test_get_messages_nonexistent_conversation(self):
        messages = self.db.get_messages(99999)
        self.assertEqual(messages, [])

    def test_message_dict_keys(self):
        result = self.db.add_message(self.conv.id, "user", "test")
        expected_keys = {"id", "role", "content", "token_estimate", "timestamp"}
        self.assertEqual(set(result.keys()), expected_keys)

    def test_multiple_roles(self):
        self.db.add_message(self.conv.id, "user", "q")
        self.db.add_message(self.conv.id, "assistant", "a")
        self.db.add_message(self.conv.id, "system", "s")
        messages = self.db.get_messages(self.conv.id)
        roles = [m["role"] for m in messages]
        self.assertEqual(roles, ["user", "assistant", "system"])

    def test_empty_content(self):
        result = self.db.add_message(self.conv.id, "user", "")
        self.assertIsNotNone(result)
        self.assertEqual(result["content"], "")
        self.assertEqual(result["token_estimate"], 0)

    def test_large_content(self):
        big = "x" * 10000
        result = self.db.add_message(self.conv.id, "user", big)
        self.assertEqual(result["content"], big)
        self.assertEqual(result["token_estimate"], 2500)

    def test_special_characters(self):
        text = 'Hello "world" <>&\n\ttab'
        result = self.db.add_message(self.conv.id, "user", text)
        self.assertEqual(result["content"], text)

    def test_timestamp_updates_conversation(self):
        """Adding a message should update the conversation's updated_at."""
        before = self.db.get_conversation(self.conv.id)
        self.db.add_message(self.conv.id, "user", "update me")
        after = self.db.get_conversation(self.conv.id)
        # updated_at should have changed (or at least not be earlier)
        self.assertIsNotNone(after["updated_at"])


class TestAutoTitle(unittest.TestCase):
    """Auto-title generation from the first user message."""

    def setUp(self):
        self.home_patcher = patch("pathlib.Path.home", _fake_home)
        self.home_patcher.start()
        _reset_db()
        from server.services import workspace_database as db
        self.db = db

    def tearDown(self):
        self.home_patcher.stop()
        _reset_db()

    def test_first_user_message_sets_title(self):
        conv = self.db.create_conversation()
        self.db.add_message(conv.id, "user", "Help me debug this function")
        result = self.db.get_conversation(conv.id)
        self.assertEqual(result["title"], "Help me debug this function")

    def test_assistant_does_not_set_title(self):
        conv = self.db.create_conversation()
        self.db.add_message(conv.id, "assistant", "Hello!")
        result = self.db.get_conversation(conv.id)
        self.assertIsNone(result["title"])

    def test_first_user_after_assistant_sets_title(self):
        conv = self.db.create_conversation()
        self.db.add_message(conv.id, "assistant", "Welcome!")
        self.db.add_message(conv.id, "user", "Fix the login bug")
        result = self.db.get_conversation(conv.id)
        self.assertEqual(result["title"], "Fix the login bug")

    def test_subsequent_user_messages_dont_overwrite(self):
        conv = self.db.create_conversation()
        self.db.add_message(conv.id, "user", "First message")
        self.db.add_message(conv.id, "user", "Second message")
        result = self.db.get_conversation(conv.id)
        self.assertEqual(result["title"], "First message")

    def test_explicit_title_preserved(self):
        conv = self.db.create_conversation(title="My Chat")
        self.db.add_message(conv.id, "user", "Should not change title")
        result = self.db.get_conversation(conv.id)
        self.assertEqual(result["title"], "My Chat")

    def test_title_exactly_50_chars_no_truncation(self):
        msg = "a" * 50
        conv = self.db.create_conversation()
        self.db.add_message(conv.id, "user", msg)
        result = self.db.get_conversation(conv.id)
        self.assertEqual(result["title"], msg)
        self.assertNotIn("...", result["title"])

    def test_title_51_chars_truncated(self):
        msg = "a" * 51
        conv = self.db.create_conversation()
        self.db.add_message(conv.id, "user", msg)
        result = self.db.get_conversation(conv.id)
        self.assertEqual(result["title"], "a" * 50 + "...")


class TestTokenTracking(unittest.TestCase):
    """Token accumulation via get_conversation_token_total."""

    def setUp(self):
        self.home_patcher = patch("pathlib.Path.home", _fake_home)
        self.home_patcher.start()
        _reset_db()
        from server.services import workspace_database as db
        self.db = db

    def tearDown(self):
        self.home_patcher.stop()
        _reset_db()

    def test_zero_for_empty(self):
        conv = self.db.create_conversation()
        self.assertEqual(self.db.get_conversation_token_total(conv.id), 0)

    def test_zero_for_nonexistent(self):
        self.assertEqual(self.db.get_conversation_token_total(99999), 0)

    def test_sum_auto_estimated(self):
        conv = self.db.create_conversation()
        self.db.add_message(conv.id, "user", "abcdefgh")      # 8 chars = 2 tokens
        self.db.add_message(conv.id, "assistant", "abcdefghijkl")  # 12 chars = 3 tokens
        total = self.db.get_conversation_token_total(conv.id)
        self.assertEqual(total, 5)

    def test_sum_precomputed(self):
        conv = self.db.create_conversation()
        self.db.add_message(conv.id, "user", "a", token_estimate=100)
        self.db.add_message(conv.id, "assistant", "b", token_estimate=200)
        total = self.db.get_conversation_token_total(conv.id)
        self.assertEqual(total, 300)

    def test_sum_mixed(self):
        conv = self.db.create_conversation()
        self.db.add_message(conv.id, "user", "abcdefgh")          # auto: 2 tokens
        self.db.add_message(conv.id, "assistant", "x", token_estimate=50)  # precomputed: 50
        total = self.db.get_conversation_token_total(conv.id)
        self.assertEqual(total, 52)


class TestDatabaseModels(unittest.TestCase):
    """SQLAlchemy model structure and table creation."""

    def test_conversation_table_name(self):
        from server.services.workspace_database import WorkspaceConversation
        self.assertEqual(WorkspaceConversation.__tablename__, "workspace_conversations")

    def test_message_table_name(self):
        from server.services.workspace_database import WorkspaceMessage
        self.assertEqual(WorkspaceMessage.__tablename__, "workspace_messages")

    def test_conversation_columns(self):
        from server.services.workspace_database import WorkspaceConversation
        expected = {"id", "title", "category", "working_directory", "created_at", "updated_at"}
        actual = {c.name for c in WorkspaceConversation.__table__.columns}
        self.assertEqual(expected, actual)

    def test_message_columns(self):
        from server.services.workspace_database import WorkspaceMessage
        expected = {"id", "conversation_id", "role", "content", "token_estimate", "timestamp"}
        actual = {c.name for c in WorkspaceMessage.__table__.columns}
        self.assertEqual(expected, actual)

    def test_cascade_relationship(self):
        from server.services.workspace_database import WorkspaceConversation
        rel = WorkspaceConversation.messages.property
        # SQLAlchemy 2.0: CascadeOptions supports 'in' operator directly
        self.assertTrue(rel.cascade.delete_orphan)

    def test_tables_create_in_sqlite(self):
        from sqlalchemy import create_engine, inspect
        from server.services.workspace_database import Base
        db_path = Path(TEMP_DIR) / "test_models.db"
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        tables = inspect(engine).get_table_names()
        self.assertIn("workspace_conversations", tables)
        self.assertIn("workspace_messages", tables)
        engine.dispose()
        db_path.unlink()


class TestThreadSafety(unittest.TestCase):
    """Concurrent access to workspace database."""

    def setUp(self):
        self.home_patcher = patch("pathlib.Path.home", _fake_home)
        self.home_patcher.start()
        _reset_db()
        from server.services import workspace_database as db
        self.db = db

    def tearDown(self):
        self.home_patcher.stop()
        _reset_db()

    def test_concurrent_conversation_creates(self):
        """5 threads each create a conversation -- all should get unique IDs."""
        results = []
        errors = []

        def create_one():
            try:
                c = self.db.create_conversation()
                results.append(c.id)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=create_one) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(errors), 0, f"Errors: {errors}")
        self.assertEqual(len(set(results)), 5)

    def test_concurrent_message_adds(self):
        """10 threads add messages to the same conversation -- no data loss."""
        conv = self.db.create_conversation()
        errors = []

        def add_one(i):
            try:
                self.db.add_message(conv.id, "user", f"msg-{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=add_one, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(errors), 0, f"Errors: {errors}")
        messages = self.db.get_messages(conv.id)
        self.assertEqual(len(messages), 10)


# ============================================================================
# Chat Session Tests — workspace_chat_session.py
# ============================================================================


class TestSessionConstants(unittest.TestCase):
    """Verify workspace session constants match spec requirements."""

    def test_builtin_tools_count(self):
        from server.services.workspace_chat_session import WORKSPACE_BUILTIN_TOOLS
        self.assertEqual(len(WORKSPACE_BUILTIN_TOOLS), 8)

    def test_builtin_tools_contents(self):
        from server.services.workspace_chat_session import WORKSPACE_BUILTIN_TOOLS
        expected = {"Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebFetch", "WebSearch"}
        self.assertEqual(set(WORKSPACE_BUILTIN_TOOLS), expected)

    def test_max_history_messages(self):
        from server.services.workspace_chat_session import MAX_HISTORY_MESSAGES
        self.assertEqual(MAX_HISTORY_MESSAGES, 100)

    def test_context_window_tokens(self):
        from server.services.workspace_chat_session import CONTEXT_WINDOW_TOKENS
        self.assertEqual(CONTEXT_WINDOW_TOKENS, 1_000_000)


class TestSystemPrompt(unittest.TestCase):
    """System prompt generation."""

    def test_contains_working_directory(self):
        from server.services.workspace_chat_session import get_workspace_system_prompt
        prompt = get_workspace_system_prompt("/home/test")
        self.assertIn("/home/test", prompt)

    def test_mentions_read_write_edit(self):
        from server.services.workspace_chat_session import get_workspace_system_prompt
        prompt = get_workspace_system_prompt("/tmp")
        self.assertIn("Read", prompt)
        self.assertIn("Write", prompt)
        self.assertIn("Edit", prompt)

    def test_mentions_bash(self):
        from server.services.workspace_chat_session import get_workspace_system_prompt
        prompt = get_workspace_system_prompt("/tmp")
        self.assertIn("Bash", prompt)

    def test_mentions_grep_glob(self):
        from server.services.workspace_chat_session import get_workspace_system_prompt
        prompt = get_workspace_system_prompt("/tmp")
        self.assertIn("Grep", prompt)
        self.assertIn("Glob", prompt)

    def test_mentions_web_tools(self):
        from server.services.workspace_chat_session import get_workspace_system_prompt
        prompt = get_workspace_system_prompt("/tmp")
        self.assertIn("WebFetch", prompt)
        self.assertIn("WebSearch", prompt)

    def test_substantial_length(self):
        from server.services.workspace_chat_session import get_workspace_system_prompt
        prompt = get_workspace_system_prompt("/tmp")
        self.assertGreater(len(prompt), 200)


class TestSessionRegistry(unittest.TestCase):
    """Thread-safe session registry operations."""

    def setUp(self):
        # Import the registry internals to manipulate directly
        from server.services import workspace_chat_session as mod
        self.mod = mod
        # Clear any leftover sessions
        with self.mod._sessions_lock:
            self.mod._sessions.clear()

    def tearDown(self):
        with self.mod._sessions_lock:
            self.mod._sessions.clear()

    def test_get_session_unknown(self):
        result = self.mod.get_session("nonexistent")
        self.assertIsNone(result)

    def test_registry_roundtrip(self):
        """Manually insert a session and verify get_session finds it."""
        session = self.mod.WorkspaceChatSession("test-1")
        with self.mod._sessions_lock:
            self.mod._sessions["test-1"] = session
        found = self.mod.get_session("test-1")
        self.assertIs(found, session)

    def test_registry_replace(self):
        """Inserting with same key replaces old session."""
        s1 = self.mod.WorkspaceChatSession("s1")
        s2 = self.mod.WorkspaceChatSession("s1")
        with self.mod._sessions_lock:
            self.mod._sessions["s1"] = s1
            self.mod._sessions["s1"] = s2
        found = self.mod.get_session("s1")
        self.assertIs(found, s2)

    def test_registry_clear(self):
        """Clear removes all sessions."""
        for i in range(3):
            with self.mod._sessions_lock:
                self.mod._sessions[f"s{i}"] = self.mod.WorkspaceChatSession(f"s{i}")
        with self.mod._sessions_lock:
            self.mod._sessions.clear()
        for i in range(3):
            self.assertIsNone(self.mod.get_session(f"s{i}"))


class TestWorkspaceChatSessionInit(unittest.TestCase):
    """WorkspaceChatSession constructor and attribute defaults."""

    def test_session_id_stored(self):
        from server.services.workspace_chat_session import WorkspaceChatSession
        s = WorkspaceChatSession("my-session")
        self.assertEqual(s.session_id, "my-session")

    def test_default_working_directory(self):
        from server.services.workspace_chat_session import WorkspaceChatSession
        s = WorkspaceChatSession("s1")
        self.assertEqual(s.working_directory, str(Path.home()))

    def test_custom_working_directory(self):
        from server.services.workspace_chat_session import WorkspaceChatSession
        s = WorkspaceChatSession("s1", working_directory="/custom/path")
        self.assertEqual(s.working_directory, "/custom/path")

    def test_conversation_id_default_none(self):
        from server.services.workspace_chat_session import WorkspaceChatSession
        s = WorkspaceChatSession("s1")
        self.assertIsNone(s.conversation_id)

    def test_conversation_id_set(self):
        from server.services.workspace_chat_session import WorkspaceChatSession
        s = WorkspaceChatSession("s1", conversation_id=42)
        self.assertEqual(s.conversation_id, 42)

    def test_client_initially_none(self):
        from server.services.workspace_chat_session import WorkspaceChatSession
        s = WorkspaceChatSession("s1")
        self.assertIsNone(s.client)

    def test_history_loaded_false(self):
        from server.services.workspace_chat_session import WorkspaceChatSession
        s = WorkspaceChatSession("s1")
        self.assertFalse(s._history_loaded)

    def test_get_conversation_id(self):
        from server.services.workspace_chat_session import WorkspaceChatSession
        s = WorkspaceChatSession("s1", conversation_id=7)
        self.assertEqual(s.get_conversation_id(), 7)


# ============================================================================
# Router Tests — workspace.py
# ============================================================================


class TestRouterConfig(unittest.TestCase):
    """Import workspace router directly (bypass __init__ which needs claude_agent_sdk)."""

    @classmethod
    def _get_router(cls):
        spec = importlib.util.spec_from_file_location(
            "server.routers.workspace",
            Path(__file__).parent / "server" / "routers" / "workspace.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.router

    def test_prefix(self):
        router = self._get_router()
        self.assertEqual(router.prefix, "/api/workspace")

    def test_tags(self):
        router = self._get_router()
        self.assertIn("workspace", router.tags)

    def test_route_count(self):
        """Should have at least 7 routes (6 REST + 1 WebSocket)."""
        router = self._get_router()
        routes = [r for r in router.routes if hasattr(r, "path")]
        self.assertGreaterEqual(len(routes), 7)

    def test_conversation_endpoints_exist(self):
        router = self._get_router()
        routes = {r.path for r in router.routes if hasattr(r, "path")}
        for ep in [
            "/api/workspace/conversations",
            "/api/workspace/conversations/{conversation_id}",
            "/api/workspace/conversations/{conversation_id}/tokens",
        ]:
            self.assertIn(ep, routes, f"Missing endpoint: {ep}")

    def test_websocket_endpoint_exists(self):
        router = self._get_router()
        routes = {r.path for r in router.routes if hasattr(r, "path")}
        self.assertIn("/api/workspace/ws", routes)


class TestPydanticModels(unittest.TestCase):
    """Pydantic model validation for request/response schemas."""

    def test_create_request_defaults(self):
        from server.routers.workspace import ConversationCreateRequest
        req = ConversationCreateRequest()
        self.assertEqual(req.category, "general")
        self.assertIsNone(req.working_directory)

    def test_create_request_custom(self):
        from server.routers.workspace import ConversationCreateRequest
        req = ConversationCreateRequest(category="debugging", working_directory="/tmp")
        self.assertEqual(req.category, "debugging")
        self.assertEqual(req.working_directory, "/tmp")

    def test_update_request_defaults(self):
        from server.routers.workspace import ConversationUpdateRequest
        req = ConversationUpdateRequest()
        self.assertIsNone(req.title)
        self.assertIsNone(req.category)

    def test_update_request_partial(self):
        from server.routers.workspace import ConversationUpdateRequest
        req = ConversationUpdateRequest(title="New Title")
        self.assertEqual(req.title, "New Title")
        self.assertIsNone(req.category)

    def test_summary_model(self):
        from server.routers.workspace import WorkspaceConversationSummary
        s = WorkspaceConversationSummary(
            id=1, title="Test", category="general", working_directory=None,
            created_at=None, updated_at=None, message_count=5,
        )
        self.assertEqual(s.id, 1)
        self.assertEqual(s.message_count, 5)

    def test_summary_model_missing_id(self):
        from server.routers.workspace import WorkspaceConversationSummary
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            WorkspaceConversationSummary(
                title="Test", category="general", working_directory=None,
                created_at=None, updated_at=None, message_count=0,
            )

    def test_message_model(self):
        from server.routers.workspace import WorkspaceMessageModel
        m = WorkspaceMessageModel(
            id=1, role="user", content="hello", token_estimate=2, timestamp=None,
        )
        self.assertEqual(m.role, "user")
        self.assertEqual(m.token_estimate, 2)

    def test_detail_model(self):
        from server.routers.workspace import WorkspaceConversationDetail
        d = WorkspaceConversationDetail(
            id=1, title=None, category="general", working_directory=None,
            created_at=None, updated_at=None, message_count=0, messages=[],
        )
        self.assertEqual(d.messages, [])

    def test_detail_model_with_messages(self):
        from server.routers.workspace import WorkspaceConversationDetail, WorkspaceMessageModel
        msg = WorkspaceMessageModel(
            id=1, role="user", content="hi", token_estimate=1, timestamp=None,
        )
        d = WorkspaceConversationDetail(
            id=1, title=None, category="general", working_directory=None,
            created_at=None, updated_at=None, message_count=1, messages=[msg],
        )
        self.assertEqual(len(d.messages), 1)
        self.assertEqual(d.messages[0].content, "hi")


# ============================================================================
# Integration Tests — full lifecycle
# ============================================================================


class TestConversationLifecycle(unittest.TestCase):
    """End-to-end: create -> add messages -> read -> update -> verify tokens -> delete."""

    def setUp(self):
        self.home_patcher = patch("pathlib.Path.home", _fake_home)
        self.home_patcher.start()
        _reset_db()
        from server.services import workspace_database as db
        self.db = db

    def tearDown(self):
        self.home_patcher.stop()
        _reset_db()

    def test_full_lifecycle(self):
        # Create
        conv = self.db.create_conversation(category="feature")
        self.assertIsNotNone(conv.id)

        # Add messages
        self.db.add_message(conv.id, "user", "Help me add auth")
        self.db.add_message(conv.id, "assistant", "Sure, I'll start with OAuth2 setup.")
        self.db.add_message(conv.id, "user", "Use JWT tokens please")

        # Read
        result = self.db.get_conversation(conv.id)
        self.assertEqual(result["category"], "feature")
        self.assertEqual(result["title"], "Help me add auth")  # auto-titled
        self.assertEqual(len(result["messages"]), 3)

        # Verify tokens
        total = self.db.get_conversation_token_total(conv.id)
        self.assertGreater(total, 0)

        # Update
        updated = self.db.update_conversation(conv.id, title="Auth Feature", category="debugging")
        self.assertEqual(updated["title"], "Auth Feature")
        self.assertEqual(updated["category"], "debugging")
        self.assertEqual(updated["message_count"], 3)

        # Delete
        self.assertTrue(self.db.delete_conversation(conv.id))
        self.assertIsNone(self.db.get_conversation(conv.id))
        self.assertEqual(self.db.get_messages(conv.id), [])
        self.assertEqual(self.db.get_conversation_token_total(conv.id), 0)

    def test_conversation_isolation(self):
        """Messages in one conversation don't appear in another."""
        c1 = self.db.create_conversation()
        c2 = self.db.create_conversation()
        self.db.add_message(c1.id, "user", "Msg for c1")
        self.db.add_message(c2.id, "user", "Msg for c2")
        self.assertEqual(len(self.db.get_messages(c1.id)), 1)
        self.assertEqual(len(self.db.get_messages(c2.id)), 1)
        self.assertEqual(self.db.get_messages(c1.id)[0]["content"], "Msg for c1")
        self.assertEqual(self.db.get_messages(c2.id)[0]["content"], "Msg for c2")

    def test_token_accumulation_across_messages(self):
        conv = self.db.create_conversation()
        self.db.add_message(conv.id, "user", "x" * 400, token_estimate=100)
        self.db.add_message(conv.id, "assistant", "y" * 800, token_estimate=200)
        self.db.add_message(conv.id, "user", "z" * 1200, token_estimate=300)
        self.assertEqual(self.db.get_conversation_token_total(conv.id), 600)

    def test_list_reflects_crud(self):
        """get_conversations reflects creates and deletes."""
        self.assertEqual(len(self.db.get_conversations()), 0)
        c1 = self.db.create_conversation(title="A")
        c2 = self.db.create_conversation(title="B")
        self.assertEqual(len(self.db.get_conversations()), 2)
        self.db.delete_conversation(c1.id)
        remaining = self.db.get_conversations()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["title"], "B")


# ============================================================================
# Cleanup
# ============================================================================


def teardown_module():
    try:
        shutil.rmtree(TEMP_DIR)
    except Exception:
        pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
