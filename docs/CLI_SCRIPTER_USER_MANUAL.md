# CLI Scripter — User Manual

**Last updated:** 2026-03-12

---

## What It Does

The CLI Scripter generates bash scripts that build apps using Claude CLI (`claude -p`). You fill in what you want to build, it creates the scripts, and you run them. The app gets built autonomously.

---

## Page Layout (Top to Bottom)

### 1. Build Dashboard (top bar)

| Element | What It Does |
|---|---|
| **▷ Start Build** (green button) | Runs the generated build scripts from the UI. Phases must be generated first. |
| **Refresh: 15s / 30s / 1m / 5m / Off** | How often the dashboard refreshes build status while running. Default 30s. |
| **▷ Build Log** (collapsible) | Click to expand — shows live terminal output during a build. Auto-scrolls. Color-coded. |

### 2. Project Basics

| Field | What To Enter |
|---|---|
| **App Name** | Name of the app you're building (e.g., "My Todo App") |
| **App Description** | What the app does, who it's for. 1-3 sentences. |
| **Boilerplate** (dropdown) | Tech stack template. Options: Web App (Supabase + Stripe), Plain React, Python CLI, etc. |
| **Create GitHub repo** (checkbox) | Auto-creates a GitHub repo for the project. Optional. |
| **✕ button** | Clears the text field. Appears on all text inputs. |

### 3. Build Rules

Named rule blocks you create once and reuse across builds.

| Element | What It Does |
|---|---|
| **Rule block name** | Name your rule set (e.g., "My Standard Rules") |
| **Main / P1 / P2+ checkboxes** | Which combiner slots this block feeds into |
| **🔒 lock icon** | Locks the block from editing |
| **🗑️ trash icon** | Deletes the block |
| **+ New Block** | Creates a new rule block |
| **+ tag** | Add category tags to organize rules |

### 4. Combiner Slots

| Slot | What It Does |
|---|---|
| **Main Combined** | Rules that go into EVERY phase |
| **Phase 1 Combo** | Rules only for phase 1 (full architecture, more detailed) |
| **Phase 2+ Combo** | Rules for phases 2 and later (lighter, references what's built) |
| **✨ Combine Rules with AI** | Uses AI to merge selected rule blocks into a coherent ruleset |
| **Re-pull** | Re-pulls rules from the blocks into the combiner slots |

### 5. Phase Rules

| Element | What It Does |
|---|---|
| **All phases use the same rules** (checkbox) | When checked, same rules for every phase. When unchecked, Phase 1 gets heavy rules, Phase 2+ gets lighter ones. |
| **Token estimate** | Shows estimated token cost per phase |

### 6. Features (collapsible)

Optional — skip if you already have a PRD. Add individual features if you want them listed in the generated PRD.

### 7. Build Settings

| Setting | Options | What It Controls |
|---|---|---|
| **Turns per Phase** | 10, 25, 50, Unlimited | Max conversation turns the agent gets per phase. 25 is default. |
| **Phase Transition** | Pause, Auto-continue, Prompt me | What happens between phases. Pause = wait. Auto-continue = keep going. |
| **Error Handling** | Retry once then skip, Stop everything, Skip immediately | What happens when lint/type check fails |
| **Git Commits** | After each feature, After each phase, Never | When the agent commits code |
| **Number of Phases** | Auto, 2, 3, 4, 5, 6+ | How many phases to split the build into. Auto = calculated from token budget. |
| **Parallel phases** (checkbox) | On/Off | Run independent phases simultaneously instead of sequentially |

### 8. Agent Roles

The pipeline: **Architect → Coder (per phase) → Reviewer (per phase) → Verifier → Cartographer**

| Role | Default Model | When It Runs | What It Does |
|---|---|---|---|
| **Architect** | sonnet | Once before building | Creates ARCHITECTURE.md — file structure, API contracts, data models |
| **Coder** | sonnet | Each phase | Writes the actual code for that phase |
| **Reviewer** | sonnet | After each phase | Reviews code for bugs, missing error handling, integration issues |
| **Verifier** | sonnet | Once after all phases | Full integration test, lint/type check, visual match report |
| **Cartographer** | sonnet | Final step | Documents codebase — creates ARCHITECTURE.md, CONVENTIONS.md, wireframe sketches |

Each role has:
- **Checkbox** — enable/disable the role
- **Model badge** (sonnet/opus) — click the dropdown to change
- **Timing** (Before build / Each phase / After all phases / Final step)
- **Expand arrow** — click to see/edit the role's prompt

**Include post-build verification phase (Opus)** checkbox — adds a dedicated Opus verification pass at the end.

### 9. Phase Assignments

Shows up AFTER you generate the phase split. Displays which phases exist and what each one builds. Read-only with a **Regenerate** button.

### 10. Build Estimate

| Metric | What It Shows |
|---|---|
| **Phases** | Number of build phases |
| **Active Roles** | How many roles are enabled |
| **Est. Total Tokens** | Estimated token consumption |
| **CLI Sessions** | Total `claude -p` calls that will run |
| **Pipeline** | Visual strip showing: Architect → Phase 1 → Phase 2 → ... → Verifier → Cartographer |

### 11. Generate Section

| Element | What It Does |
|---|---|
| **Project Directory** | Where the generated scripts will be saved. Change to your project path. |
| **🚀 Generate All (PRD → Phases)** (big orange button) | One-click: generates PRD prompt, splits into phases, creates build scripts. Shows the Gate Popup first. |
| **Generate PRD Prompt** | Just generates the PRD prompt (no AI call) |
| **Generate Phase-Split Prompt** | Calls AI to split the PRD into phases |
| **Generate Build Scripts Prompt** | Creates the bash scripts from the phases |

### 12. Gate Popup (appears when you click Generate All)

Two choices:

| Option | When To Use |
|---|---|
| **New Build** | Building from scratch. Full architecture, file structure, naming conventions. |
| **Edit / Patch** | Modifying existing code. Surgical edits, respect existing patterns, don't restructure. |

| Option | When To Use |
|---|---|
| **Single Phase** | One set of rules for all phases |
| **Split Phase** | Different rules for Phase 1 (heavy) vs Phase 2+ (lighter) |

Click **✓ Confirm & Generate** to proceed.

### 13. PRD Prompt (output)

| Element | What It Does |
|---|---|
| **Copy** button | Copies the generated prompt to clipboard |
| **✨ Run with AI** button | Sends the prompt to Claude to generate a full PRD |
| **PRD Generation Prompt** (collapsible) | Edit the system prompt used for PRD generation |

### 14. Saved Builds (collapsible)

Save and reload build configurations. Search, load, delete saved configs.

### 15. Build Queue

| Element | What It Does |
|---|---|
| **+ Add Current App to Queue** | Adds the current form as a queued build |
| **Queue list** | Shows queued apps with status badges, reorder arrows |
| **Status** | Pending / Running / Complete |

---

## How To Run a Build

### From the UI:
1. Fill in Project Basics
2. (Optional) Set up Build Rules
3. Click **Generate All (PRD → Phases)**
4. Choose New Build or Edit/Patch → Confirm
5. Wait for phases to generate
6. Click **▷ Start Build**
7. Watch progress in the Build Log panel

### From the Terminal (for pre-made scripts):
```bash
cd "C:/Users/lober/GitHub/Greptacular - AutoForge Build/Greptacular"
bash scripts/run-cli-scripter-build.sh
```

### Monitoring (separate terminal windows):

**Watch commits + build summary (refreshes every 30s):**
```bash
cd "C:/Users/lober/GitHub/Greptacular - AutoForge Build/Greptacular" && while true; do clear; echo "=== LATEST COMMITS ==="; git log --oneline -15; echo ""; echo "=== BUILD SUMMARY ==="; cat .claude/build-logs/cli-scripter-summary_*.txt 2>/dev/null | tail -20; echo ""; echo "=== RECENT FILES ==="; ls -lt ui/src/pages/ 2>/dev/null | head -5; ls -lt ui/src/components/ 2>/dev/null | head -10; sleep 30; done
```

**Watch file changes (refreshes every 5s):**
```bash
cd "C:/Users/lober/GitHub/Greptacular - AutoForge Build/Greptacular" && while true; do clear; echo "=== GIT DIFF STAT ==="; git diff --stat; echo ""; echo "=== UNTRACKED FILES ==="; git status -s; sleep 5; done
```

Change `sleep 30` or `sleep 5` to any number of seconds you want.

---

## Token Tracking

Both build scripts automatically track token usage per phase/agent using `--output-format json`.

After each phase/agent completes, you'll see:
```
[INFO] 📊 Tokens: 34902 in / 8 out | API cost equiv: $0.2183
```

At the end of a full build, you'll see grand totals:
```
=== TOKEN USAGE ===
  Total input tokens:  104706
  Total output tokens: 24
```

Token data is also saved to the summary file in `.claude/build-logs/`. The `total_cost_usd` field shows what the build WOULD cost on API pay-per-use — useful for comparing builds even though Max subscription costs $0 per token.

For the real build script (`run-cli-scripter-build.sh`), a heartbeat prints every 60 seconds so you know the agent is still running:
```
[HEARTBEAT] Agent 2 still running... 15m elapsed (14:32:07)
```

---

## Model Optimization (The Golden Rule)

All roles default to **Sonnet**. Opus is used for batch checkpoints every 3-4 phases, not per-phase review.

See `docs/SONNET_OPUS_OPTIMIZATION.md` for the full breakdown.

---

## Keyboard Shortcuts

Press `?` anywhere in AutoForge for the full shortcut list.

| Key | Action |
|---|---|
| `D` | Toggle debug panel |
| `G` | Toggle Kanban/Graph view |
| `,` | Open settings |
