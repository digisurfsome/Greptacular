# Archon Versions & Repos — Source-of-Truth Map

> **Purpose:** Stop forgetting which repo is which and what version of Archon is where.
> Owner is non-coder. This file is the answer when "wait, which one is the engine again?" comes up.
> **Last updated:** 2026-04-24 (after upgrading local engine + creating archon-pipeline-rebuild)

---

## TL;DR — Read This First

You have **four separate things**. They are NOT the same. Mixing them up is what causes 90% of confusion.

| Thing | What it is | Where | When you touch it |
|-------|-----------|-------|--------------------|
| **1. Archon engine (local)** | The actual software that runs workflows | `C:\Users\lober\archon\Archon\` | Almost never — only if upgrading or debugging the engine itself |
| **2. Archon runtime install** | Where Archon stores live state, your registered projects, current workflows it runs | `C:\Users\lober\.archon\` | Indirectly — Archon writes here when you run things |
| **3. Template repo** | A clean, empty Archon project shell. Used to spawn new project repos. | GitHub: `digisurfsome/archon-module-template`. Local: not cloned. | Only when creating a new project — you clone FROM it. Never edit the template itself. |
| **4. Working project repo** | This is where the actual pipeline rebuild work happens. Cloned from #3 today. | GitHub: `digisurfsome/archon-pipeline-rebuild`. Local: `C:\Users\lober\archon-pipeline-rebuild\` | Pass 0/1/2 agents commit here. This is the "playground" for the rebuild. |

---

## Detail Block per Thing

### 1. Archon engine (local install)

**Path:** `C:\Users\lober\archon\Archon\`
**Git remote:** `https://github.com/digisurfsome/Archonf.git` (origin) + `https://github.com/coleam00/Archon.git` (upstream)
**Current branch:** `dev`
**Current version:** `0.3.9` (npm package version) — git describe: `v0.3.9-4-g83e6c7ac`
**Current HEAD commit:** `83e6c7ac` — "org: scaffold .archon/docs structure + AGENTS rulebook + INDEX" (2026-04-22)
**Last upstream merge from coleam00:** `dd1a8f02` — "Merge remote-tracking branch 'upstream/main' into dev" (2026-04-22)

**What it is in plain English:**
This is THE Archon software. It's the program that takes your YAML workflow files and runs them. It runs in the background when you use Archon at all. When agents talk about "the Archon engine," this is what they mean.

**When you'd touch it:**
- Almost never. The owner does NOT modify the engine.
- An agent might modify it if asked to upgrade Archon, fix an engine bug, or pull in latest upstream changes.

**How current is it vs coleam00's latest?**

As of this doc's last update:
- **Local engine HEAD:** 2026-04-22 (last upstream merge dd1a8f02)
- **coleam00 latest commit on main:** `91226735` — "docs/skill: add parameter-matrix.md quick-lookup reference" (2026-04-24)
- **Gap:** Local is ~2 days behind coleam00's latest. Coleam00 has shipped 5+ commits since the last sync, including new workflow fixes and the `opus[1m]` model alias change in PR #1395.

**To re-sync from coleam00 later:**
```
cd C:\Users\lober\archon\Archon
git fetch upstream
git merge upstream/main
```
(Or have an agent do it — there's a chance of merge conflicts because this fork has local customizations like the globalSearchPath patch in commit e76daf8d.)

---

### 2. Archon runtime install (live state)

**Path:** `C:\Users\lober\.archon\`
**What lives here:**
- `archon.db` — SQLite database with project registrations, run history, etc.
- `workflows/` — workflow YAML files Archon currently sees and offers
- `commands/` — command MD files Archon loads
- `scripts/` — helper scripts
- `workspaces/` — git worktrees Archon creates per run
- `artifacts/` — outputs from runs (PRDs, build outputs)
- `config.yaml` — Archon-level config
- `features.yaml` — feature flags
- `.env` — environment vars

**What it is in plain English:**
This is Archon's home directory on your machine. When you register a project, Archon writes to the DB here. When workflows run, outputs land in `artifacts/` here. This is "live state."

**When you'd touch it:**
- Indirectly all the time — Archon writes here automatically.
- Directly almost never — only to debug Issue #1 (template second-copy bug) by inspecting the SQLite DB, or to manually clean stale entries.
- **Do not modify directly during normal operation.** Let Archon manage it.

**Important caveat:**
The `workflows/` and `commands/` here are ALSO the live ones Archon sees globally. If a project has its own `.archon/workflows/` (like the working project repo does), those project-local ones can override these globals. Pass 1's pipeline-d will live in the project repo, not here.

---

### 3. Template repo

**GitHub URL:** `https://github.com/digisurfsome/archon-module-template`
**Local clone:** None — you do NOT keep a local clone of the template. You clone FROM it to make new project repos.
**Created:** ~21 hours before this doc's last update
**Authored by:** digisurfsome (the owner)

**Two commits in its history (entire history):**
1. `bd1c960` — "Initial commit"
2. `d2525e8` — "add archon pipeline scripts and template docs"

**What it contains:**
- `.archon/` directory with workflows + commands + scripts pre-loaded
- Baseline `CLAUDE.md`, `README.md`, `.gitignore`
- Just enough scaffolding for Archon to register it as a project

**What it is in plain English:**
A clean blank "starter pack" for new modular build projects. When you want a new module repo (scraper, MP3 generator, detection bot, etc.), you start from this. It's the cookie cutter — you don't eat the cookie cutter, you stamp out cookies with it.

**Is this a fork of coleam00/archon?**
**No.** The template is its own original repo. It contains scaffolding to USE the Archon engine — it is not Archon itself. The Archon engine fork lives at `digisurfsome/Archonf` and runs locally at `C:\Users\lober\archon\Archon\` (Thing #1).

**When you'd touch it:**
- Only when adding new pre-loaded scaffolding that EVERY future module repo should inherit.
- Never modify it in the middle of a project — that pollutes future projects.

**Why this matters for the rebuild:**
The pipeline rebuild work doesn't go INTO the template. It goes into a CLONE of the template (Thing #4). This is so the template stays clean for the next module after this one (CallPitch's scraper, detection bot, etc.).

---

### 4. Working project repo (the "playground" for the rebuild)

**GitHub URL:** `https://github.com/digisurfsome/archon-pipeline-rebuild`
**Local clone:** `C:\Users\lober\archon-pipeline-rebuild\`
**Created:** today (2026-04-24)
**Created via:** `git clone` from the template (Thing #3), then `git remote set-url` to point at this new GitHub repo. NOT created via GitHub's "Use this template" button (that triggers Issue #1).

**Current state:**
- Local clone exists at `C:\Users\lober\archon-pipeline-rebuild\`
- Connected to `digisurfsome/archon-pipeline-rebuild` GitHub repo
- All template files pushed up successfully (`branch 'main' set up to track 'origin/main'`)
- Identical content to the template — `.archon/` directory ready to be modified by Pass 0/1/2

**What's in here that gets modified:**
- `.archon/commands/stage-NN.md` — Pass 0 audits and rewrites these into mode-agnostic prompts with preamble blocks
- `.archon/workflows/prd-pipeline-d.yaml` — Pass 1 creates this new workflow file from scratch
- `.archon/workflows/prd-pipeline-c.yaml` — kept as reference, not modified

**Where Pass 0/1/2 commits go:**
This repo's `main` branch on GitHub. NOT to Greptacular. NOT to the template. NOT to the engine.

**Why this is separate from everything else:**
- Engine (#1) is the program. Don't put workflow content there.
- Live install (#2) is auto-managed runtime state. Don't put source there.
- Template (#3) must stay clean. Don't pollute it with one project's work.
- This (#4) is the project-specific workspace for the rebuild.

---

## Quick Reference Card — "Which Repo Do I Use For X?"

| Task | Repo | Path |
|------|------|------|
| Read the rebuild PRDs / handoffs | Greptacular (this repo) | `docs/page-prds/archon-build-upgrade/` |
| Spawn Pass 0 agent | archon-pipeline-rebuild (Thing #4) | `C:\Users\lober\archon-pipeline-rebuild\` |
| Spawn Pass 1 agent | archon-pipeline-rebuild (Thing #4) | `C:\Users\lober\archon-pipeline-rebuild\` |
| Spawn Pass 2 agent | archon-pipeline-rebuild (Thing #4) | `C:\Users\lober\archon-pipeline-rebuild\` |
| Test pipeline-d on a real project | New module repo (clone the template AGAIN) | TBD when CallPitch starts |
| Upgrade Archon engine | Engine fork (Thing #1) | `C:\Users\lober\archon\Archon\` |
| Add a new piece of scaffolding to ALL future module repos | Template repo (Thing #3) | (don't keep local — edit on GitHub) |

---

## Update Protocol — When This File Goes Stale

This file goes stale when ANY of these happen:
- Local engine pulls new commits from coleam00 → update §1's "Current HEAD commit" + "Gap"
- Template repo gets a new commit → update §3's commit list
- A new project repo gets created from the template → add it to §4 (or make a new section if there are >1 active project repos)
- Coleam00 ships a new release → update §1's "How current is it vs coleam00's latest"

**To refresh this file:** ask any agent to "update ARCHON-VERSIONS-AND-REPOS.md with current data." They run a few git commands + one WebFetch and rewrite the version blocks.

---

## Linked References

- `KNOWN-ISSUES.md` Issue #1 — the template second-copy bug that's why we use `git clone` instead of "Use this template"
- `PASS-0-PREAMBLE-AUDIT-HANDOFF.md` §0.5 — points agents at Thing #4 as their working repo
- `PIPELINE-REBUILD-NO-BASH-HANDOFF.md` §0.5 — same
- `MASTER-MODULAR-ARCHITECTURE.md` — the architectural plan that's being executed in Thing #4
