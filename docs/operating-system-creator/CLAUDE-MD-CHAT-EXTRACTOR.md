# Chat Extractor — CLAUDE.md Build File

> **What this is:** Drop this file as CLAUDE.md into a project folder, run `claude`, and it builds the complete chat extraction system. This was produced BY the Operating System Creator framework as a proof of concept.

---

## Mission

Build a Node.js CLI system that captures Claude chats and extracts structured knowledge from them. The system operates in two phases: Phase 1 (Ingest) parses any chat into a standardized AI-generated worksheet. Phase 2 (Extract) applies extensible extraction filters — PRD consolidation, knowledge dumps, idea cards, tool extraction, checklists, decision logs — to worksheeted chats on demand. Everything is local: SQLite database, markdown file output, Claude API for AI processing. No cloud dependencies beyond the Anthropic API.

---

## API Keys Required

```
# .env file
ANTHROPIC_API_KEY=your-key-here
```

### How to get the key:

**Anthropic API:** Go to https://console.anthropic.com → API Keys → Create Key. Copy the key that starts with `sk-ant-`. You need a funded account — add credits at Settings → Billing. Haiku calls cost fractions of a cent; Sonnet costs more but is only used for complex filters.

That is the only external dependency. Everything else is local.

---

## Tech Stack

```json
{
  "dependencies": {
    "better-sqlite3": "^11.0.0",
    "@anthropic-ai/sdk": "^0.30.0",
    "commander": "^12.0.0",
    "cli-table3": "^0.6.0",
    "dotenv": "^16.0.0",
    "chalk": "^4.1.0"
  }
}
```

Runtime: Node.js 20+

**Why these choices:**
- `better-sqlite3`: Synchronous SQLite — no async complexity, no server, single file database. Perfect for a local CLI tool.
- `@anthropic-ai/sdk`: Official Anthropic SDK for Claude API calls (Haiku for worksheets, Sonnet for complex analysis).
- `commander`: Standard CLI framework — subcommands, flags, help text.
- `cli-table3`: Terminal table formatting for status displays.
- `chalk`: Terminal color output (use v4 for CommonJS compatibility with Node 20).

---

## Database Schema

The database file is created at `db/chat-extractor.db` on first run. Create these tables in `db/init.js`:

```sql
-- Raw chat storage
CREATE TABLE IF NOT EXISTS chats (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT,
  source TEXT NOT NULL,            -- 'claude_ai', 'claude_code', 'autoforge', 'manual'
  raw_content TEXT NOT NULL,
  format TEXT NOT NULL,            -- 'json', 'markdown', 'text'
  message_count INTEGER,
  content_hash TEXT UNIQUE,        -- SHA-256 of raw_content for deduplication
  imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  status TEXT DEFAULT 'raw'        -- 'raw', 'parsed', 'worksheeted', 'error'
);

-- Parsed messages (individual turns extracted from chat)
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
  speaker TEXT NOT NULL,           -- 'human', 'assistant', 'system'
  content TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  timestamp TEXT,                  -- if available from source
  UNIQUE(chat_id, sequence)
);

-- Worksheets (Phase 1 output — structured summary of each chat)
CREATE TABLE IF NOT EXISTS worksheets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chat_id INTEGER NOT NULL REFERENCES chats(id) UNIQUE,
  summary TEXT NOT NULL,
  key_topics_json TEXT NOT NULL,   -- [{topic, subtopics, details}]
  decisions_json TEXT NOT NULL,    -- [{decision, reasoning, context}]
  artifacts_json TEXT NOT NULL,    -- [{type, description, location_in_chat}]
  open_questions_json TEXT,        -- [{question, context}]
  urls_json TEXT,                  -- [{url, context}]
  category TEXT,                   -- auto-categorized topic
  tags_json TEXT,                  -- ["tag1", "tag2"]
  confidence REAL,                 -- categorization confidence 0-1
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Filter types (extensible registry — each filter is a different extraction lens)
CREATE TABLE IF NOT EXISTS filter_types (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,       -- 'prd_consolidation', 'knowledge_dump', etc.
  display_name TEXT NOT NULL,      -- 'PRD Consolidation'
  description TEXT,
  prompt_template TEXT NOT NULL,   -- Full prompt with {{placeholders}}
  output_format TEXT NOT NULL,     -- 'markdown', 'json', 'checklist'
  output_destination TEXT,         -- target dir: 'docs/ideas/', 'docs/page-prds/', etc.
  model TEXT DEFAULT 'haiku',      -- 'haiku' or 'sonnet'
  active INTEGER DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Extraction results (Phase 2 output — what each filter produced)
CREATE TABLE IF NOT EXISTS extractions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  worksheet_id INTEGER NOT NULL REFERENCES worksheets(id),
  filter_type_id INTEGER NOT NULL REFERENCES filter_types(id),
  output_content TEXT NOT NULL,
  output_file_path TEXT,           -- where the artifact was saved on disk
  quality_score REAL,              -- 0-1 from quality check
  status TEXT DEFAULT 'pending',   -- 'pending', 'complete', 'failed', 'flagged'
  attempts INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(worksheet_id, filter_type_id)
);

-- Presets (saved combinations of filters for quick reuse)
CREATE TABLE IF NOT EXISTS presets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  filter_type_ids_json TEXT NOT NULL,  -- [1, 2, 3]
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Processing queue (tracks what needs to be done and what failed)
CREATE TABLE IF NOT EXISTS queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chat_id INTEGER REFERENCES chats(id),
  worksheet_id INTEGER REFERENCES worksheets(id),
  phase TEXT NOT NULL,             -- 'ingest' or 'extract'
  filter_type_id INTEGER REFERENCES filter_types(id),
  preset_id INTEGER REFERENCES presets(id),
  status TEXT DEFAULT 'pending',   -- 'pending', 'processing', 'complete', 'failed'
  error_message TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME
);

-- API usage tracking (cost monitoring)
CREATE TABLE IF NOT EXISTS api_usage (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  model TEXT NOT NULL,             -- 'haiku' or 'sonnet'
  input_tokens INTEGER NOT NULL,
  output_tokens INTEGER NOT NULL,
  cost_usd REAL NOT NULL,
  purpose TEXT,                    -- 'worksheet', 'categorize', 'filter:knowledge_dump', etc.
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Pipeline Architecture

```
PHASE 1: INGEST (every chat, automatic)
==============================================

  [Chat Input] ──> [Detect Format] ──> [Parse Messages] ──> [Consolidate Speakers]
   (file/paste/      (JSON/MD/TXT)      (split into turns)   (merge consecutive,
    directory/                                                  normalize names)
    auto-detect)
                                              |
                                              v
                                    [AI Worksheet Gen] ──> [Auto-Categorize] ──> [Save to DB]
                                     (Claude Haiku)         (Claude Haiku)
                                     - summary
                                     - key topics
                                     - decisions
                                     - artifacts
                                     - open questions
                                     - URLs

  Status progression: raw --> parsed --> worksheeted
  On error at any step: status --> error (with message), other chats unaffected


PHASE 2: EXTRACT (on demand, user-triggered)
==============================================

  [Select Worksheets] ──> [Select Filters] ──> [Execute Each Filter]
   (by ID, --all,          (by name, or         (build prompt from template,
    --batch)                use a preset)        inject worksheet data,
                                                  call Claude with correct model)
                                    |
                                    v
                            [Quality Check] ──> pass ──> [Save Artifact]
                             (min length,                  (markdown file with
                              format check,                 frontmatter, to the
                              similarity check)             filter's target dir)
                                    |
                                    v fail
                            [Retry up to 3x] ──> still fail ──> [Mark as Failed]

  Available Filters (extensible — add more via CLI):
  +---------------------------+----------+----------------------------+
  | Filter                    | Model    | Output Directory           |
  +---------------------------+----------+----------------------------+
  | PRD Consolidation         | Sonnet   | docs/page-prds/            |
  | Knowledge Dump            | Haiku    | knowledge/                 |
  | Idea Cards                | Haiku    | docs/ideas/                |
  | Tool/Skill Extractor      | Sonnet   | skills/                    |
  | Checklist Builder         | Haiku    | checklists/                |
  | Decision Log              | Haiku    | decisions/                 |
  +---------------------------+----------+----------------------------+

  Presets (saved filter combos):
  - "Quick Capture"  → worksheet only (no extraction)
  - "Full Extract"   → knowledge + ideas + worksheet
  - "PRD Mode"       → PRD consolidation + decisions
```

### CLI Commands

```bash
# Phase 1: Ingest
chat-extractor ingest <file>           # Ingest a single chat file
chat-extractor ingest --paste          # Paste chat content interactively via stdin
chat-extractor ingest --dir <path>     # Batch ingest all chats in a directory
chat-extractor ingest --auto           # Auto-detect new chats from known source dirs

# Phase 2: Extract
chat-extractor extract <chat-id> --filters prd,knowledge,ideas   # Specific filters
chat-extractor extract <chat-id> --preset "Full Extract"         # Use a preset
chat-extractor extract --all --filters knowledge                 # All worksheeted chats
chat-extractor extract --batch 1,2,3 --preset "PRD Mode"        # Batch specific IDs

# Filter Management
chat-extractor filters list              # List all filter types (active and inactive)
chat-extractor filters add <name>        # Add a new filter type (interactive prompts)
chat-extractor filters edit <name>       # Edit an existing filter's prompt template
chat-extractor filters remove <name>     # Deactivate a filter (soft delete)

# Presets
chat-extractor presets list              # List all presets with their filter combos
chat-extractor presets create <name>     # Create a new preset (interactive)
chat-extractor presets run <name> <ids>  # Run preset on specific chat IDs

# Status & Search
chat-extractor status                    # System overview dashboard
chat-extractor list                      # List all chats with status column
chat-extractor search <query>            # Full-text search across all worksheets
chat-extractor show <chat-id>            # Display the worksheet for a specific chat
chat-extractor health                    # System health check (DB, API key, dirs)

# Export
chat-extractor export <chat-id>         # Export all extractions for one chat
chat-extractor export --all             # Export everything to a single directory

# Init (first run)
chat-extractor init                      # Create database, seed default filters/presets
```

---

## File Structure

```
chat-extractor/
├── package.json
├── .env                          (ANTHROPIC_API_KEY — not committed)
├── CLAUDE.md                     (this file)
├── db/
│   ├── init.js                   (database initialization + schema creation + seeding)
│   └── chat-extractor.db         (SQLite database — created at runtime, gitignored)
├── src/
│   ├── cli.js                    (Commander.js CLI entry point — all commands wired here)
│   ├── config.js                 (env vars, constants, paths, model names)
│   ├── ingest/
│   │   ├── capture.js            (chat capture: file read, stdin paste, directory scan)
│   │   ├── parse.js              (format detection + message extraction)
│   │   ├── consolidate.js        (speaker normalization + consecutive message merging)
│   │   └── worksheet.js          (AI worksheet generation + auto-categorization)
│   ├── extract/
│   │   ├── filter-registry.js    (load/manage/seed filter types from DB)
│   │   ├── filter-executor.js    (run one or more filters against a worksheet)
│   │   ├── quality-check.js      (validate extraction output before saving)
│   │   └── save-artifact.js      (write extraction to markdown file with frontmatter)
│   ├── filters/
│   │   ├── prd-consolidation.js  (PRD filter: prompt, config, output settings)
│   │   ├── knowledge-dump.js     (knowledge dump filter)
│   │   ├── idea-cards.js         (idea card extraction filter)
│   │   ├── tool-extractor.js     (tool/skill extraction filter)
│   │   ├── checklist-builder.js  (checklist extraction filter)
│   │   └── decision-log.js       (decision log extraction filter)
│   ├── presets/
│   │   └── defaults.js           (default preset definitions: Quick Capture, Full Extract, PRD Mode)
│   ├── queue/
│   │   └── processor.js          (queue processing loop with retry logic)
│   └── utils/
│       ├── claude.js             (Claude API wrapper: Haiku/Sonnet, rate limiting, cost tracking)
│       ├── file-output.js        (markdown file writer with frontmatter generation)
│       └── logger.js             (structured logging with timestamps and levels)
├── output/                       (default output root — subdirs created per filter type)
│   ├── knowledge/
│   ├── checklists/
│   ├── decisions/
│   ├── skills/
│   ├── docs/
│   │   ├── ideas/
│   │   └── page-prds/
│   └── exports/
└── test/
    ├── sample-chat.md            (real test chat for verification — human/assistant turns)
    └── batch/                    (directory for batch ingest testing)
```

---

## Module Specifications

### src/config.js

- Load `.env` with dotenv at the top
- Validate `ANTHROPIC_API_KEY` exists — exit with clear error message if missing
- Export constants:
  - `DB_PATH`: `path.join(__dirname, '..', 'db', 'chat-extractor.db')`
  - `ANTHROPIC_API_KEY`: from env
  - `HAIKU_MODEL`: `'claude-haiku-4-20250414'`
  - `SONNET_MODEL`: `'claude-sonnet-4-20250514'`
  - `MAX_RETRIES`: `3`
  - `RETRY_DELAY_MS`: `2000`
  - `QUALITY_THRESHOLD`: `0.6`
  - `RATE_LIMIT_HAIKU`: `10` (requests per minute)
  - `RATE_LIMIT_SONNET`: `5` (requests per minute)
  - `OUTPUT_DIRS`: `{ ideas: 'output/docs/ideas/', prds: 'output/docs/page-prds/', knowledge: 'output/knowledge/', checklists: 'output/checklists/', decisions: 'output/decisions/', skills: 'output/skills/', exports: 'output/exports/' }`

### db/init.js

- Opens or creates the SQLite database at `DB_PATH` using better-sqlite3
- Runs all `CREATE TABLE IF NOT EXISTS` statements from the schema above
- Calls `seedDefaultFilters()` from `src/extract/filter-registry.js` to insert the 6 default filter types if they don't exist
- Calls `seedDefaultPresets()` from `src/presets/defaults.js` to insert the 3 default presets if they don't exist
- Export: `getDb()` function that returns the open database connection (singleton pattern — create once, reuse)

### src/utils/logger.js

- Function: `log(level, message, data?)` — logs `[TIMESTAMP] [LEVEL] message` to console
  - Levels: `info` (white), `success` (green), `warn` (yellow), `error` (red)
  - If `data` is provided, JSON.stringify it on the next line
- Function: `logApi(model, inputTokens, outputTokens, purpose)` — logs API call and writes to `api_usage` table
  - Cost calculation: Haiku input $0.25/M tokens, output $1.25/M tokens. Sonnet input $3/M tokens, output $15/M tokens.
- Use `chalk` for coloring

### src/utils/claude.js

- Create Anthropic client using the SDK
- Track last call time per model for rate limiting
- Function: `callClaude(prompt, options?)` → `{ content, inputTokens, outputTokens, model }`
  - `options.model`: `'haiku'` (default) or `'sonnet'` — maps to actual model IDs from config
  - `options.maxTokens`: default 4096
  - `options.system`: optional system prompt
  - Before each call: check time since last call for that model. If under the rate limit interval (`60000 / RATE_LIMIT_*` ms), wait the difference.
  - After each call: log usage via `logApi()`
  - On error: retry up to `MAX_RETRIES` with `RETRY_DELAY_MS` backoff (double delay each retry). On final failure, throw with descriptive error.
  - Returns the text content from the response plus token counts.

### src/utils/file-output.js

- Function: `writeMarkdownFile(filePath, content, frontmatter)` → `filePath`
  - `frontmatter`: object with keys like `source_chat_id`, `filter`, `date`, `quality_score`
  - Renders YAML frontmatter block at top of file (`---\nkey: value\n---\n`)
  - Creates parent directories if they don't exist (`fs.mkdirSync` with `recursive: true`)
  - Writes the file
  - Returns the absolute file path
- Function: `generateFilename(chatTitle, filterName, date)` → string
  - Slugifies chat title (lowercase, spaces to hyphens, strip special chars, max 50 chars)
  - Format: `{slug}--{filterName}--{YYYY-MM-DD}.md`

### src/ingest/capture.js

- `captureFromFile(filePath)` → `{ rawContent, format, source }` — reads file, detects format, infers source from path ('claude_code', 'autoforge', or 'manual')
- `captureFromPaste()` → `{ rawContent, format, source: 'manual' }` — reads stdin until EOF, detects format
- `captureFromDirectory(dirPath)` → array — reads all `.md`, `.txt`, `.json` in directory (non-recursive), skips failures with warning
- `autoDetectNewChats(knownDirs)` → array — scans known dirs, computes SHA-256 of each file, skips already-imported (by content_hash in DB)

### src/ingest/parse.js

- `detectFormat(rawContent)` → `'json' | 'markdown' | 'text'`
  - JSON: starts with `{` or `[` and valid JSON. Markdown: contains `## Human`, `**Human:**`, etc. Otherwise: text.

- `parseChat(rawContent, format)` → `{ messages: [{ speaker, content, sequence, timestamp? }], title? }`
  - JSON: expects `{ messages: [...] }` or flat array. Handles `role`/`speaker`/`author` field variations.
  - Markdown: splits on heading/bold speaker markers (`## Human`, `### Assistant`, `**Human:**`, `**Claude:**`)
  - Text: splits on line-start labels (`Human:`, `Assistant:`, `User:`, `Claude:`, `System:`)
  - All formats: assign incrementing sequence from 1. Extract title if detectable.
  - Graceful fallback: if no messages parsed, return entire content as single assistant message.

### src/ingest/consolidate.js

- `consolidateSpeakers(messages)` → `{ messages, systemMessages }`
  - Normalize: user/Human/User/person → `'human'`, Claude/claude/AI/ai/bot → `'assistant'`, System → `'system'`
  - Merge consecutive same-speaker messages with `\n\n` separator
  - Strip system messages to separate array. Re-sequence so numbers are contiguous (1, 2, 3...).

### src/ingest/worksheet.js

- `generateWorksheet(messages, chatMetadata)` → `WorksheetObject`
  - Formats messages as: `[Speaker] (Turn N):\n{content}\n---`
  - Calls Claude Haiku with system prompt instructing it to return JSON with these fields:
    - `summary`: 2-3 sentence summary
    - `key_topics`: array of `{ topic, subtopics[], details }`
    - `decisions`: array of `{ decision, reasoning, context (early/middle/late) }`
    - `artifacts`: array of `{ type (code|schema|diagram|list|config|prompt|other), description, location_in_chat }`
    - `open_questions`: array of `{ question, context }`
    - `urls`: array of `{ url, context }`
  - Prompt must say: "Return ONLY valid JSON. Be thorough. Empty array if no items."
  - If JSON parsing fails, retry once asking Claude to fix the JSON.

- `categorizeWorksheet(worksheetSummary, keyTopics)` → `{ category, tags, confidence }`
  - Calls Claude Haiku with summary + topics
  - Categories: Architecture, Feature Design, Debugging, Research, Strategy, Setup, Brainstorming
  - Returns: one category, up to 5 tags, confidence 0-1
  - If confidence > 0.8: auto-apply. If <= 0.8: save but add `needs_review` tag.

### src/extract/filter-registry.js

- Function: `getActiveFilters()` → `FilterType[]`
  - Query: `SELECT * FROM filter_types WHERE active = 1`
  - Returns array of filter type objects

- Function: `getFilter(name)` → `FilterType | null`
  - Query: `SELECT * FROM filter_types WHERE name = ? AND active = 1`

- Function: `registerFilter(name, displayName, description, promptTemplate, outputFormat, outputDestination, model)` → `FilterType`
  - INSERT into filter_types table
  - Returns the created record

- Function: `updateFilterPrompt(name, newPromptTemplate)` → `void`
  - UPDATE filter_types SET prompt_template = ? WHERE name = ?

- Function: `deactivateFilter(name)` → `void`
  - UPDATE filter_types SET active = 0 WHERE name = ?

- Function: `seedDefaultFilters()` → `void`
  - Uses INSERT OR IGNORE to insert the 6 default filter types
  - Imports prompt templates from `src/filters/*.js`
  - Only inserts if the filter name doesn't already exist (idempotent)

### src/extract/filter-executor.js

- Function: `executeFilter(worksheet, filterType)` → `{ content, format }`
  - Builds the prompt by replacing placeholders in `filterType.prompt_template`:
    - `{{worksheet_summary}}` → `worksheet.summary`
    - `{{key_topics}}` → JSON.stringify(worksheet.key_topics_json)
    - `{{decisions}}` → JSON.stringify(worksheet.decisions_json)
    - `{{artifacts}}` → JSON.stringify(worksheet.artifacts_json)
    - `{{open_questions}}` → JSON.stringify(worksheet.open_questions_json)
    - `{{urls}}` → JSON.stringify(worksheet.urls_json)
    - `{{category}}` → worksheet.category
    - `{{tags}}` → worksheet.tags_json
  - Calls Claude with the appropriate model (`filterType.model`)
  - Returns the raw extraction content and the filter's output format

- Function: `executeFilters(worksheet, filterTypes)` → `[{ filterType, content, format, error? }]`
  - Runs filters **sequentially** (not parallel — respect rate limits)
  - Logs progress: `"Running filter 2/6: Knowledge Dump..."`
  - If one filter fails after all retries, log error and continue with next filter
  - Returns results array including any errors

### src/extract/quality-check.js

- `checkQuality(content, filterType)` → `{ score, passed, issues }`
  - Three weighted checks, each producing 0-1 partial score:
  - **Length** (0.3 weight): minimum chars vary by filter — PRD: 500, Knowledge: 300, Ideas: 100, Tool: 200, Checklist: 150, Decision: 200
  - **Format** (0.4 weight): markdown needs `#` headers + body text, checklists need `- [ ]` checkboxes, JSON must parse
  - **Originality** (0.3 weight): substring overlap vs worksheet summary — >80% overlap = 0 (just copied), <30% = full credit, linear between
  - Sum all three. `passed = score >= QUALITY_THRESHOLD` (0.6). Returns score, pass/fail, issues list.

### src/extract/save-artifact.js

- Function: `saveArtifact(content, filterType, chatMetadata, qualityScore)` → `filePath`
  - Determines output directory from `filterType.output_destination` (resolved against OUTPUT_DIRS)
  - Generates filename using `generateFilename()` from file-output.js
  - Builds frontmatter:
    ```yaml
    source_chat_id: 47
    source_chat_title: "PRD Maker Session"
    filter: prd_consolidation
    model: sonnet
    quality_score: 0.85
    extracted_at: 2026-04-13T10:30:00Z
    ```
  - Calls `writeMarkdownFile()` from file-output.js
  - Updates the `extractions` table with `output_file_path` and `status = 'complete'`
  - Returns the file path

### src/filters/*.js — Default Filter Definitions

Each filter file exports: `PROMPT_TEMPLATE`, `OUTPUT_FORMAT`, `OUTPUT_DESTINATION`, `MODEL`, `DISPLAY_NAME`, `DESCRIPTION`.

All prompts receive worksheet data via placeholders: `{{worksheet_summary}}`, `{{key_topics}}`, `{{decisions}}`, `{{artifacts}}`, `{{open_questions}}`, `{{urls}}`, `{{category}}`, `{{tags}}`. Each prompt ends with the WORKSHEET DATA block injecting the relevant placeholders.

**prd-consolidation.js** (Sonnet, markdown, docs/page-prds/)
- Role: PRD consolidation expert
- Key rule: Examine decisions CHRONOLOGICALLY — later supersedes earlier. BUT scan early messages for diagrams, architecture concepts, naming conventions, ideas mentioned once and never contradicted. Forward-pull early insights with [Early Insight] tag.
- Output sections: Overview, Requirements, Architecture, Decisions (final state), Open Items
- No changelog or history — current state only
- Uses: summary, topics, decisions, artifacts, open_questions

**knowledge-dump.js** (Haiku, markdown, knowledge/)
- Role: Knowledge extraction specialist
- Key rule: Extract EVERY fact, technique, reference, concept. No superseding logic — everything is useful.
- Categorize into: Technical (code, APIs), Strategic (business), Conceptual (mental models), Reference (links, docs)
- Include context for each item (why discussed, what problem it addresses)
- Uses: summary, topics, decisions, artifacts, urls

**idea-cards.js** (Haiku, markdown, docs/ideas/)
- Role: Idea spotter
- Key rule: Find half-formed concepts, "what if" statements, tabled suggestions, tangential ideas, "someday" features
- Per idea card: title, potential (Low/Medium/High), description (1-3 sentences), related topics, source context
- Look for prefixes: "what if", "we could", "maybe", "eventually", "it would be cool if"
- Uses: summary, topics, open_questions, artifacts

**tool-extractor.js** (Sonnet, markdown, skills/)
- Role: Process automation analyst
- Key rule: Identify processes that could become automated tools
- Per tool: name, what it does, inputs, outputs, complexity (Simple/Medium/Complex)
- Map to 6-step pattern: INPUT, PROCESS, OUTPUT, STATE, NOTIFY, SCHEDULE
- Uses: summary, topics, decisions, artifacts

**checklist-builder.js** (Haiku, checklist, checklists/)
- Role: Checklist builder
- Key rule: Find step-by-step instructions, procedures, setup guides, sequential processes
- Output: `- [ ] Step N: Description` checkbox format, grouped by topic, with prerequisites
- Sub-steps are indented
- Uses: summary, topics, decisions, artifacts

**decision-log.js** (Haiku, markdown, decisions/)
- Role: Decision documentation specialist
- Key rule: Extract every decision point in CHRONOLOGICAL order
- Per decision: what was decided, alternatives considered, reasoning, context (early/middle/late), reversed? (yes/no + reference), confidence level
- Mark reversals — reference which later decision superseded it
- Uses: summary, decisions, topics, open_questions

### src/presets/defaults.js

- Function: `seedDefaultPresets(db)` → `void`
  - Uses INSERT OR IGNORE (idempotent)
  - Default presets:
    1. **"Quick Capture"**: `filter_type_ids_json = []` — worksheet only, no extraction filters. Used when you just want the chat indexed and searchable.
    2. **"Full Extract"**: `filter_type_ids_json` = IDs for `knowledge_dump`, `idea_cards`, `decision_log`. The standard knowledge capture combo.
    3. **"PRD Mode"**: `filter_type_ids_json` = IDs for `prd_consolidation`, `decision_log`. For conversations that were about building something specific.
  - Looks up filter IDs by name at seed time (query filter_types table)

### src/queue/processor.js

- Function: `processQueue()` → `{ processed, failed, skipped }`
  - Query all pending queue entries ordered by `created_at ASC`
  - For each entry:
    - Set `status = 'processing'`
    - If `phase = 'ingest'`: run the ingest pipeline (parse → consolidate → worksheet → categorize)
    - If `phase = 'extract'`: load the worksheet, load the filter type, run filter-executor, quality-check, save-artifact
    - On success: set `status = 'complete'`, `completed_at = now()`
    - On failure: increment `attempts`. If `attempts < MAX_RETRIES`, set `status = 'pending'` (will retry on next run). If `attempts >= MAX_RETRIES`, set `status = 'failed'` with `error_message`.
  - Returns counts of processed, failed, and skipped entries.

- Function: `enqueueIngest(chatId)` → `queueId`
  - Insert a new queue entry with `phase = 'ingest'`, `chat_id = chatId`

- Function: `enqueueExtract(worksheetId, filterTypeId, presetId?)` → `queueId`
  - Insert a new queue entry with `phase = 'extract'`, `worksheet_id`, `filter_type_id`, optional `preset_id`

### src/cli.js

Commander.js entry point. Wire all commands from the CLI Commands section above. Key behaviors:

- `init`: create DB via `db/init.js`, create OUTPUT_DIRS, print success
- `ingest`: compute content_hash per chat for dedup. If hash exists, update (re-worksheet). Print: `"Ingested 3 chats. 2 new, 1 updated."`
- `extract`: load filters by name (comma-sep) or preset. Per chat: load worksheet, run filters, quality-check, save. Print: `"Chat #47: 3 filters applied, 3 passed, 0 failed."`
- `filters add`: interactive readline prompts for all filter fields
- `list`: table with ID | Title | Source | Status | Messages | Imported
- `search`: SQL LIKE across worksheets.summary, key_topics_json, category
- `health`: check DB exists, API key set, output dirs exist
- `export`: copy all extraction files for a chat to `output/exports/{chat-title}/`
- package.json `bin`: `{ "chat-extractor": "./src/cli.js" }` with `#!/usr/bin/env node` shebang

---

## Rules

1. **Save incrementally.** Write to the database after each step of the pipeline, not just at the end. If worksheet generation succeeds but categorization fails, the worksheet is still saved. Never lose work.
2. **Idempotent ingestion.** Re-ingesting the same chat file updates the existing record (matched by content_hash). It does not create a duplicate. The worksheet is regenerated. Existing extractions are NOT deleted — they reference the old worksheet which is updated in place.
3. **Filter execution is independent.** One filter failing does not block or affect other filters. Each filter runs in its own try/catch. Errors are logged and the next filter proceeds.
4. **Rate limit all Claude API calls.** Maximum 10 requests per minute for Haiku, 5 per minute for Sonnet. The `claude.js` wrapper enforces this with timestamp tracking and sleep delays. Never parallelize API calls.
5. **Quality check before saving.** Every extraction passes through quality-check.js before being written to disk. Failed quality checks trigger a retry (up to MAX_RETRIES). Only extractions that pass the threshold are saved as files. Failed extractions are recorded in the database with `status = 'failed'` for later inspection.
6. **Frontmatter on every artifact.** Every saved markdown file has YAML frontmatter linking back to its source chat ID, the filter that produced it, the date, and the quality score. This creates a traceable chain from artifact back to original conversation.
7. **New filter types via CLI, not code.** Users add new filter types using `chat-extractor filters add`, which inserts into the database. The only code-defined filters are the 6 defaults. The system reads filter definitions from the database at runtime, not from hardcoded lists.
8. **Presets reference filter IDs.** Adding new filter types does not break existing presets. Presets store an array of filter type IDs. Removing a filter type (deactivating it) means that filter is skipped when a preset references it — the preset still runs the remaining filters.
9. **Error handling: 3 retries with exponential backoff.** First retry after 2 seconds, second after 4 seconds, third after 8 seconds. After all retries fail, mark as `status = 'failed'` with `error_message` and continue processing the next item. Never crash the entire run because of one failure.
10. **Log every API call.** Every Claude API call is recorded in the `api_usage` table with model, token counts, computed cost, and purpose. The `status` command displays cumulative cost.
11. **Content hash for deduplication.** SHA-256 hash of raw chat content is stored in `chats.content_hash` with a UNIQUE constraint. Attempting to ingest identical content hits the duplicate detection path.
12. **Graceful format handling.** The parser should handle malformed input without crashing. If a file can't be parsed into messages, store it as a single-message chat and let the worksheet generator work with what it has. Log a warning, don't error out.

---

## Dashboard

The `chat-extractor status` command displays this terminal dashboard:

```
+====================================================+
|           CHAT EXTRACTOR STATUS                     |
+====================================================+
|  Total Chats: 47    Worksheeted: 42                |
|  Extractions: 156   Filters Active: 6              |
|  Queue: 3 pending   Errors: 1                      |
+----------------------------------------------------+
|  RECENT ACTIVITY (last 10)                          |
|  [ok] Chat #47 "PRD Maker Session" -> worksheeted  |
|  [ok] Chat #47 -> PRD Consolidation complete        |
|  [ok] Chat #47 -> Decision Log complete             |
|  [!!] Chat #46 -> Tool Extractor failed (retry 2/3)|
|  [ok] Chat #45 "Skill Ideas" -> 3 idea cards saved |
+----------------------------------------------------+
|  COST TRACKING                                      |
|  Haiku:  $0.42  (168 calls)                        |
|  Sonnet: $1.85  (23 calls)                         |
|  Total:  $2.27                                      |
+====================================================+
```

Implementation:
- Query `chats` table for total and worksheeted counts
- Query `extractions` table for total extractions count
- Query `filter_types` for active filter count
- Query `queue` for pending and failed counts
- Query `queue` ordered by `completed_at DESC LIMIT 10` for recent activity
- Query `api_usage` with `SUM(cost_usd)` grouped by model for cost tracking
- Use `cli-table3` for the bordered table layout
- Use `chalk` for color coding: green for success, red for errors, yellow for pending

The `chat-extractor health` command checks:
```
[ok] Database: exists, 6 tables, no corruption
[ok] API Key: ANTHROPIC_API_KEY is set (sk-ant-...xxxx)
[ok] Output dirs: all 7 directories exist
[ok] Filters: 6 active filter types loaded
[ok] Presets: 3 presets loaded
[!!] Queue: 1 failed item (chat-extractor list --failed for details)
```

---

## Testing Checklist

Run these tests in order. Each step builds on the previous one.

```
1. Setup
   [ ] npm install
   [ ] Create .env with ANTHROPIC_API_KEY
   [ ] Run: chat-extractor init
   [ ] Verify: chat-extractor health returns all green (DB, API key, dirs, filters, presets)

2. Ingest a single chat
   [ ] Run: chat-extractor ingest test/sample-chat.md
   [ ] Verify: chat-extractor list shows 1 chat with status "worksheeted"
   [ ] Run: chat-extractor show 1
   [ ] Check: summary is accurate (2-3 sentences, captures the chat's purpose)
   [ ] Check: key_topics are hierarchical (topics with subtopics)
   [ ] Check: decisions are captured with reasoning
   [ ] Check: artifacts list any code blocks, schemas, or diagrams mentioned

3. Extract with a single filter
   [ ] Run: chat-extractor extract 1 --filters knowledge
   [ ] Verify: file saved to output/knowledge/ directory
   [ ] Check: file has YAML frontmatter with source_chat_id, filter, date, quality_score
   [ ] Check: content is categorized (Technical, Strategic, Conceptual, Reference)
   [ ] Check: content is NOT just a copy of the worksheet summary

4. Extract with a preset
   [ ] Run: chat-extractor extract 1 --preset "Full Extract"
   [ ] Verify: 3 extractions created (knowledge + ideas + decisions)
   [ ] Check: each file saved to its correct directory
   [ ] Check: chat-extractor list shows extraction counts per chat

5. Add a custom filter type
   [ ] Run: chat-extractor filters add "summary-only"
   [ ] Provide: simple prompt, markdown format, output/summaries/ destination, haiku model
   [ ] Verify: chat-extractor filters list shows 7 filters (6 default + 1 new)
   [ ] Run: chat-extractor extract 1 --filters summary-only
   [ ] Verify: output file created in output/summaries/

6. Batch ingest
   [ ] Place 3 different chat files in test/batch/
   [ ] Run: chat-extractor ingest --dir test/batch/
   [ ] Verify: chat-extractor list shows 4 total chats (1 original + 3 batch)
   [ ] Verify: all 3 new chats have status "worksheeted"

7. Search
   [ ] Run: chat-extractor search "PRD" (or a keyword from the sample chat)
   [ ] Verify: returns matching chats with relevant worksheet excerpts

8. Error handling
   [ ] Create an empty file: test/empty.txt
   [ ] Run: chat-extractor ingest test/empty.txt
   [ ] Verify: chat status is "error" or gracefully handled (not a crash)
   [ ] Verify: other chats still display correctly in chat-extractor list

9. Idempotency
   [ ] Run: chat-extractor ingest test/sample-chat.md (same file again)
   [ ] Verify: chat-extractor list still shows 4 chats (not 5 — no duplicate)
   [ ] Verify: worksheet was regenerated (check updated timestamp)

10. Status dashboard
    [ ] Run: chat-extractor status
    [ ] Verify: shows correct counts for chats, extractions, filters
    [ ] Verify: shows recent activity log
    [ ] Verify: shows cost tracking with Haiku and Sonnet totals

11. Export
    [ ] Run: chat-extractor export 1
    [ ] Verify: all extraction files for chat #1 copied to output/exports/
    [ ] Verify: files are readable and frontmatter is intact
```

### Test Data: test/sample-chat.md

Create this file with real conversational content (at least 10 turns). It must contain: architecture decisions, a database schema, a deferred feature idea, a late-addition idea, and a step-by-step plan. This exercises all 6 default filters.

```markdown
## Human
I want to build a dashboard that shows all my running agents and their status. What tech stack should I use?

## Assistant
For an agent monitoring dashboard: React + TypeScript frontend, TanStack Query for data fetching, Tailwind CSS for styling, FastAPI backend with WebSocket for real-time updates, SQLite for local state. The key decision is whether to poll or use WebSockets.

## Human
Let's go with WebSockets. What about the database schema?

## Assistant
CREATE TABLE agents (id INTEGER PRIMARY KEY, name TEXT NOT NULL, status TEXT DEFAULT 'idle', last_heartbeat DATETIME, config_json TEXT);
CREATE TABLE agent_logs (id INTEGER PRIMARY KEY, agent_id INTEGER REFERENCES agents(id), level TEXT, message TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);

The heartbeat pattern: if no heartbeat in 30 seconds, mark as unresponsive.

## Human
What about agents that can spawn sub-agents?

## Assistant
Powerful pattern but adds complexity: parent_agent_id FK, tree traversal for status rollup, cascading shutdown. I'd defer this to Phase 2. Start with flat agents.

## Human
Makes sense. What should the API endpoints look like?

## Assistant
GET /api/agents, GET /api/agents/:id, POST /api/agents/:id/start, POST /api/agents/:id/stop, WS /api/agents/live. Consistent JSON shape: { data, error, timestamp }.

## Human
What about authentication? Single-user now, maybe multi-user later.

## Assistant
API key in .env for now, checked via swappable middleware. For multi-user later, JWT tokens over session cookies since you're building a SPA. Don't build auth yet — just make the middleware pluggable.

## Human
I had an idea — track costs per agent too. How much each agent spends on API calls.

## Assistant
Add a cost_events table: agent_id, model, input_tokens, output_tokens, cost_usd, created_at. Aggregate per agent/day/model. This is the observability story — not just IF agents run, but what they cost.

## Human
What's the build order?

## Assistant
Phase 1 (Foundation): 1. DB schema + migrations, 2. FastAPI CRUD endpoints, 3. WebSocket server.
Phase 2 (Dashboard): 4. React scaffolding + routing, 5. Agent list with status, 6. Agent detail with log stream.
Phase 3 (Controls): 7. Start/stop with confirmation, 8. Cost tracking, 9. Settings page.
Phase 4 (Polish): 10. Error handling + reconnection, 11. Responsive design, 12. Log export.
Test each phase independently before moving to the next.
```

---

## Build Order

Build in this exact order, testing each phase before moving to the next.

```
Phase 1: Foundation
  Test: chat-extractor health returns all green
  ─────────────────────────────────────────────
  1. package.json (dependencies, bin field, scripts)
  2. src/config.js (env loading, validation, constants)
  3. src/utils/logger.js (logging with chalk colors)
  4. db/init.js (database creation, schema, seeding trigger)
  5. src/utils/claude.js (API wrapper with rate limiting, retry, cost tracking)
  → Test: node -e "require('./db/init')" creates the database
  → Test: chat-extractor health (via npx or node src/cli.js health)

Phase 2: Ingest Pipeline
  Test: ingest a file, verify worksheet in database
  ─────────────────────────────────────────────
  6. src/ingest/capture.js (file read, stdin, directory scan)
  7. src/ingest/parse.js (format detection, message extraction)
  8. src/ingest/consolidate.js (speaker normalization, merging)
  9. src/ingest/worksheet.js (AI worksheet + categorization)
  → Test: chat-extractor ingest test/sample-chat.md
  → Test: chat-extractor show 1 displays a coherent worksheet

Phase 3: Extract Pipeline
  Test: run a filter, verify output file on disk
  ─────────────────────────────────────────────
  10. src/extract/filter-registry.js (load, seed, manage filters)
  11. src/filters/*.js (all 6 default filter definitions)
  12. src/extract/filter-executor.js (prompt building, Claude calls)
  13. src/extract/quality-check.js (scoring, pass/fail)
  14. src/extract/save-artifact.js (file writing with frontmatter)
  → Test: chat-extractor extract 1 --filters knowledge
  → Test: verify file exists in output/knowledge/ with correct frontmatter

Phase 4: Presets & Queue
  Test: run a preset, verify multiple extractions
  ─────────────────────────────────────────────
  15. src/presets/defaults.js (default preset definitions + seeding)
  16. src/queue/processor.js (queue processing with retry logic)
  → Test: chat-extractor extract 1 --preset "Full Extract"
  → Test: verify 3 files created in correct directories

Phase 5: CLI Commands
  Test: all commands respond correctly
  ─────────────────────────────────────────────
  17. src/cli.js (Commander setup, all commands wired to modules)
  18. src/utils/file-output.js (if not already built in Phase 3)
  → Test: every command from the CLI Commands section
  → Test: chat-extractor filters list, chat-extractor presets list

Phase 6: Polish & Full Test
  Test: complete testing checklist passes
  ─────────────────────────────────────────────
  19. test/sample-chat.md (the real test data from this file)
  20. Dashboard display in status command (cli-table3 formatting)
  21. Error handling edge cases (empty files, malformed JSON, huge chats)
  22. Batch ingest and --all flag for extract
  → Test: run the full Testing Checklist above, all items pass
```

---

## Cost Estimate

Per chat processed through the full pipeline (ingest + all 6 default filters):

| Step | Model | Input Tokens | Output Tokens | Cost |
|------|-------|-------------|---------------|------|
| Worksheet generation | Haiku | ~2,000 | ~1,000 | $0.002 |
| Categorization | Haiku | ~500 | ~100 | $0.0003 |
| Knowledge Dump | Haiku | ~2,000 | ~800 | $0.002 |
| Idea Cards | Haiku | ~2,000 | ~800 | $0.002 |
| Checklist Builder | Haiku | ~2,000 | ~800 | $0.002 |
| Decision Log | Haiku | ~2,000 | ~800 | $0.002 |
| PRD Consolidation | Sonnet | ~2,000 | ~1,000 | $0.021 |
| Tool/Skill Extractor | Sonnet | ~2,000 | ~1,000 | $0.021 |

**Total per chat (full extract): ~$0.052**

| Volume | Monthly Cost |
|--------|-------------|
| 10 chats/month | ~$0.52 |
| 50 chats/month | ~$2.60 |
| 200 chats/month | ~$10.40 |

Using only Haiku filters (no PRD/Tool): ~$0.01 per chat.

---

## Data Retention

- **Raw chats**: Keep forever — they are the source of truth.
- **Worksheets**: Keep forever — they are the searchable index.
- **Extractions**: Keep forever — accumulated knowledge base.
- **Queue entries**: Delete entries with `status = 'complete'` older than 30 days. Keep `'failed'` entries indefinitely for debugging.
- **API usage logs**: Keep forever for cost tracking. Aggregate old entries by month if table grows large.
