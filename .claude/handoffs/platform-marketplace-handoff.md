# Platform Marketplace: Boilerplates, Styles, and Plugins

## Overview

This handoff describes the marketplace features that transform AutoForge from a standalone coding agent into a platform ecosystem. Three marketplaces -- boilerplates, styles, and plugins -- create revenue streams, increase user stickiness, and attract professional designers and developers as contributors.

**The business model:** Users already pay $219/build (web) or $299/build (dual web+mobile). The marketplace adds upsells on top of build credits. A user selects a premium boilerplate ($49-199), picks a premium style ($9-99), and installs plugins ($19-49) before the agent starts building. The agent produces higher-quality output because the starting point is better, and AutoForge earns margin on every asset sold.

**Why this matters:**
1. **Passive revenue.** Assets sell repeatedly with near-zero marginal cost.
2. **Lock-in.** Users accumulate purchased styles and boilerplates -- switching to a competitor means abandoning their library.
3. **Network effects.** Community contributors create a flywheel: more assets attract more users, more users attract more contributors.
4. **Quality moat.** Professionally designed boilerplates and styles produce better agent output than competitors starting from blank projects.

---

## Feature 1: Boilerplate Marketplace

### What It Is

A curated library of project starting templates that users select before the agent begins building. Each boilerplate defines the tech stack, project structure, pre-built infrastructure (auth, payments, database), and deployment configuration. The agent inherits this foundation and focuses on building the user's unique features instead of re-inventing scaffolding.

This is not a new concept -- the existing `_get_boilerplate_context()` function in `prompts.py` already injects boilerplate awareness into agent prompts. The marketplace expands this from a handful of built-in options to a full catalog with community contributions and premium tiers.

### Boilerplate Categories

**Web Frameworks:**
- React + Supabase (free, included with any build credit)
- Next.js + Prisma + PostgreSQL ($49)
- SvelteKit + Supabase ($49)
- Vue + Firebase ($49)

**Mobile:**
- Flutter + Supabase ($79, standard)
- React Native + Firebase ($79)
- Flutter + AWS Amplify ($99)

**Full-Stack Enterprise:**
- Next.js + AWS (Lambda, DynamoDB, Cognito) ($149)
- Rails + PostgreSQL + Redis ($149)

**Dual Platform:**
- React + Flutter + shared Supabase ($149)
- Next.js + React Native + shared API ($149)

**Specialized:**
- E-commerce (Shopify Hydrogen) ($99)
- SaaS (multi-tenant with Stripe billing) ($99)
- Marketplace (two-sided, escrow payments) ($149)
- Content/CMS (headless, MDX blog) ($79)

**Designer Series:** ($199-299)
- Professionally designed by contracted designers (the mentor)
- Include complete component libraries with pixel-perfect Figma-to-code
- Custom animations, micro-interactions, and polished empty states
- Each includes a promotional landing page template

### Boilerplate Directory Structure

```
boilerplates/
  react-supabase/
    boilerplate.yaml          # Metadata: name, description, tech stack, pricing
    template/                 # The actual project template files
      src/
      public/
      package.json
      tsconfig.json
      ...
    CLAUDE.md                 # Pre-configured agent instructions for this stack
    .autoforge/
      prompts/
        initializer_prompt.md # Custom initializer tuned for this stack
        coding_prompt.md      # Custom coding prompt with stack-specific patterns
      allowed_commands.yaml   # Stack-specific commands (flutter, swift, etc.)
    preview/
      screenshot-1.png        # Landing page screenshot
      screenshot-2.png        # Dashboard screenshot
      demo.mp4                # Optional 30-second demo video
    README.md                 # Setup instructions and what's included
```

### boilerplate.yaml Schema

```yaml
name: "React + Supabase Starter"
slug: react-supabase
version: "2.0.0"
author:
  name: "AutoForge Team"
  id: "autoforge"              # Author ID for revenue attribution
description: >
  Production-ready React 19 starter with Supabase auth, database,
  and real-time subscriptions. Includes responsive layout system,
  error boundaries, and environment configuration.
tier: free                     # free | premium | enterprise | designer
price_cents: 0                 # 0, 4900, 9900, 14900, 19900, 29900
category: web                  # web | mobile | full-stack | dual | specialized
tech_stack:
  frontend: react
  backend: supabase
  styling: tailwind
  auth: supabase-auth
  database: postgresql
  deployment: vercel
features_included:
  - "Authentication (email/password, OAuth)"
  - "Database schema with migrations"
  - "API layer with type safety"
  - "Responsive layout system"
  - "Error handling & loading states"
  - "Environment config (.env.example)"
compatible_styles: all         # "all" or list: ["minimalism", "flat-design"]
min_autoforge_version: "1.5.0"
created_at: "2026-01-15"
updated_at: "2026-02-01"
downloads: 0                   # Populated by marketplace API
rating: 0.0                    # Populated by user reviews
tags:
  - react
  - supabase
  - typescript
  - tailwind
```

### Pricing Tiers

| Tier | Price Range | What's Included | Margin |
|------|------------|----------------|--------|
| Free | $0 | Basic React + Supabase, included with any build credit | Loss leader |
| Premium | $49-99 | Next.js, Flutter, SvelteKit, specialized starters | ~90% |
| Enterprise | $149-199 | AWS enterprise, multi-tenant SaaS, dual platform | ~90% |
| Designer Series | $199-299 | Professionally designed by contracted designers | ~60% (designer fee) |

### Implementation

#### 1.1 Boilerplate Manager Service

New file: `server/services/boilerplate_manager.py`

```python
"""
Boilerplate Manager
===================

Manages the boilerplate catalog: listing, installing, and applying
boilerplates to new projects. Supports both built-in boilerplates
(shipped with AutoForge) and marketplace boilerplates (downloaded
to ~/.autoforge/boilerplates/).
"""

import logging
import shutil
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Built-in boilerplates ship with AutoForge
BUILTIN_DIR = Path(__file__).parent.parent.parent / "boilerplates"

# User-installed boilerplates from the marketplace
INSTALLED_DIR = Path.home() / ".autoforge" / "boilerplates"


def list_boilerplates() -> list[dict[str, Any]]:
    """List all available boilerplates (built-in + installed)."""
    ...

def get_boilerplate(slug: str) -> dict[str, Any] | None:
    """Get full boilerplate metadata by slug."""
    ...

def install_boilerplate(slug: str, archive_path: Path) -> bool:
    """Install a marketplace boilerplate from a downloaded archive."""
    ...

def apply_boilerplate(slug: str, project_dir: Path) -> bool:
    """Copy boilerplate template files into a new project directory."""
    ...

def uninstall_boilerplate(slug: str) -> bool:
    """Remove an installed marketplace boilerplate."""
    ...
```

The manager loads `boilerplate.yaml` from each boilerplate directory, validates the schema, and serves the catalog to the API. The `apply_boilerplate()` function copies the `template/` directory contents into the new project, along with the `.autoforge/` configuration and `CLAUDE.md`.

#### 1.2 Boilerplate REST API

New file: `server/routers/boilerplates.py`

```python
"""
Boilerplate Router
==================

REST API for browsing, selecting, and managing boilerplates.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/boilerplates", tags=["boilerplates"])

@router.get("/")
async def list_boilerplates(category: str | None = None, tier: str | None = None):
    """List all available boilerplates with optional filters."""
    ...

@router.get("/{slug}")
async def get_boilerplate(slug: str):
    """Get full boilerplate details including preview images."""
    ...

@router.post("/{slug}/install")
async def install_boilerplate(slug: str):
    """Download and install a marketplace boilerplate."""
    ...

@router.delete("/{slug}")
async def uninstall_boilerplate(slug: str):
    """Remove an installed boilerplate."""
    ...
```

#### 1.3 Boilerplate Selector UI Component

New file: `ui/src/components/BoilerplateSelector.tsx`

Shown during the project creation flow (in `NewProjectModal.tsx`), after the user names their project and selects a folder. The selector displays:

- Category filter tabs (All, Web, Mobile, Full-Stack, Dual, Specialized)
- Tier filter (All, Free, Premium, Enterprise, Designer)
- Grid of boilerplate cards showing: name, description, tech stack badges, price, download count, rating
- Preview drawer: clicking a card opens a side panel with screenshots, full description, tech stack details, and "Select This Boilerplate" button
- Search bar for finding boilerplates by name or tech stack keyword

The selected boilerplate slug is stored in the project creation payload and passed to the backend, which calls `apply_boilerplate()` before the initializer agent runs.

#### 1.4 Prompt Injection

The existing `_get_boilerplate_context()` in `prompts.py` already handles boilerplate context injection. Marketplace boilerplates work identically to built-in ones because they follow the same directory structure. The function reads the boilerplate metadata from `.autoforge/project_config.json` and generates a markdown section describing what infrastructure is pre-built, so the agent does not duplicate it.

No changes needed to `prompts.py` -- the existing fallback chain handles custom prompts from the boilerplate's `.autoforge/prompts/` directory automatically.

#### 1.5 CLI Integration

Add to `lib/cli.js`:

```
autoforge boilerplates list              # List all available boilerplates
autoforge boilerplates list --category web  # Filter by category
autoforge boilerplates install <slug>    # Install from marketplace
autoforge boilerplates remove <slug>     # Remove installed boilerplate
autoforge boilerplates info <slug>       # Show boilerplate details
```

#### 1.6 File Changes

| File | Change |
|------|--------|
| `server/services/boilerplate_manager.py` | NEW: Boilerplate CRUD, install, apply |
| `server/routers/boilerplates.py` | NEW: REST API for boilerplate catalog |
| `server/main.py` | Register boilerplates router |
| `ui/src/components/BoilerplateSelector.tsx` | NEW: Boilerplate selection UI |
| `ui/src/components/NewProjectModal.tsx` | Add boilerplate selection step |
| `ui/src/lib/api.ts` | Add boilerplate API client functions |
| `ui/src/lib/types.ts` | Add Boilerplate type definition |
| `ui/src/hooks/useProjects.ts` | Add useBoilerplates() React Query hook |
| `lib/cli.js` | Add `boilerplates` subcommand |
| `boilerplates/react-supabase/` | NEW: First built-in boilerplate |
| `security.py` | Add boilerplate-specific allowed commands if needed |

---

## Feature 2: Style Marketplace (Expanded)

### What It Is

Expansion of the existing 12 styles (defined in `server/services/style_manager.py`) into a full marketplace. The 12 built-in styles become the free tier. Premium styles, designer-crafted styles, and community-submitted styles are available for purchase.

The existing style infrastructure is already robust: `STYLE_REGISTRY` defines complete design systems with color tokens, typography, components, spacing, and Tailwind configuration. The marketplace extends this same data model to support third-party styles.

### Style Categories

**Free (built-in 12):**
Flat Design, Minimalism, Neumorphism, Glassmorphism, Skeuomorphism, Neubrutalism, Bauhaus, Claymorphism, Retro Futurism, Cyberpunk, Dark Mode Elegant, Warmer Shades.

**Premium ($9-29 each):**
- Industry-specific: Healthcare UI, FinTech Dashboard, EdTech Learning, Legal/Compliance
- Trending: Bento Grid, Aurora Gradients, Grain Texture, Organic Shapes
- Brand-inspired: Apple-esque, Stripe-esque, Linear-esque, Notion-esque

**Designer Series ($49-99 each):**
- Hand-crafted by professional designers
- Include complete component libraries (30+ component variants)
- Custom animations and micro-interaction specifications
- Full Figma/design file included
- Guaranteed compatibility with all boilerplates

**Custom Extracted:**
- User uploads a screenshot, AI extracts the style (from `screenshot-style-extractor-handoff.md`)
- Free to extract, stored locally in `~/.autoforge/styles/`
- Not purchasable -- this is a conversion funnel into the Style Extractor standalone product

### Style Marketplace Schema

The marketplace uses a remote Supabase database for the style catalog. Purchased styles are downloaded and cached locally in `~/.autoforge/styles/`.

```sql
-- Style catalog (central marketplace database)
create table marketplace_styles (
  id uuid primary key default gen_random_uuid(),
  slug text unique not null,
  name text not null,
  description text not null,
  philosophy text,
  category text not null check (category in ('core', 'vibe', 'industry', 'trending', 'brand', 'designer')),
  tier text not null check (tier in ('free', 'premium', 'designer')),
  price_cents integer not null default 0,
  author_id uuid references auth.users,
  author_name text not null,
  -- The complete style definition (same schema as STYLE_REGISTRY entries)
  style_guide jsonb not null,
  -- Do's and don'ts for agent prompt injection
  dos_and_donts jsonb,
  -- Compatibility metadata
  compatible_boilerplates text[] default '{}',
  accent_compatibility jsonb,        -- Which styles work as accents (from style-mixing-handoff)
  -- Preview assets
  preview_urls text[] default '{}',  -- Screenshot URLs (hosted on Supabase Storage)
  thumbnail_url text,                -- Grid card thumbnail
  -- Metrics
  downloads integer not null default 0,
  rating numeric(3,2) default 0.0,
  rating_count integer not null default 0,
  -- Lifecycle
  status text not null default 'draft' check (status in ('draft', 'review', 'published', 'rejected', 'archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_styles_category on marketplace_styles(category);
create index idx_styles_tier on marketplace_styles(tier);
create index idx_styles_status on marketplace_styles(status);
create index idx_styles_author on marketplace_styles(author_id);

-- Style purchases (tracks who bought what)
create table style_purchases (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users not null,
  style_id uuid references marketplace_styles not null,
  price_cents integer not null,
  stripe_payment_id text,
  purchased_at timestamptz not null default now(),
  unique(user_id, style_id)
);

create index idx_purchases_user on style_purchases(user_id);

-- Style reviews
create table style_reviews (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users not null,
  style_id uuid references marketplace_styles not null,
  rating integer not null check (rating between 1 and 5),
  review_text text,
  created_at timestamptz not null default now(),
  unique(user_id, style_id)
);
```

### Community Style Submissions

Designers can submit custom styles to the marketplace through a submission workflow:

1. Designer creates a style definition following the `STYLE_REGISTRY` schema (color tokens, typography, components, spacing, Tailwind config)
2. Designer uploads the style via a submission form in the UI with preview screenshots
3. AutoForge team reviews the submission: tests the style with 3 sample projects to verify agent output quality
4. If approved, the style is published to the marketplace
5. Revenue split: **70% designer / 30% AutoForge** (standard marketplace cut)

**Submission format:** The designer provides a JSON/YAML file matching the `style_guide` schema from `style_manager.py`, plus 4 preview screenshots (one per preview page from the style preview engine), and metadata (name, description, philosophy, category, do's and don'ts).

### Implementation

#### 2.1 Extended Style Manager

Modify `server/services/style_manager.py` to load styles from three sources:

```python
def get_all_styles() -> list[dict]:
    """
    Return the combined style catalog from all sources.

    Sources (in order):
    1. Built-in STYLE_REGISTRY (the 12 free styles)
    2. Locally installed marketplace styles (~/.autoforge/styles/)
    3. Custom extracted styles (from screenshot extractor)

    Returns a unified list with a 'source' field indicating origin.
    """
    ...
```

The built-in `STYLE_REGISTRY` remains the source of truth for free styles. Marketplace styles are stored as individual YAML files in `~/.autoforge/styles/{slug}/style.yaml` after purchase. The existing `get_style_guide_markdown()` function works with marketplace styles because the data schema is identical.

#### 2.2 Marketplace API Client

New file: `server/services/marketplace_client.py`

```python
"""
Marketplace Client
==================

HTTP client for communicating with the central AutoForge marketplace
API (hosted on Supabase). Handles browsing, purchasing, and downloading
marketplace assets (styles, boilerplates, plugins).
"""

import httpx

MARKETPLACE_API = "https://marketplace.autoforge.app/api/v1"

async def browse_styles(
    category: str | None = None,
    tier: str | None = None,
    sort: str = "popular",
    page: int = 1,
    per_page: int = 20,
) -> dict:
    """Browse the style marketplace catalog."""
    ...

async def purchase_style(style_id: str, payment_token: str) -> dict:
    """Complete a style purchase via Stripe checkout."""
    ...

async def download_style(style_id: str, auth_token: str) -> dict:
    """Download a purchased style's full definition."""
    ...

async def submit_style(style_data: dict, auth_token: str) -> dict:
    """Submit a community style for review."""
    ...
```

#### 2.3 Style Marketplace Router

New file: `server/routers/marketplace.py`

```python
"""
Marketplace Router
==================

REST API for browsing, purchasing, and managing marketplace assets.
Serves as a proxy between the UI and the central marketplace API.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])

@router.get("/styles")
async def browse_styles(category: str | None = None, tier: str | None = None):
    """Browse marketplace styles with filtering."""
    ...

@router.get("/styles/{slug}")
async def get_style_detail(slug: str):
    """Get full style details including previews and reviews."""
    ...

@router.post("/styles/{slug}/purchase")
async def purchase_style(slug: str, body: dict):
    """Initiate Stripe checkout for a style purchase."""
    ...

@router.get("/styles/purchased")
async def list_purchased_styles():
    """List all styles the current user has purchased."""
    ...

@router.post("/styles/submit")
async def submit_community_style(body: dict):
    """Submit a new style for marketplace review."""
    ...
```

#### 2.4 Style Gallery UI

New file: `ui/src/components/StyleMarketplace.tsx`

This replaces the simple style picker in `NewProjectModal.tsx` with a rich marketplace experience:

- **Grid view:** Cards with style name, thumbnail preview (using the fanned card stack from `style-preview-grid-handoff.md`), price badge, rating stars, download count
- **Filter bar:** Category tabs (All, Core, Vibe, Industry, Trending, Brand, Designer), tier filter, sort dropdown (Popular, Newest, Highest Rated)
- **Search:** Full-text search across style names and descriptions
- **Detail modal:** Clicking a card opens a detail view with full-screen preview (using the live preview engine from `style-preview-grid-handoff.md`), description, do's and don'ts, reviews, and purchase/select button
- **Purchased library:** Tab showing all styles the user owns, with quick-select buttons

The free built-in styles show a "Free" badge. Premium styles show the price with a "Buy" button that triggers Stripe checkout. Already-purchased styles show a "Owned" badge with a "Select" button.

#### 2.5 Payment Integration

Style purchases use Stripe Checkout:

1. User clicks "Buy" on a premium style
2. Frontend calls `POST /api/marketplace/styles/{slug}/purchase`
3. Backend creates a Stripe Checkout Session with the style price
4. User completes payment in Stripe-hosted checkout page
5. Stripe `checkout.session.completed` webhook fires
6. Backend records the purchase and makes the style available for download
7. The style definition is downloaded and cached to `~/.autoforge/styles/{slug}/`

For the self-hosted scenario (where there is no central user auth), purchases are tied to a machine-level license key stored in `~/.autoforge/license.key`. The marketplace API validates the license key on each download request.

#### 2.6 File Changes

| File | Change |
|------|--------|
| `server/services/style_manager.py` | Extend to load from `~/.autoforge/styles/` in addition to built-in registry |
| `server/services/marketplace_client.py` | NEW: HTTP client for central marketplace API |
| `server/routers/marketplace.py` | NEW: REST API proxy for marketplace operations |
| `server/main.py` | Register marketplace router |
| `ui/src/components/StyleMarketplace.tsx` | NEW: Marketplace-aware style gallery |
| `ui/src/components/NewProjectModal.tsx` | Replace style picker with StyleMarketplace component |
| `ui/src/lib/api.ts` | Add marketplace API client functions |
| `ui/src/lib/types.ts` | Add MarketplaceStyle, StylePurchase types |
| `ui/src/hooks/useMarketplace.ts` | NEW: React Query hooks for marketplace data |

---

## Feature 3: Plugin System

### What It Is

An extension system that allows developers to add custom capabilities to AutoForge agents. Plugins can inject additional MCP servers, modify agent prompts, add post-build hooks, and provide custom agent templates. This makes AutoForge extensible without modifying core code.

### Plugin Types

**MCP Server Plugins:**
Connect agents to external APIs and services. The plugin provides a custom MCP server that exposes tools to the agent. Examples:
- Stripe Integration: `stripe_create_product`, `stripe_create_checkout_session`, etc.
- Twilio SMS: `twilio_send_sms`, `twilio_verify_phone`, etc.
- SendGrid Email: `sendgrid_send_email`, `sendgrid_create_template`, etc.
- AWS S3: `s3_upload_file`, `s3_create_bucket`, etc.

**Prompt Plugins:**
Inject additional instructions into agent prompts without modifying core templates. Applied via the existing `_get_style_context()` injection pattern in `prompts.py`. Examples:
- "Always use Zustand for state management" (overrides default state management choices)
- "Follow HIPAA compliance patterns" (adds healthcare security requirements to every feature)
- "Use Server Components by default" (enforces Next.js RSC patterns)
- "Write tests in Vitest, not Jest" (changes testing framework preference)

**Post-Build Hook Plugins:**
Scripts that run after the agent finishes building a feature or the entire project. Examples:
- App Store uploader (builds and uploads iOS/Android binaries)
- Slack/Discord notifier (posts build status to team channel)
- Lighthouse runner (runs performance audit and saves report)
- Docker builder (creates and pushes Docker image)

**Initializer Template Plugins:**
Industry-specific feature templates that the initializer agent uses to create features. Instead of the user describing every feature, they install a template plugin that provides a pre-defined feature set. Examples:
- "HIPAA Healthcare" (50 security/compliance features for health apps)
- "E-commerce Standard" (40 features covering cart, checkout, inventory, shipping)
- "SaaS Essentials" (35 features for multi-tenant billing, team management, admin panel)

### Plugin Directory Structure

```
plugins/
  stripe-integration/
    plugin.yaml           # Metadata, dependencies, permissions
    mcp_server/
      server.py           # Custom MCP server (Python, using mcp library)
      requirements.txt    # Python dependencies for the MCP server
    prompts/
      coding_inject.md    # Text injected into coding agent prompts
      initializer_inject.md  # Text injected into initializer prompts (optional)
    hooks/
      post_feature.sh     # Runs after each feature is built (optional)
      post_project.sh     # Runs after all features are built (optional)
    README.md             # Usage documentation
```

### plugin.yaml Schema

```yaml
name: "Stripe Integration"
slug: stripe-integration
version: "1.0.0"
author:
  name: "AutoForge Community"
  id: "community-contributor-123"
description: "Adds Stripe payment processing tools to coding agents"
type: mcp_server            # mcp_server | prompt | hook | initializer_template
tier: free                  # free | premium
price_cents: 0              # 0 for free, 1900-4900 for premium

# Permissions the plugin requires (user must approve on install)
permissions:
  network_access:
    - "api.stripe.com"
    - "js.stripe.com"
  env_vars:
    - key: "STRIPE_SECRET_KEY"
      description: "Stripe secret API key for server-side operations"
      required: true
    - key: "STRIPE_PUBLISHABLE_KEY"
      description: "Stripe publishable key for client-side Stripe.js"
      required: true
  allowed_commands:
    - name: "stripe"
      description: "Stripe CLI for testing webhooks"

# Compatibility constraints
compatible_boilerplates: all    # "all" or list of slugs
compatible_styles: all
min_autoforge_version: "1.5.0"
min_python_version: "3.11"

# Plugin-specific configuration
config:
  mcp_server:
    entry: "mcp_server/server.py"
    transport: "stdio"            # stdio | sse
  prompt_inject:
    coding: "prompts/coding_inject.md"
    initializer: "prompts/initializer_inject.md"
  hooks:
    post_feature: "hooks/post_feature.sh"
    post_project: "hooks/post_project.sh"

tags:
  - payments
  - stripe
  - checkout
  - billing
```

### Security Model

Plugins are a significant attack surface. The security model enforces defense-in-depth:

**Permission Declaration:**
Plugins must declare all required permissions upfront in `plugin.yaml`. Users see and approve these permissions during installation, similar to mobile app permission prompts.

**Network Sandboxing:**
MCP server plugins can only access the network endpoints declared in `permissions.network_access`. The MCP server process runs with environment variables that restrict outbound connections. Undeclared network access is blocked.

**Environment Variable Isolation:**
Plugin env vars are scoped to the plugin's MCP server process. They are not visible to the main agent or other plugins. The user sets plugin env vars through the plugin settings UI, and they are stored encrypted in `~/.autoforge/plugins/{slug}/.env`.

**Command Allowlist Integration:**
Commands declared in `permissions.allowed_commands` are merged into the project's allowed command set (same mechanism as `.autoforge/allowed_commands.yaml`). They pass through the existing security validation in `security.py`, which means:
- Commands on the hardcoded blocklist (dd, sudo, shutdown, etc.) can NEVER be allowed by a plugin
- Organization-level blocked commands (`~/.autoforge/config.yaml`) override plugin requests
- The existing `validate_command()` function in `security.py` handles the merged allowlist

**Review Process:**
All marketplace plugins are reviewed by the AutoForge team before listing. The review checks:
1. No malicious code in the MCP server
2. Declared permissions match actual behavior (no undeclared network access)
3. Post-build hooks do not perform destructive operations
4. The plugin actually works with 3 sample projects

**Local-only plugins (unreviewed) are allowed** for development purposes. Users can place a plugin directory in `~/.autoforge/plugins/` manually and enable it per-project. These show a "Unreviewed" warning badge in the UI.

### Premium Plugins ($19-49)

| Plugin | Price | What It Does |
|--------|-------|-------------|
| AWS Deployment Suite | $49 | CloudFormation templates, S3 uploads, Lambda deployment, CDK patterns |
| Mobile Testing | $39 | BrowserStack/Sauce Labs integration for real device testing |
| i18n Automation | $29 | Auto-translate UI to 10 languages using DeepL/Google Translate API |
| SEO Optimization | $19 | Generate meta tags, sitemap, robots.txt, structured data, Open Graph |
| Analytics Integration | $19 | Plug-and-play analytics (Plausible, PostHog, Mixpanel) with event tracking |
| CI/CD Generator | $29 | Generate GitHub Actions, GitLab CI, or Vercel deployment configs |

### Implementation

#### 3.1 Plugin Manager Service

New file: `server/services/plugin_manager.py`

```python
"""
Plugin Manager
==============

Manages the plugin lifecycle: discovery, installation, validation,
configuration, and loading. Plugins extend agent capabilities by
providing custom MCP servers, prompt injections, and build hooks.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Installed plugins directory
PLUGINS_DIR = Path.home() / ".autoforge" / "plugins"


class PluginManager:
    """Manages plugin discovery, validation, and loading."""

    def list_plugins(self) -> list[dict[str, Any]]:
        """List all installed plugins with their status."""
        ...

    def get_plugin(self, slug: str) -> dict[str, Any] | None:
        """Get full plugin metadata and configuration."""
        ...

    def install_plugin(self, slug: str, archive_path: Path) -> bool:
        """Install a plugin from a downloaded archive."""
        ...

    def uninstall_plugin(self, slug: str) -> bool:
        """Remove an installed plugin and its configuration."""
        ...

    def validate_plugin(self, plugin_dir: Path) -> tuple[bool, list[str]]:
        """Validate a plugin's structure and permissions."""
        ...

    def get_mcp_server_configs(self, project_dir: Path) -> list[dict]:
        """
        Get MCP server configurations for all enabled plugins.

        Returns a list of MCP server configs that can be passed to
        ClaudeSDKClient alongside the built-in feature MCP server.
        """
        ...

    def get_prompt_injections(self, project_dir: Path, prompt_type: str) -> str:
        """
        Collect prompt injection text from all enabled plugins.

        Args:
            project_dir: The project directory
            prompt_type: "coding" or "initializer"

        Returns:
            Combined injection text from all enabled plugins.
        """
        ...

    def get_allowed_commands(self, project_dir: Path) -> list[dict]:
        """
        Collect allowed commands from all enabled plugins.

        Returns command entries compatible with the security.py allowlist.
        """
        ...

    def run_hook(self, project_dir: Path, hook_type: str, context: dict) -> bool:
        """
        Run post-build hooks from all enabled plugins.

        Args:
            hook_type: "post_feature" or "post_project"
            context: Hook context (feature_id, project_name, etc.)
        """
        ...
```

#### 3.2 Plugin Integration with Agent Client

The key integration point is `client.py`, where the `ClaudeSDKClient` is configured. When plugins are installed and enabled for a project:

1. **MCP Servers:** Plugin MCP servers are added to the list of MCP server configurations alongside the built-in feature MCP server. The `get_mcp_server_configs()` method returns configs in the same format expected by the Claude Agent SDK.

2. **Allowed Commands:** Plugin commands are merged into the allowed commands set via `get_allowed_commands()`. These are added to the `SecurityHooks` validator in `client.py` alongside the global allowlist and project-specific allowlist.

3. **Prompt Injection:** Plugin prompt injections are collected via `get_prompt_injections()` and appended to the agent prompt. This follows the same pattern as `_get_style_context()` and `_get_boilerplate_context()` in `prompts.py`.

4. **Environment Variables:** Plugin env vars are loaded from `~/.autoforge/plugins/{slug}/.env` and passed to the plugin's MCP server subprocess (not to the main agent process).

```python
# In client.py, when building the SDK client configuration:

from server.services.plugin_manager import PluginManager

plugin_mgr = PluginManager()

# Add plugin MCP servers
mcp_servers = [feature_mcp_config]  # existing
mcp_servers.extend(plugin_mgr.get_mcp_server_configs(project_dir))

# Merge plugin allowed commands
plugin_commands = plugin_mgr.get_allowed_commands(project_dir)
# ... merge into security hooks
```

```python
# In prompts.py, when building the agent prompt:

def _get_plugin_context(project_dir: Path | None) -> str:
    """Collect prompt injections from all enabled plugins."""
    if not project_dir:
        return ""
    from server.services.plugin_manager import PluginManager
    mgr = PluginManager()
    return mgr.get_prompt_injections(project_dir, "coding")
```

#### 3.3 Plugin Configuration UI

New file: `ui/src/components/PluginManager.tsx`

The plugin management UI is accessible from:
- The Settings modal (`,` keyboard shortcut) as a new "Plugins" tab
- The project creation flow as an optional "Add Plugins" step after boilerplate and style selection

**Plugin browser:**
- Grid of available plugins with name, description, type badge, price, and install button
- Installed plugins show an "Installed" badge with configure/remove options
- Category filter: All, MCP Servers, Prompts, Hooks, Templates

**Plugin configuration:**
- Each installed plugin has a settings panel for its required env vars
- Toggle to enable/disable per project
- Permission display showing what the plugin can access

**Permission approval flow:**
When installing a plugin that requires permissions:
```
┌─────────────────────────────────────────────┐
│  Install "Stripe Integration"?              │
│                                             │
│  This plugin requires:                      │
│                                             │
│  [Network] api.stripe.com, js.stripe.com    │
│  [Env Var] STRIPE_SECRET_KEY (required)     │
│  [Env Var] STRIPE_PUBLISHABLE_KEY (required)│
│  [Command] stripe (Stripe CLI)              │
│                                             │
│  [Cancel]           [Approve & Install]     │
└─────────────────────────────────────────────┘
```

#### 3.4 Plugin REST API

New file: `server/routers/plugins.py`

```python
"""
Plugin Router
=============

REST API for managing plugins: browsing, installing, configuring,
and removing plugins.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/plugins", tags=["plugins"])

@router.get("/")
async def list_plugins():
    """List all installed plugins with status."""
    ...

@router.get("/marketplace")
async def browse_marketplace_plugins(type: str | None = None):
    """Browse available plugins from the marketplace."""
    ...

@router.post("/{slug}/install")
async def install_plugin(slug: str):
    """Install a plugin (requires permission approval)."""
    ...

@router.delete("/{slug}")
async def uninstall_plugin(slug: str):
    """Remove an installed plugin."""
    ...

@router.get("/{slug}/config")
async def get_plugin_config(slug: str):
    """Get plugin configuration (env vars, enabled projects)."""
    ...

@router.put("/{slug}/config")
async def update_plugin_config(slug: str, body: dict):
    """Update plugin configuration."""
    ...

@router.post("/{slug}/enable/{project_name}")
async def enable_plugin_for_project(slug: str, project_name: str):
    """Enable a plugin for a specific project."""
    ...

@router.post("/{slug}/disable/{project_name}")
async def disable_plugin_for_project(slug: str, project_name: str):
    """Disable a plugin for a specific project."""
    ...
```

#### 3.5 CLI Integration

Add to `lib/cli.js`:

```
autoforge plugins list                    # List installed plugins
autoforge plugins install <slug>          # Install from marketplace
autoforge plugins remove <slug>           # Remove plugin
autoforge plugins config <slug>           # Configure plugin env vars
autoforge plugins enable <slug> <project> # Enable for a project
autoforge plugins disable <slug> <project># Disable for a project
```

#### 3.6 File Changes

| File | Change |
|------|--------|
| `server/services/plugin_manager.py` | NEW: Plugin lifecycle management |
| `server/routers/plugins.py` | NEW: Plugin REST API |
| `server/main.py` | Register plugins router |
| `client.py` | Load plugin MCP servers and merge allowed commands |
| `prompts.py` | Add `_get_plugin_context()` for prompt injection |
| `security.py` | Validate plugin-declared commands against blocklist |
| `ui/src/components/PluginManager.tsx` | NEW: Plugin browser and configuration UI |
| `ui/src/components/SettingsModal.tsx` | Add Plugins tab |
| `ui/src/components/NewProjectModal.tsx` | Add optional "Add Plugins" step |
| `ui/src/lib/api.ts` | Add plugin API client functions |
| `ui/src/lib/types.ts` | Add Plugin, PluginConfig types |
| `ui/src/hooks/usePlugins.ts` | NEW: React Query hooks for plugin data |
| `lib/cli.js` | Add `plugins` subcommand |

---

## Feature 4: Central Marketplace API

### What It Is

A shared backend service that hosts the marketplace catalog, handles payments, tracks purchases, and manages the submission/review workflow. This is a separate deployment from the AutoForge desktop/server application -- it runs on Supabase and serves all AutoForge instances.

### Architecture

```
AutoForge Instance                  Central Marketplace
(user's machine)                    (Supabase + Vercel)

┌──────────────┐                    ┌──────────────────┐
│ UI           │◄──── REST ────────►│ Marketplace API  │
│ (React)      │                    │ (Edge Functions)  │
├──────────────┤                    ├──────────────────┤
│ Server       │◄──── REST ────────►│ Supabase DB      │
│ (FastAPI)    │                    │ (PostgreSQL)      │
├──────────────┤                    ├──────────────────┤
│ Local Cache  │                    │ Supabase Storage  │
│ (~/.autoforge│                    │ (Asset files)     │
│  /styles/    │                    ├──────────────────┤
│  /plugins/   │                    │ Stripe            │
│  /boilerplates/                   │ (Payments)        │
│  )           │                    └──────────────────┘
└──────────────┘
```

**The local AutoForge instance acts as a client.** It browses the catalog, initiates purchases, and downloads assets. All purchased assets are cached locally so they work offline after download.

**Authentication:** Users authenticate with the marketplace using a license key or Supabase Auth (email + password). The license key is stored in `~/.autoforge/marketplace_auth.json`. For the MVP, a simple API key tied to the user's email is sufficient.

### Marketplace API Endpoints

All endpoints are Supabase Edge Functions:

```
GET  /api/v1/catalog/styles          # Browse styles
GET  /api/v1/catalog/boilerplates    # Browse boilerplates
GET  /api/v1/catalog/plugins         # Browse plugins
GET  /api/v1/catalog/{type}/{slug}   # Get asset details

POST /api/v1/checkout                # Create Stripe Checkout session
POST /api/v1/checkout/webhook        # Stripe webhook handler

GET  /api/v1/purchases               # List user's purchases
GET  /api/v1/downloads/{purchase_id} # Download purchased asset

POST /api/v1/submissions             # Submit community asset
GET  /api/v1/submissions/mine        # List user's submissions
GET  /api/v1/submissions/{id}/status # Check submission review status

POST /api/v1/reviews                 # Post a review/rating
GET  /api/v1/reviews/{asset_id}      # Get reviews for an asset
```

### Payment Flow

1. User clicks "Buy" on a premium asset in the AutoForge UI
2. AutoForge server calls `POST /api/v1/checkout` with the asset slug and user auth token
3. Marketplace creates a Stripe Checkout Session and returns the session URL
4. UI opens the Stripe Checkout page in a new window/iframe
5. User completes payment
6. Stripe fires `checkout.session.completed` webhook to `/api/v1/checkout/webhook`
7. Webhook handler records the purchase in `style_purchases` / `boilerplate_purchases` / `plugin_purchases`
8. AutoForge polls `GET /api/v1/purchases` until the purchase appears
9. AutoForge downloads the asset via `GET /api/v1/downloads/{purchase_id}`
10. Asset is cached locally in `~/.autoforge/{type}/{slug}/`

### Community Revenue Sharing

For community-submitted assets (styles and plugins), the revenue split is tracked at the database level:

```sql
create table payouts (
  id uuid primary key default gen_random_uuid(),
  author_id uuid references auth.users not null,
  amount_cents integer not null,
  currency text not null default 'usd',
  status text not null default 'pending'
    check (status in ('pending', 'processing', 'paid', 'failed')),
  stripe_transfer_id text,
  period_start date not null,
  period_end date not null,
  line_items jsonb not null default '[]',  -- [{asset_id, sales_count, gross, net}]
  created_at timestamptz not null default now(),
  paid_at timestamptz
);
```

Payouts are processed monthly via Stripe Connect:
- Minimum payout threshold: $25
- Revenue split: 70% creator / 30% platform
- Creators sign up for Stripe Connect during the submission process

### Implementation Priority for Marketplace API

This is a separate project (likely its own repository), but the AutoForge client-side integration is what matters for this handoff.

Phase 1: Read-only catalog (browse styles/boilerplates/plugins from a static JSON hosted on CDN)
Phase 2: Payment integration (Stripe Checkout for individual purchases)
Phase 3: User accounts and purchase tracking
Phase 4: Community submissions and review workflow
Phase 5: Revenue sharing and payouts

---

## Feature 5: Marketplace Authentication and Licensing

### What It Is

A lightweight authentication system that connects a local AutoForge installation to the central marketplace. Users do not need an account to use AutoForge itself -- accounts are only needed for marketplace purchases and community submissions.

### Auth Flow

1. User clicks "Sign In to Marketplace" in Settings or when attempting a purchase
2. A Supabase Auth login form appears (email/password or Google OAuth)
3. On successful auth, the JWT is stored in `~/.autoforge/marketplace_auth.json`
4. Subsequent marketplace API calls include the JWT in the Authorization header
5. The JWT refreshes automatically; the user stays signed in indefinitely

### License Key Alternative

For users who do not want to create an account, a license key model is available:
- User purchases a license key from the AutoForge website
- The key is entered in Settings and stored in `~/.autoforge/marketplace_auth.json`
- The key is validated against the marketplace API on each request
- The key grants access to all purchased assets

### Local Auth Storage

```json
// ~/.autoforge/marketplace_auth.json
{
  "method": "supabase",           // "supabase" | "license_key"
  "jwt": "eyJ...",                // Supabase JWT (auto-refreshed)
  "refresh_token": "xxx",
  "user_id": "uuid",
  "email": "user@example.com",
  "expires_at": "2026-03-15T00:00:00Z"
}
```

This file is excluded from any backup/export operations and is not version-controlled. If the user reinstalls AutoForge, they sign in again and their purchases are restored from the marketplace database.

### File Changes

| File | Change |
|------|--------|
| `server/services/marketplace_client.py` | Add auth header injection and token refresh |
| `server/routers/marketplace.py` | Add `/api/marketplace/auth/*` endpoints |
| `ui/src/components/MarketplaceAuth.tsx` | NEW: Login/signup form for marketplace |
| `ui/src/components/SettingsModal.tsx` | Add marketplace account section |

---

## Revenue Analysis

### Per-Asset Revenue

| Item | Price Range | COGS | Margin | Volume Assumption |
|------|------------|------|--------|-------------------|
| Free boilerplate | $0 | $0 | -- | Loss leader, included with builds |
| Premium boilerplate | $49-99 | ~$0 | ~90% | 20-50 sales/month at scale |
| Enterprise boilerplate | $149-199 | ~$0 | ~90% | 5-15 sales/month |
| Designer boilerplate | $199-299 | ~$80-120 (designer fee) | ~60% | 10-30 sales/month |
| Premium style | $9-29 | ~$0 | ~90% | 50-200 sales/month |
| Designer style | $49-99 | Revenue share (30/70) | 30% platform | 20-50 sales/month |
| Community style | Revenue share (30/70) | $0 | 30% platform | Variable |
| Premium plugin | $19-49 | ~$0 | ~90% | 30-100 sales/month |
| Community plugin | Revenue share (30/70) | $0 | 30% platform | Variable |

### Monthly Revenue Projections

Assumes 500 active users with the following purchase rates:

| Revenue Stream | Avg Price | Purchase Rate | Monthly Revenue |
|---------------|-----------|---------------|-----------------|
| Build credits (core) | $219 | 2.0 builds/user | $219,000 |
| Premium boilerplates | $69 | 15% of builds | $10,350 |
| Premium styles | $19 | 25% of builds | $4,750 |
| Designer styles | $69 | 5% of builds | $3,450 |
| Premium plugins | $29 | 10% of builds | $2,900 |
| **Marketplace subtotal** | | | **$21,450** |
| **Total with builds** | | | **$240,450** |

The marketplace adds approximately 10% on top of core build revenue. As the asset catalog grows and community contributions increase, this percentage rises because:
- More assets mean more purchase opportunities per build
- Community assets generate revenue with zero COGS (30% platform fee only)
- Designer series becomes a recurring revenue source as new designers join

### Break-Even Analysis

**Upfront investment:** Building the marketplace infrastructure (central API, payment integration, submission workflow, UI components) requires approximately 4-6 weeks of development effort.

**Monthly operating cost:** Supabase Pro ($25/mo) + Stripe fees (2.9% + $0.30/transaction) + CDN for asset storage (~$20/mo). Total: ~$50/mo fixed + per-transaction fees.

**Break-even:** At just 30 marketplace transactions per month averaging $40 each ($1,200 gross), the marketplace covers its operating costs. This is achievable within the first month after launch if the initial catalog has 5+ premium boilerplates and 10+ premium styles.

---

## Implementation Priority

Build these in this order:

### Phase 1: Boilerplate Marketplace (Highest Impact, Lowest Complexity)

**Why first:** Boilerplates have the highest per-unit price ($49-299) and the most immediate impact on agent output quality. The existing `_get_boilerplate_context()` in `prompts.py` means the backend integration is partially built. The UI needs a selection component, and the backend needs a catalog manager.

**What to build:**
1. `server/services/boilerplate_manager.py` -- local catalog manager
2. `server/routers/boilerplates.py` -- REST API
3. `ui/src/components/BoilerplateSelector.tsx` -- selection UI
4. 3-5 built-in boilerplates (React + Supabase free, Next.js + Prisma premium, Flutter + Supabase premium)
5. Integration into `NewProjectModal.tsx` project creation flow

**Timeline:** 1-2 weeks
**Revenue impact:** Immediate -- premium boilerplates can be sold on day one

### Phase 2: Style Marketplace (Expand Existing Infrastructure)

**Why second:** The 12 built-in styles already work and are proven. Expanding to a marketplace means adding loading from `~/.autoforge/styles/`, a gallery UI, and payment integration. The style data model does not need to change.

**What to build:**
1. Extend `style_manager.py` to load marketplace styles
2. `server/services/marketplace_client.py` -- central API client
3. `server/routers/marketplace.py` -- marketplace proxy API
4. `ui/src/components/StyleMarketplace.tsx` -- marketplace gallery
5. 5-10 premium styles (industry and trending categories)
6. Stripe Checkout integration for individual purchases

**Timeline:** 2-3 weeks
**Revenue impact:** Moderate -- style prices are lower but purchase volume is higher

### Phase 3: Plugin System (Most Complex, Highest Long-Term Value)

**Why third:** Plugins require the most architectural work (dynamic MCP server loading, security sandboxing, prompt injection from plugins). The payoff is long-term extensibility and a developer ecosystem.

**What to build:**
1. `server/services/plugin_manager.py` -- plugin lifecycle
2. Integration with `client.py` for dynamic MCP server loading
3. Integration with `prompts.py` for prompt injection
4. Integration with `security.py` for command allowlist merging
5. `server/routers/plugins.py` -- REST API
6. `ui/src/components/PluginManager.tsx` -- plugin browser and config UI
7. 2-3 built-in plugins (Stripe Integration free, SEO Optimization premium, i18n premium)

**Timeline:** 3-4 weeks
**Revenue impact:** Grows over time as the plugin catalog expands

### Phase 4: Central Marketplace API (Enables Everything)

**Why fourth:** The first three phases can launch with local-only catalogs (built-in boilerplates, styles, and plugins shipped with AutoForge). The central marketplace API enables community submissions, cross-instance purchases, and the full marketplace flywheel.

**What to build:**
1. Supabase project setup (database, auth, storage, edge functions)
2. Catalog API endpoints
3. Stripe Checkout and webhook handling
4. Community submission and review workflow
5. Revenue sharing and payout system
6. Marketplace auth integration in AutoForge client

**Timeline:** 4-6 weeks
**Revenue impact:** Unlocks community contributions and recurring marketplace revenue

### Phase 5: Designer Program (Revenue Accelerator)

**Why last:** This is a business process, not a technical feature. Once the marketplace infrastructure is built, onboard the mentor (professional designer) to create the first "Designer Series" boilerplates and styles. These are the highest-margin, highest-price items in the catalog.

**What to do:**
1. Define the Designer Series specification (deliverables, quality bar, pricing)
2. Contract the mentor to create 3 Designer Series boilerplates and 5 Designer Series styles
3. Create a landing page showcasing the Designer Series
4. Set up Stripe Connect for designer payouts

**Timeline:** 2-4 weeks (overlaps with Phase 4)
**Revenue impact:** High -- Designer Series items at $199-299 with professional marketing

---

## Key Decisions Before Building

### 1. Local-First vs Cloud-First Marketplace

**Recommendation: Local-first.** Ship Phases 1-3 with assets bundled in the AutoForge distribution or downloadable as static files. No central API needed initially. This gets the marketplace UX into users' hands immediately. Add the central API (Phase 4) when the catalog needs community contributions and cross-instance purchase tracking.

### 2. Payment Processor

**Recommendation: Stripe.** Already used in the self-deploy VPS handoff. Stripe Checkout handles the payment page, and Stripe Connect handles creator payouts. No need to build custom payment UI.

### 3. Asset Distribution Format

**Recommendation: Compressed archives (.tar.gz) hosted on Supabase Storage.** Each asset (boilerplate, style, plugin) is packaged as a compressed archive with a manifest file. The AutoForge client downloads, verifies integrity (SHA-256 checksum in the catalog), and extracts to the local cache.

### 4. Offline Support

**Recommendation: Full offline support after initial download.** All purchased assets are cached locally in `~/.autoforge/`. Users can create projects using purchased boilerplates, styles, and plugins without an internet connection. The marketplace browser requires connectivity, but everything else works offline.

### 5. Versioning and Updates

**Recommendation: Semantic versioning with manual updates.** Each asset has a version in its YAML metadata. The marketplace client checks for updates periodically and shows an "Update Available" badge. Users manually trigger updates to avoid breaking existing projects that depend on a specific version.

---

## Relationship to Existing Handoffs

This handoff builds on and references several existing handoff documents:

- **`style-preview-grid-handoff.md`** -- The style marketplace gallery reuses the live preview engine for showing style previews. The fanned card stack and full-screen preview from that handoff become the style marketplace's browsing experience.

- **`style-mixing-handoff.md`** -- Marketplace styles must include `accent_compatibility` data so they work with the base+accent mixing system. The `compatible_boilerplates` field in the style schema ensures marketplace styles are tested with specific boilerplate stacks.

- **`screenshot-style-extractor-handoff.md`** -- The "Extract from Screenshot" flow produces custom styles that live alongside marketplace styles in `~/.autoforge/styles/`. The extractor is a free conversion funnel into the style marketplace.

- **`self-deploy-vps-handoff.md`** -- The VPS deployment system shares the Stripe payment infrastructure. Users on hosted instances get marketplace access bundled with their subscription tier.

- **`qa-pipeline-handoff.md`** -- Premium boilerplates can ship with pre-configured QA templates (test scaffolds, review agent configurations) that integrate with the QA pipeline.

- **`idea-code-integration-handoff.md`** -- The mentor's "Idea Code" methodology for generating style guides is the foundation for the Designer Series quality bar. Designer Series assets must pass the Idea Code style guide generator as a validation step.

---

## Notes for Implementation

- The `_get_boilerplate_context()` function in `prompts.py` already reads boilerplate metadata from `.autoforge/project_config.json`. Marketplace boilerplates use the same schema, so no changes to the prompt injection system are needed.
- The `STYLE_REGISTRY` list in `style_manager.py` should remain the canonical source for the 12 free styles. Marketplace styles extend this list at runtime, not replace it.
- Plugin MCP servers must follow the same transport protocol (stdio) as the built-in feature MCP server in `mcp_server/feature_mcp.py`. Using a consistent transport simplifies the client configuration in `client.py`.
- The security model in `security.py` uses a hierarchical allowlist (hardcoded blocklist > org blocklist > org allowlist > global allowlist > project allowlist). Plugins insert at a new level between global and project: hardcoded blocklist > org blocklist > org allowlist > global allowlist > **plugin allowlist** > project allowlist.
- All marketplace assets should include a `min_autoforge_version` field. The client checks this before installation and warns the user if their AutoForge version is too old.
- Consider adding a `--marketplace-offline` flag or `AUTOFORGE_MARKETPLACE_OFFLINE=1` env var for air-gapped environments that cannot reach the central marketplace API.
