# Activepieces Integration Guide

> **Read this before touching anything in Activepieces.**
> One-line reference from CLAUDE.md points here.

---

## Instance Info

| Item | Value |
|------|-------|
| URL | `http://localhost:8080` |
| Version | 0.81.0 (Community Edition) |
| Docker container | `modular-pipeline-builder-engine-1` |
| Database | PostgreSQL (`pipeline` user, `pipeline` db) |
| Redis | `modular-pipeline-builder-redis-1` |
| User | Tim Garner (`dux8bevo@gmail.com`) |
| Project ID | `zeXBGO1nhFOeOaVOfbuh3` |
| MCP Endpoint | `http://localhost:8080/mcp` |

---

## Auth Model — SUBSCRIPTION ONLY

**Until we build the SaaS version, ALL AI calls route through AutoForge's subscription model.**

- Do NOT configure Anthropic API keys directly in AP
- Do NOT use AP's built-in AI provider settings for Claude
- Every AI call goes: AP node → AutoForge server endpoint → Claude SDK (subscription auth)
- The AutoForge server handles subscription routing via `pipeline_proxy.py` / `pipeline_chat.py`

**When we build SaaS:** Then users bring their own API keys. That's a future concern.

---

## MCP Connection

### How It Works

AP exposes a JSON-RPC over SSE endpoint at `http://localhost:8080/mcp`. The bearer token is generated inside AP under: **Project Settings → MCP Server → Connection tab**.

### The Bearer Token (MCP-only, NOT REST API)

The MCP bearer token is a **project-scoped token** — it authenticates against the `/mcp` endpoint ONLY. It does NOT work for AP's general REST API (`/api/v1/*`). The REST API requires either:
- A paid API Key (locked in Community Edition)
- A session JWT from `POST /api/v1/authentication/sign-in` (expires)

For everything we do, **use the MCP endpoint, not the REST API.**

### Current Token

```
Bearer 4ofcu1CSmBzTBmZXEBmxVUl75zdT8gS26DvSY9aTIYO6MhYbohoLG13LGrEkB1EDLuLdUIdk
```

If this expires: AP → Project Settings → MCP Server → click the refresh icon (🔄) next to "Bearer Token" → copy new token → update `mcp.json` and this file.

### mcp.json Config (`C:\Users\lober\.claude\mcp.json`)

```json
{
  "mcpServers": {
    "activepieces": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:8080/mcp", "--header", "Authorization: Bearer 4ofcu1CSmBzTBmZXEBmxVUl75zdT8gS26DvSY9aTIYO6MhYbohoLG13LGrEkB1EDLuLdUIdk"]
    }
  }
}
```

**Known issue:** `mcp-remote` sometimes fails to bridge into Claude Code sessions (npm/npx cache or startup timing). When that happens, the 28 MCP tools don't load. **Workaround:** Call the MCP endpoint directly via curl (see below).

### Direct MCP Calls via curl (When Bridge Fails)

Every MCP tool can be called directly:

```bash
curl -s -X POST "http://localhost:8080/mcp" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"TOOL_NAME","arguments":{...}},"id":1}'
```

**Critical headers:**
- `Content-Type: application/json` — required
- `Accept: application/json, text/event-stream` — MUST include BOTH. Without `text/event-stream`, the endpoint returns a "Not Acceptable" error.
- `Authorization: Bearer TOKEN` — the MCP bearer token from AP settings

**Response format:** SSE with `event: message` prefix, then `data: {JSON-RPC response}`.

### Available MCP Tools (28 total)

| Tool | What It Does |
|------|-------------|
| `ap_list_flows` | List all flows in the project |
| `ap_create_flow` | Create a new empty flow |
| `ap_rename_flow` | Rename a flow |
| `ap_flow_structure` | Get step tree, config status, valid insert locations |
| `ap_list_pieces` | List available pieces (280+), with actions/triggers |
| `ap_list_connections` | List OAuth/app connections |
| `ap_update_trigger` | Set/update a flow's trigger |
| `ap_add_step` | Add a new step (CODE, PIECE, LOOP, ROUTER) |
| `ap_update_step` | Configure a step's inputs, action, auth |
| `ap_delete_step` | Remove a step |
| `ap_add_branch` | Add a branch to a ROUTER step |
| `ap_delete_branch` | Remove a branch from a ROUTER |
| `ap_lock_and_publish` | Publish and enable a flow |
| `ap_change_flow_status` | Enable/disable a published flow |
| `ap_manage_notes` | Add/edit/delete canvas notes |
| `ap_list_ai_models` | List configured AI providers |
| `ap_list_tables` | List project tables |
| `ap_find_records` | Query table records |
| `ap_create_table` | Create a new table |
| `ap_delete_table` | Delete a table |
| `ap_manage_fields` | Add/rename/delete table fields |
| `ap_insert_records` | Insert records into a table |
| `ap_update_record` | Update a record |
| `ap_delete_records` | Delete records |
| `ap_list_runs` | List flow run history |
| `ap_get_run` | Get detailed run results |
| `ap_test_flow` | Test a flow end-to-end |
| `ap_test_step` | Test a single step |
| `ap_retry_run` | Retry a failed run |
| `ap_setup_guide` | Get setup instructions for connections |

---

## Existing Flows

| Flow | ID | Purpose | Status |
|------|----|---------|--------|
| PRD Maker - 11 Stage Pipeline | `qmWm4lyxgWnZZDVY1ikNt` | **SOURCE OF TRUTH.** Original 11-stage pipeline. DO NOT MODIFY. | Configured |
| PRD Maker - Skill Chatbot (COPY - WIP) | `zepqUcFVu3CuUupNUDP3O` | Working copy: Chat UI → Skill Chatbot Engine (Code) → Router → Respond on UI. Calls AutoForge proxy for subscription Claude. | Wired up, needs testing |

**Rule:** Always create a copy before experimenting. Never modify the original pipeline.

---

## Docker Commands

```bash
# Check if AP is running
docker ps | grep activepieces

# View AP logs
docker logs modular-pipeline-builder-engine-1 --tail 50

# Restart AP
docker restart modular-pipeline-builder-engine-1

# Get container env vars (JWT secret, encryption key, etc.)
docker inspect modular-pipeline-builder-engine-1 --format '{{range .Config.Env}}{{println .}}{{end}}'
```

### Database Direct Access

```bash
# Query the AP database
docker exec modular-pipeline-builder-postgres-1 psql -U pipeline -d pipeline -c "YOUR SQL HERE"

# Useful queries:
# List users:    SELECT id, email, "firstName" FROM user_identity;
# List projects: SELECT id FROM project;
# List flows:    SELECT id, "projectId" FROM flow;
```

---

## MCP Known Limitations

1. **`ap_update_step` cannot set `sourceCode` on CODE steps.** The MCP tool schema lacks a `sourceCode` parameter. To set code on a Code action node, you must update the database directly:
   ```bash
   docker exec modular-pipeline-builder-postgres-1 psql -U pipeline -d pipeline -c "
     UPDATE flow_version SET trigger = jsonb_set(trigger, '{nextAction,settings,sourceCode,code}', '\"YOUR_ESCAPED_CODE\"'::jsonb)
     WHERE \"flowId\" = 'YOUR_FLOW_ID' AND id = (SELECT MAX(id) FROM flow_version WHERE \"flowId\" = 'YOUR_FLOW_ID');
   "
   ```
   Path varies depending on step depth: `{nextAction,settings,...}` for step_1, `{nextAction,nextAction,settings,...}` for step_2, etc.

2. **Chat UI trigger may show "invalid" until first test run.** This is normal — the trigger validates when you test the flow for the first time via the AP UI or `ap_test_flow`.

3. **`mcp-remote` bridge unreliable in Claude Code sessions.** The npm bridge (`npx -y mcp-remote`) sometimes fails to start. Workaround: call MCP endpoint directly via curl (see curl patterns above).

---

## Solved Problems — Real World Fixes

> **Tags:** Each fix is tagged so agents can ctrl+F for the right one.
> These are problems we actually hit and solved. Not theoretical.

---

### FIX-001: Docker Sandbox ECONNREFUSED (Tags: chatbot, docker, sandbox, code-node, ECONNREFUSED)

**What happened:** The AP Chat UI said "No response from chatbot." Flow runs showed the Code node failing with `ECONNREFUSED 127.0.0.1:8080`.

**Root cause:** AP runs Code steps in an isolated sandbox process inside the Docker container. The sandbox tries to phone home to the AP engine. The engine listens on port **80** inside the container (mapped to 8080 on the host). But `AP_FRONTEND_URL` was set to `http://localhost:8080` — telling the sandbox to connect to port 8080 inside the container, which doesn't exist.

**The fix:** Set `AP_EXECUTION_MODE=UNSANDBOXED` in the Docker environment. This runs Code steps directly in the engine process instead of a separate sandbox. No more network connectivity issue.

**Where to apply:** In the Docker Compose file at `C:\Users\lober\modular-pipeline-builder\docker-compose.yml`, under the engine service's `environment:` section:
```yaml
AP_EXECUTION_MODE: UNSANDBOXED
```

**After changing:** Run `docker restart modular-pipeline-builder-engine-1` to apply.

**Tradeoff:** Unsandboxed mode means Code steps run in the same process as the AP engine. If a Code step crashes, it could theoretically affect the engine. For our use case (single user, controlled code), this is fine. For a multi-tenant SaaS, you'd want to fix the sandbox networking properly instead.

---

### FIX-002: Code Node Timeout — AI Calls Too Slow (Tags: chatbot, timeout, sandbox, code-node)

**What happened:** Code node timed out before the Claude API call could complete.

**Root cause:** Default `AP_SANDBOX_RUN_TIME_SECONDS=30`. Claude calls through AutoForge's subscription proxy take 10-30 seconds depending on prompt size and model. The 30-second limit was too tight.

**The fix:** Set `AP_CODE_SANDBOX_EXECUTION_TIMEOUT=120` in Docker environment:
```yaml
AP_CODE_SANDBOX_EXECUTION_TIMEOUT: 120
```

**After changing:** Restart the AP container.

---

### FIX-003: Code Node Compilation Error (Tags: chatbot, code-node, compilation, export, CommonJS)

**What happened:** Flow run showed `"Compilation error"` on the Code step. The step never executed — it failed before running any code.

**Root cause:** AP compiles Code steps as **CommonJS (cjs) modules**. AP expects ALL code to be wrapped inside:
```javascript
export const code = async ({inputs, store}) => {
  // your code here
  return { output_field: value };
};
```

The original code used **top-level `await`** and raw procedural code outside any function. AP's compiler choked on this.

**The fix:** Wrap ALL code inside the `export const code = async ({inputs, store}) => { ... }` function. No top-level code allowed. No top-level `await` allowed. Everything goes inside the exported function.

**Correct format:**
```javascript
export const code = async ({inputs, store}) => {
  const response = await fetch('...');
  const data = await response.json();
  return { result: data };
};
```

**Wrong format (will crash):**
```javascript
const response = await fetch('...');  // ← top-level await = CRASH
const data = await response.json();
return { result: data };
```

**For agents writing AP Code nodes:** ALWAYS use the `export const code` wrapper. This is non-negotiable. The MCP tool `ap_update_step` cannot set source code (see FIX-005), so code goes through the database. But the FORMAT must be correct or AP won't compile it.

---

### FIX-004: Skill File Too Large — 82KB vs 17KB (Tags: chatbot, skill, SKILL.md, file-size, proxy)

**What happened:** Claude responded with a generic greeting ("Hi, I'm PRD...") instead of following the gap analysis skill. Then the second message timed out.

**Root cause:** The proxy was loading from `skills-complete/` directory (82KB files with ALL reference material embedded). The 82KB system prompt overwhelmed Claude — it gave a generic response because the prompt was too large and unfocused.

**The fix:** Changed `pipeline_chat.py` to load from `skills/` directory (17KB base versions) instead of `skills-complete/`. The base versions have the core behavior instructions without bloating reference tables.

**File changed:** `server/routers/pipeline_chat.py` — the `SKILLS_DIR` variable:
```python
# WRONG — bloated versions
SKILLS_DIR = Path(__file__).parent.parent.parent / "docs" / "page-prds" / "prd-maker" / "skills-complete"

# RIGHT — focused base versions
SKILLS_DIR = Path(__file__).parent.parent.parent / "docs" / "page-prds" / "prd-maker" / "skills"
```

**Important:** This fix needs to be applied on BOTH the dev repo AND the live install (`C:\Users\lober\Greptacular\server\routers\pipeline_chat.py`). They're separate copies.

---

### FIX-005: MCP Cannot Set Source Code on Code Steps (Tags: code-node, MCP, ap_update_step, database, permanent)

**What happened:** Used `ap_update_step` to configure a Code node. The inputs (STAGE_NUMBER, AUTOFORGE_URL, etc.) were set correctly. But the actual JavaScript source code was NOT set — the tool has no parameter for it.

**Root cause:** AP's MCP schema for `ap_update_step` lacks a `sourceCode` field. This is an AP design gap — the tool was built for configuring Piece steps (where you set input fields), not Code steps (where you write JavaScript).

**The fix (immediate):** Update the database directly:
```bash
docker exec modular-pipeline-builder-postgres-1 psql -U pipeline -d pipeline -c "
  UPDATE flow_version 
  SET trigger = jsonb_set(
    trigger, 
    '{nextAction,settings,sourceCode,code}', 
    '\"YOUR_ESCAPED_CODE\"'::jsonb
  )
  WHERE \"flowId\" = 'YOUR_FLOW_ID' 
  AND id = (SELECT MAX(id) FROM flow_version WHERE \"flowId\" = 'YOUR_FLOW_ID');
"
```

**The fix (permanent):** AutoForge has a custom endpoint at `/api/ap-code/update-step` that handles the database update cleanly. Agents call this instead of fighting with MCP:
```bash
POST http://localhost:8888/api/ap-code/update-step
{
  "flow_id": "FLOW_ID",
  "step_name": "step_1",
  "source_code": "export const code = async ({inputs, store}) => { ... };"
}
```

**For the future vision (agent building flows in real-time):** The agent uses MCP for everything EXCEPT source code on Code steps. For that one thing, it calls the AutoForge endpoint. Full coverage, no handicap.

---

### FIX-006: Chat UI Trigger Shows "Incomplete" (Tags: chatbot, trigger, incomplete, botName)

**What happened:** Couldn't publish the flow. The trigger showed "Incomplete" status. Publish button was blocked.

**Root cause:** The `botName` field on the Chat UI trigger was empty. It's a required field (marked with asterisk *).

**The fix:** Set `botName` to any non-empty string via MCP:
```json
{
  "method": "tools/call",
  "params": {
    "name": "ap_update_trigger",
    "arguments": {
      "flowId": "FLOW_ID",
      "pieceName": "@activepieces/piece-forms",
      "pieceVersion": "0.4.14",
      "triggerName": "chat_submission",
      "input": { "botName": "PRD Gap Analysis" }
    }
  }
}
```

**Or in the UI:** Click the trigger → fill in "Bot Name" field → save.

---

### FIX-007: Dev Repo vs Live Install — Different Folders (Tags: deployment, dev-repo, live-install, paths)

**What happened:** Made a code fix in the dev repo. The fix didn't take effect because AutoForge was running from the live install (a different folder).

**Root cause:** Two separate copies of the codebase exist:
- **Dev repo:** `C:\Users\lober\GitHub\Greptacular - AutoForge Build\Greptacular` — where Claude Code edits
- **Live install:** `C:\Users\lober\Greptacular` — where AutoForge actually runs (port 8888)

Changes to one do NOT automatically appear in the other.

**The fix:** When making urgent fixes that need to work immediately:
1. Edit the file directly on the **live install** path
2. Later, sync back to dev repo via git push/pull

**The proper deploy chain:**
1. Edit in dev repo
2. `git push origin main`
3. `cd C:\Users\lober\Greptacular && git pull origin main --no-edit`
4. Restart AutoForge

**For agents:** If the user says "it's not working" after you made a code change, check WHICH copy you edited. If you edited the workspace repo (`~/.autoforge/workspace/repos/...`), that's a THIRD copy that's neither the dev repo nor the live install.

---

## Custom Piece Development

Custom pieces are TypeScript npm packages. See `activepieces-pieces/skill-chatbot/` for the Skill Chatbot piece code.

**Quick path (Code node):** Paste TypeScript directly into AP's Code action node — no build needed.
**Full piece path:** Build via AP CLI → `ap publish` → appears in piece list.

See `activepieces-pieces/skill-chatbot/DEPLOY.md` for full instructions.

---

## Key Architectural Decisions

1. **AP is the pipeline engine.** It orchestrates flows. It does NOT run AI directly.
2. **AutoForge is the AI brain.** All Claude calls route through AutoForge's subscription model.
3. **AP nodes are small, isolated, replaceable.** One bad node doesn't break the pipeline.
4. **The Skill Chatbot pattern:** Plug a SKILL.md into a node's brain → get a focused chatbot. Chain these with deterministic nodes.
5. **File-based conversation:** Store conversation history in AP's persistent store (free). Only send minimal data to Claude per turn.
