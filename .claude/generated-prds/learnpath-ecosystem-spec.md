# LearnPath — Personalized Learning Optimization Platform
# Connected Ecosystem: BookBrain → LearnPath → Life Board

## Status: Architecture & Vision Document (Pre-Build)

---

## The Ecosystem Vision

Three separate apps, connected via API, promoted as a package:

```
┌──────────────────────────────────────────────────────────────────────┐
│                     THE LEARNING ECOSYSTEM                          │
│                                                                     │
│  ┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐  │
│  │  BookBrain   │────▶│  LearnPath   │────▶│    Life Board       │  │
│  │             │     │              │     │                     │  │
│  │ Extract     │     │ Learn it     │     │ Apply it            │  │
│  │ techniques  │     │ YOUR way     │     │ to real projects    │  │
│  │ from books  │     │              │     │                     │  │
│  └──────┬──────┘     └──────┬───────┘     └──────────┬──────────┘  │
│         │                   │                        │             │
│         └───────────┬───────┴────────────────────────┘             │
│                     │                                              │
│              ┌──────▼──────┐                                       │
│              │  Supabase   │                                       │
│              │  (shared)   │                                       │
│              └─────────────┘                                       │
│                                                                     │
│  Each app: Web (React) + Mobile (React Native) + Shared Backend    │
└──────────────────────────────────────────────────────────────────────┘
```

### Why Separate Apps?

1. **Independent value** — Each app solves a real problem on its own
2. **Reduced complexity** — Each app stays focused and maintainable
3. **Mix-and-match pricing** — Users can buy just what they need
4. **API-first** — Any future app can plug into the ecosystem
5. **Lead magnets** — Each app can drive users to the others
6. **Mobile parity** — Shared Supabase means web and mobile see the same data instantly

---

## App 1: BookBrain (Already Specified)

**Full spec:** `.claude/generated-prds/bookbrain-spec.md`

**What it does:** Upload any book → extract every technique, concept, framework → query it forever.

**What it sends to LearnPath:**
- Extracted techniques (structured JSON)
- Technique metadata: name, category, difficulty, time_to_implement, detailed_steps
- Source attribution (book title, author, page references)

**API contract (BookBrain → LearnPath):**
```json
POST /api/ecosystem/techniques/export
{
  "techniques": [
    {
      "source_app": "bookbrain",
      "source_id": "tech_142",
      "name": "Neuro-Associative Conditioning",
      "category": "mindset",
      "difficulty": "moderate",
      "time_to_implement": "days",
      "summary": "Replace limiting beliefs by associating pain with old patterns and pleasure with new ones",
      "detailed_steps": ["Step 1: ...", "Step 2: ..."],
      "source_book": "Awaken the Giant Within",
      "source_author": "Tony Robbins",
      "page_reference": "pp. 128-145"
    }
  ]
}
```

---

## App 2: LearnPath (This Spec)

### Product Overview

**App Name:** LearnPath
**One-Line Description:** Discover your optimal learning style, then master any technique using the methods that work best for YOUR brain.
**Core Problem:** Everyone learns differently. You extract 47 techniques from a Tony Robbins book, but how do you actually LEARN them? Reading steps isn't learning. LearnPath runs you through 18 different learning methods, measures what sticks, and builds your personal learning profile. Then it optimizes HOW it teaches you every new technique.

### The Core Loop

```
1. IMPORT techniques (from BookBrain, manual entry, or LearnPath's own library)
         ↓
2. DISCOVERY PHASE: Try each technique through different learning methods
         ↓
3. PROFILE BUILD: Algorithm identifies your top 2-3 learning methods
         ↓
4. OPTIMIZATION: Fine-tune the percentage mix and rotation strategy
         ↓
5. MASTERY: Learn new techniques using your optimized profile
         ↓
6. EVOLUTION: Profile adapts as you learn more (some methods work better for different categories)
```

### The 18 Learning Methods

Each method is a MODULE — a complete, self-contained way to learn and practice a technique. The user tries each method during Discovery, and the system measures engagement, retention, and self-reported effectiveness.

| # | Method | Module Type | How It Works |
|---|--------|-------------|-------------|
| 1 | **Visual Mapping** | Interactive | Create mind maps connecting technique steps to existing knowledge |
| 2 | **Spaced Repetition** | Automated | Flashcard-style review with intelligent spacing (like Anki) |
| 3 | **Teach-Back** | AI Conversation | Explain the technique to an AI student who asks challenging questions |
| 4 | **Scenario Simulation** | AI Roleplay | AI presents real-life scenarios where you apply the technique |
| 5 | **Micro-Practice** | Daily Tasks | Break technique into tiny daily actions (5-min exercises) |
| 6 | **Journaling/Reflection** | Writing | Guided journaling prompts that connect technique to personal experience |
| 7 | **Socratic Dialogue** | AI Conversation | AI asks probing questions until you derive the technique's principles yourself |
| 8 | **Chunking** | Structured | Break technique into progressive chunks, master each before moving on |
| 9 | **Analogical Learning** | AI Generated | AI generates analogies from domains you already understand |
| 10 | **Implementation Intention** | Planning | "When X happens, I will do Y" — create specific trigger-action plans |
| 11 | **Elaborative Interrogation** | Quiz | "Why does this work?" — deep questioning that forces understanding |
| 12 | **Interleaving** | Mixed Practice | Mix different techniques in a single session to strengthen discrimination |
| 13 | **Dual Coding** | Visual + Verbal | Combine visual diagrams with verbal explanations simultaneously |
| 14 | **Generation Effect** | Active Recall | Try to recall technique steps BEFORE reviewing them |
| 15 | **Concrete Examples** | AI Generated | AI generates real-world examples specific to YOUR life context |
| 16 | **Self-Testing** | Quizzes | Timed quizzes on technique details, scoring tracks progress |
| 17 | **Narrative Learning** | Storytelling | AI wraps the technique in a story — characters applying it in their lives |
| 18 | **Physical Anchoring** | Kinesthetic | Audio-guided exercises that associate physical movements with technique steps |

### Learning Profile System

#### Discovery Phase

When a user first starts, they go through a Discovery Phase:

1. Pick any technique (imported from BookBrain or from the built-in library)
2. System presents the technique through 4-6 different learning methods (randomized selection)
3. After each method, user rates:
   - Engagement (1-5): "How much did this hold my attention?"
   - Clarity (1-5): "How well do I understand the technique now?"
   - Retention (1-5): "Could I explain this to someone tomorrow?"
4. System also measures: time spent, completion rate, quiz scores (where applicable)
5. Repeat for 3-5 techniques (minimum data for initial profile)

#### Profile Algorithm

```python
class LearningProfile:
    """User's personalized learning fingerprint"""

    # Core profile: effectiveness scores per method (0-100)
    method_scores: dict[str, float]  # e.g., {"teach_back": 87, "spaced_repetition": 72, ...}

    # Top methods: the 2-3 methods that work best
    primary_methods: list[str]       # e.g., ["teach_back", "scenario_simulation"]

    # Category overrides: some methods work better for certain categories
    category_preferences: dict[str, list[str]]
    # e.g., {"mindset": ["journaling", "socratic_dialogue"],
    #        "productivity": ["micro_practice", "implementation_intention"]}

    # Optimization percentages
    method_mix: dict[str, int]       # e.g., {"teach_back": 45, "scenario_sim": 35, "spaced_rep": 20}

    # Rotation strategy
    rotation_type: str               # "fixed" | "adaptive" | "cyclic"
    rotation_interval: int           # sessions before rotating methods

    # Evolution tracking
    profile_confidence: float        # 0-1, increases with more data points
    last_updated: datetime
    total_sessions: int
    total_techniques_learned: int

def calculate_profile(user_id: str) -> LearningProfile:
    """
    Score each method based on:
    - User ratings (engagement, clarity, retention) — weighted 40%
    - Objective measures (quiz scores, completion rate) — weighted 35%
    - Long-term retention (follow-up quiz scores after 7/30 days) — weighted 25%

    Category preferences detected when a method scores significantly
    higher for one category vs overall average.
    """
    pass

def get_optimal_session(user_id: str, technique_id: str) -> LearningSession:
    """
    Build an optimal learning session for this user + technique:
    1. Check technique category
    2. Check if category has preference overrides
    3. Apply method_mix percentages to determine session structure
    4. Apply rotation strategy
    5. Return ordered list of method modules with time allocations
    """
    pass
```

#### Optimization Phase

After Discovery, users can fine-tune their profile:

1. **Method Mix Sliders** — Adjust the percentage split between top methods
   ```
   Teach-Back:          ████████████████░░░░ 45%
   Scenario Simulation: ████████████░░░░░░░░ 35%
   Spaced Repetition:   ████████░░░░░░░░░░░░ 20%
                                              [Auto-Optimize]
   ```

2. **Rotation Controls** — How often to mix in other methods
   - Fixed: Same methods every session
   - Adaptive: System occasionally introduces new methods to re-test
   - Cyclic: Rotate through top 5 methods on a schedule

3. **Category Overrides** — Set different method preferences per technique category
   - "For mindset techniques, use more Journaling"
   - "For productivity techniques, use more Micro-Practice"

4. **Auto-Optimize Button** — Let the algorithm adjust based on accumulated data

### Mastery Tracking

Each technique has a mastery score (0-100):

```
┌────────────────────────────────────────────────────────────┐
│ Neuro-Associative Conditioning                    ★★★★☆   │
│ Source: Awaken the Giant Within, Ch. 6                     │
│                                                            │
│ Mastery: ████████████████████░░░░░ 78%                     │
│                                                            │
│ Understanding:  ████████████████████████ 92%               │
│ Recall:         █████████████████░░░░░░░ 71%               │
│ Application:    ██████████████░░░░░░░░░░ 62%               │
│                                                            │
│ Last practiced: 3 days ago                                 │
│ Sessions: 12  |  Next review: Tomorrow                     │
│ Methods used: Teach-Back (6), Scenario Sim (4), Quiz (2)   │
│                                                            │
│ [Practice Now]  [View History]  [Apply to Life Board →]    │
└────────────────────────────────────────────────────────────┘
```

Mastery is a composite of:
- **Understanding** (can you explain it?): Measured by Teach-Back and Socratic Dialogue scores
- **Recall** (can you remember the steps?): Measured by Self-Testing and Generation Effect scores
- **Application** (can you use it in context?): Measured by Scenario Simulation and Implementation Intention completion

### Technology Stack

```xml
<technology_stack>
  <frontend>
    <web>React 19 + TypeScript + Tailwind CSS v4 + Radix UI</web>
    <mobile>React Native + Expo (shared business logic)</mobile>
  </frontend>
  <backend>
    <database>Supabase (PostgreSQL + Auth + Realtime + Edge Functions)</database>
    <ai>Claude API via Anthropic SDK (for AI-powered learning methods)</ai>
    <notifications>Supabase Realtime + push notifications (mobile)</notifications>
    <scheduling>Supabase Edge Functions (spaced repetition scheduler)</scheduling>
  </backend>
  <shared>
    <api>REST + Supabase Realtime subscriptions</api>
    <auth>Supabase Auth (shared across web and mobile)</auth>
    <storage>Supabase Storage (for visual maps, journal exports)</storage>
  </shared>
</technology_stack>
```

### Database Schema (Supabase/PostgreSQL)

```sql
-- Users (managed by Supabase Auth, extended with profile)
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    display_name TEXT,
    plan TEXT DEFAULT 'free', -- free/pro/enterprise
    discovery_completed BOOLEAN DEFAULT FALSE,
    profile_confidence FLOAT DEFAULT 0,
    total_sessions INT DEFAULT 0,
    total_techniques_mastered INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Learning methods catalog (the 18 methods)
CREATE TABLE learning_methods (
    id TEXT PRIMARY KEY, -- e.g., 'teach_back', 'spaced_repetition'
    name TEXT NOT NULL,
    description TEXT,
    module_type TEXT, -- interactive/automated/ai_conversation/etc.
    requires_ai BOOLEAN DEFAULT FALSE,
    estimated_minutes INT,
    icon TEXT -- emoji or icon name
);

-- User's learning profile
CREATE TABLE learning_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id),
    method_scores JSONB DEFAULT '{}', -- {method_id: score}
    primary_methods TEXT[] DEFAULT '{}',
    method_mix JSONB DEFAULT '{}', -- {method_id: percentage}
    category_preferences JSONB DEFAULT '{}',
    rotation_type TEXT DEFAULT 'adaptive',
    rotation_interval INT DEFAULT 5,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Techniques (imported from BookBrain or manually created)
CREATE TABLE techniques (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id),
    source_app TEXT, -- 'bookbrain', 'manual', 'learnpath_library'
    source_id TEXT, -- ID in source app
    name TEXT NOT NULL,
    category TEXT, -- mindset/behavior/communication/planning/etc.
    difficulty TEXT, -- easy/moderate/advanced
    summary TEXT,
    detailed_steps JSONB,
    source_book TEXT,
    source_author TEXT,
    page_reference TEXT,
    mastery_score FLOAT DEFAULT 0,
    understanding_score FLOAT DEFAULT 0,
    recall_score FLOAT DEFAULT 0,
    application_score FLOAT DEFAULT 0,
    sessions_completed INT DEFAULT 0,
    last_practiced TIMESTAMPTZ,
    next_review TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Learning sessions
CREATE TABLE learning_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id),
    technique_id UUID REFERENCES techniques(id),
    method_id TEXT REFERENCES learning_methods(id),

    -- Session data
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds INT,
    completion_rate FLOAT, -- 0-1

    -- User ratings
    engagement_rating INT, -- 1-5
    clarity_rating INT, -- 1-5
    retention_rating INT, -- 1-5

    -- Objective measures
    quiz_score FLOAT, -- 0-100 (if method has quiz)
    ai_assessment_score FLOAT, -- 0-100 (AI-judged quality of teach-back, etc.)

    -- Context
    is_discovery BOOLEAN DEFAULT FALSE,
    session_notes TEXT
);

-- Spaced repetition schedule
CREATE TABLE review_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id),
    technique_id UUID REFERENCES techniques(id),
    scheduled_date DATE NOT NULL,
    interval_days INT, -- current interval
    ease_factor FLOAT DEFAULT 2.5, -- SM-2 algorithm
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMPTZ
);

-- Discovery phase tracking
CREATE TABLE discovery_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id),
    technique_index INT, -- which discovery technique (1-5)
    method_index INT, -- which method attempt for this technique
    technique_id UUID REFERENCES techniques(id),
    method_id TEXT REFERENCES learning_methods(id),
    completed BOOLEAN DEFAULT FALSE,
    session_id UUID REFERENCES learning_sessions(id)
);

-- Ecosystem connections
CREATE TABLE ecosystem_syncs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id),
    source_app TEXT NOT NULL, -- 'bookbrain'
    target_app TEXT NOT NULL, -- 'learnpath'
    sync_type TEXT, -- 'technique_import', 'mastery_export'
    payload JSONB,
    synced_at TIMESTAMPTZ DEFAULT NOW()
);
```

### API Endpoints

```
AUTH (via Supabase Auth)
  POST /auth/signup
  POST /auth/login
  POST /auth/logout
  GET  /auth/session

TECHNIQUES
  GET    /api/techniques                    (list user's techniques)
  POST   /api/techniques                    (create manually)
  POST   /api/techniques/import             (import from BookBrain)
  GET    /api/techniques/:id                (detail with mastery data)
  DELETE /api/techniques/:id
  GET    /api/techniques/:id/history        (all sessions for this technique)

LEARNING PROFILE
  GET    /api/profile                       (get user's learning profile)
  PATCH  /api/profile/mix                   (update method percentages)
  PATCH  /api/profile/rotation              (update rotation strategy)
  PATCH  /api/profile/category-prefs        (update category overrides)
  POST   /api/profile/auto-optimize         (trigger algorithm optimization)

DISCOVERY
  GET    /api/discovery/status              (discovery phase progress)
  POST   /api/discovery/start               (begin discovery phase)
  GET    /api/discovery/next                (get next method to try)
  POST   /api/discovery/complete-step       (submit ratings for a step)
  POST   /api/discovery/finalize            (complete discovery, build profile)

LEARNING SESSIONS
  POST   /api/sessions/start                (start a learning session)
  PATCH  /api/sessions/:id/complete         (complete with ratings + scores)
  GET    /api/sessions/history              (session history with filters)
  GET    /api/sessions/stats                (aggregate learning statistics)

REVIEW SCHEDULE
  GET    /api/reviews/today                 (techniques due for review today)
  GET    /api/reviews/upcoming              (upcoming 7-day schedule)
  POST   /api/reviews/:id/complete          (mark review completed)
  POST   /api/reviews/:id/skip              (skip with reschedule)

ECOSYSTEM
  POST   /api/ecosystem/sync               (sync data with connected apps)
  GET    /api/ecosystem/connections          (list connected apps)
  POST   /api/ecosystem/connect             (establish connection to another app)

LIBRARY (Built-in Technique Library)
  GET    /api/library/techniques            (browse built-in techniques)
  GET    /api/library/categories            (list categories)
  POST   /api/library/techniques/:id/add    (add library technique to user's list)
```

### UI Layout

```
┌───────────────────────────────────────────────────────────────────┐
│  LearnPath                          [Profile] [Settings] [🔔]    │
├───────────┬───────────────────────────────────────────────────────┤
│           │                                                       │
│ Dashboard │  MAIN CONTENT AREA                                    │
│           │                                                       │
│ My        │  Dashboard View:                                      │
│ Techniques│  ┌─────────────┬─────────────┬─────────────┐          │
│           │  │ Due Today   │ In Progress │ Mastered    │          │
│ Discovery │  │     3       │     8       │    12       │          │
│           │  └─────────────┴─────────────┴─────────────┘          │
│ Learning  │                                                       │
│ Profile   │  Today's Learning:                                    │
│           │  ┌──────────────────────────────────────────┐         │
│ Review    │  │ 🎯 NAC Technique — Review Due            │         │
│ Schedule  │  │    Teach-Back (15 min) → Start           │         │
│           │  ├──────────────────────────────────────────┤         │
│ Stats     │  │ 📚 Power of Questions — Continue         │         │
│           │  │    Scenario Simulation (10 min) → Start  │         │
│ Library   │  ├──────────────────────────────────────────┤         │
│           │  │ ✨ New: Goal Setting — From BookBrain     │         │
│ Connected │  │    Start Discovery → Begin               │         │
│ Apps      │  └──────────────────────────────────────────┘         │
│           │                                                       │
│ Settings  │  Your Learning Profile:                               │
│           │  Teach-Back: ████████████████ 45%                     │
│           │  Scenarios:  ████████████ 35%                         │
│           │  Spaced Rep: ████████ 20%                             │
│           │  Confidence: 82% (47 sessions)                        │
│           │                                                       │
└───────────┴───────────────────────────────────────────────────────┘
```

### AI-Powered Learning Methods (Implementation Notes)

Several of the 18 methods require AI interaction. These use the same dual-mode engine pattern as BookBrain:

**Methods requiring Claude API:**
- Teach-Back (method 3): AI plays a curious student
- Scenario Simulation (method 4): AI generates realistic scenarios
- Socratic Dialogue (method 7): AI asks probing questions
- Analogical Learning (method 9): AI generates domain-relevant analogies
- Concrete Examples (method 15): AI generates personalized examples
- Narrative Learning (method 17): AI wraps techniques in stories

**Prompt structure for AI methods:**
```
System: You are a {method_type} learning facilitator for LearnPath.

The user is learning this technique:
Name: {technique.name}
Category: {technique.category}
Steps: {technique.detailed_steps}
Source: {technique.source_book} by {technique.source_author}

User's learning profile:
- Primary methods: {profile.primary_methods}
- This method effectiveness for user: {method_score}/100
- Category preference: {category_preference}
- Sessions with this technique: {technique.sessions_completed}
- Current mastery: {technique.mastery_score}%

{method_specific_instructions}
```

**AI cost estimate per session:** ~$0.02-0.05 on Sonnet (short conversational turns, no 1M context needed)

### Estimated Feature Count (for AutoForge)

| Category | Features |
|----------|----------|
| Auth + User Profile | 8 |
| Technique Management | 12 |
| Discovery Phase | 15 |
| Learning Profile Algorithm | 12 |
| 18 Learning Method Modules | 54 (3 per method avg) |
| Mastery Tracking | 10 |
| Review Schedule (Spaced Repetition) | 8 |
| AI Method Integration | 10 |
| Stats & Analytics Dashboard | 8 |
| Built-in Technique Library | 6 |
| Ecosystem API (BookBrain sync) | 8 |
| Settings & Preferences | 5 |
| Infrastructure | 4 |
| **Total** | **~160 features (Medium-Large tier)** |

---

## App 3: Life Board (Future — Conceptual)

**One-Line Description:** Apply mastered techniques to real life projects on an interactive board.

### Concept

Life Board is where learned techniques become actions. Users define life projects (career change, fitness goal, relationship improvement, business launch), and the board helps them:

1. **Map techniques to projects** — "Which techniques from Tony Robbins apply to my career change?"
2. **Create action plans** — Break projects into steps using the techniques
3. **Track execution** — Daily/weekly check-ins on technique application
4. **Measure results** — Did applying this technique move the needle?
5. **Feedback loop** — Results feed back into LearnPath mastery scores

### Board Structure

```
┌──────────────────────────────────────────────────────────────┐
│  LIFE BOARD — My Active Projects                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Career Change │  │ Fitness 2026 │  │ Side Business│       │
│  │              │  │              │  │              │       │
│  │ Techniques:  │  │ Techniques:  │  │ Techniques:  │       │
│  │ • NAC (87%)  │  │ • Micro-hab  │  │ • Goal Set   │       │
│  │ • Goal Set   │  │   (92%)      │  │   (78%)      │       │
│  │   (78%)      │  │ • Pain/Pleas │  │ • RPM Plan   │       │
│  │ • Questions  │  │   (71%)      │  │   (65%)      │       │
│  │   (65%)      │  │              │  │ • Questions  │       │
│  │              │  │              │  │   (65%)      │       │
│  │ Next action: │  │ Next action: │  │              │       │
│  │ Do NAC on    │  │ 5-min micro  │  │ Next action: │       │
│  │ limiting     │  │ exercise     │  │ Define RPM   │       │
│  │ beliefs      │  │ (Tue/Thu)    │  │ outcome map  │       │
│  │              │  │              │  │              │       │
│  │ Progress: 34%│  │ Progress: 62%│  │ Progress: 15%│       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  [+ New Project]                                             │
└──────────────────────────────────────────────────────────────┘
```

Life Board is the longest-term vision. It can be specified in detail when BookBrain and LearnPath are underway.

---

## Shared Infrastructure: Supabase

### Why Supabase (not SQLite)

BookBrain's initial spec uses SQLite for simplicity (personal use mode). For the ecosystem with mobile apps, we need:

- **Real-time sync** between web and mobile (Supabase Realtime)
- **Authentication** shared across all three apps (Supabase Auth)
- **Row-level security** for multi-tenant SaaS (Supabase RLS)
- **Edge Functions** for server-side logic (spaced repetition scheduler, ecosystem sync)
- **Storage** for user-generated content (visual maps, journal exports)

### Migration Path

```
Phase 1: BookBrain with SQLite (personal use, quick build)
Phase 2: BookBrain SaaS with Supabase (multi-user, shared auth)
Phase 3: LearnPath with Supabase (shares auth + user profiles)
Phase 4: Life Board with Supabase (shares everything)
Phase 5: Mobile apps for each (shared Supabase = instant data sync)
```

### Supabase Project Structure

One Supabase project, three schemas:

```sql
-- Shared schema (auth, profiles, ecosystem)
CREATE SCHEMA shared;

-- App-specific schemas
CREATE SCHEMA bookbrain;
CREATE SCHEMA learnpath;
CREATE SCHEMA lifeboard;  -- future

-- Cross-app tables live in 'shared'
-- App-specific tables live in their own schema
-- RLS policies ensure users only see their own data
```

### Ecosystem Sync API

Apps communicate through a shared `ecosystem_events` table:

```sql
CREATE TABLE shared.ecosystem_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    source_app TEXT NOT NULL,
    target_app TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Example events:
-- BookBrain → LearnPath: technique_extracted
-- LearnPath → Life Board: technique_mastered
-- Life Board → LearnPath: technique_applied (feeds back into mastery score)
```

Each app listens for events targeting it via Supabase Realtime subscriptions:

```typescript
// In LearnPath
supabase
  .channel('ecosystem')
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'shared',
    table: 'ecosystem_events',
    filter: 'target_app=eq.learnpath'
  }, (payload) => {
    handleEcosystemEvent(payload.new)
  })
  .subscribe()
```

---

## Mobile Apps (React Native + Expo)

### Shared Architecture

All three mobile apps share:
- **Supabase client** — same database, same auth
- **UI component library** — shared design tokens, buttons, cards
- **Business logic** — shared TypeScript modules for scoring, scheduling, profiles

### Mobile-Specific Features

**BookBrain Mobile:**
- Camera scan: photograph book pages → OCR → extract text
- Offline reading of extracted knowledge base
- Push notifications: "New analysis complete"

**LearnPath Mobile:**
- Push notifications for spaced repetition reviews ("Time to review NAC technique")
- Audio mode for Physical Anchoring method (method 18)
- Quick 5-minute micro-practice sessions designed for mobile
- Offline learning sessions (cached technique data)

**Life Board Mobile:**
- Daily check-in notifications
- Quick action logging (did you apply the technique today?)
- Photo evidence (take a photo of your progress)
- Widget for home screen showing today's actions

### React Native Structure

```
apps/
  bookbrain-mobile/    # Expo app
  learnpath-mobile/    # Expo app
  lifeboard-mobile/    # Expo app (future)
packages/
  shared-ui/           # Shared components (buttons, cards, design tokens)
  shared-logic/        # Shared business logic (scoring, profiles)
  shared-supabase/     # Supabase client config, types, queries
  shared-types/        # TypeScript types shared across all apps
```

---

## Monetization Strategy (Ecosystem)

### Individual App Pricing

| Plan | BookBrain | LearnPath | Life Board |
|------|-----------|-----------|------------|
| Free | 1 book, 20 queries/mo | 3 techniques, 2 methods | 1 project |
| Pro | $15/mo — 10 books, unlimited | $12/mo — unlimited, all 18 methods | $8/mo — unlimited |
| Enterprise | $49/mo — teams | $39/mo — teams + custom methods | $29/mo — teams |

### Bundle Pricing

| Bundle | Price | Savings |
|--------|-------|---------|
| BookBrain + LearnPath Pro | $22/mo | Save $5/mo |
| Full Ecosystem Pro | $28/mo | Save $7/mo |
| Full Ecosystem Enterprise | $89/mo | Save $28/mo |

### Ebook Affiliate Revenue (BookBrain)

When users search for books in BookBrain, purchase links earn affiliate commission:
- **eBooks.com:** 10-15% commission, 45-day cookie, API for search + metadata
- **Amazon Associates:** 1-4.5% commission, 24-hour cookie, Product Advertising API
- **Bookshop.org:** 10% commission, supports independent bookstores
- **Apple Books:** 7% commission via Apple Services Performance Partners

See updated BookBrain spec for full ebook integration details.

---

## Build Order (AutoForge Pipeline)

```
Phase 1: BookBrain Web (SQLite, personal use)     ← Already specified
Phase 2: BookBrain SaaS (migrate to Supabase)     ← Update spec
Phase 3: LearnPath Web                             ← This spec
Phase 4: Ecosystem API (BookBrain ↔ LearnPath)     ← Integration
Phase 5: BookBrain Mobile                          ← React Native
Phase 6: LearnPath Mobile                          ← React Native
Phase 7: Life Board Web                            ← Future spec
Phase 8: Life Board Mobile                         ← Future
```

Each phase is a separate AutoForge project. They share a Supabase backend from Phase 2 onward.

---

## Design Notes

All three apps should feel like a cohesive ecosystem:
- **Shared color palette:** Deep Teal or similar knowledge/growth aesthetic
- **Shared design tokens:** Same typography, spacing, border radius
- **App accent colors:** Each app has a subtle accent to distinguish it
  - BookBrain: Warm amber (books/knowledge)
  - LearnPath: Vibrant green (growth/learning)
  - Life Board: Deep blue (depth/application)
- **Style recommendation:** Minimalism (base) + Glassmorphism (accent) for modern, clean feel
- Use AutoForge Design Advisor for final decisions during each build

---

## Success Criteria

1. A user can extract techniques from BookBrain and import them into LearnPath in <30 seconds
2. Discovery Phase identifies top learning methods within 5 technique completions
3. Mastery scores correlate with actual retention (measured by follow-up quizzes)
4. Users show measurable improvement in technique recall after 4 weeks of LearnPath use
5. Spaced repetition notifications bring users back daily
6. Mobile and web show identical data with <2 second sync delay
7. Bundle pricing drives 40%+ of users to multi-app subscriptions
8. The ecosystem sync API allows new apps to plug in without modifying existing apps
