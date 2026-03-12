#!/bin/bash
# ============================================================================
# CLI Scripter v2 — Multi-Package Build Runner
# ============================================================================
# Runs all 4 packages sequentially using Claude CLI (subscription auth).
# Each package is a separate Claude session with its own context window.
#
# Usage:
#   bash scripts/run-cli-scripter-build.sh                    # Run all 4 packages
#   bash scripts/run-cli-scripter-build.sh --start-from 2     # Resume from Package 2
#   bash scripts/run-cli-scripter-build.sh --package 4        # Run only Package 4
#   bash scripts/run-cli-scripter-build.sh --dry-run          # Show prompts without running
#
# After each package completes, the script:
#   1. Runs `cd ui && npm run build` to verify TypeScript compiles
#   2. Runs `cd ui && npm run lint` to verify no lint errors
#   3. Pauses and asks you to confirm before continuing to the next package
#
# Requirements:
#   - Claude CLI installed and authenticated (subscription plan)
#   - Node.js 20+ (for UI build/lint)
#   - Git (for commit verification)
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
ORANGE='\033[0;33m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Config
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PRD_FILE="docs/prd-cli-scripter-v2.md"
MODEL="sonnet"  # Default model — sonnet for building, opus for verification
LOG_DIR="$PROJECT_DIR/.claude/build-logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Parse arguments
START_FROM=1
SINGLE_PACKAGE=0
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --start-from)
      START_FROM="$2"
      shift 2
      ;;
    --package)
      SINGLE_PACKAGE="$2"
      START_FROM="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --model)
      MODEL="$2"
      shift 2
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Usage: $0 [--start-from N] [--package N] [--dry-run] [--model sonnet|opus]"
      exit 1
      ;;
  esac
done

# Create log directory
mkdir -p "$LOG_DIR"

# ============================================================================
# Helper Functions
# ============================================================================

log_header() {
  echo ""
  echo -e "${ORANGE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BOLD}${ORANGE}  $1${NC}"
  echo -e "${ORANGE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
}

log_step() {
  echo -e "${CYAN}  ▶ $1${NC}"
}

log_success() {
  echo -e "${GREEN}  ✓ $1${NC}"
}

log_error() {
  echo -e "${RED}  ✗ $1${NC}"
}

log_warn() {
  echo -e "${YELLOW}  ⚠ $1${NC}"
}

# Run build verification between packages
verify_build() {
  local pkg_num=$1
  log_step "Running post-package verification..."

  cd "$PROJECT_DIR"

  # TypeScript build check
  log_step "TypeScript build check (cd ui && npm run build)..."
  if cd ui && npm run build 2>&1 | tee "$LOG_DIR/pkg${pkg_num}_build_${TIMESTAMP}.log"; then
    log_success "TypeScript build passed"
    cd "$PROJECT_DIR"
  else
    log_error "TypeScript build FAILED — check $LOG_DIR/pkg${pkg_num}_build_${TIMESTAMP}.log"
    cd "$PROJECT_DIR"
    return 1
  fi

  # Lint check
  log_step "Lint check (cd ui && npm run lint)..."
  if cd ui && npm run lint 2>&1 | tee "$LOG_DIR/pkg${pkg_num}_lint_${TIMESTAMP}.log"; then
    log_success "Lint passed"
    cd "$PROJECT_DIR"
  else
    log_warn "Lint warnings — check $LOG_DIR/pkg${pkg_num}_lint_${TIMESTAMP}.log"
    cd "$PROJECT_DIR"
  fi

  # Git status
  log_step "Git status..."
  cd "$PROJECT_DIR"
  local uncommitted=$(git status --porcelain | wc -l)
  if [ "$uncommitted" -gt 0 ]; then
    log_warn "$uncommitted uncommitted files — agent may not have committed everything"
    git status --short
  else
    log_success "All changes committed"
  fi

  return 0
}

# Pause between packages
pause_between_packages() {
  local current=$1
  local next=$2
  echo ""
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${YELLOW}  Package $current complete. Package $next is next.${NC}"
  echo -e "${YELLOW}  Check the build output above. If something looks wrong, Ctrl+C to stop.${NC}"
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
  read -p "  Press Enter to continue to Package $next, or Ctrl+C to stop... "
  echo ""
}

# ============================================================================
# Package Prompts
# ============================================================================

PACKAGE_1_PROMPT="You are building Package 1 of the CLI Scripter v2 upgrade for AutoForge.

READ THE FULL PRD FIRST: $PRD_FILE

YOUR ASSIGNMENT: Package 1 — Foundation & UX Fixes (8 phases)

Build these phases IN ORDER:
1. Phase 20: usePersistedState hook + migrate ~30 useState calls to localStorage
2. Phase 21: Clear buttons (✕ icon) on all text inputs and textareas
3. Phase 22: Phase Assignments → read-only output + Regenerate button
4. Phase 23: ProjectFileBrowser component in 2 spots + backend git endpoint
5. Phase 16: RuleBlock component (named blocks, tags, checkboxes, sidebar rail)
6. Phase 17: Combiner component + two-way checkbox binding with RuleBlocks
7. Phase 18: Gate popup (single/split + new build/edit mode) + Send-to-Combiner flow
8. Phase 19: Backend rule persistence (SQLite or JSON) + load/save endpoints

RULES:
- Read the PRD section for each phase BEFORE building it
- Read existing source files to understand current patterns
- After EVERY phase: run 'cd ui && npm run build' — must pass with zero TypeScript errors
- Commit to main after each phase with a clear message
- Match existing patterns: neobrutalism design, Tailwind CSS v4, React 19, TanStack Query, Radix UI
- Do NOT skip phases. Do NOT restructure the page layout. Build exactly what the PRD describes.
- If you run out of context, commit what you have and leave a note about what's next.

When all 8 phases are done, commit with: 'Package 1 complete — persistence, UX fixes, rules library done.'"

PACKAGE_2_PROMPT="You are building Package 2 of the CLI Scripter v2 upgrade for AutoForge.

READ THE FULL PRD FIRST: $PRD_FILE

YOUR ASSIGNMENT: Package 2 — Storage, Prompts & Display Systems (8 phases)

IMPORTANT: Package 1 has already been built. Its code is in the codebase. Read it to understand what exists before you start.

Build these phases IN ORDER:
1. Phase 7: SQLite config storage (build configs with full state snapshots)
2. Phase 8: Build Library UI (save/load/delete build configs, search, timestamps)
3. Phase 9: Queue management upgrade (reorder, status badges, dependency handling)
4. Phase 12: PromptBar component (lock icon, inline edit, collapse/expand per prompt)
5. Phase 13: Prompt persistence in Build Storage (save edited prompts with configs)
6. Phase 14: Pipeline card component (replace unusable text list with visual cards)
7. Phase 15: Parallel wave parser + CLI script generation for concurrent phases
8. FIX: Deterministic script templates (Python string formatting, no LLM)

RULES:
- Read the PRD section for each phase BEFORE building it
- Read existing source files to understand current patterns
- After EVERY phase: run 'cd ui && npm run build' — must pass with zero TypeScript errors
- Commit to main after each phase with a clear message
- Match existing patterns: neobrutalism design, Tailwind CSS v4, React 19, TanStack Query, Radix UI
- Do NOT skip phases. Do NOT restructure the page layout. Build exactly what the PRD describes.
- If you run out of context, commit what you have and leave a note about what's next.

When all 8 phases are done, commit with: 'Package 2 complete — storage, prompts, estimate cards, parallel waves, deterministic fix done.'"

PACKAGE_3_PROMPT="You are building Package 3 of the CLI Scripter v2 upgrade for AutoForge.

READ THE FULL PRD FIRST: $PRD_FILE

YOUR ASSIGNMENT: Package 3 — Live Dashboard, Terminal, Boilerplate & Sketches (10 phases)

IMPORTANT: Packages 1 and 2 have already been built. Their code is in the codebase. Read it to understand what exists before you start.

Build these phases IN ORDER:
1. Phase 1: Backend process manager (subprocess lifecycle, PID tracking)
2. Phase 2: Progress parser (regex extraction from Claude CLI stdout)
3. Phase 3: Dashboard UI strip (progress bars, agent status, phase indicators)
4. Phase 4: Embedded terminal panel (xterm.js, WebSocket to pty)
5. Phase 5: Phase status sidebar (clickable phase list with live status icons)
6. Phase 6: Refresh interval selector (auto-refresh rate control)
7. Phase 10: Boilerplate analysis docs (framework detection, structure templates)
8. Phase 11: Prep phase for dual builds (boilerplate + fresh project support)
9. Phase 24: Cartographer prompt enhancement — ASCII wireframe sketches for all pages
10. Phase 25: Verifier prompt enhancement — sketch-aware testing + visual match report

RULES:
- Read the PRD section for each phase BEFORE building it
- Read existing source files to understand current patterns
- After EVERY phase: run 'cd ui && npm run build' — must pass with zero TypeScript errors
- Commit to main after each phase with a clear message
- Match existing patterns: neobrutalism design, Tailwind CSS v4, React 19, TanStack Query, Radix UI
- Do NOT skip phases. Do NOT restructure the page layout. Build exactly what the PRD describes.
- If you run out of context, commit what you have and leave a note about what's next.

When all 10 phases are done, commit with: 'Package 3 complete — live dashboard, terminal, boilerplate, architectural sketches done.'"

PACKAGE_4_PROMPT="You are the Verification Agent for the CLI Scripter v2 upgrade in AutoForge.

READ THE FULL PRD FIRST: $PRD_FILE — especially the 'Package 4: Post-Build Verification & Testing' section.

YOUR ASSIGNMENT: Package 4 — Full Post-Build Verification & Testing

IMPORTANT: Packages 1, 2, and 3 have already been built. ALL the code is in the codebase. You are NOT building anything new. You are TESTING everything that was built and FIXING bugs you find.

First, understand what was built. Run:
  git log --oneline -30
to see all commits from the 3 build packages.

Then follow the 8-phase verification protocol from the PRD:

Phase V1: INVESTIGATION
- Map the application: startup commands, routes, user journeys, key UI components
- Document DB schema and data flows
- Bug hunt via code analysis — look for logic errors, UI issues, data integrity risks, security concerns

Phase V2: STATIC VERIFICATION
- Run: cd ui && npm run lint && npm run build
- Run existing test suites
- Audit dependencies and imports for issues

Phase V3: FUNCTIONAL VERIFICATION
- Start the dev server, verify clean startup
- Test EVERY user journey end-to-end
- Validate database after data-modifying actions
- Test edge cases: empty states, invalid input, boundary values

Phase V4: CROSS-FEATURE INTEGRATION
- Test data flowing between features (Rules Library → Combiner → Gate → Scripts)
- Verify persistence survives reloads (localStorage + backend)
- Check for side effects between features

Phase V5: RESPONSIVE & VISUAL CHECK
- Test at Mobile (375×812), Tablet (768×1024), Desktop (1440×900)
- Look for overflow, overlapping elements, unreadable text

Phase V6: ISSUE HANDLING
- Fix critical and high issues immediately
- Document medium/low for follow-up
- Re-verify every fix

Phase V7: FINAL VERIFICATION PASS
- Re-run lint, type check, tests
- Restart dev server fresh
- Smoke test every feature

Phase V8: REPORT
- Output the structured Verification Report (see PRD for format)
- Include: features verified, issues found/fixed/remaining, static analysis results, visual match vs wireframes

RULES:
- Fix bugs as you find them — don't just document
- Commit fixes with clear messages (e.g., 'fix: correct Rules Library two-way binding')
- Zero console errors, zero unhandled warnings
- Be thorough — every feature should be exercised
- After all fixes: run 'cd ui && npm run build' one final time to confirm clean build

When done, commit with: 'Package 4 complete — full verification done. [X] issues found, [Y] fixed, [Z] remaining.'"

# ============================================================================
# Main Execution
# ============================================================================

log_header "CLI Scripter v2 — Multi-Package Build Runner"

echo -e "  Project:    ${BOLD}$PROJECT_DIR${NC}"
echo -e "  PRD:        ${BOLD}$PRD_FILE${NC}"
echo -e "  Model:      ${BOLD}$MODEL${NC}"
echo -e "  Logs:       ${BOLD}$LOG_DIR${NC}"
echo -e "  Start from: ${BOLD}Package $START_FROM${NC}"
if [ "$SINGLE_PACKAGE" -gt 0 ]; then
  echo -e "  Mode:       ${BOLD}Single package only (#$SINGLE_PACKAGE)${NC}"
fi
if [ "$DRY_RUN" = true ]; then
  echo -e "  Mode:       ${BOLD}DRY RUN (no execution)${NC}"
fi
echo ""

cd "$PROJECT_DIR"

# Verify PRD exists
if [ ! -f "$PRD_FILE" ]; then
  log_error "PRD not found: $PRD_FILE"
  exit 1
fi

# Verify claude CLI is available
if ! command -v claude &> /dev/null; then
  log_error "Claude CLI not found. Install it first: npm install -g @anthropic-ai/claude-code"
  exit 1
fi

# Array of packages
declare -a PACKAGE_PROMPTS=("$PACKAGE_1_PROMPT" "$PACKAGE_2_PROMPT" "$PACKAGE_3_PROMPT" "$PACKAGE_4_PROMPT")
declare -a PACKAGE_NAMES=("Foundation & UX Fixes" "Storage, Prompts & Display" "Dashboard, Terminal & Sketches" "Verification & Testing")
declare -a PACKAGE_MODELS=("$MODEL" "$MODEL" "$MODEL" "opus")  # Verification uses Opus

TOTAL_PACKAGES=4
if [ "$SINGLE_PACKAGE" -gt 0 ]; then
  TOTAL_PACKAGES=$SINGLE_PACKAGE
fi

for i in $(seq $START_FROM $TOTAL_PACKAGES); do
  idx=$((i - 1))
  pkg_model="${PACKAGE_MODELS[$idx]}"
  pkg_name="${PACKAGE_NAMES[$idx]}"
  pkg_prompt="${PACKAGE_PROMPTS[$idx]}"
  log_file="$LOG_DIR/package${i}_${TIMESTAMP}.log"

  log_header "PACKAGE $i of $TOTAL_PACKAGES: $pkg_name (model: $pkg_model)"

  if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}  [DRY RUN] Would execute:${NC}"
    echo -e "  claude -p --model $pkg_model --dangerously-skip-permissions"
    echo -e "  Prompt length: ${#pkg_prompt} chars"
    echo ""
    echo -e "  ${CYAN}First 500 chars of prompt:${NC}"
    echo "${pkg_prompt:0:500}"
    echo "..."
    echo ""
    continue
  fi

  # Run the Claude session
  log_step "Starting Claude session for Package $i..."
  echo ""

  START_TIME=$(date +%s)

  # Run claude with the package prompt
  claude -p --model "$pkg_model" --dangerously-skip-permissions <<PROMPT_EOF 2>&1 | tee "$log_file"
$pkg_prompt
PROMPT_EOF

  EXIT_CODE=$?
  END_TIME=$(date +%s)
  DURATION=$((END_TIME - START_TIME))
  MINUTES=$((DURATION / 60))
  SECONDS=$((DURATION % 60))

  echo ""
  if [ $EXIT_CODE -eq 0 ]; then
    log_success "Package $i completed in ${MINUTES}m ${SECONDS}s"
  else
    log_error "Package $i exited with code $EXIT_CODE after ${MINUTES}m ${SECONDS}s"
    log_error "Check log: $log_file"
  fi

  # Run verification
  echo ""
  if ! verify_build "$i"; then
    log_error "Build verification FAILED for Package $i"
    log_warn "Fix the build before continuing. Log: $log_file"
    exit 1
  fi

  # Pause between packages (unless it's the last one or single package mode)
  if [ "$i" -lt "$TOTAL_PACKAGES" ]; then
    pause_between_packages "$i" "$((i + 1))"
  fi
done

# Final summary
echo ""
log_header "BUILD COMPLETE"

if [ "$DRY_RUN" = true ]; then
  echo -e "  ${YELLOW}This was a dry run. No packages were executed.${NC}"
else
  echo -e "  ${GREEN}All packages completed successfully.${NC}"
  echo ""
  echo -e "  Logs saved to: $LOG_DIR"
  echo ""
  echo -e "  ${BOLD}Next steps:${NC}"
  echo -e "  1. Review the git log:  git log --oneline -30"
  echo -e "  2. Build for production: cd ui && npm run build"
  echo -e "  3. Push to remote:      git push origin main"
  echo -e "  4. Deploy to live:      cd C:\\Users\\lober\\Greptacular && git pull origin main --no-edit"
fi

echo ""
