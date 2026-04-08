# Spec 008 — MCP Integration + Skills Layer

## What This Is
Two things working together:

1. **Activepieces MCP Server** — Every Activepieces piece (280+) is exposed as an MCP tool that any AI agent can call directly. Install once, Claude can call Gmail/Slack/YouTube/Notion/etc. as native tool calls.

2. **Skills Layer** — Pre-built Claude skills per node category (YouTube, Gmail, LLM ops, etc.) that pull live docs from Context7 and handle the most common automation patterns. Skills are the "expert prompts" — they know the exact Activepieces piece schemas and patterns for their category.

## Why It Matters
The MCP server is what makes this AI-native. Claude doesn't just describe what to do — it can directly execute actions: send an email, post to Slack, fetch a YouTube video, query a database. The skills layer adds category expertise so Claude doesn't have to discover piece schemas from scratch every time.

Together: Claude knows what tools exist (MCP) + knows exactly how to use them (skills) + can build pipelines that combine them (AI co-pilot). That's the complete AI-native automation stack.

---

## Part 1: Activepieces MCP Server Setup

### Installation
```bash
# Install Activepieces CLI (also installs MCP server)
npm install -g @activepieces/cli

# Or run directly without installing:
npx -y @activepieces/cli
```

### Connect to Claude Desktop
Add to `~/.claude/mcp.json` (or `~/.cursor/mcp.json` for Cursor):
```json
{
  "mcpServers": {
    "activepieces": {
      "command": "npx",
      "args": ["-y", "@activepieces/cli"],
      "env": {
        "AP_API_KEY": "your_api_key",
        "AP_BASE_URL": "http://localhost:8080"
      }
    }
  }
}
```

### What the MCP Server Gives You

Once connected, Claude has direct tool access to all 280+ pieces:

```
Claude can now call:
  activepieces__gmail__send_email({ to, subject, body })
  activepieces__slack__send_message({ channel, text })
  activepieces__youtube__get_videos({ channelId, maxResults })
  activepieces__notion__create_page({ parentId, title, content })
  activepieces__google_sheets__append_row({ spreadsheetId, row })
  activepieces__anthropic__ask_claude({ prompt, model })
  ... (280 more)
```

### MCP Flows — Exposing Complete Pipelines as MCP Tools

After building a pipeline in Activepieces, you can expose the entire flow as a single MCP tool:

```
Pipeline: YouTube Research → Transcribe → Summarize → Slack Digest

Exposed as MCP tool:
  activepieces__flows__run_youtube_research({ channel_ids, date_range })
  → Returns: { summary: "...", slack_sent: true }
```

The AI agent (or you via Claude) calls one tool and the entire 7-step pipeline runs. The agent doesn't need to know the pipeline internals — it just calls it like a function.

**How to create an MCP Flow in Activepieces:**
1. Build your flow in the builder
2. Go to Flow Settings → "Expose as MCP Tool"
3. Define the input parameters (what the caller passes in)
4. Define the output shape (what gets returned)
5. The flow now appears as a tool in the MCP server

---

## Part 2: The Skills Layer

### What Skills Are
A skill is a pre-written expert prompt that Claude uses to handle a specific category of automation task. Each skill:
- Knows the piece schemas for its category (via Context7)
- Knows common patterns for that category
- Knows typical failure modes and how to handle them
- Produces consistent, correct output for its domain

Skills are stored in `.claude/skills/` in this repo, or injected into Claude sessions as system context.

### Skill Structure
Each skill file contains:
1. **What this skill does** — one sentence
2. **Pieces covered** — exact pieceName strings for this category
3. **Common patterns** — the 3-5 most frequent workflows in this category
4. **Schema reference** — key input/output fields for each piece
5. **Failure modes** — what goes wrong and how to handle it
6. **Example flow fragment** — ready-to-use JSON for the most common pattern

---

### Skill: YouTube
```markdown
# Skill: YouTube Automation

PIECES: @activepieces/piece-youtube
Context7: /activepieces/activepieces → search "piece-youtube"

COMMON PATTERNS:
1. New video trigger → process video
   Trigger: new_video_in_channel
   Input: { channelId: string, pollingInterval: "every_5_minutes" }

2. Search videos
   Action: search_videos
   Input: { query: string, maxResults: number, order: "relevance|date|viewCount" }

3. Get video details
   Action: get_video_details
   Input: { videoId: string }
   Output: { title, description, viewCount, likeCount, publishedAt, channelId }

4. Get channel videos
   Action: get_channel_videos
   Input: { channelId: string, maxResults: number }

KEY FAILURE MODES:
- API quota exceeded: add delay node between calls, batch requests
- Private/deleted video: check status field before processing
- channelId vs channel handle: AP expects channelId (UCxxxxx format), not @handle
  Fix: use get_channel_by_handle action first to resolve the ID
```

---

### Skill: LLM Operations
```markdown
# Skill: LLM / AI Operations

PIECES: @activepieces/piece-anthropic, @activepieces/piece-openai
Context7: /activepieces/activepieces → search "piece-anthropic"

COMMON PATTERNS:
1. Basic LLM call
   Action: ask_claude (Anthropic) | send_message (OpenAI)
   Input: { prompt: string, model: "claude-sonnet-4-6", maxTokens: 1024 }
   Output: { content: string }

2. Structured output (JSON extraction)
   Prompt pattern: "Return ONLY valid JSON. Format: { field1: type, field2: type }. No explanation."
   Follow with: Code Module node to JSON.parse() the output

3. Batch LLM (loop over items)
   Pattern: Loop node → LLM node inside loop
   Rate limit: Add Delay node (1 second) inside loop to avoid hitting limits

4. Classification
   Prompt: "Classify this text into ONE of: [A, B, C]. Return only the letter."
   Follow with: Router node branching on output value

KEY FAILURE MODES:
- Rate limit: add retry logic (AP has built-in retry option on actions)
- Long input: use chunk-long-text mechanism from library before LLM call
- JSON parse failure: always validate LLM output before passing downstream
```

---

### Skill: Gmail / Email
```markdown
# Skill: Gmail + Email

PIECES: @activepieces/piece-gmail
Context7: /activepieces/activepieces → search "piece-gmail"

COMMON PATTERNS:
1. Send email
   Action: send_email
   Input: { to: string, subject: string, body: string, bodyType: "html|plain" }

2. New email trigger
   Trigger: new_email
   Input: { from: string (optional filter), subject: string (optional filter) }

3. Send with attachments
   Action: send_email_with_attachments
   Input: { to, subject, body, attachments: [{ filename, content }] }

4. Reply to email
   Action: send_email
   + Set replyTo field to original sender

KEY FAILURE MODES:
- Gmail OAuth expired: user needs to reconnect Gmail in AP connections
- HTML in body: set bodyType: "html" explicitly — defaults to plain text
- Rate limit: 100 emails/second max — unlikely to hit in automation context
```

---

### Skill: Master Flow Builder
```markdown
# Skill: Flow Builder (Master)

This skill builds complete Activepieces flows from plain English descriptions.

STEP 1: Understand the request
- What triggers this pipeline? (schedule / webhook / new email / new data / manual)
- What data comes in?
- What should happen to it? (transform / filter / call AI / enrich)
- Where does the result go? (email / slack / database / webhook / file)

STEP 2: Select pieces
- Use the 20 priority pieces list (see Spec 002)
- Pull exact schemas from Context7 before generating JSON
- Map each step to a specific pieceName + actionName

STEP 3: Generate FlowVersion JSON
- schemaVersion: "21"
- Trigger as root, actions as linked list via nextAction
- Step names: trigger, step_1, step_2, etc.
- Include errorHandlingOptions on every PieceAction

STEP 4: Present the plan (text summary first, JSON second)
- Show the user what will be built before building it
- List any connections needed (Gmail, Slack, etc.)
- Ask for confirmation or adjustments

STEP 5: Inject via IMPORT_FLOW
- POST /v1/flows (create empty)
- POST /v1/flows/{id} with { type: IMPORT_FLOW, request: flow_json }
```

---

## Part 3: Context7 Usage in Skills

Every skill should pull live schema data at the start of any complex flow generation:

```python
# In any flow generation session, prepend this to the Claude context:
CONTEXT7_INSTRUCTION = """
Before generating any Activepieces piece configuration, use Context7:
  Library: /activepieces/activepieces
  Search for: [pieceName] [actionName]
  
This gives you the exact input field names, types, required flags, and valid values.
Never guess at these — always look them up first.
"""
```

---

## Part 4: Skills as Claude Code Skills (`.claude/skills/`)

Each skill above can also be saved as a Claude Code skill in `.claude/skills/` so it auto-loads in relevant sessions:

```
.claude/skills/
├── activepieces-master.md     # Master flow builder skill
├── activepieces-youtube.md    # YouTube pieces skill
├── activepieces-llm-ops.md    # LLM operations skill
├── activepieces-gmail.md      # Gmail skill
├── activepieces-slack.md      # Slack skill
├── activepieces-scraping.md   # HTTP + scraping skill
└── activepieces-storage.md    # Sheets + Notion + Airtable skill
```

When starting a session to build a YouTube pipeline, load the YouTube skill + master skill. Claude arrives already knowing the piece schemas, common patterns, and failure modes.

---

## Success Criteria

- [ ] Activepieces MCP server installs and connects to Claude Desktop via mcp.json
- [ ] Claude can call at least 5 pieces as MCP tools (Gmail, Slack, YouTube, HTTP, Anthropic)
- [ ] At least one complete pipeline exposed as an MCP Flow (callable in one tool call)
- [ ] YouTube skill loads and Claude can build a YouTube pipeline without querying Context7 redundantly
- [ ] Master flow builder skill generates valid FlowVersion JSON for any description
- [ ] All skill files reference exact pieceName strings (not approximate names)
- [ ] Context7 integration instruction is present in every flow generation prompt
- [ ] Skills saved in `.claude/skills/` folder and loadable per session
