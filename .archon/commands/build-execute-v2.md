# Build: Execute Phase (v2)

Implement the phase specified in `$ARGUMENTS`. Read your phase file and build exactly what it says.

> **v2 change (M6):** Before writing any file, check for per-directory CLAUDE.md files
> as described in "Directory Rules" below. This is best-effort guidance — the pipeline
> enforces it via an audit node, not a hard gate.

## Input

Read `$ARTIFACTS_DIR/phases/$ARGUMENTS.md` (e.g., `phases/phase-1.md` when `$ARGUMENTS` is `phase-1`).

This file contains everything you need:
1. Build Rules Preamble — the engineering standards for this build
2. File Sandbox Declaration — which files you may and may not touch
3. Build Order with Pulse Points — the exact sequence to follow
4. Seam Check Definitions — cross-mechanism connection checks
5. Objective and Feature Requirements — what this phase delivers
6. Pattern References — Wall/Door/Room classifications with verification methods
7. Violation Handling — severity table
8. Full Checkpoint — the 4-step gate you must pass before finishing

## Directory Rules (soft guidance — best-effort, not gated)

Before writing a file at path P, check for CLAUDE.md files in this order:
1. `<dir of P>/CLAUDE.md`
2. `<parent dir of P>/CLAUDE.md`
3. Project root `CLAUDE.md`

Read the most-specific one that exists. Its rules apply to your work in that directory.

If no CLAUDE.md exists for a directory you are creating, write one. It should state:
- What lives in this directory
- What conventions apply (naming, exports, file size limits)
- What must NOT be placed here

Keep per-directory CLAUDE.md files under 80 lines. They are not READMEs — they are rules files.

## Process

Follow the Build Order in your phase file exactly. At each Pulse Point:
1. Verify the file compiles (no syntax errors)
2. Verify imports resolve
3. Run the Pulse check described in the phase file

At Seam Checks: verify the cross-file connections are correct before continuing.

At the Full Checkpoint: run all 4 steps. Do not claim done until all 4 pass.

## Contract (MANDATORY — NO EXCEPTIONS)

You build only what is in the File Sandbox Declaration. No files outside `files_allowed`
may be created or modified. If you need to touch a file not in `files_allowed`, STOP and
document why in `$ARTIFACTS_DIR/sandbox-violations-attempted.md` — do not proceed.

## Output

- All files listed in the Build Order
- Per-directory CLAUDE.md files for any new directories created
- Update `$ARTIFACTS_DIR/build-progress.md` with a one-line status per file written
