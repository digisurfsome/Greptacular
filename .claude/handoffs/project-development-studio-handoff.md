# Project Development Studio — 1M Context Brainstorming & PRD Engine

## Status: Ready for Implementation

## The Core Insight

The exact workflow that produces the best app specs is:
1. User rants out an idea in plain language
2. AI iterates, asks questions, explains what's possible
3. AI translates the conversation into technical PRDs, handoffs, and specs
4. New ideas spawn mid-conversation — AI captures them as separate project starters
5. Deep investigation happens in real-time (pros/cons, cost analysis, architecture options)

This workflow currently happens in Claude Code conversations (like this one). The problem: **Claude Code's standard context window (~200K) degrades at ~50% usage (~100K tokens), and complex idea development regularly exceeds that.** The user starts losing quality exactly when the conversation gets deep enough to be valuable.

**The fix:** AutoForge already has the 1M context window enabled via `betas=["context-1m-2025-08-07"]` in `client.py` line 641. But it's only wired into the coding/initializer agent. The three existing chat sessions (`assistant_chat_session.py`, `spec_chat_session.py`, `expand_chat_session.py`) do NOT use the 1M beta. The Project Development Studio would be a new chat session that:

1. Enables the 1M context beta (500K usable at 50% budget = 10x the current effective limit)
2. Is purpose-built for the brainstorming → PRD pipeline
3. Runs on the CLI subscription (no API cost)
4. Produces structured outputs that feed directly into AutoForge's build pipeline

**Why this is a killer differentiator:** Leon's free AutoForge has no brainstorming or planning layer. Users go directly from a vague idea to the spec creation questionnaire. The Development Studio is a premium feature that justifies the paid version — it's the difference between "build me an app from this sentence" and "let's spend 2 hours designing the perfect app together, investigate every option, then build it."

---

## What It Does (User's Perspective)

### The Tab

A new tab in the AutoForge UI: **"Development Studio"** (or "Idea Lab" / "Plan" — name TBD)

```
┌─────────────────────────────────────────────────────────────────────┐
│  AutoForge                                                          │
│  [Projects] [Development Studio] [Settings]                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  DEVELOPMENT STUDIO                                     1M Context  │
│  ─────────────────                                                  │
│                                                                     │
│  Active Sessions:                     Idea Backlog:                 │
│  ┌─────────────────────────┐          ┌──────────────────────────┐  │
│  │ BookBrain SaaS ★        │          │ 💡 Mobile fitness app    │  │
│  │ Last: 2 hours ago       │          │    (spawned from         │  │
│  │ Tokens: 234K / 500K     │          │     BookBrain session)   │  │
│  │ PRDs: 2 | Handoffs: 3   │          │                          │  │
│  │ [Continue] [Export]      │          │ 💡 SaaS boilerplate      │  │
│  ├─────────────────────────┤          │    (spawned from         │  │
│  │ Learning Ecosystem      │          │     LearnPath session)   │  │
│  │ Last: 45 min ago        │          │                          │  │
│  │ Tokens: 89K / 500K      │          │ 💡 Chrome extension idea │  │
│  │ PRDs: 1 | Handoffs: 1   │          │    (spawned from         │  │
│  │ [Continue] [Export]      │          │     general chat)        │  │
│  ├─────────────────────────┤          │                          │  │
│  │ + New Session            │          │ [Develop →] [Archive]    │  │
│  └─────────────────────────┘          └──────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Inside a Session

```
┌──────────────────────────────────────────────────────────────────────┐
│  Development Studio: BookBrain SaaS                                  │
│  Context: ████████████░░░░░░░░ 234K / 500K (47%)          [Export ▾]│
├─────────────────────────────┬────────────────────────────────────────┤
│                             │                                        │
│  CONVERSATION               │  GENERATED ARTIFACTS                   │
│                             │                                        │
│  You: "so the idea is I     │  📄 PRDs:                              │
│  want to upload any book    │  ├── bookbrain-spec.md ✓               │
│  and extract every          │  └── learnpath-ecosystem-spec.md ✓     │
│  technique..."              │                                        │
│                             │  📋 Handoffs:                          │
│  AI: "Got it. Let me break  │  ├── ebook-api-integration.md ✓        │
│  down what's possible       │  ├── dual-mode-engine.md ✓             │
│  here. There are two        │  └── context-budget-controls.md ✓      │
│  approaches to full-book    │                                        │
│  analysis..."               │  💡 Spawned Ideas:                     │
│                             │  ├── "Learning App with 18 methods"    │
│  You: "holy shit what       │  │   [Develop →] [Quick Spec →]        │
│  about using the 1M         │  ├── "Mobile app sharing Supabase"     │
│  context window?"           │  │   [Develop →] [Quick Spec →]        │
│                             │  └── "Affiliate revenue system"        │
│  AI: "Yes — and here's      │      [Develop →] [Quick Spec →]        │
│  why that changes           │                                        │
│  everything..."             │  📊 Research:                          │
│                             │  ├── API cost analysis ($3.63/book)    │
│  [Continue conversation...] │  ├── Ebook API comparison (7 vendors)  │
│                             │  └── RAG vs 1M context tradeoffs       │
│  ┌────────────────────────┐ │                                        │
│  │ Type your idea...      │ │  ──────────────────────                │
│  │                    [⏎] │ │  [Export All to Project →]             │
│  └────────────────────────┘ │  [Generate app_spec.txt →]             │
│                             │                                        │
└─────────────────────────────┴────────────────────────────────────────┘
```

### The Flow

```
1. User opens Development Studio → starts a new session
2. User starts ranting about their idea (voice-to-text or typing)
3. AI does FOUR things simultaneously:
   a. Iterates on the idea (asks clarifying questions, suggests possibilities)
   b. Translates layman's terms into technical architecture in real-time
   c. Captures spawned ideas into the Idea Backlog (sidebar)
   d. Generates artifacts (PRDs, handoffs, research docs) into the sidebar
4. User can go deep on any topic (cost analysis, architecture options, etc.)
5. When ready, user clicks "Export All to Project" → creates an AutoForge project
6. Or clicks "Generate app_spec.txt" → produces a ready-to-build spec
7. Session persists — user can come back tomorrow and continue where they left off
```

---

## Technical Architecture

### New Chat Session: `DevStudioChatSession`

Follows the exact pattern of existing chat sessions but with critical differences:

```python
# server/services/dev_studio_session.py

class DevStudioChatSession:
    """
    1M-context development planning session.

    Unlike other chat sessions:
    - Uses betas=["context-1m-2025-08-07"] for 500K+ usable context
    - Has Write tool access (generates PRDs, handoffs, specs)
    - Tracks artifacts generated during the conversation
    - Captures spawned ideas into a separate backlog
    - Persists conversation to SQLite for resume capability
    """

    def __init__(self, session_id: str, session_name: str):
        self.session_id = session_id
        self.session_name = session_name
        self.client: Optional[ClaudeSDKClient] = None
        self.artifacts: list[Artifact] = []
        self.spawned_ideas: list[SpawnedIdea] = []
        self.token_usage: TokenUsage = TokenUsage()
        self.messages: list[dict] = []
        self._client_entered: bool = False

    async def start(self) -> None:
        """Initialize the Claude SDK client with 1M context."""
        self.client = ClaudeSDKClient(options=ClaudeAgentOptions(
            model=self._get_model(),
            max_turns=100,
            betas=["context-1m-2025-08-07"],  # THE KEY DIFFERENCE
            allowed_tools=self._get_tools(),
            system_prompt=self._get_system_prompt(),
        ))
        await self.client.__aenter__()
        self._client_entered = True
```

### Comparison with Existing Sessions

| Feature | Assistant Chat | Spec Creation | Expand Project | **Dev Studio** |
|---------|---------------|---------------|----------------|----------------|
| 1M Context Beta | No | No | No | **Yes** |
| Effective context | ~100K | ~100K | ~100K | **~500K** |
| Write tool | No | Yes (spec only) | No | **Yes (PRDs, handoffs)** |
| WebSearch | Yes | No | No | **Yes** |
| WebFetch | Yes | No | No | **Yes** |
| Persistence | SQLite | In-memory | In-memory | **SQLite** |
| Resume | Yes | No (session only) | No | **Yes** |
| Artifact tracking | No | No | No | **Yes** |
| Idea spawning | No | No | No | **Yes** |
| Feature creation | Yes | Indirect (spec) | Yes | **Yes (via export)** |

### System Prompt

The system prompt is the key to making this work. It instructs Claude to simultaneously:
1. Have a natural brainstorming conversation
2. Translate into technical architecture
3. Detect and capture spawned ideas
4. Generate structured artifacts on the fly

```python
DEV_STUDIO_SYSTEM_PROMPT = """You are the AutoForge Development Studio — an elite product architect and brainstorming partner.

## YOUR ROLE

You help users develop app ideas from vague concepts into complete, buildable specifications. You operate in a 1M token context window, giving you massive space for deep, thorough development sessions.

## HOW YOU WORK

### 1. Natural Conversation
- Let the user talk freely — rants, stream of consciousness, half-formed ideas
- Ask smart questions that draw out requirements they haven't thought of
- Explain what's technically possible in plain language
- When the user asks "is that possible?" — give honest, specific answers

### 2. Real-Time Translation
- As the user describes features in layman's terms, you translate to technical architecture
- Identify the technology stack implications
- Flag complexity (this is a 2-day feature vs. this is a 2-month feature)
- Point out where ideas connect or conflict

### 3. Idea Spawning Detection
- When the user says something like "oh and another thing we could do..." or "that reminds me of..." or "what if we also..." — and it's a SEPARATE product/app concept (not a feature of the current one):
- Capture it immediately as a spawned idea
- Log it with: name, 2-3 sentence description, which conversation it came from
- Briefly acknowledge it ("Great idea — I've captured that in your Idea Backlog")
- Return to the main conversation flow

### 4. Artifact Generation
Generate structured documents as the conversation develops:

**PRD (Product Requirements Document):**
- When enough detail exists for a product section, write it to a .md file
- Format compatible with AutoForge's app_spec.txt requirements
- Include: overview, features, database schema, API endpoints, UI layout

**Handoffs:**
- When a specific implementation detail is discussed in depth, capture it as a handoff
- Include exact file paths, code snippets, and step-by-step instructions

**Research Notes:**
- When you investigate options (API providers, cost analysis, architecture tradeoffs)
- Save as structured comparison documents

**app_spec.txt:**
- When the user is ready, generate the final AutoForge-compatible spec
- Follow the XML format that AutoForge's Initializer expects

### 5. Investigation Depth
The user will ask you to investigate things at different depths:
- "Quick question" → 2-3 sentence answer
- "Can you look into that?" → Medium investigation, compare 3-4 options
- "I need to understand this fully" → Deep dive, read documentation, analyze tradeoffs

Use WebSearch and WebFetch for current information (API docs, pricing, trends).

## CONTEXT BUDGET

You have a ~500K usable token budget (50% of 1M). This is 5-10x more than a normal conversation.
- Track token usage mentally — when you estimate you're past 60%, mention it
- Prioritize: keep generating artifacts (they persist even if context fills)
- If approaching limit, generate a comprehensive summary + all remaining artifacts

## OUTPUT ARTIFACTS DIRECTORY

Write all generated artifacts to the session's output directory:
- PRDs: {output_dir}/prds/
- Handoffs: {output_dir}/handoffs/
- Research: {output_dir}/research/
- Specs: {output_dir}/specs/

## IMPORTANT RULES

- Never say "I can't do that" to a technically feasible idea. Say "here's how we'd build it and what it would cost"
- Always explain the WHY behind technical decisions, not just the WHAT
- When the user is excited about an idea, match their energy — but also ground it in reality
- If an idea has a fatal flaw, say so early — don't let them plan for 30 minutes before revealing a dealbreaker
- Every session should produce at least ONE exportable artifact (PRD, handoff, or spec)
"""
```

### Artifact Tracking

```python
@dataclass
class Artifact:
    """A document generated during a Dev Studio session."""
    id: str
    type: str  # "prd", "handoff", "research", "spec"
    name: str
    file_path: str
    created_at: datetime
    updated_at: datetime
    word_count: int

@dataclass
class SpawnedIdea:
    """An idea captured during conversation that could become its own project."""
    id: str
    name: str
    description: str  # 2-3 sentences
    spawned_from_session: str
    spawned_at: datetime
    status: str  # "backlog", "developing", "exported"
    exported_to_project: Optional[str]  # project name if exported
```

### Database Schema

```sql
-- Dev Studio sessions
CREATE TABLE dev_studio_sessions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',  -- active, paused, completed, exported
    token_usage INTEGER DEFAULT 0,
    token_budget INTEGER DEFAULT 500000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversation messages (for persistence and resume)
CREATE TABLE dev_studio_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT REFERENCES dev_studio_sessions(id),
    role TEXT NOT NULL,  -- user, assistant
    content TEXT NOT NULL,
    token_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Generated artifacts
CREATE TABLE dev_studio_artifacts (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES dev_studio_sessions(id),
    type TEXT NOT NULL,  -- prd, handoff, research, spec
    name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Spawned ideas
CREATE TABLE dev_studio_ideas (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES dev_studio_sessions(id),
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'backlog',  -- backlog, developing, exported, archived
    exported_to_project TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Storage Structure

Each Dev Studio session gets its own directory:

```
~/.autoforge/dev-studio/
├── sessions.db                     # Session metadata, messages, ideas
├── {session-id}/
│   ├── prds/
│   │   ├── bookbrain-spec.md
│   │   └── learnpath-ecosystem-spec.md
│   ├── handoffs/
│   │   ├── ebook-api-integration.md
│   │   └── dual-mode-engine.md
│   ├── research/
│   │   ├── api-cost-analysis.md
│   │   └── ebook-api-comparison.md
│   └── specs/
│       └── app_spec.txt           # Final AutoForge-compatible spec
└── {another-session-id}/
    └── ...
```

---

## API Endpoints

### New Router: `server/routers/dev_studio.py`

```
DEV STUDIO SESSIONS
  GET    /api/dev-studio/sessions                    (list all sessions)
  POST   /api/dev-studio/sessions                    (create new session)
  GET    /api/dev-studio/sessions/:id                (get session details)
  PATCH  /api/dev-studio/sessions/:id                (update name/description)
  DELETE /api/dev-studio/sessions/:id                (delete session)

CONVERSATION
  GET    /api/dev-studio/sessions/:id/messages       (get message history)
  WS     /ws/dev-studio/sessions/:id                 (WebSocket for streaming chat)

ARTIFACTS
  GET    /api/dev-studio/sessions/:id/artifacts      (list artifacts)
  GET    /api/dev-studio/artifacts/:id               (get artifact content)
  DELETE /api/dev-studio/artifacts/:id               (delete artifact)

SPAWNED IDEAS
  GET    /api/dev-studio/ideas                       (list all ideas across sessions)
  GET    /api/dev-studio/sessions/:id/ideas          (list ideas from session)
  PATCH  /api/dev-studio/ideas/:id                   (update idea status)
  POST   /api/dev-studio/ideas/:id/develop           (start new session from idea)
  POST   /api/dev-studio/ideas/:id/quick-spec        (generate quick spec from idea)

EXPORT
  POST   /api/dev-studio/sessions/:id/export         (export to AutoForge project)
  POST   /api/dev-studio/sessions/:id/generate-spec  (generate app_spec.txt from artifacts)
```

---

## UI Components

### New Components

```
src/components/dev-studio/
├── DevStudioPage.tsx              # Main page (session list + idea backlog)
├── DevStudioSession.tsx           # Active session view (chat + artifacts)
├── DevStudioChat.tsx              # Chat interface (similar to AssistantChat)
├── ArtifactPanel.tsx              # Right sidebar showing generated artifacts
├── ArtifactViewer.tsx             # Markdown viewer for artifacts
├── IdeaBacklog.tsx                # List of spawned ideas
├── IdeaCard.tsx                   # Individual idea card
├── SessionCard.tsx                # Session summary card
├── TokenBudgetBar.tsx             # Context usage indicator
├── ExportModal.tsx                # Export session to AutoForge project
└── QuickSpecModal.tsx             # Generate quick spec from spawned idea
```

### Token Budget Bar (Critical UX Element)

This is always visible at the top of the session view:

```
Context Budget                                          47% used
████████████████████░░░░░░░░░░░░░░░░░░░░  234K / 500K tokens

Conversation: 198K | Artifacts: 28K | System: 8K     [Budget Settings ⚙]
```

The bar changes color as usage increases:
- 0-60%: Green (comfortable working space)
- 60-80%: Yellow (start wrapping up or exporting)
- 80-90%: Orange (generate remaining artifacts NOW)
- 90%+: Red (emergency export mode)

At 80%, the AI automatically:
1. Generates a comprehensive session summary
2. Exports all in-progress artifacts
3. Suggests creating a new continuation session

### Export Flow

When the user clicks "Export to AutoForge Project":

```
┌─────────────────────────────────────────────┐
│  Export to AutoForge Project                │
│                                             │
│  Project Name: [BookBrain SaaS         ]    │
│  Project Dir:  [Browse...              ]    │
│                                             │
│  Include:                                   │
│  ☑ PRDs (2 documents)                       │
│  ☑ Handoffs (3 documents)                   │
│  ☑ Research notes (2 documents)             │
│  ☑ Generated app_spec.txt                   │
│                                             │
│  Actions after export:                      │
│  ☑ Create project in registry               │
│  ☑ Copy artifacts to .autoforge/ dir        │
│  ☐ Auto-run Initializer (create features)   │
│  ☐ Mark session as exported                 │
│                                             │
│  [Cancel]                      [Export →]    │
└─────────────────────────────────────────────┘
```

Export creates:
```
my-project/
├── .autoforge/
│   ├── prompts/
│   │   └── app_spec.txt            # Generated from session
│   ├── dev-studio/
│   │   ├── prds/                   # Copied from session
│   │   ├── handoffs/               # Copied from session
│   │   └── research/               # Copied from session
│   └── features.db                 # Empty (ready for Initializer)
└── CLAUDE.md                       # Generated with project context
```

---

## The "Idea Spawning" Mechanism

This is one of the most valuable features. During brainstorming, new ideas constantly emerge. Instead of losing them, the AI captures them.

### How It Works

The system prompt instructs Claude to detect idea spawning patterns:
- "oh, that could also be its own app"
- "what if we built a separate tool for..."
- "this reminds me, I also want to build..."
- "could we make that into a standalone thing?"

When detected, Claude:
1. Writes a brief entry to the spawned ideas list
2. Acknowledges it in conversation ("Captured 'Mobile Fitness Tracker' in your Idea Backlog")
3. Returns to the main conversation

### Idea Backlog UI

```
┌─────────────────────────────────────────────┐
│  💡 Idea Backlog (5 ideas)                  │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │ Mobile Fitness App                  │    │
│  │ "Track workouts with AI form        │    │
│  │  analysis using phone camera"       │    │
│  │ From: BookBrain session · 2h ago    │    │
│  │ [Develop →]  [Quick Spec]  [✕]     │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │ SaaS Boilerplate Generator          │    │
│  │ "Pre-built auth, billing, admin     │    │
│  │  panels for common SaaS patterns"   │    │
│  │ From: LearnPath session · 45m ago   │    │
│  │ [Develop →]  [Quick Spec]  [✕]     │    │
│  └─────────────────────────────────────┘    │
│                                             │
└─────────────────────────────────────────────┘
```

- **"Develop"** → Opens a new Dev Studio session with the idea pre-loaded as context
- **"Quick Spec"** → Generates a basic app_spec.txt from the 2-3 sentence description (lower quality but instant)
- **"Archive"** → Moves to archived ideas (not deleted, just hidden)

---

## Integration with Existing Features

### Connects to Spec Creation
After a Dev Studio session produces a solid plan, the user can either:
- Export directly to an AutoForge project (bypasses spec creation questionnaire entirely)
- Use the generated PRD as input to the spec creation flow (for users who want the guided questionnaire)

### Connects to AI Advisors (Roadmap v2)
The Dev Studio session can invoke the AI Setup Advisor and Design Advisor:
- "What settings should I use for this app?" → Setup Advisor logic
- "What design style fits this audience?" → Design Advisor logic
- Both advisors' editable prompts in Settings apply to Dev Studio sessions too

### Connects to Codebase Ingestion
If the user starts with "I have an existing app I want to rebuild," the Dev Studio can:
1. Use the codebase analysis pipeline from the ingestion handoff
2. Discuss findings with the user
3. Produce a rebuild plan as a PRD

---

## Implementation Plan

### Files to Create

| File | Purpose |
|------|---------|
| `server/services/dev_studio_session.py` | Core session management (follows `assistant_chat_session.py` pattern) |
| `server/services/dev_studio_database.py` | SQLite operations for sessions, messages, artifacts, ideas |
| `server/routers/dev_studio.py` | REST + WebSocket endpoints |
| `ui/src/components/dev-studio/DevStudioPage.tsx` | Main page |
| `ui/src/components/dev-studio/DevStudioSession.tsx` | Session view |
| `ui/src/components/dev-studio/DevStudioChat.tsx` | Chat component |
| `ui/src/components/dev-studio/ArtifactPanel.tsx` | Artifact sidebar |
| `ui/src/components/dev-studio/IdeaBacklog.tsx` | Idea list |
| `ui/src/components/dev-studio/TokenBudgetBar.tsx` | Context usage bar |
| `ui/src/components/dev-studio/ExportModal.tsx` | Export to project |
| `ui/src/hooks/useDevStudio.ts` | React Query hooks |

### Files to Modify

| File | Change |
|------|--------|
| `server/main.py` | Register dev_studio router |
| `ui/src/App.tsx` | Add Dev Studio route/tab |
| `ui/src/lib/types.ts` | Add DevStudio types |
| `ui/src/lib/api.ts` | Add API functions |

### Key Implementation Detail: The 1M Beta

The ONLY code change needed to enable 1M context in the chat session:

```python
# In dev_studio_session.py
self.client = ClaudeSDKClient(options=ClaudeAgentOptions(
    model=model,
    max_turns=100,
    betas=["context-1m-2025-08-07"],  # This is all it takes
    allowed_tools=[
        "Read", "Glob", "Grep",       # Code exploration
        "Write",                        # Artifact generation
        "WebSearch", "WebFetch",        # Research
        "mcp__features__ask_user",      # Interactive questions
    ],
    system_prompt=DEV_STUDIO_SYSTEM_PROMPT,
))
```

That one line — `betas=["context-1m-2025-08-07"]` — is the entire magic. It's already proven in the coding agent. We're just extending it to the brainstorming context.

---

## Estimated Feature Count (for AutoForge)

| Category | Features |
|----------|----------|
| Session Management | 8 |
| Chat Interface (1M context) | 10 |
| Artifact Generation & Tracking | 10 |
| Idea Spawning & Backlog | 8 |
| Token Budget Monitoring | 5 |
| Export to Project | 8 |
| Persistence & Resume | 6 |
| UI Components | 12 |
| Settings Integration | 3 |
| **Total** | **~70 features** |

---

## Why This Justifies Premium Pricing

Leon's free AutoForge: User writes a sentence → spec questionnaire → build
AutoForge with Dev Studio: User brainstorms for hours → full technical investigation → deep PRDs → handoffs → spawned idea backlog → export to build

The Development Studio is **the planning layer that makes everything downstream better.** Better specs → better features → better apps → happier users. It's the difference between "I threw together an app" and "I architected a product."

For users like the current user who are "thorough about everything," this is THE feature. For SaaS: it's the premium tier differentiator that free users can't access.

---

## SaaS Implications

### Free Tier
- No Dev Studio access
- Only standard spec creation questionnaire

### Pro Tier
- Dev Studio with 3 active sessions
- 500K token budget per session
- Basic artifact generation

### Enterprise Tier
- Unlimited Dev Studio sessions
- Full 1M token budget (80% = 800K)
- Advanced artifact templates
- Team sharing of sessions and ideas
- Export to multiple project formats

This feature alone could justify a $10-15/month price increase over the base tier.
