#!/usr/bin/env bash
# =============================================================================
# Quick Test Build — 3 tiny phases to verify the pipeline works
# Should take ~5-10 minutes total
# =============================================================================
#
# Usage:
#   cd "C:/Users/lober/GitHub/Greptacular - AutoForge Build/Greptacular"
#   bash scripts/test-build-quick.sh
#
# =============================================================================

set -euo pipefail

# ─── Auth Fix ────────────────────────────────────────────────────────────────
unset ANTHROPIC_API_KEY 2>/dev/null || true

# ─── Config ──────────────────────────────────────────────────────────────────
PROJECT_DIR="C:/Users/lober/GitHub/Greptacular - AutoForge Build/Greptacular"
TEST_DIR="${PROJECT_DIR}/.claude/test-build"
LOG_DIR="${PROJECT_DIR}/.claude/build-logs"
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
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ─── Setup test directory ────────────────────────────────────────────────────
mkdir -p "$LOG_DIR"
mkdir -p "$TEST_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║       QUICK TEST BUILD — 3 phases, ~5-10 min total                     ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
log_info "Test dir: ${TEST_DIR}"
log_info "Model: sonnet"
log_info "Timestamp: ${TIMESTAMP}"

PIPELINE_START=$(date +%s)
TOTAL_PHASES=3

# ─── Phase Runner ────────────────────────────────────────────────────────────
run_phase() {
    local PHASE_NUM=$1
    local PHASE_DESC=$2
    local PROMPT=$3
    local JSON_FILE="${LOG_DIR}/test-build-phase-${PHASE_NUM}_${TIMESTAMP}.json"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "PHASE ${PHASE_NUM} of ${TOTAL_PHASES}: ${PHASE_DESC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "Starting... (output: ${JSON_FILE})"

    local START_TIME=$(date +%s)

    cd "$TEST_DIR"
    if echo "$PROMPT" | claude -p \
        --model sonnet \
        --output-format json \
        --dangerously-skip-permissions \
        > "$JSON_FILE" 2>&1; then

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
    total_in = inp + cache_create + cache_read
    print(f'{total_in}|{out}|{cost:.4f}')
except Exception as e:
    print('0|0|0.0000')
" "$JSON_FILE" 2>/dev/null) || PARSE_OUTPUT="0|0|0.0000"

        local TOTAL_IN=$(echo "$PARSE_OUTPUT" | cut -d'|' -f1)
        local OUT_TOKENS=$(echo "$PARSE_OUTPUT" | cut -d'|' -f2)
        local COST_USD=$(echo "$PARSE_OUTPUT" | cut -d'|' -f3)

        # Display result text from JSON
        $PYTHON -c "
import json, sys
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    print(d.get('result', 'No result text'))
except:
    print('Could not parse result')
" "$JSON_FILE" 2>/dev/null

        echo ""
        log_info "📊 Tokens: ${TOTAL_IN} in / ${OUT_TOKENS} out | API cost equiv: \$${COST_USD}"
        log_ok "Phase ${PHASE_NUM} of ${TOTAL_PHASES} completed in ${MINUTES}m ${SECONDS}s"
        echo "${PHASE_NUM}: SUCCESS (${MINUTES}m ${SECONDS}s) [model: sonnet] [tokens: ${TOTAL_IN} in / ${OUT_TOKENS} out | \$${COST_USD}]" >> "${LOG_DIR}/test-build-summary_${TIMESTAMP}.txt"

        # Accumulate totals (bash integer math)
        TOTAL_INPUT_TOKENS=$(( TOTAL_INPUT_TOKENS + TOTAL_IN ))
        TOTAL_OUTPUT_TOKENS=$(( TOTAL_OUTPUT_TOKENS + OUT_TOKENS ))

        return 0
    else
        local EXIT_CODE=$?
        log_error "Phase ${PHASE_NUM} of ${TOTAL_PHASES} failed with exit code ${EXIT_CODE}"
        echo "${PHASE_NUM}: FAILED (exit code ${EXIT_CODE}) [model: sonnet]" >> "${LOG_DIR}/test-build-summary_${TIMESTAMP}.txt"
        return $EXIT_CODE
    fi
}

# ─── Record start ────────────────────────────────────────────────────────────
echo "=== TEST BUILD ===" > "${LOG_DIR}/test-build-summary_${TIMESTAMP}.txt"
echo "Started: $(date)" >> "${LOG_DIR}/test-build-summary_${TIMESTAMP}.txt"
echo "---" >> "${LOG_DIR}/test-build-summary_${TIMESTAMP}.txt"

# ─── Phase 1: Create a simple HTML file ──────────────────────────────────────
run_phase 1 "Create index.html with basic structure" \
"Create a single file called index.html in the current directory. It should be a simple todo app with:
- An input field and Add button
- A list that shows todos
- Each todo has a delete button
- All in one file (inline CSS and JS)
- Use localStorage to persist todos
Keep it simple — under 100 lines total. Just create the file and confirm it exists."

# ─── Phase 2: Add styling ────────────────────────────────────────────────────
run_phase 2 "Add dark mode styling" \
"Read the existing index.html file. Add dark mode styling to it:
- Dark background (#1a1a2e)
- Light text (#eee)
- Styled input field with border
- Hover effects on buttons
- A nice font (system-ui)
Edit the existing file — don't create a new one. Keep all functionality working."

# ─── Phase 3: Verify and report ──────────────────────────────────────────────
run_phase 3 "Verify everything works" \
"Read index.html and verify:
1. The file exists and is valid HTML
2. It has an input field and add button
3. It has delete functionality
4. It uses localStorage
5. It has dark mode styling
Report what you find. If anything is broken, fix it. Then list all files in the current directory."

# ─── Summary ─────────────────────────────────────────────────────────────────
PIPELINE_END=$(date +%s)
TOTAL_DURATION=$(( PIPELINE_END - PIPELINE_START ))
TOTAL_MINUTES=$(( TOTAL_DURATION / 60 ))
TOTAL_SECONDS=$(( TOTAL_DURATION % 60 ))

echo "" >> "${LOG_DIR}/test-build-summary_${TIMESTAMP}.txt"
echo "---" >> "${LOG_DIR}/test-build-summary_${TIMESTAMP}.txt"
echo "Total time: ${TOTAL_MINUTES}m ${TOTAL_SECONDS}s" >> "${LOG_DIR}/test-build-summary_${TIMESTAMP}.txt"
echo "TOKEN TOTALS: ${TOTAL_INPUT_TOKENS} input / ${TOTAL_OUTPUT_TOKENS} output" >> "${LOG_DIR}/test-build-summary_${TIMESTAMP}.txt"
echo "Completed: $(date)" >> "${LOG_DIR}/test-build-summary_${TIMESTAMP}.txt"

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║       ✅  ALL 3 PHASES FINISHED — TEST BUILD COMPLETE  ✅              ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
log_ok "Total time: ${TOTAL_MINUTES}m ${TOTAL_SECONDS}s"
echo ""
echo "=== TOKEN USAGE ==="
echo -e "  Total input tokens:  ${GREEN}${TOTAL_INPUT_TOKENS}${NC}"
echo -e "  Total output tokens: ${GREEN}${TOTAL_OUTPUT_TOKENS}${NC}"
echo ""
echo "=== PHASE SUMMARY ==="
cat "${LOG_DIR}/test-build-summary_${TIMESTAMP}.txt"
echo ""
echo "=== FILES CREATED ==="
ls -la "${TEST_DIR}/"
echo ""
log_info "Full logs: ${LOG_DIR}/test-build-phase-*_${TIMESTAMP}.json"
echo ""
