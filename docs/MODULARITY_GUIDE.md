# Greptacular Modularity Guide: How to Make Your Customizations Upgrade-Proof

## The Core Insight

Your customizations naturally fall into **three layers** around AutoForge:

```
┌──────────────────────────────────────────────────────┐
│                  YOUR PARALLEL STUFF                  │
│    Workspace, DunkStack, Role Library, Swarm          │
│    (sits alongside AutoForge, barely touches it)      │
├──────────────────────────────────────────────────────┤
│  PRE ──►  ┌─────────────────────┐  ──► POST          │
│           │                     │                     │
│ Boiler-   │    AUTOFORGE CORE   │   QA Pipeline       │
│ plates    │                     │   Reviewer Agent    │
│ Styles    │  (upstream code)    │   Notifications     │
│ Design    │                     │   CI Monitor        │
│ Guide     │                     │   Computer Use QA   │
│           └─────────────────────┘                     │
│                                                       │
│  MIDDLE (intertwined with core) ───────────────────── │
│  ~12 files: client.py, orchestrator, database, etc.   │
└──────────────────────────────────────────────────────┘
```

**The good news**: ~60% of your work is PARALLEL (barely touches core) and ~15% is clean PRE/POST. Those are already naturally API-shaped and could be disconnected today.

**The hard part**: ~25% is MIDDLE -- changes woven into AutoForge's guts. Those ~12 files will always need manual merge attention, but can be minimized with an adapter pattern.

---

## What You Have Today: File-by-File Classification

### PARALLEL Features (60% -- Already Nearly Pluggable)

These are basically independent apps riding the same FastAPI server:

| Feature | Backend Files | UI Files | AutoForge Touchpoints |
|---------|--------------|----------|----------------------|
| **IdeaForge Workspace** | `server/routers/workspace.py`, `server/services/workspace_*.py` (6 files) | `ui/src/pages/WorkspacePage.tsx`, `ui/src/components/workspace/` (~25 components), `ui/src/hooks/useWorkspace*.ts` (5 hooks) | Only imports `security.py` hook for its chat session. Own database at `~/.autoforge/workspace.db` |
| **Role Library** | `server/routers/role_library.py` | `ui/src/pages/RoleLibraryPage.tsx`, `ui/src/hooks/useRoleLibrary.ts` | Uses workspace database. Zero core touchpoints |
| **DunkStack** | `server/routers/dunkstack.py` | `ui/src/pages/DunkStackPage.tsx`, `ui/src/components/dunkstack/` (3 files), `ui/src/hooks/useDunkStack.ts` | Reads/writes `.agent/` directory. Zero core touchpoints |
| **Swarm** | `server/routers/swarm.py`, `server/services/swarm_orchestrator.py` | (uses workspace UI) | Uses `workspace_chat_session.py`. Medium coupling |

**Why these are easy to disconnect**: They have their own databases, their own routes, their own UI pages. The only wire into AutoForge is that they're registered in `server/main.py` and share the same FastAPI app. You could literally `git rm` all workspace files and AutoForge wouldn't notice.

### PRE Features (Feeds INTO AutoForge -- 15%)

These run before AutoForge starts building. They prepare the project:

| Feature | Backend Files | How It Connects |
|---------|--------------|-----------------|
| **Boilerplate Selection** | `server/services/boilerplate_manager.py` | Called from `projects.py:create_project()` to clone a starter template before the initializer agent runs |
| **Style System** | `server/services/style_manager.py`, `style_extractor.py`, `style_modifiers.py` | Called from `projects.py:create_project()` to write `.autoforge/style_guide.md` and CSS files into the project |
| **Design Guide Chat** | `server/services/design_guide_session.py`, `server/routers/design_guide.py` | Independent WebSocket chat during project creation. Outputs style selection |
| **Style Context in Prompts** | 2 functions in `prompts.py` | `_get_boilerplate_context()` and `_get_style_context()` inject extra sections into agent prompts |
| **Pre-Build Intelligence** | Flags in `process_manager.py` | Passes `--skip-spec-analysis`, `--min-spec-score` etc. to `autonomous_agent_demo.py` |
| **Agent Prompt Templates** | `.claude/templates/architect_prompt.template.md`, `qa_prompt.template.md`, `reviewer_prompt.template.md`, `spec_analyzer_prompt.template.md` | Loaded by `prompts.py` using existing fallback pattern |

**Why these are fairly easy**: The handoff point is clear -- they produce files and config, then AutoForge takes over. The only coupling is the 2 functions added to `prompts.py` and the extra parameters in `process_manager.py`.

### POST Features (Takes FROM AutoForge -- 10%)

These consume AutoForge's output after it finishes building:

| Feature | Backend Files | How It Connects |
|---------|--------------|-----------------|
| **Pushover/Twilio Notifications** | Functions in `progress.py` | Called when features complete. Pure functions, easy to extract |
| **Reviewer Agent Pipeline** | Logic in `parallel_orchestrator.py` | Spawns reviewer agents after all coding features pass. **Deeply woven into orchestrator loop** |
| **QA Agent Pipeline** | Logic in `parallel_orchestrator.py` | Spawns QA agent after review completes. **Deeply woven into orchestrator loop** |
| **Computer Use QA** | `computer_use.py` | Called after QA pipeline. References `prompts.py` for template |
| **CI Monitor** | `server/services/ci_monitor.py`, `server/routers/ci_status.py` | Polls GitHub Actions. Completely standalone |
| **QA Reports** | Endpoints in `features.py` | Reads `.autoforge/qa-report.md` from project dir. Standalone |

**Why POST is mostly easy except the QA pipeline**: CI monitor, notifications, and report reading are all standalone. But the reviewer/QA agent lifecycle is stitched into the parallel orchestrator's scheduling loop -- that's MIDDLE territory.

### MIDDLE Features (~12 Files -- The Hard Part)

These are changes to AutoForge's core that can't just be unplugged:

| File | What You Changed | Why It's Hard |
|------|-----------------|---------------|
| **`client.py`** | Added 4 agent types (reviewer, qa, spec-analyzer, architect) with unique tool allowlists. Added Playwright MCP config. Changed billing (API vs subscription split). Reduced max_turns. Added context budget enforcement | This IS the agent factory. Every agent type config lives here |
| **`parallel_orchestrator.py`** | Added reviewer/QA agent lifecycle, budget-aware batch sizing, removed graceful pause/drain | The scheduling loop is the core control flow |
| **`api/database.py`** | Replaced `needs_human_input` columns with `reviewed`/`qa_verified` | **Incompatible schema** -- upstream and fork can't share the same DB |
| **`server/schemas.py`** | Removed Human Input types, added QA pipeline + pre-build + walkie-talkie settings | API contract divergence |
| **`mcp_server/feature_mcp.py`** | Added `feature_mark_reviewed`, `feature_mark_qa_verified`, `feature_split`; removed `feature_request_human_input` | MCP tool API change |
| **`agent.py`** | Added turn counting, budget checkpoints | Core streaming loop modification |
| **`progress.py`** | Changed return signature (4-tuple to 3-tuple), added notification functions | Cascading signature change |
| **`prompts.py`** | Added boilerplate/style context injection, new prompt loaders | Medium -- follows existing pattern |
| **`registry.py`** | Added model lock, removed Azure provider | Config divergence |
| **`process_manager.py`** | Removed playwright-cli, graceful pause; added pre-build flags | Control flow divergence |
| **`server/websocket.py`** | Removed drain patterns, human_input tracking | Event system changes |
| **`server/routers/features.py`** | Added QA endpoints, removed human input resolution | API endpoint divergence |

---

## If You Had to Do It Over Again: The Pluggable Architecture

### The Goal

When upstream releases a new version, you want to be able to:
1. Drop in the new AutoForge core (replace ~50 upstream files)
2. Re-attach your PRE/POST/PARALLEL features
3. Only manually merge ~12 MIDDLE files
4. Everything works

### Step 1: Extensions Directory for PARALLEL Features

```
extensions/
  workspace/
    __init__.py          # exports router, cleanup()
    router.py            # FastAPI router
    services/
      database.py
      chat_session.py
      github.py
      ...
    ui/                  # React components (lazy-loaded)
  dunkstack/
    __init__.py
    router.py
    ui/
  role_library/
    __init__.py
    router.py
    ui/
  swarm/
    __init__.py
    router.py
    services/
```

In `server/main.py`:
```python
# Dynamic extension loading
import importlib, pkgutil
for finder, name, _ in pkgutil.iter_modules(["extensions"]):
    ext = importlib.import_module(f"extensions.{name}")
    if hasattr(ext, "router"):
        app.include_router(ext.router, prefix=f"/api/{name}")
    if hasattr(ext, "cleanup"):
        register_cleanup(ext.cleanup)
```

**Result**: You can `git rm -r extensions/workspace` or add a new `extensions/billing` without touching any core file.

### Step 2: Hook Interfaces for PRE/POST

```python
# hooks.py -- the interface definitions

class ProjectCreationHook:
    """Runs during project creation wizard"""
    def get_wizard_steps(self) -> list[WizardStep]:
        """Additional UI steps to show in NewProjectModal"""
        return []

    async def on_project_created(self, project_dir: str, config: dict):
        """Called after project dir exists but before initializer runs"""
        pass

    def get_prompt_injections(self, project_dir: str) -> list[str]:
        """Extra context to inject into agent prompts"""
        return []


class PostBuildStage:
    """Runs after all coding features pass"""
    name: str
    agent_type: str  # e.g. "reviewer", "qa"

    def should_run(self, features: list) -> bool:
        """Whether this stage should execute"""
        return True

    def get_agent_config(self) -> dict:
        """Agent configuration for this stage"""
        return {}


class NotificationProvider:
    """Sends notifications on events"""
    async def notify(self, event: str, data: dict):
        pass
```

Then your boilerplate/style system becomes:
```python
# pre_hooks/boilerplate_hook.py
class BoilerplateHook(ProjectCreationHook):
    async def on_project_created(self, project_dir, config):
        if config.get("boilerplate"):
            clone_boilerplate(project_dir, config["boilerplate"])

# pre_hooks/style_hook.py
class StyleHook(ProjectCreationHook):
    async def on_project_created(self, project_dir, config):
        if config.get("style"):
            save_style_guide(project_dir, config["style"])

    def get_prompt_injections(self, project_dir):
        guide = Path(project_dir) / ".autoforge" / "style_guide.md"
        if guide.exists():
            return [f"## Design System\n{guide.read_text()}"]
        return []
```

And your QA pipeline becomes:
```python
# post_stages/reviewer_stage.py
class ReviewerStage(PostBuildStage):
    name = "reviewer"
    agent_type = "reviewer"

    def should_run(self, features):
        return any(not f.reviewed for f in features if f.passes)

# post_stages/qa_stage.py
class QAStage(PostBuildStage):
    name = "qa"
    agent_type = "qa"

    def should_run(self, features):
        return all(f.reviewed for f in features if f.passes)
```

**Result**: `prompts.py` has ONE hook call instead of your two custom functions. `parallel_orchestrator.py` has a generic pipeline loop instead of hardcoded reviewer/QA logic.

### Step 3: Adapter Layer for MIDDLE Changes

This is the minimum "fork surface" you accept:

```python
# autoforge_adapter.py -- YOUR layer between your code and AutoForge core

# Agent type registry (instead of hardcoding in client.py)
AGENT_TYPES = {
    "coding": AgentConfig(max_turns=150, billing="subscription", ...),
    "testing": AgentConfig(max_turns=75, billing="subscription", ...),
    "initializer": AgentConfig(max_turns=200, billing="api", ...),
    "reviewer": AgentConfig(max_turns=100, billing="subscription", ...),
    "qa": AgentConfig(max_turns=100, billing="subscription", ...),
}

# Database column extensions (SQLAlchemy mixin)
class QAColumnsMixin:
    reviewed = Column(Boolean, default=False)
    qa_verified = Column(Boolean, default=False)

# Settings extensions
EXTRA_SETTINGS = {
    "qa_enabled": {"type": bool, "default": True},
    "reviewer_enabled": {"type": bool, "default": True},
    "notifications_pushover_key": {"type": str, "default": ""},
    ...
}

# Budget tracking
class BudgetTracker:
    def on_turn(self, turn_count, context_usage):
        if context_usage > 0.8:
            print("[BUDGET] Warning: 80% context used")
```

Then `client.py` has a small diff:
```python
# Instead of hardcoded agent types:
from autoforge_adapter import AGENT_TYPES
config = AGENT_TYPES.get(agent_type, AGENT_TYPES["coding"])
```

**Result**: When upstream updates `client.py`, your merge is ONE line (the import + lookup) instead of 200 lines of scattered changes.

### Step 4: What CANNOT Be Extracted (Accept These ~12 Files)

Some things will always need manual merge attention:

1. **`client.py`** -- Agent type lookup, billing routing, MCP server choice. Even with the adapter, you need ~5-10 lines changed in this file.
2. **`api/database.py`** -- Your QA columns. Even with a mixin, the migration logic needs to live somewhere.
3. **`server/schemas.py`** -- Your extra settings fields. The Pydantic models must include them.
4. **`mcp_server/feature_mcp.py`** -- Your extra MCP tools (mark_reviewed, mark_qa_verified, split).
5. **`parallel_orchestrator.py`** -- The post-build pipeline hook call.
6. **`agent.py`** -- Budget checkpoint hook call.
7. **`progress.py`** -- Return signature + notification dispatch.
8. **`server/main.py`** -- Extension loader registration.
9. **`server/routers/__init__.py`** -- Extension router imports.
10. **`server/routers/projects.py`** -- Hook calls during project creation.
11. **`process_manager.py`** -- Pre-build intelligence flags.
12. **`ui/src/App.tsx`** -- Navigation links to your pages.

But the KEY difference: instead of each of these files having 50-200 lines of changes scattered throughout, each one would have **5-15 lines** that call into your adapter/hooks/extensions. That's the difference between a painful multi-day merge and a 30-minute merge.

---

## The Upgrade Workflow (After Restructuring)

```bash
# 1. Fetch new upstream
git fetch upstream
git log upstream/master --oneline -20  # see what changed

# 2. Create upgrade branch
git checkout -b upgrade/0.1.16

# 3. Merge upstream core files only (not your extensions/)
git checkout upstream/master -- \
  client.py agent.py parallel_orchestrator.py \
  api/database.py server/schemas.py \
  mcp_server/feature_mcp.py progress.py \
  prompts.py registry.py server/main.py \
  # ... all upstream-owned files

# 4. Re-apply your ~12 adapter touchpoints
# These are small, predictable diffs:
#   - client.py: add agent type registry import
#   - database.py: add QA columns mixin
#   - schemas.py: add extra settings fields
#   - etc.

# 5. Test
npm run build && python -m pytest

# 6. Done - your extensions/ haven't changed at all
```

---

## Decision Framework: Replace Core vs. Port Features

When a new upstream version drops, ask:

| Question | If Yes | If No |
|----------|--------|-------|
| Does it change files I modified? | Manual merge needed | Drop-in replace |
| Does it add a feature I already built differently? | Evaluate: is theirs better? Keep yours? Support both? | No conflict |
| Does it change the database schema? | **Highest risk** -- test migration carefully | Safe to merge |
| Does it change API schemas? | Check your UI components that consume those types | Safe to merge |
| Are the changes in files I only added hook calls to? | Quick re-apply of your 5-10 line adapter diffs | N/A |

### When to Replace Core vs. Port Features Yourself

**Replace core** when:
- The upstream change is large (like the 21-file Playwright CLI migration)
- Multiple contributors worked on it (community-tested)
- It touches areas you don't have custom logic in
- Your adapter touchpoints in those files are minimal

**Port the features yourself** when:
- The upstream change conflicts with a deliberate design choice (e.g., Human Input vs QA Pipeline)
- The change is small and targeted (e.g., a rate limit fix)
- You have heavy custom logic in the affected files

---

## Effort Estimate

| Phase | Work | Days |
|-------|------|------|
| Extract PARALLEL features to `extensions/` | Move files, add dynamic loader | 2-3 |
| Define hook interfaces | Create `hooks.py`, refactor PRE/POST | 3-5 |
| Build adapter layer for MIDDLE | Create `autoforge_adapter.py`, minimize core diffs | 5-7 |
| Test full upgrade cycle | Fetch upstream 0.1.15, merge, verify | 2-3 |
| **Total** | | **12-18 days** |

After this one-time investment, each future upstream merge should take **hours, not days**.

---

## Summary

Your instinct is correct: the front-end stuff (boilerplates, styles, design guide) and back-end stuff (QA pipeline, notifications, CI monitor) CAN be cleanly disconnected. The PARALLEL features (Workspace, DunkStack, Role Library) are already almost there.

The key learning for future projects: **every time you're about to edit an upstream file, ask "can I do this via a hook/wrapper/config instead?"** If you'd done that from day one, your merge surface would be ~5 files instead of ~12. But ~12 is still very manageable -- especially when each one only has a few lines of adapter code instead of 200 lines of inline changes.
