#!/bin/bash
# Hook: Called by Claude Code after each tool use
# Sends event to CLI Dashboard server
#
# Configure in .claude/settings.json:
# {
#   "hooks": {
#     "afterToolUse": [{ "command": "/path/to/on_tool_use.sh" }]
#   }
# }

DASHBOARD_URL="${CLI_DASHBOARD_URL:-http://localhost:9111}"
SESSION_ID="${CLI_DASHBOARD_SESSION_ID:-unknown}"

# Tool info comes via environment or stdin
TOOL_NAME="${CLAUDE_TOOL_NAME:-$1}"

curl -s -X POST "${DASHBOARD_URL}/hook" \
  -H "Content-Type: application/json" \
  -d "{
    \"event_type\": \"tool_use\",
    \"session_id\": \"${SESSION_ID}\",
    \"tool_name\": \"${TOOL_NAME}\",
    \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
  }" > /dev/null 2>&1 &
