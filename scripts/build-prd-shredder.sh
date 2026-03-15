#!/usr/bin/env bash
# Build the PRD Shredder — Phases 1-3 (Queue + Analysis Pipeline + Execution)
# Run from the dev repo root: bash scripts/build-prd-shredder.sh
set -euo pipefail

# Unset env vars that break nested claude -p
unset CLAUDECODE 2>/dev/null || true
unset CLAUDE_CODE_ENTRYPOINT 2>/dev/null || true
unset CLAUDE_CODE_OAUTH_TOKEN 2>/dev/null || true
unset ANTHROPIC_API_KEY 2>/dev/null || true

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== PRD Shredder Builder ==="
echo "Building Phases 1-3: Queue + Analysis Pipeline + Execution"
echo "Repo: $REPO_ROOT"
echo ""

# Read the PRD and build rules
PRD_CONTENT=$(cat docs/prd-prd-shredder.md)
BUILD_RULES=$(cat docs/stripe-minions-build-rules.md)

# Build the prompt
PROMPT="You are building the PRD Shredder for AutoForge. This is an automatic PRD-to-code pipeline.

## YOUR TASK
Build Phases 1-3 of the PRD Shredder:
- Phase 1: Queue (SQLite data model, FIFO processing loop, repo clone/pull)
- Phase 2: Analysis Pipeline (4-stage: PRD ingestion → codebase discovery → task extraction → consulting review)
- Phase 3: Execution (claude -p one-shot session with build rules, lint, test, commit, push)

## THE FULL PRD
${PRD_CONTENT}

## BUILD RULES (Stripe Minions Pattern — follow these)
${BUILD_RULES}

## CRITICAL ARCHITECTURE RULES

1. **Subscription auth:** ALL Claude calls use subscription auth (force_subscription=True).
   Copy the _call_via_sdk() pattern from server/services/yt_processor.py — it has every fix.
   NEVER use API keys for Claude. Read CLAUDE.md section on subscription auth.

2. **No hardcoded prompts:** All AI prompts must be stored in editable config, NOT hardcoded in Python.
   Store prompts in a JSON/YAML config file that can be edited without touching code.

3. **WebSocket logging:** Every long-running operation must stream logs via WebSocket.
   Copy the on_progress callback pattern from yt_processor.py.

4. **SDK client pattern:** Use permission_mode='acceptEdits' + settings file.
   Wrap receive_response() in try/except for rate_limit_event recovery.
   See CLAUDE.md section on SDK CLIENT PATTERN.

## FILES TO CREATE
- server/models/prd_shredder.py — SQLAlchemy models (PRDQueueItem)
- server/services/prd_shredder.py — Queue manager + processing loop
- server/services/prd_analyzer.py — 4-stage analysis pipeline
- server/routers/prd_shredder.py — REST + WebSocket endpoints

## FILES TO READ FOR REFERENCE (copy patterns from these)
- server/services/yt_processor.py — SDK client pattern, _call_via_sdk(), subscription auth
- server/services/yt_discovery.py — Multi-stage analysis pipeline pattern
- server/services/sheet_blueprint.py — Robot+agent step interleaving pattern
- server/models/tool_factory.py — SQLAlchemy model patterns
- server/routers/tool_factory.py — Router patterns
- CLAUDE.md — All architecture rules

## EXECUTION SEQUENCE (follow the Stripe Blueprint Pattern)

STEP 1 [AGENT] — Read reference files, understand existing patterns
STEP 2 [AGENT] — Create server/models/prd_shredder.py (data model)
STEP 3 [ROBOT] — ruff check server/models/prd_shredder.py --fix
STEP 4 [AGENT] — Create server/services/prd_shredder.py (queue + processing loop)
STEP 5 [ROBOT] — ruff check server/services/prd_shredder.py --fix
STEP 6 [AGENT] — Create server/services/prd_analyzer.py (4-stage analysis pipeline)
STEP 7 [ROBOT] — ruff check server/services/prd_analyzer.py --fix
STEP 8 [AGENT] — Create server/routers/prd_shredder.py (REST endpoints)
STEP 9 [ROBOT] — ruff check server/routers/prd_shredder.py --fix
STEP 10 [ROBOT] — ruff check . (full project lint)
STEP 11 [AGENT] — Wire router into server/main.py
STEP 12 [ROBOT] — Final ruff check, verify imports resolve
STEP 13 [ROBOT] — git add + git commit

DO NOT modify UI files. Backend only. The UI page comes later.
DO NOT skip lint checks between files.
DO NOT use bypassPermissions — use acceptEdits.
Maximum 2 retry attempts on any single error.
"

echo "Launching claude -p to build the PRD Shredder..."
echo "This will take 3-10 minutes."
echo ""

claude -p "$PROMPT" \
  --allowedTools "Edit,Write,Read,Bash(ruff*),Bash(git*),Bash(python*),Bash(pip*),Bash(ls*),Bash(cat*),Bash(mkdir*),Glob,Grep" \
  2>&1 | tee "$REPO_ROOT/.claude/build-logs/prd-shredder-$(date +%Y%m%d-%H%M%S).log"

echo ""
echo "=== Build complete ==="
echo "Check git log for the commit."
echo "Next: build the UI page, then feed all other PRDs into the Shredder."
