#!/usr/bin/env bash
# =============================================================================
# CLI Scripter v2 Build Pipeline — Runs 4 agents sequentially via Claude CLI
# =============================================================================
#
# Usage (from Git Bash on Windows):
#   cd "C:/Users/lober/GitHub/Greptacular - AutoForge Build/Greptacular"
#   bash scripts/run-cli-scripter-build.sh
#
# Or to run a single agent:
#   bash scripts/run-cli-scripter-build.sh --agent 1
#   bash scripts/run-cli-scripter-build.sh --agent 4
#
# Options:
#   --agent N       Run only agent N (1-4)
#   --start-from N  Start from agent N and run all remaining
#   --dry-run       Print commands without executing
#   --model MODEL   Override model (default: sonnet, agent 4 always uses opus)
#
# No interaction required — runs all agents straight through.
# =============================================================================

set -euo pipefail

# ─── Auth Fix ────────────────────────────────────────────────────────────────
# Unset API key so Claude CLI uses the Max subscription instead of API credits
unset ANTHROPIC_API_KEY 2>/dev/null || true
unset CLAUDECODE 2>/dev/null || true
unset CLAUDE_CODE_ENTRYPOINT 2>/dev/null || true
unset CLAUDE_CODE_OAUTH_TOKEN 2>/dev/null || true

# ─── Config ──────────────────────────────────────────────────────────────────
PROJECT_DIR="C:/Users/lober/GitHub/Greptacular - AutoForge Build/Greptacular"
BRIEFS_DIR="${PROJECT_DIR}/docs/agent-briefs"
PRD_FILE="${PROJECT_DIR}/docs/prd-cli-scripter-v2.md"
LOG_DIR="${PROJECT_DIR}/.claude/build-logs"
MODEL="sonnet"
DRY_RUN=false
SINGLE_AGENT=0
START_FROM=1

# ─── Parse Args ──────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --agent)    SINGLE_AGENT=$2; shift 2 ;;
        --start-from) START_FROM=$2; shift 2 ;;
        --dry-run)  DRY_RUN=true; shift ;;
        --model)    MODEL=$2; shift 2 ;;
        *)          echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ─── Setup ───────────────────────────────────────────────────────────────────
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TOTAL_INPUT_TOKENS=0
TOTAL_OUTPUT_TOKENS=0
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "python")

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${CYAN}[INFO]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ─── Agent Runner ────────────────────────────────────────────────────────────
run_agent() {
    local AGENT_NUM=$1
    local BRIEF_FILE="${BRIEFS_DIR}/cli-scripter-agent-${AGENT_NUM}.md"
    local JSON_FILE="${LOG_DIR}/cli-scripter-agent-${AGENT_NUM}_${TIMESTAMP}.json"
    local AGENT_MODEL="$MODEL"
    local AGENT_DESC=""

    # Agent 4 (verification) always uses opus
    if [ "$AGENT_NUM" -eq 4 ]; then
        AGENT_MODEL="opus"
    fi

    case $AGENT_NUM in
        1) AGENT_DESC="Package 1: Foundation & UX Fixes (8 phases)" ;;
        2) AGENT_DESC="Package 2: Storage, Prompts & Display (8 phases)" ;;
        3) AGENT_DESC="Package 3: Dashboard, Terminal, Sketches (10 phases)" ;;
        4) AGENT_DESC="Package 4: Post-Build Verification & Testing" ;;
    esac

    local TOTAL_AGENTS=4
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "AGENT ${AGENT_NUM} of ${TOTAL_AGENTS}: ${AGENT_DESC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ ! -f "$BRIEF_FILE" ]; then
        log_error "Brief file not found: ${BRIEF_FILE}"
        return 1
    fi

    local BRIEF_CONTENT
    BRIEF_CONTENT=$(cat "$BRIEF_FILE")

    local PROMPT="You are implementing the CLI Scripter v2 upgrade for AutoForge.

PROJECT DIRECTORY: ${PROJECT_DIR}

FULL PRD: Read docs/prd-cli-scripter-v2.md for complete specs, diagrams, and data models.

YOUR BRIEF (implement everything in this document):
${BRIEF_CONTENT}

INSTRUCTIONS:
1. Read the full PRD first: docs/prd-cli-scripter-v2.md
2. Read the existing source files to understand current patterns
3. Build every phase in your brief, in order
4. After EVERY phase: run 'cd ui && npm run build' — zero TypeScript errors
5. Run 'cd ui && npm run lint' to check for lint issues
6. Commit after each phase with a clear message
7. Stage only files you created or modified — do NOT use 'git add -A'
8. Do NOT push to remote — just commit locally
9. Stay under 50% context window (100k tokens). If running low, commit what you have.

CRITICAL: Match existing patterns — neobrutalism design, Tailwind CSS v4, React 19, TanStack Query, Radix UI, orange accent."

    if [ "$DRY_RUN" = true ]; then
        log_warn "DRY RUN — would execute:"
        echo "  claude -p --output-format json --model ${AGENT_MODEL} --dangerously-skip-permissions [prompt from ${BRIEF_FILE}]"
        echo "  Output → ${JSON_FILE}"
        return 0
    fi

    log_info "Starting Agent ${AGENT_NUM}... (output: ${JSON_FILE})"
    log_info "Model: ${AGENT_MODEL}"
    local START_TIME=$(date +%s)

    # Start heartbeat so user knows agent is still running
    (while true; do
        sleep 60
        local ELAPSED=$(( $(date +%s) - START_TIME ))
        local E_MIN=$(( ELAPSED / 60 ))
        echo -e "${CYAN}[HEARTBEAT]${NC} Agent ${AGENT_NUM} still running... ${E_MIN}m elapsed ($(date +%H:%M:%S))"
    done) &
    local HEARTBEAT_PID=$!

    cd "$PROJECT_DIR"
    if claude -p \
        --model "$AGENT_MODEL" \
        --output-format json \
        --dangerously-skip-permissions \
        "$PROMPT" \
        > "$JSON_FILE" 2>&1; then

        # Kill heartbeat
        kill $HEARTBEAT_PID 2>/dev/null
        wait $HEARTBEAT_PID 2>/dev/null

        local END_TIME=$(date +%s)
        local DURATION=$(( END_TIME - START_TIME ))
        local MINUTES=$(( DURATION / 60 ))
        local SECONDS=$(( DURATION % 60 ))

        # Parse token data from JSON output
        local PARSE_OUTPUT
        PARSE_OUTPUT=$($PYTHON -c "
import json, sys
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    u = d.get('usage', {})
    inp = u.get('input_tokens', 0)
    cache_create = u.get('cache_creation_input_tokens', 0)
    cache_read = u.get('cache_read_input_tokens', 0)
    out = u.get('output_tokens', 0)
    cost = d.get('total_cost_usd', 0)
    num_turns = d.get('num_turns', 0)
    duration_api = d.get('duration_api_ms', 0) / 1000
    total_in = inp + cache_create + cache_read
    print(f'{total_in}|{out}|{cost:.4f}|{num_turns}|{duration_api:.0f}')
except Exception as e:
    print('0|0|0.0000|0|0')
" "$JSON_FILE" 2>/dev/null) || PARSE_OUTPUT="0|0|0.0000|0|0"

        local TOTAL_IN=$(echo "$PARSE_OUTPUT" | cut -d'|' -f1)
        local OUT_TOKENS=$(echo "$PARSE_OUTPUT" | cut -d'|' -f2)
        local COST_USD=$(echo "$PARSE_OUTPUT" | cut -d'|' -f3)
        local NUM_TURNS=$(echo "$PARSE_OUTPUT" | cut -d'|' -f4)
        local API_DURATION=$(echo "$PARSE_OUTPUT" | cut -d'|' -f5)

        # Show abbreviated result (first 500 chars)
        echo ""
        $PYTHON -c "
import json, sys
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    r = d.get('result', 'No result')
    # Show last 500 chars (most relevant part — the summary)
    if len(r) > 500:
        print('...' + r[-500:])
    else:
        print(r)
except:
    print('Could not parse result')
" "$JSON_FILE" 2>/dev/null

        echo ""
        log_info "📊 Tokens: ${TOTAL_IN} in / ${OUT_TOKENS} out | Turns: ${NUM_TURNS} | API time: ${API_DURATION}s | Cost equiv: \$${COST_USD}"
        log_ok "Agent ${AGENT_NUM} of ${TOTAL_AGENTS} completed in ${MINUTES}m ${SECONDS}s"
        echo "${AGENT_NUM}: SUCCESS (${MINUTES}m ${SECONDS}s) [model: ${AGENT_MODEL}] [tokens: ${TOTAL_IN} in / ${OUT_TOKENS} out | turns: ${NUM_TURNS} | \$${COST_USD}]" >> "${LOG_DIR}/cli-scripter-summary_${TIMESTAMP}.txt"

        # Accumulate totals
        TOTAL_INPUT_TOKENS=$(( TOTAL_INPUT_TOKENS + TOTAL_IN ))
        TOTAL_OUTPUT_TOKENS=$(( TOTAL_OUTPUT_TOKENS + OUT_TOKENS ))

        return 0
    else
        local EXIT_CODE=$?

        # Kill heartbeat
        kill $HEARTBEAT_PID 2>/dev/null
        wait $HEARTBEAT_PID 2>/dev/null

        local END_TIME=$(date +%s)
        local DURATION=$(( END_TIME - START_TIME ))

        log_error "Agent ${AGENT_NUM} of ${TOTAL_AGENTS} failed with exit code ${EXIT_CODE} after ${DURATION}s"
        echo "${AGENT_NUM}: FAILED (exit code ${EXIT_CODE}) [model: ${AGENT_MODEL}]" >> "${LOG_DIR}/cli-scripter-summary_${TIMESTAMP}.txt"
        return $EXIT_CODE
    fi
}

# ─── Main ────────────────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║       CLI SCRIPTER v2 BUILD PIPELINE — 4 AGENTS                        ║"
echo "║       3 build packages + 1 verification package                        ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
log_info "Project: ${PROJECT_DIR}"
log_info "Model: ${MODEL} (agent 4 uses opus)"
log_info "Logs: ${LOG_DIR}"
log_info "Timestamp: ${TIMESTAMP}"

if [ "$DRY_RUN" = true ]; then
    log_warn "DRY RUN MODE — no agents will actually execute"
fi

# Record start
echo "=== BUILD STATUS ===" > "${LOG_DIR}/cli-scripter-summary_${TIMESTAMP}.txt"
echo "Build started: $(date)" >> "${LOG_DIR}/cli-scripter-summary_${TIMESTAMP}.txt"
echo "Model: ${MODEL}" >> "${LOG_DIR}/cli-scripter-summary_${TIMESTAMP}.txt"
echo "---" >> "${LOG_DIR}/cli-scripter-summary_${TIMESTAMP}.txt"

PIPELINE_START=$(date +%s)

# ─── Single Agent Mode ───────────────────────────────────────────────────────
if [ "$SINGLE_AGENT" -gt 0 ]; then
    log_info "Running single agent: ${SINGLE_AGENT}"
    run_agent "$SINGLE_AGENT"
    exit $?
fi

# ─── Sequential Pipeline (no pauses — runs all the way through) ─────────────
for AGENT_NUM in 1 2 3 4; do
    if [ "$AGENT_NUM" -lt "$START_FROM" ]; then
        continue
    fi

    run_agent "$AGENT_NUM"
    if [ $? -ne 0 ]; then
        log_error "Agent ${AGENT_NUM} failed. Stopping pipeline."
        exit 1
    fi
done

# ─── Summary ─────────────────────────────────────────────────────────────────
PIPELINE_END=$(date +%s)
TOTAL_DURATION=$(( PIPELINE_END - PIPELINE_START ))
TOTAL_MINUTES=$(( TOTAL_DURATION / 60 ))
TOTAL_SECONDS=$(( TOTAL_DURATION % 60 ))

echo "" >> "${LOG_DIR}/cli-scripter-summary_${TIMESTAMP}.txt"
echo "---" >> "${LOG_DIR}/cli-scripter-summary_${TIMESTAMP}.txt"
echo "Total time: ${TOTAL_MINUTES}m ${TOTAL_SECONDS}s" >> "${LOG_DIR}/cli-scripter-summary_${TIMESTAMP}.txt"
echo "TOKEN TOTALS: ${TOTAL_INPUT_TOKENS} input / ${TOTAL_OUTPUT_TOKENS} output" >> "${LOG_DIR}/cli-scripter-summary_${TIMESTAMP}.txt"
echo "Build completed: $(date)" >> "${LOG_DIR}/cli-scripter-summary_${TIMESTAMP}.txt"

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║              ✅  ALL 4 AGENTS FINISHED — BUILD COMPLETE  ✅            ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
log_ok "Total time: ${TOTAL_MINUTES}m ${TOTAL_SECONDS}s"
echo ""
echo "=== TOKEN USAGE ==="
echo -e "  Total input tokens:  ${GREEN}${TOTAL_INPUT_TOKENS}${NC}"
echo -e "  Total output tokens: ${GREEN}${TOTAL_OUTPUT_TOKENS}${NC}"
echo ""
echo "=== AGENT SUMMARY ==="
cat "${LOG_DIR}/cli-scripter-summary_${TIMESTAMP}.txt"
echo ""
log_info "Full logs: ${LOG_DIR}/cli-scripter-agent-*_${TIMESTAMP}.json"
echo ""

# Show latest files and git log
echo "=== LATEST FILES ==="
ls -lt "${PROJECT_DIR}/ui/src/pages/" | head -5
ls -lt "${PROJECT_DIR}/ui/src/components/" 2>/dev/null | head -10
echo ""
echo "=== GIT LOG ==="
cd "$PROJECT_DIR"
git log --oneline -15
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║  Next: Deploy chain — npm build, git push, pull to live, restart       ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
