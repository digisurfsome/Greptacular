# AutoForge Systems Reference — For PRD Maker Integration

> This document covers four core AutoForge systems that should be replicated or referenced
> in the PRD Maker app. Each section includes architecture overview, how it works,
> key file locations (linkable within the AutoForge repo), and enough implementation
> detail for an agent to understand and rebuild these systems.

---

## Table of Contents

1. [Style Set System (Step 3 — Design Guide & Live Preview)](#1-style-set-system)
2. [Screenshot-to-Theme Engine (Astro/WordPress Theme Maker)](#2-screenshot-to-theme-engine)
3. [Dependency Graph System (Visual + Ordering Logic)](#3-dependency-graph-system)
4. [Boilerplate Selection & GitHub Integration](#4-boilerplate-selection--github-integration)

---

## 1. Style Set System

### What It Does
During project creation (Step 3 of the AutoForge flow), users pick a visual design style
from 12 predefined options. As they click different style cards, the **live preview renderer
changes in real-time** — showing a Landing page, Dashboard, Settings, and Feed page all
rendered with that style's exact design tokens. This is the "gold" feature.

### Architecture

**Frontend Components:**
- `ui/src/components/StyleCardPreview.tsx` — Mini 120-150px tile previews showing cards/buttons/inputs in the style
- `ui/src/components/StylePreview.tsx` — Full live preview renderer (~2000 lines), renders 4 sample pages using resolved tokens
- `ui/src/components/StyleFullPreview.tsx` — Full-screen overlay with style selector strip, page tabs, modifier toggles, accent selector
- `ui/src/components/ThemeSelector.tsx` — Simple dropdown theme picker

**Backend Services:**
- `server/services/style_manager.py` — Registry of 12 styles with complete design tokens, audience/vibe/age matching
- `server/services/style_extractor.py` — Vision LLM service that analyzes screenshots and extracts design tokens
- `server/services/style_modifiers.py` — 4 accessibility modifiers that layer on top of any style
- `server/services/design_guide_session.py` — AI chat that helps users choose styles via conversation
- `server/routers/design_guide.py` — WebSocket endpoint for the design guide chat

### The 12 Styles

| ID | Name | Best For |
|----|------|----------|
| flat-design | Flat Design | Clarity, scalability, universal appeal |
| minimalism | Minimalism | Premium feel, Apple-style elegance |
| neumorphism | Neumorphism | Finance apps, dashboards, toggles |
| glassmorphism | Glassmorphism | Modern SaaS, trendy products |
| skeuomorphism | Skeuomorphism | Familiarity, older demographics |
| neubrutalism | Neubrutalism | Young/edgy, Gen Z products |
| bauhaus | Bauhaus | Design-forward, artistic |
| claymorphism | Claymorphism | Friendly, approachable products |
| retro-futurism | Retro Futurism | Gaming, entertainment |
| cyberpunk | Cyberpunk | Edgy tech, gaming |
| dark-mode | Dark Mode Elegant | Developer tools, media apps |
| warmer-shades | Warmer Shades | Nostalgic, comfortable feel |

### Style Data Structure (Each Style Contains)

```python
{
    "id": "flat-design",
    "name": "Flat Design",
    "category": "core",
    "description": "Simple 2D, solid colors, clean icons, minimal ornamentation",
    "best_for": "Clarity, scalability, universal appeal",
    "philosophy": "Remove all decorative elements. Every pixel serves a purpose.",
    "style_guide": {
        "color_tokens": {
            "brand": {"light": "#60A5FA", "DEFAULT": "#3B82F6", "dark": "#2563EB"},
            "surface": {"canvas": "#FFFFFF", "base": "#F8FAFC", "muted": "#F1F5F9"},
            "text": {"primary": "#0F172A", "secondary": "#475569", "tertiary": "#94A3B8"},
            "border": {"subtle": "#E2E8F0", "DEFAULT": "#CBD5E1"},
            "status": {"success": "#22C55E", "error": "#EF4444", "warning": "#F59E0B", "info": "#3B82F6"}
        },
        "typography": {
            "font_family": "Inter",
            "hierarchy": [
                {"level": "Display", "size": "36px", "weight": 700, "line_height": 1.2},
                {"level": "H1", "size": "28px", "weight": 600, "line_height": 1.3},
                {"level": "H2", "size": "22px", "weight": 600, "line_height": 1.35},
                {"level": "H3", "size": "18px", "weight": 600, "line_height": 1.4},
                {"level": "Body", "size": "14px", "weight": 400, "line_height": 1.6},
                {"level": "Micro", "size": "12px", "weight": 400, "line_height": 1.5}
            ]
        },
        "components": {
            "cards": {
                "background": "surface-base",
                "border": "1px solid border-subtle",
                "radius": "8px",
                "shadow": "none",
                "padding": "16px"
            },
            "buttons": {
                "primary_bg": "brand-DEFAULT",
                "primary_text": "#FFFFFF",
                "radius": "6px",
                "padding": "10px 20px",
                "hover": "brand-dark"
            },
            "inputs": {
                "background": "surface-canvas",
                "border": "1px solid border-DEFAULT",
                "radius": "6px",
                "padding": "10px 12px"
            },
            "icons": {"style": "Line/stroke, 1.5px, rounded caps", "size": "20px"}
        },
        "spacing": {
            "base_unit": "4px",
            "density": "Balanced",
            "card_gap": "16px",
            "section_gap": "24px"
        },
        "tailwind_config": {
            "colors": {
                "brand": {"light": "#60A5FA", "DEFAULT": "#3B82F6", "dark": "#2563EB"},
                "surface": {"canvas": "#FFFFFF", "base": "#F8FAFC", "muted": "#F1F5F9"},
                "text": {"primary": "#0F172A", "secondary": "#475569", "tertiary": "#94A3B8"},
                "border": {"subtle": "#E2E8F0"}
            },
            "fontFamily": {"sans": ["Inter", "ui-sans-serif", "system-ui", "sans-serif"]},
            "borderRadius": {"card": "8px", "input": "6px", "btn": "6px"},
            "boxShadow": {"card": "none"}
        }
    }
}
```

### How the Live Preview Renderer Works

**Token Resolution System:**
1. Takes a `StyleGuide` object (color_tokens, typography, components, spacing, tailwind_config)
2. Merges base style guide + optional accent guide + 0-3 accessibility modifiers
3. Resolves token references — e.g., `"brand-DEFAULT"` looks up `color_tokens.brand.DEFAULT` → `"#3B82F6"`
4. Handles raw CSS values, gradients, shadows
5. Fallback chain for missing values

**Multi-Page Preview (4 Sample Pages):**
- **Landing**: Hero section with CTA buttons, feature cards grid, call-to-action block
- **Dashboard**: Stats cards with numbers, data tables, chart placeholders
- **Settings**: Form controls, toggles, section dividers, save buttons
- **Feed**: Article/content cards, comments, metadata tags, interaction buttons

**Modifier Merging:**
- Accent only affects interactive elements (buttons, inputs, cards)
- Modifiers adjust weights, padding, sizing without replacing the base style

### Accessibility Modifiers (4 Available)

| Modifier | Effect |
|----------|--------|
| High Contrast Buttons | 2px borders, 700 weight, 44px min height |
| Large Touch Targets | 48px minimum, increased padding/gaps |
| High Contrast Text | WCAG AAA (7:1) contrast, 500+ body weight |
| Larger Type | All fonts scale 1.15x, body line-height 1.8 |

### Audience/Vibe/Age Recommendation Engine

The system can recommend styles based on three dimensions:

**Audience Profiles:**
- Health-conscious/50+ → recommends minimalism, neumorphism; avoids neubrutalism, cyberpunk
- Young/Edgy/Gen Z → recommends neubrutalism, cyberpunk, retro-futurism
- Premium/Luxury → recommends minimalism, glassmorphism
- Friendly/Approachable → recommends claymorphism, flat-design
- Finance/Dashboard → recommends neumorphism, minimalism
- Gaming/Entertainment → recommends retro-futurism, cyberpunk

**Vibe Profiles:** Trustworthy, Fun, Modern, Nostalgic — each boosts certain styles

**Age Profiles:** Under 30, 30-50, 50+ — each boosts/penalizes certain styles

**Scoring:** Each dimension adds/subtracts from style scores. Styles with score > 0 are returned ranked.

### Design Guide Chat

A WebSocket-based AI chat (Claude) acts as a friendly design consultant. It can embed
action blocks to programmatically select styles in the UI:

```
```action
{"action": "select_style", "styleId": "minimalism"}
```
```

Available actions: `select_style`, `set_color`, `set_font`, `reset_customizations`

---

## 2. Screenshot-to-Theme Engine

### What It Does
Takes a screenshot of ANY website or app and extracts the "Visual DNA" — color tokens,
typography, component patterns — into a reusable style guide. This powers both the
Astro theme maker and WordPress theme maker.

### The "Idea Code" Methodology (Mentor's 5-Page System)

This is based on a 5-page Google Doc methodology that turns any screenshot into a complete
style sheet/theme. The implementation lives in `style_extractor.py`.

### How It Works

1. **User provides a screenshot** (base64 encoded, PNG or JPEG)
2. **Vision LLM analysis** — Screenshot sent to Claude with the extraction prompt
3. **Claude extracts Visual DNA:**
   - Abstract Color Tokens (brand, surface, text, border, status — all with exact hex values)
   - Global Typography System (font family, hierarchy from Display to Micro)
   - Universal Component Patterns (cards, buttons, inputs, icons with CSS values)
   - Layout & Spacing Physics (base unit, density, radius rules)
   - Tailwind CSS Theme Extension (complete JSON config)
   - Style Classification (matches to one of 12 known styles with confidence levels)
4. **Response parsed** into structured data:
   - `identified_style`: primary + accent style IDs with confidence
   - `extracted_tokens`: Tailwind config JSON
   - `style_guide_markdown`: Full markdown design system document
   - `tailwind_config`: Parsed theme extension

### The Extraction Prompt (Full Production Version)

```
Role: You are an expert Design System Architect and Senior Frontend Engineer.
You specialize in "Atomic Design" principles and creating abstract, reusable
component libraries.

Objective: I will provide an image. Your task is to ignore the specific content,
text, and business context of the image. Instead, extract the underlying Visual
Design Language (the "Visual DNA"). I need a generic, reusable style guide that
I can apply to any type of application, not just the one shown in the image.

Strict Constraints:
1. Do not mention specific text found in the image
2. Do not mention specific business logic
3. Generalize all findings into reusable tokens and classes
4. Name tokens by FUNCTION not content (brand-DEFAULT not "revenue-title-color")

Output Requirements — Generate a Technical Design System Report covering:

### 1. Abstract Color Tokens (Global Variables)
Extract the palette named by function:
- Brand/Primary: (main interaction color with light/DEFAULT/dark variants)
- Surface/Backgrounds: (canvas, base/cards, muted/inputs)
- Text Hierarchy: (primary, secondary/muted, tertiary)
- Borders/Dividers: (line colors)
- Status Colors: (success, error, warning if present)
Provide EXACT hex values where possible, with [approx] tag if estimated.

### 2. Global Typography System
- Font family (or closest Google Font match)
- Define the abstract hierarchy:
  Display/Hero | Headings (H1-H3) | Body (regular/bold) | Microcopy
- Include weights (400-700) and approximate line-heights

### 3. Universal Component Patterns
- Surfaces/Cards: radius, border, shadow, background (provide CSS values)
- Buttons: primary/secondary styles (padding, radius, color, hover)
- Form Inputs: background, border, radius
- Icons: visual style description (stroke weight, caps, fill)

### 4. Layout & Spacing Physics
- Spacing scale base unit (4px, 8px, or 10px)
- Density: Cozy (whitespace-heavy) or Compact (data-dense)
- Radius consistency rule

### 5. Tailwind CSS Theme Extension
Provide a valid JSON object for the theme extension:
{
  "colors": { "brand": {...}, "surface": {...}, "text": {...}, "border": {...} },
  "fontFamily": { "sans": ["FontName", "fallback"] },
  "borderRadius": { "card": "Xpx", "input": "Xpx", "btn": "Xpx" },
  "boxShadow": { "card": "shadow-value" }
}

### 6. Style Classification
PRIMARY_STYLE: style-id (confidence: high/medium/low)
ACCENT_STYLE: style-id or none (confidence: high/medium/low)
```

### Parsing Logic

The response parser handles:
- `PRIMARY_STYLE: style-id (confidence: high/medium/low)` pattern matching
- `ACCENT_STYLE: style-id (confidence: high/medium/low)` pattern matching
- Fuzzy style name matching (e.g., "minimal" → "minimalism", "glass" → "glassmorphism")
- JSON extraction from code fences for Tailwind config
- Fallback patterns for alternate response formats

### Integration with Astro/WordPress Theme Maker

The extracted style guide (Tailwind config + design tokens) feeds directly into:
- **Astro Theme**: Generates Tailwind config, CSS custom properties, and component styles
- **WordPress Theme**: Generates theme.json, style.css variables, and block styles
- The same extraction works for both — the output format is platform-agnostic design tokens

### Key File
- `server/services/style_extractor.py` — Complete implementation (331 lines)

---

## 3. Dependency Graph System

### What It Does
Two parts: (1) A visual interactive graph showing feature dependencies, and (2) a backend
algorithm that determines build order, detects cycles, and schedules what gets built next.

### Visual Component — DependencyGraph.tsx

**Tech Stack:** `@xyflow/react` (React Flow) + `dagre` for auto-layout

**Features:**
- Auto-layout using dagre with configurable spacing (nodesep: 50, ranksep: 100)
- Layout direction toggle (Left-to-Right / Top-to-Bottom)
- Status-based node coloring:
  - `pending` — gray/neutral
  - `in_progress` — blue/active (shows agent mascot avatar)
  - `done` — green/complete
  - `blocked` — red/warning
- MiniMap and zoom controls
- Click a node to see feature details
- Error boundary for stability
- Responsive to real-time agent updates via WebSocket

**Data Format:**
```typescript
interface GraphNode {
  id: number
  name: string
  category: string
  status: 'pending' | 'in_progress' | 'done' | 'blocked'
  priority: number
  dependencies: number[]  // IDs of prerequisite features
}
```

**Key File:** `ui/src/components/DependencyGraph.tsx`

### Backend — Dependency Resolver

**Algorithm:** Kahn's Algorithm for topological sorting with priority-aware heap ordering.

**Core Functions:**

```python
def resolve_dependencies(features: list[dict]) -> DependencyResult:
    """
    Topological sort using Kahn's algorithm.
    Returns:
      - ordered_features: Build order respecting all dependencies
      - circular_dependencies: Any detected cycles
      - blocked_features: feature_id -> [blocking_feature_ids]
      - missing_dependencies: feature_id -> [missing_ids]
    """

def are_dependencies_satisfied(feature: dict, features: list[dict]) -> bool:
    """Check if ALL dependencies of a feature have passes=True"""

def get_blocking_dependencies(feature: dict, features: list[dict]) -> list[dict]:
    """Return list of incomplete blocking dependencies"""

def would_create_circular_dependency(features, feature_id, new_dep_id) -> bool:
    """DFS cycle detection BEFORE adding a new dependency"""

def compute_scheduling_scores(features: list[dict]) -> dict[int, float]:
    """Score features for scheduling priority:
    - Unblocking potential: how many downstream features get unblocked
    - Depth in graph: root features score higher
    - User priority field
    """

def get_ready_features(features: list[dict]) -> list[dict]:
    """Features with ALL deps satisfied, sorted by scheduling score"""

def build_graph_data(features: list[dict]) -> dict:
    """Convert features to visualization format for the React component"""
```

**Security Limits:**
- `MAX_DEPENDENCIES_PER_FEATURE = 20`
- `MAX_DEPENDENCY_DEPTH = 50` (prevents stack overflow in cycle detection)

**Key File:** `api/dependency_resolver.py`

### Parallel Orchestrator — Dependency-Aware Multi-Agent Scheduling

The `parallel_orchestrator.py` uses the dependency resolver to coordinate multiple
AI coding agents working simultaneously.

**Process Limits:**
- MAX_PARALLEL_AGENTS = 5
- MAX_TOTAL_AGENTS = 10
- DEFAULT_CONCURRENCY = 3

**Feature Batching Algorithm:**
1. Get ready features (all deps satisfied), sorted by scheduling score
2. Estimate turns per feature: `step_count × TURNS_PER_STEP (10)`
3. Budget target: 45% context usage (~120 usable turns)
4. Chain extension: add dependents if they fit in budget
5. Same-category fill: fill remaining budget with same-category features
6. Respect batch_size (1-3) AND turn budget
7. MIN_FEATURE_TURNS = 30 (floor for tiny features)

**Key File:** `parallel_orchestrator.py`

### Build Planning Workflow (for PRD Maker)

1. **Parse PRD output** → Convert features to GraphNode[]
2. **Visual review** → Render DependencyGraph with node interaction
3. **Edit dependencies** → Connect/disconnect edges
4. **Topological sort** → Kahn's algorithm identifies layers
5. **Phase assignment** → Each layer = parallel execution phase
6. **Export structure** → Feed to agent for sequential/parallel build

### PRD Documentation
- `docs/prd-dependency-graph-component.md` — Complete component specification with:
  - Use cases (AutoForge, project management, CI/CD, learning paths)
  - Props API with all configuration options
  - Technical architecture (component hierarchy, state management)
  - Stretch features (critical path, parallel groups, phase visualization, drag-to-connect)

---

## 4. Boilerplate Selection & GitHub Integration

### What It Does
Step 1 of project creation: user picks a starting point from 4 categories. If they
provide a GitHub token, the system creates a fresh repo. Otherwise it clones the
boilerplate locally.

### The 4 Boilerplate Categories

**Web Application** (`web-supabase-stripe`):
- Next.js + TypeScript + Supabase + Stripe + PostHog + Loops.so + Netlify
- Pre-built: Auth, Stripe subscriptions, PostHog analytics, Loops.so emails, account management, dark/light theme, CI/CD, Netlify deploy
- Repo: `https://github.com/digisurfsome/Web-BoilerPlate-D2D`

**Mobile Application** (`mobile-flutter-firebase`):
- Flutter + Dart + Firebase (Auth, Firestore, Storage, Functions, Messaging, Remote Config) + Riverpod + RevenueCat + Mixpanel + Sentry + GoRouter + Freezed
- Pre-built: 7 auth methods, RevenueCat paywall, multi-step onboarding, push notifications, Riverpod state, GoRouter navigation, Firestore offline, Firebase Storage uploads, Cloud Functions, Remote Config feature flags, Mixpanel analytics, Sentry errors, Material 3 theming, responsive layouts, i18n, in-app review, feedback voting, profile with avatar, settings with account deletion, 30+ UI components, 7 complete screens, CI/CD
- Repo: `https://github.com/digisurfsome/apparence-kit-firebase`

**Web + Mobile** (`web-mobile-full-stack`):
- Next.js + Flutter + Dart + TypeScript + Supabase + Stripe + PostHog
- Combination of web and mobile boilerplates

**From Scratch** (`scratch`):
- No boilerplate — user decides during spec creation
- Full control over tech stack and architecture

### Boilerplate Data Structure

```python
BOILERPLATE_REGISTRY = {
    "web": {
        "label": "Web Application",
        "options": [{
            "id": "web-supabase-stripe",
            "name": "Web App (Supabase + Stripe)",
            "description": "Full-stack web SaaS...",
            "tech_summary": "Next.js + TypeScript + Supabase + Stripe + PostHog + Loops.so + Netlify",
            "repo_url": "https://github.com/digisurfsome/Web-BoilerPlate-D2D",
            "available": True,
            "pre_built": [
                "Authentication (Supabase Auth)",
                "Stripe subscriptions and one-time payments",
                "PostHog analytics tracking",
                # ... etc
            ]
        }]
    },
    # mobile, web_mobile, scratch categories follow same pattern
}
```

### Clone Operation

```python
async def clone_boilerplate(option_id: str, target_dir: str) -> dict:
    """
    1. Shallow clone of boilerplate repo using git
    2. Removes original .git history (clean slate)
    3. Initializes fresh git repository
    4. Returns clone metadata with ISO 8601 timestamp
    """
```

### GitHub Integration

**3 Core Functions:**

```python
async def validate_github_token(token: str) -> dict:
    """Validate token via GET /user. Returns {login, name, avatar_url}"""

async def create_repo_from_template(
    token, template_owner, template_repo, new_repo_name,
    private=True, description=""
) -> dict:
    """Create GitHub repo from template. Returns {status, repo_url, clone_url, full_name, private}"""

async def create_empty_repo(
    token, repo_name, private=True, description=""
) -> dict:
    """Create empty GitHub repo (for scratch). Returns same schema."""

def slugify_repo_name(name: str) -> str:
    """Convert project name to valid GitHub repo name (kebab-case)"""
```

**Flow:**
1. User provides GitHub personal access token (optional)
2. If token provided → validate via GitHub API `/user`
3. If boilerplate selected → use GitHub template API (`/repos/{owner}/{repo}/generate`)
4. If "From Scratch" → create empty repo with `auto_init: True`
5. If no token → just git clone locally without GitHub remote

### Project Creation Endpoint

`POST /api/projects` with schema:
```python
class ProjectCreate(BaseModel):
    name: str               # 1-50 chars, alphanumeric + hyphens + underscores
    path: str               # Absolute path to project directory
    spec_method: str        # "claude" or "manual"
    boilerplate_id: str     # e.g., "web-supabase-stripe", "scratch"
    style_id: str           # UI style/theme ID
    accent_style: str       # Accent style ID
    modifier_ids: list[str] # Accessibility modifier IDs
    custom_colors: dict     # Color role overrides
    palette_id: str         # Preset palette ID
```

**Initialization Flow:**
1. Validate project name and path
2. Clone boilerplate (or create directory for scratch)
3. Scaffold `.autoforge/prompts/` directory
4. Save `project_config.json` with all selections
5. Save style guide markdown
6. Generate CSS theme files
7. Register project in SQLite registry

### Key Files
- `server/services/boilerplate_manager.py` — Registry and clone logic
- `server/services/github_integration.py` — GitHub API integration
- `server/routers/projects.py` — Project creation endpoint
- `server/schemas.py` — Request/response schemas
- `docs/boilerplate-web-d2d.md` — Web boilerplate documentation
- `docs/boilerplate-flutter-firebase.md` — Mobile boilerplate documentation

---

## Related PRD Documents in AutoForge

These docs in `docs/` provide additional context for the PRD Maker:

| Document | What It Covers |
|----------|---------------|
| `rant-to-prd-spec.md` | 7-stage pipeline: Rant → PRD (Transcriber, Classifier, Gap Analyst, Decision Facilitator, Mechanism Analyst, PRD Compiler, AutoForge Bridge) |
| `rant-to-prd-addendum.md` | Verification agents, Developer's Choice scoring, Feature Addition Engine, Codebase Reality Engine |
| `prd-build-planner-v2.md` | Complete Build Planner PRD (two-agent split, queue management, dashboard) |
| `prd-prd-shredder.md` | PRD ingestion, gravity-feed queue, overnight batch processing |
| `prd-dependency-graph-component.md` | Full component spec with props API and stretch features |
| `normieforge-product-concept.md` | Consumer version concept (Normies → Power Normies → Vibe Coders) |
| `normieforge-metaprogram-engine.md` | Personalization via 3 metaprograms, 8 communication profiles |
| `prd-image-calibration-system.md` | Autonomous image generation loop with multi-agent scoring |
| `prd-reverse-engineering-scanner.md` | Auto-mapping apps to specs (Browser Use + ADB) |
| `coding-structure-reference/` | Universal coding standards extracted from AutoForge and VidAi |

---

## How to Use This Document

**For the PRD Maker agent:** Paste this entire document as context. It contains:
- Complete data structures for all systems
- Algorithm descriptions with enough detail to implement
- The exact extraction prompt for screenshot-to-theme
- File paths for deeper code review if needed

**For future reference:** This document is saved at:
`docs/PRD_MAKER_REFERENCE_SYSTEMS.md`

All file paths in this document are relative to the AutoForge repo root:
`C:/Users/lober/GitHub/Greptacular - AutoForge Build/Greptacular/`
