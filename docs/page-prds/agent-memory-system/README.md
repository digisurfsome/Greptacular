# Agent Memory System — PRD

> **Agent OS framework.** Standards + Product + Specs. Read all three before touching code.
> **Status:** Draft v1. Author: forked Opus session, 2026-04-23.
> **Owner:** Not a coder. Plain language. Move fast.

---

## 0. Executive Summary (1-minute read)

Build a **local-first, cross-LLM, cross-session memory system** that captures every chat in append-only markdown, extracts structured metadata cheaply via Haiku/Sonnet subagents, indexes it for hybrid search (metadata + keyword + semantic), and lets any future agent (or fork) retrieve relevant past context at 5 zoom levels — from 1-line summary to full chat.

**Why:** Today's chats evaporate. Forks inherit only the surface transcript — not rationale, failures, or standing orders. Scale breaks current "dump to Downloads" approach at ~500 chats.

**Moat:** Anthropic/OpenAI won't build this — they want vendor lock-in. Owner's data stays on owner's disk. Works across any LLM vendor.

**Cost at scale (~100 chats/mo, heavy use):** ~$50–$130/mo in model API calls. Opus-only alternative: ~$800–$1500/mo. **10× savings by routing work to the right model.**

**Total build cost:** ~700k tokens Opus (~45 min gen) + pure-code daemon work.

---

# LAYER 1 — STANDARDS

> Rules every agent follows when building or extending this system. Non-negotiable.

## 1.1 Coding Standards

| Rule | Detail |
|------|--------|
| **Language** | Python 3.12 for daemon + indexing. Markdown for chat storage. SQLite for indexes. No frameworks heavier than needed. |
| **File safety** | Every write = `.tmp` → atomic rename. Never rewrite chat files — append only. |
| **Crash safety** | If process dies mid-write, system must self-heal on next start. No corrupt state. |
| **Portability** | Local-first. Zero cloud deps. User can zip `~/.claude-memory/` and move to any machine. |
| **Vendor neutrality** | Works with Claude, Gemini, GPT, local models. Storage format does not assume a vendor. |
| **Git-diffable** | All files human-readable markdown or JSON. No binary blobs except embeddings DB. |
| **Idempotent** | Running the indexer twice on the same data = same result. No duplicate entries. |

## 1.2 Architecture Standards

| Rule | Detail |
|------|--------|
| **Memory Contract** | Every agent, every turn, treats session as if a fork may happen at any moment. State is always externalized. Never held only in working context. |
| **Three layers, never mix** | L1 = daemon (background, cheap). L2 = subagents (on-demand, mid). L3 = main agent (live, premium). Never do L1 work in L3. |
| **Threshold rule** | Subagent only spawned if task > ~10k tokens of work. Below that = inline or daemon. |
| **Channel separation** | Chat file has 4 channels: `user`, `assistant-visible`, `assistant-internal`, `tool-calls`. Each turn tagged clearly. |
| **Append-only** | Chat transcripts never rewritten. Edits happen in sidecar files. |
| **Structured blocks** | Main agent emits `[HANDOFF]`, `[DECISION]`, `[STANDING-ORDER]`, `[FAILURE]` tags. Daemon parses, user never sees unless requested. |

## 1.3 Model Routing Standards

**Hard rule:** match model to task complexity. Opus tokens are 5× Sonnet, 19× Haiku. Waste = real dollars.

| Task class | Model | Examples |
|-----------|-------|----------|
| Pure I/O | None (code) | Append turn, index refresh, file rename |
| Pattern extraction | Haiku | Metadata, 1-line summary, handoff block parse |
| Light synthesis | Sonnet | Paragraph summary, decision extraction, topic drift |
| Judgment + inference | Sonnet | Déjà vu detection, relevance ranking, standing orders |
| Strategy + architecture | Opus | Live conversation, PRDs, cross-chat reasoning |

## 1.4 Data Standards

**Directory layout (canonical):**
```
~/.claude-memory/
├── chats/
│   └── YYYY/MM/DD/
│       ├── {chat_id}_{slug}.md          (append-only transcript)
│       └── {chat_id}_{slug}.meta.json   (sidecar metadata)
├── index/
│   ├── fulltext.sqlite                   (FTS5)
│   ├── embeddings.db                     (vectors)
│   └── topics.json                       (topic → chat list)
├── summaries/
│   └── {chat_id}/
│       ├── one-line.txt
│       ├── one-para.md
│       └── checkpoint.md
├── decisions/
│   └── YYYY-MM-DD.md                     (all decisions, daily rollup)
├── principles/
│   └── standing-orders.md                (auto-extracted rules)
└── daemon/
    ├── state.json                        (daemon runtime state)
    ├── queue.jsonl                       (pending jobs)
    └── logs/
```

**Chat file format (markdown, per-turn block):**
```
---
turn: 42
timestamp: 2026-04-23T03:41:00Z
channel: user | assistant-visible | assistant-internal | tool-calls
tokens_in: 1234
tokens_out: 567
cost_usd: 0.003
---
{content}
```

**Sidecar metadata (JSON schema):** see §3.2 below.

## 1.5 Privacy + Security Standards

| Rule | Detail |
|------|--------|
| **Local-only** | No network calls from daemon except LLM API for enrichment. |
| **API keys** | Read from `.env` only. Never committed. Never in chat transcripts. |
| **Scrubbing** | Daemon scans for API-key-shaped strings + PII before writing to searchable index. Flagged turns get `[REDACTED]` in index but kept raw in source file. |
| **User-owned** | User can `rm -rf ~/.claude-memory/` and lose nothing vendor-hosted. |

---

# LAYER 2 — PRODUCT

> Vision, roadmap, use cases. Why this exists, who it's for, where it's going.

## 2.1 Vision

**Every agent you talk to, forever, shares one memory.**

Chat with Claude today, fork next week, talk to Gemini next month — all three see the same structured history, with the same decisions log, same standing orders, same failure log. **The user's memory, not the vendor's.**

## 2.2 Who It's For

- **Primary user:** the owner. Not a coder. Talks to multiple AI agents daily across many projects. Loses context every time a chat ends. Forks exist but transcripts alone lose rationale.
- **Secondary user:** future agents (Claude, Gemini, GPT, whatever). Need rich context to be useful on day 1 of a new session.
- **Tertiary user:** tools that query the memory (dashboards, search UIs, automation scripts).

## 2.3 Core Use Cases

| # | Use case | Current pain | Fixed by |
|---|----------|-------------|----------|
| 1 | Fork mid-project, new agent continues seamlessly | Fork gets surface transcript, loses rationale | Handoff blocks + checkpoints |
| 2 | "Have we discussed this before?" | Owner re-explains same thing 5 times | Déjà vu detection |
| 3 | "What did we decide about X last month?" | Lost in 200+ chats | Decisions log + semantic search |
| 4 | Owner's preferences auto-applied to new chats | Every fresh agent starts generic | Standing orders auto-extraction |
| 5 | "Show me all chats where we hit a wall on hyperframes" | Impossible today | Failure tagging + metadata filter |
| 6 | Walk away from a chat, come back 3 months later | Cold start, no memory | Auto-save every turn, auto-checkpoint |
| 7 | Cross-project insight ("remember that SEO trick from the plumber project?") | Manual hunt through Downloads | Hybrid search (metadata + keyword + semantic) |

## 2.4 Non-Goals

Ruthless scoping. **This system does NOT:**

- Replace Git for code history
- Store vendor-hosted chat threads (Claude.ai's own chats — those are the vendor's problem)
- Sync across multiple users (single-owner tool)
- Provide a chat UI (it's storage + retrieval, not a frontend)
- Run in the cloud (local-first, period)
- Replace the owner's intuition — it augments, doesn't decide

## 2.5 Roadmap — 3 Phases

### Phase 1 — MVP (Capture + Basic Retrieval)
**Goal:** never lose a chat again. Manual retrieval works.

- Auto-save every turn to markdown (append-only, atomic writes)
- Sidecar metadata extraction (Haiku daemon)
- FTS5 full-text index
- CLI tool: `memory search "keyword"` → returns chat list
- Structured block parsing (`[HANDOFF]`, `[DECISION]`)
- Daily decisions log rollup

**Done when:** owner can search every chat they've ever had, in <1 sec, and forks carry structured handoff blocks.

**Build cost:** ~250k Opus tokens (~15 min gen) + ~$5/mo Haiku ops.

### Phase 2 — Intelligence (Summaries + Semantic)
**Goal:** agent proactively uses memory.

- Multi-zoom summaries (1-line, paragraph, checkpoint) via Haiku + Sonnet
- Embedding indexer (local model, e.g. `nomic-embed-text` via Ollama — free)
- Hybrid search: metadata filter → FTS5 → vector rerank
- Déjà vu detection at turn-start (main agent calls Sonnet subagent)
- Standing orders auto-extractor (weekly Sonnet scan)
- Failure tagging + "avoid these paths" surface

**Done when:** main agent says "we decided X in chat Y, here's why" without owner asking.

**Build cost:** ~300k Opus tokens (~18 min gen) + ~$30–80/mo Sonnet ops.

### Phase 3 — Cross-Vendor + Agent Notebook
**Goal:** one memory across all LLM vendors. Agent has private long-term notebook.

- Importers for Claude.ai exports, ChatGPT exports, Gemini exports
- Unified chat format across vendors
- Agent's private notebook (shadow channel, invisible to user by default)
- Knowledge graph: chats → topics → decisions → artifacts
- Dashboard UI (optional) for browsing + tagging

**Done when:** owner can ask any LLM "remember the thing from my Gemini chat last month?" and it works.

**Build cost:** ~250k Opus tokens (~15 min gen) + importers per vendor.

## 2.6 Success Metrics

| Metric | Phase 1 target | Phase 2 target | Phase 3 target |
|--------|---------------|---------------|---------------|
| Chats captured w/ zero loss | 100% | 100% | 100% |
| Search latency | <1s | <1s | <1s |
| Fork context quality (subjective) | "better than raw transcript" | "agent catches mistakes I forgot" | "agent knows me across vendors" |
| Monthly cost | <$10 | <$100 | <$150 |
| Owner re-explaining same thing | 50% reduction | 90% reduction | 95% reduction |

## 2.7 Trade-offs + Decisions

| Decision | Chose | Rejected | Why |
|----------|-------|---------|-----|
| Storage format | Markdown + JSON sidecar | Single DB, proprietary format | Git-diffable, human-readable, portable |
| Embedding model | Local (Ollama nomic) | OpenAI ada-002 | Free, private, offline-capable |
| Daemon language | Python | Node / Rust | Ecosystem for LLM APIs + SQLite. Not a coder's language = fine. |
| Search stack | SQLite FTS5 + vector | Elasticsearch / Meilisearch | Zero infra. Local-first. Fast enough at 10k chats. |
| Capture timing | Per-turn atomic | Periodic flush | Zero loss risk outweighs write cost |
| Agent subagent model mix | Haiku + Sonnet, Opus never | All Opus | 10× cost reduction. Task complexity doesn't need Opus. |

---

# LAYER 3 — SPECS

> Concrete feature specifications. Each spec is self-contained, implementable.

## 3.1 SPEC-001: Capture Daemon

**Purpose:** background process that watches chat buffer and writes turns to disk atomically.

### Behavior
- On every turn emitted (user or assistant), append a turn-block to the current chat's `.md` file.
- Write sequence: compose block → write to `{file}.tmp` → `fsync` → rename to `{file}`.
- Update `daemon/state.json` with latest turn index + chat_id.
- Maintain append-only invariant: NEVER rewrite earlier turns.

### Input contract
```json
{
  "chat_id": "42326156a",
  "turn": 42,
  "timestamp": "2026-04-23T03:41:00Z",
  "channel": "assistant-visible",
  "content": "...",
  "tokens_in": 1234,
  "tokens_out": 567,
  "cost_usd": 0.003
}
```

### Output
- Appended turn-block in `chats/YYYY/MM/DD/{chat_id}_{slug}.md`
- Updated `state.json`

### Model: none (pure code).

### Failure modes
- Disk full → queue to `daemon/queue.jsonl`, retry on free space
- Write fails mid-flight → `.tmp` file orphaned, garbage-collected on next start
- Daemon dies → chat buffer flushes on next daemon start via hook

### Done criteria
- 1000 turns written with zero data loss under SIGKILL testing
- Recovery from dirty shutdown within 5 seconds

---

## 3.2 SPEC-002: Sidecar Metadata Extractor

**Purpose:** on chat close (or every 10 turns, whichever first), generate `.meta.json` sidecar.

### Schema
```json
{
  "id": "42326156a",
  "started": "2026-04-23T03:41:00Z",
  "ended": "2026-04-23T05:12:00Z",
  "status": "active|dormant|archived",
  "project": "agent-memory-system",
  "topics": ["memory", "agent-os", "forking", "subagents"],
  "tokens_in": 189234,
  "tokens_out": 41892,
  "cost_usd": 0.26,
  "agent_model": "claude-opus-4-7",
  "artifacts_created": ["docs/page-prds/agent-memory-system/README.md"],
  "decisions_count": 7,
  "forked_from": null,
  "forked_to": [],
  "linked_chats": ["abc123"],
  "sentiment_arc": "productive",
  "success_marker": "prd-written",
  "failure_markers": []
}
```

### Process
1. Read last 10 turns + prior summary (if any)
2. Send to Haiku w/ schema-enforcing prompt
3. Parse JSON response
4. Merge into existing sidecar (additive, never overwrite user-tagged fields)
5. Atomic write

### Model: Haiku (~$0.001 per chat at typical size).

### Done criteria
- Valid JSON 99.5% of the time (retry on failure)
- Topics consistent across re-runs (cache stable topic embeddings)

---

## 3.3 SPEC-003: Structured Block Parser

**Purpose:** extract `[HANDOFF]`, `[DECISION]`, `[STANDING-ORDER]`, `[FAILURE]` blocks from main-agent output.

### Block format
```
[HANDOFF]
did: cloned repos to C:\Users\lober\VideoStudio
state: disk 99MB free, clone failed
next: user freeing space, plug external drive AM
avoid: don't retry clone to C:
why: C: drive catastrophically full
[/HANDOFF]

[DECISION]
chose: hyperframes-only pipeline
rejected: Veo 3 photoreal video
why: Veo at scale = $18k/day
reversible: yes, swap renderer later
[/DECISION]

[STANDING-ORDER]
rule: never quote human-week timelines, always token/minute estimates
scope: forever
source: user explicit request 2026-04-23
[/STANDING-ORDER]

[FAILURE]
attempted: install to C: drive
failed: disk full at 99MB free
learned: check disk space before any clone
cost: wasted ~30k tokens + 10 min user time
[/FAILURE]
```

### Process
1. Scan latest turn block for `[TAG]...[/TAG]` patterns
2. Extract + validate schema
3. Route to appropriate rollup:
   - `[HANDOFF]` → `daemon/handoffs.jsonl`
   - `[DECISION]` → `decisions/YYYY-MM-DD.md`
   - `[STANDING-ORDER]` → `principles/standing-orders.md` (dedupe)
   - `[FAILURE]` → `principles/failures.md` + tag sidecar

### Model: Haiku for validation. Pure code for routing.

### Done criteria
- 100% of emitted blocks captured
- Standing orders never duplicate (fuzzy match on rule text)

---

## 3.4 SPEC-004: Full-Text Index (FTS5)

**Purpose:** instant keyword search across all chats.

### Schema
```sql
CREATE VIRTUAL TABLE chat_fts USING fts5(
  chat_id,
  turn,
  channel,
  content,
  topics,
  tokenize='porter unicode61'
);
```

### Process
- On turn write, daemon inserts row into FTS
- On chat rename / metadata update, update row
- Indexer runs continuous (tailing daemon state) or batch (hourly)

### Query API
```python
def search(query: str, filters: dict = None) -> list[ChatMatch]:
    # filters: {project, date_range, min_cost, has_decision, ...}
```

### Model: none (pure code).

### Done criteria
- Sub-100ms for 10k-chat corpus
- Supports phrase search, boolean ops, proximity

---

## 3.5 SPEC-005: Embedding Indexer

**Purpose:** semantic search ("fuzzy meaning") across chats.

### Chunking strategy
- **Per turn** if turn > 500 tokens
- **Per [HANDOFF]/[DECISION] block** always its own chunk
- **Per natural boundary** (summary break, topic drift marker) — rolling window

### Embedding model
- Local via Ollama: `nomic-embed-text` (768-dim, free)
- Fallback: Haiku-powered compressed summary → embed

### Storage
- SQLite with `sqlite-vec` extension
- Row: `chunk_id, chat_id, turn_range, text, embedding (BLOB), metadata`

### Process
- Nightly batch on new/changed chats
- Incremental: only re-embed changed chunks

### Query
```python
def semantic_search(query: str, top_k=20, filters=None) -> list[ChunkMatch]:
    q_embed = embed(query)
    return vector_search(q_embed, top_k, filters)
```

### Model: local embedding + Haiku for compression fallback.

### Done criteria
- Semantic match quality beats pure keyword on eval set of 50 queries
- Build index for 1000 chats in <10 min

---

## 3.6 SPEC-006: Hybrid Search API

**Purpose:** the one search endpoint to rule them all.

### Algorithm
```
def hybrid_search(query, filters):
    # Step 1: metadata filter (instant, cheap)
    candidates = metadata_filter(filters)  # reduces 10k → ~500

    # Step 2: FTS5 keyword match (fast, precise)
    fts_hits = fts_search(query, in=candidates, top_k=100)

    # Step 3: semantic rerank (medium, fuzzy)
    vector_hits = semantic_search(query, in=candidates, top_k=100)

    # Step 4: combine + Sonnet rerank top 20
    merged = reciprocal_rank_fusion(fts_hits, vector_hits)
    top20 = merged[:20]

    # Step 5: Sonnet subagent picks top 5 with reasoning
    final = sonnet_rerank(query, top20, context=filters)
    return final
```

### Model: Sonnet only for final rerank (~20 chunks × ~500 tokens = 10k tokens, one call).

### Done criteria
- Query latency <2s end-to-end on 10k-chat corpus
- Top-5 relevance ≥ 80% on eval set

---

## 3.7 SPEC-007: Summarizer (Multi-Zoom)

**Purpose:** generate summary at 5 zoom levels for every chat.

### Zooms
| Level | Size | Model | Trigger |
|-------|------|-------|---------|
| Link | ~30 tokens | pure code (extract title) | on every turn |
| One-line | ~20 tokens | Haiku | on chat close / every 50 turns |
| Paragraph | ~150 tokens | Haiku | on chat close |
| Checkpoint | ~500 tokens | Sonnet | on chat close + structured block extract |
| Full | raw | none | always available |

### Checkpoint template
```markdown
# {chat_id} Checkpoint — {date}

## Goal
{one-line}

## Decisions
- {from [DECISION] blocks}

## State
- {from latest [HANDOFF] block}

## Open Questions
- {extracted inference}

## Dead Paths
- {from [FAILURE] blocks}

## Artifacts Created
- {from sidecar}
```

### Done criteria
- 100% of chats have checkpoint within 5 min of close
- Summaries factually consistent (Sonnet eval on sample)

---

## 3.8 SPEC-008: Déjà Vu Detector

**Purpose:** at start of new turn, main agent checks "have we discussed this before?"

### Trigger
Main agent calls Layer-2 subagent when user message contains:
- Proposal ("what if we...", "should I...", "let's build...")
- Reference ("remember when...", "the thing from...")
- Decision request ("A or B?", "which is better?")

### Process
1. Main agent spawns Sonnet subagent with user message + recent context
2. Subagent runs hybrid_search against memory
3. Returns top 3 relevant past chats with:
   - Relevance score
   - What was decided / tried
   - Outcome (success / failure / pending)
4. Main agent folds result into its response

### Threshold
Only spawn if user message is strategic (not "ok" / "yes" / "fix this bug"). Simple heuristic or Haiku classifier.

### Model: Haiku classifier + Sonnet search.

### Done criteria
- False positive rate <15%
- Retrieves relevant past context 70%+ of strategic messages

---

## 3.9 SPEC-009: Standing Orders Auto-Extractor

**Purpose:** weekly scan of chats for user's repeated preferences → add to `principles/standing-orders.md`.

### Process
1. Scan chats from last 7 days
2. Send to Sonnet with prompt: "identify rules the user stated or implied that should apply to all future sessions"
3. Dedupe against existing standing orders
4. Write new orders w/ source chat link + date

### Example output
```markdown
## Standing Order: No human-week timelines
Added: 2026-04-23
Source: chat 42326156a turn 84
Rule: Always give estimates in tokens / minutes of agent time, never hours/days/weeks.
Scope: All sessions.
```

### Loading into new sessions
Standing orders prepended to CLAUDE.md or injected as system prompt supplement.

### Model: Sonnet weekly (~50k tokens input, ~2k output = ~$1/week).

### Done criteria
- New orders surface within 7 days of pattern emerging
- Zero duplicates
- User can reject an order → permanent ignore

---

## 3.10 SPEC-010: Main Agent Protocol

**Purpose:** rules main agent follows to play well with memory system.

### CLAUDE.md additions
```markdown
## Memory System Integration

### Emit Structured Blocks
At end of each substantive action, emit:

[HANDOFF]
did: <1 line>
state: <files changed, services affected>
next: <immediate next step>
avoid: <dead paths>
why: <rationale for key choices>
[/HANDOFF]

For significant decisions, emit:

[DECISION]
chose: <option>
rejected: <alternatives>
why: <reasoning>
reversible: yes|no
[/DECISION]

For user-stated preferences or rules, emit:

[STANDING-ORDER]
rule: <the rule>
scope: <session|project|forever>
source: <context>
[/STANDING-ORDER]

For failures:

[FAILURE]
attempted: <what>
failed: <why>
learned: <what not to repeat>
cost: <tokens/time/money>
[/FAILURE]

### Memory Queries
Before proposing a major approach, consider:
"Should I check memory for prior discussion?"
If yes, spawn Sonnet subagent with hybrid_search.

### Checkpoint Writing
At 40% context or on natural task completion,
write full checkpoint to:
.autoforge/handoffs/session-{id}-checkpoint-{n}.md
```

### Done criteria
- Main agent emits blocks on 80%+ of substantive turns
- Blocks are well-formed (schema-valid)

---

## 3.11 SPEC-011: CLI Tool

**Purpose:** owner-facing command-line for browsing / searching memory.

### Commands
```bash
memory search "hyperframes timeline editor"
memory list --project video-pipeline --since 2026-04-01
memory show {chat_id}
memory checkpoint {chat_id}
memory decisions --since last-week
memory standing-orders
memory stats
memory inject {chat_id} --zoom checkpoint   # prints context to paste
```

### Done criteria
- Responds in <1s for typical queries
- Color + formatted output
- Works on Windows, Mac, Linux

---

## 3.12 SPEC-012: Importers (Phase 3)

**Purpose:** ingest exports from other LLM vendors.

### Vendors
- Claude.ai export (JSON)
- ChatGPT export (JSON)
- Gemini export (JSON / HTML)

### Process
1. User drops export file → importer runs
2. Parse vendor-specific format → canonical turn blocks
3. Generate sidecar metadata (Haiku)
4. Index into FTS + vectors
5. Tag with `vendor` field for filtering

### Done criteria
- Round-trip: Claude export → import → search finds original content
- Preserves timestamps, turn order, role attribution

---

# 4. BUILD PLAN (Phased)

## Phase 1 — MVP (Week 1, ~250k Opus tokens)

Build order:
1. SPEC-001 Capture daemon (pure code, ~40k)
2. SPEC-002 Metadata extractor (Haiku integration, ~30k)
3. SPEC-003 Structured block parser (~30k)
4. SPEC-004 FTS5 index (~25k)
5. SPEC-010 Main agent protocol — CLAUDE.md updates (~15k)
6. SPEC-011 CLI tool — basic search/list/show (~40k)
7. Daemon runner + systemd service + Windows service variants (~30k)
8. Testing + hardening (~40k)

**Phase 1 done = owner never loses a chat, can search every word across all chats, forks carry structured handoffs.**

## Phase 2 — Intelligence (Week 2, ~300k Opus tokens)

1. SPEC-005 Embedding indexer + Ollama setup (~50k)
2. SPEC-006 Hybrid search API (~40k)
3. SPEC-007 Summarizer multi-zoom (~40k)
4. SPEC-008 Déjà vu detector (~50k)
5. SPEC-009 Standing orders extractor (~40k)
6. Main agent protocol v2 — memory query integration (~30k)
7. CLI tool v2 — checkpoint, decisions, inject (~30k)
8. Testing + tuning (~20k)

**Phase 2 done = agent proactively surfaces relevant past context.**

## Phase 3 — Cross-Vendor (Week 3+, ~250k Opus tokens)

1. SPEC-012 Importers — Claude.ai, ChatGPT, Gemini (~100k)
2. Knowledge graph builder (~50k)
3. Agent's private notebook (~40k)
4. Optional dashboard UI (~60k, stretch)

**Phase 3 done = unified memory across any LLM vendor.**

---

# 5. COST PROJECTIONS

## Build (one-time)
| Phase | Opus tokens | Opus cost | Gen time |
|-------|-------------|-----------|----------|
| Phase 1 | 250k | ~$19 | ~15 min |
| Phase 2 | 300k | ~$23 | ~18 min |
| Phase 3 | 250k | ~$19 | ~15 min |
| **Total** | **800k** | **~$61** | **~48 min** |

## Runtime (monthly, heavy use: ~100 chats, ~50k turns/mo)
| Component | Model | Monthly cost |
|-----------|-------|-------------|
| Turn append | none | $0 |
| Metadata extract (100 chats × Haiku) | Haiku | ~$0.10 |
| Block parsing (~500 blocks × Haiku validate) | Haiku | ~$0.50 |
| Paragraph summaries (100 × Haiku) | Haiku | ~$0.50 |
| Checkpoint summaries (100 × Sonnet) | Sonnet | ~$5 |
| Embedding (local Ollama) | local | $0 (electricity) |
| Déjà vu queries (~200/mo × Sonnet) | Sonnet | ~$20 |
| Standing orders (4 weekly scans × Sonnet) | Sonnet | ~$4 |
| Search reranks (~500/mo × Sonnet) | Sonnet | ~$25 |
| **Total** | | **~$55/mo** |

**Opus-only alternative: ~$1,050/mo. Savings: 95%.**

---

# 6. RISKS + MITIGATIONS

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Daemon crash → turn loss | Med | High | Atomic writes + queue + WAL semantics |
| Index corruption | Low | High | SQLite WAL mode + periodic full rebuild option |
| Embedding drift (model update) | Med | Med | Version tag embeddings; rebuild on change |
| API key leak in chat file | Med | Critical | Scrubbing pass before index write |
| Memory gets "opinionated" wrongly | Med | Med | User can reject standing orders, mark failures |
| Cost creep | Low | Med | Budget cap in daemon config; alerts at 80% |
| Vendor export format changes | High | Low | Versioned importers, tested against fixtures |
| Too many false "déjà vu" surfacings | High | Med | Threshold tuning + user feedback loop |

---

# 7. OPEN QUESTIONS

1. **Owner input:** do you want agent's private notebook visible in any UI, or truly hidden until asked?
2. **Ollama dep:** willing to install Ollama for local embeddings, or prefer Haiku embeddings (costs ~$1/mo more)?
3. **Chat boundary:** when is a chat "closed"? 24hr inactivity? User action? Fork point?
4. **Principle conflict resolution:** if two standing orders contradict, how to resolve?
5. **Multi-device:** does this need to sync across laptop + desktop eventually? (adds Syncthing/Dropbox pattern)

---

# 8. APPENDIX

## 8.1 File Path Summary

- **This PRD:** `docs/page-prds/agent-memory-system/README.md`
- **Memory root:** `~/.claude-memory/` (user home)
- **Main agent protocol updates:** `CLAUDE.md` (project root, §Memory System Integration)
- **Daemon install:** `services/memory-daemon/` (new, Phase 1)
- **CLI tool install:** `bin/memory` (new, Phase 1)

## 8.2 Glossary

- **Fork:** spawning a fresh agent from a prior conversation's transcript + context
- **Handoff block:** structured markdown tag containing agent-to-agent state transfer
- **Déjà vu:** agent detecting a topic has been discussed before
- **Standing order:** a user preference that applies to all future sessions
- **Checkpoint:** a ~500-token structured summary of a chat's state
- **Zoom level:** retrieval granularity (link → one-line → paragraph → checkpoint → full)
- **Memory Contract:** architectural principle — always externalize state

## 8.3 Related Docs

- `docs/info/video-studio-setup-plan.md` — video pipeline (different project, same memory system serves it)
- `docs/info/commercial-playbook.md` — commercial template system
- `CLAUDE.md` — project instructions (will be updated with Memory System Integration section)
- `.claude/rules/tool-efficiency.md` — tool-use discipline (compatible principles)

---

**END OF PRD**

Ready to build. Start Phase 1 SPEC-001 when greenlit.
