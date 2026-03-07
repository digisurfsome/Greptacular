# Agent Handoff Template

> Copy this into the start of every coding session. Fill in the blanks. This keeps the agent focused and preserves context for maximum coding output.

---

## Copy-Paste Below This Line

```
## MANDATORY: Context Efficiency Rules

You are working on the Greptacular codebase. Follow these rules strictly to preserve your context window for coding:

### Step 1: Read Briefings (do this FIRST, before anything else)
1. Read `AGENT_BRIEFING.md` at project root — master architecture overview
2. Read `docs/agent-briefs/{FEATURE_BRIEF}.md` — specific to your task

### Step 2: Read ONLY Files You Will Edit
- Read ONLY the files listed in "Files You Will Modify" below
- Do NOT read files "just to understand" — the briefings cover that
- Do NOT read types.ts or api.ts in full — search for the specific interface/function you need
- Maximum 5 files read directly by you

### Step 3: Use Subagents for Everything Else
- **Need to understand how another component works?** → Spawn an Explore subagent
- **Need to find where something is imported?** → Spawn an Explore subagent
- **Need to check what pattern a similar component uses?** → Spawn an Explore subagent
- **Need to search for a string across the codebase?** → Spawn an Explore subagent
- NEVER run Glob/Grep yourself unless it's a single targeted search for a specific file
- The subagent's context is separate from yours — use this to your advantage

### Step 4: Context Budget
- Stop coding at 50% context usage
- If you hit 45%, wrap up current work, commit, and save progress notes
- Never start a new feature if you're above 40%

---

## Your Task

{DESCRIBE THE SPECIFIC TASK — be detailed about what to build, not how}

## Feature Brief to Read

docs/agent-briefs/{BRIEF_NAME}.md

## Files You Will Modify

- {path/to/file1}
- {path/to/file2}
- {path/to/file3}

## Files You Might Need to Reference (use subagent)

- {path/to/reference1} — {why you might need it}
- {path/to/reference2} — {why you might need it}

## Acceptance Criteria

- {What "done" looks like — specific, testable}
- {Another criterion}
- {Another criterion}
```

---

## Examples

### Example 1: Adding Auto-Notes to YT Lab

```
## Your Task
Add an auto-notes pipeline to YT Strategy Lab. When a video is queued, automatically
pull its transcript and generate concise notes using Claude Haiku. Notes should include:
core topic, key bullet points, tools mentioned, and a relevance verdict.

## Feature Brief to Read
docs/agent-briefs/yt-lab-ingest.md

## Files You Will Modify
- server/services/yt_notes.py (NEW — auto-notes service)
- server/routers/yt_notes.py (NEW — API endpoints)
- server/main.py (register new router)
- ui/src/components/yt-lab/NotesTriageView.tsx (NEW — notes card UI)
- ui/src/lib/api.ts (add new API functions)
- ui/src/lib/types.ts (add YTAutoNotes interface)

## Files You Might Need to Reference (use subagent)
- server/services/yt_processor.py — similar AI service pattern to follow
- server/routers/yt_processing.py — similar SSE streaming pattern
- ui/src/components/yt-lab/DiscoveryPanel.tsx — similar card-based results UI

## Acceptance Criteria
- POST /api/yt-lab/auto-notes accepts a video_id and returns structured notes
- Notes include: core_topic, key_points[], tools_mentioned[], verdict
- Uses Haiku model for speed (< 30 seconds per video)
- UI shows notes as swipeable cards with "Full Process" / "Skip" actions
```

### Example 2: Adding a Setting to Workspace

```
## Your Task
Add a "default model" setting to the Workspace that persists per-user. When creating
a new conversation, it should default to the user's preferred model instead of always
defaulting to Sonnet.

## Feature Brief to Read
docs/agent-briefs/workspace.md

## Files You Will Modify
- server/services/workspace_database.py (add default_model to conversations or settings)
- server/routers/workspace.py (expose new setting endpoint)
- ui/src/components/workspace/WorkspaceSidebar.tsx (default model in new chat form)
- ui/src/hooks/useWorkspaceConversations.ts (use default model when creating)

## Files You Might Need to Reference (use subagent)
- server/routers/settings.py — pattern for settings endpoints
- ui/src/components/SettingsModal.tsx — pattern for settings UI

## Acceptance Criteria
- New conversations use the user's preferred default model
- Setting persists across browser sessions (stored in database, not localStorage)
- UI shows current default in the new chat form
```

---

## Tips for Writing Good Handoffs

1. **Be specific about the task** — "add X that does Y" not "improve the system"
2. **List exact files** — the agent shouldn't need to guess
3. **Reference files go through subagents** — only list files the agent will EDIT in the main section
4. **Acceptance criteria are testable** — not "it should work well" but "POST /api/x returns Y"
5. **One task per session** — don't ask for 5 features at once
6. **If the task is big, split it** — backend in one session, frontend in another
