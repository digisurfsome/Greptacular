# PRD: The PRD Shredder — Drop a PRD In, Code Comes Out

**Created: 2026-03-14 — Session 10b**
**Status: Ready to build**
**Priority: HIGH — This turns every PRD into automatic code. The factory that builds the factory.**
**Template: Cloned from YT Lab pipeline structure**

---

## What This Is

A paper shredder for PRDs. Drop a PRD into the chute, it automatically gets processed and built. If nothing's being built, it starts immediately. If something's already building, it queues up — gravity feed, one drops out the bottom done, the next one falls in.

**The flow:**
```
Idea → [Quick PRD Button] → PRD Template wraps it → Drops into Queue
                                                          ↓
                                              ┌───────────────────────┐
                                              │   THE SHREDDER        │
                                              │                       │
                                              │   PRD #4  (waiting)   │
                                              │   ─── stopper ───     │
                                              │   PRD #3  (waiting)   │
                                              │   ─── stopper ───     │
                                              │   PRD #2  (waiting)   │
                                              │   ─── stopper ───     │
                                              │   PRD #1  (building)  │
                                              │          ↓            │
                                              │   [Code + Test + Done]│
                                              └───────────────────────┘
```

**Not the CLI Scripter.** CLI Scripter = big multi-phase builds with 5 agent roles, parallel waves, architecture planning. That's for building entire apps from scratch.

**The Shredder** = one-shot fixes and additions. One 1M-token Claude session reads the PRD, reads the codebase, writes the code, lints, tests, commits, pushes. Done. Next PRD.

---

## Why It Matters

Right now the workflow is:
1. Talk to Claude → PRD gets written → dropped in `docs/`
2. Owner manually reads the PRD
3. Owner manually opens CLI Scripter or starts a new Claude session
4. Owner manually sets up the build
5. Owner waits, checks, restarts if it crashes

After this:
1. Talk to Claude → PRD gets written → **auto-drops into Shredder queue**
2. Walk away
3. Come back to commits

Every PRD this session has produced (tool execution engine, tool analyzer, self-building, Stripe rules) — if the Shredder existed, they'd already be built by now.

---

## Architecture: Clone YT Lab, Swap the Prompts

### What We Steal from YT Lab

| YT Lab Component | Shredder Equivalent |
|---|---|
| YouTube URL input | PRD text input (paste or file path) |
| Video ingestion (transcript) | PRD ingestion (parse structure) |
| Discovery (what's in the video?) | Codebase discovery (what exists now?) |
| Strategy extraction (steps) | Task extraction (code changes) |
| Blueprint generation (prompts) | Execution plan (file creates/edits) |
| Step list UI with status | Same — task list UI with status |
| Progress tracking + logs | Same |
| Generate Tool button | Build It button |

### What's Different

| YT Lab | Shredder |
|---|---|
| Output = prompts (text) | Output = committed code |
| Needs Google Sheets deploy | Needs git push to target repo |
| One video = one tool | One PRD = one set of commits |
| No execution | Full execution (lint, test, commit) |

---

## Phase 1: The Queue (The Chute)

### 1.1 PRD Queue data model

```python
class PRDQueueItem:
    id: str                    # UUID
    title: str                 # PRD title (extracted from doc)
    prd_text: str              # Full PRD content
    target_repo: str           # GitHub repo URL or local path
    target_branch: str         # Branch to commit to (default: main)
    status: str                # queued | cloning | analyzing | building | testing | committing | done | failed
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error: str | None
    commit_hash: str | None
    build_log: list[str]       # Real-time log lines
    tasks_total: int           # How many code tasks extracted
    tasks_done: int            # How many completed
```

**Storage:** SQLite at `~/.autoforge/prd_shredder.db`

### 1.2 Queue processing loop

```python
class PRDShredder:
    async def run_forever(self):
        """The conveyor belt. Runs as background task on server start."""
        while True:
            next_item = self.get_next_queued()
            if next_item:
                await self.process(next_item)
            else:
                await asyncio.sleep(5)  # Check every 5 seconds

    async def process(self, item: PRDQueueItem):
        """The shredder. One PRD in, code out."""
        try:
            item.status = "cloning"
            repo_dir = await self.clone_or_pull(item)

            item.status = "analyzing"
            analysis = await self.analyze_prd(item, repo_dir)

            item.status = "building"
            await self.execute_tasks(item, analysis, repo_dir)

            item.status = "testing"
            await self.verify(item, repo_dir)

            item.status = "committing"
            await self.commit_and_push(item, repo_dir)

            item.status = "done"
        except Exception as e:
            item.status = "failed"
            item.error = str(e)
```

### 1.3 GitHub token management

**On first use or from settings:**
- Store GitHub personal access token in `~/.autoforge/.env` as `GITHUB_TOKEN`
- Token needs `repo` scope (read + write to repos)
- One token covers all repos the user has access to

**Repo cloning:**
```python
async def clone_or_pull(self, item: PRDQueueItem) -> Path:
    """Clone the target repo or pull latest if already cloned."""
    repo_cache = Path.home() / ".autoforge" / "shredder_repos"
    repo_name = extract_repo_name(item.target_repo)  # e.g. "digisurfsome/Greptacular"
    repo_dir = repo_cache / repo_name

    if repo_dir.exists():
        # Pull latest
        subprocess.run(["git", "pull", "origin", item.target_branch], cwd=repo_dir)
    else:
        # Clone fresh
        clone_url = f"https://{token}@github.com/{repo_name}.git"
        subprocess.run(["git", "clone", clone_url, str(repo_dir)])

    return repo_dir
```

**For local repos (like Greptacular itself):**
- If `target_repo` is a local path instead of a GitHub URL, skip clone, work directly
- Detect: if path starts with `/` or `C:\` or `~`, it's local

---

## Phase 2: PRD Ingestion + Analysis (The Brain)

### 2.1 PRD Ingestion — Stage 1

**What it does:** Parse the PRD, extract the key information the coding agent needs.

**Prompt (Claude Sonnet — cheap, fast):**
```
You are a PRD analyst. Read this PRD and extract:

1. OBJECTIVE — What is being built or fixed? One sentence.
2. TARGET FILES — Every file mentioned that needs to be created or modified.
3. REQUIREMENTS — Every specific requirement, numbered.
4. SUCCESS CRITERIA — How do we know it's done?
5. DEPENDENCIES — What must exist before this can be built?
6. SCOPE — What is explicitly OUT of scope?
7. DIFFICULTY — Your honest estimate (1-10) with reasoning.

Return as structured JSON.

PRD:
{prd_text}
```

### 2.2 Codebase Discovery — Stage 2

**What it does:** Scan the target repo and map what currently exists vs. what the PRD needs.

**Prompt (Claude Sonnet):**
```
You are a codebase analyst. You've been given a PRD analysis and a file listing of the target repository.

PRD Analysis:
{stage1_output}

Repository file tree:
{file_tree}

Key file contents (auto-selected based on PRD target files):
{relevant_file_contents}

Analyze:
1. Which files from the PRD already exist? What's their current state?
2. Which files need to be created from scratch?
3. Which existing files need modification? What specifically needs to change?
4. Are there patterns in the codebase the new code should follow? (naming, structure, imports)
5. Are there any conflicts between the PRD and the current codebase?
6. What is the correct order to make these changes? (dependencies between files)

Return as structured JSON with a task list.
```

### 2.3 Task Extraction — Stage 3

**What it does:** Break the PRD into specific, ordered code tasks that can be executed.

**Prompt (Claude Sonnet):**
```
You are a task planner for a coding agent. Given the PRD analysis and codebase discovery,
create an ordered list of exact code tasks.

PRD Analysis:
{stage1_output}

Codebase Discovery:
{stage2_output}

For each task, specify:
1. task_number — execution order
2. action — "create_file" | "modify_file" | "delete_lines" | "add_dependency"
3. file_path — exact path relative to repo root
4. description — what to do in plain English
5. details — specific code patterns to follow, functions to create, imports needed
6. depends_on — which task numbers must complete first
7. verification — how to check this task succeeded (lint command, import check, etc.)

Rules:
- Each task should be small enough to verify independently
- Order tasks so dependencies come first
- Group related changes (e.g., model + router + UI for same feature)
- Include lint/test verification as separate tasks between groups

Return as JSON array of tasks.
```

### 2.4 Consulting Assessment — Stage 4 (The Secret Sauce)

**What it does:** Same thing that makes YT Lab incredible — a second AI pass that reviews the plan and catches problems before execution.

**Prompt (Claude Sonnet):**
```
You are a senior software architect reviewing a build plan before execution.

Original PRD:
{prd_text}

Extracted Tasks:
{stage3_output}

Review this plan and identify:

1. MISSING TASKS — What did the task extraction miss? Are there obvious requirements
   in the PRD that don't have corresponding tasks?

2. ORDER PROBLEMS — Are any tasks in the wrong order? Will anything fail because
   a dependency hasn't been created yet?

3. SCOPE CREEP — Are any tasks doing MORE than the PRD asks for? Remove them.

4. INTEGRATION GAPS — After all tasks complete, will everything actually work together?
   Are there missing imports, missing route registrations, missing UI links?

5. RISK ASSESSMENT — Which tasks are most likely to cause problems? Flag them.

6. FINAL TASK LIST — Return the corrected, complete task list as JSON.
   Add any missing tasks. Remove any scope-creep tasks. Fix the order.
```

**This is the YT Lab pattern:** extraction → conversion → consulting assessment. Three layers of prompts that catch what each previous layer missed.

---

## Phase 3: Execution (The Actual Building)

### 3.1 Single-session execution with 1M context

**Why one session works:**
- 1M context = can read the entire PRD + all target files + all reference files
- One session maintains full context across all tasks
- No handoff overhead between agents
- Stripe's "one-shot" philosophy: plan completely, execute completely

**Execution method:** `claude -p` with the full task list and Stripe build rules baked in.

**The mega-prompt sent to Claude 1M:**

```
You are a coding agent executing a PRD. Follow the Stripe Blueprint Pattern:
alternate between robot steps (exact commands) and agent steps (creative coding).

## YOUR TASK LIST
{stage4_corrected_tasks}

## CODEBASE CONTEXT
{relevant_file_contents — auto-loaded based on task file paths}

## BUILD RULES
{stripe_minions_build_rules — from docs/stripe-minions-build-rules.md}

## EXECUTION RULES

1. Execute tasks in order. Do NOT skip ahead.
2. After each file create/modify:
   - [ROBOT] Run lint: ruff check {file} --fix (Python) or npx tsc --noEmit (TypeScript)
   - Fix any errors BEFORE moving to the next task
3. After completing all tasks:
   - [ROBOT] Run full lint: ruff check . && cd ui && npm run build
   - [ROBOT] Run tests if any exist for modified code
4. Maximum 2 retry attempts on any single error
5. If a task is impossible (missing dependency, wrong assumption in PRD):
   - Document why in a comment
   - Skip it
   - Continue with remaining tasks
6. When done:
   - [ROBOT] git add (specific files only)
   - [ROBOT] git commit with message describing all changes
   - Report: what was done, what was skipped, what needs human attention
```

### 3.2 Progress tracking

During execution, parse Claude's output for progress signals:
- "Creating file X" → update task status to "in_progress"
- "Lint passed" → update task verification
- "Task N complete" → increment tasks_done counter
- Stream all output to the Shredder UI via WebSocket (same pattern as YT Lab logs)

### 3.3 Verification gate

After Claude session completes:

```python
async def verify(self, item: PRDQueueItem, repo_dir: Path):
    """Robot verification — no AI needed."""
    # Run lint
    lint_result = subprocess.run(["ruff", "check", "."], cwd=repo_dir)
    if lint_result.returncode != 0:
        item.build_log.append("LINT FAILED — attempting auto-fix")
        subprocess.run(["ruff", "check", ".", "--fix"], cwd=repo_dir)

    # Run TypeScript build if ui/ exists
    ui_dir = repo_dir / "ui"
    if ui_dir.exists():
        build_result = subprocess.run(["npm", "run", "build"], cwd=ui_dir)
        if build_result.returncode != 0:
            item.build_log.append("TS BUILD FAILED")
            raise BuildError("TypeScript build failed after agent execution")

    # Run tests if they exist
    test_result = subprocess.run(["python", "-m", "pytest", "--tb=short", "-q"], cwd=repo_dir)
    item.build_log.append(f"Tests: {'PASSED' if test_result.returncode == 0 else 'FAILED'}")
```

### 3.4 Commit and push

```python
async def commit_and_push(self, item: PRDQueueItem, repo_dir: Path):
    """Robot step — deterministic commit."""
    # Stage only files that were in the task list
    for task in item.tasks:
        subprocess.run(["git", "add", task.file_path], cwd=repo_dir)

    # Commit
    message = f"PRD Shredder: {item.title}\n\nAuto-built from PRD. Tasks: {item.tasks_done}/{item.tasks_total}"
    subprocess.run(["git", "commit", "-m", message], cwd=repo_dir)

    # Push
    subprocess.run(["git", "push", "origin", item.target_branch], cwd=repo_dir)

    item.commit_hash = get_commit_hash(repo_dir)
```

---

## Phase 4: The Quick-PRD Button (One-Click from Anywhere)

### 4.1 The idea-to-PRD template

When the user has an idea, they shouldn't have to write a full PRD. They describe the idea in plain language, and a template wraps it into a proper PRD.

**Template prompt (Claude Haiku — instant, cheap):**
```
You are a PRD writer. Take this raw idea and wrap it into a structured PRD.

Idea:
{user_idea}

Target repo: {repo_name}
Current date: {date}

Write a PRD with these sections:
1. What This Is — one paragraph
2. Why It Matters — the problem it solves
3. What To Build — specific requirements, numbered
4. Files To Create — with purpose
5. Files To Modify — with what changes
6. Success Criteria — how we know it's done
7. What's Out of Scope — keep it focused

Keep it concise. No fluff. Focus on what a coding agent needs to build this.
```

### 4.2 Quick-PRD button in workspace chat

**In the workspace chat page**, add a button: **"Shred This →"**

When the user is chatting with Claude and generates a PRD:
1. User clicks "Shred This →"
2. The PRD text gets wrapped in the template (if it's a raw idea) or sent directly (if it's already a PRD)
3. User picks the target repo from a dropdown (populated from `~/.autoforge/shredder_repos/` + registry)
4. PRD drops into the queue
5. Toast notification: "PRD queued. Position: #3. Estimated start: ~15 min."

### 4.3 Auto-drop from Claude conversations

When Claude writes a PRD during a conversation (like this session), it can auto-detect and offer:

```
PRD detected in conversation.

[Drop into Shredder]  [Save to docs/ only]  [Dismiss]

Target: Greptacular (main)
```

### 4.4 Bulk drop

Drag-and-drop multiple `.md` files from `docs/` onto the Shredder page. Each one becomes a queue item. The chute fills up.

---

## Phase 5: The Shredder UI Page

### 5.1 Layout — Clone YT Lab structure

**Route:** `/#/prd-shredder`
**Nav:** Add to sidebar under YT Strategy Lab

**Left panel — The Queue (the chute):**
```
┌──────────────────────────────────┐
│  PRD SHREDDER                    │
│  ════════════════════════════     │
│                                   │
│  🔄 Building: Tool Analyzer P1   │
│     ████████░░░░  67%  (4/6)     │
│     Target: Greptacular          │
│     Started: 2 min ago           │
│                                   │
│  ── queue ──────────────────     │
│                                   │
│  ⏳ #2: Execution Engine P1      │
│     Target: Greptacular          │
│                                   │
│  ⏳ #3: Webhook Handler          │
│     Target: Greptacular          │
│                                   │
│  ⏳ #4: File Creator Component   │
│     Target: Greptacular          │
│                                   │
│  ── done ───────────────────     │
│                                   │
│  ✅ CLI Scripter Fix             │
│     3/3 tasks · abc1234 · 4m     │
│                                   │
│  ✅ Subscription Auth Update     │
│     5/5 tasks · def5678 · 7m     │
│                                   │
│  [+ Drop PRD]  [+ Quick Idea]    │
└──────────────────────────────────┘
```

**Right panel — Active build detail:**
```
┌──────────────────────────────────────────────────┐
│  Tool Analyzer Phase 1 — Component Registry      │
│  Target: digisurfsome/Greptacular (main)         │
│                                                   │
│  TASKS                                            │
│  ✅ 1. Create component_registry.py              │
│  ✅ 2. Create component_registry.json template   │
│  ✅ 3. Add auto-detection on server startup      │
│  🔄 4. Create tool_analyzer.py (Quick Check)     │
│  ⬜ 5. Add REST endpoints                        │
│  ⬜ 6. Lint + verify                             │
│                                                   │
│  BUILD LOG                                        │
│  [14:32:01] Cloned Greptacular (main)            │
│  [14:32:03] PRD analysis: 6 tasks extracted      │
│  [14:32:15] Task 1: Creating component_registry  │
│  [14:32:45] Task 1: ruff check passed            │
│  [14:33:02] Task 2: Creating JSON template       │
│  [14:33:10] Task 3: Adding startup detection     │
│  [14:33:55] Task 3: ruff check passed            │
│  [14:34:10] Task 4: Creating tool_analyzer.py... │
│                                                   │
│  [Pause]  [Skip Task]  [Cancel Build]            │
└──────────────────────────────────────────────────┘
```

### 5.2 Drop zone

At the top of the page, a drag-and-drop zone:
```
┌─────────────────────────────────────────┐
│                                          │
│   📄 Drop PRD files here                │
│   or paste PRD text below               │
│                                          │
│   [Choose files]                         │
│                                          │
│   Target repo: [Greptacular ▾]          │
│   Branch:      [main ▾]                 │
│                                          │
│   [🔥 Shred It]                         │
└─────────────────────────────────────────┘
```

---

## Phase 6: Smart Routing — Shredder vs. CLI Scripter

### 6.1 Auto-detect complexity

Not every PRD should go through the Shredder. Big builds need the CLI Scripter.

**Decision matrix:**

| Signal | Shredder (one-shot) | CLI Scripter (multi-phase) |
|---|---|---|
| Files to create | < 10 | 10+ |
| Files to modify | < 15 | 15+ |
| New UI pages | 0-1 | 2+ |
| Estimated difficulty | 1-5/10 | 6-10/10 |
| Database migrations | None | Yes |
| New npm packages | 0-2 | 3+ |
| PRD mentions "phases" | No | Yes |

**After Stage 1 (PRD Ingestion), the system recommends:**
```
┌─────────────────────────────────────────────────┐
│  Analysis complete. Recommendation:              │
│                                                   │
│  ✅ SHREDDER — This is a one-shot fix            │
│     4 files to modify, 1 to create               │
│     Estimated: ~5 minutes                        │
│                                                   │
│  [Shred It]  [Send to CLI Scripter Instead]      │
└─────────────────────────────────────────────────┘
```

Or:
```
┌─────────────────────────────────────────────────┐
│  Analysis complete. Recommendation:              │
│                                                   │
│  ⚠️ CLI SCRIPTER — This is a big build          │
│     22 files to create, 8 to modify              │
│     3 new UI pages, database changes             │
│     Estimated: multi-phase (4-6 phases)          │
│                                                   │
│  [Send to CLI Scripter]  [Shred It Anyway]       │
└─────────────────────────────────────────────────┘
```

---

## Phase 7: The Overnight Factory

### 7.1 Scheduled processing

Combine with the existing scheduler service:
- User sets "Shredder hours" in settings (e.g., 10pm - 8am)
- During Shredder hours, queue processes automatically
- Outside Shredder hours, queue pauses (saves rate limit for human work)
- Or: always-on mode for users who want instant processing

### 7.2 Rate limit awareness

- Before starting a build, check `~/.autoforge/rate_limit_log.json`
- If the 5-hour window is near capacity, pause and wait
- Priority: human work > Shredder builds
- The Shredder should never eat the owner's working hours

### 7.3 Chain reaction with Tool Analyzer

When the Tool Analyzer (from the other PRD) discovers a missing component:
1. Analyzer generates a mini-PRD for the component
2. Mini-PRD auto-drops into the Shredder queue
3. Shredder builds it
4. Component goes live after server restart
5. Analyzer re-checks → more tools pass

**This is the full loop:** YT Lab finds gaps → Analyzer writes PRDs → Shredder builds them → capabilities expand → YT Lab can do more.

---

## Implementation Order

```
Phase 1 (Queue)  →  Phase 2 (Analysis Pipeline)  →  Phase 3 (Execution)  →  Phase 4 (Quick-PRD)  →  Phase 5 (UI)  →  Phase 6 (Smart Routing)  →  Phase 7 (Overnight)
```

| Phase | Difficulty | What It Gets You |
|---|---|---|
| 1: Queue + processing loop | 3/10 | SQLite queue, FIFO processing, repo clone/pull |
| 2: Analysis pipeline (4 stages) | 5/10 | PRD → tasks extraction with multi-layer prompts |
| 3: Execution (claude -p + verify) | 5/10 | Actual code generation, lint, test, commit, push |
| 4: Quick-PRD button | 3/10 | One-click idea-to-queue from workspace chat |
| 5: Shredder UI page | 4/10 | Queue view, build logs, drag-and-drop |
| 6: Smart routing | 2/10 | Auto-detect Shredder vs CLI Scripter |
| 7: Overnight factory | 3/10 | Scheduled processing, rate limit awareness |

**Total: ~25/70 difficulty. Seven phases.**

---

## Files To Create

| File | Phase | Purpose |
|---|---|---|
| `server/services/prd_shredder.py` | 1-3 | Queue manager + processing loop + execution |
| `server/services/prd_analyzer.py` | 2 | 4-stage PRD analysis pipeline (ingestion → discovery → tasks → review) |
| `server/routers/prd_shredder.py` | 1 | REST + WebSocket endpoints |
| `ui/src/pages/PRDShredderPage.tsx` | 5 | Shredder UI with queue, build detail, drag-and-drop |
| `server/models/prd_shredder.py` | 1 | SQLAlchemy models for queue items |

## Files To Modify

| File | Phase | Changes |
|---|---|---|
| `ui/src/App.tsx` | 5 | Add Shredder route |
| `server/main.py` | 1 | Start Shredder background loop on server start |
| `ui/src/components/workspace/WorkspaceChat.tsx` | 4 | Add "Shred This →" button for PRD detection |
| `server/routers/tool_analyzer.py` | 7 | Auto-drop analyzer PRDs into Shredder queue |

---

## Success Criteria

1. **Phase 1:** Drop a PRD into the queue, it gets picked up and processed FIFO
2. **Phase 2:** PRD analysis extracts correct file paths, requirements, and ordered tasks
3. **Phase 3:** Claude 1M session executes all tasks, code passes lint, gets committed and pushed
4. **Phase 4:** One click from workspace chat drops an idea into the queue as a formatted PRD
5. **Phase 5:** UI shows queue, active build, build logs, completed items with commit hashes
6. **Phase 6:** System correctly routes big PRDs to CLI Scripter, small ones to Shredder
7. **Phase 7:** Overnight batch processing respects rate limits and doesn't eat daytime capacity

## The End State

You're sitting in a Claude conversation. You say "I need a webhook handler for the tool runner." Claude writes a mini-PRD. You click "Shred It." It drops into the queue. Five minutes later, the code is committed and pushed. You didn't touch a file, open a terminal, or think about build scripts.

Stack 10 PRDs in the chute before bed. Wake up to 10 commits.

The PRD Shredder + Tool Analyzer + YT Lab = a system that finds its own gaps, writes its own PRDs, and builds its own code. You just feed it YouTube videos and ideas.
