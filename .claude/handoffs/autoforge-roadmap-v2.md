# AutoForge Enhancement Roadmap v2
# Configurable Levers + Care Levels + AI Advisors (Setup + Design)

## Status: Ready for Implementation (4 Phases)

## Overview

This roadmap covers 4 major enhancements to AutoForge, designed to be implemented in order since each phase builds on the previous. The core philosophy: **give users maximum control through adjustable levers, but provide AI guidance so they don't need to understand every lever to get great results.**

**Critical Discovery:** The 1M context window is ALREADY enabled via `betas=["context-1m-2025-08-07"]` in `client.py` line 641. This runs through the Claude Code CLI subscription — no API key needed. The Initializer already benefits from this. This changes the cost equation entirely: complex apps with 400+ features can be decomposed in a single Initializer session without worrying about context limits, all within the $200/month plan.

---

## Phase 1: Configurable Agent Budget Levers

**Status:** Handoff complete at `.claude/handoffs/feature-sizing-overhaul-handoff.md`
**Estimated scope:** 10 files, ~300 lines of changes

This is fully documented in the existing handoff. Summary: Replace 6 hardcoded constants across 4 Python files with 9 configurable levers stored in SQLite, accessible from the Settings UI. Default budget drops from 45% to 30% for better quality.

**No changes needed to this handoff.** Implement it as written.

---

## Phase 2: Spec Creation Care Levels (1-5)

**Estimated scope:** 1 file modified (`create-spec.md`), 1 new settings field, minor UI change

### The Problem

Currently the spec creation flow offers two modes: Quick Mode and Detailed Mode. This is too binary. Many users can't articulate what they want (Level 1-2), while power users want to review every individual feature before generation (Level 5).

### The 5 Levels

| Level | Name | Phases Used | User Effort | Time |
|-------|------|-------------|-------------|------|
| 1 | **Autopilot** | 1 (identity only) → generate | 2-3 minutes | ~5 min total |
| 2 | **Light Touch** | 1 + brief 4 (main flow only) → generate | 5-10 minutes | ~10 min total |
| 3 | **Balanced** | 1 + 2 + 3 + 4 + 5 + 6 + 7 (current Quick Mode) | 15-25 minutes | ~30 min total |
| 4 | **Detailed** | All phases, user weighs in on tech decisions (current Detailed Mode) | 25-40 minutes | ~45 min total |
| 5 | **Architect** | All phases + user reviews the actual feature list item-by-item before generation, can add/remove/reword features | 40-60+ minutes | ~60+ min total |

### Level Descriptions for the UI

**Level 1 — Autopilot:**
> "Give me 1-2 sentences about your app and I'll handle everything. You'll get a working app but features and UX are entirely my choice."
>
> **WARNING:** At this level, the AI makes ALL creative and technical decisions. Features will be generic and may not match your vision. You'll get a functional app, but it might not be what you had in mind. Use this for quick prototypes or when you genuinely don't care about specifics.

**Level 2 — Light Touch:**
> "Answer a few basic questions about your app's main purpose and I'll fill in the details."
>
> **NOTE:** Core functionality will match your description, but edge cases, roles, detailed UX flows, and polish decisions are the AI's best guess. Good for early exploration.

**Level 3 — Balanced (Recommended):**
> "Walk through your app's features in conversation. I'll derive all technical details from what you describe. Best balance of quality and speed."

**Level 4 — Detailed:**
> "You'll be involved in technology choices, database design, and architecture decisions alongside feature planning."

**Level 5 — Architect:**
> "Full detailed mode PLUS you'll review every individual feature and its test steps before I generate. Maximum control — you approve the exact feature list the agents will build."

### Implementation: Modify `create-spec.md`

**File:** `.claude/commands/create-spec.md`

**Change Phase 2** (around line 96) from the current Quick/Detailed binary to:

```markdown
## Phase 2: Involvement Level

Ask the user how involved they want to be:

> "How involved do you want to be in planning your app?
>
> 1. **Autopilot** — Give me 1-2 sentences, I'll handle everything
> 2. **Light Touch** — Answer a few basics, I'll fill in the rest
> 3. **Balanced (Recommended)** — Walk through features together, I derive the tech
> 4. **Detailed** — You weigh in on technology and architecture decisions
> 5. **Architect** — Full control. You review every feature before I generate
>
> Levels 1-2 are fast but the AI makes most decisions.
> Levels 4-5 take longer but give you maximum control."

**Branching Logic:**

**Level 1 (Autopilot):**
- Complete Phase 1 (identity — all 4 fields are still mandatory)
- Skip Phases 2b-6 entirely
- Agent derives EVERYTHING: tech stack, features, database, UI, success criteria
- Generate files immediately after identity
- Show this warning before generating: "I've designed your entire app based on your description. The feature count is [X]. Since you chose Autopilot mode, I made all feature, UX, and technical decisions. If you want to review or change anything, say so now — otherwise I'll generate the spec."

**Level 2 (Light Touch):**
- Complete Phase 1 (identity)
- Ask Phase 3b (database: yes/no/not sure) — mandatory
- Ask ONLY: "Walk me through the main thing users do in your app. What's the primary workflow?"
- Ask: "Any other key features you definitely want?" (one question, not the full 12-area drill-down)
- Agent derives everything else
- Present brief summary + feature count → generate

**Level 3 (Balanced):**
- This IS the current Quick Mode. No changes needed.
- All 7 phases, agent derives tech details.

**Level 4 (Detailed):**
- This IS the current Detailed Mode. No changes needed.
- All 7 phases, user involved in tech decisions.

**Level 5 (Architect):**
- Everything in Level 4, PLUS:
- After Phase 4L (feature count), add a NEW Phase 4M:

**Phase 4M: Feature Review (Level 5 Only)**

> "Here are the individual features I've planned, organized by category. Review each one — you can:
> - **Accept** a feature as-is
> - **Modify** its description or test steps
> - **Remove** a feature you don't want
> - **Add** features I missed
>
> I'll present them in batches of 10. For each batch, tell me your changes."

Present features in batches of 10 with:
- Feature name
- Category (functional/style)
- Description (technical)
- User action (plain English)
- Number of test steps
- Dependencies (which features it depends on)

After all batches reviewed, recalculate feature_count and proceed to Phase 5.
```

### Settings Integration

**Add to `server/schemas.py`** (SettingsResponse + SettingsUpdate):

```python
# Spec Creation Settings
default_care_level: int = 3  # 1-5, default Balanced
```

**Add to Settings UI** (`SettingsModal.tsx`):
A button group in the "Build Settings" section:

```
Spec Creation Detail Level: [1] [2] [3] [4] [5]
                             ↑             ↑
                          Autopilot     Architect
```

This sets the DEFAULT for new projects. The spec creation agent still asks the user during the flow, but pre-selects this default.

### Disclaimers

Add to the spec creation flow for Levels 1-2:

```markdown
## DISCLAIMERS FOR LOW INVOLVEMENT LEVELS

When the user selects Level 1 or 2, display this warning BEFORE proceeding:

> **Important:** At this involvement level:
> - The AI will decide your app's features, UX patterns, and technical architecture
> - You may get a fully working app that doesn't match your mental picture
> - Features will be reasonable but generic — the AI can't read your mind
> - You can always re-run spec creation at a higher level if the result doesn't fit
>
> **The rule:** The less you put in, the more generic you get out.
>
> Want to continue at Level [N], or would you like to bump up?
```

---

## Phase 3: AI Setup Advisor Agent

**Estimated scope:** 2-3 new files, settings additions, new UI component

### The Problem

Phase 1 gives users 9+ levers to configure. Most users won't know what values to pick. The Setup Advisor analyzes the project spec and recommends optimal settings.

### Architecture

The Setup Advisor is a **chat agent** that runs during project setup (after spec creation, before the Initializer). It can also be opened from the Settings panel at any time.

**Key design decision from the user:** The advisor's system prompt is NOT hardcoded. It lives in editable text boxes in the Settings UI so it can be updated as models change, best practices evolve, or the user discovers better prompting strategies.

### Data the Advisor Has Access To

From the project's `app_spec.txt`:
- Feature count
- Complexity tier (Simple/Medium/Advanced)
- Technology stack
- Number of database tables
- Number of API endpoints
- Number of user roles
- Whether it has auth

From the settings database:
- Current lever values
- Historical session metrics (future: `session_metrics` table)

### Advisor Prompts (Editable in Settings)

**Add 2 new text fields to Settings UI:**

1. **`advisor_system_prompt`** — The system prompt for the Setup Advisor
2. **`advisor_knowledge_context`** — Additional context/knowledge to inject (updated as practices evolve)

**Default `advisor_system_prompt`:**

```
You are AutoForge's Setup Advisor. You help users configure their project's
build settings for optimal quality and efficiency.

You have access to the project's specification (feature count, complexity,
tech stack) and the current build settings (context budget, batch size,
parallel agents, etc.).

Your job:
1. Analyze the project spec to understand complexity
2. Recommend optimal values for each configurable lever
3. Explain WHY each recommendation makes sense for THIS specific project
4. Warn about settings that could cause problems

Key principles:
- Lower context budget = higher quality per session but more sessions
- Higher batch size = fewer sessions but risk of exceeding budget
- Parallel agents only help if the dependency graph is wide enough
- Complex features (many steps, external integrations) need more budget per feature
- Simple CRUD features can be batched aggressively

When recommending, always explain the tradeoff. Never just say "use X" —
say "use X because your project has Y features averaging Z steps, which means..."

Format recommendations as a clear table showing:
- Lever name
- Recommended value
- Current value (if different)
- Reason for recommendation
```

**Default `advisor_knowledge_context`:**

```
Context budget benchmarks from real builds:
- 20% budget: Zero errors per session, ~45 turns usable, 1-2 features/session
- 30% budget: Very rare errors, ~70 turns usable, 2-3 features/session
- 40% budget: Occasional errors in later turns, ~100 turns usable, 3-4 features/session
- 45%+ budget: Increasing error rate, not recommended for production apps

Feature sizing observations:
- Features with 2-5 steps: ~20-50 turns to implement and verify
- Features with 6-10 steps: ~60-100 turns
- Features with 10+ steps: May need feature_split, budget for ~120+ turns

Batch sizing guidelines:
- Batch 1: Safest, most context per feature
- Batch 3: Good balance for features averaging 4-6 steps
- Batch 5-7: Only for very small features (2-3 steps each)

The 1M context window is enabled via the CLI subscription (betas flag in
client.py). This means the Initializer can handle even 400+ feature projects
in a single session. No API key needed.
```

### Implementation

**New file: `server/services/advisor_session.py`**

Similar pattern to `assistant_chat_session.py` (the existing project assistant). Key differences:
- Uses the editable system prompt from settings instead of hardcoded
- Reads project spec and current settings as context
- Outputs structured recommendations (not just free-form chat)
- Can apply recommended settings directly when user approves

```python
class AdvisorSession:
    """AI advisor that helps users configure build settings."""

    async def start(self, project_name: str):
        """Initialize advisor with project context."""
        # Read app_spec.txt for project analysis
        # Read current settings from registry
        # Load advisor_system_prompt from settings
        # Load advisor_knowledge_context from settings
        # Inject project spec + settings + knowledge as context
        # Start conversation

    async def send_message(self, user_message: str):
        """Process user message and return advisor response."""
        # Standard chat flow with Claude
        # Can call internal functions to read/update settings

    async def apply_recommendations(self, recommendations: dict):
        """Apply advisor's recommended settings."""
        # Calls set_setting() for each recommended value
        # Returns confirmation of what was changed
```

**New file: `server/routers/advisor.py`**

WebSocket endpoint (same pattern as `spec_creation.py`):
```
WebSocket: /ws/advisor/{project_name}
  {"type": "start"}       → Starts advisor session with project context
  {"type": "message"}     → User message
  {"type": "apply"}       → Apply recommended settings

REST:
  GET    /api/advisor/sessions         → List active sessions
  DELETE /api/advisor/sessions/{name}  → Cancel session
```

**UI: New component `SetupAdvisor.tsx`**

Accessible from:
1. **After spec creation** — "Would you like the AI advisor to recommend build settings?" button
2. **Settings modal** — "Ask AI Advisor" button in the Agent Budget section
3. **Keyboard shortcut** — Could be mapped to a key (future)

The component is a chat interface (similar to AssistantChat.tsx) with:
- Conversation area showing advisor analysis and recommendations
- "Accept All Recommendations" button
- "Accept" buttons next to individual recommendations
- Link to Settings to manually adjust after seeing recommendations

**Settings UI for editable prompts:**

In SettingsModal.tsx, add a new "AI Advisors" section (collapsed by default):

```
AI Advisors
├── Setup Advisor
│   ├── System Prompt: [textarea, 10 rows, monospace font]
│   │   └── [Reset to Default] button
│   └── Knowledge Context: [textarea, 10 rows, monospace font]
│       └── [Reset to Default] button
│
└── Design Advisor (Phase 4)
    ├── System Prompt: [textarea, 10 rows, monospace font]
    │   └── [Reset to Default] button
    └── Knowledge Context: [textarea, 10 rows, monospace font]
        └── [Reset to Default] button
```

**Settings keys:**

| Key | Type | Default |
|-----|------|---------|
| `advisor_system_prompt` | text | (see default above) |
| `advisor_knowledge_context` | text | (see default above) |
| `design_advisor_system_prompt` | text | (see Phase 4 default) |
| `design_advisor_knowledge_context` | text | (see Phase 4 default) |

**Important:** These are TEXT fields stored as strings in the settings key-value store. The UI renders them as resizable textareas with monospace font. Each has a "Reset to Default" button that restores the factory prompt.

### Why Non-Hardcoded Prompts Matter

1. **Models change** — When a new Claude version drops, the optimal prompting strategy may shift. The user can update the prompt without a code deploy.
2. **Best practices evolve** — As more projects are built, the knowledge context gets richer. Update it with new benchmarks.
3. **Project types differ** — A user building enterprise SaaS might want different advisor behavior than someone prototyping a game. They can customize.
4. **Community contributions** — If the open source community discovers better advisor prompts, they can be shared as text, not PRs.

---

## Phase 4: AI Design Advisor Agent

**Estimated scope:** 1-2 new files, settings additions, new UI component, knowledge source integration

### The Problem

AutoForge already has an incredible design system: 12 styles, style mixing (base + accent), 25 color palettes, 4 accessibility modifiers, live previews, and audience matching. But most users don't know how to combine these effectively for their target audience. They need an AI advisor that understands design principles and current trends.

### What Already Exists (Don't Rebuild This)

The design infrastructure is mature. Reference these files:
- `server/services/style_manager.py` — 12 styles with complete token systems, audience/vibe/age matching (`recommend_styles()`, `AUDIENCE_PROFILES`, `AGE_PROFILES`)
- `server/services/style_modifiers.py` — 4 accessibility modifiers
- `ui/src/data/palettes.ts` — 25 color palettes organized by category
- `ui/src/components/ColorCustomizer.tsx` — Color picker with palette presets
- `ui/src/components/StylePreview.tsx` — Live preview rendering with token merging
- `ui/src/components/NewProjectModal.tsx` — "Help Me Choose" button already exists for style recommendation

### The Design Advisor's Role

Lives in the project setup flow (NewProjectModal step 4 — style selection) AND accessible from project settings. It's a chat agent that:

1. **Understands the target audience** — Reads `app_spec.txt` for target_user, core_problem, app type
2. **Knows all 12 styles intimately** — Token systems, philosophy, what each looks like
3. **Knows design trends** — What's current, what's played out, what works for which demographics
4. **Recommends combinations** — Base style + accent style + color palette + modifiers
5. **Explains WHY** — "For a finance app targeting 40-60 year olds, Minimalism base gives trust and clarity. Add Neumorphism accent for tactile buttons. Use the 'Charcoal & Cream' palette for professional warmth. Enable 'Larger Type' and 'High Contrast Buttons' for the age demographic."

### Design Advisor Prompts (Editable in Settings)

**Default `design_advisor_system_prompt`:**

```
You are AutoForge's Design Advisor. You help users choose the perfect visual
style for their application based on their target audience, app type, and
personal preferences.

You have deep knowledge of:
- 12 design styles (Flat Design, Minimalism, Neumorphism, Glassmorphism,
  Skeuomorphism, Neubrutalism, Bauhaus, Claymorphism, Retro-Futurism,
  Cyberpunk, Dark Mode, Warmer Shades)
- Style mixing (any base style + compatible accent style)
- 25 color palettes across 9 categories
- 4 accessibility modifiers (high contrast buttons, large touch targets,
  high contrast text, larger type)
- Current UI/UX design trends and what's becoming overused

Your job:
1. Understand the app's target audience (age, profession, tech savviness)
2. Understand the app's mood/vibe (professional, fun, cutting-edge, warm)
3. Recommend a complete design configuration:
   - Base style (1 of 12)
   - Accent style (optional, from compatible list)
   - Color palette (1 of 25, or custom)
   - Accessibility modifiers (based on audience needs)
4. Explain WHY each choice works for this specific audience
5. Warn about choices that don't fit (e.g., Cyberpunk for a senior health app)

Design principles to follow:
- Match the style to the AUDIENCE, not the developer's preference
- Accessibility is not optional — if the audience is 40+, recommend modifiers
- Avoid AI-stereotypical aesthetics (generic gradients, over-used purple-to-blue)
- Simple is almost always better than complex for business apps
- Dark mode is a STYLE choice, not just a toggle — it changes the entire feel
- Color palettes should support the brand, not fight the style

When mixing styles, explain what the accent brings:
- "Neumorphism accent adds tactile depth to Minimalism's clean surfaces"
- "Glassmorphism accent gives Dark Mode an elegant frosted quality"
- "Neubrutalism accent adds playful energy to Flat Design's simplicity"
```

**Default `design_advisor_knowledge_context`:**

```
CURRENT DESIGN TRENDS (keep updated):

Played Out / Overused (2024-2026):
- Purple-to-blue gradients (every AI product uses this)
- Glassmorphism on EVERYTHING (was trendy 2022-2023, now overdone)
- Generic dark mode with neon accents (seen in every dev tool)
- Bento grid layouts with random gradient cards
- Over-animated micro-interactions that slow down the experience
- "Figma-default" design (Inter font, 8px rounded corners, blue primary)

Currently Fresh:
- Warm neutrals with a single bold accent color
- Brutalism-lite: bold borders and playful typography without going full chaos
- High-contrast accessibility-first design (looks good AND is accessible)
- Earthy, nature-inspired palettes (Forest Floor, Sand & Stone)
- Intentional whitespace (not empty — purposeful breathing room)
- Dark mode done thoughtfully (not just "invert colors")

Audience-Specific Guidance:
- Finance/Legal: Minimalism or Flat Design. Navy/charcoal palettes. Trust > trendy.
- Health/Senior: Warmer Shades base. ALWAYS enable larger type + high contrast.
  44px minimum touch targets. Sans-serif fonts only.
- Gaming/Youth: Cyberpunk, Retro-Futurism, or Neubrutalism. Bold palettes OK.
  Can push boundaries on animation and color.
- E-commerce: Flat Design or Minimalism. Product images are the star — style
  should not compete with product photography. Clean, fast, trustworthy.
- SaaS/Dashboard: Minimalism or Bauhaus. Data density matters — use compact
  typography with clear hierarchy. Monochrome or cool palettes.
- Creative tools: Glassmorphism or Claymorphism. Show personality. Warmer
  palettes that feel inviting, not clinical.
- Education: Warmer Shades or Claymorphism. Friendly, approachable. Consider
  Neubrutalism accent for younger audiences (K-12).

Style Mixing Compatibility Notes:
- Minimalism works as base with almost anything as accent
- Dark Mode works as base with Glassmorphism or Cyberpunk accent
- Neubrutalism as accent adds energy to any calm base style
- Skeuomorphism as base is niche — only for specific retro aesthetics
- Bauhaus + Retro-Futurism is a surprisingly good combo for creative tools
- Warmer Shades + Claymorphism creates a very friendly, approachable feel

The 25 Color Palettes by Use Case:
- Professional apps: Midnight Office, Charcoal & Cream, Deep Teal
- Apps for women 25-45: Rose Garden, Dusty Mauve, Champagne
- Apps for men 25-45: Midnight Office, Slate Mode, Indigo Night
- Apps for teens: Electric Coral, Retro Arcade, Candy Pop, Citrus Splash
- Apps for seniors: Warmer earth tones — Sand & Stone, Sage Whisper, Sunset Glow
- Premium/luxury: Champagne, Plum Velvet, Obsidian Gold
- Nature/wellness: Forest Floor, Ocean Dusk, Sage Whisper
```

### Implementation

**New file: `server/services/design_advisor_session.py`**

Same pattern as `advisor_session.py` from Phase 3, but with design-specific context:

```python
class DesignAdvisorSession:
    """AI advisor that helps users choose styles, colors, and modifiers."""

    async def start(self, project_name: str):
        """Initialize with project context + full style/palette knowledge."""
        # Read app_spec.txt for target_user, core_problem, app type
        # Load all 12 style definitions from style_manager.py
        # Load all 25 palettes from palettes data
        # Load modifier definitions from style_modifiers.py
        # Load design_advisor_system_prompt from settings
        # Load design_advisor_knowledge_context from settings
        # Inject all context
        # Start conversation

    async def send_message(self, user_message: str):
        """Process user message and return design recommendation."""
        pass

    async def apply_design(self, config: dict):
        """Apply recommended style/palette/modifiers to project config."""
        # Updates project_config.json with:
        #   style_id, accent_style, custom_colors, style_modifiers
        pass
```

**New router: `server/routers/design_advisor.py`**

```
WebSocket: /ws/design-advisor/{project_name}
  {"type": "start"}       → Starts design advisor with project context
  {"type": "message"}     → User message
  {"type": "apply"}       → Apply recommended design configuration

REST:
  GET    /api/design-advisor/sessions         → List active sessions
  DELETE /api/design-advisor/sessions/{name}  → Cancel session
```

**UI Integration:**

The Design Advisor appears in TWO places:

1. **NewProjectModal Step 4** — Replace or enhance the existing "Help Me Choose" button:
   - Currently `recommend_styles()` in `style_manager.py` does rule-based matching
   - Upgrade to: clicking "Help Me Choose" opens the Design Advisor chat
   - Advisor reads the spec (already created in steps 1-3), recommends a full design config
   - User can accept recommendations or continue browsing manually

2. **Project Settings** — "Design Advisor" button that opens the same chat interface
   - For users who want to change their design after initial setup

**New component: `DesignAdvisorChat.tsx`**

Chat interface similar to `AssistantChat.tsx` with additions:
- Live style preview that updates as the advisor makes recommendations
- "Apply This Design" button that sets style + accent + palette + modifiers in one click
- Style/palette chips in the chat that the user can click to preview
- Side-by-side comparison: "Current Design" vs "Recommended Design"

### External Knowledge Sources (Two-Layer System)

The Design Advisor stays current through TWO mechanisms working together:

#### Layer 1: Scheduled Background Knowledge Refresh

A monthly background job fetches design trend articles, summarizes them, and appends to the knowledge context automatically. The user never has to manually paste trend info — it just stays fresh.

**Implementation: `server/services/knowledge_updater.py`**

```python
"""
Design Knowledge Auto-Updater
==============================

Monthly scheduled job that fetches design trend articles from RSS feeds,
summarizes them using Claude, and appends to the design_advisor_knowledge_context
setting. Uses the existing APScheduler infrastructure (scheduler_service.py).
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# RSS feeds to monitor for design trends
# Curated list of high-quality, regularly-updated design sources
DESIGN_FEEDS = [
    {
        "name": "Smashing Magazine",
        "url": "https://www.smashingmagazine.com/feed/",
        "focus": "web design, UX, CSS techniques"
    },
    {
        "name": "CSS-Tricks",
        "url": "https://css-tricks.com/feed/",
        "focus": "CSS, frontend patterns, design systems"
    },
    {
        "name": "UX Collective",
        "url": "https://uxdesign.cc/feed",
        "focus": "UX design, interaction patterns, user research"
    },
    {
        "name": "Nielsen Norman Group",
        "url": "https://www.nngroup.com/feed/rss/",
        "focus": "usability research, UX best practices, accessibility"
    },
    {
        "name": "A List Apart",
        "url": "https://alistapart.com/main/feed/",
        "focus": "web standards, design philosophy, inclusive design"
    },
    {
        "name": "Dribbble Blog",
        "url": "https://dribbble.com/stories/feed",
        "focus": "visual design trends, popular styles, color trends"
    },
    {
        "name": "Codrops",
        "url": "https://tympanus.net/codrops/feed/",
        "focus": "experimental UI, animation trends, creative coding"
    },
    {
        "name": "Web Designer Depot",
        "url": "https://www.webdesignerdepot.com/feed/",
        "focus": "design tools, trend roundups, industry news"
    },
]

# Summarization prompt sent to Claude with the fetched articles
SUMMARIZATION_PROMPT = """You are analyzing recent design articles to extract current UI/UX trends.

From the articles below, extract and summarize:

1. **Trending Now** — What design styles, patterns, or approaches are gaining popularity?
2. **Played Out** — What's becoming overused or cliché? (especially AI-generated aesthetics)
3. **Color Trends** — What color palettes or combinations are appearing frequently?
4. **Accessibility Updates** — Any new accessibility best practices or standards?
5. **Industry-Specific** — Any trends specific to certain industries (fintech, health, e-commerce)?
6. **Typography** — Any font or typography trends worth noting?

Format as bullet points. Be specific and opinionated — don't just list things,
say whether they're worth adopting or avoiding. Include source attribution.

ARTICLES:
{article_summaries}
"""


class KnowledgeUpdater:
    """Fetches and summarizes design trends on a schedule."""

    async def run_update(self) -> str | None:
        """
        Fetch recent articles from design feeds, summarize, and update settings.

        Returns the generated summary text, or None if the update failed.
        """
        from registry import get_setting, set_setting

        try:
            # 1. Fetch recent articles from RSS feeds (last 30 days)
            articles = await self._fetch_recent_articles()
            if not articles:
                logger.warning("No recent articles fetched from design feeds")
                return None

            logger.info(f"Fetched {len(articles)} recent design articles")

            # 2. Summarize using Claude (uses CLI subscription, minimal cost)
            summary = await self._summarize_articles(articles)
            if not summary:
                logger.warning("Failed to summarize design articles")
                return None

            # 3. Build the update block with timestamp
            timestamp = datetime.now(timezone.utc).strftime("%B %Y")
            update_block = f"\n\n--- Auto-Updated: {timestamp} ---\n{summary}"

            # 4. Append to existing knowledge context
            current_context = get_setting(
                "design_advisor_knowledge_context", ""
            )

            # Remove previous auto-update blocks (keep only the latest)
            # Split on the auto-update marker and keep everything before it
            if "--- Auto-Updated:" in current_context:
                # Keep the manually-written part, replace the auto-generated part
                manual_part = current_context.split("--- Auto-Updated:")[0].rstrip()
                updated_context = manual_part + update_block
            else:
                updated_context = current_context + update_block

            set_setting("design_advisor_knowledge_context", updated_context)
            logger.info(f"Design knowledge context updated ({len(summary)} chars)")

            return summary

        except Exception as e:
            logger.error(f"Knowledge update failed: {e}")
            return None

    async def _fetch_recent_articles(self) -> list[dict]:
        """
        Fetch recent articles from RSS feeds.

        Returns list of dicts with keys: title, source, url, summary, date
        """
        import aiohttp
        import feedparser
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        articles = []

        async with aiohttp.ClientSession() as session:
            for feed_info in DESIGN_FEEDS:
                try:
                    async with session.get(
                        feed_info["url"], timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        if resp.status != 200:
                            continue
                        content = await resp.text()

                    parsed = feedparser.parse(content)
                    for entry in parsed.entries[:5]:  # Top 5 per feed
                        # Parse published date
                        published = entry.get("published_parsed")
                        if published:
                            from time import mktime
                            entry_date = datetime.fromtimestamp(
                                mktime(published), tz=timezone.utc
                            )
                            if entry_date < cutoff:
                                continue

                        articles.append({
                            "title": entry.get("title", "Untitled"),
                            "source": feed_info["name"],
                            "url": entry.get("link", ""),
                            "summary": entry.get("summary", "")[:500],
                            "focus": feed_info["focus"],
                        })
                except Exception as e:
                    logger.warning(f"Failed to fetch {feed_info['name']}: {e}")
                    continue

        return articles

    async def _summarize_articles(self, articles: list[dict]) -> str | None:
        """
        Send articles to Claude for trend summarization.

        Uses the Claude Agent SDK client (CLI subscription) for minimal cost.
        A single summarization call uses ~2K input tokens + ~500 output tokens.
        """
        # Build article text for the prompt
        article_text = ""
        for i, article in enumerate(articles[:30], 1):  # Cap at 30 articles
            article_text += (
                f"\n[{i}] {article['title']} ({article['source']})\n"
                f"Focus area: {article['focus']}\n"
                f"Summary: {article['summary']}\n"
            )

        prompt = SUMMARIZATION_PROMPT.format(article_summaries=article_text)

        # Use a lightweight Claude call for summarization
        # This could use the Claude Agent SDK or a direct API call
        # Implementation depends on what's simplest:
        #
        # Option A: Use ClaudeSDKClient with a minimal config (no MCP, no tools)
        # Option B: Use the anthropic Python package directly if an API key is set
        # Option C: Use WebFetch to call a summarization endpoint
        #
        # The implementing agent should choose the approach that fits best.
        # The key constraint: this should use the CLI subscription (not API key)
        # so it doesn't cost extra money.
        #
        # Recommended: Create a minimal ClaudeSDKClient with:
        #   - model = haiku (fastest, cheapest for summarization)
        #   - max_turns = 1 (single response, no tools needed)
        #   - no MCP servers
        #   - no security hooks
        #   - system_prompt = SUMMARIZATION_PROMPT

        # Placeholder for implementation:
        # client = create_summarization_client()
        # response = await client.query(prompt)
        # return response.text

        raise NotImplementedError(
            "Implement using ClaudeSDKClient with haiku model, "
            "max_turns=1, no MCP servers"
        )
```

**Wire into the scheduler: `server/services/scheduler_service.py`**

Add a system-level job alongside the existing per-project agent schedules:

```python
# In SchedulerService.__init__() or start():
async def _schedule_knowledge_updates(self):
    """Schedule monthly design knowledge refresh."""
    from server.services.knowledge_updater import KnowledgeUpdater

    updater = KnowledgeUpdater()

    # Run on the 1st of each month at 3:00 AM UTC
    self.scheduler.add_job(
        updater.run_update,
        trigger=CronTrigger(day=1, hour=3, minute=0),
        id="design_knowledge_update",
        name="Monthly design trend refresh",
        replace_existing=True,
    )
    logger.info("Scheduled monthly design knowledge update (1st of month, 3am UTC)")
```

**Settings for the scheduler:**

| Key | Type | Default | UI Control |
|-----|------|---------|------------|
| `knowledge_auto_update` | bool | true | Toggle |
| `knowledge_update_interval` | string | "monthly" | Dropdown: weekly/monthly/quarterly |
| `knowledge_feed_urls` | text | (DESIGN_FEEDS urls, one per line) | Textarea |

The feed URL list is also editable in Settings — users can add/remove sources, add industry-specific blogs, or point to their company's internal design system blog.

**New pip dependencies:** `feedparser`, `aiohttp` (aiohttp likely already installed for the async server)

**UI: Knowledge Update Status**

In the Settings > AI Advisors > Design Advisor section, show:

```
Knowledge Auto-Update: [ON] / [OFF]
Update Frequency: [Weekly] [Monthly] [Quarterly]
Last Updated: February 1, 2026
Next Update: March 1, 2026
[Run Update Now] button
Feed Sources: [textarea with URLs, one per line]
```

The "Run Update Now" button triggers `KnowledgeUpdater.run_update()` immediately via a REST endpoint:

```
POST /api/design-advisor/update-knowledge
  → Returns: { "success": true, "summary": "...", "articles_processed": 23 }
```

#### Layer 2: Live Web Search During Advisor Conversations

The Design Advisor also searches the web in real-time during conversations when it needs specific, current information. This complements the cached knowledge with on-demand freshness.

**Implementation:** Add WebSearch/WebFetch instructions to the Design Advisor's system prompt. These tools are already available in the Claude Agent SDK (`client.py` lines 292-301: `BUILTIN_TOOLS` includes `WebFetch` and `WebSearch`).

**Add to the default `design_advisor_system_prompt`:**

```
## LIVE TREND RESEARCH

You have access to WebSearch and WebFetch tools. Use them when:
- The user asks about very recent design trends (last 1-2 months)
- You need to verify if a style/pattern is still current or has become cliché
- The user mentions a specific design trend you're not confident about
- You need industry-specific design guidance not in your knowledge context
- The user asks "what's trending right now for [industry] apps?"

Example searches you might perform:
- "UI design trends 2026 [industry]"
- "is glassmorphism still popular 2026"
- "[color palette name] overused design"
- "best design systems for [app type] 2026"
- "accessibility design trends WCAG 2026"

When citing search results, tell the user where the information came from.
This builds trust and lets them explore further.

IMPORTANT: Don't search for every recommendation. Use your built-in knowledge
and the knowledge context for standard recommendations. Only search when you
need something very current or very specific.
```

**How the two layers work together:**

```
Layer 1 (Background):                    Layer 2 (Live):
Monthly RSS fetch                        Real-time web search
        ↓                                       ↓
Claude summarizes articles               Search during conversation
        ↓                                       ↓
Appends to knowledge_context             Results cited in chat
        ↓                                       ↓
Advisor reads on next conversation       Advisor uses immediately
        ↓                                       ↓
Covers broad trends                      Covers specific questions
Cost: ~free (1 haiku call/month)         Cost: ~2-5 turns per search
```

**The user controls both:**
- Layer 1: Toggle on/off, set frequency, edit feed URLs — all in Settings
- Layer 2: Edit the system prompt to add/remove search instructions — also in Settings
- Both layers feed into the same Design Advisor conversation
- If auto-update generates bad summaries, user can delete them from the knowledge textarea
- If live search wastes too many turns, user can remove the search section from the prompt

---

## Implementation Order

```
Phase 1: Configurable Levers
├── Already documented in feature-sizing-overhaul-handoff.md
├── 10 files, ~300 LOC
├── No dependencies
└── Foundation for everything else

Phase 2: Care Levels (1-5)
├── Modify create-spec.md (1 file, major rewrite of Phase 2)
├── Add default_care_level to settings (minor, follows Phase 1 patterns)
├── Depends on: Phase 1 (settings infrastructure used)
└── Can be done independently if needed

Phase 3: AI Setup Advisor
├── New: server/services/advisor_session.py
├── New: server/routers/advisor.py
├── New: ui/src/components/SetupAdvisor.tsx
├── Settings: advisor_system_prompt, advisor_knowledge_context
├── Depends on: Phase 1 (levers must exist to recommend values)
└── Follows existing patterns: assistant_chat_session.py, spec_chat_session.py

Phase 4: AI Design Advisor + Knowledge Auto-Update
├── New: server/services/design_advisor_session.py
├── New: server/services/knowledge_updater.py (RSS fetch + summarize)
├── New: server/routers/design_advisor.py (includes /update-knowledge endpoint)
├── New: ui/src/components/DesignAdvisorChat.tsx
├── Settings: design_advisor_system_prompt, design_advisor_knowledge_context,
│             knowledge_auto_update, knowledge_update_interval, knowledge_feed_urls
├── Scheduler: Monthly CronTrigger job in scheduler_service.py
├── New pip deps: feedparser (aiohttp likely already present)
├── Depends on: Phase 3 (shared patterns and UI components)
├── Two-layer knowledge: Background RSS refresh + Live WebSearch in conversations
└── Integrates with: style_manager.py, palettes.ts, StylePreview.tsx,
                      scheduler_service.py (APScheduler)
```

---

## Settings Summary (All Phases)

### Phase 1 Settings (Agent Budget)

| Key | Type | Default | Range | UI Control |
|-----|------|---------|-------|------------|
| `context_budget_pct` | int | 30 | 15-50 | Button group |
| `hard_stop_buffer_pct` | int | 5 | 3-15 | Button group |
| `turns_per_step` | int | 10 | 5-20 | Button group |
| `min_feature_turns` | int | 30 | 15-50 | Button group |
| `budget_checkpoint_interval` | int | 30 | 10-40 | Button group |
| `max_feature_retries` | int | 3 | 1-5 | Button group |
| `max_total_agents` | int | 10 | 5-15 | Button group |

### Phase 2 Settings (Spec Creation)

| Key | Type | Default | Range | UI Control |
|-----|------|---------|-------|------------|
| `default_care_level` | int | 3 | 1-5 | Button group |

### Phase 3 Settings (Setup Advisor)

| Key | Type | Default | UI Control |
|-----|------|---------|------------|
| `advisor_system_prompt` | text | (see Phase 3 section) | Textarea, 10 rows, monospace |
| `advisor_knowledge_context` | text | (see Phase 3 section) | Textarea, 10 rows, monospace |

### Phase 4 Settings (Design Advisor + Knowledge Updates)

| Key | Type | Default | UI Control |
|-----|------|---------|------------|
| `design_advisor_system_prompt` | text | (see Phase 4 section) | Textarea, 10 rows, monospace |
| `design_advisor_knowledge_context` | text | (see Phase 4 section) | Textarea, 10 rows, monospace |
| `knowledge_auto_update` | bool | true | Toggle |
| `knowledge_update_interval` | string | "monthly" | Dropdown: weekly/monthly/quarterly |
| `knowledge_feed_urls` | text | (default RSS feed URLs, one per line) | Textarea |

---

## Settings UI Layout (All Phases Combined)

```
Settings Modal
├── General (existing)
│   ├── Model Selection
│   ├── YOLO Mode
│   └── Headless Browser
│
├── Build Settings (existing + Phase 1 + Phase 2)
│   ├── Batch Size: [1] [2] [3] [5] [7]          ← updated range
│   ├── Max Parallel Agents: [1] [2] [3] [4] [5] ← existing
│   ├── Spec Creation Detail: [1] [2] [3] [4] [5] ← NEW Phase 2
│   │
│   ├── Agent Context Budget                       ← NEW Phase 1
│   │   ├── Context Budget: [20%] [25%] [30%] [35%] [40%] [45%]
│   │   ├── Derived Values (read-only):
│   │   │   Target Turn: 90 | Hard Stop: 105 | Max Turns: 115
│   │   │   Usable: 70 | Est. Features/Session: ~2-3
│   │   └── [▶ Advanced Budget Controls]
│   │       ├── Hard Stop Buffer: [3%] [5%] [8%] [10%] [15%]
│   │       ├── Turns Per Step: [5] [8] [10] [15] [20]
│   │       ├── Min Feature Turns: [15] [20] [30] [40] [50]
│   │       ├── Checkpoint Interval: [10] [15] [20] [30] [40]
│   │       ├── Max Feature Retries: [1] [2] [3] [4] [5]
│   │       └── Max Total Agents: [5] [8] [10] [12] [15]
│   │
│   └── [Ask AI Advisor] button                    ← NEW Phase 3
│
├── API Provider (existing)
│   └── ...
│
└── AI Advisors (collapsed by default)             ← NEW Phase 3+4
    ├── Setup Advisor
    │   ├── System Prompt: [textarea]
    │   │   └── [Reset to Default]
    │   └── Knowledge Context: [textarea]
    │       └── [Reset to Default]
    │
    └── Design Advisor
        ├── System Prompt: [textarea]
        │   └── [Reset to Default]
        ├── Knowledge Context: [textarea]
        │   └── [Reset to Default]
        │
        └── Knowledge Auto-Update                  ← NEW Phase 4
            ├── Enabled: [ON] / [OFF]
            ├── Frequency: [Weekly] [Monthly] [Quarterly]
            ├── Last Updated: February 1, 2026
            ├── Next Update: March 1, 2026
            ├── [Run Update Now] button
            └── Feed Sources: [textarea, URLs one per line]
```

---

## What NOT to Change (Across All Phases)

1. **The 12 style definitions** — Don't modify style_manager.py's STYLE_REGISTRY
2. **The 25 color palettes** — Don't modify palettes.ts
3. **The 4 accessibility modifiers** — Don't modify style_modifiers.py
4. **The feature creation system** — Keep Initializer's granular features as-is
5. **The 20 mandatory test categories** — Keep the distribution table
6. **The 1M context beta** — Already enabled, don't touch `client.py` line 641
7. **The `feature_split` MCP tool** — Still the runtime escape valve
8. **The dependency DAG system** — Wide graphs, no cycles, still enforced

---

## Future Enhancements (Not Part of This Implementation)

1. **Per-project overrides** — `.autoforge/agent_config.yaml` for project-specific lever values
2. **Session metrics tracking** — `session_metrics` table logging turns used, context %, errors, duration per agent session. Feeds into advisor's knowledge over time.
3. **Advisor learning** — Track which recommendations led to successful builds, weight future recommendations accordingly. Both Setup Advisor and Design Advisor benefit from historical data showing what settings/designs produced the best outcomes.
4. **Community prompt library** — Share advisor prompts that work well for specific project types. Users could export/import advisor prompts and knowledge contexts.
5. **Initializer max_turns lever** — Currently hardcoded at 200, could be adjustable for very complex projects
6. **Setup Advisor knowledge auto-update** — Same RSS + summarization pattern as the Design Advisor, but for build optimization articles. Sources: Anthropic blog (model updates), CI/CD best practices, Claude Code changelog.
7. **Design advisor screenshot analysis** — Feed the Design Advisor screenshots of competitor apps or design inspiration. Uses the existing `style_extractor.py` vision LLM pipeline to extract tokens from images and recommend matching AutoForge configurations.
8. **A/B design testing** — Generate two style configurations, build both, let the user compare side-by-side with the live preview system.
