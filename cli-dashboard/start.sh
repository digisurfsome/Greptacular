#!/bin/bash
# CLI Dashboard Launcher
# Starts the dashboard server and opens the browser

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT="${DASHBOARD_PORT:-9111}"

echo ""
echo "  ╔═══════════════════════════════════════╗"
echo "  ║         CLI Dashboard v0.1            ║"
echo "  ║     Zero SDK / Pure Claude Code       ║"
echo "  ╚═══════════════════════════════════════╝"
echo ""
echo "  Server: http://localhost:${PORT}"
echo "  Press Ctrl+C to stop"
echo ""

# Check for dependencies
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "  Installing dependencies..."
    pip install fastapi uvicorn 2>/dev/null || pip3 install fastapi uvicorn
fi

# Start server
cd "$SCRIPT_DIR"
python3 server.py
