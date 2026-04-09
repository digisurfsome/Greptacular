# Activepieces Flow Build Log: PRD Maker - Skill Chatbot

> **Permanent reference.** Covers exactly how the Skill Chatbot flow was built in Activepieces.
> A human can follow the step-by-step to rebuild manually. An agent can follow the MCP section
> to rebuild programmatically.

---

## 1. Flow Overview

| Field | Value |
|-------|-------|
| Flow Name | PRD Maker - Skill Chatbot (COPY - WIP) |
| Flow ID | `zepqUcFVu3CuUupNUDP3O` |
| Project ID | `zeXBGO1nhFOeOaVOfbuh3` |
| AP Instance | `http://localhost:8080` |
| Status | Wired up, needs testing |

### Purpose

Interactive skill chatbot that runs skills (SKILL.md files) via the Activepieces Chat UI.
Each chat message from the user flows through a Code step that calls AutoForge's subscription
proxy for Claude, then routes the response based on whether the skill is "complete" or still
needs more conversation turns.

### Architecture (Text Diagram)

```
+---------------------+
|   Chat UI Trigger   |  <-- User types a message in the AP Chat interface
|  (Human Input piece) |
+----------+----------+
           |
           v
+---------------------+
| Skill Chatbot Engine |  <-- Code step (ap-code-node.js)
|      (step_1)       |      Calls POST /api/pipeline-proxy/chat on AutoForge
+----------+----------+      Returns: assistant_message, is_complete, structured_output, ...
           |
           v
+---------------------+
|   Check Completion   |  <-- Router step (step_2)
|      (ROUTER)       |      Branches on step_1.is_complete
+----+------------+---+
     |            |
     v            v
 Branch 1      Otherwise
 (complete)    (continue)
     |            |
     v            v
+-----------+ +-----------+
| Respond   | | Respond   |
| on UI     | | on UI     |
| (step_3)  | | (step_4)  |
| Markdown: | | Markdown: |
| Stage     | | assistant |
| Complete  | | message   |
| header +  | |           |
| message   | |           |
+-----------+ +-----------+
```

### Data Flow

1. User types message in Chat UI.
2. Trigger fires with `chatMessage` (the text) and `chatId` (session identifier).
3. Code step builds a conversation context from AP's persistent store, calls AutoForge proxy.
4. AutoForge proxy loads SKILL.md from disk (by stage number), calls Claude via subscription auth.
5. Claude response comes back. Code step stores it in AP's persistent store, checks for `[STAGE_COMPLETE]`.
6. Router checks `is_complete`. If true, Branch 1 shows a "Stage Complete" header. Otherwise, regular response.
7. Both branches use "Respond on UI" (Human Input piece) to send markdown back to the Chat UI.

---

## 2. Human Rebuild Instructions

Step-by-step for rebuilding this flow from scratch in the Activepieces web UI.
No coding experience required -- just follow each step exactly.

### Prerequisites

- Activepieces running at `http://localhost:8080`
- AutoForge server running at `http://localhost:8888` (or `http://host.docker.internal:8888` from inside Docker)
- The file `activepieces-pieces/skill-chatbot/ap-code-node.js` open in a text editor (you will copy-paste from it)

### Step 1: Create the Flow

1. Open AP at `http://localhost:8080`.
2. Click **Flows** in the sidebar.
3. Click **+ New Flow** (top right).
4. A new flow opens with an empty trigger. The flow gets an auto-generated name.
5. Click the flow name at the top and rename it to: `PRD Maker - Skill Chatbot`

### Step 2: Set the Trigger to Chat UI

1. Click the trigger step (the first block in the flow).
2. In the piece selector, search for **Human Input** (or **Chat**).
3. Select the **Chat Submission** trigger (also labeled "Chat UI").
4. In the trigger settings panel on the right:
   - **Bot Name**: Type `PRD Gap Analysis`
   - Leave all other settings at defaults.
5. Click **Test Trigger** to generate sample data (you can type a test message).
   - This creates data references: `trigger.chatMessage` and `trigger.chatId`.

### Step 3: Add the Code Step

1. Click the **+** button below the trigger.
2. Select **Code** from the step type list (it is a built-in step type, not a piece).
3. Name the step: `Skill Chatbot Engine` (click the step name to rename).

### Step 4: Configure the Code Step Inputs

In the Code step settings panel, you need to add **9 input fields**. Click "Add Input" for each one.

| Input Name | Value | How to Set It |
|-----------|-------|---------------|
| `STAGE_NUMBER` | `2` | Type `2` directly. This tells AutoForge to load the Stage 2 (Gap Analysis) SKILL.md from disk. |
| `AUTOFORGE_URL` | `http://host.docker.internal:8888` | Type this directly. This is how Docker containers reach your local AutoForge server. |
| `USER_MESSAGE` | `{{trigger.chatMessage}}` | Click the **data reference icon** (the `{}` button or the "Insert Data" link). Navigate to **Trigger** and select **chatMessage**. |
| `SESSION_ID` | `{{trigger.chatId}}` | Click the **data reference icon**. Navigate to **Trigger** and select **chatId**. |
| `MODEL` | `claude-sonnet-4-6` | Type this directly. This is the subscription model name. |
| `COMPLETION_PATTERN` | `\\[STAGE_COMPLETE\\]` | Type this directly, including the double backslashes. This is the regex that detects when the skill signals it is done. |
| `RECENT_TURNS` | `4` | Type `4` directly. This controls how many recent conversation turns are sent to Claude (4 turns = 8 messages). |
| `SKILL_PROMPT` | *(leave empty)* | Do not type anything. When `STAGE_NUMBER` is set, the proxy loads the skill from disk automatically. |
| `CONTEXT_PACKET` | *(leave empty)* | Do not type anything. This is for chaining stages -- not needed for standalone use. |

### Step 5: Paste the Code

1. In the Code step settings, find the **Code Editor** section (below the inputs).
2. Delete any placeholder code that is already there.
3. Open the file `activepieces-pieces/skill-chatbot/ap-code-node.js` in a text editor.
4. Select ALL the code (Ctrl+A) and copy it (Ctrl+C).
5. Paste it into the AP Code Editor (Ctrl+V).
6. The step may show as "invalid" until you publish -- this is normal.

**Important:** The AP MCP tool `ap_update_step` cannot set source code on Code steps. If rebuilding programmatically, you must use AutoForge's `/api/ap-code/update-step` endpoint (see Section 3).

### Step 6: Add the Router Step

1. Click the **+** button below the Code step.
2. Select **Router** from the step type list (built-in, not a piece).
3. Name the step: `Check Completion`

### Step 7: Configure Router Branch 1 (Complete)

1. The Router starts with two branches: **Branch 1** and **Otherwise** (fallback).
2. Click **Branch 1** to configure it.
3. Add a condition:
   - **Left side**: Click the data reference icon. Navigate to **step_1** (the Code step) and select **is_complete**.
   - **Operator**: Select **TEXT_EXACTLY_MATCHES** (or "(Text) Exactly Matches").
   - **Right side**: Type `true` (lowercase, no quotes).
4. This branch fires when the skill signals it is done.

### Step 8: Add "Respond on UI" to Branch 1 (Complete Path)

1. Inside Branch 1 (the "complete" path), click the **+** button.
2. Search for **Human Input** piece.
3. Select the **Respond on UI** action (also labeled "Return Response" in some versions).
4. In the Markdown field, type:

```
## Stage Complete

{{step_1.assistant_message}}
```

Use the data reference icon to insert `{{step_1.assistant_message}}` -- navigate to **step_1** and select **assistant_message**.

### Step 9: Add "Respond on UI" to Otherwise Branch (Continue Path)

1. Inside the **Otherwise** branch (the fallback), click the **+** button.
2. Search for **Human Input** piece.
3. Select the **Respond on UI** action.
4. In the Markdown field, type:

```
{{step_1.assistant_message}}
```

Again use the data reference icon to insert the reference to step_1's assistant_message.

### Step 10: Publish the Flow

1. Click the **Publish** button (top right of the flow editor).
2. Wait for the confirmation message.
3. The flow is now live and accessible via the Chat URL.

### Step 11: Test the Flow

1. After publishing, click the **Chat** icon in the left sidebar (or find the Chat URL in the flow's trigger settings).
2. Open the Chat URL in your browser.
3. Type a test message like: "I want to build a project management tool"
4. You should see a response from the Gap Analysis skill within 10-30 seconds.
5. If nothing happens, check the Troubleshooting section (Section 5).

---

## 3. Agent Rebuild Instructions (MCP)

Exact MCP commands to rebuild this flow programmatically. Execute these in order.

All commands use the Activepieces MCP endpoint at `http://localhost:8080/mcp` with the project bearer token. See `docs/ACTIVEPIECES.md` for auth details and curl patterns.

### 3.1 Create the Flow

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "ap_create_flow",
    "arguments": {
      "displayName": "PRD Maker - Skill Chatbot"
    }
  },
  "id": 1
}
```

**Save the returned `flowId`** -- you need it for every subsequent call. It will look like `zepqUcFVu3CuUupNUDP3O`.

### 3.2 Set the Trigger (Chat UI)

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "ap_update_trigger",
    "arguments": {
      "flowId": "FLOW_ID",
      "pieceName": "@activepieces/piece-forms",
      "pieceVersion": "0.4.14",
      "triggerName": "chat_submission",
      "input": {
        "botName": "PRD Gap Analysis"
      }
    }
  },
  "id": 2
}
```

**Notes:**
- Replace `FLOW_ID` with the actual flow ID from step 3.1.
- The Chat UI trigger is part of the `@activepieces/piece-forms` piece.
- `pieceVersion` may change with AP updates. Use `ap_list_pieces` to find the current version if `0.4.14` fails.
- `chat_submission` is the trigger name for the Chat UI.

### 3.3 Add the Code Step

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "ap_add_step",
    "arguments": {
      "flowId": "FLOW_ID",
      "stepType": "CODE",
      "displayName": "Skill Chatbot Engine",
      "afterStepName": "trigger"
    }
  },
  "id": 3
}
```

This creates `step_1`. The step name is auto-assigned by AP.

### 3.4 Configure the Code Step Inputs

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "ap_update_step",
    "arguments": {
      "flowId": "FLOW_ID",
      "stepName": "step_1",
      "input": {
        "STAGE_NUMBER": "2",
        "AUTOFORGE_URL": "http://host.docker.internal:8888",
        "USER_MESSAGE": "{{trigger.chatMessage}}",
        "SESSION_ID": "{{trigger.chatId}}",
        "MODEL": "claude-sonnet-4-6",
        "COMPLETION_PATTERN": "\\[STAGE_COMPLETE\\]",
        "RECENT_TURNS": "4",
        "SKILL_PROMPT": "",
        "CONTEXT_PACKET": ""
      }
    }
  },
  "id": 4
}
```

**Important:** This sets the inputs but NOT the source code. See step 3.7.

### 3.5 Add the Router Step

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "ap_add_step",
    "arguments": {
      "flowId": "FLOW_ID",
      "stepType": "ROUTER",
      "displayName": "Check Completion",
      "afterStepName": "step_1"
    }
  },
  "id": 5
}
```

This creates `step_2` (the Router). AP auto-creates two branches: Branch 1 and Otherwise.

### 3.6 Configure Router Branch 1 Condition

Use `ap_update_step` to set the branch condition:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "ap_update_step",
    "arguments": {
      "flowId": "FLOW_ID",
      "stepName": "step_2",
      "input": {
        "branches": [
          {
            "branchName": "Complete",
            "branchType": "CONDITION",
            "conditions": [
              [
                {
                  "firstValue": "{{step_1.is_complete}}",
                  "operator": "TEXT_EXACTLY_MATCHES",
                  "secondValue": "true",
                  "caseSensitive": false
                }
              ]
            ]
          }
        ]
      }
    }
  },
  "id": 6
}
```

**Notes:**
- The `conditions` array is nested: outer array = OR groups, inner array = AND conditions within a group.
- This config has a single AND condition: `step_1.is_complete` exactly matches `"true"`.

### 3.7 Add "Respond on UI" to Branch 1 (Complete Path)

First, get the branch step names by calling `ap_flow_structure`:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "ap_flow_structure",
    "arguments": {
      "flowId": "FLOW_ID"
    }
  },
  "id": 7
}
```

The response will show the Router's branches and their insertable locations. Use those to add steps inside each branch.

Add Respond on UI to Branch 1:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "ap_add_step",
    "arguments": {
      "flowId": "FLOW_ID",
      "stepType": "PIECE",
      "displayName": "Stage Complete Response",
      "afterStepName": "step_2",
      "branchIndex": 0,
      "pieceName": "@activepieces/piece-forms",
      "pieceVersion": "0.4.14",
      "actionName": "return_response"
    }
  },
  "id": 8
}
```

Then configure it:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "ap_update_step",
    "arguments": {
      "flowId": "FLOW_ID",
      "stepName": "step_3",
      "input": {
        "markdown": "## Stage Complete\n\n{{step_1.assistant_message}}"
      }
    }
  },
  "id": 9
}
```

### 3.8 Add "Respond on UI" to Otherwise Branch (Continue Path)

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "ap_add_step",
    "arguments": {
      "flowId": "FLOW_ID",
      "stepType": "PIECE",
      "displayName": "Continue Response",
      "afterStepName": "step_2",
      "branchIndex": 1,
      "pieceName": "@activepieces/piece-forms",
      "pieceVersion": "0.4.14",
      "actionName": "return_response"
    }
  },
  "id": 10
}
```

Then configure it:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "ap_update_step",
    "arguments": {
      "flowId": "FLOW_ID",
      "stepName": "step_4",
      "input": {
        "markdown": "{{step_1.assistant_message}}"
      }
    }
  },
  "id": 11
}
```

### 3.9 Set Source Code on the Code Step

The MCP tool `ap_update_step` **cannot** set `sourceCode` on CODE steps (known AP MCP limitation). Use AutoForge's `/api/ap-code/update-step` endpoint instead.

```bash
curl -s -X POST "http://localhost:8888/api/ap-code/update-step" \
  -H "Content-Type: application/json" \
  -d '{
    "flow_id": "FLOW_ID",
    "step_name": "step_1",
    "source_code": "CONTENTS_OF_AP_CODE_NODE_JS"
  }'
```

**How to get the source code string:**
- Read the file `activepieces-pieces/skill-chatbot/ap-code-node.js`.
- Escape it for JSON (escape backslashes, quotes, newlines).
- Paste into the `source_code` field.

**What this endpoint does under the hood:**
1. Connects to AP's PostgreSQL database via `docker exec` + `psql`.
2. Finds the latest `flow_version` row for the given `flowId`.
3. Uses `jsonb_set` to write the code into `trigger.nextAction.settings.sourceCode.code`.
4. Sets `trigger.nextAction.valid` to `true` so AP treats the step as configured.

**API Reference:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `flow_id` | string | Yes | The AP flow ID |
| `step_name` | string | Yes | Step name (e.g., `step_1`). Determines JSONB path depth. |
| `source_code` | string | Yes | Full JavaScript source code to set on the Code step. |

**Response:**

```json
{
  "success": true,
  "flow_id": "FLOW_ID",
  "step_name": "step_1",
  "rows_affected": 1
}
```

**Companion endpoint -- read existing code:**

```bash
curl -s -X POST "http://localhost:8888/api/ap-code/get-step-code" \
  -H "Content-Type: application/json" \
  -d '{"flow_id": "FLOW_ID", "step_name": "step_1"}'
```

### 3.10 Publish the Flow

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "ap_lock_and_publish",
    "arguments": {
      "flowId": "FLOW_ID"
    }
  },
  "id": 12
}
```

After publishing, the Chat UI becomes accessible. Find the URL in the trigger settings or via the AP Chat sidebar.

---

## 4. All Parameters Reference

### 4.1 Trigger Parameters (Chat UI)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `botName` | string | Yes | *(none)* | Display name shown in the Chat UI. Without this, the trigger shows "Incomplete". |

**Trigger outputs** (available as data references in downstream steps):

| Output | Type | Description |
|--------|------|-------------|
| `chatMessage` | string | The user's message text |
| `chatId` | string | Unique session identifier for the chat. Persists across turns in the same chat session. |

### 4.2 Code Step Inputs (Skill Chatbot Engine)

| Input | Type | Required | Default | Valid Values | Description |
|-------|------|----------|---------|-------------|-------------|
| `STAGE_NUMBER` | string | No | `""` (empty) | `"0"` through `"10"` | Stage number. When set, the AutoForge proxy loads the corresponding SKILL.md from `docs/page-prds/prd-maker/skills-complete/stage-NN-*/SKILL.md`. When empty, falls back to `SKILL_PROMPT`. |
| `AUTOFORGE_URL` | string | No | `"http://host.docker.internal:8888"` | Any valid URL | AutoForge server base URL. Use `host.docker.internal` from Docker containers, `localhost` from the host machine. |
| `USER_MESSAGE` | string | Yes | `""` | Any text | The user's message. Wire to `{{trigger.chatMessage}}`. |
| `SESSION_ID` | string | No | `"default"` | Any string | Session identifier for conversation state in AP's persistent store. Wire to `{{trigger.chatId}}`. |
| `MODEL` | string | No | `"claude-sonnet-4-6"` | `"claude-sonnet-4-6"`, `"claude-opus-4-6"`, any valid Claude model ID | The Claude model to use via subscription auth. |
| `COMPLETION_PATTERN` | string | No | `"\\[STAGE_COMPLETE\\]"` | Any valid JavaScript regex string | Regex tested against assistant response. When matched, `is_complete` returns `true`. |
| `RECENT_TURNS` | string | No | `"4"` | Any positive integer as string | Number of recent conversation turns to include in the context window. `4` means 4 user turns + 4 assistant turns = 8 messages. |
| `SKILL_PROMPT` | string | No | `""` | Any text (full SKILL.md content) | Fallback system prompt when `STAGE_NUMBER` is empty. Ignored when `STAGE_NUMBER` is set. |
| `CONTEXT_PACKET` | string | No | `""` | JSON string | Structured output from a prior stage. When non-empty, prepended to the user message wrapped in `[CONTEXT]...[/CONTEXT]` tags. Used for chaining stages. |

### 4.3 Code Step Outputs

| Output | Type | Description |
|--------|------|-------------|
| `assistant_message` | string | Claude's full response text |
| `is_complete` | boolean | `true` if the assistant response matched the `COMPLETION_PATTERN` |
| `structured_output` | object or null | If `is_complete` is true and the response contains a ` ```json ``` ` block, this is the parsed JSON object. Otherwise `null`. |
| `turn_count` | number | Total number of user turns in this session |
| `session_id` | string | Echo of the `SESSION_ID` input |
| `model_used` | string | Echo of the `MODEL` input |
| `stage_number` | number or null | Parsed integer from `STAGE_NUMBER`, or `null` if not set |
| `duration_seconds` | number | Time taken for the Claude call (from the proxy response) |

### 4.4 Router Configuration

| Parameter | Value |
|-----------|-------|
| Step Name | `step_2` |
| Display Name | `Check Completion` |
| Branch Count | 2 (Branch 1 + Otherwise) |

**Branch 1 condition:**

| Field | Value |
|-------|-------|
| Left value | `{{step_1.is_complete}}` |
| Operator | `TEXT_EXACTLY_MATCHES` |
| Right value | `true` |
| Case sensitive | `false` |

**Otherwise:** No condition (catches everything that does not match Branch 1).

### 4.5 Respond on UI Parameters

**Branch 1 (Complete path) -- step_3:**

| Parameter | Value |
|-----------|-------|
| markdown | `## Stage Complete\n\n{{step_1.assistant_message}}` |

**Otherwise (Continue path) -- step_4:**

| Parameter | Value |
|-----------|-------|
| markdown | `{{step_1.assistant_message}}` |

### 4.6 AutoForge Proxy Endpoint

The Code step calls this endpoint:

```
POST {AUTOFORGE_URL}/api/pipeline-proxy/chat
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_message` | string | Yes | The assembled conversation context (recent turns + optional context packet) |
| `model` | string | No | Claude model ID (default: `claude-sonnet-4-6`) |
| `max_turns` | number | No | Max SDK turns (default: `2`) |
| `system_prompt` | string | No | Full system prompt text. Used when `stage_number` is not set, or as supplemental (conversation summary) when `stage_number` is set. |
| `stage_number` | number | No | When set, the proxy loads SKILL.md from `docs/page-prds/prd-maker/skills-complete/stage-NN-*/SKILL.md` and uses it as the system prompt. |

**Response body:**

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the call succeeded |
| `response_text` | string | Claude's response text |
| `model` | string | Model that was used |
| `duration_seconds` | number | Wall-clock time for the Claude call |
| `error` | string or null | Error message if `success` is `false` |

---

## 5. Troubleshooting

### CRITICAL: Docker Sandbox Blocks Code Node Execution

**Symptoms:** Chat says "No response from chatbot." Run logs show `ECONNREFUSED 127.0.0.1:8080`.
**Cause:** AP's code sandbox can't connect back to the AP engine inside Docker (port mismatch: engine on 80, sandbox looking for 8080).
**Fix:** Set `AP_EXECUTION_MODE=UNSANDBOXED` in Docker Compose environment. Restart container.
**Full details:** See `docs/ACTIVEPIECES.md` → FIX-001.

### CRITICAL: Code Node Must Use `export const code` Wrapper

**Symptoms:** `"Compilation error"` on the Code step. Step never executes.
**Cause:** AP compiles Code nodes as CommonJS. Top-level code and `await` crash the compiler.
**Fix:** ALL code must be inside `export const code = async ({inputs, store}) => { ... };`
**Full details:** See `docs/ACTIVEPIECES.md` → FIX-003.

### CRITICAL: AI Call Timeout

**Symptoms:** Code step runs but times out before Claude responds.
**Cause:** Default sandbox timeout is 30 seconds. Claude calls take 10-30 seconds.
**Fix:** Set `AP_CODE_SANDBOX_EXECUTION_TIMEOUT=120` in Docker Compose. Restart container.
**Full details:** See `docs/ACTIVEPIECES.md` → FIX-002.

### Trigger Shows "Incomplete"

**Cause:** The `botName` field is not set on the Chat UI trigger.
**Fix:** Open the trigger settings and set Bot Name to any non-empty string (e.g., `PRD Gap Analysis`).

### Code Step Shows "Invalid"

**Cause:** The source code was not set on the Code step. The MCP tool `ap_update_step` cannot set source code -- it only sets inputs.
**Fix:** Use AutoForge's `/api/ap-code/update-step` endpoint:
```bash
curl -s -X POST "http://localhost:8888/api/ap-code/update-step" \
  -H "Content-Type: application/json" \
  -d '{"flow_id": "YOUR_FLOW_ID", "step_name": "step_1", "source_code": "...code..."}'
```
Verify the endpoint is available by checking `GET http://localhost:8888/api/ap-code/health`.

### "AutoForge Proxy Error" or "fetch failed"

**Cause:** The AutoForge server is not running, or it is not reachable from Docker.
**Fixes:**
1. Verify AutoForge is running: `curl http://localhost:8888/api/pipeline-proxy/health`
2. From Docker, the URL must use `host.docker.internal` instead of `localhost`. Check that `AUTOFORGE_URL` is set to `http://host.docker.internal:8888`.
3. On Linux hosts, `host.docker.internal` may not resolve. Add `--add-host=host.docker.internal:host-gateway` to your Docker run command.

### Chat Not Responding (No Output After Sending Message)

**Cause:** The flow is not published.
**Fix:** Click "Publish" in the AP flow editor. Unpublished flows do not respond to the Chat UI trigger.

**Also check:**
- Is the flow enabled? (`ap_change_flow_status` to enable if disabled)
- Are there errors in the AP run history? (Click "Runs" in the sidebar to see recent executions)

### stage_number Not Loading the Skill

**Cause:** The SKILL.md file does not exist at the expected path.
**Expected path pattern:**
```
docs/page-prds/prd-maker/skills-complete/stage-{NN}-{name}/SKILL.md
```
Where `NN` is the zero-padded stage number (e.g., `00`, `01`, `02`).

**Stage folder names:**
| Stage | Folder |
|-------|--------|
| 0 | `stage-00-technical-foundation` |
| 1 | `stage-01-idea-capture` |
| 2 | `stage-02-gap-analysis` |
| 3 | `stage-03-agent-os-structuring` |
| 4 | `stage-04-mechanism-extraction` |
| 5 | `stage-05-seven-question-scaffolding` |

**Fix:** Verify the file exists on disk. The path is resolved relative to the project root (where `docs/` lives).

### Claude Returns Empty or Nonsensical Response

**Cause:** Usually a conversation state issue.
**Fixes:**
1. Start a new chat session (new Chat URL or different chatId) to reset state.
2. Check `RECENT_TURNS` -- if set too low, Claude loses context. Try `6` or `8`.
3. Check the AP persistent store: the conversation state is stored under key `skillchat_{SESSION_ID}`.

### Rate Limiting (429 Errors)

**Cause:** Claude subscription rate limits.
**Fix:** The AutoForge proxy has a generous timeout (300 seconds) that handles retries. If still failing:
1. Wait a few minutes.
2. Use a different model (e.g., `claude-sonnet-4-6` is less likely to rate-limit than Opus).
3. Reduce `RECENT_TURNS` to send less context per call.

### Router Branch Not Matching

**Cause:** The `is_complete` output is a boolean but the branch condition checks a string.
**Fix:** Ensure the branch condition uses `TEXT_EXACTLY_MATCHES` with value `true` (lowercase string). AP serializes boolean outputs as strings in conditions.

---

## 6. Modification Guide

### Change Which Skill Runs

Update the `STAGE_NUMBER` input on the Code step:
- **In the UI:** Open step_1 settings, change `STAGE_NUMBER` from `2` to the desired stage number.
- **Via MCP:**
  ```json
  {
    "method": "tools/call",
    "params": {
      "name": "ap_update_step",
      "arguments": {
        "flowId": "FLOW_ID",
        "stepName": "step_1",
        "input": { "STAGE_NUMBER": "3" }
      }
    }
  }
  ```
- Re-publish after changing.

### Use a Custom Skill (Not from Disk)

Instead of setting `STAGE_NUMBER`, leave it empty and paste the full SKILL.md content into the `SKILL_PROMPT` input:
- **In the UI:** Clear `STAGE_NUMBER`, paste your prompt into `SKILL_PROMPT`.
- **Via MCP:** Same as above but set `"STAGE_NUMBER": ""` and `"SKILL_PROMPT": "Your full system prompt here..."`.

### Change the Claude Model

Update the `MODEL` input:
- `claude-sonnet-4-6` -- fast, cheap, good for conversational stages
- `claude-opus-4-6` -- slower, more expensive, better for complex analysis
- Any valid Claude model ID works, as long as it is available via subscription auth.

### Add a New Stage (Chain After Completion)

To chain Stage 2 into Stage 3 when the user finishes:

1. In Branch 1 (the "complete" path), remove the existing Respond on UI step.
2. Add a new Code step after the Router's complete branch.
3. Configure it identically to step_1, but:
   - Set `STAGE_NUMBER` to `3`.
   - Set `CONTEXT_PACKET` to `{{step_1.structured_output}}` -- this passes the Stage 2 output as context for Stage 3.
4. Add a new Router after this Code step for Stage 3 completion.
5. Add Respond on UI steps in each of the new Router's branches.

**Architecture for chained stages:**

```
Trigger → Code (Stage 2) → Router
  Branch 1 (complete) → Code (Stage 3) → Router
    Branch 1 (complete) → Respond "All Done"
    Otherwise → Respond (Stage 3 message)
  Otherwise → Respond (Stage 2 message)
```

### Pass Context Between Stages

The `CONTEXT_PACKET` input accepts a JSON string. When the Code step's `is_complete` is `true`, it extracts any ` ```json ``` ` block from the assistant's response into `structured_output`.

To chain:
- Stage N's `structured_output` becomes Stage N+1's `CONTEXT_PACKET`.
- The Code step wraps it in `[CONTEXT]...[/CONTEXT]` tags and prepends it to the user message.
- The receiving skill's SKILL.md should contain instructions for how to use `[CONTEXT]` data.

### Change the Completion Pattern

Update `COMPLETION_PATTERN` on the Code step. Examples:
- `\\[STAGE_COMPLETE\\]` -- default, matches `[STAGE_COMPLETE]`
- `\\[DONE\\]` -- matches `[DONE]`
- `FINAL_ANSWER:` -- matches any line starting with `FINAL_ANSWER:`
- The value is passed to JavaScript's `new RegExp()`, so use JavaScript regex syntax with doubled backslashes for escaping.

### Change the Bot Name

Update the trigger's `botName` field:
- **In the UI:** Click the trigger, change Bot Name.
- **Via MCP:** Use `ap_update_trigger` with `"input": {"botName": "New Name Here"}`.
- Re-publish after changing.

### Adjust Conversation Memory

Change `RECENT_TURNS` to control how much history Claude sees each turn:
- `2` -- minimal memory (4 messages). Fast, cheap, but Claude forgets quickly.
- `4` -- moderate memory (8 messages). Good balance for most skills.
- `8` -- deep memory (16 messages). Slower, more expensive, but Claude retains more context.
- Beyond `8`, the conversation summary mechanism handles older turns automatically (older messages get summarized into a rolling summary block).

---

## Appendix: File Locations

| File | Path | What It Is |
|------|------|-----------|
| Code node source | `activepieces-pieces/skill-chatbot/ap-code-node.js` | The JavaScript pasted into the AP Code step |
| AP integration guide | `docs/ACTIVEPIECES.md` | MCP auth, tools, Docker commands, known limitations |
| AP Code Manager router | `server/routers/ap_code_manager.py` | AutoForge endpoint for reading/writing Code step source code |
| Pipeline Proxy router | `server/routers/pipeline_proxy.py` | AutoForge endpoint for proxying Claude calls (subscription auth) |
| Pipeline Chat router | `server/routers/pipeline_chat.py` | AutoForge endpoint for conversational pipeline stages 0-2 |
| Stage skills directory | `docs/page-prds/prd-maker/skills-complete/` | SKILL.md files loaded by stage number |
| This document | `docs/page-prds/prd-maker/ACTIVEPIECES_FLOW_BUILD_LOG.md` | You are reading it |
