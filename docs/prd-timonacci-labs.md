# PRD: Timonacci Labs — Universal Knowledge Hub

**Created: 2026-03-15**
**Status: Ready to build**
**Priority: HIGHEST — This is the evolution of YT Lab into the central nervous system of the entire system**
**Supersedes: YT Lab (which becomes one ingestion source among many)**

---

## What This Is

YT Lab grew up. It's not just YouTube anymore.

Timonacci Labs is a universal knowledge ingestion, synthesis, and distribution hub. Anything goes in — YouTube videos, articles, PDFs, raw text, transcripts. The system ingests it, matches it to what it already knows, extracts only what's genuinely new, and routes the knowledge to wherever it needs to go: skills, prompts, reference files, PRDs, tools, build rules.

Three core innovations:

1. **Truth Documents + Sword Sharpener** — One razor-sharp document per topic, auto-improved with every new source
2. **The Diverter** — Routes knowledge to the right destination (skill, prompt, PRD, tool, reference file)
3. **Self-Improvement Loops** — The system tracks its own accuracy and gets better over time

**The end state:** Paste a URL. Walk away. The system ingests it, sharpens the relevant truth document, routes new knowledge to skills and tools, and self-improves its matching accuracy. Your only job is finding interesting content.

---

## Why It Matters

Right now, every piece of content is an island. Watch a video about AI SEO — get some notes. Read an article about AI SEO — get more notes. Watch another video — more notes. None of them talk to each other. The insights are scattered across 15 tabs, 3 note apps, and your memory.

After Timonacci Labs:
- Upload 10 videos about AI SEO over a month
- Each one adds 5-15% new insights to the truth document
- After all 10, the truth document covers 99% of everything known about AI SEO
- No single video had that — the **synthesis** created it
- The system auto-generated 3 skills, 8 reference files, and 2 PRDs from the knowledge
- You didn't organize anything. The system did it all.

---

## Core Concept 1: The Truth Document & Sword Sharpener

This is the MAIN innovation.

The system maintains a **truth document** per topic. Think of it like a wiki article that auto-improves every time someone finds a new source. When new content comes in:

```
NEW CONTENT ARRIVES
       |
       v
  MATCHER — Does this match an existing truth document?
  |                                    |
  | YES                                | NO
  v                                    v
  SWORD SHARPENER                      Create new truth document
  |                                    from scratch
  |
  Compare new content vs truth doc
  |
  v
  DIFF ENGINE — What's genuinely new?
  |                          |
  | Something new            | Nothing new
  v                          v
  Show diff to user          Mark as "absorbed,
  User approves merge        nothing new" — done
  Truth doc gets sharper
  Version incremented
```

### The Matching System

How does the system know if new content matches an existing topic?

**Layer 1 [ROBOT]: Keyword/tag matching (fast, free)**
- Every truth document has tags: `["ai-seo", "search-optimization", "content-strategy"]`
- New content gets auto-tagged from its title, description, and first 500 words
- If tag overlap > 60% — it's a match, send to Sword Sharpener
- If tag overlap 30-60% — ambiguous, escalate to Layer 2
- If tag overlap < 30% — no match, create new truth document

**Layer 2 [AGENT]: Semantic similarity (when keywords are ambiguous)**
- Send both the truth document summary and the new content summary to Claude Haiku
- Prompt: "Are these about the same topic? Rate similarity 0-100. If >70, they match."
- This catches cases where different words describe the same concept (e.g., "prompt engineering" vs "prompt design")

**The system suggests matches:**
```
This video looks 85% similar to your "AI SEO" truth document.

[Sharpen It]  [New Topic Instead]  [Skip]
```

### The Sword Sharpener (Diff Engine)

Once a match is confirmed, the Sharpener runs:

**Prompt (Claude Sonnet):**
```
You are a knowledge analyst. You have two documents:

1. TRUTH DOCUMENT (the current single source of truth for this topic):
{truth_document_content}

2. NEW CONTENT (just ingested):
{new_content}

Your job: identify ONLY what the new content contains that is NOT already
in the truth document. Be strict. If a concept is already covered, even
with different words, it's not new.

Return:
1. NEW_INSIGHTS — List of genuinely new information, techniques, data points,
   or perspectives not in the truth document. Be specific.
2. CONTRADICTIONS — Anything that directly contradicts the truth document.
3. VERDICT — "new_value" (has new insights) or "nothing_new" (fully absorbed)
4. MERGE_SUGGESTION — If new_value, show exactly what text to add and where
   in the truth document it belongs.
```

**If verdict = "nothing_new":**
- Log: "Absorbed [source title]. Nothing new for [topic]."
- Increment the truth doc's `sources_absorbed` counter
- Done. No changes to truth doc.

**If verdict = "new_value":**
- Show the diff to the user (or auto-merge if auto-approve is on)
- Merge new insights into the truth document
- Increment version number
- Add source to the truth doc's source list

### Truth Document Data Model

```python
class TruthDocument:
    id: str                        # UUID
    title: str                     # "AI SEO" / "Prompt Engineering" / etc.
    slug: str                      # URL-safe: "ai-seo"
    content: str                   # The actual truth document (markdown)
    summary: str                   # 2-3 sentence summary for matching
    tags: list[str]                # Keywords for Layer 1 matching
    version: int                   # Incremented on each merge
    sources: list[SourceRef]       # All content that fed into this doc
    sources_absorbed: int          # Count of "nothing new" sources
    created_at: datetime
    updated_at: datetime
    quality_score: float | None    # From self-improvement loop (0-1)

class SourceRef:
    url: str | None                # Original URL (if applicable)
    title: str                     # Source title
    source_type: str               # "youtube" | "article" | "pdf" | "paste"
    ingested_at: datetime
    verdict: str                   # "new_value" | "nothing_new"
    insights_added: list[str]      # What was merged (empty if nothing_new)
```

**Storage:** SQLite at `~/.autoforge/timonacci_labs.db`

### Version History

Every merge creates a version snapshot:

```python
class TruthDocVersion:
    id: str
    truth_doc_id: str              # FK to TruthDocument
    version: int
    content: str                   # Full content at this version
    diff_from_previous: str        # What changed
    source_that_triggered: str     # Which source caused this version
    created_at: datetime
```

Users can browse version history and roll back if a bad merge got through.

### The Scale Play

```
Day 1:   Upload video #1 about AI SEO     → New truth doc created (v1)
Day 3:   Upload video #2 about AI SEO     → +12% new insights (v2)
Day 7:   Upload article #1 about AI SEO   → +8% new (v3)
Day 10:  Upload video #3 about AI SEO     → Nothing new. Absorbed.
Day 14:  Upload video #4 about AI SEO     → +5% new (v4)
Day 21:  Upload video #5 about AI SEO     → Nothing new. Absorbed.
Day 28:  Upload PDF about AI SEO          → +3% new (v5)

Result: Truth doc v5 covers 99% of everything known about AI SEO.
        Synthesized from 7 sources. Sharper than any single one.
        2 sources had nothing new — system saved you the time of reading them.
```

---

## Core Concept 2: The Diverter (Universal Distribution)

Once content is ingested and the truth document is updated, the Diverter analyzes: **"What can we DO with this knowledge?"**

```
TRUTH DOCUMENT (updated)
        |
        v
   DIVERTER AI — "What can we build from this?"
        |
        +---> Skill (.claude/skills/skill.md)
        |         -> Auto-runs SkillForge refinement loop
        |
        +---> Prompt (reusable prompt for any context)
        |         -> Added to prompt library
        |
        +---> Reference file (.md context file)
        |         -> Attached to relevant skill's context folder
        |
        +---> Plugin/MCP tool connector
        |         -> Added to tool chamber
        |
        +---> App/Feature PRD
        |         -> Dropped into Shredder queue
        |
        +---> Build Rule
        |         -> Added to Stripe Blueprint rules
        |
        +---> Tool Steps (existing YT Lab extraction)
        |         -> Same pipeline as today
        |
        +---> Training Data
                  -> Fed into SkillForge eval assertions
```

### How Routing Works

**Step 1: Analysis**

After a truth document merge (or new creation), the Diverter runs:

**Prompt (Claude Sonnet):**
```
You are a knowledge router. You've just received an updated truth document
about "{topic}". Analyze what actionable outputs can be created from this
knowledge.

Truth Document:
{truth_document_content}

New insights just added (if any):
{latest_diff}

For each possible output, assess:
1. TYPE — skill | prompt | reference | plugin | prd | build_rule | tool_steps | training
2. TITLE — what would this output be called?
3. DESCRIPTION — one sentence on what it does
4. CONFIDENCE — how confident are you this is worth creating? (0-100)
5. CONTENT_PREVIEW — first 100 words of what the output would contain
6. DESTINATION — exact file path or system location

Only suggest outputs with confidence > 60.
```

**Step 2: User Review (or Auto-Approve)**

```
The Diverter found 5 possible outputs from "AI SEO" truth doc:

[x] Skill: ai-seo-audit (confidence: 92%)
    -> .claude/skills/ai-seo-audit.md

[x] Reference: seo-ranking-factors-2026 (confidence: 88%)
    -> .claude/skills/ai-seo-audit/context/ranking-factors.md

[x] Reference: ai-content-detection-bypass (confidence: 85%)
    -> .claude/skills/ai-seo-audit/context/detection-bypass.md

[x] PRD: seo-dashboard-feature (confidence: 78%)
    -> docs/prd-seo-dashboard.md -> Shredder queue

[ ] Plugin: google-search-console-connector (confidence: 55%)
    -> Skipped (below threshold)

[Route Selected]  [Route All]  [Skip All]
```

**Step 3: Auto-Distribution**

For each approved output, the system creates it:

- **Skills:** Creates `skill.md`, generates `eval.json` with binary assertions, kicks off SkillForge refinement loop
- **Reference files:** Creates `.md` file in the skill's context directory
- **Prompts:** Adds to the prompt library database
- **PRDs:** Writes the PRD file to `docs/`, auto-drops into Shredder queue
- **Build rules:** Appends to the Stripe Blueprint rules file
- **Tool steps:** Routes through existing YT Lab step extraction pipeline
- **Training data:** Generates eval assertions and adds to SkillForge

### Auto-Routing Mode

For trusted topic categories, skip human review entirely:

```python
class DiverterConfig:
    auto_approve_types: list[str]     # e.g. ["reference", "training"]
    auto_approve_above: int           # confidence threshold, e.g. 85
    require_review_types: list[str]   # e.g. ["prd", "plugin"]
    notify_on_auto: bool              # Toast notification when auto-routing
```

**The dream:** Feed content before bed. Wake up to new skills, new reference files, new tools. The system routed everything while you slept.

---

## Core Concept 3: Self-Improving System (Karpathy Loop Applied to Everything)

The entire system improves itself using binary assertion patterns — the same approach that makes SkillForge work, but applied to every layer.

### Layer 1: Truth Document Quality

**Assertions:**
- "Does the truth doc cover all major subtopics for this domain?"
- "Are there internal contradictions?"
- "Is it actionable (has steps, not just theory)?"
- "Is it under 5000 words (concise, not bloated)?"
- "Would an expert in this field agree with the claims?"

**The loop:**
1. Generate 10 test queries someone might ask about this topic
2. Feed each query + the truth document to an AI
3. Ask: "Can this truth document fully answer this question?"
4. If NO — flag the gap, suggest what's missing
5. Track gap rate over time — it should decrease as more sources are absorbed

### Layer 2: Diverter Accuracy

**Assertions:**
- "Did the skill it generated actually work when tested?"
- "Did the reference file get used by an agent within 30 days?"
- "Was the PRD buildable by the Shredder without errors?"
- "Did the prompt produce useful output when used?"

**The loop:**
1. Track which routed outputs succeed vs fail
2. Track which outputs get used vs gather dust
3. Feed success/failure data back into the Diverter prompt
4. Over time, it stops suggesting outputs that never get used

### Layer 3: Matching Accuracy

**Assertions:**
- "Did it correctly match new content to existing topics?"
- "Were there false positives (matched to the wrong topic)?"
- "Were there misses (didn't match when it should have)?"

**The loop:**
1. After every match decision, log: content title, matched topic, confidence score
2. User can flag incorrect matches: "This wasn't about AI SEO, it was about AI copywriting"
3. Feed corrections back into matching tags and thresholds
4. Track accuracy rate — should approach 95%+ after 50 pieces of content

### Layer 4: Extraction Quality (Already Exists)

The existing SkillForge binary assertion loop for individual skills. No changes needed — it plugs right in.

### Self-Improvement Dashboard

```
SYSTEM HEALTH
=============

Truth Document Quality:
  32 truth docs   avg quality: 87%   gaps found: 4   last check: 2h ago

Diverter Accuracy:
  142 outputs routed   success rate: 79%   unused: 12   last 30 days

Matching Accuracy:
  89 matches made   accuracy: 93%   false positives: 3   misses: 2

Skill Quality (SkillForge):
  47 skills   avg score: 84%   improving: 8   plateaued: 39
```

---

## Architecture

```
CONTENT IN
  YouTube URLs ─────┐
  Article URLs ─────┤
  PDF uploads ──────┤──→ INGESTION ──→ MATCHER ──→ SWORD SHARPENER ──→ TRUTH DOC
  Raw text paste ───┤                    |                                  |
  Transcripts ──────┘                    |                                  |
                                    No match?                               |
                                    Create new                              |
                                    truth doc                               |
                                                                            v
                                                                       DIVERTER
                                                                    What can we DO?
                                                                            |
                                    ┌───────────────────────────────────────┤
                                    |           |          |                |
                                    v           v          v                v
                                  Skill      Prompt    Reference         PRD
                                    |                      |                |
                                    v                      v                v
                                SkillForge            Skill context     Shredder
                                refinement            folder           queue
                                    |
                                    v
                               SELF-IMPROVEMENT LOOPS
                               ├── Truth doc quality
                               ├── Diverter accuracy
                               ├── Matching accuracy
                               └── Skill quality (SkillForge)
```

---

## Multi-Source Ingestion

YT Lab already handles YouTube. The system needs to normalize ALL content into the same format so the Matcher doesn't care where it came from.

### Ingestion Adapters

```python
class IngestedContent:
    """Universal format — every source converts to this."""
    source_type: str           # "youtube" | "article" | "pdf" | "paste"
    source_url: str | None     # Original URL
    title: str                 # Content title
    raw_text: str              # Full text content
    structured_text: str       # Cleaned, formatted markdown
    metadata: dict             # Source-specific (channel, author, date, etc.)
    ingested_at: datetime
```

| Source | Adapter | How It Works |
|---|---|---|
| YouTube | Existing YT Lab pipeline | Transcript extraction (already built) |
| Article (URL) | `article_adapter.py` | Fetch URL, strip HTML, extract article body |
| PDF | `pdf_adapter.py` | Extract text from PDF pages |
| Raw text | `paste_adapter.py` | User pastes text directly — minimal processing |
| Transcript | `transcript_adapter.py` | Raw transcript file (.txt, .srt) — clean and format |

After ingestion, every source is just a `IngestedContent` object. The Matcher and Sharpener don't know or care where it came from.

---

## Phases

### Phase 1: Truth Document System

**What it gets you:** The core innovation — truth documents that get sharper with every source.

| Task | Difficulty |
|---|---|
| Truth document SQLAlchemy models | 2/10 |
| Topic matching — keyword Layer 1 | 3/10 |
| Topic matching — semantic Layer 2 | 4/10 |
| Sword Sharpener diff engine | 5/10 |
| Version history + rollback | 3/10 |
| Truth doc CRUD API endpoints | 3/10 |
| Basic truth doc viewer UI | 4/10 |

**Phase difficulty: 5/10**

### Phase 2: Multi-Source Ingestion

**What it gets you:** Accept any content type, not just YouTube.

| Task | Difficulty |
|---|---|
| Universal `IngestedContent` model | 2/10 |
| Article adapter (URL scrape) | 3/10 |
| PDF adapter | 3/10 |
| Raw text paste adapter | 1/10 |
| Transcript adapter | 2/10 |
| Unified ingestion API endpoint | 3/10 |
| Multi-source upload UI | 4/10 |

**Phase difficulty: 4/10**

### Phase 3: The Diverter

**What it gets you:** Knowledge auto-routes to the right destination.

| Task | Difficulty |
|---|---|
| Diverter analysis prompt | 4/10 |
| Routing engine (dispatch to each destination) | 5/10 |
| Human-in-loop review UI (checkboxes + preview) | 5/10 |
| Auto-approve mode with confidence thresholds | 3/10 |
| Skill generation output handler | 4/10 |
| Reference file output handler | 3/10 |
| PRD output handler (drop into Shredder) | 3/10 |
| Prompt library output handler | 3/10 |

**Phase difficulty: 6/10**

### Phase 4: Auto-Distribution

**What it gets you:** The Diverter doesn't just suggest — it actually creates the outputs.

| Task | Difficulty |
|---|---|
| Skill creation + SkillForge integration | 5/10 |
| Reference file creation in skill context folders | 3/10 |
| PRD auto-drop into Shredder queue | 3/10 |
| Eval.json auto-generation for new skills | 5/10 |
| Build rule appender | 3/10 |
| Distribution confirmation + logging | 3/10 |

**Phase difficulty: 6/10**

### Phase 5: Self-Improvement Loops

**What it gets you:** The system tracks its own accuracy and gets better automatically.

| Task | Difficulty |
|---|---|
| Truth doc quality assertions + test query generation | 5/10 |
| Diverter accuracy tracking (success/fail/unused) | 4/10 |
| Matching accuracy tracking + correction UI | 4/10 |
| Self-improvement dashboard UI | 4/10 |
| Overnight refinement scheduler | 3/10 |

**Phase difficulty: 5/10**

### Phase 6: Scale Mode

**What it gets you:** Batch upload, overnight factory, full dashboard.

| Task | Difficulty |
|---|---|
| Batch upload (drop 20 URLs, process all) | 4/10 |
| Queue processing with progress tracking | 4/10 |
| Overnight factory (queue before bed, wake up to results) | 3/10 |
| Coverage dashboard (truth doc stats, diverter stats, system health) | 4/10 |
| Rate limit awareness for batch processing | 3/10 |

**Phase difficulty: 4/10**

### Implementation Order

```
Phase 1          Phase 2            Phase 3         Phase 4           Phase 5           Phase 6
Truth Docs  -->  Multi-Source  -->  Diverter  -->  Auto-Distribute  -->  Self-Improve  -->  Scale
  5/10             4/10              6/10            6/10                5/10              4/10
```

**Total: ~30/60 difficulty. Six phases. Each is independently useful.**

---

## Files To Create

| File | Phase | Purpose |
|---|---|---|
| `server/models/truth_document.py` | 1 | SQLAlchemy models: TruthDocument, TruthDocVersion, SourceRef |
| `server/services/truth_document_service.py` | 1 | CRUD + version history + tag management |
| `server/services/topic_matcher.py` | 1 | Layer 1 keyword + Layer 2 semantic matching |
| `server/services/sword_sharpener.py` | 1 | Diff engine: compare new content vs truth doc, extract new insights |
| `server/routers/truth_documents.py` | 1 | REST endpoints for truth doc CRUD, matching, sharpening |
| `ui/src/pages/TruthDocumentsPage.tsx` | 1 | Truth doc list, viewer, version history |
| `ui/src/components/timonacci/TruthDocViewer.tsx` | 1 | Single truth doc display with version diff |
| `ui/src/components/timonacci/SwordSharpenerView.tsx` | 1 | Diff review UI (new insights + merge approval) |
| `server/services/ingestion/article_adapter.py` | 2 | URL fetch + HTML strip + article extraction |
| `server/services/ingestion/pdf_adapter.py` | 2 | PDF text extraction |
| `server/services/ingestion/paste_adapter.py` | 2 | Raw text paste handler |
| `server/services/ingestion/transcript_adapter.py` | 2 | Transcript file cleanup |
| `server/services/ingestion/base_adapter.py` | 2 | Base adapter class + IngestedContent model |
| `server/routers/ingestion.py` | 2 | Universal ingestion endpoint (accepts any source type) |
| `ui/src/components/timonacci/ContentUpload.tsx` | 2 | Multi-source upload UI (URL, file, paste) |
| `server/services/diverter.py` | 3 | Analysis prompt + routing engine |
| `server/services/diverter_handlers/skill_handler.py` | 3-4 | Creates skills + kicks off SkillForge |
| `server/services/diverter_handlers/reference_handler.py` | 3-4 | Creates reference files in skill context |
| `server/services/diverter_handlers/prd_handler.py` | 3-4 | Creates PRDs + drops into Shredder queue |
| `server/services/diverter_handlers/prompt_handler.py` | 3-4 | Adds to prompt library |
| `server/services/diverter_handlers/build_rule_handler.py` | 3-4 | Appends build rules |
| `server/routers/diverter.py` | 3 | Diverter endpoints (analyze, route, auto-route) |
| `ui/src/components/timonacci/DiverterReview.tsx` | 3 | Checkbox review UI for routing decisions |
| `ui/src/pages/TimonacciLabsPage.tsx` | 3 | Main hub page (replaces/extends YT Lab) |
| `server/services/self_improvement.py` | 5 | Assertion loops for all 4 layers |
| `server/services/accuracy_tracker.py` | 5 | Logs match decisions, diverter outcomes, corrections |
| `ui/src/components/timonacci/SystemHealthDashboard.tsx` | 5 | Self-improvement metrics dashboard |
| `server/services/batch_processor.py` | 6 | Batch URL processing + queue management |
| `ui/src/components/timonacci/BatchUpload.tsx` | 6 | Drop 20 URLs, track progress |

## Files To Modify

| File | Phase | Changes |
|---|---|---|
| `ui/src/App.tsx` | 1 | Add Timonacci Labs route |
| `server/main.py` | 1 | Register truth document router |
| `server/main.py` | 2 | Register ingestion router |
| `server/main.py` | 3 | Register diverter router |
| `server/services/yt_processor.py` | 2 | Pipe YT Lab output into universal ingestion format |
| `server/services/prd_shredder.py` | 4 | Accept PRDs from Diverter auto-drop |
| `server/services/scheduler_service.py` | 5-6 | Add overnight refinement + batch processing schedules |
| `ui/src/pages/YTStrategyLabPage.tsx` | 2 | Add link/redirect to Timonacci Labs for ingested content |

---

## The Timonacci Labs UI

### Main Hub Page

```
┌────────────────────────────────────────────────────────────────────────┐
│  TIMONACCI LABS                                           [Settings]  │
│  ═══════════════                                                      │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  DROP CONTENT HERE                                              │  │
│  │                                                                  │  │
│  │  [Paste URL]  [Upload PDF]  [Paste Text]  [Batch URLs]          │  │
│  │                                                                  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  TRUTH DOCUMENTS (32)                                    [View All]   │
│  ─────────────────────                                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐│
│  │ AI SEO       │ │ Prompt Eng   │ │ MCP Tools    │ │ Claude Code  ││
│  │ v5 · 7 src   │ │ v8 · 12 src  │ │ v3 · 4 src   │ │ v6 · 9 src   ││
│  │ 87% quality  │ │ 94% quality  │ │ 78% quality  │ │ 91% quality  ││
│  │ Updated 2d   │ │ Updated 4h   │ │ Updated 1w   │ │ Updated 1d   ││
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘│
│                                                                        │
│  RECENT ACTIVITY                                                      │
│  ───────────────                                                      │
│  14:32  Absorbed "AI SEO Masterclass" → Nothing new for "AI SEO"     │
│  14:28  Sharpened "Prompt Engineering" → +3 new techniques (v8)      │
│  14:25  Diverted → Created skill: advanced-prompt-chaining           │
│  14:20  New truth doc: "Agentic Workflows" created from PDF          │
│                                                                        │
│  SYSTEM HEALTH                                                        │
│  ─────────────                                                        │
│  Truth Docs: 32  │  Matching: 93%  │  Diverter: 79%  │  Skills: 47  │
│                                                                        │
│  QUEUE: 3 items processing  │  OVERNIGHT: 12 items scheduled         │
└────────────────────────────────────────────────────────────────────────┘
```

### Truth Document Detail View

```
┌────────────────────────────────────────────────────────────────────────┐
│  ← Back to Hub                                                        │
│                                                                        │
│  AI SEO — Truth Document v5                                           │
│  ═════════════════════════════                                        │
│  Tags: ai-seo, search-optimization, content-strategy, serp-ranking   │
│  Quality: 87%  │  Sources: 7 (5 absorbed, 2 nothing-new)             │
│  Last updated: 2 days ago                                             │
│                                                                        │
│  ┌──────────────────────────┐  ┌──────────────────────────────────┐  │
│  │  SOURCES                 │  │  CONTENT                         │  │
│  │                          │  │                                   │  │
│  │  v5: PDF "SEO Guide"    │  │  # AI SEO: Complete Truth Doc    │  │
│  │      +3% new · Mar 12   │  │                                   │  │
│  │                          │  │  ## Core Principles              │  │
│  │  --: Video "SEO Tips"   │  │  1. Search intent matching...    │  │
│  │      nothing new · Mar 8│  │  2. Content quality signals...   │  │
│  │                          │  │  3. Technical SEO baseline...    │  │
│  │  v4: Video "AI Content" │  │                                   │  │
│  │      +5% new · Feb 28   │  │  ## Advanced Techniques          │  │
│  │                          │  │  - Programmatic SEO with AI...   │  │
│  │  v3: Article "SERP AI"  │  │  - Entity optimization...        │  │
│  │      +8% new · Feb 14   │  │                                   │  │
│  │                          │  │  ## Tools & Implementation       │  │
│  │  ...                     │  │  ...                              │  │
│  └──────────────────────────┘  └──────────────────────────────────┘  │
│                                                                        │
│  DIVERTED OUTPUTS                                                     │
│  ────────────────                                                     │
│  Skill: ai-seo-audit (score: 84%)                                    │
│  Reference: ranking-factors-2026.md                                   │
│  Reference: content-detection-bypass.md                               │
│  PRD: seo-dashboard → Shredder (built, commit abc1234)               │
│                                                                        │
│  [Sharpen with new content]  [View version history]  [Re-run Diverter]│
└────────────────────────────────────────────────────────────────────────┘
```

---

## Success Criteria

1. **Phase 1:** Upload a YouTube video. System creates a truth document. Upload a second video on the same topic. System matches it, runs Sword Sharpener, shows what's new, merges it. Truth doc is now v2.
2. **Phase 2:** Upload an article URL, a PDF, and paste raw text. All three get normalized and fed through the same pipeline. System doesn't care about the source type.
3. **Phase 3:** After truth doc update, Diverter presents routing options. User checks boxes, system creates the selected outputs in the correct locations.
4. **Phase 4:** Diverter auto-creates a skill. SkillForge picks it up and refines it. Diverter auto-drops a PRD into the Shredder. Shredder builds it. No human intervention between ingestion and output.
5. **Phase 5:** Self-improvement dashboard shows truth doc quality, diverter accuracy, and matching accuracy. All metrics trend upward over time.
6. **Phase 6:** Drop 20 URLs into batch upload. Walk away. Come back to 20 processed pieces of content, 8 truth docs updated, 4 new truth docs created, 12 outputs routed and built.

---

## CRITICAL: Capacity Management — Don't Clog the System

### The Problem

Every output destination has limits. If the Diverter just keeps creating skills, reference files, prompts, and tools without restraint, it will:
- Create 200 skills when Claude can only effectively trigger from ~30-40
- Stuff skill descriptions past character limits (YAML descriptions have a sweet spot)
- Add 50 reference files to one skill when the context window can only handle 5-10
- Generate duplicate prompts that overlap with existing ones
- Create tools that duplicate existing tool chamber capabilities
- Flood the PRD Shredder queue with low-priority items

### The Solution: Per-Destination Capacity Limits + Self-Optimization

Each destination the Diverter routes to gets **hard limits, soft limits, and smart consolidation logic.**

#### Skills (.claude/skills/)
- **Hard limit:** 40 active skills max (beyond this, activation accuracy drops because descriptions compete)
- **Soft limit:** 25 skills (warning zone — start consolidating)
- **Description limit:** ~200 chars for YAML description (longer = worse triggering)
- **Self-optimization:**
  - When approaching soft limit, AI analyzes: "Can any 2-3 skills be MERGED into one broader skill?"
  - Track activation rates — skills that never trigger get flagged for removal or merger
  - Skills with <10% activation after 2 weeks → auto-archive
  - Before creating a new skill, check: "Does an existing skill already cover 80%+ of this?" → enhance existing instead

#### Reference Files (skill context)
- **Hard limit:** 8 reference files per skill (context window budget)
- **Total size limit:** ~50KB per skill's reference files combined
- **Self-optimization:**
  - When a skill hits 8 files, AI must MERGE the least-used two before adding a new one
  - Track which reference files actually get used in outputs — unused files get flagged
  - Consolidate overlapping reference files: "tone-of-voice.md" + "brand-voice.md" → merge into one

#### Prompts (prompt library)
- **Hard limit:** 100 prompts per category
- **Dedup check:** Before creating a new prompt, semantic similarity check against existing prompts
  - >85% similar → don't create, enhance the existing one
  - 60-85% similar → flag for human review: "This is similar to prompt X — merge or keep both?"
  - <60% similar → create new prompt
- **Self-optimization:**
  - Track prompt usage frequency — unused prompts get archived after 30 days
  - Merge prompts that always get used together

#### Tool Chamber Connectors
- **Hard limit:** Based on the component registry — don't create duplicate connectors
- **Dedup check:** Before building a new connector, check: "Does the component registry already have something that handles this?"
- **Self-optimization:**
  - Track tool usage — connectors that never get selected by the AI router get flagged
  - Consolidate tools that do similar things

#### PRD Shredder Queue
- **Hard limit:** 10 items in queue max (prevent overwhelming overnight builds)
- **Priority scoring:** Each PRD gets a priority score based on:
  - How many other things it unblocks
  - How many truth documents reference it
  - How recently the topic was ingested
- **Self-optimization:**
  - Low-priority PRDs that sit in queue for 7+ days get auto-archived
  - PRDs that fail to build twice get removed and flagged for human review

#### Truth Documents
- **Size limit:** 5,000 words max per truth document (beyond this, it's too long for effective use)
- **When approaching limit:** AI must DISTILL — cut redundancies, merge similar points, tighten language
- **Version limit:** Keep last 5 versions only (save disk space)
- **Self-optimization:**
  - Track which sections of truth docs actually get used downstream
  - Sections never referenced in skills/prompts/tools → candidates for trimming
  - Periodic "spring cleaning" pass: "Can this 4,500 word doc be tightened to 3,000 without losing value?"

### The Capacity Dashboard

```
SYSTEM CAPACITY
═══════════════════════════════════════════
Skills:          23/40  ████████████░░░░░░  58%  ✅ Healthy
Ref Files (avg): 4.2/8  █████████░░░░░░░░░  53%  ✅ Healthy
Prompts:         67/100 █████████████░░░░░  67%  ⚠️ Watch
Tool Connectors: 6/15   ███████░░░░░░░░░░░  40%  ✅ Healthy
Shredder Queue:  3/10   ██████░░░░░░░░░░░░  30%  ✅ Healthy
Truth Docs:      12     (no hard limit)      -   ✅ Healthy

ACTIONS NEEDED:
• 2 skills have <10% activation — consider archiving
• 3 reference files unused in 14 days — review
• Prompt category "marketing" at 89/100 — consolidation recommended
```

### The Core Rule: ENHANCE BEFORE CREATE

The #1 anti-clog rule across ALL destinations:

**Before creating anything new, ALWAYS check: can we make something existing better instead?**

- New skill idea? → Check if existing skill can absorb it
- New reference file? → Check if existing file can be extended
- New prompt? → Check if existing prompt covers it
- New tool? → Check if existing tool handles this case
- New truth doc? → Check if an existing topic is close enough to merge

This is the difference between a hoarder and an optimizer. The system should get **SHARPER, not BIGGER.** Quality over quantity at every level.

### Self-Optimization Loops (Capacity-Specific)

Binary assertions for the overnight Karpathy loops:

**Skills capacity loop:**
- "Total active skills < 40" → binary
- "No skill has < 10% activation rate" → binary
- "No skill description exceeds 200 chars" → binary
- "No two skills have > 80% description overlap" → binary

**Reference files capacity loop:**
- "No skill has > 8 reference files" → binary
- "No skill's reference files total > 50KB" → binary
- "No reference file has been unused for > 14 days" → binary

**Truth doc capacity loop:**
- "No truth doc exceeds 5,000 words" → binary
- "All truth docs have been used in at least one downstream output" → binary
- "No two truth docs have > 70% topic overlap" → binary

---

## Core Concept 4: Human Context Layer (The Nyne Pattern)

### The Insight

Every agent in the system knows about the BUSINESS but knows nothing about the PEOPLE — not the user, not clients, not prospects. Nyne (nyne.ai) built exactly this: a person-level context graph that AI agents load before taking any action. They stitch together public data (social profiles, posts, interests, company, role) into one unified profile via 24 APIs.

**We don't need to rebuild Nyne.** We steal the concept and apply it two ways:

### Way 1: Personal Context File (Your Own Graph)

A structured truth document about YOU that every agent loads first:

```yaml
# ~/.autoforge/human-context/owner.md
name: [owner name]
role: Solo founder, non-technical
working_style:
  - Thinks in creative leaps, not linear steps
  - Tests ideas by throwing options at the wall
  - Wants fast results, iterates from there
  - Not a coder — needs plain language explanations
decision_history:
  - Chose subscription auth over API keys (cost control)
  - Chose neobrutalism design (stands out)
  - Chose Stripe Blueprint pattern (deterministic + AI hybrid)
  - Chose overnight automation (rate limits are free at night)
current_goals:
  - Timonacci Labs as universal knowledge hub
  - Tool chamber for YT Lab step execution
  - SkillForge for overnight skill refinement
  - Scale to 3 tools per day from YouTube content
constraints:
  - Subscription-only (no API credit burn)
  - Windows laptop as primary dev machine
  - VPS planned for computer use / Playwright
  - Rate limits matter during working hours
```

**Every agent session pre-loads this.** The consultant agent, the builder agents, the tool pipeline — they all start with context about who they're working for. This is what the consultant foundation prompt already does manually. This makes it automatic and persistent.

### Way 2: Client/Prospect Context (For Business Use)

When the Astro theme business or any client-facing tool launches:

1. Prospect lands on site → grab email
2. Hit Nyne's enrichment API (free trial available) → get role, company, tech stack, interests
3. AI sales agent or onboarding flow already knows who they are
4. Agent personalizes the entire experience before they type a word

**API integration for the tool chamber:**
- `nyne_person_enrichment` — component in the tool chamber registry
- Takes: email, phone, or social URL
- Returns: full profile (role, company, interests, social activity)
- The Diverter can route this to: personalized skill outputs, client truth documents, sales agent context

### Way 3: Person Truth Documents

Just like topic truth documents, but for people:

```
Client: John Smith
Role: VP Marketing at TechCo
Sources: LinkedIn profile, 3 email threads, 2 meeting transcripts
Truth doc:
  - Cares about: SEO automation, content scaling, team efficiency
  - Pain points: Manual content creation, inconsistent brand voice
  - Decision style: Data-driven, needs ROI numbers
  - Budget authority: Yes, up to $50K/year
  - Last interaction: 2026-03-10, discussed AI SEO tool demo
```

The Sword Sharpener works the same way — each new interaction with a person sharpens their truth document. After 5 meetings, you know exactly what they care about, how they decide, and what language resonates.

### What This Unlocks

```
WITHOUT human context:
  Agent: "Here's a generic proposal for AI SEO services."

WITH human context:
  Agent: "John, based on your team's current manual content workflow
  and your Q2 goal of 3x organic traffic, here's a proposal focused
  on ROI metrics since I know that's how you evaluate tools.
  Budget is structured under your $50K authority threshold."
```

Every agent in the stack gets smarter about people, not just topics.

### Implementation

- **Phase 1:** Personal context file for the owner (manual, load into all agents)
- **Phase 2:** Nyne API integration as a tool chamber component (enrichment on demand)
- **Phase 3:** Person truth documents with Sword Sharpener (auto-improve from interactions)
- **Phase 4:** Auto-load person context into any agent that interacts with clients

**Files:**
- `~/.autoforge/human-context/owner.md` — owner's personal context
- `~/.autoforge/human-context/{person_id}.md` — per-person truth docs
- `server/services/person_context.py` — person context management
- `server/services/nyne_client.py` — Nyne API integration (optional, for enrichment)

---

## Core Concept 5: Firehose Ingestion — Saturate Then Maintain

### The Usage Pattern

There are two modes of operation:

**Mode 1: Saturation Sprint (first 1-2 weeks)**
- User dumps EVERYTHING they've been collecting — 50-100 videos, articles, bookmarks, notes
- The system ingests at scale, builds 20-30 truth documents, routes knowledge everywhere
- After the sprint, the system is "caught up" to everything the user knows
- This is the "filling the storage unit" phase — but with capacity management so it stays organized

**Mode 2: Maintenance Drip (ongoing)**
- User pastes 1-3 new things per day as they find them
- System matches to existing truth docs, sharpens, routes
- Most new content adds 5-10% new value — quick merge, done
- Occasional new topic creates a new truth document
- This is the "keeping the edge sharp" phase

### Firehose Ingestion Interface

The saturation sprint needs to be FAST. No friction. Multiple input methods:

```
┌─────────────────────────────────────────────────────────┐
│  TIMONACCI LABS — INGEST                                 │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Paste URLs, text, or drag files here              │  │
│  │                                                    │  │
│  │  https://youtube.com/watch?v=abc123                │  │
│  │  https://youtube.com/watch?v=def456                │  │
│  │  https://blog.example.com/ai-seo-guide             │  │
│  │  https://twitter.com/elonmusk/status/123456        │  │
│  │                                                    │  │
│  │  (paste as many as you want — one per line)        │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  Or: [Upload PDF/TXT files]  [Paste raw text]            │
│                                                          │
│  [🔥 Ingest All]                                        │
│                                                          │
│  QUEUE: 47 items                                         │
│  ✅ Processed: 12  🔄 Processing: 1  ⏳ Waiting: 34    │
│                                                          │
│  Recent:                                                 │
│  ✅ "AI SEO Masterclass" → matched to AI SEO truth doc  │
│     → 3 new insights merged, 2 were duplicates           │
│  ✅ "Cold Email That Works" → NEW truth doc created     │
│     → routed to: skill, 2 ref files, 1 prompt            │
│  🔄 "Advanced Playwright Tips" → processing...          │
└─────────────────────────────────────────────────────────┘
```

### Input Methods

| Method | How | What It Handles |
|---|---|---|
| **Multi-URL paste** | Paste 1-50 URLs, one per line | YouTube, articles, blog posts, tweets |
| **File drag-and-drop** | Drag PDFs, TXT, MD files onto the page | Documents, reports, exported notes |
| **Raw text paste** | Paste text directly into a text box | Meeting notes, copy-pasted content, ideas |
| **Bookmarks import** | Upload browser bookmarks HTML export | Batch import saved articles |
| **Watch folder** | Drop files into `~/.autoforge/ingest/` | Automated — anything in the folder gets processed |
| **API endpoint** | `POST /api/ingest` with content | Programmatic — other tools can feed the system |

### Processing Pipeline Per Item

```
INPUT (URL / file / text)
    ↓
[ROBOT] Detect type:
  YouTube URL → yt-dlp + transcript API
  Article URL → web scrape + readability extract
  PDF file → text extraction (pdftotext)
  Raw text → use as-is
    ↓
[ROBOT] Clean + normalize to plain text
    ↓
[ROBOT] Keyword extract → check against existing truth doc tags
    ↓
[AGENT] If ambiguous match → semantic similarity check
    ↓
MATCH RESULT:
  ├── Strong match (>80%) → Sword Sharpener (diff + merge)
  ├── Weak match (50-80%) → suggest to user: "Match to X?"
  └── No match (<50%) → create new truth document
    ↓
[AGENT] Extract value (new insights only if matching)
    ↓
[ROBOT] Update truth document + version
    ↓
[AGENT] Diverter: "What can we do with this?"
    ↓
[ROBOT] Route to destinations (with capacity checks)
    ↓
DONE — next item in queue
```

### Rate Limit Strategy for Saturation Sprint

During a sprint, you might ingest 50 items. Each one needs 1-3 AI calls. That's 50-150 Claude calls.

**Strategy:**
- Process items in priority order (not FIFO — smart ordering)
- [ROBOT] steps (scraping, cleaning, keyword matching) run instantly, no rate limit
- [AGENT] steps (semantic matching, extraction, diverting) are rate-limited
- Space AI calls with rate limit awareness (same pattern as PRD Shredder)
- Batch overnight: queue 50 items before bed, wake up to all processed
- Status dashboard shows estimated completion time

**Smart ordering:**
1. Items that match existing truth docs → process first (quick merge, low AI cost)
2. Items that are clearly new topics → process second (need full extraction)
3. Ambiguous matches → process last (need more AI reasoning)

### The Saturation Dashboard

Shows how "caught up" the system is:

```
SATURATION STATUS
═══════════════════════════════════════════
Total ingested:     127 items
Truth documents:    23 topics
Coverage estimate:  ~85% of known topics

TOPIC HEALTH:
AI SEO           ████████████████████  12 sources  [Saturated]
Cold Outreach    ████████████░░░░░░░░   7 sources  [Strong]
Playwright       ████████░░░░░░░░░░░░   4 sources  [Growing]
Email Marketing  ██████░░░░░░░░░░░░░░   3 sources  [Needs more]
Pricing Strategy ████░░░░░░░░░░░░░░░░   2 sources  [Early]

RECENT INGESTION:
Last 24h: 8 items → 5 merges, 2 new docs, 1 no-new-value skip
Last 7d:  34 items → 22 merges, 9 new docs, 3 skips
```

---

## The End State

After 3 months of feeding content:

- **30-50 truth documents** covering every topic the user cares about
- Each truth doc synthesized from **5-20 sources** — sharper than any single source
- **50+ skills** auto-generated and self-refined through SkillForge
- **100+ reference files** distributed to the right skills' context folders
- Tool chamber populated with connectors for common step types
- The system matches new content to existing topics with **95%+ accuracy**
- Feeding a new video takes **30 seconds** (paste URL) and the system does everything else
- The Diverter routes knowledge to skills, PRDs, reference files, and tools **without human review** for trusted categories
- The self-improvement loops have pushed truth doc quality above **90%** and diverter accuracy above **85%**

**The user's only job: find interesting content and paste URLs.**

The system ingests, matches, sharpens, routes, builds, and self-improves. Every piece of content makes the entire system smarter. The knowledge compounds. The tools multiply. The truth documents get razor-sharp.

This is not a note-taking app. This is a knowledge factory.
