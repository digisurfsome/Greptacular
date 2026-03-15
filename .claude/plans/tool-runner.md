# Tool Runner — Agent-Powered Tool Execution

## What We're Building

A page inside AutoForge where any generated tool becomes a conversational agent. You talk to it like a consultant. It fills in variables, runs all steps, delivers output. Every tool gets the same agent engine — the blueprint is the playbook.

**The agent NEVER mentions AutoForge, Tool Factory, or how it was built.** It IS the tool.

## Architecture (Reuse Existing Patterns)

We already have a working chat system (WorkspaceChat). The Tool Runner is a **specialized workspace conversation** with the tool's blueprint injected as context.

### What Already Exists (reuse, don't rebuild)
- `useWorkspaceChat.ts` — WebSocket chat hook (messages, streaming, token tracking)
- `workspace.py` router — WebSocket handler, session management, background sessions
- `workspace_chat_session.py` — Backend agent session with SDK client
- `workspace_database.py` — Conversation persistence (SQLite)
- Tool registry with full blueprints (chain_config, user_input_variables)

### What We Build New

**Frontend (2 files):**

1. **`ui/src/pages/ToolRunnerPage.tsx`** — Main page
   - Route: `/#/tool-runner/:toolId`
   - Layout: Chat area (left/center) + Tool sidebar (right)
   - Chat area: reuse `useWorkspaceChat` hook, same message rendering
   - Sidebar: tool name, description, variable checklist (filled/unfilled), step progress
   - On load: fetch tool blueprint, create workspace conversation with tool context injected
   - Clean SaaS look — no AutoForge branding visible

2. **`ui/src/components/tool-runner/ToolRunnerSidebar.tsx`** — Right sidebar
   - Tool name + description at top
   - Variables section: checkboxes showing which are filled (extracted from chat)
   - Steps section: 1-10 with status (pending/running/done)
   - Output section: collapsible per-step results
   - "Export" button (copy all outputs / download)

**Backend (1 file + 1 router addition):**

3. **`server/services/tool_runner_session.py`** — Specialized session
   - Extends or wraps WorkspaceChatSession
   - Injects tool-specific system prompt with:
     - Tool name, description
     - Full chain_config (all 10 steps with prompts)
     - user_input_variables list
     - Instructions: "You are a [tool_name] consultant. Help the user fill in variables and execute each step."
     - Rule: never mention AutoForge, Tool Factory, or how tool was generated
     - Rule: offer to build more tools ("I can create similar tools for other workflows")
   - Tracks which variables have been collected
   - Tracks which steps have been executed

4. **Router additions to `server/routers/tool_factory.py`:**
   - `GET /api/tool-factory/{tool_id}/runner-context` — returns system prompt + blueprint for frontend
   - The actual chat goes through existing `/api/workspace/ws` with the tool context injected

### How It Works (User Flow)

1. User clicks "Run" on any tool → navigates to `/#/tool-runner/{toolId}`
2. Page loads tool blueprint, creates a workspace conversation
3. System prompt tells agent: "You are the ListicleForge consultant. Here are 10 steps and 28 variables."
4. User types: "I run an HVAC business in Chicago, website is hvacchicago.com"
5. Agent: "Got it! Let me research your business..." [uses WebFetch to study the site]
6. Agent fills in variables from conversation, confirms with user
7. Agent runs each step: generates content following the blueprint's prompt templates
8. Sidebar updates: variables check off, steps go green
9. User can say "Step 7 is too formal, make it punchier" → agent re-runs just that step
10. All outputs saved to conversation history

### System Prompt Template

```
You are {{tool_name}}, a specialized AI consultant.

{{tool_description}}

## Your Capabilities
You help users execute this {{step_count}}-step process by collecting their information and generating high-quality output for each step.

## Required Information (Variables)
{{#each user_input_variables}}
- {{this}}: [not yet collected]
{{/each}}

## Process Steps
{{#each chain_config}}
### Step {{row_number}}: {{step_type}}
Prompt: {{prompt_template}}
Expected Output: {{expected_output}}
{{/each}}

## Rules
- You are a domain expert consultant. Be conversational and helpful.
- Collect variables naturally through conversation — don't present a form.
- When you have enough info, offer to run the steps.
- Execute steps one at a time, showing output for each.
- If the user wants changes, re-run just that step.
- You can research websites and businesses to fill in variables.
- NEVER mention how you were created, AutoForge, Tool Factory, or any internal systems.
- When appropriate, mention you can create similar tools for other workflows.
```

## Build Order

1. Backend: `tool_runner_session.py` + router endpoint (~30 min)
2. Frontend: `ToolRunnerPage.tsx` with chat + sidebar (~60 min)
3. Wire up: route, navigation from tool detail, conversation creation (~15 min)
4. Test with ListicleForge tool (~15 min)

## What This Enables (Future Layers)

- **Layer 2 — Research Agent**: Agent already has WebFetch. Just needs prompt guidance to auto-research.
- **Layer 3 — Batch Mode**: Queue of inputs, agent runs tool N times. Add batch endpoint.
- **The Revolver**: Tool selector in sidebar. Switch tools mid-conversation. Agent adapts.
- **Multi-Agent**: Spin up N agents, each with a tool, each processing a queue item.
