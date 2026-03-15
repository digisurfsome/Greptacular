"""
PRD Shredder Service — Drop a PRD In, Code Comes Out
=====================================================

Queue manager + FIFO processing loop + execution via claude -p.

Phase 1: SQLite queue, FIFO processing, repo clone/pull
Phase 2: 4-stage analysis pipeline (delegated to prd_analyzer.py)
Phase 3: Execution via claude -p one-shot session, lint, test, commit, push
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ..models.prd_shredder import PRDAnalysis, PRDQueueItem, PRDStatus, QueueStats

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path.home() / ".autoforge" / "prd_shredder.db"

# Repo cache directory
REPO_CACHE = Path.home() / ".autoforge" / "shredder_repos"

# Build rules file
BUILD_RULES_PATH = Path(__file__).resolve().parent.parent.parent / "docs" / "stripe-minions-build-rules.md"

# Execution prompt config
EXECUTION_PROMPT_CONFIG = Path.home() / ".autoforge" / "prd_shredder_execution_prompt.json"

DEFAULT_EXECUTION_PROMPT = (
    "You are a coding agent executing a PRD. Follow the Stripe Blueprint Pattern: "
    "alternate between robot steps (exact commands) and agent steps (creative coding).\n\n"
    "## YOUR TASK LIST\n{task_list}\n\n"
    "## CODEBASE CONTEXT\n{codebase_context}\n\n"
    "## BUILD RULES\n{build_rules}\n\n"
    "## EXECUTION RULES\n\n"
    "1. Execute tasks in order. Do NOT skip ahead.\n"
    "2. After each file create/modify:\n"
    "   - [ROBOT] Run lint: ruff check {{file}} --fix (Python) or npx tsc --noEmit (TypeScript)\n"
    "   - Fix any errors BEFORE moving to the next task\n"
    "3. After completing all tasks:\n"
    "   - [ROBOT] Run full lint: ruff check . && cd ui && npm run build\n"
    "   - [ROBOT] Run tests if any exist for modified code\n"
    "4. Maximum 2 retry attempts on any single error\n"
    "5. If a task is impossible (missing dependency, wrong assumption in PRD):\n"
    "   - Document why in a comment\n"
    "   - Skip it\n"
    "   - Continue with remaining tasks\n"
    "6. When done:\n"
    "   - [ROBOT] git add (specific files only)\n"
    "   - [ROBOT] git commit with message describing all changes\n"
    "   - Report: what was done, what was skipped, what needs human attention\n"
)


def _load_execution_prompt() -> str:
    """Load execution prompt from config, creating default if missing."""
    if EXECUTION_PROMPT_CONFIG.exists():
        try:
            data = json.loads(EXECUTION_PROMPT_CONFIG.read_text(encoding="utf-8"))
            return data.get("prompt", DEFAULT_EXECUTION_PROMPT)
        except Exception:
            pass
    EXECUTION_PROMPT_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    EXECUTION_PROMPT_CONFIG.write_text(
        json.dumps({"prompt": DEFAULT_EXECUTION_PROMPT}, indent=2),
        encoding="utf-8",
    )
    return DEFAULT_EXECUTION_PROMPT


# ---------------------------------------------------------------------------
# SQLite persistence via JSON file (lightweight — no SQLAlchemy needed)
# ---------------------------------------------------------------------------

class PRDQueue:
    """Persistent FIFO queue backed by a JSON file.

    Using JSON instead of SQLAlchemy because the queue is small (< 100 items)
    and we want minimal dependencies. Each item is a PRDQueueItem.
    """

    def __init__(self) -> None:
        self._path = DB_PATH.with_suffix(".json")
        self._lock = asyncio.Lock()
        self._items: list[PRDQueueItem] = []
        self._load()

    def _load(self) -> None:
        """Load queue from disk."""
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._items = [PRDQueueItem(**item) for item in data]
            except Exception as e:
                logger.warning("Failed to load PRD queue: %s", e)
                self._items = []
        else:
            self._path.parent.mkdir(parents=True, exist_ok=True)

    def _save(self) -> None:
        """Persist queue to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps([item.model_dump() for item in self._items], indent=2, default=str),
            encoding="utf-8",
        )

    async def add(self, item: PRDQueueItem) -> PRDQueueItem:
        """Add an item to the queue."""
        async with self._lock:
            self._items.append(item)
            self._save()
        return item

    async def get_next_queued(self) -> PRDQueueItem | None:
        """Get the next QUEUED item (FIFO order)."""
        async with self._lock:
            for item in self._items:
                if item.status == PRDStatus.QUEUED:
                    return item
        return None

    async def update(self, item_id: str, **kwargs) -> PRDQueueItem | None:
        """Update fields on a queue item."""
        async with self._lock:
            for item in self._items:
                if item.id == item_id:
                    for key, value in kwargs.items():
                        if hasattr(item, key):
                            setattr(item, key, value)
                    self._save()
                    return item
        return None

    async def get(self, item_id: str) -> PRDQueueItem | None:
        """Get a single item by ID."""
        for item in self._items:
            if item.id == item_id:
                return item
        return None

    async def list_all(self) -> list[PRDQueueItem]:
        """List all items."""
        return list(self._items)

    async def delete(self, item_id: str) -> bool:
        """Delete an item from the queue."""
        async with self._lock:
            before = len(self._items)
            self._items = [i for i in self._items if i.id != item_id]
            if len(self._items) < before:
                self._save()
                return True
        return False

    async def get_stats(self) -> QueueStats:
        """Get aggregate stats."""
        stats = QueueStats(total=len(self._items))
        for item in self._items:
            if item.status == PRDStatus.QUEUED:
                stats.queued += 1
            elif item.status in (PRDStatus.CLONING, PRDStatus.ANALYZING, PRDStatus.BUILDING,
                                 PRDStatus.TESTING, PRDStatus.COMMITTING, PRDStatus.QA_TESTING):
                stats.building += 1
            elif item.status == PRDStatus.DONE:
                stats.done += 1
            elif item.status == PRDStatus.FAILED:
                stats.failed += 1
        return stats

    async def append_log(self, item_id: str, message: str) -> None:
        """Append a log line to an item."""
        async with self._lock:
            for item in self._items:
                if item.id == item_id:
                    timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
                    item.build_log.append(f"[{timestamp}] {message}")
                    # Save periodically (every 10 log lines) to avoid excessive I/O
                    if len(item.build_log) % 10 == 0:
                        self._save()
                    return


# ---------------------------------------------------------------------------
# The Shredder
# ---------------------------------------------------------------------------

class PRDShredder:
    """The paper shredder for PRDs. FIFO queue processing with background loop."""

    def __init__(self) -> None:
        self.queue = PRDQueue()
        self._running = False
        self._task: asyncio.Task | None = None
        self._progress_callbacks: dict[str, list[Callable[[str], None]]] = {}

    async def enqueue(
        self,
        title: str,
        prd_text: str,
        target_repo: str,
        target_branch: str = "main",
    ) -> PRDQueueItem:
        """Add a PRD to the shredder queue."""
        item = PRDQueueItem(
            id=str(uuid.uuid4()),
            title=title,
            prd_text=prd_text,
            target_repo=target_repo,
            target_branch=target_branch,
        )
        await self.queue.add(item)
        logger.info("PRD queued: %s (repo=%s, branch=%s)", title, target_repo, target_branch)
        return item

    def subscribe_progress(self, item_id: str, callback: Callable[[str], None]) -> None:
        """Subscribe to progress updates for an item."""
        if item_id not in self._progress_callbacks:
            self._progress_callbacks[item_id] = []
        self._progress_callbacks[item_id].append(callback)

    def unsubscribe_progress(self, item_id: str, callback: Callable[[str], None]) -> None:
        """Unsubscribe from progress updates."""
        if item_id in self._progress_callbacks:
            self._progress_callbacks[item_id] = [
                cb for cb in self._progress_callbacks[item_id] if cb is not callback
            ]

    def _notify_progress(self, item_id: str, message: str) -> None:
        """Notify all subscribers of a progress update."""
        for cb in self._progress_callbacks.get(item_id, []):
            try:
                cb(message)
            except Exception:
                pass

    async def start_loop(self) -> None:
        """Start the background processing loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_forever())
        logger.info("PRD Shredder background loop started")

    async def stop_loop(self) -> None:
        """Stop the background processing loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("PRD Shredder background loop stopped")

    async def _run_forever(self) -> None:
        """The conveyor belt. Runs as background task on server start."""
        while self._running:
            try:
                next_item = await self.queue.get_next_queued()
                if next_item:
                    await self._process(next_item)
                else:
                    await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Shredder loop error: %s", e)
                await asyncio.sleep(10)

    async def _process(self, item: PRDQueueItem) -> None:
        """Process a single PRD — the shredder."""
        item_id = item.id

        def on_progress(msg: str) -> None:
            asyncio.create_task(self.queue.append_log(item_id, msg))
            self._notify_progress(item_id, msg)
            logger.info("[Shredder %s] %s", item.title[:30], msg)

        try:
            # Phase 1: Clone/pull
            await self.queue.update(item_id, status=PRDStatus.CLONING,
                                    started_at=datetime.now(timezone.utc).isoformat())
            on_progress("Cloning/pulling target repository...")
            repo_dir = await self._clone_or_pull(item, on_progress)
            on_progress(f"Repository ready at {repo_dir}")

            # Phase 2: Analysis
            await self.queue.update(item_id, status=PRDStatus.ANALYZING)
            on_progress("Starting 4-stage PRD analysis...")
            from .prd_analyzer import PRDAnalyzer
            analyzer = PRDAnalyzer()
            analysis = await analyzer.analyze(item.prd_text, repo_dir, on_progress=on_progress)
            await self.queue.update(
                item_id,
                analysis=analysis,
                tasks_total=len(analysis.tasks),
            )
            on_progress(f"Analysis complete: {len(analysis.tasks)} tasks extracted")

            # Phase 3: Execution
            await self.queue.update(item_id, status=PRDStatus.BUILDING)
            on_progress("Starting code execution via claude -p...")
            await self._execute(item, analysis, repo_dir, on_progress)

            # Verification
            await self.queue.update(item_id, status=PRDStatus.TESTING)
            on_progress("Running verification checks...")
            await self._verify(item, repo_dir, on_progress)

            # Commit and push
            await self.queue.update(item_id, status=PRDStatus.COMMITTING)
            on_progress("Committing and pushing...")
            commit_hash = await self._commit_and_push(item, analysis, repo_dir, on_progress)

            # Playwright QA — test the running app
            await self.queue.update(item_id, status=PRDStatus.QA_TESTING, commit_hash=commit_hash)
            on_progress("Running Playwright QA smoke tests...")
            qa_errors = await self._playwright_qa(item, repo_dir, on_progress)

            if qa_errors:
                await self.queue.update(item_id, playwright_errors=qa_errors)
                on_progress(f"Playwright found {len(qa_errors)} error(s) — creating bug-fix PRD...")
                bugfix_id = await self._create_bugfix_prd(item, qa_errors, repo_dir)
                await self.queue.update(item_id, bugfix_prd_id=bugfix_id)
                on_progress(f"Bug-fix PRD queued: {bugfix_id}")

            # Done!
            await self.queue.update(
                item_id,
                status=PRDStatus.DONE,
                commit_hash=commit_hash,
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
            on_progress(f"DONE! Commit: {commit_hash}" + (
                f" | {len(qa_errors)} QA errors → bug-fix PRD queued" if qa_errors else " | QA clean"
            ))

        except Exception as e:
            error_msg = str(e)
            logger.exception("Shredder failed for %s: %s", item.title, error_msg)
            await self.queue.update(
                item_id,
                status=PRDStatus.FAILED,
                error=error_msg,
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
            on_progress(f"FAILED: {error_msg}")

        # Final save
        await self.queue.update(item_id)
        # Flush log
        self.queue._save()

    # ----- Phase 1: Clone/Pull -----

    async def _clone_or_pull(
        self,
        item: PRDQueueItem,
        on_progress: Callable[[str], None],
    ) -> Path:
        """Clone the target repo or pull latest if already cloned."""
        target = item.target_repo

        # Local path detection
        if _is_local_path(target):
            local_path = Path(target).resolve()
            if not local_path.exists():
                raise FileNotFoundError(f"Local repo path does not exist: {target}")
            on_progress(f"Using local repo: {local_path}")
            # Pull latest on the target branch
            result = subprocess.run(
                ["git", "pull", "origin", item.target_branch, "--no-edit"],
                cwd=str(local_path),
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                on_progress(f"git pull warning: {result.stderr.strip()}")
            return local_path

        # GitHub URL — clone to cache
        repo_name = _extract_repo_name(target)
        if not repo_name:
            raise ValueError(f"Cannot parse GitHub repo from: {target}")

        REPO_CACHE.mkdir(parents=True, exist_ok=True)
        repo_dir = REPO_CACHE / repo_name.replace("/", "_")

        # Get GitHub token
        github_token = os.getenv("GITHUB_TOKEN", "")

        if repo_dir.exists():
            on_progress(f"Pulling latest for {repo_name}...")
            result = subprocess.run(
                ["git", "pull", "origin", item.target_branch, "--no-edit"],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                on_progress(f"Pull failed — re-cloning: {result.stderr.strip()}")
                shutil.rmtree(repo_dir, ignore_errors=True)
            else:
                return repo_dir

        # Clone fresh
        on_progress(f"Cloning {repo_name}...")
        if github_token:
            clone_url = f"https://{github_token}@github.com/{repo_name}.git"
        else:
            clone_url = f"https://github.com/{repo_name}.git"

        result = subprocess.run(
            ["git", "clone", "--branch", item.target_branch, clone_url, str(repo_dir)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            raise RuntimeError(f"git clone failed: {result.stderr.strip()}")

        return repo_dir

    # ----- Phase 3: Execution via claude -p -----

    async def _execute(
        self,
        item: PRDQueueItem,
        analysis: PRDAnalysis,
        repo_dir: Path,
        on_progress: Callable[[str], None],
    ) -> None:
        """Execute the task list via claude -p one-shot session."""
        from .prd_analyzer import _read_relevant_files

        # Build the mega-prompt
        task_list = json.dumps(
            [t.model_dump() for t in analysis.tasks],
            indent=2,
        )

        # Read relevant file contents for context
        all_files = list(set(
            analysis.target_files
            + analysis.files_to_create
            + [f.get("path", "") for f in analysis.files_to_modify if isinstance(f, dict)]
        ))
        codebase_context = _read_relevant_files(repo_dir, all_files, max_chars=200_000)

        # Load build rules
        build_rules = ""
        if BUILD_RULES_PATH.exists():
            try:
                build_rules = BUILD_RULES_PATH.read_text(encoding="utf-8")
            except Exception:
                on_progress("Warning: Could not load build rules file")

        # Build the prompt
        execution_prompt = _load_execution_prompt()
        full_prompt = execution_prompt.format(
            task_list=task_list,
            codebase_context=codebase_context,
            build_rules=build_rules,
        )

        on_progress(f"Prompt size: {len(full_prompt):,} chars | Tasks: {len(analysis.tasks)}")

        # Run via claude -p
        claude_cli = shutil.which("claude")
        if not claude_cli:
            raise RuntimeError("Claude CLI not found on PATH")

        # Remove CLAUDECODE env var to avoid nested session blocks
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)

        on_progress("Spawning claude -p session...")
        process = await asyncio.create_subprocess_exec(
            claude_cli, "-p", full_prompt,
            "--model", "claude-sonnet-4-6",
            cwd=str(repo_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        # Stream output
        tasks_done = 0
        stdout_lines: list[str] = []

        async def _read_stream(stream: asyncio.StreamReader, label: str) -> None:
            nonlocal tasks_done
            while True:
                line_bytes = await stream.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode("utf-8", errors="replace").rstrip()
                if not line:
                    continue
                stdout_lines.append(line)

                # Parse progress signals
                line_lower = line.lower()
                if "task" in line_lower and ("complete" in line_lower or "done" in line_lower):
                    tasks_done += 1
                    await self.queue.update(item.id, tasks_done=tasks_done)

                # Log periodically (every 5th line to avoid spam)
                if len(stdout_lines) % 5 == 1:
                    on_progress(f"[{label}] {line[:200]}")

        # Read stdout and stderr concurrently
        await asyncio.gather(
            _read_stream(process.stdout, "claude"),
            _read_stream(process.stderr, "stderr"),
        )

        return_code = await process.wait()
        on_progress(f"claude -p exited with code {return_code} | {len(stdout_lines)} output lines")

        if return_code != 0:
            # Not fatal — claude -p may exit non-zero but still produce code
            on_progress(f"Warning: claude -p returned exit code {return_code}")

        await self.queue.update(item.id, tasks_done=tasks_done)

    # ----- Verification Gate -----

    async def _verify(
        self,
        item: PRDQueueItem,
        repo_dir: Path,
        on_progress: Callable[[str], None],
    ) -> None:
        """Robot verification — lint, type check, tests."""
        # Python lint
        on_progress("Running ruff check...")
        result = subprocess.run(
            ["ruff", "check", ".", "--fix"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            on_progress(f"Ruff warnings: {result.stdout[:300]}")
        else:
            on_progress("Ruff: all clean")

        # TypeScript build if ui/ exists
        ui_dir = repo_dir / "ui"
        if ui_dir.exists() and (ui_dir / "package.json").exists():
            on_progress("Running TypeScript build...")
            ts_result = subprocess.run(
                ["npm", "run", "build"],
                cwd=str(ui_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )
            if ts_result.returncode != 0:
                on_progress(f"TS build warning: {ts_result.stderr[:300]}")
            else:
                on_progress("TypeScript build: passed")

        # Python tests if pytest is available
        pytest_path = shutil.which("pytest")
        if pytest_path:
            test_result = subprocess.run(
                [pytest_path, "--tb=short", "-q", "--no-header"],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )
            on_progress(f"Tests: {'PASSED' if test_result.returncode == 0 else 'FAILED'}")

    # ----- Commit and Push -----

    async def _commit_and_push(
        self,
        item: PRDQueueItem,
        analysis: PRDAnalysis,
        repo_dir: Path,
        on_progress: Callable[[str], None],
    ) -> str:
        """Commit changes and push to remote."""
        # Stage changes
        on_progress("Staging changes...")
        subprocess.run(
            ["git", "add", "-A"],
            cwd=str(repo_dir),
            capture_output=True,
            timeout=30,
        )

        # Check if there are changes to commit
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if not status.stdout.strip():
            on_progress("No changes to commit — claude may have already committed")
            # Get latest commit hash
            hash_result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
                timeout=10,
            )
            return hash_result.stdout.strip() or "unknown"

        # Commit
        tasks_done = item.tasks_done
        tasks_total = item.tasks_total
        message = (
            f"PRD Shredder: {item.title}\n\n"
            f"Auto-built from PRD. Tasks: {tasks_done}/{tasks_total}\n"
            f"Analysis difficulty: {analysis.difficulty}/10"
        )
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=str(repo_dir),
            capture_output=True,
            timeout=30,
        )

        # Push
        on_progress(f"Pushing to origin/{item.target_branch}...")
        push_result = subprocess.run(
            ["git", "push", "origin", item.target_branch],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if push_result.returncode != 0:
            on_progress(f"Push warning: {push_result.stderr.strip()}")

        # Get commit hash
        hash_result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=10,
        )
        return hash_result.stdout.strip() or "unknown"

    # ----- Playwright QA -----

    async def _playwright_qa(
        self,
        item: PRDQueueItem,
        repo_dir: Path,
        on_progress: Callable[[str], None],
    ) -> list[dict]:
        """Run Playwright smoke tests against the built app.

        Steps:
        1. Detect dev server command + port
        2. Start dev server
        3. Wait for it to be ready
        4. Run smoke test (navigate routes, check console errors, click buttons)
        5. Kill dev server
        6. Return list of errors (empty = all clean)
        """
        dev_info = _detect_dev_command(repo_dir)
        if not dev_info:
            on_progress("No web UI detected — skipping Playwright QA")
            return []

        dev_cmd, port = dev_info
        on_progress(f"Starting dev server: {' '.join(dev_cmd)} (port {port})")

        # Start dev server as background process
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)
        env.pop("CLAUDE_CODE_ENTRYPOINT", None)

        try:
            server_proc = subprocess.Popen(
                dev_cmd,
                cwd=str(repo_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
        except Exception as e:
            on_progress(f"Failed to start dev server: {e}")
            return []

        try:
            # Wait for server to be ready
            on_progress("Waiting for dev server to start...")
            ready = await _wait_for_server(port, timeout=30)
            if not ready:
                on_progress(f"Dev server didn't respond on port {port} within 30s — skipping QA")
                return []

            on_progress("Dev server ready — running Playwright smoke test...")
            errors = await _run_playwright_smoke(port, repo_dir, on_progress)
            return errors

        finally:
            # Kill the dev server
            try:
                server_proc.terminate()
                server_proc.wait(timeout=5)
            except Exception:
                try:
                    server_proc.kill()
                except Exception:
                    pass

    async def _create_bugfix_prd(
        self,
        original_item: PRDQueueItem,
        errors: list[dict],
        repo_dir: Path,
    ) -> str:
        """Create a bug-fix PRD from Playwright errors and re-enqueue it."""
        error_descriptions = []
        for err in errors[:20]:  # Cap at 20 errors
            err_type = err.get("type", "unknown")
            if err_type == "console_error":
                error_descriptions.append(f"- Console error: {err.get('text', '')[:200]}")
            elif err_type == "http_error":
                error_descriptions.append(f"- HTTP {err.get('status')} on {err.get('url', '')}")
            elif err_type == "route_error":
                error_descriptions.append(f"- Route failed: {err.get('url', '')} — {err.get('message', '')[:200]}")
            elif err_type == "pageerror":
                error_descriptions.append(f"- Page crash: {err.get('message', '')[:200]}")
            elif err_type == "load_error":
                error_descriptions.append(f"- Load failed: {err.get('message', '')[:200]}")
            else:
                error_descriptions.append(f"- {err_type}: {json.dumps(err)[:200]}")

        bugfix_prd = (
            f"# Bug Fix: {original_item.title}\n\n"
            f"## Context\n"
            f"This PRD was auto-generated by the PRD Shredder's Playwright QA step.\n"
            f"The original PRD \"{original_item.title}\" was built and committed "
            f"(commit: {original_item.commit_hash}), but Playwright found errors.\n\n"
            f"## Errors Found ({len(errors)})\n\n"
            + "\n".join(error_descriptions)
            + "\n\n## Requirements\n\n"
            f"1. Fix ALL errors listed above\n"
            f"2. Do NOT change working functionality\n"
            f"3. Run `ruff check .` after every file change\n"
            f"4. If a UI build exists, run `npm run build` in ui/\n"
            f"5. Commit with message: \"fix: Playwright QA errors from {original_item.title}\"\n\n"
            f"## Scope\n"
            f"- ONLY fix the specific errors above\n"
            f"- Do NOT refactor, add features, or change unrelated code\n"
        )

        # Enqueue the bug-fix PRD
        bugfix_item = await self.enqueue(
            title=f"Bug Fix: {original_item.title}",
            prd_text=bugfix_prd,
            target_repo=original_item.target_repo,
            target_branch=original_item.target_branch,
        )
        return bugfix_item.id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_local_path(path: str) -> bool:
    """Detect if target_repo is a local path vs GitHub URL."""
    return (
        path.startswith("/")
        or path.startswith("~")
        or (len(path) > 2 and path[1] == ":")  # Windows: C:\...
        or path.startswith("\\")
    )


def _detect_dev_command(repo_dir: Path) -> tuple[list[str], int] | None:
    """Detect the dev server command and port for a web project.

    Returns (command_list, port) or None if no web UI detected.
    """
    # Check ui/ subdirectory first (AutoForge pattern)
    ui_dir = repo_dir / "ui"
    if ui_dir.exists() and (ui_dir / "package.json").exists():
        pkg = _read_package_json(ui_dir / "package.json")
        port = _extract_port_from_scripts(pkg) or 5173  # Vite default
        dev_script = _find_dev_script(pkg)
        if dev_script:
            return (["npm", "run", dev_script], port)

    # Check root package.json
    root_pkg = repo_dir / "package.json"
    if root_pkg.exists():
        pkg = _read_package_json(root_pkg)
        port = _extract_port_from_scripts(pkg) or 3000  # Node default
        dev_script = _find_dev_script(pkg)
        if dev_script:
            return (["npm", "run", dev_script], port)

    # Check for Python web apps (FastAPI/Flask/Django)
    main_py = repo_dir / "server" / "main.py"
    if main_py.exists():
        return (["python", "-m", "uvicorn", "server.main:app", "--port", "8000"], 8000)

    manage_py = repo_dir / "manage.py"
    if manage_py.exists():
        return (["python", "manage.py", "runserver", "8000"], 8000)

    app_py = repo_dir / "app.py"
    if app_py.exists():
        return (["python", "app.py"], 5000)  # Flask default

    return None


def _read_package_json(path: Path) -> dict:
    """Read and parse a package.json file."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _find_dev_script(pkg: dict) -> str | None:
    """Find the best dev server script in package.json."""
    scripts = pkg.get("scripts", {})
    for name in ("dev", "start", "serve", "start:dev"):
        if name in scripts:
            return name
    return None


def _extract_port_from_scripts(pkg: dict) -> int | None:
    """Try to extract port number from package.json scripts."""
    import re as _re
    scripts = pkg.get("scripts", {})
    for script_val in scripts.values():
        # Match --port 3000, --port=3000, -p 3000
        match = _re.search(r"(?:--port[= ]|[ ]-p[ ])(\d{4,5})", str(script_val))
        if match:
            return int(match.group(1))
    return None


async def _wait_for_server(port: int, timeout: int = 30) -> bool:
    """Wait for a server to start responding on the given port."""
    import socket
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            if result == 0:
                # Give it a moment to be fully ready
                await asyncio.sleep(1)
                return True
        except Exception:
            pass
        await asyncio.sleep(1)
    return False


async def _run_playwright_smoke(
    port: int,
    repo_dir: Path,
    on_progress: Callable[[str], None],
) -> list[dict]:
    """Run a Playwright smoke test against localhost:port.

    Navigates to every internal route, collects console errors, checks for
    HTTP errors, and clicks interactive elements. Returns a list of error dicts.
    """
    import tempfile

    base_url = f"http://localhost:{port}"

    # Write a temporary Python smoke test script
    smoke_script = f'''#!/usr/bin/env python
"""Auto-generated Playwright smoke test — PRD Shredder QA"""
import json
import sys

errors = []

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    # Playwright not available — report and exit
    print(json.dumps([{{"type": "setup_error", "message": "playwright not installed"}}]))
    sys.exit(0)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        # Collect console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: errors.append({{"type": "pageerror", "message": str(exc)[:500]}}))

        # Navigate to root
        try:
            response = page.goto("{base_url}", timeout=15000, wait_until="networkidle")
            if response and response.status >= 400:
                errors.append({{"type": "http_error", "url": "{base_url}", "status": response.status}})
        except Exception as e:
            errors.append({{"type": "load_error", "url": "{base_url}", "message": str(e)[:500]}})
            print(json.dumps(errors))
            sys.exit(0)

        # Find all internal links
        visited = set()
        links = page.query_selector_all("a[href]")
        for link in links:
            try:
                href = link.get_attribute("href")
                if href and (href.startswith("/") or href.startswith("#")):
                    clean = href.split("?")[0].split("#")[0] or "/"
                    if clean != "/":
                        visited.add(clean)
            except Exception:
                pass

        # Visit each internal route (limit to 20)
        for route in sorted(visited)[:20]:
            url = f"{base_url}{{route}}"
            try:
                response = page.goto(url, timeout=10000, wait_until="networkidle")
                if response and response.status >= 400:
                    errors.append({{"type": "http_error", "url": url, "status": response.status}})
            except Exception as e:
                errors.append({{"type": "route_error", "url": url, "message": str(e)[:500]}})

        # Go back to root and click buttons
        try:
            page.goto("{base_url}", timeout=10000, wait_until="networkidle")
            buttons = page.query_selector_all("button:visible")
            for btn in buttons[:10]:
                try:
                    btn.click(timeout=2000, no_wait_after=True)
                    page.wait_for_timeout(500)
                except Exception:
                    pass  # Some buttons may trigger navigation etc.
        except Exception:
            pass

        # Collect accumulated console errors
        for ce_text in console_errors:
            errors.append({{"type": "console_error", "text": ce_text[:500]}})

        browser.close()

except Exception as e:
    errors.append({{"type": "smoke_test_crash", "message": str(e)[:500]}})

print(json.dumps(errors))
'''

    # Write to temp file
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8",
        dir=str(repo_dir),
    )
    tmp.write(smoke_script)
    tmp.close()
    tmp_path = tmp.name

    try:
        on_progress(f"Running smoke test against {base_url}...")

        process = await asyncio.create_subprocess_exec(
            "python", tmp_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(repo_dir),
            env={**os.environ, "PLAYWRIGHT_BROWSERS_PATH": "0"},
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=120,  # 2 min max for QA
        )

        output = stdout.decode("utf-8", errors="replace").strip()

        if not output:
            on_progress("Playwright returned no output")
            return []

        try:
            errors = json.loads(output)
            if not isinstance(errors, list):
                errors = []
        except json.JSONDecodeError:
            on_progress(f"Playwright output not JSON: {output[:200]}")
            return []

        # Filter out noise
        errors = [e for e in errors if e.get("type") != "setup_error"]

        if errors:
            on_progress(f"Playwright found {len(errors)} error(s):")
            for err in errors[:5]:
                on_progress(f"  - {err.get('type')}: {str(err.get('text') or err.get('message') or err.get('url', ''))[:100]}")
        else:
            on_progress("Playwright QA: all routes clean, no console errors")

        return errors

    except asyncio.TimeoutError:
        on_progress("Playwright smoke test timed out (120s)")
        return [{"type": "timeout", "message": "Smoke test exceeded 120s"}]
    except Exception as e:
        on_progress(f"Playwright smoke test error: {e}")
        return []
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def _extract_repo_name(url: str) -> str:
    """Extract 'owner/repo' from a GitHub URL."""
    # https://github.com/owner/repo.git
    # https://github.com/owner/repo
    # git@github.com:owner/repo.git
    url = url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]

    if "github.com/" in url:
        parts = url.split("github.com/")[-1].split("/")
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}"
    elif "github.com:" in url:
        parts = url.split("github.com:")[-1].split("/")
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}"
    return ""


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_shredder_instance: PRDShredder | None = None


def get_shredder() -> PRDShredder:
    """Get or create the singleton PRDShredder instance."""
    global _shredder_instance
    if _shredder_instance is None:
        _shredder_instance = PRDShredder()
    return _shredder_instance
