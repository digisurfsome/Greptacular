# Mission Control

Connects [Plane](https://plane.so) (project management) to Claude AI agents.

When you assign an issue to AI in Plane, Mission Control picks it up, sends it to Claude, and posts the results back. No API keys needed — it uses your Claude subscription.

## How It Works

1. Plane sends a webhook when an issue is assigned to AI
2. Mission Control receives it and calls Claude via the SDK
3. Claude does the work and returns results
4. Mission Control posts the results back to Plane

## Quick Start

```bash
# 1. Clone this repo
git clone https://github.com/digisurfsome/Mission-Control.git
cd Mission-Control

# 2. Make sure you're logged into Claude
claude login

# 3. Set up Python environment
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
pip install -r requirements.txt

# 4. Copy the example env file
cp .env.example .env

# 5. Run the bridge (once it's built)
python plane_bridge.py
```

## Auth

This project uses **subscription auth** (not API keys). Your Claude subscription covers all usage. The SDK wrapper automatically clears any API keys and falls back to your subscription credentials in `~/.claude/.credentials.json`.

Just make sure you've run `claude login` once.

## Files

| File | What it does |
|------|-------------|
| `sdk_wrapper.py` | Core SDK wrapper — call Claude with subscription auth |
| `plane_bridge.py` | Webhook listener that connects Plane to Claude (placeholder) |
| `docker-compose.plane.yml` | Plane self-hosted setup (placeholder) |
