"""Phase 3 Test Suite — File Library & GitHub Integration"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TEMP_DIR = tempfile.mkdtemp(prefix="phase3_test_")

def _fake_home():
    return Path(TEMP_DIR)

sys.path.insert(0, str(Path(__file__).parent))


class TestTokenEncryption(unittest.TestCase):

    def setUp(self):
        self.home_patcher = patch("pathlib.Path.home", _fake_home)
        self.home_patcher.start()
        if "server.services.workspace_token_encryption" in sys.modules:
            del sys.modules["server.services.workspace_token_encryption"]
        from server.services import workspace_token_encryption
        workspace_token_encryption.TOKENS_FILE = Path(TEMP_DIR) / ".autoforge" / "workspace" / ".tokens"
        self.mod = workspace_token_encryption

    def tearDown(self):
        self.home_patcher.stop()
        tf = Path(TEMP_DIR) / ".autoforge" / "workspace" / ".tokens"
        if tf.exists():
            tf.unlink()

    def test_machine_key_stable_bytes(self):
        k1 = self.mod._get_machine_key()
        k2 = self.mod._get_machine_key()
        self.assertIsInstance(k1, bytes)
        self.assertEqual(len(k1), 44)
        self.assertEqual(k1, k2)

    def test_encrypt_decrypt_roundtrip(self):
        token = "ghp_abc123XYZ456"
        encrypted = self.mod.encrypt_token(token)
        self.assertNotEqual(encrypted, token)
        self.assertEqual(self.mod.decrypt_token(encrypted), token)

    def test_store_retrieve_delete(self):
        self.mod.store_token("r1", "secret1")
        self.assertEqual(self.mod.retrieve_token("r1"), "secret1")
        self.assertTrue(self.mod.delete_token("r1"))
        self.assertIsNone(self.mod.retrieve_token("r1"))

    def test_retrieve_nonexistent(self):
        self.assertIsNone(self.mod.retrieve_token("nope"))

    def test_delete_nonexistent(self):
        self.assertFalse(self.mod.delete_token("nope"))

    def test_multiple_tokens(self):
        self.mod.store_token("a", "t1")
        self.mod.store_token("b", "t2")
        self.mod.store_token("c", "t3")
        self.assertEqual(self.mod.retrieve_token("a"), "t1")
        self.assertEqual(self.mod.retrieve_token("b"), "t2")
        self.assertEqual(self.mod.retrieve_token("c"), "t3")

    def test_overwrite_token(self):
        self.mod.store_token("ow", "original")
        self.mod.store_token("ow", "updated")
        self.assertEqual(self.mod.retrieve_token("ow"), "updated")

    def test_encrypted_on_disk(self):
        self.mod.store_token("disk", "plaintext_secret")
        data = json.loads(self.mod.TOKENS_FILE.read_text())
        self.assertIn("disk", data)
        self.assertNotEqual(data["disk"], "plaintext_secret")


class TestDatabaseModels(unittest.TestCase):

    def test_models_importable(self):
        from server.services.workspace_database import (
            WorkspaceLibraryFile, WorkspaceFileActivation, WorkspaceConnectedRepo,
        )
        self.assertEqual(WorkspaceLibraryFile.__tablename__, "workspace_library_files")
        self.assertEqual(WorkspaceFileActivation.__tablename__, "workspace_file_activations")
        self.assertEqual(WorkspaceConnectedRepo.__tablename__, "workspace_connected_repos")

    def test_library_file_columns(self):
        from server.services.workspace_database import WorkspaceLibraryFile
        expected = {"id", "conversation_id", "filename", "display_name", "file_type",
                    "content", "file_path", "file_size", "tags", "active_in_context", "created_at"}
        actual = {c.name for c in WorkspaceLibraryFile.__table__.columns}
        self.assertEqual(expected, actual)

    def test_file_activation_columns(self):
        from server.services.workspace_database import WorkspaceFileActivation
        expected = {"id", "file_id", "conversation_id", "active"}
        actual = {c.name for c in WorkspaceFileActivation.__table__.columns}
        self.assertEqual(expected, actual)

    def test_connected_repo_columns(self):
        from server.services.workspace_database import WorkspaceConnectedRepo
        expected = {"id", "conversation_id", "repo_url", "repo_name", "local_path",
                    "access_token_ref", "branch", "last_synced_at", "created_at"}
        actual = {c.name for c in WorkspaceConnectedRepo.__table__.columns}
        self.assertEqual(expected, actual)

    def test_unique_constraint(self):
        from server.services.workspace_database import WorkspaceFileActivation
        names = [c.name for c in WorkspaceFileActivation.__table__.constraints
                 if hasattr(c, "columns") and len(c.columns) > 1]
        self.assertIn("uq_file_conversation", names)

    def test_tables_create_in_sqlite(self):
        from sqlalchemy import create_engine, inspect
        from server.services.workspace_database import Base
        db_path = Path(TEMP_DIR) / "test_models.db"
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        tables = inspect(engine).get_table_names()
        for t in ["workspace_library_files", "workspace_file_activations", "workspace_connected_repos"]:
            self.assertIn(t, tables)
        engine.dispose()
        db_path.unlink()


class TestLibraryService(unittest.TestCase):

    def setUp(self):
        self.home_patcher = patch("pathlib.Path.home", _fake_home)
        self.home_patcher.start()
        from server.services import workspace_database as db
        db._engine_cache.clear()
        import server.services.workspace_library as lib_mod
        lib_mod.LIBRARY_DIR = Path(TEMP_DIR) / ".autoforge" / "workspace" / "library"

    def tearDown(self):
        self.home_patcher.stop()
        from server.services import workspace_database as db
        db._engine_cache.clear()

    def test_detect_file_type(self):
        from server.services.workspace_library import detect_file_type
        self.assertEqual(detect_file_type("app.py"), "code")
        self.assertEqual(detect_file_type("README.md"), "doc")
        self.assertEqual(detect_file_type("config.json"), "spec")
        self.assertEqual(detect_file_type("data.csv"), "upload")

    def test_validate_extension(self):
        from server.services.workspace_library import validate_file_extension
        self.assertTrue(validate_file_extension("main.py"))
        self.assertTrue(validate_file_extension("Dockerfile"))
        self.assertFalse(validate_file_extension("image.png"))
        self.assertFalse(validate_file_extension("archive.zip"))

    def test_upload_and_get_small_file(self):
        from server.services.workspace_library import upload_file, get_file_content
        r = upload_file("small.txt", b"hello world")
        self.assertEqual(r["filename"], "small.txt")
        self.assertEqual(r["file_type"], "doc")
        self.assertEqual(r["file_size"], 11)
        self.assertFalse(r["active_in_context"])
        self.assertEqual(get_file_content(r["id"]), "hello world")

    def test_upload_text(self):
        from server.services.workspace_library import upload_text, get_file_content
        r = upload_text("notes.md", "# Notes")
        self.assertEqual(r["file_type"], "doc")
        self.assertEqual(get_file_content(r["id"]), "# Notes")

    def test_delete_file(self):
        from server.services.workspace_library import upload_text, delete_file, get_file_content
        r = upload_text("del.txt", "bye")
        self.assertTrue(delete_file(r["id"]))
        self.assertIsNone(get_file_content(r["id"]))
        self.assertFalse(delete_file(r["id"]))

    def test_list_global_files(self):
        from server.services.workspace_library import upload_text, list_global_files
        upload_text("g1.txt", "a")
        upload_text("g2.txt", "b")
        names = [f["filename"] for f in list_global_files()]
        self.assertIn("g1.txt", names)
        self.assertIn("g2.txt", names)

    def test_update_metadata(self):
        from server.services.workspace_library import upload_text, update_file_metadata
        r = upload_text("m.txt", "x")
        u = update_file_metadata(r["id"], display_name="Renamed", tags="a,b")
        self.assertEqual(u["display_name"], "Renamed")
        self.assertEqual(u["tags"], "a,b")

    def test_update_nonexistent(self):
        from server.services.workspace_library import update_file_metadata
        self.assertIsNone(update_file_metadata(99999, display_name="nope"))

    def test_large_file_on_disk(self):
        from server.services.workspace_library import upload_file, get_file_content
        big = b"x" * (101 * 1024)
        r = upload_file("large.txt", big)
        self.assertEqual(r["file_size"], len(big))
        content = get_file_content(r["id"])
        self.assertIsNotNone(content)
        self.assertEqual(len(content), len(big))


class TestLibraryIntegration(unittest.TestCase):

    def setUp(self):
        self.home_patcher = patch("pathlib.Path.home", _fake_home)
        self.home_patcher.start()
        from server.services import workspace_database as db
        db._engine_cache.clear()
        import server.services.workspace_library as lib_mod
        lib_mod.LIBRARY_DIR = Path(TEMP_DIR) / ".autoforge" / "workspace" / "library"

    def tearDown(self):
        self.home_patcher.stop()
        from server.services import workspace_database as db
        db._engine_cache.clear()

    def test_toggle_global_file(self):
        from server.services.workspace_library import upload_text, toggle_file_in_context
        from server.services.workspace_database import create_conversation
        conv = create_conversation(title="Toggle Test")
        f = upload_text("t.txt", "content")
        t1 = toggle_file_in_context(f["id"], conv.id)
        self.assertTrue(t1["active_in_context"])
        t2 = toggle_file_in_context(f["id"], conv.id)
        self.assertFalse(t2["active_in_context"])
        t3 = toggle_file_in_context(f["id"], conv.id)
        self.assertTrue(t3["active_in_context"])

    def test_toggle_per_chat_file(self):
        from server.services.workspace_library import upload_text, toggle_file_in_context
        from server.services.workspace_database import create_conversation
        conv = create_conversation(title="PerChat")
        f = upload_text("pc.txt", "chat", conversation_id=conv.id)
        self.assertFalse(f["active_in_context"])
        t = toggle_file_in_context(f["id"], conv.id)
        self.assertTrue(t["active_in_context"])

    def test_toggle_nonexistent(self):
        from server.services.workspace_library import toggle_file_in_context
        self.assertIsNone(toggle_file_in_context(99999, 99999))

    def test_active_files_context_string(self):
        from server.services.workspace_library import upload_text, toggle_file_in_context, get_active_files_context
        from server.services.workspace_database import create_conversation
        conv = create_conversation(title="Ctx Build")
        f1 = upload_text("s.json", '{"k":"v"}')
        f2 = upload_text("n.md", "# Notes")
        toggle_file_in_context(f1["id"], conv.id)
        toggle_file_in_context(f2["id"], conv.id)
        ctx, tokens = get_active_files_context(conv.id)
        self.assertGreater(len(ctx), 0)
        self.assertGreater(tokens, 0)
        self.assertIn("s.json", ctx)
        self.assertIn("n.md", ctx)
        self.assertIn("--- Library File:", ctx)
        self.assertIn("--- End File ---", ctx)

    def test_conversation_files_includes_global(self):
        from server.services.workspace_library import upload_text, list_conversation_files
        from server.services.workspace_database import create_conversation
        conv = create_conversation(title="List")
        upload_text("gf.txt", "global")
        upload_text("cf.txt", "chat", conversation_id=conv.id)
        names = [f["filename"] for f in list_conversation_files(conv.id)]
        self.assertIn("gf.txt", names)
        self.assertIn("cf.txt", names)

    def test_empty_context(self):
        from server.services.workspace_library import get_active_files_context
        ctx, tokens = get_active_files_context(99999)
        self.assertEqual(ctx, "")
        self.assertEqual(tokens, 0)


class TestReposService(unittest.TestCase):

    def test_validate_url_valid(self):
        from server.services.workspace_repos import validate_repo_url
        self.assertTrue(validate_repo_url("https://github.com/owner/repo"))
        self.assertTrue(validate_repo_url("https://github.com/owner/repo.git"))
        self.assertTrue(validate_repo_url("https://github.com/my-org/my-repo"))

    def test_validate_url_invalid(self):
        from server.services.workspace_repos import validate_repo_url
        self.assertFalse(validate_repo_url("http://github.com/owner/repo"))
        self.assertFalse(validate_repo_url("https://gitlab.com/owner/repo"))
        self.assertFalse(validate_repo_url("git@github.com:owner/repo.git"))
        self.assertFalse(validate_repo_url("https://github.com/repo"))
        self.assertFalse(validate_repo_url(""))

    def test_extract_repo_name(self):
        from server.services.workspace_repos import extract_repo_name
        self.assertEqual(extract_repo_name("https://github.com/owner/repo"), "owner/repo")
        self.assertEqual(extract_repo_name("https://github.com/owner/repo.git"), "owner/repo")

    def test_authenticated_url(self):
        from server.services.workspace_repos import _build_authenticated_url
        r = _build_authenticated_url("https://github.com/o/r", "ghp_tok")
        self.assertEqual(r, "https://ghp_tok@github.com/o/r")

    def test_sanitize_error(self):
        from server.services.workspace_repos import _sanitize_error
        err = "fatal: https://ghp_secret@github.com failed"
        s = _sanitize_error(err, "ghp_secret")
        self.assertNotIn("ghp_secret", s)
        self.assertIn("***", s)

    def test_local_dir_name(self):
        from server.services.workspace_repos import _local_dir_name
        self.assertEqual(_local_dir_name("https://github.com/o/r"), "o_r")

    def test_path_traversal_blocked(self):
        from server.services.workspace_repos import get_repo_file
        from server.services.workspace_database import WorkspaceConnectedRepo
        repo_dir = Path(TEMP_DIR) / "traversal_repo"
        repo_dir.mkdir(exist_ok=True)
        (repo_dir / "safe.txt").write_text("safe")
        (Path(TEMP_DIR) / "secret.txt").write_text("SECRET")

        with patch("pathlib.Path.home", _fake_home):
            from server.services import workspace_database as db
            db._engine_cache.clear()
            session = db.get_db_session()
            try:
                repo = WorkspaceConnectedRepo(repo_url="https://github.com/t/r",
                    repo_name="t/r", local_path=str(repo_dir), branch="main")
                session.add(repo)
                session.commit()
                session.refresh(repo)
                rid = repo.id
            finally:
                session.close()
            self.assertEqual(get_repo_file(rid, "safe.txt"), "safe")
            self.assertIsNone(get_repo_file(rid, "../secret.txt"))
            self.assertIsNone(get_repo_file(rid, "../../etc/passwd"))
            db._engine_cache.clear()
        shutil.rmtree(repo_dir)
        (Path(TEMP_DIR) / "secret.txt").unlink()

    def test_repo_tree(self):
        from server.services.workspace_repos import get_repo_tree
        from server.services.workspace_database import WorkspaceConnectedRepo
        rd = Path(TEMP_DIR) / "tree_repo2"
        rd.mkdir(exist_ok=True)
        (rd / "README.md").write_text("# Hi")
        (rd / "src").mkdir(exist_ok=True)
        (rd / "src" / "main.py").write_text("print(1)")
        (rd / ".git").mkdir(exist_ok=True)
        (rd / ".git" / "HEAD").write_text("ref: refs/heads/main")

        with patch("pathlib.Path.home", _fake_home):
            from server.services import workspace_database as db
            db._engine_cache.clear()
            session = db.get_db_session()
            try:
                repo = WorkspaceConnectedRepo(repo_url="https://github.com/t/tr",
                    repo_name="t/tr", local_path=str(rd), branch="main")
                session.add(repo)
                session.commit()
                session.refresh(repo)
                rid = repo.id
            finally:
                session.close()
            tree = get_repo_tree(rid)
            paths = [e["path"] for e in tree]
            self.assertIn("README.md", paths)
            self.assertIn("src", paths)
            self.assertNotIn(".git", paths)
            types = {e["path"]: e["type"] for e in tree}
            self.assertEqual(types["src"], "dir")
            self.assertEqual(types["README.md"], "file")
            db._engine_cache.clear()
        shutil.rmtree(rd)


class TestRouterEndpoints(unittest.TestCase):
    """Import workspace router directly (bypass __init__ which needs claude_agent_sdk)."""

    @classmethod
    def _get_router(cls):
        import importlib
        # Direct import to bypass server.routers.__init__ which imports claude_agent_sdk
        spec = importlib.util.spec_from_file_location(
            "server.routers.workspace",
            Path(__file__).parent / "server" / "routers" / "workspace.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.router

    def test_library_endpoints_exist(self):
        router = self._get_router()
        routes = {r.path for r in router.routes if hasattr(r, "path")}
        for ep in ["/api/workspace/library", "/api/workspace/library/upload",
                   "/api/workspace/library/upload-text",
                   "/api/workspace/library/conversation/{conversation_id}",
                   "/api/workspace/library/active/{conversation_id}",
                   "/api/workspace/library/{file_id}/content",
                   "/api/workspace/library/{file_id}",
                   "/api/workspace/library/{file_id}/toggle/{conversation_id}"]:
            self.assertIn(ep, routes, f"Missing endpoint: {ep}")

    def test_repo_endpoints_exist(self):
        router = self._get_router()
        routes = {r.path for r in router.routes if hasattr(r, "path")}
        for ep in ["/api/workspace/repos/connect", "/api/workspace/repos/{repo_id}",
                   "/api/workspace/repos", "/api/workspace/repos/{repo_id}/tree",
                   "/api/workspace/repos/{repo_id}/file", "/api/workspace/repos/{repo_id}/sync"]:
            self.assertIn(ep, routes, f"Missing endpoint: {ep}")

    def test_upload_is_post(self):
        router = self._get_router()
        for r in router.routes:
            if hasattr(r, "path") and r.path == "/api/workspace/library/upload":
                self.assertIn("POST", r.methods)
                return
        self.fail("Upload endpoint not found")

    def test_connect_is_post(self):
        router = self._get_router()
        for r in router.routes:
            if hasattr(r, "path") and r.path == "/api/workspace/repos/connect":
                self.assertIn("POST", r.methods)
                return
        self.fail("Connect endpoint not found")

    def test_delete_repo_is_delete(self):
        router = self._get_router()
        for r in router.routes:
            if hasattr(r, "path") and r.path == "/api/workspace/repos/{repo_id}":
                if hasattr(r, "methods") and "DELETE" in r.methods:
                    return
        self.fail("DELETE repos endpoint not found")


def teardown_module():
    try:
        shutil.rmtree(TEMP_DIR)
    except Exception:
        pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
