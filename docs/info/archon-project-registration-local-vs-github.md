# Archon Project Registration — Local Path vs GitHub URL

> **Source of truth** for how Archon registers projects and creates worktrees.
> Written after a local-path registration failed and the Archon docs/videos didn't explain it.
> All claims here verified against Archon source code. File paths in the Appendix.

---

## TL;DR (30 seconds)

1. Archon gives you two ways to add a project: **paste a GitHub URL** or **paste a local folder path**.
2. **Both modes end up running the same worktree-creation code.**
3. That code **requires `origin` to exist** on the repo — always. No local-only mode.
4. GitHub-URL mode: works because Archon **clones the repo**, which auto-sets `origin`.
5. Local-path mode: works ONLY IF your local repo already has `origin` pointing somewhere (GitHub, local bare repo, anywhere).
6. The `.archon/config.yaml` `baseBranch` setting **does NOT skip the fetch** — it only tells Archon which branch to fetch from `origin`. Without `origin` it still fails.

If your local repo has no remote → Archon will crash at worktree creation. **No workaround in config alone.**

---

## How Local-Path Mode Is Supposed to Work

You paste a path like `C:\Users\lober\repos\mp3-generator` into the "add codebase" field.

**Archon's steps:**

1. Verifies the folder is a git repo (`git rev-parse --git-dir`). Fails fast if not.
2. Checks if the repo has a remote (`git remote get-url origin`).
   - If yes → stores the URL in Archon's database.
   - If no → registers it anyway, with `repository_url: null`.
3. Creates a symlink at `~/.archon/workspaces/{owner}/{repo}/source/` → your local path.
4. Saves the record to its SQLite database.
5. Registration succeeds.

**So registration works even without `origin`.** The problem comes later.

**When you run a workflow against this project:**

1. Archon reads `.archon/config.yaml` from your repo (if it exists).
2. Archon tries to create a worktree (an isolated copy of the repo).
3. Worktree creation calls `syncWorkspaceBeforeCreate()` which calls `syncWorkspace()`.
4. `syncWorkspace()` runs `git fetch origin <branchName>` — **unconditionally**.
5. No `origin` → fetch fails → worktree creation fails → pipeline never starts.

---

## How GitHub-URL Mode Is Supposed to Work

You paste a URL like `https://github.com/owner/repo` into the same field.

**Archon's steps:**

1. Parses the URL to extract `owner/repo`.
2. If `GH_TOKEN` env var is set, injects it as HTTPS auth. Otherwise falls back to SSH.
3. Runs `git clone <url> ~/.archon/workspaces/{owner}/{repo}/source/`.
4. Stores the URL in Archon's database.
5. Registration succeeds.

**Key difference:** the clone automatically sets up `origin` pointing at GitHub. So when worktree creation runs later, `git fetch origin <branch>` works on the first try.

The `default_cwd` in Archon's database points to the managed clone, not to a user-supplied folder.

---

## Why the Local-Path Attempt Failed

The specific sequence:

1. User ran `git init` in an empty folder → local repo with `master` branch, no remote.
2. Made one commit.
3. Registered the path in Archon UI → registration succeeded (no remote required at this step).
4. Clicked "run PRD Pipeline C" → Archon tried to create a worktree.
5. `syncWorkspace()` ran `git fetch origin master`.
6. Git returned: `fatal: 'origin' does not appear to be a git repository`.
7. Archon wrapped the error: `Failed to fetch base branch from origin: Cannot detect default branch for ... neither origin/HEAD nor origin/main exist. Set worktree.baseBranch in .archon/config.yaml to specify the branch explicitly.`
8. User added `worktree.baseBranch: master` to `.archon/config.yaml`.
9. Retried → **same error**.

The config.yaml doesn't help because setting `baseBranch` only changes which branch Archon tries to fetch — from `master` instead of auto-detection. Either way, **`git fetch origin` runs** and fails.

The Archon error message is misleading. It says "set baseBranch in config.yaml" as if that's the fix. In reality, you ALSO need a remote called `origin` to exist.

---

## Fix Options (Ranked)

### Option A — Push to GitHub (RECOMMENDED)

Cleanest. Intended workflow. No hacks.

```powershell
# Create empty private repo at github.com/digisurfsome/mp3-generator (no README)
cd C:\Users\lober\repos\mp3-generator
git remote add origin https://github.com/digisurfsome/mp3-generator.git
git push -u origin master
```

Then in Archon UI — you can either keep using the local path (now that it has `origin`) OR re-register via the GitHub URL. Both work.

**Upside:** Real backup, GitHub Actions available later, clean for teams.

**Downside:** You need a GitHub account and the network up.

### Option B — Fake Local Origin (WORKS OFFLINE)

If you really don't want GitHub for this repo, create a bare repo locally and point `origin` at it.

```powershell
# Create bare repo (this IS the "remote" — lives on your disk)
mkdir C:\Users\lober\repos\mp3-generator.git
cd C:\Users\lober\repos\mp3-generator.git
git init --bare

# Wire it up
cd C:\Users\lober\repos\mp3-generator
git remote add origin C:\Users\lober\repos\mp3-generator.git
git push -u origin master
```

Archon can now fetch from the bare repo. Works offline. No GitHub involvement.

**Upside:** No internet needed. No GitHub account.

**Downside:** No backup, just another folder on your disk. Two-directory pattern is easy to lose track of.

### Option C — Use `file://` URL at Registration (UNTESTED)

Paste `file:///C:/Users/lober/repos/mp3-generator` into the GitHub URL field. Archon should clone from it. Not verified in the codebase and may depend on git's `file://` transport being enabled. **Try only if A and B are blocked.**

### Option D — Config Only

Add `worktree.baseBranch: master` to `.archon/config.yaml` WITHOUT any other change.

**This does not work. Confirmed by source code.** Documented here only because the error message incorrectly suggests it's the fix.

---

## Required Contents of a Working Target Repo

Once `origin` is sorted, the target repo also needs everything the pipeline's bash nodes reference:

1. **`.archon/scripts/`** — Python scripts run by bash nodes:
   - `compliance-gate.py`, `full-checkpoint.py`, `lint-autofix.py`, `claude-md-audit.py`, `deploy-gate.py`, `archive-prd.py`
   - These run inside the worktree (cloned from the target repo), so the target repo must have them committed.
2. **At least one commit** — `git init` alone isn't enough.
3. **`origin` remote** — see above.
4. **Optional but recommended:** `.archon/config.yaml` with `worktree.baseBranch` if your default branch is not `main`.

**Commands and workflows are different.** Those auto-load from:
- Bundled in Archon (defaults)
- Global: `~/.archon/commands/`, `~/.archon/workflows/`
- Project: `<cwd>/.archon/commands/`, `<cwd>/.archon/workflows/`

So commands can live globally. Scripts cannot — they run inside the worktree.

---

## Module Bootstrap Checklist (For Every New Module Repo)

Copy this for each new module:

```
[ ] Create empty repo on GitHub: github.com/digisurfsome/<module-name>
[ ] Local setup:
      cd C:\Users\lober\repos
      git clone https://github.com/digisurfsome/<module-name>
      cd <module-name>
      echo "# <module-name>" > README.md
[ ] Copy scripts + commit:
      xcopy "C:\Users\lober\.autoforge\workspace\repos\digisurfsome__Greptacular\.archon\scripts" ".archon\scripts\" /E /I /Y
      git add .archon README.md
      git commit -m "init: scripts + readme"
      git push -u origin main
[ ] (Optional) Add .archon/config.yaml with worktree.baseBranch if branch is not "main"
[ ] In Archon UI: paste local path into "add codebase" field
[ ] Verify project appears in dropdown
[ ] Run pipeline
```

Alternative fully-offline path (swap steps 1 and 3):

```
[ ] mkdir C:\Users\lober\repos\<module-name>.git && cd there && git init --bare
[ ] cd back to the working dir, git remote add origin <bare-path>, git push -u origin master
```

---

## Things That Are NOT Required

- **GitHub Actions / CI** — Archon doesn't use them.
- **GitHub Issues / PRs** — not required for pipeline runs. Some workflows integrate with GitHub, but `prd-pipeline-c` does not.
- **Network access to GitHub during pipeline run** — the fetch runs once at worktree creation. After that, everything is local.
- **Archon-managed clone** — you can register via local path. Only requirement is `origin` exists.

---

## Why There's No Local-Only Mode

Searched source for flags like `skipFetch`, `offline`, `local-only`, `allowNoRemote`. None exist. The fetch is unconditional. This is a design gap in Archon, not a user mistake.

Until Archon adds a flag, the two workarounds are: real remote (GitHub) or fake remote (local bare repo).

---

## Appendix — Source Evidence

All verified against `C:\Users\lober\archon\Archon\` source as of 2026-04-22.

| Behavior | File | Lines |
|---|---|---|
| Local path registration | `packages/core/src/handlers/clone.ts` | 290–357 |
| GitHub URL clone + register | `packages/core/src/handlers/clone.ts` | 197–285 |
| Worktree `create()` entry | `packages/isolation/src/providers/worktree.ts` | 129–166 |
| `syncWorkspaceBeforeCreate()` | `packages/isolation/src/providers/worktree.ts` | 699–816 |
| Unconditional `git fetch origin` | `packages/git/src/repo.ts` | 104 |
| `getDefaultBranch()` error | `packages/git/src/branch.ts` | 68–71 |
| `WorktreeCreateConfig.baseBranch` | `packages/core/src/config/config-types.ts` | 154–202 |

---

## Related Docs

- Pipeline audit: `docs/page-prds/archon-build-upgrade/SKILL-AUDIT-REPORT.md`
- Architecture: `docs/page-prds/archon-build-upgrade/MASTER-MODULAR-ARCHITECTURE.md`
- Deferred specs: `M13-EXISTING-APP-MODE.md`, `M14-PRD-SELF-CHECK.md`, `M15-INTAKE-CLASSIFIER.md`
