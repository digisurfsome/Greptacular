#!/usr/bin/env bash
# =============================================================================
# Tool Factory Build Pipeline — Runs 4 agents sequentially via Claude CLI
# =============================================================================
#
# Usage (from Git Bash on Windows):
#   cd "C:/Users/lober/GitHub/Greptacular - AutoForge Build/Greptacular"
#   bash run_all_phases.sh
#
# Or to run a single agent:
#   bash run_all_phases.sh --agent 1
#   bash run_all_phases.sh --agent 3
#
# Options:
#   --agent N       Run only agent N (1-4)
#   --start-from N  Start from agent N and run all remaining
#   --parallel      Run agents 2 and 3 in parallel (after agent 1)
#   --dry-run       Print commands without executing
#   --model MODEL   Override model (default: opus)
#
# Dependency chain:
#   Agent 1 (Phases 1+2) → Agent 2 (Phases 3+4) → Agent 4 (Phases 7+8)
#                        → Agent 3 (Phases 5+6) →
# =============================================================================

set -euo pipefail

# ─── Config ──────────────────────────────────────────────────────────────────
PROJECT_DIR="C:/Users/lober/GitHub/Greptacular - AutoForge Build/Greptacular"
BRIEFS_DIR="${PROJECT_DIR}/docs/agent-briefs"
PRD_FILE="${PROJECT_DIR}/docs/prd-video-to-tool-factory.md"
LOG_DIR="${PROJECT_DIR}/.claude/build-logs"
MODEL="opus"
DRY_RUN=false
SINGLE_AGENT=0
START_FROM=1
PARALLEL=false

# ─── Parse Args ──────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --agent)    SINGLE_AGENT=$2; shift 2 ;;
        --start-from) START_FROM=$2; shift 2 ;;
        --parallel) PARALLEL=true; shift ;;
        --dry-run)  DRY_RUN=true; shift ;;
        --model)    MODEL=$2; shift 2 ;;
        *)          echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ─── Setup ───────────────────────────────────────────────────────────────────
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info()  { echo -e "${CYAN}[INFO]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ─── Agent Runner ────────────────────────────────────────────────────────────
run_agent() {
    local AGENT_NUM=$1
    local BRIEF_FILE="${BRIEFS_DIR}/tool-factory-agent-${AGENT_NUM}.md"
    local LOG_FILE="${LOG_DIR}/agent-${AGENT_NUM}_${TIMESTAMP}.log"
    local AGENT_DESC=""

    case $AGENT_NUM in
        1) AGENT_DESC="Phases 1+2: Data Models + Blueprint Engine + PRD Input" ;;
        2) AGENT_DESC="Phases 3+4: Theme Integration + Google Sheets Deployer" ;;
        3) AGENT_DESC="Phases 5+6: Generation Flow UI + Tool Manager UI" ;;
        4) AGENT_DESC="Phases 7+8: Batch Processing + SaaS Layer" ;;
    esac

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "AGENT ${AGENT_NUM}: ${AGENT_DESC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ ! -f "$BRIEF_FILE" ]; then
        log_error "Brief file not found: ${BRIEF_FILE}"
        return 1
    fi

    local BRIEF_CONTENT
    BRIEF_CONTENT=$(cat "$BRIEF_FILE")

    # Build the prompt
    local PROMPT="You are implementing Phase ${AGENT_NUM} of the Video-to-Tool Factory for AutoForge.

PROJECT DIRECTORY: ${PROJECT_DIR}

YOUR BRIEF (implement everything in this document):
${BRIEF_CONTENT}

INSTRUCTIONS:
1. Read the existing code files mentioned in 'EXISTING CODE REFERENCES' section of your brief
2. Create all files listed in 'FILES TO CREATE/MODIFY'
3. Every function labeled [ROBOT] must be pure Python/TypeScript with ZERO LLM calls
4. Every function labeled [AGENT] must include error handling, retries, and output validation
5. Run the test plan at the end to verify everything works
6. Run ruff check on Python files and npm run lint + npm run build on UI files
7. If tests fail, fix the issues before finishing
8. When all tests pass, commit ALL your changes to git with a descriptive message. Stage only the files you created or modified — do not use 'git add -A'. Use this format:
   git commit -m 'feat(tool-factory): Agent ${AGENT_NUM} — [short description of what was built]'
9. Do NOT push to remote — just commit locally

CRITICAL: Stay under 50% context window (100k tokens). If you're running low, commit what you have and note what's remaining."

    if [ "$DRY_RUN" = true ]; then
        log_warn "DRY RUN — would execute:"
        echo "  claude -p --model ${MODEL} --dangerously-skip-permissions [prompt from ${BRIEF_FILE}]"
        echo "  Output → ${LOG_FILE}"
        return 0
    fi

    log_info "Starting Agent ${AGENT_NUM}... (log: ${LOG_FILE})"
    log_info "Model: ${MODEL}"
    local START_TIME=$(date +%s)

    # Run Claude CLI in print mode with no permission prompts
    cd "$PROJECT_DIR"
    if claude -p \
        --model "$MODEL" \
        --dangerously-skip-permissions \
        "$PROMPT" \
        2>&1 | tee "$LOG_FILE"; then

        local END_TIME=$(date +%s)
        local DURATION=$(( END_TIME - START_TIME ))
        local MINUTES=$(( DURATION / 60 ))
        local SECONDS=$(( DURATION % 60 ))

        log_ok "Agent ${AGENT_NUM} completed in ${MINUTES}m ${SECONDS}s"
        echo "${AGENT_NUM}: SUCCESS (${MINUTES}m ${SECONDS}s)" >> "${LOG_DIR}/summary_${TIMESTAMP}.txt"
        return 0
    else
        local EXIT_CODE=$?
        local END_TIME=$(date +%s)
        local DURATION=$(( END_TIME - START_TIME ))

        log_error "Agent ${AGENT_NUM} failed with exit code ${EXIT_CODE} after ${DURATION}s"
        echo "${AGENT_NUM}: FAILED (exit code ${EXIT_CODE})" >> "${LOG_DIR}/summary_${TIMESTAMP}.txt"
        return $EXIT_CODE
    fi
}

# ─── Main ────────────────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║          TOOL FACTORY BUILD PIPELINE — 4 AGENTS                        ║"
echo "║          Stripe Minions Pattern: [ROBOT] + [AGENT] labeled             ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
log_info "Project: ${PROJECT_DIR}"
log_info "Model: ${MODEL}"
log_info "Logs: ${LOG_DIR}"
log_info "Timestamp: ${TIMESTAMP}"

if [ "$DRY_RUN" = true ]; then
    log_warn "DRY RUN MODE — no agents will actually execute"
fi

# Record start
echo "Build started: $(date)" > "${LOG_DIR}/summary_${TIMESTAMP}.txt"
echo "Model: ${MODEL}" >> "${LOG_DIR}/summary_${TIMESTAMP}.txt"
echo "---" >> "${LOG_DIR}/summary_${TIMESTAMP}.txt"

PIPELINE_START=$(date +%s)

# ─── Single Agent Mode ───────────────────────────────────────────────────────
if [ "$SINGLE_AGENT" -gt 0 ]; then
    log_info "Running single agent: ${SINGLE_AGENT}"
    run_agent "$SINGLE_AGENT"
    exit $?
fi

# ─── Sequential Pipeline ────────────────────────────────────────────────────
# Agent 1 always goes first
if [ "$START_FROM" -le 1 ]; then
    run_agent 1
    if [ $? -ne 0 ]; then
        log_error "Agent 1 failed. Cannot continue — all other agents depend on it."
        exit 1
    fi
fi

# Agents 2 and 3 — parallel or sequential
if [ "$START_FROM" -le 2 ]; then
    if [ "$PARALLEL" = true ]; then
        log_info "Running Agents 2 and 3 in PARALLEL..."

        run_agent 2 &
        PID_2=$!
        run_agent 3 &
        PID_3=$!

        FAIL=0
        wait $PID_2 || { log_error "Agent 2 failed"; FAIL=1; }
        wait $PID_3 || { log_error "Agent 3 failed"; FAIL=1; }

        if [ $FAIL -ne 0 ]; then
            log_error "One or more parallel agents failed. Check logs."
            exit 1
        fi
    else
        run_agent 2
        if [ $? -ne 0 ]; then
            log_error "Agent 2 failed."
            exit 1
        fi

        if [ "$START_FROM" -le 3 ]; then
            run_agent 3
            if [ $? -ne 0 ]; then
                log_error "Agent 3 failed."
                exit 1
            fi
        fi
    fi
elif [ "$START_FROM" -le 3 ]; then
    run_agent 3
    if [ $? -ne 0 ]; then
        log_error "Agent 3 failed."
        exit 1
    fi
fi

# Agent 4 runs last
if [ "$START_FROM" -le 4 ]; then
    run_agent 4
    if [ $? -ne 0 ]; then
        log_error "Agent 4 failed."
        exit 1
    fi
fi

# ─── Summary ─────────────────────────────────────────────────────────────────
PIPELINE_END=$(date +%s)
TOTAL_DURATION=$(( PIPELINE_END - PIPELINE_START ))
TOTAL_MINUTES=$(( TOTAL_DURATION / 60 ))
TOTAL_SECONDS=$(( TOTAL_DURATION % 60 ))

echo "" >> "${LOG_DIR}/summary_${TIMESTAMP}.txt"
echo "---" >> "${LOG_DIR}/summary_${TIMESTAMP}.txt"
echo "Total time: ${TOTAL_MINUTES}m ${TOTAL_SECONDS}s" >> "${LOG_DIR}/summary_${TIMESTAMP}.txt"
echo "Build completed: $(date)" >> "${LOG_DIR}/summary_${TIMESTAMP}.txt"

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                    BUILD PIPELINE COMPLETE                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
log_ok "Total time: ${TOTAL_MINUTES}m ${TOTAL_SECONDS}s"
log_info "Summary: ${LOG_DIR}/summary_${TIMESTAMP}.txt"
log_info "Logs: ${LOG_DIR}/agent-*_${TIMESTAMP}.log"
echo ""
echo "Next steps:"
echo "  1. Review the build logs for any warnings"
echo "  2. Check git log for the 4 commits:"
echo "     git log --oneline -6"
echo "  3. Run the full test suite:"
echo "     python -m pytest tests/test_tool_factory*.py tests/test_sheet*.py tests/test_batch*.py -v"
echo "     cd ui && npm run lint && npm run build"
echo "  4. Push everything to remote:"
echo "     git push origin main"
echo "  5. Deploy to live:"
echo "     cd C:/Users/lober/Greptacular && git pull origin main --no-edit"
echo ""
