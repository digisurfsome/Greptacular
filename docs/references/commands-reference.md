# Commands Reference

## npm Global Install (Recommended)

```bash
npm install -g autoforge-ai
autoforge                    # Start server (first run sets up Python venv)
autoforge config             # Edit ~/.autoforge/.env in $EDITOR
autoforge config --show      # Print active configuration
autoforge --port 9999        # Custom port
autoforge --no-browser       # Don't auto-open browser
autoforge --repair           # Delete and recreate ~/.autoforge/venv/
```

## From Source (Development)

```bash
start_ui.bat      # Windows — Launch Web UI
./start_ui.sh     # macOS/Linux
start.bat         # Windows — CLI menu
./start.sh        # macOS/Linux
```

## Python Backend (Manual)

```bash
python -m venv venv
venv\Scripts\activate                    # Windows
source venv/bin/activate                 # macOS/Linux
pip install -r requirements.txt
python start.py                          # CLI launcher

# Run agent
python autonomous_agent_demo.py --project-dir C:/Projects/my-app
python autonomous_agent_demo.py --project-dir my-app   # registered name
python autonomous_agent_demo.py --project-dir my-app --yolo           # skip testing
python autonomous_agent_demo.py --project-dir my-app --parallel --max-concurrency 3
python autonomous_agent_demo.py --project-dir my-app --batch-size 3
python autonomous_agent_demo.py --project-dir my-app --batch-features 1,2,3
```

## YOLO Mode

Skips all testing for faster iteration. Lint/type-check still runs.
- CLI: `--yolo` flag
- UI: Toggle the lightning bolt button

## React UI

```bash
cd ui
npm install
npm run dev      # Dev server (hot reload)
npm run build    # Production build (required for start_ui.bat)
npm run lint     # ESLint
```

## Claude Code Integration

**Slash commands** (`.claude/commands/`): `/create-spec`, `/expand-project`, `/gsd-to-autoforge-spec`, `/check-code`, `/checkpoint`, `/review-pr`

**Custom agents** (`.claude/agents/`): `coder.md` (Opus), `code-review.md` (Opus), `deep-dive.md` (Opus)

**Skills** (`.claude/skills/`): `frontend-design`, `gsd-to-autoforge-spec`
