# AI Provider Configuration

## Subscription Auth (Claude — Default)

**Full guide with code examples:** `docs/SUBSCRIPTION_AND_WEBSOCKET_GUIDE.md` — READ THAT FIRST.

Quick summary: ALL Claude models use subscription (`force_subscription=True`). Never use API keys. `get_effective_sdk_env()` in `registry.py` is the single source of truth.

## Vertex AI (Optional)

```bash
gcloud auth application-default login
```

`.env` config:
```
CLAUDE_CODE_USE_VERTEX=1
CLOUD_ML_REGION=us-east5
ANTHROPIC_VERTEX_PROJECT_ID=your-gcp-project-id
ANTHROPIC_DEFAULT_OPUS_MODEL=claude-opus-4-6
ANTHROPIC_DEFAULT_SONNET_MODEL=claude-sonnet-4-6
ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-3-5-haiku@20241022
```

Note: Use `@` instead of `-` in model names for Vertex AI.

## Alternative Providers (GLM, Ollama, Kimi, Custom)

Configured via Settings UI (gear icon > API Provider). No `.env` changes needed.

**Ollama:** Requires v0.14.0+. `ollama serve` → `ollama pull qwen3-coder`. GPU recommended.
