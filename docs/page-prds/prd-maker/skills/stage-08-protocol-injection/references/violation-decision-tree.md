# Violation Decision Tree

## The Four Severity Levels

Every phase gets all four levels. Triggers are customized per phase based on its `files_allowed` sandbox.

```
VIOLATION DETECTED (via git diff comparison)
│
├─ LOW: Touched shared/common files
│   Triggers:
│   - Modified a shared types file (e.g., types.ts, interfaces.ts)
│   - Added an import to an existing utility file
│   - Added an export to a shared constants file
│   - Modified a shared config that multiple phases reference
│   Response: log_and_proceed
│   Action: Log the modification in the phase report. Note which file
│   was touched and why. Proceed with the build. Review at full checkpoint.
│
├─ MEDIUM: Modified another phase's domain file
│   Triggers:
│   - Modified a file listed in ANOTHER phase's files_allowed
│   - Added a new export to a file owned by another phase
│   - Changed import structure of a file from another phase
│   Response: review_and_decide
│   Decision Tree:
│   ├─ Additive change (added export, added prop, added route):
│   │   → proceed_with_caution — log it, continue, verify at checkpoint
│   ├─ Destructive change (renamed function, changed logic, removed export):
│   │   → revert_file — git checkout that specific file, re-run phase
│   │   with constraint: "Do NOT modify [file]"
│   └─ Unclear (can't determine if additive or destructive):
│       → flag_human — save state, present the diff, ask human to decide
│
├─ HIGH: Deleted files or changed core config outside scope
│   Triggers:
│   - Deleted any file (rm, unlink)
│   - Modified core config files outside this phase's scope
│   - Changed authentication logic outside the auth phase
│   - Modified database schema outside the data-model phase
│   - Changed environment variable definitions
│   Response: revert_entire_phase
│   Action: git reset --hard to phase baseline snapshot. Re-run with
│   tighter constraints or break the phase into smaller sub-phases.
│
└─ CRITICAL: Touched protected files
    Triggers:
    - Modified CLAUDE.md
    - Modified .env or any .env.* file
    - Modified package.json "scripts" section
    - Modified build configuration (vite.config, webpack.config, tsconfig)
    - Modified CI/CD configuration (.github/workflows, Dockerfile)
    - Modified security configuration (auth middleware, CORS settings)
    Response: full_stop
    Action: IMMEDIATELY STOP. Revert ALL changes. Flag for human review.
    This is either a prompt injection attempt or a fundamentally confused
    agent. Do NOT retry automatically. Human must inspect and approve
    before any further work.
```

## Customizing Triggers Per Phase

When embedding the violation tree into a specific phase:

1. **LOW triggers**: List the specific shared files relevant to this phase. Example: Phase 2 (Dashboard) might list `src/types/index.ts` and `src/lib/utils.ts`.

2. **MEDIUM triggers**: List specific files from OTHER phases' sandboxes. Example: If Phase 1 owns `src/lib/auth.ts`, then Phase 2's MEDIUM triggers include `"modified src/lib/auth.ts (owned by Phase 1)"`.

3. **HIGH triggers**: Always include file deletion. Add phase-specific high-severity items (e.g., "changed auth logic" for non-auth phases).

4. **CRITICAL triggers**: These are the same across ALL phases. The protected file list is global.

## Self-Report vs Git Diff

The violation tree is evaluated using TWO inputs:

1. **Agent self-report** (Step 1): Agent lists files it created/modified. This is the FIRST pass.
2. **Git diff** (Step 2): Run `git diff --name-only $BASELINE`. This is GROUND TRUTH.

If the self-report and git diff DO NOT MATCH, that ITSELF is a violation:
- If agent reported MORE files than git shows → probably harmless (agent over-reported), log as LOW
- If git shows MORE files than agent reported → agent touched files it didn't disclose. Treat as MEDIUM minimum, escalate to HIGH if the undisclosed files are from another phase's domain.
