#!/usr/bin/env bash
# Feed a PRD file into the PRD Shredder
# Usage: bash scripts/shred-prd.sh docs/prd-token-budget-system.md
# Usage: bash scripts/shred-prd.sh docs/prd-tool-execution-engine.md /path/to/other/repo
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PRD_FILE="${1:?Usage: shred-prd.sh <prd-file> [target-repo]}"
TARGET_REPO="${2:-$REPO_ROOT}"

# Resolve relative paths
if [[ ! "$PRD_FILE" = /* ]]; then
  PRD_FILE="$REPO_ROOT/$PRD_FILE"
fi

if [ ! -f "$PRD_FILE" ]; then
  echo "ERROR: PRD file not found: $PRD_FILE"
  exit 1
fi

# Read the PRD content
PRD_CONTENT=$(cat "$PRD_FILE")
PRD_TITLE=$(head -1 "$PRD_FILE" | sed 's/^#\s*//')

echo "=== PRD Shredder ==="
echo "File: $PRD_FILE"
echo "Title: $PRD_TITLE"
echo "Target: $TARGET_REPO"
echo ""

# Escape the content for JSON (handle newlines, quotes, backslashes)
PRD_JSON=$(python -c "
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    content = f.read()
print(json.dumps({
    'prd_text': content,
    'target_repo': sys.argv[2],
    'title': sys.argv[3]
}))
" "$PRD_FILE" "$TARGET_REPO" "$PRD_TITLE")

# Send to the shredder
RESPONSE=$(curl -s -X POST http://localhost:8888/api/prd-shredder/enqueue \
  -H "Content-Type: application/json" \
  -d "$PRD_JSON")

echo "Response: $RESPONSE"
echo ""
echo "=== PRD Queued ==="
echo "Check status: curl http://localhost:8888/api/prd-shredder/queue"
echo "Watch logs:   curl http://localhost:8888/api/prd-shredder/status"
