"""Phase 4 Test Suite — Chat Forking, Inject, Export, Navigation, Keyboard Shortcuts, Polish"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TEMP_DIR = tempfile.mkdtemp(prefix="phase4_test_")


def _fake_home():
    return Path(TEMP_DIR)


sys.path.insert(0, str(Path(__file__).parent))


def _reset_db():
    """Clear workspace database engine cache and delete temp DB."""
    import server.services.workspace_database as db_mod
    db_mod._engine_cache.clear()
    db_path = Path(TEMP_DIR) / ".autoforge" / "workspace.db"
    if db_path.exists():
        db_path.unlink()


# ============================================================================
# Database Model Tests
# ============================================================================

class TestForkedFromColumn(unittest.TestCase):
    """Test that the forked_from_id column was properly added to the model."""

    def test_forked_from_column_exists(self):
        from server.services.workspace_database import WorkspaceConversation
        col_names = {c.name for c in WorkspaceConversation.__table__.columns}
        self.assertIn("forked_from_id", col_names)

    def test_forked_from_column_nullable(self):
        from server.services.workspace_database import WorkspaceConversation
        col = WorkspaceConversation.__table__.columns["forked_from_id"]
        self.assertTrue(col.nullable)

    def test_forked_from_column_is_integer(self):
        from server.services.workspace_database import WorkspaceConversation
        from sqlalchemy import Integer
        col = WorkspaceConversation.__table__.columns["forked_from_id"]
        self.assertIsInstance(col.type, Integer)

    def test_forked_from_column_has_fk(self):
        from server.services.workspace_database import WorkspaceConversation
        col = WorkspaceConversation.__table__.columns["forked_from_id"]
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        self.assertIn("workspace_conversations.id", fk_targets)


# ============================================================================
# Database Migration Tests
# ============================================================================

class TestDatabaseMigration(unittest.TestCase):
    """Test that migration adds forked_from_id column to existing databases."""

    def setUp(self):
        self.home_patcher = patch("pathlib.Path.home", _fake_home)
        self.home_patcher.start()
        _reset_db()

    def tearDown(self):
        self.home_patcher.stop()
        _reset_db()

    def test_migration_adds_forked_from_id(self):
        """Verify the forked_from_id migration runs successfully."""
        autoforge_dir = Path(TEMP_DIR) / ".autoforge"
        autoforge_dir.mkdir(parents=True, exist_ok=True)
        db_path = autoforge_dir / "workspace.db"

        # Create a minimal database WITHOUT forked_from_id
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE workspace_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                category TEXT DEFAULT 'general',
                working_directory TEXT,
                pinned INTEGER DEFAULT 0,
                token_count INTEGER DEFAULT 0,
                summary TEXT,
                summary_updated_at DATETIME,
                created_at DATETIME,
                updated_at DATETIME
            )
        """)
        # Create workspace_messages table (needed for FK)
        conn.execute("""
            CREATE TABLE workspace_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                role TEXT,
                content TEXT,
                token_estimate INTEGER DEFAULT 0,
                timestamp DATETIME
            )
        """)
        conn.commit()
        conn.close()

        # Trigger the engine initialization which runs migrations
        import server.services.workspace_database as db_mod
        db_mod._engine_cache.clear()
        db_mod.get_engine()

        # Verify column was added
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("PRAGMA table_info(workspace_conversations)")
        col_names = {row[1] for row in cursor.fetchall()}
        conn.close()

        self.assertIn("forked_from_id", col_names)


# ============================================================================
# Fork Conversation Tests
# ============================================================================

class TestForkConversation(unittest.TestCase):
    """Test the fork_conversation() database function."""

    def setUp(self):
        self.home_patcher = patch("pathlib.Path.home", _fake_home)
        self.home_patcher.start()
        _reset_db()
        import server.services.workspace_database as db_mod
        self.db = db_mod

    def tearDown(self):
        self.home_patcher.stop()
        _reset_db()

    def _create_conversation_with_messages(self, title="Test Chat", n_messages=4):
        """Helper to create a conversation with alternating user/assistant messages."""
        conv = self.db.create_conversation(category="general")
        conv_id = conv.id
        self.db.update_conversation(conv_id, title=title)
        for i in range(n_messages):
            role = "user" if i % 2 == 0 else "assistant"
            self.db.add_message(conv_id, role, f"Message {i + 1}")
        return conv_id

    def test_fork_copies_all_messages(self):
        conv_id = self._create_conversation_with_messages(n_messages=4)
        result = self.db.fork_conversation(conv_id)
        self.assertNotEqual(result["id"], conv_id)
        self.assertEqual(result["message_count"], 4)
        self.assertEqual(result["forked_from_id"], conv_id)
        self.assertIn("(fork)", result["title"])

    def test_fork_at_specific_message(self):
        conv_id = self._create_conversation_with_messages(n_messages=6)
        messages = self.db.get_messages(conv_id)
        # Fork at message #3
        fork_msg_id = messages[2]["id"]
        result = self.db.fork_conversation(conv_id, fork_at_message_id=fork_msg_id)
        self.assertEqual(result["message_count"], 3)
        self.assertEqual(result["forked_from_id"], conv_id)

    def test_fork_nonexistent_conversation(self):
        with self.assertRaises(ValueError):
            self.db.fork_conversation(99999)

    def test_fork_nonexistent_message(self):
        conv_id = self._create_conversation_with_messages(n_messages=2)
        with self.assertRaises(ValueError):
            self.db.fork_conversation(conv_id, fork_at_message_id=99999)

    def test_fork_preserves_category(self):
        conv = self.db.create_conversation(category="debugging")
        conv_id = conv.id
        self.db.add_message(conv_id, "user", "Hello")
        result = self.db.fork_conversation(conv_id)
        self.assertEqual(result["category"], "debugging")

    def test_fork_title_format(self):
        conv_id = self._create_conversation_with_messages(title="My Project")
        result = self.db.fork_conversation(conv_id)
        self.assertEqual(result["title"], "My Project (fork)")

    def test_fork_empty_conversation(self):
        conv = self.db.create_conversation(category="general")
        result = self.db.fork_conversation(conv.id)
        self.assertEqual(result["message_count"], 0)


# ============================================================================
# Paginated Messages Tests
# ============================================================================

class TestGetMessagesPaginated(unittest.TestCase):
    """Test the get_messages_paginated() database function."""

    def setUp(self):
        self.home_patcher = patch("pathlib.Path.home", _fake_home)
        self.home_patcher.start()
        _reset_db()
        import server.services.workspace_database as db_mod
        self.db = db_mod

    def tearDown(self):
        self.home_patcher.stop()
        _reset_db()

    def test_default_pagination(self):
        conv = self.db.create_conversation(category="general")
        for i in range(10):
            self.db.add_message(conv.id, "user", f"Message {i}")
        result = self.db.get_messages_paginated(conv.id)
        self.assertEqual(result["total"], 10)
        self.assertEqual(len(result["messages"]), 10)

    def test_limit(self):
        conv = self.db.create_conversation(category="general")
        for i in range(10):
            self.db.add_message(conv.id, "user", f"Message {i}")
        result = self.db.get_messages_paginated(conv.id, limit=3)
        self.assertEqual(result["total"], 10)
        self.assertEqual(len(result["messages"]), 3)

    def test_offset(self):
        conv = self.db.create_conversation(category="general")
        for i in range(10):
            self.db.add_message(conv.id, "user", f"Message {i}")
        result = self.db.get_messages_paginated(conv.id, limit=3, offset=7)
        self.assertEqual(result["total"], 10)
        self.assertEqual(len(result["messages"]), 3)
        self.assertIn("Message 7", result["messages"][0]["content"])

    def test_empty_conversation(self):
        conv = self.db.create_conversation(category="general")
        result = self.db.get_messages_paginated(conv.id)
        self.assertEqual(result["total"], 0)
        self.assertEqual(len(result["messages"]), 0)

    def test_message_fields(self):
        conv = self.db.create_conversation(category="general")
        self.db.add_message(conv.id, "user", "Hello world")
        result = self.db.get_messages_paginated(conv.id)
        msg = result["messages"][0]
        self.assertIn("id", msg)
        self.assertIn("role", msg)
        self.assertIn("content", msg)
        self.assertIn("token_estimate", msg)
        self.assertIn("timestamp", msg)
        self.assertEqual(msg["role"], "user")
        self.assertEqual(msg["content"], "Hello world")


# ============================================================================
# Export Conversation Markdown Tests
# ============================================================================

class TestExportConversationMarkdown(unittest.TestCase):
    """Test the export_conversation_markdown() database function."""

    def setUp(self):
        self.home_patcher = patch("pathlib.Path.home", _fake_home)
        self.home_patcher.start()
        _reset_db()
        import server.services.workspace_database as db_mod
        self.db = db_mod

    def tearDown(self):
        self.home_patcher.stop()
        _reset_db()

    def test_export_basic(self):
        conv = self.db.create_conversation(category="general")
        self.db.update_conversation(conv.id, title="Test Export")
        self.db.add_message(conv.id, "user", "Hello Claude")
        self.db.add_message(conv.id, "assistant", "Hello! How can I help?")
        md = self.db.export_conversation_markdown(conv.id)
        self.assertIn("# Test Export", md)
        self.assertIn("**User**", md)
        self.assertIn("**Assistant**", md)
        self.assertIn("Hello Claude", md)
        self.assertIn("Hello! How can I help?", md)

    def test_export_includes_metadata(self):
        conv = self.db.create_conversation(category="debugging")
        self.db.update_conversation(conv.id, title="Debug Session")
        self.db.add_message(conv.id, "user", "Test")
        md = self.db.export_conversation_markdown(conv.id)
        self.assertIn("**Category:** debugging", md)
        self.assertIn("**Messages:** 1", md)
        self.assertIn("## Conversation", md)

    def test_export_nonexistent(self):
        with self.assertRaises(ValueError):
            self.db.export_conversation_markdown(99999)

    def test_export_empty_conversation(self):
        conv = self.db.create_conversation(category="general")
        self.db.update_conversation(conv.id, title="Empty Chat")
        md = self.db.export_conversation_markdown(conv.id)
        self.assertIn("# Empty Chat", md)
        self.assertIn("**Messages:** 0", md)

    def test_export_preserves_message_content(self):
        conv = self.db.create_conversation(category="general")
        code_content = "```python\ndef hello():\n    print('world')\n```"
        self.db.add_message(conv.id, "assistant", code_content)
        md = self.db.export_conversation_markdown(conv.id)
        self.assertIn(code_content, md)


# ============================================================================
# Router Endpoint Tests (skipped if claude_agent_sdk unavailable)
# ============================================================================

def _can_import_router():
    try:
        from server.routers.workspace import router  # noqa: F401
        return True
    except (ImportError, ModuleNotFoundError):
        return False


@unittest.skipUnless(_can_import_router(), "claude_agent_sdk not installed")
class TestRouterEndpoints(unittest.TestCase):
    """Test that Phase 4 router endpoints are properly defined."""

    def test_fork_endpoint_exists(self):
        from server.routers.workspace import router
        routes = [r.path for r in router.routes]
        self.assertIn("/conversations/{conversation_id}/fork", routes)

    def test_messages_endpoint_exists(self):
        from server.routers.workspace import router
        routes = [r.path for r in router.routes]
        self.assertIn("/conversations/{conversation_id}/messages", routes)

    def test_export_endpoint_exists(self):
        from server.routers.workspace import router
        routes = [r.path for r in router.routes]
        self.assertIn("/conversations/{conversation_id}/export", routes)

    def test_inject_endpoint_exists(self):
        from server.routers.workspace import router
        routes = [r.path for r in router.routes]
        self.assertIn("/conversations/{conversation_id}/inject", routes)


# ============================================================================
# Pydantic Model Tests (skipped if claude_agent_sdk unavailable)
# ============================================================================

@unittest.skipUnless(_can_import_router(), "claude_agent_sdk not installed")
class TestPydanticModels(unittest.TestCase):
    """Test Phase 4 Pydantic request/response models."""

    def test_fork_request_model(self):
        from server.routers.workspace import ForkRequest
        req = ForkRequest()
        self.assertIsNone(req.fork_at_message_id)

    def test_fork_request_with_message_id(self):
        from server.routers.workspace import ForkRequest
        req = ForkRequest(fork_at_message_id=42)
        self.assertEqual(req.fork_at_message_id, 42)

    def test_inject_request_model_with_list(self):
        from server.routers.workspace import InjectRequest
        req = InjectRequest(source_conversation_id=1, message_ids=[1, 2, 3])
        self.assertEqual(req.source_conversation_id, 1)
        self.assertEqual(req.message_ids, [1, 2, 3])

    def test_inject_request_model_with_all(self):
        from server.routers.workspace import InjectRequest
        req = InjectRequest(source_conversation_id=1, message_ids="all")
        self.assertEqual(req.message_ids, "all")


# ============================================================================
# Frontend File Existence Tests
# ============================================================================

class TestFrontendFiles(unittest.TestCase):
    """Test that all Phase 4 frontend files exist."""

    BASE = Path(__file__).parent / "ui" / "src"

    def test_chat_fork_modal_exists(self):
        self.assertTrue((self.BASE / "components" / "workspace" / "ChatForkModal.tsx").exists())

    def test_inject_modal_exists(self):
        self.assertTrue((self.BASE / "components" / "workspace" / "InjectFromChatModal.tsx").exists())

    def test_keyboard_help_exists(self):
        self.assertTrue((self.BASE / "components" / "workspace" / "WorkspaceKeyboardHelp.tsx").exists())

    def test_keyboard_shortcuts_hook_exists(self):
        self.assertTrue((self.BASE / "hooks" / "useWorkspaceKeyboardShortcuts.ts").exists())


# ============================================================================
# Frontend Content Tests
# ============================================================================

class TestFrontendContent(unittest.TestCase):
    """Verify Phase 4 features are properly integrated in frontend files."""

    BASE = Path(__file__).parent / "ui" / "src"

    def test_workspace_chat_has_fork_modal(self):
        content = (self.BASE / "components" / "workspace" / "WorkspaceChat.tsx").read_text()
        self.assertIn("ChatForkModal", content)
        self.assertIn("showForkModal", content)

    def test_workspace_chat_has_inject_modal(self):
        content = (self.BASE / "components" / "workspace" / "WorkspaceChat.tsx").read_text()
        self.assertIn("InjectFromChatModal", content)
        self.assertIn("showInjectModal", content)

    def test_workspace_chat_has_export(self):
        content = (self.BASE / "components" / "workspace" / "WorkspaceChat.tsx").read_text()
        self.assertIn("exportConversationMarkdown", content)
        self.assertIn("Export as Markdown", content)

    def test_workspace_chat_has_dropdown_menu(self):
        content = (self.BASE / "components" / "workspace" / "WorkspaceChat.tsx").read_text()
        self.assertIn("DropdownMenu", content)
        self.assertIn("Fork Chat", content)
        self.assertIn("Inject from Chat", content)

    def test_workspace_chat_has_injection_indicator(self):
        content = (self.BASE / "components" / "workspace" / "WorkspaceChat.tsx").read_text()
        self.assertIn("pendingInjection", content)
        self.assertIn("Injecting", content)

    def test_workspace_chat_has_draft_persistence(self):
        content = (self.BASE / "components" / "workspace" / "WorkspaceChat.tsx").read_text()
        self.assertIn("DRAFT_KEY_PREFIX", content)
        self.assertIn("localStorage", content)

    def test_workspace_chat_has_smart_scroll(self):
        content = (self.BASE / "components" / "workspace" / "WorkspaceChat.tsx").read_text()
        self.assertIn("isUserScrolledUp", content)
        self.assertIn("handleScroll", content)

    def test_workspace_chat_has_empty_state(self):
        content = (self.BASE / "components" / "workspace" / "WorkspaceChat.tsx").read_text()
        self.assertIn("No conversations yet", content)
        self.assertIn("Start a Conversation", content)

    def test_workspace_chat_has_disconnect_banner(self):
        content = (self.BASE / "components" / "workspace" / "WorkspaceChat.tsx").read_text()
        self.assertIn("Connection lost", content)
        self.assertIn("WifiOff", content)

    def test_workspace_page_has_breadcrumbs(self):
        content = (self.BASE / "pages" / "WorkspacePage.tsx").read_text()
        self.assertIn("Breadcrumb", content)
        self.assertIn("ChevronRight", content)
        self.assertIn("AutoForge", content)

    def test_workspace_page_has_keyboard_shortcuts(self):
        content = (self.BASE / "pages" / "WorkspacePage.tsx").read_text()
        self.assertIn("useWorkspaceKeyboardShortcuts", content)
        self.assertIn("WorkspaceKeyboardHelp", content)
        self.assertIn("showKeyboardHelp", content)

    def test_workspace_page_passes_chat_input_ref(self):
        content = (self.BASE / "pages" / "WorkspacePage.tsx").read_text()
        self.assertIn("chatInputRef", content)

    def test_keyboard_hook_has_all_shortcuts(self):
        content = (self.BASE / "hooks" / "useWorkspaceKeyboardShortcuts.ts").read_text()
        self.assertIn("onNewConversation", content)
        self.assertIn("onToggleLibrary", content)
        self.assertIn("onToggleSidebar", content)
        self.assertIn("onFocusSearch", content)
        self.assertIn("onExportChat", content)
        self.assertIn("onShowShortcutsHelp", content)
        self.assertIn("onFocusChatInput", content)

    def test_workspace_chat_hook_has_injection(self):
        content = (self.BASE / "hooks" / "useWorkspaceChat.ts").read_text()
        self.assertIn("pendingInjection", content)
        self.assertIn("setPendingInjection", content)
        self.assertIn("PendingInjection", content)

    def test_api_has_phase4_functions(self):
        content = (self.BASE / "lib" / "api.ts").read_text()
        self.assertIn("forkConversation", content)
        self.assertIn("getConversationMessages", content)
        self.assertIn("exportConversationMarkdown", content)
        self.assertIn("getInjectionContent", content)

    def test_types_has_phase4_types(self):
        content = (self.BASE / "lib" / "types.ts").read_text()
        self.assertIn("ForkResponse", content)
        self.assertIn("PaginatedMessages", content)
        self.assertIn("PendingInjection", content)
        self.assertIn("InjectResponse", content)

    def test_chat_fork_modal_content(self):
        content = (self.BASE / "components" / "workspace" / "ChatForkModal.tsx").read_text()
        self.assertIn("Fork Conversation", content)
        self.assertIn("forkConversation", content)
        self.assertIn("onForkCreated", content)
        self.assertIn("selectedMessageId", content)

    def test_inject_modal_content(self):
        content = (self.BASE / "components" / "workspace" / "InjectFromChatModal.tsx").read_text()
        self.assertIn("Select Source Conversation", content)
        self.assertIn("Select Messages to Inject", content)
        self.assertIn("onInject", content)
        self.assertIn("Checkbox", content)

    def test_keyboard_help_modal_content(self):
        content = (self.BASE / "components" / "workspace" / "WorkspaceKeyboardHelp.tsx").read_text()
        self.assertIn("Workspace Shortcuts", content)
        self.assertIn("New conversation", content)
        self.assertIn("Toggle library panel", content)

    def test_conversation_search_has_data_attribute(self):
        content = (self.BASE / "components" / "workspace" / "ConversationSearch.tsx").read_text()
        self.assertIn("data-workspace-search", content)

    def test_app_tsx_has_workspace_link(self):
        content = (self.BASE / "App.tsx").read_text()
        self.assertIn("Workspace", content)
        self.assertIn("#/workspace", content)


# ============================================================================
# Integration Tests — Fork + Export roundtrip
# ============================================================================

class TestForkExportIntegration(unittest.TestCase):
    """Integration test: create, fork, then export both and compare."""

    def setUp(self):
        self.home_patcher = patch("pathlib.Path.home", _fake_home)
        self.home_patcher.start()
        _reset_db()
        import server.services.workspace_database as db_mod
        self.db = db_mod

    def tearDown(self):
        self.home_patcher.stop()
        _reset_db()

    def test_fork_then_export(self):
        # Create original conversation
        conv = self.db.create_conversation(category="general")
        self.db.update_conversation(conv.id, title="Original")
        self.db.add_message(conv.id, "user", "First question")
        self.db.add_message(conv.id, "assistant", "First answer")
        self.db.add_message(conv.id, "user", "Second question")
        self.db.add_message(conv.id, "assistant", "Second answer")

        # Fork at message 2
        messages = self.db.get_messages(conv.id)
        fork_result = self.db.fork_conversation(conv.id, fork_at_message_id=messages[1]["id"])

        # Export both
        original_md = self.db.export_conversation_markdown(conv.id)
        fork_md = self.db.export_conversation_markdown(fork_result["id"])

        # Original has all 4 messages
        self.assertIn("Second question", original_md)
        self.assertIn("Second answer", original_md)

        # Fork only has first 2
        self.assertIn("First question", fork_md)
        self.assertIn("First answer", fork_md)
        self.assertNotIn("Second question", fork_md)
        self.assertNotIn("Second answer", fork_md)

    def test_paginate_forked_conversation(self):
        # Create and fork
        conv = self.db.create_conversation(category="general")
        for i in range(20):
            self.db.add_message(conv.id, "user", f"Msg {i}")
        fork_result = self.db.fork_conversation(conv.id)

        # Paginate the fork
        page1 = self.db.get_messages_paginated(fork_result["id"], limit=5, offset=0)
        page2 = self.db.get_messages_paginated(fork_result["id"], limit=5, offset=5)
        self.assertEqual(page1["total"], 20)
        self.assertEqual(len(page1["messages"]), 5)
        self.assertEqual(len(page2["messages"]), 5)
        # Different pages should have different messages
        self.assertNotEqual(
            page1["messages"][0]["content"],
            page2["messages"][0]["content"],
        )


# ============================================================================
# Build Verification
# ============================================================================

class TestBuildVerification(unittest.TestCase):
    """Verify that the UI builds successfully."""

    def test_ui_dist_exists(self):
        dist = Path(__file__).parent / "ui" / "dist"
        self.assertTrue(dist.exists(), "ui/dist directory should exist after build")

    def test_ui_dist_has_index(self):
        index = Path(__file__).parent / "ui" / "dist" / "index.html"
        self.assertTrue(index.exists(), "ui/dist/index.html should exist after build")


# ============================================================================
# Run
# ============================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
