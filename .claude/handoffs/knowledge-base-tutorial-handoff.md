# Knowledge Base & Tutorial Video Generation System - Handoff Document

## Overview

AutoForge builds complete apps autonomously. But every app it ships today has zero documentation and zero training materials. No getting-started guide. No feature walkthroughs. No FAQ. No API reference. No onboarding tour. The end user receives a working app and a blank stare.

90% of SaaS apps have terrible onboarding. This is the gap: a new agent type that auto-generates a full knowledge base, tutorial video scripts, and an embedded in-app help system for every AutoForge-built project. Every app ships with professional onboarding out of the box.

**This is a key differentiator feature** -- a clear competitive advantage against Bolt, Lovable, and every other AI code generator that ships code with no docs.

---

## Feature 1: Knowledge Base Generator Agent

### What It Does

A new agent type (`--agent-type knowledge-base`) that reads the completed app, navigates every feature via Playwright, takes screenshots at each step, and produces a complete, organized help center in markdown format.

This agent runs AFTER the QA pipeline completes (or after all features are passing in non-QA mode). It is a post-build agent -- it does not modify application code. It only reads the codebase, interacts with the running app, and writes documentation files.

### What It Generates

#### 1. Getting Started Guide

- Account creation walkthrough (if the app has auth)
- First-time setup steps
- Quick tour of main features with annotated screenshots
- Screenshots of each step (taken via Playwright)

The agent identifies the app's entry point, navigates the signup/login flow, and documents every screen the user encounters in their first session.

#### 2. Feature Documentation (One Article Per Feature)

For each feature in the `features.db`:

- **What it does** -- plain-language description derived from the feature spec
- **How to use it** -- step-by-step instructions with Playwright screenshots at each step
- **Tips and best practices** -- inferred from the implementation (e.g., "Use keyboard shortcuts for faster navigation")
- **Common issues and solutions** -- generated from error handling code and edge cases in the implementation
- **Related features** -- derived from the dependency graph via `feature_get_graph`

#### 3. FAQ Section

Generated from common patterns detected in the feature set:

- Auth features present? Generate: "How do I reset my password?", "How do I change my email?", "How do I enable two-factor authentication?"
- CRUD features present? Generate: "How do I export my data?", "How do I bulk delete items?", "Is there a way to undo changes?"
- Settings features present? Generate: "How do I change my notification preferences?", "How do I switch themes?", "How do I delete my account?"
- Payment features present? Generate: "How do I update my billing info?", "How do I cancel my subscription?", "Where can I see my invoices?"

The FAQ is customized based on what the app actually does -- not a generic template.

#### 4. API Documentation (If Applicable)

The agent scans the codebase for API routes and generates:

- **Endpoint reference** -- method, path, parameters, request/response schemas
- **Authentication guide** -- how to obtain and use API tokens
- **Code examples** -- curl, JavaScript (fetch), and Python (requests) for each endpoint
- **Rate limits and error codes** -- extracted from middleware and error handling code

API detection strategy:
1. Scan for Express/Fastify route definitions (`app.get`, `app.post`, `router.get`, etc.)
2. Scan for Next.js API routes (`pages/api/` or `app/api/`)
3. Scan for FastAPI/Flask endpoints (`@app.route`, `@router.get`, etc.)
4. Extract request/response types from TypeScript interfaces or Pydantic models

#### 5. Troubleshooting Guide

- Common error messages and their fixes (extracted from error boundaries and catch blocks)
- Browser compatibility notes (based on the tech stack)
- Performance tips (based on the app's architecture)
- Contact/support information template (placeholder for the project owner to fill in)

### Output Format

```
docs/knowledge-base/
  index.md                    # Table of contents with links to all sections
  getting-started.md          # Quick start guide with screenshots
  features/
    001-user-registration.md  # One file per feature, numbered by priority
    002-dashboard.md
    003-project-management.md
    ...
  faq.md                      # Frequently asked questions
  api/
    reference.md              # API endpoint reference
    authentication.md         # Auth guide with code examples
    examples.md               # curl, JavaScript, Python samples
  troubleshooting.md          # Common issues and fixes
  screenshots/                # Playwright-captured images
    getting-started/
      step-01-landing-page.png
      step-02-signup-form.png
      step-03-dashboard.png
    features/
      001-registration-step-1.png
      001-registration-step-2.png
      002-dashboard-overview.png
      002-dashboard-sidebar.png
    ...
```

All screenshots use a consistent viewport size (1280x800) and are taken with Playwright's built-in screenshot capability. The agent names screenshots with the feature ID and step number for traceability.

### How It Works

1. Agent calls `feature_get_summary` to get the full feature list with descriptions
2. Agent calls `feature_get_graph` to understand feature relationships and dependencies
3. Agent reads the app spec (`app_spec.txt`) for high-level project context
4. For each feature (in priority order):
   a. Read the feature's description and steps from the database
   b. Navigate to the relevant page(s) via Playwright
   c. Execute the feature's workflow step by step
   d. Take a screenshot at each meaningful state change
   e. Write the documentation article with embedded screenshot references
5. Scan the codebase for API routes and generate API documentation
6. Generate FAQ based on detected feature patterns
7. Generate the troubleshooting guide
8. Write the `index.md` table of contents linking everything together
9. Git commit all docs: `git add docs/knowledge-base/ && git commit -m "Add knowledge base documentation"`

### Implementation

#### 1.1 New Agent Type: `knowledge-base`

Add to `autonomous_agent_demo.py` CLI args:

```python
choices=["initializer", "coding", "testing", "knowledge-base"]
```

New CLI flags:

```python
parser.add_argument("--kb-tier", type=str, default="basic",
                    choices=["basic", "full", "premium"],
                    help="Knowledge base tier: basic (docs only), full (docs + scripts), premium (docs + scripts + in-app help)")
```

#### 1.2 New Prompt Template

Create `.claude/templates/knowledge_base_prompt.template.md`:

```markdown
## YOUR ROLE - KNOWLEDGE BASE GENERATOR AGENT

You are a **documentation agent** responsible for creating a complete, professional
knowledge base for a finished application. The app has been built and tested -- your
job is to document it so end users can learn how to use every feature.

You do NOT modify application code. You only READ the codebase, INTERACT with the
running app via Playwright, TAKE screenshots, and WRITE documentation files.

## PREPARATION

### Step 1: Understand the App

1. Call `feature_get_summary` to get all features with descriptions
2. Call `feature_get_graph` to understand feature relationships
3. Read the app spec at `app_spec.txt` for high-level context
4. Read the project's `package.json` or equivalent to understand the tech stack
5. Identify the app's entry URL (usually `http://localhost:3000` or similar)

### Step 2: Navigate and Map the App

Before writing any documentation:

1. Launch the app via Playwright: `browser_navigate` to the entry URL
2. Take a screenshot of the landing page
3. Identify all navigation elements (sidebar, navbar, menus)
4. Build a mental map of all pages and their URLs
5. Identify authentication flows (login, signup, password reset)

## DOCUMENTATION GENERATION

### Step 3: Getting Started Guide

Write `docs/knowledge-base/getting-started.md`:

1. Navigate to the app's entry point
2. Screenshot the landing page
3. Walk through the signup/login flow step by step
4. Screenshot each step
5. Navigate to the main dashboard/home page after auth
6. Screenshot the main view
7. Write clear, numbered instructions referencing each screenshot

Format for screenshot references:
```
![Step 1: Landing page](screenshots/getting-started/step-01-landing-page.png)
```

### Step 4: Feature Documentation

For EACH feature from `feature_get_summary` (process in priority order):

1. Call `feature_get_by_id` to get full details
2. Navigate to the feature's primary page
3. Execute the feature's workflow:
   - Fill forms with realistic sample data
   - Click buttons and links
   - Screenshot each state change
4. Write `docs/knowledge-base/features/{NNN}-{slug}.md` with:
   - Title and description
   - Step-by-step instructions with screenshots
   - Tips section (inferred from the UI)
   - Common issues (inferred from error states)
   - Related features (from the dependency graph)

### Step 5: FAQ Generation

Write `docs/knowledge-base/faq.md`:

Analyze the feature set and generate relevant FAQs:
- Auth features → password reset, email change, account deletion
- CRUD features → data export, bulk operations, undo
- Settings features → preferences, themes, notifications
- Payment features → billing, subscriptions, invoices

Each FAQ entry: question, concise answer, link to the relevant feature doc.

### Step 6: API Documentation (If Applicable)

Scan the codebase for API routes:

```bash
# Express/Fastify
grep -r "app\.\(get\|post\|put\|patch\|delete\)" --include="*.ts" --include="*.js" src/
grep -r "router\.\(get\|post\|put\|patch\|delete\)" --include="*.ts" --include="*.js" src/

# Next.js API routes
ls -la pages/api/ app/api/ 2>/dev/null

# FastAPI/Flask
grep -r "@\(app\|router\)\.\(get\|post\|put\|patch\|delete\)" --include="*.py" .
```

For each endpoint found, write:
- Method and path
- Description (inferred from function name and comments)
- Parameters (from function signatures and validation)
- Example request (curl, JavaScript fetch, Python requests)
- Example response (from TypeScript types or Pydantic models)

Output files:
- `docs/knowledge-base/api/reference.md` - All endpoints
- `docs/knowledge-base/api/authentication.md` - Auth flow
- `docs/knowledge-base/api/examples.md` - Code samples

### Step 7: Troubleshooting Guide

Write `docs/knowledge-base/troubleshooting.md`:

1. Scan for error boundary components and catch blocks
2. Identify common error messages in the codebase
3. For each error pattern, write:
   - The error message the user would see
   - What causes it
   - How to fix it
4. Add browser compatibility notes based on the tech stack
5. Add a support contact template section

### Step 8: Table of Contents

Write `docs/knowledge-base/index.md`:

- Link to getting started guide
- List all feature docs with brief descriptions
- Link to FAQ
- Link to API docs (if generated)
- Link to troubleshooting

### Step 9: Commit

```bash
git add docs/knowledge-base/
git commit -m "Add knowledge base documentation with screenshots"
```

## SCREENSHOT CONVENTIONS

- Viewport: 1280x800
- Format: PNG
- Naming: `{section}/{feature-id}-{step-description}.png`
- Take screenshots AFTER the page has fully loaded (wait for network idle)
- Capture the full page, not just the viewport, for long pages
- Use `browser_screenshot` after each significant action

## MCP TOOLS AVAILABLE

### Feature Management
- `feature_get_stats` - Progress overview
- `feature_get_by_id` - Get feature details
- `feature_get_summary` - Get all features with descriptions
- `feature_get_graph` - Get dependency graph

### Browser Automation (Playwright)
All standard Playwright tools for navigating and screenshotting.

## IMPORTANT REMINDERS

- You are a DOCUMENTATION agent -- do NOT modify application code
- Every feature must have its own documentation article
- Every step must have a screenshot
- Use realistic sample data in screenshots (not "test123" or "asdf")
- Write for non-technical end users -- no jargon, no assumptions
- The knowledge base must be self-contained and navigable
- Commit everything when done
```

#### 1.3 Client Configuration for Knowledge Base Agent

In `client.py`, add knowledge-base agent type handling:

```python
KNOWLEDGE_BASE_FEATURE_TOOLS = [
    "mcp__features__feature_get_stats",
    "mcp__features__feature_get_by_id",
    "mcp__features__feature_get_summary",
    "mcp__features__feature_get_graph",
    "mcp__features__feature_get_ready",
]
```

The knowledge base agent gets:
- Feature MCP tools (read-only -- no mark_passing, no mark_failing, no claiming)
- Built-in tools (Read, Write, Edit, Bash, Grep, Glob)
- Playwright MCP server (for navigating the app and taking screenshots)
- NO feature mutation tools (this agent does not change feature status)

#### 1.4 Prompt Loading in `prompts.py`

Add a new function:

```python
def get_knowledge_base_prompt(
    project_dir: Path | None = None,
    kb_tier: str = "basic",
) -> str:
    """Load the knowledge base agent prompt.

    Args:
        project_dir: Optional project directory for project-specific prompts
        kb_tier: Tier level - "basic" (docs only), "full" (docs + scripts),
                 "premium" (docs + scripts + in-app help)

    Returns:
        The knowledge base prompt with tier-specific instructions.
    """
    prompt = load_prompt("knowledge_base_prompt", project_dir)

    # Inject tier-specific sections
    if kb_tier in ("full", "premium"):
        prompt += "\n\n" + _get_tutorial_script_section()
    if kb_tier == "premium":
        prompt += "\n\n" + _get_in_app_help_section()

    return prompt
```

#### 1.5 Orchestrator Integration

In `parallel_orchestrator.py`, add knowledge-base agent spawning after all features pass:

```python
def _check_knowledge_base_ready(self):
    """Spawn knowledge-base agent after all features are passing."""
    if self._kb_completed or self._kb_running:
        return
    if not self.kb_enabled:
        return

    stats = get_feature_stats(self.db_path)
    if stats['passing'] == stats['total'] and stats['total'] > 0:
        print("\n=== ALL FEATURES PASSING ===")
        print("=== SPAWNING KNOWLEDGE BASE AGENT ===\n")
        self._spawn_knowledge_base_agent()
```

The knowledge base agent runs in parallel with the QA agent if both are enabled. They do not conflict because:
- The knowledge base agent only reads code and writes to `docs/`
- The QA agent reads code and may fix issues in `src/`
- No file overlap, no feature status conflicts

#### 1.6 Turn Budget

The knowledge base agent needs a generous turn budget because it must navigate every feature:

| Project Size | Features | Estimated Turns | Estimated Cost (Max Sub) |
|---|---|---|---|
| Small (10 features) | 10 | 40-60 turns | ~$0 (included in Max) |
| Medium (30 features) | 30 | 75-100 turns | ~$0 (included in Max) |
| Large (100 features) | 100 | 150-200 turns | ~$0 (included in Max) |

```python
# In the knowledge-base agent subprocess command
if agent_type == "knowledge-base":
    max_turns = 200  # Generous budget for screenshotting every feature
```

#### 1.7 Deployable Formats

The output is static markdown with relative image paths. This works out of the box with:

- **GitBook** -- push the `docs/knowledge-base/` directory; GitBook renders markdown natively
- **Docusaurus** -- drop into `docs/` with a `sidebars.js` config
- **ReadTheDocs** -- add a `mkdocs.yml` config pointing to the directory
- **Notion** -- import markdown files (screenshots need manual upload)
- **In-app help route** -- serve from the app itself at `/help` with a markdown renderer (see Feature 3)

A future enhancement could auto-generate platform-specific config files (e.g., `mkdocs.yml`, `docusaurus.config.js`) based on user selection.

#### 1.8 File Changes

| File | Change |
|---|---|
| `.claude/templates/knowledge_base_prompt.template.md` | NEW -- knowledge base agent prompt template |
| `autonomous_agent_demo.py` | Add `knowledge-base` to agent-type choices, add `--kb-tier` flag |
| `client.py` | Add knowledge-base agent tool config (read-only feature tools + Playwright) |
| `prompts.py` | Add `get_knowledge_base_prompt()` with tier-aware section injection |
| `parallel_orchestrator.py` | Add `_check_knowledge_base_ready()`, `_spawn_knowledge_base_agent()` |
| `server/routers/agent.py` | Support `knowledge-base` agent type in start/stop endpoints |

---

## Feature 2: Tutorial Video Script Generator

### What It Does

Generates complete tutorial video scripts that are ready for AI voice narration and automated screen recording. Each script includes:

- Narration text (what the voice says)
- Screen actions (what the viewer sees)
- Exact Playwright commands (for automated recording in a future pipeline)

The scripts alone are the deliverable for now. They are professional tutorials that just need a voice. A future automation tool can execute the Playwright commands to capture screen recordings, feed the narrator text to an AI voice API (ElevenLabs, OpenAI TTS), sync audio to video, and output finished MP4s.

### Script Structure Per Video

```markdown
# Tutorial: How to Create Your First Project

## Video Metadata
- Duration: ~45 seconds
- Type: Feature walkthrough
- Audience: New users
- Prerequisites: Account created

## Script

[SCREEN: Show the dashboard page at http://localhost:3000/dashboard]
NARRATOR: "Welcome to ProjectHub. Let's create your first project."

[WAIT: 1.5s]

[ACTION: Click the 'New Project' button in the top-right corner]
NARRATOR: "Click the New Project button to get started."

[SCREEN: Show the project creation form]
[WAIT: 1s]
NARRATOR: "Give your project a name and select a category."

[ACTION: Type "My First Project" into the name field]
[ACTION: Select "Personal" from the category dropdown]
NARRATOR: "Fill in the details, then click Create."

[ACTION: Click the 'Create' button]
[WAIT: 2s]
[SCREEN: Show the new project page with success message]
NARRATOR: "That's it! Your project is ready to go. You can now add tasks, invite collaborators, and start tracking progress."

## Playwright Commands (for automated recording)
1. browser_navigate('http://localhost:3000/dashboard')
2. browser_wait(1500)
3. browser_click('button:has-text("New Project")')
4. browser_wait(1000)
5. browser_fill('[name="projectName"]', 'My First Project')
6. browser_select_option('[name="category"]', 'Personal')
7. browser_click('button:has-text("Create")')
8. browser_wait(2000)
9. browser_screenshot()
```

### Video Categories

#### Quick Start (1 video, ~2-3 minutes)

A single overview video covering:
- What the app does (30 seconds)
- Signing up and logging in (30 seconds)
- Quick tour of the main sections (60 seconds)
- One simple task end-to-end (30 seconds)

This is the first video new users see. It should give them confidence that the app is easy to use.

#### Feature Walkthroughs (1 per major feature, ~30-60 seconds each)

One short video per feature, focused on the happy path:
- Navigate to the feature
- Perform the primary action
- Show the result
- Mention one related feature

Not every feature needs a video. The agent selects "major" features by filtering for features with priority <= 3 and that have a UI component (not background jobs or API-only features).

#### Admin Guide (if applicable, ~2-3 minutes)

If the app has admin/settings features:
- How to configure the app
- User management (if applicable)
- System settings and preferences

#### Tips and Tricks (1 video, ~1-2 minutes)

Power user features discovered during documentation:
- Keyboard shortcuts
- Bulk operations
- Hidden features (e.g., right-click menus, drag and drop)
- Search/filter tips

### Output Format

```
docs/tutorials/
  scripts/
    00-quick-start.md           # Overview video script
    01-user-registration.md     # Feature walkthrough
    02-dashboard-overview.md    # Feature walkthrough
    03-creating-projects.md     # Feature walkthrough
    ...
    admin-guide.md              # Admin/settings walkthrough
    tips-and-tricks.md          # Power user tips
  README.md                     # Index of all scripts with metadata
```

### Implementation

The tutorial scripts are generated by the same knowledge-base agent as an additional pass after the documentation is complete. The agent already has the app mapped and screenshots taken, so generating scripts is a matter of converting the step-by-step documentation into narrated video format.

#### 2.1 Prompt Section (Injected for "full" and "premium" Tiers)

This section is appended to the knowledge base prompt when `kb_tier` is `"full"` or `"premium"`:

```markdown
## TUTORIAL VIDEO SCRIPT GENERATION

After completing the knowledge base documentation, generate tutorial video scripts.

### Script Format

Each script is a markdown file in `docs/tutorials/scripts/` with three sections:

1. **Video Metadata**: duration estimate, type, audience, prerequisites
2. **Script**: interleaved SCREEN/ACTION/NARRATOR directives
3. **Playwright Commands**: exact commands for automated recording

### Directives

- `[SCREEN: description]` -- What the viewer sees on screen
- `[ACTION: description]` -- A user action (click, type, scroll)
- `[WAIT: duration]` -- Pause for the viewer to absorb what they see
- `NARRATOR: "text"` -- What the voiceover says

### Writing Style for Narration

- Conversational, friendly, and concise
- Use "you" and "your" (second person)
- Avoid jargon -- explain terms if unavoidable
- Keep sentences short (under 15 words)
- One concept per sentence
- Match the pacing: ~150 words per minute of narration

### Video Selection

Not every feature needs a video. Generate scripts for:
1. Quick Start (always -- this is the first video)
2. Features with priority <= 3 (major features)
3. Features with UI components (skip API-only and background features)
4. Admin/settings guide if admin features exist
5. Tips and Tricks (always -- compile from interesting UI patterns)

### Playwright Commands

Include exact Playwright MCP tool calls for each action in the script.
These commands will be used by a future automation tool to:
1. Execute the commands and capture screen recordings
2. Feed NARRATOR text to an AI voice API
3. Sync audio to screen recordings
4. Output finished video files

The commands must be independently executable -- they should not depend on
state from a previous script (each video is self-contained).

### Commit

```bash
git add docs/tutorials/
git commit -m "Add tutorial video scripts"
```
```

#### 2.2 Turn Budget Addition

Tutorial script generation adds ~20-30 turns on top of the knowledge base agent's budget. The agent already has all the navigation context and screenshots from the documentation pass, so scripts are faster to generate than the initial docs.

```python
# Adjust turn budget when tutorial scripts are requested
if agent_type == "knowledge-base" and kb_tier in ("full", "premium"):
    max_turns = 250  # 200 base + 50 for scripts
```

#### 2.3 File Changes

| File | Change |
|---|---|
| `.claude/templates/knowledge_base_prompt.template.md` | Contains base prompt; tutorial section injected by `prompts.py` |
| `prompts.py` | `_get_tutorial_script_section()` returns the tutorial prompt markdown |

---

## Feature 3: In-App Help System

### What It Does

Instead of (or in addition to) external docs, this tier embeds help directly into the built app. The knowledge base agent generates a structured JSON file and a small React component library that the app can consume to display contextual help.

This is the premium tier -- it adds the most value because users never have to leave the app to find help.

### Components Generated

#### 1. Contextual Tooltips

Help icons (?) next to complex UI elements that show explanatory tooltips on hover or click. The agent identifies which elements need tooltips by looking for:
- Form inputs with validation rules
- Buttons that trigger destructive actions
- Settings with non-obvious consequences
- Features that have prerequisites

#### 2. Searchable Help Sidebar

A panel that slides in from the right edge of the screen, containing:
- Search input that filters all help content
- Table of contents organized by feature
- Article content rendered from the knowledge base markdown
- Screenshot thumbnails that expand on click

Triggered by a floating help button (?) in the bottom-right corner, or by a keyboard shortcut (`?`).

#### 3. Onboarding Tour

A first-time user walkthrough that highlights key UI elements in sequence:
- Step 1: "This is your dashboard" (highlight the main content area)
- Step 2: "Create new items here" (highlight the primary CTA)
- Step 3: "Navigate between sections" (highlight the sidebar)
- Step 4: "Access your settings here" (highlight the settings link)
- Step 5: "Need help? Click here anytime" (highlight the help button)

Uses a tour library pattern (similar to Shepherd.js or React Joyride) but implemented as a lightweight custom component to avoid adding heavy dependencies to the generated app.

#### 4. Keyboard Shortcuts Help

A modal triggered by pressing `?` that shows:
- All keyboard shortcuts available in the app
- Organized by section (navigation, actions, etc.)
- Detected by scanning the codebase for `addEventListener('keydown')` patterns

### help-content.json Structure

The knowledge base agent generates this file at `src/help-content.json` (or `public/help-content.json` depending on the framework):

```json
{
  "app_name": "ProjectHub",
  "version": "1.0",
  "generated_at": "2026-02-13T12:00:00Z",
  "pages": {
    "/dashboard": {
      "title": "Dashboard",
      "description": "Your central hub for all projects and recent activity.",
      "article_ref": "docs/knowledge-base/features/002-dashboard.md",
      "tooltips": [
        {
          "selector": "[data-help='new-project']",
          "text": "Create a new project from scratch or use a template.",
          "position": "bottom"
        },
        {
          "selector": "[data-help='search']",
          "text": "Search across all your projects, tasks, and notes.",
          "position": "bottom"
        },
        {
          "selector": "[data-help='notifications']",
          "text": "View recent notifications and activity from your team.",
          "position": "left"
        }
      ],
      "tour_steps": [
        {
          "selector": ".main-content",
          "title": "Your Dashboard",
          "text": "This is where you'll see all your projects and recent activity.",
          "position": "center"
        },
        {
          "selector": "[data-help='new-project']",
          "title": "Create a Project",
          "text": "Click here to start a new project. You can choose from templates or start blank.",
          "position": "bottom"
        },
        {
          "selector": "nav.sidebar",
          "title": "Navigation",
          "text": "Use the sidebar to switch between different sections of the app.",
          "position": "right"
        }
      ]
    },
    "/projects/:id": {
      "title": "Project Details",
      "description": "View and manage a specific project.",
      "article_ref": "docs/knowledge-base/features/003-project-management.md",
      "tooltips": [
        {
          "selector": "[data-help='project-settings']",
          "text": "Configure project-specific settings like visibility and permissions.",
          "position": "bottom"
        }
      ],
      "tour_steps": []
    }
  },
  "keyboard_shortcuts": [
    { "keys": ["?"], "description": "Show keyboard shortcuts", "scope": "global" },
    { "keys": ["n"], "description": "Create new item", "scope": "dashboard" },
    { "keys": ["s"], "description": "Save changes", "scope": "editor" },
    { "keys": ["Esc"], "description": "Close modal or panel", "scope": "global" }
  ],
  "faq": [
    {
      "question": "How do I reset my password?",
      "answer": "Go to Settings > Account > Change Password. You'll need to enter your current password first.",
      "article_ref": "docs/knowledge-base/faq.md#password-reset"
    }
  ]
}
```

### React Component Library

The agent generates a small, self-contained component library at `src/components/help/`:

#### `HelpProvider.tsx`

Context provider that loads `help-content.json` and provides it to all child components. Tracks which page the user is on (from the router) and provides page-specific help content.

```tsx
// Minimal interface -- the agent generates the full implementation
interface HelpContextValue {
  currentPage: PageHelp | null;
  searchResults: SearchResult[];
  search: (query: string) => void;
  showSidebar: boolean;
  toggleSidebar: () => void;
  tourComplete: boolean;
  startTour: () => void;
}
```

#### `HelpTooltip.tsx`

A tooltip component that reads from the help context and attaches to matching selectors. Uses a portal to render above all other content. Appears on hover with a 300ms delay, or on click for touch devices.

#### `HelpSidebar.tsx`

A slide-in panel with:
- Search input at the top
- Filtered article list below
- Article content rendered with a lightweight markdown parser (the agent uses `marked` or `react-markdown` if already in the project's dependencies, otherwise raw HTML)
- Close button and `Esc` key support

#### `OnboardingTour.tsx`

A step-by-step tour component that:
- Shows a spotlight on the current step's element (dims the rest of the page)
- Displays a tooltip with title, description, and navigation buttons (Next, Skip, Finish)
- Persists completion state to localStorage so the tour only runs once
- Can be restarted from the help sidebar

#### `HelpButton.tsx`

A floating action button in the bottom-right corner. Click to open the help sidebar. Includes a subtle pulse animation on first visit (before the user has interacted with help).

### Integration into the App

The agent adds the help system to the app's root layout:

```tsx
// In the app's root layout (App.tsx or layout.tsx)
import { HelpProvider } from './components/help/HelpProvider';
import { HelpButton } from './components/help/HelpButton';
import { HelpSidebar } from './components/help/HelpSidebar';
import { OnboardingTour } from './components/help/OnboardingTour';

function App() {
  return (
    <HelpProvider>
      {/* ... existing app content ... */}
      <HelpSidebar />
      <OnboardingTour />
      <HelpButton />
    </HelpProvider>
  );
}
```

### Implementation

#### 3.1 Prompt Section (Injected for "premium" Tier Only)

This section is appended to the knowledge base prompt when `kb_tier` is `"premium"`:

```markdown
## IN-APP HELP SYSTEM GENERATION

After completing the knowledge base and tutorial scripts, generate an embedded
help system for the application.

### Step 1: Generate help-content.json

Create `src/help-content.json` (or `public/help-content.json` for non-React apps):

For EACH page in the app:
1. Navigate to the page via Playwright
2. Use `browser_snapshot` to get the accessibility tree
3. Identify interactive elements that would benefit from tooltips
4. Identify the logical tour order for first-time users
5. Record CSS selectors for each element

For keyboard shortcuts:
1. Search the codebase for `keydown`, `keyup`, `onKeyDown`, `useHotkeys` patterns
2. Extract the key bindings and their descriptions
3. Organize by scope (global, page-specific)

### Step 2: Generate Help Components

Create `src/components/help/` with these files:
- `HelpProvider.tsx` - Context provider
- `HelpTooltip.tsx` - Tooltip component
- `HelpSidebar.tsx` - Searchable help panel
- `OnboardingTour.tsx` - First-time user tour
- `HelpButton.tsx` - Floating help button
- `index.ts` - Barrel export

### Step 3: Integrate into App Root

Modify the app's root layout to include the help components.
Wrap the app content in `<HelpProvider>` and add `<HelpSidebar>`,
`<OnboardingTour>`, and `<HelpButton>` as siblings.

### Step 4: Verify

1. Navigate the app and verify tooltips appear on hover
2. Open the help sidebar and verify search works
3. Trigger the onboarding tour and verify each step highlights correctly
4. Press `?` and verify the keyboard shortcuts modal appears
5. Screenshot each state for verification

### Component Requirements

- Zero external dependencies beyond what the app already has
- Use the app's existing styling system (Tailwind, CSS modules, etc.)
- Components must be tree-shakeable (each component is independently importable)
- Tour state persisted to localStorage
- Sidebar is responsive (full-width on mobile, 400px panel on desktop)
- All components use the app's existing color scheme
- Accessible: proper ARIA attributes, keyboard navigation, focus management

### Commit

```bash
git add src/components/help/ src/help-content.json
git commit -m "Add in-app help system with tooltips, sidebar, and onboarding tour"
```
```

#### 3.2 Turn Budget Addition

The in-app help system adds ~15-20 turns for generating the JSON and components, plus ~10 turns for integration and verification.

```python
# Adjust turn budget for premium tier
if agent_type == "knowledge-base" and kb_tier == "premium":
    max_turns = 280  # 200 base + 50 scripts + 30 in-app help
```

#### 3.3 File Changes

| File | Change |
|---|---|
| `prompts.py` | `_get_in_app_help_section()` returns the in-app help prompt markdown |

---

## Server API Changes

### New Endpoints

#### Start Knowledge Base Agent

```
POST /api/projects/{project_name}/knowledge-base
Content-Type: application/json

{
  "tier": "basic" | "full" | "premium"
}
```

Response:
```json
{
  "status": "started",
  "agent_type": "knowledge-base",
  "tier": "full",
  "estimated_turns": 150
}
```

#### Get Knowledge Base Status

```
GET /api/projects/{project_name}/knowledge-base/status
```

Response:
```json
{
  "status": "running" | "completed" | "failed" | "not_started",
  "tier": "full",
  "progress": {
    "features_documented": 15,
    "features_total": 30,
    "screenshots_taken": 42,
    "scripts_generated": 8
  },
  "output_path": "docs/knowledge-base/",
  "completed_at": "2026-02-13T14:30:00Z"
}
```

### Router Changes

Add knowledge-base endpoints to `server/routers/agent.py` (or a new `server/routers/knowledge_base.py` if the agent router is already large):

```python
@router.post("/projects/{project_name}/knowledge-base")
async def start_knowledge_base(project_name: str, request: KBStartRequest):
    """Start the knowledge base generator agent."""
    ...

@router.get("/projects/{project_name}/knowledge-base/status")
async def get_knowledge_base_status(project_name: str):
    """Get knowledge base generation status."""
    ...
```

---

## UI Changes

### Settings Modal Addition

Add a "Knowledge Base" section to `SettingsModal.tsx`:

```
Knowledge Base
  [ ] Auto-generate after build completes
  Tier: [Basic ▼]  (dropdown: Basic, Full, Premium)
```

When auto-generate is enabled, the orchestrator spawns the knowledge-base agent automatically after all features pass. When disabled, the user can manually trigger it from the project dashboard.

### Project Dashboard Addition

Add a "Docs" tab or section to the project view:

```
[Kanban] [Graph] [Terminal] [Docs]
```

The Docs tab shows:
- Knowledge base generation status (if running: progress bar with feature count)
- Link to browse the generated docs (opens `docs/knowledge-base/index.md` in a markdown viewer)
- Download button (zip the docs directory)
- "Regenerate" button to re-run the knowledge base agent

### Agent Mission Control

Add a new mascot for the knowledge base agent:
- **Name:** "Sage" (book/scroll mascot) -- documenting everything
- **States:** Reading (analyzing features) / Writing (generating docs) / Screenshotting (capturing UI)
- Displayed alongside coding, testing, review, and QA agents

### File Changes

| File | Change |
|---|---|
| `ui/src/components/SettingsModal.tsx` | Add knowledge base tier selection and auto-generate toggle |
| `ui/src/components/AgentMissionControl.tsx` | Add "Sage" mascot for knowledge-base agent |
| `ui/src/lib/types.ts` | Add knowledge-base agent type, KB status types |
| `ui/src/lib/api.ts` | Add KB start and status API calls |
| `ui/src/hooks/useProjects.ts` | Add React Query hooks for KB endpoints |
| `server/routers/agent.py` | Add KB start/status endpoints (or new router) |
| `server/services/process_manager.py` | Support knowledge-base agent process lifecycle |

---

## Complete File Changes Summary

| File | Change | Feature |
|---|---|---|
| `.claude/templates/knowledge_base_prompt.template.md` | NEW -- knowledge base agent prompt template | 1 |
| `autonomous_agent_demo.py` | Add `knowledge-base` to agent-type choices, add `--kb-tier` flag | 1 |
| `client.py` | Add knowledge-base agent tool config (read-only features + Playwright) | 1 |
| `prompts.py` | Add `get_knowledge_base_prompt()`, `_get_tutorial_script_section()`, `_get_in_app_help_section()` | 1, 2, 3 |
| `parallel_orchestrator.py` | Add `_check_knowledge_base_ready()`, `_spawn_knowledge_base_agent()`, `--kb-tier` flag | 1 |
| `server/routers/agent.py` | Support `knowledge-base` agent type, add KB start/status endpoints | 1 |
| `server/services/process_manager.py` | Support knowledge-base agent process lifecycle | 1 |
| `ui/src/components/SettingsModal.tsx` | Add knowledge base toggle and tier selection | UI |
| `ui/src/components/AgentMissionControl.tsx` | Add "Sage" mascot for knowledge-base agent | UI |
| `ui/src/lib/types.ts` | Add knowledge-base agent type and KB status types | UI |
| `ui/src/lib/api.ts` | Add KB API calls | UI |
| `ui/src/hooks/useProjects.ts` | Add React Query hooks for KB endpoints | UI |

---

## Implementation Priority

Build these in order:

1. **Feature 1: Knowledge Base Generator** -- The core deliverable. A new agent type, a new prompt template, and orchestrator wiring. This produces markdown docs with screenshots that work anywhere. Most value, most straightforward.

2. **Feature 2: Tutorial Video Scripts** -- Natural extension of the knowledge base. The agent already has all the navigation context from documenting features. Adding script generation is a prompt addition, not new infrastructure. ~20-30 extra turns.

3. **Feature 3: In-App Help System** -- The premium tier. Adds the most perceived value (contextual help embedded directly in the app) but requires the agent to modify application code (adding components and modifying the root layout). More complex, higher risk, higher reward.

---

## Edge Cases and Failure Modes

### App Requires Authentication

Most apps need login before the agent can document features. The knowledge base agent should:
1. Check if the app has a login page
2. Look for test/seed credentials in the codebase (`.env`, `seed.ts`, `fixtures/`)
3. If no credentials found, create a test account via the signup flow
4. Store the session for reuse across all documentation runs

### App Has No Running Dev Server

The agent needs the app running to take screenshots. If the dev server is not running:
1. Start the dev server using the project's `npm run dev` or equivalent
2. Wait for the health check to pass
3. Proceed with documentation
4. The dev server lifecycle is already managed by `server/services/dev_server_manager.py`

### Feature Has No UI

Some features are backend-only (API endpoints, background jobs, database migrations). For these:
- Skip screenshot-based documentation
- Generate text-only documentation from the feature description and code
- For API endpoints, generate the API reference entry
- Mark as "no-screenshot" in the output

### Screenshots Fail

Playwright screenshots can fail due to timing, animations, or dynamic content. The agent should:
1. Retry once with a longer wait time
2. If still failing, take a viewport screenshot instead of a full-page screenshot
3. Log the failure but continue with other features
4. Note missing screenshots in the documentation ("Screenshot unavailable")

### Large Projects (100+ Features)

For very large projects, the agent may hit the turn budget before documenting every feature. Strategy:
1. Document features in priority order (highest priority first)
2. If approaching the turn limit, generate summary docs for remaining features (title + description only, no screenshots)
3. Mark undocumented features in `index.md` with "Coming soon"
4. A second run can pick up where the first left off

---

## Future Enhancements

### Automated Video Rendering Pipeline

Build a tool that takes the tutorial scripts and produces finished MP4 videos:
1. Execute Playwright commands and record the screen (using `ffmpeg` or Playwright's video recording)
2. Feed NARRATOR text to OpenAI TTS or ElevenLabs
3. Sync audio to video with timestamps from WAIT directives
4. Add title cards, transitions, and branding
5. Output MP4 files to `docs/tutorials/videos/`

This turns the "Full" tier into a higher-value offering with actual rendered videos.

### Multi-Language Documentation

Generate the knowledge base in multiple languages:
1. Agent writes docs in English first
2. A second pass translates each file using Claude
3. Output to `docs/knowledge-base/{locale}/` (e.g., `es/`, `fr/`, `ja/`)
4. Add language switcher to the in-app help sidebar

### Interactive Documentation

Generate interactive tutorials that run in the browser:
1. Embed code sandboxes (CodeSandbox, StackBlitz) for API examples
2. Add "Try it yourself" sections with pre-filled forms
3. Generate Storybook stories for each component documented

### Documentation Freshness

When features are updated after initial documentation:
1. Track which features have been modified since docs were generated
2. Offer a "Refresh docs" option that re-runs only for changed features
3. Diff the new screenshots against old ones to highlight visual changes

---

## Competitive Positioning

### What Other AI Code Generators Ship

- **Bolt:** Code only. No docs. No screenshots. No help system.
- **Lovable:** Code only. Minimal README at best.
- **Cursor:** Code with inline comments. No user-facing docs.
- **v0 (Vercel):** Code snippets. No docs for the generated app.

### What AutoForge Ships (With This Feature)

- Complete, working application
- Full knowledge base with screenshots of every feature
- Professional tutorial video scripts
- Embedded in-app help system with tooltips and onboarding tour
- API documentation with code examples in 3 languages
- FAQ and troubleshooting guide

**The tagline:** "AutoForge doesn't just build your app. It ships it with a help center, tutorial scripts, and in-app onboarding -- ready for real users on day one."

---

## Notes for Implementation

- The knowledge-base agent runs on the Max subscription -- zero additional API cost beyond the subscription
- It spawns AFTER all features pass, in parallel with the QA agent (no conflicts)
- The agent only reads application code -- it writes exclusively to `docs/` and (for premium tier) `src/components/help/`
- The turn budget scales with project size: small projects (~60 turns), large projects (~200 turns)
- The tiered system (Basic/Full/Premium) provides increasing levels of documentation output
- All output is git-committed by the agent, so the docs are version-controlled alongside the code
- The `--kb-tier` flag can be set via CLI, API, or the UI settings modal
- Consider adding a `--kb-only` flag that skips the build and just generates docs for an already-built project
