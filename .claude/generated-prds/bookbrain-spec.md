# BookBrain — PDF/Book Intelligence Platform
# AutoForge App Spec (SaaS Product)

## Status: Ready for AutoForge Build

## Product Overview

**App Name:** BookBrain
**One-Line Description:** Upload any book, extract structured intelligence, query it forever.
**Target User:** Knowledge workers, entrepreneurs, self-improvement enthusiasts, students, and coaches who read business/self-help/technical books and want to extract, reference, and apply specific techniques without re-reading.
**Core Problem:** You read a life-changing book 5 years ago. There was a technique in Chapter 14 that transformed how you think. You can't remember the exact steps. Re-reading 500 pages to find it is not happening. BookBrain reads the entire book in one pass using a 1M token context window, extracts every technique, concept, and framework into a structured knowledge base, and lets you query it forever.

---

## Dual-Mode Architecture

BookBrain runs in TWO modes, controlled by configuration:

### Mode 1: Personal Use (Claude Code CLI Subscription)

For the owner's personal use. Uses the same mechanism Leon built into AutoForge:

```
BookBrain Python App
      ↓
Claude Agent SDK (ClaudeSDKClient)
      ↓
subprocess: claude --betas context-1m-2025-08-07 --max-turns 50 --model claude-opus-4-6
      ↓
Claude Code CLI (uses your $200/month subscription)
      ↓
Anthropic API (1M context window, no extra cost)
```

**How it works:**
- Same `claude-agent-sdk` package AutoForge uses
- Same `betas=["context-1m-2025-08-07"]` flag for 1M context
- Your Claude Code subscription pays for everything
- No API key needed
- Rate limited by subscription plan (but personal use won't hit limits)

**Configuration:**
```env
BOOKBRAIN_MODE=cli          # Use CLI subscription
# That's it. The SDK auto-detects your Claude Code auth.
```

### Mode 2: SaaS (Anthropic API Key)

For paying customers. Uses direct API calls:

```
BookBrain Web App
      ↓
Anthropic Python SDK (anthropic package)
      ↓
Direct API calls with API key
      ↓
Anthropic API (1M context window, pay-per-token)
```

**How it works:**
- Uses the `anthropic` Python package directly (not the Agent SDK)
- Your API key pays for customer usage
- You meter and bill customers based on usage
- Prompt caching reduces costs for repeat queries on the same book

**Configuration:**
```env
BOOKBRAIN_MODE=api          # Use API key
ANTHROPIC_API_KEY=sk-ant-... # Your API key
```

### Switching Between Modes

The app code is identical — only the "engine" layer changes. A factory function returns the right client:

```python
def get_engine():
    mode = os.getenv("BOOKBRAIN_MODE", "cli")
    if mode == "cli":
        return CLIEngine()    # Uses Claude Agent SDK + CLI subscription
    elif mode == "api":
        return APIEngine()    # Uses anthropic Python package + API key
```

When you build the SaaS version, you just:
1. Set `BOOKBRAIN_MODE=api`
2. Set your `ANTHROPIC_API_KEY`
3. Add usage metering middleware
4. Hide the CLI mode from the settings UI (or leave it for power users who have their own subscription)

---

## Technology Stack

```xml
<technology_stack>
  <frontend>
    <framework>React 19 with TypeScript</framework>
    <styling>Tailwind CSS v4</styling>
    <ui_library>Radix UI (primitives)</ui_library>
    <pdf_rendering>PDF.js for preview, pdf-parse for text extraction</pdf_rendering>
    <state>TanStack Query + Zustand</state>
  </frontend>
  <backend>
    <runtime>Python 3.11+ (FastAPI)</runtime>
    <database>SQLite (via SQLAlchemy)</database>
    <pdf_extraction>PyMuPDF (fitz) for text, pdfplumber for tables</pdf_extraction>
    <ai_engines>
      <cli_engine>claude-agent-sdk (Claude Code CLI wrapper)</cli_engine>
      <api_engine>anthropic Python SDK (direct API)</api_engine>
    </ai_engines>
    <search>SQLite FTS5 (full-text search on extracted content)</search>
  </backend>
  <communication>
    <api>REST + WebSocket (for streaming analysis progress)</api>
  </communication>
</technology_stack>
```

---

## Core Features

### 1. Book Upload & Text Extraction
- Upload PDF, EPUB, or paste raw text
- Extract full text with chapter detection
- Show token count and estimated analysis cost (API mode)
- Show page count, chapter count, word count
- Store extracted text in SQLite for persistence

### 2. Full-Book Analysis (1M Context Window)
- Send entire book text to Claude in a single context window
- Use the 1M beta (`context-1m-2025-08-07`) for full comprehension
- Analysis agent extracts:
  - **Techniques/Frameworks:** Every actionable technique with steps, context, and page references
  - **Key Concepts:** Core ideas and mental models
  - **Chapter Summaries:** Concise summary of each chapter
  - **Cross-References:** Where concepts connect across chapters
  - **Quotes:** Notable quotes with page numbers
  - **Action Items:** Specific things the reader should do
- Real-time progress via WebSocket (streaming analysis output)
- Store structured results in SQLite

### 3. Knowledge Base Browser
- Browse extracted techniques by category
- Search across all extracted content (FTS5)
- Filter by chapter, category, or tag
- Each technique shows: name, summary, detailed steps, page reference, related techniques
- Expand/collapse for progressive disclosure

### 4. Chat Interface (Query Your Books)
- Chat with the knowledge base about the book
- Two query modes:
  - **Quick Query:** Searches structured knowledge base (fast, cheap, works forever)
  - **Deep Dive:** Reloads full book into 1M context for comprehensive analysis (slower, uses more tokens)
- Conversation history persisted in SQLite
- Source citations with page numbers in every response
- Follow-up questions maintain conversation context

### 5. Multi-Book Library
- Upload and analyze multiple books
- Cross-book queries: "Compare Tony Robbins' goal-setting approach with James Clear's habit system"
- Library view with book covers, analysis status, technique counts
- Tags and categories for organizing books

### 6. Context Budget Controls
- Token counter showing current context usage
- Context budget lever in Settings:
  - Backend setting: hard limit on context % (admin-controlled)
  - User setting: personal preference within admin limit
  - Default: 50% of 1M window (500K tokens)
  - Range: 20% to 80%
- Cost estimator (API mode): shows estimated cost before running analysis
- Warning when approaching budget limit
- Auto-stop at configured limit

### 7. Usage Metering (SaaS Mode)
- Track tokens consumed per user per month
- Credit system: users buy credits, each analysis/query costs credits
- Usage dashboard: tokens used, credits remaining, cost breakdown
- Admin dashboard: total usage across all users, revenue tracking

---

## Database Schema

```xml
<database_schema>
  <tables>
    <users>
      - id (PK), email, password_hash, name
      - plan (free/pro/enterprise), credits_remaining
      - context_budget_pct (user preference, default 50)
      - created_at, updated_at
    </users>

    <books>
      - id (PK), user_id (FK), title, author
      - file_path, file_type (pdf/epub/text)
      - total_pages, total_words, total_tokens
      - analysis_status (pending/analyzing/complete/failed)
      - analyzed_at, created_at
    </books>

    <chapters>
      - id (PK), book_id (FK), chapter_number, title
      - start_page, end_page
      - summary (generated), word_count, token_count
    </chapters>

    <techniques>
      - id (PK), book_id (FK), chapter_id (FK)
      - name, category, summary, detailed_steps (JSON)
      - page_start, page_end, page_references (JSON)
      - related_technique_ids (JSON)
      - tags (JSON), confidence_score
    </techniques>

    <concepts>
      - id (PK), book_id (FK), chapter_id (FK)
      - name, description, significance
      - page_references (JSON), related_concept_ids (JSON)
    </concepts>

    <quotes>
      - id (PK), book_id (FK), chapter_id (FK)
      - text, page_number, context, significance
    </quotes>

    <conversations>
      - id (PK), user_id (FK), book_id (FK, nullable for cross-book)
      - title, mode (quick/deep), created_at
    </conversations>

    <messages>
      - id (PK), conversation_id (FK)
      - role (user/assistant), content
      - tokens_used, mode (quick/deep)
      - sources (JSON - page refs, technique IDs cited)
      - created_at
    </messages>

    <usage_logs>
      - id (PK), user_id (FK), book_id (FK, nullable)
      - action (analyze/query_quick/query_deep)
      - input_tokens, output_tokens, cost_usd
      - engine_mode (cli/api), model_used
      - created_at
    </usage_logs>

    <settings>
      - key (PK), value (TEXT)
      - (Same key-value pattern as AutoForge's registry.py)
    </settings>
  </tables>
</database_schema>
```

---

## API Endpoints

```xml
<api_endpoints_summary>
  <auth>
    - POST /api/auth/register
    - POST /api/auth/login
    - POST /api/auth/logout
    - GET  /api/auth/me
  </auth>

  <books>
    - GET    /api/books                    (list user's books)
    - POST   /api/books/upload             (upload PDF/EPUB)
    - GET    /api/books/:id                (get book details)
    - DELETE /api/books/:id                (delete book + all data)
    - POST   /api/books/:id/analyze        (start 1M context analysis)
    - GET    /api/books/:id/analysis       (get analysis results)
    - GET    /api/books/:id/status         (analysis progress)
    - WS     /ws/books/:id/analyze         (stream analysis progress)
  </books>

  <knowledge>
    - GET    /api/books/:id/techniques     (list extracted techniques)
    - GET    /api/books/:id/techniques/:tid (technique detail)
    - GET    /api/books/:id/concepts       (list concepts)
    - GET    /api/books/:id/chapters       (chapter summaries)
    - GET    /api/books/:id/quotes         (notable quotes)
    - GET    /api/search?q=...&book_id=... (full-text search)
  </knowledge>

  <chat>
    - GET    /api/conversations            (list conversations)
    - POST   /api/conversations            (start new conversation)
    - GET    /api/conversations/:id        (get conversation + messages)
    - DELETE /api/conversations/:id        (delete conversation)
    - POST   /api/conversations/:id/message (send message, get response)
    - WS     /ws/conversations/:id         (stream chat responses)
  </chat>

  <usage>
    - GET    /api/usage                    (user's usage stats)
    - GET    /api/usage/estimate           (estimate cost for an action)
    - GET    /api/admin/usage              (admin: all users usage)
  </usage>

  <settings>
    - GET    /api/settings                 (get all settings)
    - PATCH  /api/settings                 (update settings)
  </settings>
</api_endpoints_summary>
```

---

## UI Layout

```xml
<ui_layout>
  <main_structure>
    Sidebar (left) + Main Content (right)

    Sidebar:
    - BookBrain logo
    - Library section (list of uploaded books with status icons)
    - "+ Upload Book" button
    - Conversations section (recent chats)
    - Settings gear icon

    Main Content (varies by route):
    - /library         → Book grid with covers, analysis status, technique counts
    - /books/:id       → Book detail: chapters, techniques, concepts tabs
    - /books/:id/chat  → Chat interface for querying the book
    - /chat/cross-book → Cross-book chat (query multiple books)
    - /settings        → Settings panel
    - /usage           → Usage dashboard
  </main_structure>
</ui_layout>
```

---

## Settings (Configurable Levers)

### Engine Settings (Admin/Owner Only)

| Setting | Key | Type | Default | Description |
|---------|-----|------|---------|-------------|
| Engine Mode | `engine_mode` | string | "cli" | "cli" (subscription) or "api" (API key) |
| API Key | `anthropic_api_key` | string | "" | Only needed in API mode |
| Model | `analysis_model` | string | "claude-opus-4-6" | Model for book analysis |
| Chat Model | `chat_model` | string | "claude-sonnet-4-5-20250929" | Model for chat queries (cheaper) |

### Context Budget Settings (Admin + User)

| Setting | Key | Type | Default | Range | Description |
|---------|-----|------|---------|-------|-------------|
| Admin Max Context % | `admin_max_context_pct` | int | 80 | 20-90 | Hard ceiling (users can't exceed) |
| User Context Budget % | `user_context_budget_pct` | int | 50 | 20-{admin_max} | User's preferred limit |
| Max Tokens Per Query | `max_tokens_per_query` | int | 500000 | 50000-1000000 | Token limit per single query |
| Deep Dive Enabled | `deep_dive_enabled` | bool | true | - | Allow full-book reload for deep queries |

### SaaS Settings (API Mode Only)

| Setting | Key | Type | Default | Description |
|---------|-----|------|---------|-------------|
| Free Tier Books | `free_tier_max_books` | int | 1 | Books allowed on free plan |
| Free Tier Queries/Month | `free_tier_monthly_queries` | int | 20 | Queries on free plan |
| Pro Price/Month | `pro_price_monthly` | float | 15.00 | Pro plan monthly price |
| Pro Max Books | `pro_max_books` | int | 10 | Books on pro plan |
| Cost Markup % | `cost_markup_pct` | int | 200 | Markup on API costs for billing |

---

## Analysis Agent Prompt (The Core Intelligence)

This is the prompt sent to Claude with the full book text. It runs in the 1M context window:

```
You are BookBrain's Analysis Agent. You have been given the complete text of a book.
Your job is to extract EVERY actionable technique, framework, concept, and insight
into a structured knowledge base.

## YOUR TASK

Read the entire book carefully. Then produce a structured JSON output with:

### 1. TECHNIQUES (the most important extraction)
For every actionable technique, framework, method, or exercise in the book:
- name: Clear, descriptive name
- category: One of [mindset, behavior, communication, planning, emotional, physical, financial, relationship, productivity, leadership, custom]
- chapter: Which chapter it appears in
- page_start / page_end: Approximate page range
- summary: 2-3 sentence description of what this technique does
- detailed_steps: Numbered list of EXACT steps to perform the technique
- when_to_use: Situations where this technique is most useful
- expected_outcome: What happens when you apply it correctly
- related_techniques: Names of other techniques in this book that connect to this one
- difficulty: easy / moderate / advanced
- time_to_implement: immediate / minutes / hours / days / ongoing

### 2. CHAPTER SUMMARIES
For each chapter:
- chapter_number, title
- summary: 3-5 sentence summary
- key_takeaways: Bullet points of main ideas
- techniques_introduced: List of technique names introduced in this chapter

### 3. KEY CONCEPTS
Core ideas and mental models that aren't step-by-step techniques:
- name, description, significance
- how it connects to the techniques

### 4. NOTABLE QUOTES
Memorable, impactful quotes:
- text, page_number
- context: Why this quote matters
- related_technique: If applicable

### 5. ACTION ITEMS
Specific things the author tells the reader to DO:
- action, page_reference, priority (must-do / should-do / nice-to-do)

## OUTPUT FORMAT

Return a single JSON object with keys: techniques, chapters, concepts, quotes, action_items

## IMPORTANT RULES

- Extract EVERY technique, no matter how small. If the author says "try this exercise" — that's a technique.
- Use the author's terminology. If Tony Robbins calls it "Neuro-Associative Conditioning," use that name.
- Page numbers should be approximate but useful for finding the section in the physical book.
- detailed_steps must be specific enough that someone could follow them WITHOUT reading the book.
- Don't summarize — extract. The goal is to make the book's knowledge permanently accessible.
- If a technique appears in multiple chapters with variations, create separate entries for each variation.

## BOOK TEXT

{book_text}
```

---

## Implementation Notes for AutoForge

### Building Through AutoForge

This spec is formatted for AutoForge's build pipeline:
1. Feed this as `app_spec.txt` to the AutoForge Initializer
2. Initializer creates features in SQLite (estimated: 105-155 features, Medium tier)
3. Coding agents implement features using the standard pipeline
4. The AI engine layer (CLI vs API) is the unique infrastructure piece

### Key Implementation Details

**PDF Text Extraction:**
- Use PyMuPDF (`fitz`) for high-quality text extraction
- Detect chapter boundaries from heading styles or "Chapter N" patterns
- Preserve page numbers for citation references
- Handle multi-column layouts, headers/footers, table of contents

**The Engine Factory Pattern:**
```python
# engine/base.py
class BookBrainEngine(ABC):
    @abstractmethod
    async def analyze_book(self, text: str, prompt: str) -> str: ...

    @abstractmethod
    async def query(self, context: str, question: str) -> AsyncIterator[str]: ...

# engine/cli_engine.py
class CLIEngine(BookBrainEngine):
    """Uses Claude Agent SDK → Claude Code CLI → Subscription"""
    async def analyze_book(self, text: str, prompt: str) -> str:
        client = ClaudeSDKClient(options=ClaudeAgentOptions(
            model="claude-opus-4-6",
            max_turns=50,
            betas=["context-1m-2025-08-07"],
            # No MCP servers, no tools needed — pure text analysis
            system_prompt=prompt,
        ))
        async with client:
            await client.query(text)
            response = ""
            async for msg in client.receive_response():
                if hasattr(msg, 'content'):
                    for block in msg.content:
                        if hasattr(block, 'text'):
                            response += block.text
            return response

# engine/api_engine.py
class APIEngine(BookBrainEngine):
    """Uses anthropic Python SDK → Direct API → Pay-per-token"""
    async def analyze_book(self, text: str, prompt: str) -> str:
        client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = await client.messages.create(
            model="claude-opus-4-6",
            max_tokens=16384,
            betas=["context-1m-2025-08-07"],
            system=prompt,
            messages=[{"role": "user", "content": text}],
        )
        return response.content[0].text
```

**Context Budget Enforcement:**
```python
def check_context_budget(book_tokens: int, query_tokens: int) -> bool:
    """Check if this query fits within the user's context budget."""
    admin_max = int(get_setting("admin_max_context_pct", "80"))
    user_pref = int(get_setting("user_context_budget_pct", "50"))
    effective_limit = min(admin_max, user_pref)

    max_tokens = int(1_000_000 * effective_limit / 100)
    total_needed = book_tokens + query_tokens + 2000  # 2K for system prompt

    return total_needed <= max_tokens
```

**Token Counter UI Component:**
```
┌─────────────────────────────────────────┐
│ Context Budget                          │
│ ████████████░░░░░░░░ 165K / 500K (33%) │
│                                         │
│ Book: 162,500 tokens                    │
│ Query overhead: 2,500 tokens            │
│ Remaining: 335,000 tokens               │
│                                         │
│ Budget Limit: [50%] ← user adjustable   │
│ Admin Max: 80%                          │
│ Est. Cost: ~$2.65 (API mode)            │
└─────────────────────────────────────────┘
```

---

## Estimated Feature Count

Based on the scope:
- Auth: 10 features
- Book upload/management: 15 features
- PDF extraction: 10 features
- 1M context analysis: 15 features
- Knowledge base browser: 20 features
- Chat interface: 15 features
- Multi-book library: 10 features
- Context budget controls: 10 features
- Usage metering: 10 features
- Settings: 5 features
- Infrastructure: 5 features

**Total: ~125 features (Medium tier)**

---

## Monetization Strategy

### Free Tier
- 1 book
- Basic analysis (techniques + chapter summaries only)
- 20 queries/month
- Quick query mode only (no deep dive)

### Pro ($15/month)
- 10 books
- Full analysis (techniques, concepts, quotes, action items, cross-references)
- Unlimited queries
- Deep dive mode
- Cross-book queries
- Export to PDF/Markdown

### Enterprise ($49/month)
- Unlimited books
- Team sharing (share knowledge bases with team members)
- API access (query knowledge bases programmatically)
- Priority analysis (faster queue)
- Custom analysis prompts (editable in settings, like AutoForge's advisor prompts)

---

## Standalone Components (Lead Magnets)

### Component 1: "PDF Brain Dump" (Free Tool)
Just the extraction part. Upload PDF, get structured summary. No chat, no persistence.
Shows enough value to upsell to full BookBrain.

### Component 2: "Quote Finder" (Free Tool)
Upload a book, get every notable quote with page numbers. Simple, useful, shareable.
"I found 47 actionable quotes in Awaken the Giant Within — see them all."

### Component 3: "Technique Extractor" (Free Tool)
Upload a self-help/business book, get a numbered list of every technique.
The list is free. Detailed steps require BookBrain Pro.

---

## Design Notes

Use AutoForge's design system — pick a style during the build:
- **Recommended:** Minimalism (base) + Neumorphism (accent) for a clean, professional feel
- **Color palette:** Charcoal & Cream or Deep Teal for a knowledge/learning aesthetic
- **Modifiers:** None needed unless targeting older audiences (then add Larger Type)
- Let the Design Advisor recommend based on target audience during AutoForge build

---

## Success Criteria

1. A user can upload a 500-page PDF and have the full analysis complete within 10 minutes
2. Every technique in the book is extracted with enough detail to follow without the book
3. Chat queries return accurate answers with page-number citations in under 5 seconds (quick mode)
4. Deep dive mode reloads the full book and answers comprehensive questions
5. The knowledge base persists forever — query a book you uploaded 6 months ago
6. Context budget prevents wasteful token usage without limiting functionality
7. Switching between CLI and API mode requires only changing an environment variable
8. Token costs in API mode are visible and controllable by both admin and user
