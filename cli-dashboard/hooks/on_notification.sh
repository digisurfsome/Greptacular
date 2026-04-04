#!/bin/bash
# Hook: Called by Claude Code on notifications
# Sends event to CLI Dashboard server

DASHBOARD_URL="${CLI_DASHBOARD_URL:-http://localhost:9111}"
SESSION_ID="${CLI_DASHBOARD_SESSION_ID:-unknown}"

MESSAGE="${1:-notification}"

curl -s -X POST "${DASHBOARD_URL}/hook" \
  -H "Content-Type: application/json" \
  -d "{
    \"event_type\": \"notification\",
    \"session_id\": \"${SESSION_ID}\",
    \"message\": \"${MESSAGE}\",
    \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
  }" > /dev/null 2>&1 &
