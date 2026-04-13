# Operating System Creator — Proof of Concept: Chat Extractor

> **What this is:** The 8th system run through the OS Automation Creator Pipeline (10 stages + 2 gap analyses). This takes a real, daily pain point — hundreds of Claude chats containing buried PRDs, ideas, decisions, and reference material with no way to search or extract them — and builds it from scratch using the unified pipeline. This is a 2-phase system with an extensible filter architecture, similar in structure to the Video Intelligence Pipeline.

---

## Stage 0: Process Capture

### Purpose

Raw intake. Everything about the manual process on paper before organizing it.

---

**1. Process name:** Chat Extractor — AI Conversation Knowledge Mining System

**2. What a human does today, step by step:**

1. Finish a Claude chat session (Claude.ai, Claude Code, or AutoForge workspace chat)
2. Realize the chat contains valuable stuff — a PRD section, a decision about architecture, a half-baked idea, a diagram, a process description
3. Try to remember which chat it was in. Scroll through recent conversations. Open 5-6 chats looking for the one with "that thing about the pipeline"
4. Find it (maybe). Re-read 200+ messages to locate the 3 paragraphs that matter
5. Copy-paste those paragraphs into a doc, a new chat, or just leave them buried
6. For Claude Code sessions — can't even search them. JSONL files in `~/.claude/projects/` with no search interface. Good luck finding anything
7. Realize a week later that an early chat had a diagram or concept that got dropped during iteration. Go hunting again
8. Give up on some chats entirely — the insight is gone because it's buried in iteration noise
9. For PRDs that evolved across 4-5 chats: try to manually merge the latest version with early insights that didn't get carried forward. Spend 30+ minutes producing an incomplete merge
10. Repeat daily. The backlog of unprocessed chats grows. Valuable knowledge decays

**3. Phase structure:** Two distinct phases.

- **Phase 1: Ingest** — Every chat gets captured and turned into a structured worksheet. Runs for every chat, no exceptions. Steps 1-4.
- **Phase 2: Filter/Extract** — Apply extraction lenses to worksheeted chats on demand. The filter list is extensible (new types get added over time). Steps 5-8.

Phase 1 can run without Phase 2. Phase 2 requires Phase 1 to have completed for the target chat. Phases are independent once the worksheet exists.

**4. Frequency:** Ad hoc, multiple times per day. Can batch old chats. 5-10 chats/day when catching up on backlog, 1-2 chats/day when maintaining.

**5. Duration per run:** 15-30 minutes per chat manually (worksheet creation). 10-20 minutes per extraction filter applied manually. A chat with 3 filters = 45-90 minutes total.

**6. Volume per run:** 1-5 chats per session. Backlog of hundreds of unprocessed chats.

**7. Starting data sources:**
- Chat exports from Claude.ai (JSON or copy-paste)
- Claude Code session logs (JSONL files at `~/.claude/projects/`)
- AutoForge workspace chat logs (from the app's own database)
- Raw text pasted from any chat window

**8. End result goes to:**
- `docs/ideas/` — idea cards extracted from chats
- `docs/page-prds/` — consolidated PRD sections
- Knowledge base files in the repo (organized by topic)
- Decision logs
- Checklists and process docs
- Skill/automation specs

**9. Tools already in use:**

| Tool/Service | What it's used for | Has API? |
|---|---|---|
| Claude.ai | Source of conversations to extract | Yes (export JSON) |
| Claude Code | Source of CLI conversations (JSONL) | Yes (local files) |
| AutoForge | Source of workspace chats | Yes (local database) |
| File system | Where extracted outputs land | Yes (Python os/pathlib) |
| Claude API (Sonnet/Haiku) | AI analysis for worksheet generation and filter extraction | Yes |

**10. What breaks most often / pain points:**
- **Can't search Claude Code sessions at all.** JSONL files with no index, no search, no way to find "which session discussed X?"
- **Good ideas get buried under iteration.** Chat message 47 had a brilliant diagram. Messages 48-200 iterated past it. The diagram is functionally lost.
- **Early insights don't survive to final versions.** PRD v1 had a concept discussed once. PRD v4 is the "latest" but silently dropped that concept. Nobody notices until months later.
- **No categorization or tagging.** Can't answer "show me all chats where we discussed database schema" without manually re-reading every chat.
- **Manual extraction is incomplete by nature.** Humans re-reading their own chats skip things they think they remember but actually don't. AI extraction catches what humans skip.

**11. Most tedious part:** Re-reading long chats looking for specific content. The ratio of "reading noise" to "extracting signal" is approximately 20:1.

**12. Interaction method:** CLI commands. `chat-extract ingest <file>`, `chat-extract filter <chat-id> --type prd`, `chat-extract batch <directory>`.

**13. Compliance:** None. These are the user's own conversations with AI tools. No PII unless the chat itself contained client data (standard data handling applies).

**14. Access model:** Solo operator. Just one user.

### Output

- `process_name`: Chat Extractor
- `raw_description`: 10-step manual process above
- `phase_count`: 2 (Ingest + Filter/Extract)
- `trigger`: User runs CLI command (ad hoc) or batch processes a directory
- `frequency`: Multiple times daily, ad hoc
- `duration_minutes`: 15-30 per chat (Phase 1), 10-20 per filter (Phase 2)
- `volume_per_run`: 1-5 chats, backlog of hundreds
- `data_source`: Claude.ai exports, Claude Code JSONL, AutoForge workspace chats, raw paste
- `data_destination`: docs/ideas/, docs/page-prds/, knowledge base files, decision logs, checklists
- `tools_in_use`: Claude.ai, Claude Code, AutoForge, Claude API (Sonnet/Haiku), file system
- `pain_points`: Can't search Claude Code, ideas buried in iteration, early insights lost, no categorization, incomplete manual extraction
- `interaction_method`: CLI
- `compliance_requirements`: None
- `access_model`: Solo operator

### Done When

- [x] Every question has an answer
- [x] Step-by-step walkthrough is specific enough to train someone new
- [x] Pain points captured (5 listed)
- [x] Phase count determined (2 phases)
- [x] Interaction method identified (CLI)

**Status: COMPLETE**

---

## Stage 1: 6-Step Mapping

### Purpose

Map the raw process to INPUT -> PROCESS -> OUTPUT -> STATE -> NOTIFY -> SCHEDULE. Two phases, mapped separately.

---

### Phase 1: Ingest

**1. INPUT type:** File read (JSONL, JSON, markdown, raw text). User provides a file path or pastes text. Also: database query for AutoForge workspace chats.

**2. PROCESS type:** Analyze-extract (parse chat format) + Generate (produce structured worksheet from conversation). The worksheet is the core value — it transforms a 200-message conversation into a scannable, structured document.

**3. OUTPUT type:** Database write (worksheet saved with metadata) + file export (worksheet as markdown).

### Phase 2: Filter/Extract

**1. INPUT type:** Database query (load worksheet for a given chat ID). User selects which filters to apply.

**2. PROCESS type:** Analyze-extract (run each selected filter against the worksheet). Each filter has its own prompt template. This step REPEATS once per filter selected.

**3. OUTPUT type:** File export (each filter produces a file in the appropriate location — idea cards to `docs/ideas/`, PRD sections to `docs/page-prds/`, etc.) + database write (link artifact back to source chat).

### State Tracking

**4. Status lifecycle:**

```
captured -> parsing -> parsed -> worksheeting -> worksheeted -> filtering -> filtered -> archived
```

- `captured`: Raw chat file registered, not yet processed
- `parsing`: Format detection and speaker consolidation in progress
- `parsed`: Clean conversation object created
- `worksheeting`: AI analyzing chat, generating worksheet
- `worksheeted`: Worksheet complete, ready for Phase 2 filters
- `filtering`: One or more extraction filters running
- `filtered`: All requested filters complete, artifacts saved
- `archived`: Chat and all artifacts archived (long-term storage)

**5. Audit trail:** Full event log with timestamps. Need to know when each chat was ingested, what filters were applied, when artifacts were created, and whether any filters were re-run with updated prompts.

**6. Dedup key:** Source file hash (SHA-256 of the raw chat content). Prevents re-ingesting the same chat twice. If a Claude Code session file grows (appended messages), the hash changes — treat as a new version, link to the previous one.

### Notifications

**7. Who needs to know:** Just the operator (solo user).

**8. What they need to know:**
- Completion: "Worksheeted 3 chats. 47 key points extracted. Ready for filtering."
- Error: "Failed to parse chat X — unknown format."
- Batch summary: "Batch complete: 12/15 chats worksheeted, 3 failed (2 empty, 1 format error)."

**9. How:** Terminal output for interactive use. Log file for batch runs. No Telegram/Slack needed — this is a local CLI tool.

### Scheduling

**10. When:** On-demand (user runs the command). No scheduled runs. Could add a file watcher later for auto-ingest of new Claude Code sessions.

**11. Failure recovery:** Resume from where it left off. Each chat is independent — if one fails, continue processing the rest. Failed chats get status `error` with the error message stored.

**12. Infrastructure:** Local machine (the user's dev computer). Same machine where Claude Code sessions live. No cloud needed.

### Multi-Phase Connection

**13. Phase 1 output feeds Phase 2:** The worksheet (structured document) is the handoff artifact. Phase 2 filters operate on worksheets, not raw chats. This means Phase 1 must complete before Phase 2 can run for a given chat, but Phase 2 can be deferred indefinitely. Multiple Phase 2 filter runs can happen on the same worksheet at different times.

### Architecture Diagram

```
USER INPUT                         PHASE 1: INGEST                              PHASE 2: FILTER/EXTRACT
==========                         ===============                              =======================

                                   ┌─────────────────┐
  CLI command ──────────────────>  │  Step 1: Capture  │
  (file path / paste / batch)      │  Parse format     │
                                   │  Detect source    │
                                   └────────┬──────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │  Step 2: Speaker  │
                                   │  Consolidation    │
                                   │  Merge fragments  │
                                   └────────┬──────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │  Step 3: Worksheet│       ┌─────────────────────────────────────┐
                                   │  Generation       │       │  Step 5: Filter Selection            │
                                   │  (AI — Sonnet)    │       │  User picks 1+ extraction types      │
                                   └────────┬──────────┘       │                                      │
                                            │                  │  ┌──────────┐  ┌──────────┐          │
                                            ▼                  │  │ PRD      │  │ Knowledge│  ...     │
                                   ┌─────────────────┐        │  │ Consol.  │  │ Dump     │  [+]     │
                                   │  Step 4: Save &   │       │  └──────────┘  └──────────┘          │
                                   │  Categorize       │──────>│  ┌──────────┐  ┌──────────┐          │
                                   │  (DB + metadata)  │       │  │ Idea     │  │ Tool/    │          │
                                   └──────────────────┘       │  │ Cards    │  │ Skill    │          │
                                                               │  └──────────┘  └──────────┘          │
                                            WORKSHEET          │  ┌──────────┐  ┌──────────┐          │
                                            STORED             │  │ Checklist│  │ Decision │          │
                                              │                │  │ Builder  │  │ Log      │          │
                                              │                │  └──────────┘  └──────────┘          │
                                              │                └──────────┬──────────────────────────┘
                                              │                           │
                                              │                           ▼
                                              │                ┌─────────────────────────────────────┐
                                              │                │  Step 6: Filter Execution             │
                                              └───────────────>│  Run selected filter(s) against       │
                                                               │  worksheet. Repeats per filter.        │
                                                               │  Each filter = own prompt template.    │
                                                               └──────────┬────────────────────────────┘
                                                                          │
                                                                          ▼
                                                               ┌─────────────────────────────────────┐
                                                               │  Step 7: Quality Check                │
                                                               │  Validate output (length, format,     │
                                                               │  key fields). Pass → save.            │
                                                               │  Fail → retry or flag.                │
                                                               └──────────┬────────────────────────────┘
                                                                          │
                                                                          ▼
                                                               ┌─────────────────────────────────────┐
                                                               │  Step 8: Save Artifacts               │
                                                               │  Save to appropriate location:        │
                                                               │    PRD → docs/page-prds/              │
                                                               │    Idea → docs/ideas/                 │
                                                               │    Knowledge → knowledge-base/        │
                                                               │  Link back to source chat.            │
                                                               └───────────────────────────────────────┘

STATE: SQLite database
  - chats (chat_id, source_type, source_path, content_hash, status, created_at)
  - worksheets (worksheet_id, chat_id, summary, topics_json, decisions_json, created_at)
  - artifacts (artifact_id, worksheet_id, filter_type, output_path, quality_score, created_at)
  - filter_runs (run_id, worksheet_id, filter_type, status, started_at, completed_at)

PRESETS:
  - "Quick Capture" → Phase 1 only (worksheet)
  - "Full Extract"  → Worksheet + Knowledge Dump + Idea Cards
  - "PRD Mode"      → Worksheet + PRD Consolidation + Decision Log
```

### Output

- `architecture_map`: INPUT (file read/DB query) -> PROCESS (parse + AI analyze) -> OUTPUT (DB write + file export) -> STATE (SQLite) -> NOTIFY (terminal/log) -> SCHEDULE (on-demand CLI)
- `phase_connections`: Phase 1 produces worksheet -> Phase 2 consumes worksheet. Independent after handoff.
- `status_lifecycle`: captured -> parsing -> parsed -> worksheeting -> worksheeted -> filtering -> filtered -> archived
- `dedup_key`: SHA-256 content hash
- `notification_plan`: Terminal output for interactive, log file for batch
- `schedule_plan`: On-demand via CLI
- `architecture_diagram`: See above

### Done When

- [x] Every component of the 6-step pattern has a type assigned
- [x] Each phase mapped separately with connections documented
- [x] State tracking has a status lifecycle defined
- [x] Text architecture diagram exists
- [x] Schedule and notification plans are defined

**Status: COMPLETE**

---

## Stage 2: Step Decomposition

### Purpose

Break each step into granular detail. Run once per phase.

---

### Phase 1 Steps

#### Step 1: Chat Capture

**1. Human action:** Take a raw chat (file path, paste, or auto-detect from Claude Code session directory). Detect the format — is it JSONL (Claude Code), JSON (Claude.ai export), markdown, or raw text? Parse it into a normalized internal structure.

**2. Input needed:** File path provided by user via CLI argument. Or raw text piped to stdin. Or a directory path for batch mode (scan for all chat files).

**3. Decisions:** Which format parser to use. Handled by file extension and content sniffing — no human judgment needed.

**4. Claude decides?** Yes with clear rules. Format detection is deterministic: `.jsonl` = Claude Code, `.json` = Claude.ai export, `.md` = markdown, everything else = raw text. Content sniffing as fallback (look for JSON structure, JSONL line-by-line structure, markdown headers).

**5. Output:** Normalized chat object — array of messages, each with `speaker` (human/assistant/system), `content` (text), `timestamp` (if available), `message_index`.

**6. Output goes to:** Step 2 (speaker consolidation). Also saved to database as raw record.

**7. API tool:** None needed. Pure file I/O with Python. `json` and custom JSONL parser. No external APIs.

**8. Error case:** Unrecognized format → alert user, skip file, log error. Empty file → skip with warning. Corrupted JSON → try recovery parse, if fails → skip with error.

**9. Redo strategy:** Safe to re-run. Overwrites the raw record in DB. No side effects.

**10. Human time:** 2-5 minutes per chat (finding the file, copy-pasting, deciding format). Automated: <1 second.

**11. Repeats:** Once per chat. In batch mode, repeats per file in directory.

**12. Extensible options:** Yes — new source formats get added over time (e.g., ChatGPT export format, Gemini sessions, Cursor conversations). Each format needs a parser. Format parsers are a plugin-style extensible list.

#### Step 2: Speaker Consolidation

**1. Human action:** Identify speakers (human vs assistant). Merge fragmented messages — sometimes a single thought spans multiple consecutive messages from the same speaker. Clean up system messages, tool calls, and noise.

**2. Input needed:** Normalized chat object from Step 1.

**3. Decisions:** Whether consecutive messages from the same speaker should merge. Whether system/tool messages should be kept, summarized, or dropped.

**4. Claude decides?** Yes with clear rules: Consecutive same-speaker messages within 60 seconds → merge. System messages → summarize as `[system: tool call to X]`. Empty messages → drop. Code blocks → preserve intact.

**5. Output:** Clean conversation — sequential alternating human/assistant turns, each turn containing the complete thought. Metadata preserved (timestamps, original message count).

**6. Output goes to:** Step 3 (worksheet generation). Saved to DB as the "cleaned" version.

**7. API tool:** None. Pure Python string processing and heuristics.

**8. Error case:** No messages after cleaning (all were empty/system) → flag as "empty chat," skip with warning. Single-speaker chat (monologue) → proceed but tag as unusual.

**9. Redo strategy:** Safe to re-run. Deterministic — same input always produces same output.

**10. Human time:** 5-10 minutes per chat. Automated: <2 seconds.

**11. Repeats:** Once per chat.

**12. Extensible options:** No. The consolidation rules are fixed.

#### Step 3: Worksheet Generation (MVP STEP)

**1. Human action:** Read the entire chat. Produce a structured worksheet containing: one-paragraph summary, hierarchical key topics (main point -> sub-points -> details), all decisions made and reasoning, all artifacts mentioned or created (diagrams, code, configs), all URLs referenced, open questions left unresolved, and a list of unique early insights that weren't repeated in later messages.

**2. Input needed:** Clean conversation from Step 2. Full text, all turns.

**3. Decisions:** What counts as a "key topic" vs noise. What counts as a "decision" vs casual discussion. Whether an early insight is truly unique or was restated later. These are judgment calls.

**4. Claude decides?** Yes but needs judgment. This is the core AI step. Claude reads the full conversation and produces the worksheet. "Good" looks like: every substantive topic captured, no hallucinated topics, decisions include the reasoning, early unique insights are correctly identified as not repeated later.

**5. Output:** Structured worksheet (JSON + rendered markdown):
```
{
  "summary": "One paragraph overview",
  "key_topics": [
    {
      "topic": "Main topic name",
      "sub_points": ["detail 1", "detail 2"],
      "message_range": [12, 45]
    }
  ],
  "decisions": [
    {
      "decision": "What was decided",
      "reasoning": "Why",
      "message_index": 34
    }
  ],
  "artifacts": ["diagram of X", "code snippet for Y"],
  "urls": ["https://..."],
  "open_questions": ["Unresolved: should we use X or Y?"],
  "unique_early_insights": ["Message 8 had concept Z which was never mentioned again"],
  "tags": ["architecture", "database", "prd"]
}
```

**6. Output goes to:** Step 4 (save & categorize). This is the primary artifact of the system.

**7. API tool:** Claude API (Sonnet 4). Needs the full conversation as context. Cost: ~$0.01-0.05 per chat depending on length (Sonnet input pricing on conversations of 5K-50K tokens).

**8. Error case:** Claude returns malformed JSON → retry with stricter formatting instructions. Claude hallucinates topics not in the chat → quality check in Phase 2 catches this. Context too long for model → split conversation into overlapping chunks, worksheet each chunk, then merge.

**9. Redo strategy:** Safe to re-run. Worksheet gets overwritten. Old artifacts from Phase 2 become stale — flag them for re-extraction but don't auto-delete (user might prefer the old version).

**10. Human time:** 15-30 minutes per chat. This is the bottleneck. Automated: 10-30 seconds (API call latency).

**11. Repeats:** Once per chat. May re-run if prompt improves.

**12. Extensible options:** The worksheet STRUCTURE is fixed (same fields every time). But the prompt can be tuned — this is versioned, not extensible.

#### Step 4: Save & Categorize

**1. Human action:** Save the worksheet to a database with metadata (source, date, topic tags). Auto-categorize by topic using keyword extraction from the worksheet. If AI confidence is >80%, auto-assign category. Below 80%, suggest to user for confirmation.

**2. Input needed:** Worksheet from Step 3. Source metadata from Step 1.

**3. Decisions:** Which category/tags to assign. Whether the auto-suggestion is correct.

**4. Claude decides?** Yes with clear rules for high-confidence cases. Claude (Haiku — cheap) reads the worksheet summary and key topics, suggests 1-3 tags from a known tag list. Confidence score returned. >80% → auto-assign. <80% → prompt user.

**5. Output:** Saved worksheet record in database with metadata and tags. Markdown file written to a worksheets directory.

**6. Output goes to:** Database (primary). File system (markdown backup). Ready for Phase 2 filters.

**7. API tool:** Claude API (Haiku) for categorization. ~$0.001 per chat. SQLite for storage.

**8. Error case:** Database write fails → retry. Tag suggestion fails → save without tags, flag for manual tagging.

**9. Redo strategy:** Safe to re-run. Overwrites existing record. Tags get updated.

**10. Human time:** 2-5 minutes. Automated: <3 seconds.

**11. Repeats:** Once per chat.

**12. Extensible options:** Yes — the tag list grows over time. New tags get added as the user encounters new topics. The system should support `chat-extract tags add <tag>`.

### Phase 2 Steps

#### Step 5: Filter Selection

**1. Human action:** Look at a worksheeted chat (or batch of chats). Decide which extraction filters to apply. Pick from the available filter list, or use a preset.

**2. Input needed:** Worksheet ID (or list of IDs for batch). Available filter types.

**3. Decisions:** Which filters are useful for this chat. This is a human judgment call — the system can suggest based on tags, but the user decides.

**4. Claude decides?** Partially. The system can suggest filters based on worksheet tags (e.g., if tags include "architecture" and "prd", suggest PRD Consolidation + Decision Log). But the user confirms.

**5. Output:** List of selected filter types to run.

**6. Output goes to:** Step 6 (filter execution).

**7. API tool:** None. Pure CLI interaction.

**8. Error case:** User selects a filter that doesn't exist → show available filters, ask again. No filters selected → abort with message.

**9. Redo strategy:** N/A — this is just a selection step. Can re-select anytime.

**10. Human time:** 1 minute. Just picking from a list.

**11. Repeats:** Once per extraction session. User can come back and select more filters later.

**12. Extensible options:** YES — this is the core extensibility point. The filter list grows over time. New filter types are added via a "plus button" pattern. Starting set:
- PRD Consolidation
- Knowledge Dump
- Idea Cards
- Tool/Skill Extractor
- Checklist Builder
- Decision Log

Each filter is defined by: a name, a prompt template, an output format, and a destination path pattern.

#### Step 6: Filter Execution

**1. Human action:** Run each selected filter against the worksheet. Each filter has its own prompt that instructs Claude on what to extract and how to format it.

**2. Input needed:** Worksheet content + filter prompt template. For PRD Consolidation across multiple chats: multiple worksheets + chronological ordering.

**3. Decisions:** None within a single filter run — the prompt template defines the extraction. For multi-chat PRD Consolidation: which chat is "later" supersedes "earlier," but pull forward unique early insights.

**4. Claude decides?** Yes with judgment. Each filter is an AI task. The prompt template provides structure, but Claude must use judgment to extract the right content. "Good" looks like: relevant content extracted, nothing hallucinated, proper format followed.

**5. Output:** Structured extraction in the filter's output format. Each filter type has a defined schema:
- PRD Consolidation → merged PRD markdown with sections
- Knowledge Dump → categorized knowledge base entry
- Idea Cards → individual idea card files (title, concept, potential, next steps)
- Tool/Skill Extractor → automation spec (trigger, inputs, process, outputs)
- Checklist Builder → numbered step-by-step checklist
- Decision Log → table of decisions with context and reasoning

**6. Output goes to:** Step 7 (quality check) before final save.

**7. API tool:** Claude API (Sonnet 4 for complex filters like PRD Consolidation, Haiku for simple ones like Checklist Builder). Cost: $0.01-0.05 per filter run.

**8. Error case:** Claude returns wrong format → retry with stricter prompt. Claude returns empty extraction ("no relevant content found") → log as "no match," don't save empty artifact. API timeout → retry once, then flag.

**9. Redo strategy:** Safe to re-run. Each filter run produces a new artifact version. Old versions kept (append with timestamp).

**10. Human time:** 10-20 minutes per filter (reading worksheet, extracting manually, formatting). Automated: 10-30 seconds.

**11. Repeats:** Once per filter selected. If 3 filters selected, this step runs 3 times.

**12. Extensible options:** The filter LIST is extensible (new filters added over time). Each individual filter's prompt template can also be versioned/improved.

#### Step 7: Quality Check

**1. Human action:** Review the extraction output. Does it make sense? Is it complete? Does it match the expected format? Is it actually useful?

**2. Input needed:** Filter output from Step 6. Expected format specification for that filter type.

**3. Decisions:** Pass or fail. If fail: retry with adjusted prompt, or flag for manual review.

**4. Claude decides?** Yes with clear rules. Automated validation:
- Length check: output is not empty, not suspiciously short (<50 words for most filters)
- Format check: required sections present (e.g., idea card must have title, concept, potential)
- Hallucination check: key claims in the extraction should trace back to worksheet content
- Confidence score: Claude rates its own extraction confidence 1-10

Rules: confidence >= 7 AND format passes AND length passes → auto-save. Confidence 4-6 → save but flag for review. Confidence <4 → retry once, then flag.

**5. Output:** Quality verdict (pass/flag/retry) + quality score.

**6. Output goes to:** Step 8 if pass. Back to Step 6 if retry. Flagged queue if flag.

**7. API tool:** Claude API (Haiku for validation — cheap). ~$0.001 per check.

**8. Error case:** Quality check itself fails → default to "flag for review" (safe fallback).

**9. Redo strategy:** N/A — quality check is stateless. Re-run anytime.

**10. Human time:** 2-5 minutes per filter output. Automated: <3 seconds.

**11. Repeats:** Once per filter output. Retries loop back to Step 6 (max 2 retries).

**12. Extensible options:** Quality criteria per filter type. Each filter defines its own "what good looks like" rules.

#### Step 8: Save Artifacts

**1. Human action:** Save each extracted artifact to the appropriate file location. Link it back to the source chat for traceability.

**2. Input needed:** Validated filter output from Step 7. Destination path pattern from the filter type definition.

**3. Decisions:** File naming. Conflict resolution if a file already exists at the destination.

**4. Claude decides?** Yes with clear rules. File naming: `{filter_type}-{chat_date}-{topic_slug}.md`. Conflict: append incrementing number. Destination paths by filter:
- PRD Consolidation → `docs/page-prds/{page-name}/extracted-{date}.md`
- Knowledge Dump → `knowledge-base/{category}/{topic}.md`
- Idea Cards → `docs/ideas/{idea-slug}.md`
- Tool/Skill Extractor → `docs/ideas/tool-{name}.md`
- Checklist Builder → `docs/checklists/{process-name}.md`
- Decision Log → `docs/decisions/{date}-{topic}.md`

**5. Output:** Saved file + database record linking artifact to source chat and filter run.

**6. Output goes to:** File system (the actual artifact) + database (traceability record).

**7. API tool:** None. Pure file I/O + SQLite.

**8. Error case:** Write permission denied → alert, don't lose the content (save to temp location). Path doesn't exist → create directory. Overwrite conflict → save as new version with timestamp suffix.

**9. Redo strategy:** Safe to re-run. New artifacts get new version numbers. Old versions kept.

**10. Human time:** 2-3 minutes (deciding where to save, naming the file). Automated: <1 second.

**11. Repeats:** Once per artifact (one per filter that passed quality check).

**12. Extensible options:** Destination path patterns are extensible — each new filter type defines where its output goes.

### Cross-Step Questions

**13. Batch/group processing:** Yes. Can queue multiple chats through Phase 1, then selectively apply Phase 2 filters across them. PRD Consolidation specifically operates on MULTIPLE worksheets — it merges insights across chats chronologically.

**14. Presets:**
- **Preset 1: "Quick Capture"** — Phase 1 only. Just worksheet the chat. 80% of the value for 20% of the effort.
- **Preset 2: "Full Extract"** — Worksheet + Knowledge Dump + Idea Cards. General-purpose extraction.
- **Preset 3: "PRD Mode"** — Worksheet + PRD Consolidation + Decision Log. For chats about building things.

**15. MVP step:** Step 3 (Worksheet Generation). Just getting chats into structured, searchable format is 80% of the value. Everything else builds on top of a good worksheet.

### Output

All 12 per-step questions answered for all 8 steps. See above.

- `supports_batch`: Yes — multiple chats through Phase 1, selective Phase 2 across them
- `presets`: Quick Capture, Full Extract, PRD Mode
- `mvp_step`: Step 3 — Worksheet Generation

### Done When

- [x] Every step has all 12 per-step questions answered
- [x] Every decision captured
- [x] MVP step identified (Step 3)
- [x] Batch processing and preset questions answered
- [x] Error AND redo scenarios documented for each step

**Status: COMPLETE**

---

## Gap Analysis (Early Pass)

### Purpose

Quick 2-minute scan of the 18 gaps. Catch showstoppers before investing in detailed design.

---

**Structural (gaps 1-5):**

| # | Gap | Status |
|---|-----|--------|
| 1 | Multi-phase structure | COVERED — 2 phases documented separately |
| 2 | Repeating steps | COVERED — Step 6 repeats per filter selected |
| 3 | Growing option lists | COVERED — Filter types are extensible, format parsers are extensible, tag list grows |
| 4 | Presets | COVERED — 3 presets defined (Quick Capture, Full Extract, PRD Mode) |
| 5 | Cross-item batch/merge | COVERED — Batch ingest + PRD Consolidation across multiple worksheets |

**Practical blockers (gaps 6-11):**

| # | Gap | Status |
|---|-----|--------|
| 6 | API keys needed | NO BLOCKER — Only Claude API key needed (already have it). No external services. |
| 7 | Interaction method | COVERED — CLI commands |
| 8 | AI prompt rough idea | COVERED — Worksheet generation prompt and filter prompt templates described |

### Output

- `pass_type`: "early"
- `showstoppers_found`: None
- `notes`: All structural patterns captured. This system's architecture is well-understood because it mirrors the Video Intelligence Pipeline structure (Ingest + extensible Filters).
- `action`: "proceed"

### Done When

- [x] All 5 structural gaps scanned
- [x] Practical blockers checked
- [x] No showstoppers found

**Status: COMPLETE — Proceed to Stage 3**

---

## Stage 3: Automation Classification

### Purpose

For each step, determine HOW it gets automated — deterministic code, AI-driven, hybrid, human required, or external API.

---

### Classifications

#### Step 1: Chat Capture
- **Classification:** DETERMINISTIC
- **Logic:** File extension check → parser selection. `.jsonl` → JSONL parser. `.json` → JSON parser. `.md` → Markdown parser. Else → raw text parser. Content sniffing fallback: try JSON parse, try JSONL line parse, default to raw text.
- **Could be bash?** Partially — `cat` + `jq` for JSON, but the multi-format detection and normalization needs Python.

#### Step 2: Speaker Consolidation
- **Classification:** DETERMINISTIC
- **Logic:** Iterate messages. If `messages[i].speaker == messages[i-1].speaker` AND `messages[i].timestamp - messages[i-1].timestamp < 60s` → merge content. If speaker is "system" or "tool" → summarize as `[system: {action}]`. If content is empty → drop. Preserve code blocks (detect by ``` markers).

#### Step 3: Worksheet Generation
- **Classification:** AI_DRIVEN
- **Model:** Sonnet 4
- **Prompt skeleton:**
  - **Task:** "You are analyzing a conversation between a human and an AI assistant. Produce a structured worksheet extracting all substantive content."
  - **Input format:** Full cleaned conversation as text, with speaker labels and message indices
  - **Output format:** JSON matching the worksheet schema (summary, key_topics[], decisions[], artifacts[], urls[], open_questions[], unique_early_insights[], tags[])
  - **Key instructions:** "Pay special attention to insights that appear ONLY in early messages and are not repeated or refined later. These are the most at-risk content. For decisions, always capture the REASONING, not just the conclusion."
  - **Example input:** A 20-message conversation about database schema design
  - **Example output:** Worksheet with 3 key topics, 2 decisions, 1 unique early insight about indexing strategy mentioned in message 4 but never revisited
- **Cost estimate:** ~$0.01-0.05 per chat (5K-50K input tokens at Sonnet pricing)

#### Step 4: Save & Categorize
- **Classification:** HYBRID
- **Deterministic part:** Save worksheet to SQLite, write markdown file, compute content hash
- **AI part:** Tag suggestion using Haiku. Read worksheet summary + topics, suggest tags from known list + confidence score
- **Prompt skeleton (Haiku):**
  - **Task:** "Given this worksheet summary and topic list, suggest 1-3 tags from the following tag list. Return tags and confidence score (0-100)."
  - **Input format:** `{summary: "...", topics: [...], available_tags: [...]}`
  - **Output format:** `{tags: ["tag1", "tag2"], confidence: 85}`
  - **Model:** Haiku (cheapest, this is a simple classification task)
- **Cost estimate:** ~$0.001 per chat

#### Step 5: Filter Selection
- **Classification:** HUMAN_REQUIRED
- **Why:** The user decides what they want to extract. The system can suggest based on tags, but the user must confirm. This is a 10-second interaction, not worth automating the decision away.

#### Step 6: Filter Execution
- **Classification:** AI_DRIVEN
- **Model:** Sonnet 4 for complex filters (PRD Consolidation, Knowledge Dump), Haiku for simple ones (Checklist Builder, Decision Log extraction)
- **Prompt skeleton (per filter type):**
  - **PRD Consolidation:** "Given these worksheets in chronological order, produce a consolidated PRD. Later versions supersede earlier ones for any content that evolved. BUT: identify concepts, diagrams, or ideas that appeared in earlier worksheets and were NOT carried forward to later ones. Pull these forward explicitly in a 'Recovered Early Insights' section."
  - **Knowledge Dump:** "Categorize all knowledge from this worksheet into a structured second-brain entry. Categories: concepts, facts, tools/techniques, references, open questions."
  - **Idea Cards:** "Extract every half-baked concept or 'what if' idea from this worksheet. For each, produce: title, one-paragraph concept, potential value (high/medium/low), suggested next step."
  - **Tool/Skill Extractor:** "Find any process described in this worksheet that could become an automation. For each: trigger, inputs, process steps, outputs, estimated complexity (1-10)."
  - **Checklist Builder:** "Extract step-by-step processes from this worksheet. Number each step. Include prerequisites, expected outcome per step, and common mistakes."
  - **Decision Log:** "Extract every decision made in this conversation. For each: what was decided, the alternatives considered, the reasoning, and any caveats mentioned."
  - **Output format:** Each filter defines its own JSON schema
  - **Model choice:** Sonnet for PRD Consolidation and Knowledge Dump (require synthesis). Haiku for the rest (extraction/formatting tasks).
- **Cost estimate:** $0.005-0.03 per filter run depending on model and worksheet length

#### Step 7: Quality Check
- **Classification:** HYBRID
- **Deterministic part:** Format validation (required fields present, length thresholds, no empty sections)
- **AI part:** Haiku confidence check. "Rate your confidence that this extraction is complete and accurate, 1-10. Explain any concerns."
- **Cost estimate:** ~$0.001 per check

#### Step 8: Save Artifacts
- **Classification:** DETERMINISTIC
- **Logic:** Look up destination path pattern for the filter type. Generate filename from template. Check for conflicts. Write file. Insert database record linking artifact to source chat.

### Summary

| Classification | Steps | Count |
|---|---|---|
| Deterministic | 1, 2, 8 | 3 |
| AI-driven | 3, 6 | 2 |
| Hybrid | 4, 7 | 2 |
| Human required | 5 | 1 |
| External API | (none) | 0 |

- `ai_step_count`: 2 (Steps 3, 6) + 2 hybrid = 4 steps using Claude
- `deterministic_step_count`: 3
- `human_step_count`: 1
- `estimated_cost_per_run`: Phase 1: ~$0.01-0.05. Phase 2 per filter: ~$0.005-0.03. Full run with 3 filters: ~$0.03-0.15.

### Done When

- [x] Every step has exactly one classification
- [x] Every AI step has a prompt skeleton with task, input format, output format, model choice
- [x] Every deterministic step has exact logic
- [x] Cost-per-run estimate exists
- [x] No "we'll figure it out later" steps

**Status: COMPLETE**

---

## Stage 4: Environment Setup

### Purpose

Everything needed to actually RUN this system. Runtime, packages, API keys, database, prerequisites, cost math, rate limits.

---

### Runtime

**1. Runtime:** Python 3.11+

**2. Packages:**

| Package | Version | Purpose |
|---|---|---|
| `anthropic` | `>=0.39.0` | Claude API calls (worksheet generation, filter execution, quality checks) |
| `click` | `>=8.1` | CLI framework |
| `sqlite3` | (stdlib) | Database — no external package needed |
| `pathlib` | (stdlib) | File path handling |
| `hashlib` | (stdlib) | SHA-256 content hashing for dedup |
| `json` | (stdlib) | JSON parsing |
| `rich` | `>=13.0` | Terminal output formatting (tables, progress bars) |
| `pydantic` | `>=2.0` | Data validation for worksheets and filter outputs |

**3. System requirements:** None. Runs on any machine with Python 3.11+. No Docker, no minimum RAM beyond Python baseline. The user's dev machine is the target environment.

### API Keys and Credentials

**Service 1: Anthropic (Claude API)**

**4. Credential type:** API key (bearer token)

**5. How to get it:** Log into console.anthropic.com → Settings → API Keys → Create Key → Copy

**6. Plan required:** Any paid plan. Free tier may have rate limits.

**7. Monthly cost:** Usage-based. Estimated $2-10/month for this system at 5-10 chats/day.

**8. Environment variable:** `ANTHROPIC_API_KEY`

**9. Extra setup:** None.

No other external services. This is a local-first system. No Supabase, no Telegram, no external APIs beyond Claude.

### Database

**10. Database:** SQLite (file-based, zero config, included with Python)

**11. Tables:**

```sql
CREATE TABLE chats (
    chat_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,        -- 'claude_code' | 'claude_ai' | 'autoforge' | 'raw_text'
    source_path TEXT,
    content_hash TEXT NOT NULL UNIQUE, -- SHA-256 for dedup
    raw_content TEXT NOT NULL,
    message_count INTEGER,
    status TEXT NOT NULL DEFAULT 'captured',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE worksheets (
    worksheet_id TEXT PRIMARY KEY,
    chat_id TEXT NOT NULL REFERENCES chats(chat_id),
    summary TEXT NOT NULL,
    topics_json TEXT NOT NULL,         -- JSON array of key topics
    decisions_json TEXT NOT NULL,      -- JSON array of decisions
    artifacts_json TEXT,               -- JSON array of artifacts mentioned
    urls_json TEXT,                    -- JSON array of URLs
    open_questions_json TEXT,          -- JSON array of unresolved questions
    early_insights_json TEXT,          -- JSON array of unique early insights
    tags TEXT,                         -- comma-separated tags
    prompt_version TEXT,               -- version of the worksheet prompt used
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE artifacts (
    artifact_id TEXT PRIMARY KEY,
    worksheet_id TEXT NOT NULL REFERENCES worksheets(worksheet_id),
    filter_type TEXT NOT NULL,         -- 'prd_consolidation' | 'knowledge_dump' | 'idea_cards' | etc.
    output_path TEXT NOT NULL,         -- where the file was saved
    quality_score INTEGER,             -- 1-10 from quality check
    content_preview TEXT,              -- first 200 chars for quick display
    prompt_version TEXT,               -- version of the filter prompt used
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE filter_runs (
    run_id TEXT PRIMARY KEY,
    worksheet_id TEXT NOT NULL REFERENCES worksheets(worksheet_id),
    filter_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending' | 'running' | 'passed' | 'failed' | 'flagged'
    quality_score INTEGER,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE tags (
    tag TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_chats_status ON chats(status);
CREATE INDEX idx_chats_hash ON chats(content_hash);
CREATE INDEX idx_worksheets_chat ON worksheets(chat_id);
CREATE INDEX idx_artifacts_worksheet ON artifacts(worksheet_id);
CREATE INDEX idx_artifacts_filter ON artifacts(filter_type);
CREATE INDEX idx_filter_runs_worksheet ON filter_runs(worksheet_id);
```

**12. Seed data:** Initial tag list: `["architecture", "database", "prd", "idea", "process", "tool", "ui", "api", "security", "testing", "deployment", "debugging"]`. Initial filter type definitions (name, prompt template path, output format, destination pattern) loaded from a `filters/` config directory.

### Prerequisites

**13. Setup steps (in order):**

| # | Step | Type | Description |
|---|---|---|---|
| 1 | Install Python 3.11+ | One-time | `python --version` to verify |
| 2 | Clone/create project | One-time | `mkdir chat-extractor && cd chat-extractor` |
| 3 | Install dependencies | One-time | `pip install anthropic click rich pydantic` |
| 4 | Set API key | One-time | `export ANTHROPIC_API_KEY=sk-...` in shell profile |
| 5 | Initialize database | One-time | `chat-extract init` (creates SQLite file + tables + seed data) |
| 6 | Configure paths | One-time | Set output directories in config (docs/ideas/, docs/page-prds/, etc.) |

**14. What must already exist:** Python installed. Anthropic API key. A directory structure for output files (docs/ideas/, etc.) — or the system creates them on first run.

### Cost Math

**15. Cost per API call:**

| Step | API Used | Model | Cost Per Call | Calls Per Chat | Daily Cost (5 chats) | Monthly Cost |
|---|---|---|---|---|---|---|
| Step 3: Worksheet | Claude API | Sonnet 4 | ~$0.03 | 1 | $0.15 | $4.50 |
| Step 4: Categorize | Claude API | Haiku | ~$0.001 | 1 | $0.005 | $0.15 |
| Step 6: Filter (complex) | Claude API | Sonnet 4 | ~$0.02 | 1 | $0.10 | $3.00 |
| Step 6: Filter (simple) | Claude API | Haiku | ~$0.003 | 2 | $0.03 | $0.90 |
| Step 7: Quality Check | Claude API | Haiku | ~$0.001 | 3 | $0.015 | $0.45 |
| **TOTAL** | | | | | **~$0.30/day** | **~$9.00/month** |

Assumes: 5 chats/day, average 3 filters per chat (1 Sonnet + 2 Haiku). Actual cost varies with conversation length.

### Rate Limits

**16. Anthropic API rate limits:**

| Limit Type | Value | Buffer Strategy |
|---|---|---|
| Requests per minute | 50 (Tier 1) | Process sequentially with 1.5s delay between calls. Batch mode uses 2s delay. |
| Tokens per minute | 40,000 (Tier 1) | Long conversations may hit this. Split into chunks if >30K tokens. |
| Concurrent requests | 5 | Sequential processing, no parallelism needed for this volume. |
| What happens at limit | 429 error, retry-after header | Exponential backoff: 2s, 4s, 8s, max 3 retries. |

### Output

- `runtime`: Python 3.11+
- `dependencies`: anthropic, click, rich, pydantic (+ stdlib: sqlite3, pathlib, hashlib, json)
- `api_keys`: 1 — ANTHROPIC_API_KEY (console.anthropic.com → Settings → API Keys)
- `database`: SQLite, 5 tables (chats, worksheets, artifacts, filter_runs, tags)
- `prerequisites`: 6 steps, all one-time
- `cost_per_run`: ~$0.06 per chat with 3 filters
- `monthly_estimate`: ~$9/month at 5 chats/day
- `rate_limits`: 50 req/min, 40K tokens/min, sequential with 1.5s delay

### Done When

- [x] Every API key has "how to get it" walkthrough
- [x] Cost math itemized with real numbers
- [x] Rate limits documented with buffer strategy
- [x] Prerequisites in order
- [x] A developer could set up the environment from this output alone

**Status: COMPLETE**

---

## Stage 5: Error Handling & Validation

### Purpose

Define what happens when things go wrong AND when things "succeed" but produce bad output.

---

### Error Matrix

| Step | Failure Mode | Detection | Action | Retry Strategy | Fallback |
|---|---|---|---|---|---|
| 1: Capture | Unrecognized format | Parser throws exception | Skip file, log error | No retry — format won't change | Treat as raw text |
| 1: Capture | Empty file | File size = 0 | Skip with warning | No retry | None |
| 1: Capture | Corrupted JSON | json.JSONDecodeError | Try recovery parse (strip trailing comma, fix quotes) | 1 recovery attempt | Fall back to raw text parser |
| 2: Consolidation | No messages after cleaning | Message count = 0 | Flag as "empty chat," skip | No retry — chat is genuinely empty | None |
| 3: Worksheet | Claude API down/timeout | HTTPError, Timeout | Retry with backoff | 3 retries, 2s/4s/8s delay | None — this step requires AI |
| 3: Worksheet | Malformed JSON response | json.JSONDecodeError on response | Retry with stricter prompt ("respond ONLY with valid JSON") | 2 retries with prompt adjustment | Parse what you can, flag missing fields |
| 3: Worksheet | Context too long | Token limit error | Split conversation into overlapping chunks | Process chunks, merge worksheets | Truncate to most recent N messages |
| 4: Categorize | Haiku fails | API error | Save without tags | 1 retry | Manual tagging later |
| 4: Categorize | DB write fails | sqlite3.Error | Retry once | 1 retry after 1s | Write to temp file, alert user |
| 6: Filter Exec | Wrong output format | Pydantic validation fails | Retry with stricter prompt | 2 retries | Save raw output, flag for review |
| 6: Filter Exec | Empty extraction | Output has no substantive content | Log "no relevant content" | No retry — worksheet genuinely lacks this content type | None |
| 7: Quality Check | Quality check itself fails | Any exception in validation | Default to "flag for review" | No retry | Safe fallback — flag, don't discard |
| 8: Save | Write permission denied | OSError | Try temp directory | 1 retry to alternate path | Save content to database, alert user |
| 8: Save | Path doesn't exist | FileNotFoundError | Create directory, retry | Auto-create and retry | None needed |

### Quality Gates

| Step | Good Output | Bad Output | Action on Bad |
|---|---|---|---|
| 3: Worksheet | summary >=50 words, >=1 key topic, topics reference actual message content | Empty summary, 0 topics, topics hallucinated | Retry with adjusted prompt (max 2). Then flag for manual review. |
| 4: Categorize | Tags from known list, confidence score present | Tags not in known list, no confidence | Accept unknown tags as new tag suggestions. Default confidence = 50. |
| 6: Filter Exec | Required fields per filter type present, content substantive (>100 words for most types) | Missing required fields, <50 words, content is generic filler | Retry once with "be more specific and thorough." Then flag. |
| 7: Quality | Confidence >=7 = pass, 4-6 = flag, <4 = retry | N/A — this IS the quality gate | Confidence <4 → retry Step 6. Still <4 → flag for human review. |

### Rollback and Redo

**9. Idempotency by step:**
- Steps 1-2: Fully idempotent. Same input → same output. Safe to re-run.
- Step 3: Idempotent in effect (overwrites previous worksheet). AI output may vary but intent is the same.
- Step 4: Idempotent. Upserts database record.
- Steps 5-8: Idempotent at the artifact level — re-running a filter creates a new version, doesn't destroy the old one.

**10. What gets kept on redo:** Source chat record always preserved. Old worksheet overwritten (one worksheet per chat). Old artifacts preserved with version timestamps — never auto-deleted.

**11. Reprocessing old items:** Yes. When a prompt improves, the user should be able to `chat-extract reprocess --step worksheet --since 2024-01-01` to re-worksheet all chats since a date. Similarly `chat-extract reprocess --filter prd_consolidation --since 2024-01-01` to re-run a filter.

**12. Versioning:** Worksheets: overwrite (one canonical version per chat, tracked by prompt_version). Artifacts: append with timestamp (keep all versions). Filter prompts: versioned in the `filters/` directory with semantic versions.

### Data Retention

**13. Raw data:** Forever. Chat transcripts are the source of truth and take minimal space (text).

**14. Results:** Forever. Worksheets and artifacts are the whole point of the system.

**15. Cleanup:** Never for this system. Data only grows. Could add archival after 1 year if database exceeds 1GB, but that's thousands of chats — unlikely to be a problem.

**16. PII:** Only if the source chat contained PII. The system doesn't add PII. Flag: if source_type is from a client project, mark as `contains_pii = true` and exclude from any future batch exports.

### Cascade Failures

| If This Fails | What Breaks Downstream | Action |
|---|---|---|
| Step 1 (Capture) | Everything — no chat object to process | Skip this chat, continue batch. Log error. |
| Step 2 (Consolidation) | Steps 3-4 can't run — no clean conversation | Skip this chat. Raw chat is still in DB for manual review. |
| Step 3 (Worksheet) | Phase 2 can't run — no worksheet to filter | Chat stays at `parsed` status. User can retry later. |
| Step 4 (Save) | Worksheet exists in memory but not persisted | Critical — retry immediately. If DB truly broken, write worksheet to markdown file as emergency backup. |
| Step 6 (Filter Exec) | Steps 7-8 can't run for this filter | Other filters unaffected. This filter marked as `failed`. |
| Step 7 (Quality) | Step 8 can't run — don't know if output is good | Default to "flag" — save the artifact but mark it unvalidated. |

### Done When

- [x] Every step has at least one documented failure mode
- [x] Quality gates exist for every output-producing step
- [x] Rollback strategy defined
- [x] Data retention has specific timeframes
- [x] Cascade failures mapped

**Status: COMPLETE**

---

## Stage 6: Dashboard Design

### Purpose

Define what the operator sees. For a CLI tool, this is status commands and terminal output — not a web dashboard.

---

### Key Metrics

| # | Metric | Example Value | Update Frequency |
|---|---|---|---|
| 1 | Chats processed (total / today) | "247 total, 3 today" | Every run |
| 2 | Worksheets pending / complete | "2 pending, 245 complete" | Every run |
| 3 | Filters run today (pass / flag / fail) | "8 pass, 1 flagged, 0 fail" | Every run |
| 4 | Cost today / this month | "$0.18 today, $5.40 this month" | Every API call |
| 5 | Flagged items awaiting review | "1 item flagged" | Every quality check |

### Dashboard Layout (Terminal)

```
┌─────────────────────────────────────────────────────────┐
│  CHAT EXTRACTOR STATUS                     2026-04-13   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Chats:  247 total │ 3 today │ 2 pending               │
│  Filters: 892 run │ 8 today │ 1 flagged                │
│  Cost:   $0.18 today │ $5.40 this month                 │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  RECENT ACTIVITY                                        │
│                                                         │
│  14:32  Worksheeted "pipeline-architecture-chat"  [3 topics, 2 decisions]  │
│  14:33  PRD Consolidation → docs/page-prds/pipeline/extracted-20260413.md  │
│  14:33  Idea Card → docs/ideas/self-healing-pipeline.md                    │
│  14:34  ⚠ FLAGGED: Knowledge Dump for "pipeline-architecture-chat"         │
│         Confidence: 5/10. Run: chat-extract review run-abc123              │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  TOP TAGS (last 30 days)                                │
│                                                         │
│  architecture (34) │ prd (28) │ database (19) │ ui (15) │
└─────────────────────────────────────────────────────────┘
```

### CLI Commands

| Command | Description | Example |
|---|---|---|
| `chat-extract ingest <file>` | Ingest a single chat file (Phase 1) | `chat-extract ingest ~/chats/session.jsonl` |
| `chat-extract ingest --batch <dir>` | Batch ingest all chat files in a directory | `chat-extract ingest --batch ~/.claude/projects/` |
| `chat-extract filter <chat-id> --type <filter>` | Run a specific filter on a worksheeted chat | `chat-extract filter abc123 --type prd_consolidation` |
| `chat-extract filter <chat-id> --preset <name>` | Run a preset combination of filters | `chat-extract filter abc123 --preset "Full Extract"` |
| `chat-extract status` | Show the dashboard (key metrics + recent activity) | `chat-extract status` |
| `chat-extract search <query>` | Search across all worksheets by keyword | `chat-extract search "database schema"` |
| `chat-extract list [--status <status>]` | List chats with optional status filter | `chat-extract list --status worksheeted` |
| `chat-extract review <run-id>` | View a flagged filter run for manual review | `chat-extract review run-abc123` |
| `chat-extract tags` | List all tags with usage counts | `chat-extract tags` |
| `chat-extract tags add <tag>` | Add a new tag to the known tag list | `chat-extract tags add "performance"` |
| `chat-extract filters` | List available filter types | `chat-extract filters` |
| `chat-extract filters add <name>` | Add a new filter type (interactive setup) | `chat-extract filters add "Meeting Notes"` |
| `chat-extract reprocess --step <step> --since <date>` | Re-run a step on old chats with updated prompts | `chat-extract reprocess --step worksheet --since 2024-01-01` |
| `chat-extract cost [--month]` | Show API cost breakdown | `chat-extract cost --month` |
| `chat-extract init` | Initialize database and config | `chat-extract init` |

### Notification Thresholds

| Severity | Condition | Action |
|---|---|---|
| INFO | Chat worksheeted successfully, filter passed quality | Terminal output only. Logged to activity. |
| WARNING | Filter output flagged (confidence 4-6), unknown format encountered | Yellow highlight in terminal. Added to flagged queue. |
| CRITICAL | Database write failed, API key invalid, all retries exhausted | Red highlight in terminal. Processing paused. Immediate user attention needed. |

### Operator Actions

From the CLI, the operator can:
- Review and approve/reject flagged items
- Re-run any filter on any chat
- Add new filter types and tags
- Search across all worksheets
- Reprocess old chats with updated prompts
- View cost breakdown

### Done When

- [x] 5 key metrics defined
- [x] ASCII mockup exists
- [x] CLI commands listed with descriptions
- [x] Notification thresholds defined with severity levels
- [x] Dashboard answers "do I need to do anything?" at a glance

**Status: COMPLETE**

---

## Stage 7: Build Order

### Purpose

Turn the complete design into a construction plan. What gets built first, dependencies, file structure, module specs, MVP path.

---

### File Structure

```
chat-extractor/
├── chat_extractor/
│   ├── __init__.py
│   ├── cli.py                    # Click CLI entry point, all commands
│   ├── config.py                 # Config loading, paths, defaults
│   ├── db.py                     # SQLite connection, table creation, queries
│   ├── models.py                 # Pydantic models (Chat, Worksheet, Artifact, FilterRun)
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base.py               # Base parser interface
│   │   ├── claude_code.py        # JSONL parser for Claude Code sessions
│   │   ├── claude_ai.py          # JSON parser for Claude.ai exports
│   │   ├── markdown.py           # Markdown chat parser
│   │   └── raw_text.py           # Raw text fallback parser
│   ├── steps/
│   │   ├── __init__.py
│   │   ├── capture.py            # Step 1: format detection + parsing
│   │   ├── consolidate.py        # Step 2: speaker consolidation
│   │   ├── worksheet.py          # Step 3: AI worksheet generation
│   │   ├── categorize.py         # Step 4: save + auto-tag
│   │   ├── filter_select.py      # Step 5: filter selection + presets
│   │   ├── filter_execute.py     # Step 6: run filter against worksheet
│   │   ├── quality_check.py      # Step 7: validate output quality
│   │   └── save_artifact.py      # Step 8: save to file + DB
│   ├── filters/
│   │   ├── __init__.py
│   │   ├── registry.py           # Filter type registry (extensible)
│   │   ├── prd_consolidation.py  # PRD Consolidation filter
│   │   ├── knowledge_dump.py     # Knowledge Dump filter
│   │   ├── idea_cards.py         # Idea Cards filter
│   │   ├── tool_skill.py         # Tool/Skill Extractor filter
│   │   ├── checklist.py          # Checklist Builder filter
│   │   └── decision_log.py       # Decision Log filter
│   ├── ai.py                     # Claude API wrapper (retry, rate limit, cost tracking)
│   ├── display.py                # Rich terminal output (status dashboard, tables, progress)
│   └── search.py                 # Full-text search across worksheets
├── filters/                       # User-editable filter prompt templates (YAML/JSON)
│   ├── prd_consolidation.yaml
│   ├── knowledge_dump.yaml
│   ├── idea_cards.yaml
│   ├── tool_skill.yaml
│   ├── checklist.yaml
│   └── decision_log.yaml
├── data/
│   └── chat_extractor.db         # SQLite database (created by init)
├── tests/
│   ├── test_parsers.py
│   ├── test_consolidate.py
│   ├── test_worksheet.py
│   ├── test_filters.py
│   └── fixtures/
│       ├── sample_claude_code.jsonl
│       ├── sample_claude_ai.json
│       └── sample_raw.txt
├── setup.py
├── requirements.txt
└── README.md
```

### Dependency Graph

| Module | Depends On |
|---|---|
| `config.py` | Nothing |
| `models.py` | Nothing (Pydantic only) |
| `db.py` | config, models |
| `ai.py` | config (API key, rate limits) |
| `parsers/*` | models |
| `steps/capture.py` | parsers, db, models |
| `steps/consolidate.py` | models |
| `steps/worksheet.py` | ai, models |
| `steps/categorize.py` | ai, db, models |
| `steps/filter_select.py` | db, models, filters/registry |
| `steps/filter_execute.py` | ai, models, filters/registry |
| `steps/quality_check.py` | ai, models |
| `steps/save_artifact.py` | db, models, config |
| `filters/registry.py` | config (loads YAML templates) |
| `filters/*.py` | models, ai |
| `display.py` | db, models (reads status for dashboard) |
| `search.py` | db |
| `cli.py` | Everything (orchestrates all modules) |

### Build Phases

**Phase 1: Foundation** (independently testable)
- `config.py` — load config, paths, API key from env
- `models.py` — Pydantic models for Chat, Message, Worksheet, Artifact, FilterRun
- `db.py` — SQLite init, table creation, basic CRUD
- **Test:** `chat-extract init` creates database, tables exist, can insert/query a record

**Phase 2: Parsers** (independently testable)
- `parsers/base.py` — base interface
- `parsers/claude_code.py` — parse JSONL
- `parsers/claude_ai.py` — parse JSON export
- `parsers/raw_text.py` — parse raw text
- `parsers/markdown.py` — parse markdown chat
- `steps/capture.py` — format detection + dispatch to correct parser
- **Test:** Feed each sample fixture file, get back normalized Chat object with correct message count and speaker labels

**Phase 3: Core Pipeline (Phase 1 — Ingest)**
- `ai.py` — Claude API wrapper with retry, rate limiting, cost tracking
- `steps/consolidate.py` — speaker consolidation logic
- `steps/worksheet.py` — worksheet generation via Claude
- `steps/categorize.py` — auto-tagging via Haiku + DB save
- **Test:** `chat-extract ingest sample.jsonl` produces a worksheet in the database. Worksheet has summary, topics, decisions. Tags are suggested.

**Phase 4: Filter System (Phase 2 — Extract)**
- `filters/registry.py` — load filter definitions from YAML
- `filters/*.py` — 6 starting filters
- `filters/*.yaml` — prompt templates
- `steps/filter_select.py` — selection + presets
- `steps/filter_execute.py` — run filter against worksheet
- `steps/quality_check.py` — validation
- `steps/save_artifact.py` — save to file + DB
- **Test:** `chat-extract filter <id> --type idea_cards` produces idea card files in `docs/ideas/`. Quality score logged.

**Phase 5: Display & Search**
- `display.py` — Rich dashboard, status tables, progress bars
- `search.py` — full-text search across worksheet content
- **Test:** `chat-extract status` shows dashboard. `chat-extract search "database"` returns matching worksheets.

**Phase 6: CLI & Orchestration**
- `cli.py` — all commands wired together, batch mode, presets, reprocess
- **Test:** Full workflow: `chat-extract ingest file → chat-extract filter <id> --preset "Full Extract" → chat-extract status → chat-extract search "topic"`

### Module Specs (Key Functions)

**`ai.py`:**
- `call_claude(prompt: str, model: str = "sonnet", max_tokens: int = 4096, response_format: str = "json") -> dict` — core API call with retry (3x backoff), rate limiting (1.5s delay), cost tracking
- `get_cost_summary(period: str = "today") -> CostSummary` — return total cost for period

**`steps/worksheet.py`:**
- `generate_worksheet(conversation: Conversation, prompt_version: str = "v1") -> Worksheet` — send full conversation to Sonnet, parse structured worksheet response
- `split_and_merge(conversation: Conversation, max_tokens: int = 30000) -> Conversation[]` — split long conversations into overlapping chunks

**`steps/filter_execute.py`:**
- `execute_filter(worksheet: Worksheet, filter_type: str, filter_config: FilterConfig) -> FilterOutput` — load prompt template, inject worksheet content, call Claude, parse response

**`filters/registry.py`:**
- `get_filter(name: str) -> FilterConfig` — look up filter by name
- `list_filters() -> list[FilterConfig]` — list all available filters
- `register_filter(name: str, prompt_template: str, output_schema: dict, destination_pattern: str) -> None` — add new filter type
- `get_preset(name: str) -> list[str]` — return filter names for a preset

**`search.py`:**
- `search_worksheets(query: str, limit: int = 20) -> list[SearchResult]` — SQLite LIKE search across summary + topics + decisions fields

### MVP Path

1. `config.py` + `models.py` + `db.py` (foundation)
2. `parsers/claude_code.py` + `steps/capture.py` (just Claude Code format — the most painful gap)
3. `ai.py` + `steps/consolidate.py` + `steps/worksheet.py` (the core value — worksheet generation)
4. `steps/categorize.py` (save + basic tagging)
5. `cli.py` (minimal: `ingest` and `status` commands only)

**MVP is 5 modules.** Gets the user from "can't search Claude Code sessions" to "every chat is a structured, searchable worksheet." Phase 2 filters can come after MVP proves value.

### Output

- `total_files`: 28 source files + 6 filter templates + 3 test fixtures = 37 files
- `estimated_build_phases`: 6
- `mvp_path`: config → models → db → claude_code parser → capture → ai → consolidate → worksheet → categorize → minimal cli (5 modules, 10 files)

### Done When

- [x] Every file listed in the structure
- [x] Every module has dependencies listed
- [x] Build phases ordered and independently testable
- [x] Module specs include function signatures
- [x] MVP path defined and genuinely minimal

**Status: COMPLETE**

---

## Stage 8: Test Cases & Health Checks

### Purpose

Prove the system works with real data. Runnable tests, health checks, monitoring plan.

---

### Sample Test Case (Real Data)

**Input:** A Claude Code session JSONL file from `~/.claude/projects/default/sessions/` — pick a recent session where the user discussed database schema design for a project. File is approximately 150 messages, 25K tokens.

**Expected behavior at each step:**

1. **Capture:** Detects JSONL format. Parses into 150 messages with speaker labels (human/assistant). Source type = `claude_code`.
2. **Consolidation:** Merges consecutive same-speaker messages. Result: ~80 turns (alternating human/assistant). System/tool messages summarized.
3. **Worksheet:** Claude produces worksheet with:
   - Summary: ~100 words describing the database design discussion
   - Key topics: 3-5 topics (e.g., "table structure for chats," "indexing strategy," "migration approach")
   - Decisions: 2-3 decisions (e.g., "decided on SQLite over Supabase because local-first")
   - Open questions: 1-2 (e.g., "full-text search index approach TBD")
   - Tags: ["database", "architecture"]
4. **Save:** Worksheet saved to SQLite. Markdown file written to `data/worksheets/`. Tags auto-assigned with >80% confidence.

**Verification:** `chat-extract list` shows the chat with status `worksheeted`. `chat-extract search "database"` returns it. Markdown file exists at expected path. Database has worksheet record with non-empty topics_json.

### Testing Checklist

| # | Test | Command | Pass Criteria |
|---|---|---|---|
| 1 | Initialize database | `chat-extract init` | Database file created. All 5 tables exist. Tag seed data present. |
| 2 | Ingest Claude Code session | `chat-extract ingest ~/.claude/projects/default/sessions/<recent>.jsonl` | Status shows `worksheeted`. Worksheet has summary, >=1 topic, >=1 decision. |
| 3 | Ingest raw text | `echo "Human: hello\nAssistant: hi" \| chat-extract ingest --stdin` | Parsed as 2 messages. Worksheet generated (even if trivial). |
| 4 | Duplicate detection | Run same ingest command again | "Already processed (hash match)" message. No duplicate record. |
| 5 | Search worksheets | `chat-extract search "database"` | Returns the ingested chat if it discussed databases. Returns empty if not. |
| 6 | Run single filter | `chat-extract filter <id> --type idea_cards` | Idea card files created in `docs/ideas/`. Quality score >= 4. |
| 7 | Run preset | `chat-extract filter <id> --preset "Full Extract"` | 3 filter runs (Knowledge Dump + Idea Cards + Worksheet). All artifacts saved. |
| 8 | View status | `chat-extract status` | Dashboard renders with correct counts. Recent activity shows today's runs. |
| 9 | Trigger error — bad file | `chat-extract ingest /nonexistent/path.txt` | Error message: "File not found." No crash. Exit code 1. |
| 10 | Trigger error — empty file | `chat-extract ingest empty.txt` (0 bytes) | Warning: "Empty file, skipping." No database record created. |
| 11 | Quality flag | Manually create a filter run with confidence = 3 | Appears in flagged queue. `chat-extract review <id>` shows the output. |
| 12 | Add new filter | `chat-extract filters add "Meeting Notes"` | New filter appears in `chat-extract filters` list. Can be used in filter command. |
| 13 | Reprocess | `chat-extract reprocess --step worksheet --since 2026-01-01` | All matching chats re-worksheeted. prompt_version updated. |
| 14 | Cost tracking | `chat-extract cost` | Shows today's API cost. Matches approximate expected cost. |
| 15 | Batch ingest | `chat-extract ingest --batch ~/.claude/projects/default/sessions/` | Multiple chats processed. Status shows count. Failures logged but don't stop batch. |

### Health Checks

| Command | What It Checks | Healthy Looks Like |
|---|---|---|
| `chat-extract health` | Database connection, table integrity, API key validity, output directories exist | "All checks passed. DB: 247 chats. API: valid. Dirs: all exist." |
| `chat-extract health --db` | Database specifically: table count, row counts, integrity check | "5 tables. 247 chats, 245 worksheets, 892 artifacts. PRAGMA integrity_check: ok." |
| `chat-extract health --api` | Claude API key validity and rate limit status | "API key valid. Rate limit: 42/50 requests remaining this minute." |

### Ongoing Monitoring

| Check | Frequency | What to Look For |
|---|---|---|
| Flagged items queue | Daily | Any flagged items that need review. Target: <5% of filter runs flagged. |
| API cost | Weekly | Cost trending as expected. Spike could indicate runaway retries. |
| Database size | Monthly | SQLite file size. Should grow ~1MB per 100 chats. |
| Prompt quality | Weekly | Spot-check 2-3 worksheets against source chats. Are key points captured? |
| Error log | Weekly | Any recurring errors (format parsing failures, API timeouts). |

### Regression Tests

| Change Type | What to Re-Test |
|---|---|
| Worksheet prompt updated | Re-run test #2. Compare new worksheet against old for same chat. Key topics should be equal or better. |
| New filter type added | Run test #12 (add filter) + test #6 (run filter) with new type. Verify output format matches schema. |
| Parser updated | Re-run test #2 with the source format that changed. Verify message count and speaker labels unchanged. |
| Quality threshold changed | Run test #11 with new threshold. Verify items correctly bucketed into pass/flag/retry. |
| Database schema changed | Run `chat-extract health --db`. Run tests #1-5 on a fresh database. |

### Done When

- [x] Sample test uses real data (actual Claude Code session file)
- [x] Testing checklist is runnable by someone who didn't build the system
- [x] Every test has clear pass/fail criteria
- [x] Health checks cover database, API, and system status
- [x] Regression strategy exists for prompt changes, threshold changes, new filters

**Status: COMPLETE**

---

## Gap Analysis (Final Pass)

### Purpose

Full 18-point sweep across everything captured in Stages 0-8. Quality gate before generating the final CLAUDE.md.

---

### 18-Point Checklist

| # | Gap | Covered? | Where | Notes |
|---|---|---|---|---|
| 1 | Multi-phase structure | YES | Stage 0 (2 phases), Stage 1 (mapped separately), Stage 2 (decomposed per phase) | Ingest + Filter/Extract. Phases independent after worksheet handoff. |
| 2 | Repeating steps | YES | Stage 2, Step 6 | Filter Execution repeats per selected filter. Controlled by user choice. |
| 3 | Extensible options | YES | Stage 2, Steps 1/5/6/8/12 | Format parsers, filter types, tags, destination patterns — all extensible. Filter registry pattern. |
| 4 | Presets | YES | Stage 2, Q14 | 3 presets: Quick Capture, Full Extract, PRD Mode. |
| 5 | Cross-item batch/merge | YES | Stage 2, Q13 | Batch ingest. PRD Consolidation merges multiple worksheets. |
| 6 | API keys/credentials | YES | Stage 4 | Only ANTHROPIC_API_KEY. Step-by-step instructions provided. |
| 7 | Dependencies | YES | Stage 4 | Python 3.11+, 4 packages with versions, all stdlib dependencies listed. |
| 8 | Cost-per-run | YES | Stage 4 | Itemized: ~$0.06/chat with 3 filters. ~$9/month at 5 chats/day. |
| 9 | Rate limits | YES | Stage 4 | 50 req/min, 40K tokens/min. Sequential with 1.5s delay. Backoff strategy. |
| 10 | Prerequisites | YES | Stage 4 | 6 steps in order, all one-time. |
| 11 | Prompt templates | YES | Stage 3 | Every AI step has prompt skeleton with task, format, model, example. Filter prompts detailed. |
| 12 | User interaction | YES | Stage 6 | CLI commands with 15 commands defined. Dashboard mockup. |
| 13 | Data retention | YES | Stage 5 | Raw data: forever. Results: forever. No cleanup needed at this scale. PII flag documented. |
| 14 | Output quality | YES | Stage 5 | Quality gates per step. Confidence scoring. Pass/flag/retry thresholds. |
| 15 | Versioning/reprocessing | YES | Stage 5 | Worksheets: overwrite with prompt_version. Artifacts: append. `reprocess` CLI command defined. |
| 16 | Sample test case | YES | Stage 8 | Real Claude Code session JSONL file. Expected behavior at each step. 15 numbered test commands. |
| 17 | Rollback/undo | YES | Stage 5 | All steps idempotent or append-only. Old artifacts preserved. Re-run any step safely. |
| 18 | Access control | YES | Stage 0 | Solo operator. No multi-user access needed. N/A for this system. |

### Process-Specific Gaps (Beyond the 18)

| # | Gap | Status | Notes |
|---|---|---|---|
| 19 | Self-improvement loop | NOTED | The "Panning for Gold" reference skill has a Phase 4: "did I miss anything?" after each extraction. Worth adopting — after worksheet generation, run a second pass asking "what did the first pass miss?" Not in MVP but should be in the filter prompt templates as an optional second-pass instruction. |
| 20 | Cross-chat linking | NOTED | When multiple chats discuss the same topic, the system should suggest "these 3 chats may be related" based on overlapping tags/topics. Not in MVP but the tag system supports it. Query: `SELECT * FROM worksheets WHERE tags LIKE '%architecture%' ORDER BY created_at`. |

### Output

- `coverage_score`: 18/18
- `rating`: **COMPLETE**
- `new_gaps_discovered`: 2 (self-improvement loop, cross-chat linking — both deferred to post-MVP)
- `actions_required`: None blocking. Proceed to Stage 10.

**Status: COMPLETE — 18/18. Proceed to Stage 10.**

---

## Stage 10: CLAUDE.md Generator

### Purpose

This stage renders everything from Stages 0-8 into a self-contained CLAUDE.md build file. The output of this stage IS the build file. For this POC document, we document readiness — the actual CLAUDE.md generation happens as a separate deliverable when the user is ready to build.

### Readiness Assessment

Every section of the CLAUDE.md template has source material:

| CLAUDE.md Section | Source Stage | Ready? |
|---|---|---|
| Mission | Stage 0 (process name, pain points, phase structure) | YES |
| API Keys Required | Stage 4 (ANTHROPIC_API_KEY, setup walkthrough) | YES |
| Tech Stack | Stage 4 (Python 3.11+, 4 packages) | YES |
| Database Schema | Stage 4 (5 tables, full SQL, indexes, seed data) | YES |
| Pipeline Architecture | Stage 1 (architecture diagram) + Stage 6 (CLI commands) | YES |
| File Structure | Stage 7 (37 files, exact tree) | YES |
| Module Specifications | Stages 2, 3, 7 (function signatures, prompts, logic) | YES |
| Rules | Stages 3, 5 (rate limits, quality gates, error handling) | YES |
| Dashboard | Stage 6 (ASCII mockup, CLI commands, thresholds) | YES |
| Testing Checklist | Stage 8 (15 tests with real data, health checks) | YES |
| Build Order | Stage 7 (6 phases, MVP path, dependency graph) | YES |

### What the CLAUDE.md Would Contain

When generated, the build file will be approximately 500-700 lines and include:
- Mission statement (what and why)
- `.env` template with `ANTHROPIC_API_KEY`
- Full dependency list with versions
- Complete SQLite schema (5 tables + indexes + seed data)
- Architecture diagram from Stage 1
- File tree (37 files)
- Module specs for every file with function signatures, imports, error handling
- All 6 filter prompt templates
- Numbered rules (rate limits, quality gates, retry logic, save-incrementally)
- ASCII dashboard mockup + all 15 CLI commands
- 15-step testing checklist with real test data
- 6 build phases with test criteria per phase

### Done When

- [x] Every section has source material ready
- [x] No "figure it out later" sections
- [x] Build order lets developers test as they go
- [x] Testing checklist uses real data

**Status: COMPLETE — Ready for CLAUDE.md generation on demand.**

---

## Summary

| Stage | Status | Key Output |
|---|---|---|
| 0: Process Capture | COMPLETE | 2-phase system (Ingest + Filter), 5 pain points, CLI interaction, solo operator |
| 1: 6-Step Mapping | COMPLETE | Architecture diagram, SQLite state, on-demand schedule, per-phase mapping |
| 2: Step Decomposition | COMPLETE | 8 steps fully decomposed (4 per phase), 3 presets, MVP = worksheet generation |
| Gap Analysis (Early) | COMPLETE | 0 showstoppers, all structural gaps covered |
| 3: Automation Classification | COMPLETE | 3 deterministic, 2 AI-driven, 2 hybrid, 1 human. ~$0.06/run |
| 4: Environment Setup | COMPLETE | Python 3.11+, 4 packages, 1 API key, SQLite, ~$9/month |
| 5: Error Handling | COMPLETE | Error matrix (12 failure modes), quality gates, cascade rules, data retention |
| 6: Dashboard Design | COMPLETE | 5 metrics, ASCII dashboard, 15 CLI commands, 3 severity levels |
| 7: Build Order | COMPLETE | 37 files, 6 build phases, MVP = 10 files (5 modules), dependency graph |
| 8: Test Cases | COMPLETE | 15 test commands, 3 health checks, 5 monitoring items, regression strategy |
| Gap Analysis (Final) | COMPLETE | 18/18 covered. 2 post-MVP gaps noted (self-improvement loop, cross-chat linking) |
| 10: CLAUDE.md Generator | COMPLETE | All sections have source material. Ready for generation on demand. |

**This system is fully designed and ready to build.** The MVP (5 modules, 10 files) delivers the highest-value capability — turning unsearchable Claude Code sessions into structured, searchable worksheets. Phase 2 filters add extraction power incrementally.
