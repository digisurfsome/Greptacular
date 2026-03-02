// ==UserScript==
// @name         Phase Forge - Build Orchestrator & Prompt Injector
// @namespace    https://github.com/digisurfsome/Greptacular
// @version      2.0
// @description  Multi-phase build orchestrator with prompt injection for Claude/ChatGPT/Gemini
// @author       AutoForge
// @match        https://claude.ai/*
// @match        https://chatgpt.com/*
// @match        https://chat.openai.com/*
// @match        https://gemini.google.com/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  // ================================================================
  // SECTION: PROMPT DEFINITIONS (20 default prompts)
  // ================================================================

  const PROMPTS = [
    {
      id: 1,
      title: 'Martin Style Prompt',
      prompt: `**Role:** You are an expert Design System Architect and Senior Frontend Engineer. You specialize in "Atomic Design" principles and creating abstract, reusable component libraries.

**Objective:** I will provide an image. Your task is to ignore the specific content, text, and business context of the image. Instead, extract the underlying Visual Design Language (the "Visual DNA"). I need a generic, reusable style guide that I can apply to any type of application, not just the one shown in the image.

**Strict Constraints (Read Carefully):**
1. Do not mention specific text found in the image (e.g., do not say "The 'Revenue' title uses 16px"; say "Section Headers use 16px").
2. Do not mention specific business logic (e.g., do not say "The 'Sales Card' has a shadow"; say "The 'Primary Data Container' has a shadow").
3. Generalize all findings into reusable tokens and classes.

**Output Requirements:** Please generate a Technical Design System Report in Markdown covering:

#### 1. Abstract Color Tokens (Global Variables)
Extract the palette but name them by function, not content:
- **Brand/Primary:** (The main interaction color)
- **Surface/Backgrounds:** (Main background, Secondary background/sidebar, Card background)
- **Text Hierarchy:** (Primary, Secondary/Muted, Tertiary)
- **Borders/Dividers:** (Line colors)
- **Status Colors:** (If present: Success, Error, Warning)

#### 2. Global Typography System
- Identify the font family (or closest Google Font)
- Define the abstract hierarchy:
  - **Display/Hero:** (Largest text styles)
  - **Headings:** (H1, H2, H3 equivalents)
  - **Body:** (Regular and Bold variants)
  - **Microcopy:** (Labels, captions, small text)
- Detail: Include specific weights (400, 500, 600, 700) and approximate line-heights

#### 3. Universal Component Patterns (Molecules)
- **Surfaces/Cards:** Analyze the container style. What is the border radius? Is there a border stroke? Is there a box shadow? (Provide CSS values)
- **Interactables (Buttons/Links):** Analyze the primary and secondary button styles (padding, radius, color, hover effects)
- **Form Inputs:** Analyze the style of text fields (background color, border color, corner radius)
- **Iconography:** Describe the visual style of icons used (e.g., "Thin stroke, 1.5px, rounded corners" or "Solid filled, sharp edges")

#### 4. Layout & Spacing Physics
- **Spacing Scale:** Determine the base unit of the design (e.g., 4px, 8px, or 10px)
- **Density:** Is the design "Cozy" (lots of whitespace/padding) or "Compact" (data-dense)?
- **Radius Consistency:** What is the rule for rounded corners? (e.g., "4px for small elements, 12px for containers")

#### 5. Tailwind CSS Theme Extension
Based on the abstract analysis, write a tailwind.config.js theme object. Do not include content-specific names.`
    },
    {
      id: 2,
      title: 'Martin App Idea Prompt',
      prompt: `**Role:** You are a product strategist and startup advisor who helps people turn vague app ideas into clear, buildable MVPs.

**Objective:** I'm going to describe an app idea. It might be rough, incomplete, or just a general concept. Your job is to help me clarify it and output a structured specification I can use to build it.

**Your Process:**
1. If my idea is unclear, ask me 2-3 quick clarifying questions first
2. Once you understand, output the structured format below
3. Keep it MVP-focused — only essential features, nothing fancy

**Output Format (Follow Exactly):**

## SECTION 1: APP IDENTITY

**App Name:** [Suggest a short, memorable name]

**One-Line Description:** [What it does in one sentence — be specific]

**Target User:** [Who is this for? Be specific about their situation]

**Core Problem It Solves:** [What pain point does this eliminate?]

---

## SECTION 2: FEATURES

**Core Features (3-5 max):**
1. [Feature 1 — specific and actionable]
2. [Feature 2]
3. [Feature 3]
4. [Feature 4 — if needed]
5. [Feature 5 — if needed]

**What Users Can Do:**
- [Main action 1 — e.g., "Create and save recipes"]
- [Main action 2 — e.g., "Organize recipes into collections"]
- [Main action 3 — e.g., "Search their saved recipes"]

**Rules:**
- Maximum 5 features — this is an MVP
- Each feature should be one clear thing, not multiple things bundled
- "What Users Can Do" should be plain English actions, not technical jargon
- Don't include features like "user authentication" or "responsive design" — those are assumed
- Focus on what makes this app unique and useful`
    },
    {
      id: 3,
      title: 'Martin Build Prompt Rules',
      prompt: `Critical Rules (25 Rules)
Technical (1-7)
NO database calls in components - use service layer only
NO unprotected routes for authenticated features
NO inline styles - Tailwind only
NO any types - define TypeScript interfaces
ALL database writes include createdAt/updatedAt timestamps
ALL user data scoped to the authenticated user
Wrap app in ErrorBoundary component
UI/UX (8-25)
NO alert(), confirm(), prompt() - use Modal/ConfirmModal/Toast
ALL destructive actions require ConfirmModal
ALL async operations show loading state (Skeleton for lists, Spinner in buttons)
ALL empty lists use EmptyState component with icon and CTA
ALL success/error actions show Toast feedback
ALL saved items have Detail View (read-only) separate from Edit View
ALL forms validate before submission
ALL buttons show loading state during async actions
ALL avatars have fallback for failed images
ALL pages set document title via usePageTitle hook
ALL forms autofocus first input
ALL lists have search/filter when > 5 items expected
ALL error states have retry action
ALL dates formatted as relative time (not raw timestamps)
ALL long text truncated with ellipsis
ALL detail pages have back navigation
Use Lucide React for all icons
Zero console errors in production
Design System
Typography Scale
Element	Size	Weight	Tailwind
Page Title	24px	Semi-bold	text-2xl font-semibold text-text-primary
Section Header	18px	Semi-bold	text-lg font-semibold text-text-primary
Card Title	16px	Medium	text-base font-medium text-text-primary
Body Text	14px	Regular	text-sm text-text-secondary
Small/Meta	12px	Regular	text-xs text-text-tertiary
Spacing
Card padding: p-6 (24px)
Section gaps: gap-6 (24px)
Element gaps: gap-4 (16px)
Component Patterns
Cards: bg-surface-base rounded-card border border-border-subtle shadow-card p-6
Primary Button: bg-brand hover:bg-brand-dark text-text-primary font-medium px-6 py-3 rounded-lg transition-colors
Inputs: bg-surface-muted text-text-primary placeholder:text-text-tertiary px-4 py-3 rounded-lg w-full outline-none focus:ring-2 focus:ring-brand
Layout Structure
Sidebar: 240px wide, bg-surface-base, border-r
Header: Full width, bg-surface-base, border-b, h-16
Main: flex-1, overflow-y-auto, p-8
Responsive Breakpoints
Mobile: < 640px (default, no prefix)
Tablet: sm:640px+
Desktop: lg:1024px+
Touch targets: minimum 44x44px
Required File Structure
src/
\u251C\u2500\u2500 config/          # Backend configuration
\u251C\u2500\u2500 contexts/        # Auth, Theme, Toast, feature contexts
\u251C\u2500\u2500 hooks/           # useAuth, usePageTitle, custom hooks
\u251C\u2500\u2500 components/
\u2502   \u251C\u2500\u2500 ProtectedRoute.tsx
\u2502   \u251C\u2500\u2500 AdminRoute.tsx
\u2502   \u251C\u2500\u2500 ErrorBoundary.tsx
\u2502   \u251C\u2500\u2500 Layout.tsx
\u2502   \u251C\u2500\u2500 Sidebar.tsx
\u2502   \u251C\u2500\u2500 MobileNav.tsx
\u2502   \u2514\u2500\u2500 ui/          # Modal, ConfirmModal, Toast, Button, Avatar, ThemeToggle, Card, Skeleton, EmptyState, Spinner
\u251C\u2500\u2500 pages/           # LandingPage, LoginPage, Dashboard, Profile, NotFoundPage, [Item]Detail/Create/Edit
\u251C\u2500\u2500 services/        # api.ts (ALL backend operations)
\u251C\u2500\u2500 utils/           # formatDate.ts, pluralize.ts
\u2514\u2500\u2500 types/           # index.ts (ALL TypeScript interfaces)
Navigation Flow Pattern
LIST \u2192 click item \u2192 DETAIL \u2192 click edit \u2192 EDIT \u2192 save \u2192 DETAIL
LIST \u2192 click new  \u2192 CREATE \u2192 save \u2192 DETAIL
DETAIL \u2192 delete (with ConfirmModal) \u2192 LIST
Key Patterns
Dark-first styles use CSS variables for both modes
Unsaved changes warning via beforeunload
Network/offline detection with banner
Pagination or Load More for all lists
Search/filter when list > 5 items
404 handling at route and data level`
    },
    {
      id: 4,
      title: 'Agent OS',
      prompt: `# Agent OS Integration Guide for Claude Code (claude.ai/code)
## What is Agent OS?
 Agent OS is a **spec-driven development system** that provides structured context to AI coding agents through a 3-layer model:
1. **Standards Layer** \u2014 Your team's coding conventions, patterns, and best practices
2. **Product Layer** \u2014 The vision, roadmap, and use cases you're building
3. **Specs Layer** \u2014 Detailed specifications for upcoming features
**Core Philosophy**: Your coding standards become executable specifications that guide AI agents to build your way, every time\u2014eliminating repetitive prompting and reducing manual corrections.
## How to Use Agent OS in Claude Code Web (claude.ai/code)
Unlike VS Code where .claude directory files are automatically detected, Claude Code on the web requires you to **explicitly provide context** in your project. Here are the recommended approaches:
### Option 1: Repository-Based Approach (Recommended)
Store your Agent OS files in your repository:
your-project/
\u251C\u2500\u2500 .claude/
\u2502   \u251C\u2500\u2500 standards/
\u2502   \u2502   \u251C\u2500\u2500 coding-conventions.md
\u2502   \u2502   \u251C\u2500\u2500 architecture-patterns.md
\u2502   \u2502   \u2514\u2500\u2500 security-requirements.md
\u2502   \u251C\u2500\u2500 product/
\u2502   \u2502   \u251C\u2500\u2500 vision.md
\u2502   \u2502   \u251C\u2500\u2500 roadmap.md
\u2502   \u2502   \u2514\u2500\u2500 use-cases.md
\u2502   \u2514\u2500\u2500 specs/
\u2502       \u251C\u2500\u2500 feature-001-auth.md
\u2502       \u251C\u2500\u2500 feature-002-dashboard.md
\u2502       \u2514\u2500\u2500 [upcoming features]
**When starting a session**, reference these files explicitly:
"I'm using the Agent OS system. Please read the standards in .claude/standards/,
the product context in .claude/product/, and the feature specs in .claude/specs/
before implementing [specific feature]."
### Option 2: Inline Context Approach
For smaller projects or quick sessions, provide the Agent OS context directly in your initial prompt:
# Agent OS Context
## STANDARDS
[Your coding conventions, patterns, and practices]
## PRODUCT
[Your vision, roadmap, and use cases]
## SPEC
[Detailed specification for the current feature]
Task: [Your specific request]
## Best Practices for Claude Code Web
### 1. **Start Every Session with Context**
Always provide or reference your Agent OS layers at the start. Claude's memory resets between sessions.
### 2. **Use File References**
If you have Agent OS files in your repo, ask me to read them.
### 3. **Layer Your Prompts**
- **First message**: Provide Standards + Product context
- **Second message**: Provide Spec + Task
### 4. **Maintain a Living Document**
Keep an AGENT_OS_CONTEXT.md file in your project root.
### 5. **Update Specs as You Build**
After each feature, update your specs to reflect what was built, what changed, and what was learned.
**Ready to use Agent OS?** Start by filling out the template above with your project's context, and I'll build exactly the way you want, every time.`
    },
    {
      id: 5,
      title: 'Context Efficiency Rules',
      prompt: `## MANDATORY: Context Efficiency Rules
You are working on the Greptacular codebase. Follow these rules strictly to preserve your context window for coding:
### Step 1: Read Briefings (do this FIRST, before anything else)
1. Read \`AGENT_BRIEFING.md\` at project root \u2014 master architecture overview
2. Read \`docs/agent-briefs/{FEATURE_BRIEF}.md\` \u2014 specific to your task
### Step 2: Read ONLY Files You Will Edit
- Read ONLY the files listed in "Files You Will Modify" below
- Do NOT read files "just to understand" \u2014 the briefings cover that
- Do NOT read types.ts or api.ts in full \u2014 search for the specific interface/function you need
- Maximum 5 files read directly by you
### Step 3: Use Subagents for Everything Else
- **Need to understand how another component works?** \u2192 Spawn an Explore subagent
- **Need to find where something is imported?** \u2192 Spawn an Explore subagent
- **Need to check what pattern a similar component uses?** \u2192 Spawn an Explore subagent
- **Need to search for a string across the codebase?** \u2192 Spawn an Explore subagent
- NEVER run Glob/Grep yourself unless it's a single targeted search for a specific file
- The subagent's context is separate from yours \u2014 use this to your advantage
### Step 4: Context Budget
- Stop coding at 50% context usage
- If you hit 45%, wrap up current work, commit, and save progress notes
- Never start a new feature if you're above 40%
---
## Your Task
{DESCRIBE THE SPECIFIC TASK \u2014 be detailed about what to build, not how}
## Feature Brief to Read
docs/agent-briefs/{BRIEF_NAME}.md
## Files You Will Modify
- {path/to/file1}
- {path/to/file2}
- {path/to/file3}
## Files You Might Need to Reference (use subagent)
- {path/to/reference1} \u2014 {why you might need it}
- {path/to/reference2} \u2014 {why you might need it}
## Acceptance Criteria
- {What "done" looks like \u2014 specific, testable}
- {Another criterion}
- {Another criterion}`
    },
    { id: 6, title: 'Prompt 6', prompt: 'Replace with your prompt.' },
    { id: 7, title: 'Prompt 7', prompt: 'Replace with your prompt.' },
    { id: 8, title: 'Prompt 8', prompt: 'Replace with your prompt.' },
    { id: 9, title: 'Prompt 9', prompt: 'Replace with your prompt.' },
    { id: 10, title: 'Prompt 10', prompt: 'Replace with your prompt.' },
    { id: 11, title: 'Prompt 11', prompt: 'Replace with your prompt.' },
    { id: 12, title: 'Prompt 12', prompt: 'Replace with your prompt.' },
    { id: 13, title: 'Prompt 13', prompt: 'Replace with your prompt.' },
    { id: 14, title: 'Prompt 14', prompt: 'Replace with your prompt.' },
    { id: 15, title: 'Prompt 15', prompt: 'Replace with your prompt.' },
    { id: 16, title: 'Prompt 16', prompt: 'Replace with your prompt.' },
    { id: 17, title: 'Prompt 17', prompt: 'Replace with your prompt.' },
    { id: 18, title: 'Prompt 18', prompt: 'Replace with your prompt.' },
    { id: 19, title: 'Prompt 19', prompt: 'Replace with your prompt.' },
    { id: 20, title: 'Prompt 20', prompt: 'Replace with your prompt.' }
  ];

  // ================================================================
  // SECTION: ZOOM STATE & CONSTANTS
  // ================================================================

  const ZOOM_STORAGE_KEY = 'cpi-zoom-level';
  const DEFAULT_ZOOM = 100;
  const ZOOM_STEP = 10;
  const ZOOM_MIN = 30;
  const ZOOM_MAX = 300;

  // ================================================================
  // SECTION: PROMPT STORAGE (localStorage persistence)
  // ================================================================

  const PROMPT_STORAGE_KEY = 'cpi-custom-prompts';

  /** Load prompts from localStorage, falling back to hardcoded PROMPTS. */
  function loadCustomPrompts() {
    try {
      const raw = localStorage.getItem(PROMPT_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch (_) {
      // Corrupted data -- fall back to defaults
    }
    return PROMPTS.map((p) => ({ id: p.id, title: p.title, prompt: p.prompt }));
  }

  /** Save prompts to localStorage (strips backticks from title and prompt). */
  function saveCustomPrompts(prompts) {
    const cleaned = prompts.map((p) => ({
      id: p.id,
      title: String(p.title).replace(/`/g, ''),
      prompt: String(p.prompt).replace(/`/g, '')
    }));
    localStorage.setItem(PROMPT_STORAGE_KEY, JSON.stringify(cleaned));
    return cleaned;
  }

  let activePrompts = loadCustomPrompts();

  function loadZoom() {
    const saved = localStorage.getItem(ZOOM_STORAGE_KEY);
    if (saved !== null) {
      const num = parseInt(saved, 10);
      if (!isNaN(num) && num >= ZOOM_MIN && num <= ZOOM_MAX) {
        return num;
      }
    }
    return DEFAULT_ZOOM;
  }

  let currentZoom = loadZoom();

  // ================================================================
  // SECTION: PHASE FORGE STORAGE KEYS
  // ================================================================

  const PF_KEYS = {
    projectName: 'pf-project-name',
    prd: 'pf-prd',
    config: 'pf-config',
    phases: 'pf-phases',
    sharedAssets: 'pf-shared-assets',
    runnerState: 'pf-runner-state',
    panelOpen: 'pf-panel-open'
  };

  // ================================================================
  // SECTION: PHASE FORGE STATE MANAGEMENT
  // ================================================================

  /** Load a JSON value from localStorage with a fallback default. */
  function pfLoad(key, defaultValue) {
    try {
      const raw = localStorage.getItem(key);
      if (raw !== null) {
        return JSON.parse(raw);
      }
    } catch (_) {
      // Corrupted -- use default
    }
    return defaultValue;
  }

  /** Save a JSON value to localStorage. */
  function pfSave(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  }

  // Phase Forge state object -- single source of truth
  const pfState = {
    projectName: pfLoad(PF_KEYS.projectName, ''),
    prd: pfLoad(PF_KEYS.prd, ''),
    prdCaptured: false,
    prdStep: 0,
    prdMode: 'questionnaire', // 'questionnaire' or 'rant'
    config: pfLoad(PF_KEYS.config, {
      model: 'claude-web-200k',
      contextPercent: 50,
      roles: {
        builder: true,
        reviewer: false,
        architect: false,
        tester: false,
        planner: false
      }
    }),
    phases: pfLoad(PF_KEYS.phases, []),
    sharedAssets: pfLoad(PF_KEYS.sharedAssets, {
      testingScript: '',
      architectureDoc: ''
    }),
    runner: pfLoad(PF_KEYS.runnerState, {
      currentPhase: 0,
      status: 'stopped' // 'stopped', 'running', 'paused'
    }),
    panelOpen: pfLoad(PF_KEYS.panelOpen, false)
  };

  // Check if PRD was previously captured
  if (pfState.prd && pfState.prd.length > 0) {
    pfState.prdCaptured = true;
  }

  /** Persist all Phase Forge state to localStorage. */
  function pfPersist() {
    pfSave(PF_KEYS.projectName, pfState.projectName);
    pfSave(PF_KEYS.prd, pfState.prd);
    pfSave(PF_KEYS.config, pfState.config);
    pfSave(PF_KEYS.phases, pfState.phases);
    pfSave(PF_KEYS.sharedAssets, pfState.sharedAssets);
    pfSave(PF_KEYS.runnerState, pfState.runner);
    pfSave(PF_KEYS.panelOpen, pfState.panelOpen);
  }

  // ================================================================
  // SECTION: MODEL DEFINITIONS (token budgets)
  // ================================================================

  const MODELS = {
    'claude-web-200k': { label: 'Claude Web (200K)', tokens: 200000 },
    'codex-web-400k': { label: 'Codex Web (400K)', tokens: 400000 },
    'gemini-web-1m': { label: 'Gemini Web (1M)', tokens: 1000000 },
    'custom': { label: 'Custom', tokens: 200000 }
  };

  // Role budget percentages (of the working budget, not total context)
  const ROLE_BUDGETS = {
    builder: 0.40,
    reviewer: 0.08,
    architect: 0.08,
    tester: 0.15,
    planner: 0.05
  };

  // ================================================================
  // SECTION: CSS STYLES (all inline)
  // ================================================================

  const PANEL_WIDTH = 180;

  const styles = document.createElement('style');
  styles.textContent = `
    /* ============================================================
       PROMPT INJECTOR PANEL STYLES
       ============================================================ */

    #cpi-panel {
      position: fixed;
      top: 50%;
      right: 16px;
      transform: translateY(-50%) scale(${currentZoom / 100});
      transform-origin: top right;
      width: ${PANEL_WIDTH}px;
      max-height: 85vh;
      z-index: 99999;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      display: flex;
      flex-direction: column;
      gap: 4px;
      transition: opacity 0.2s;
    }

    /* When Phase Forge panel is open, shift the prompt injector left */
    #cpi-panel.cpi-shifted {
      right: 356px;
    }

    #cpi-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: #262624;
      border: 1px solid #da7757;
      border-radius: 6px;
      padding: 3px 6px;
      grid-column: 1 / -1;
      gap: 4px;
    }

    #cpi-header-label {
      color: #e0e0e0;
      font-size: 9px;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
      user-select: none;
      flex-shrink: 0;
    }

    #cpi-header-label:hover {
      color: #da7757;
    }

    /* ---- Improved Zoom Pill ---- */

    #cpi-zoom-pill {
      display: flex;
      width: 100%;
      height: 36px;
      border-radius: 18px;
      overflow: hidden;
      border: 1px solid #555;
      background: #262624;
      margin-bottom: 2px;
    }

    .cpi-zoom-pill-half {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: #e0e0e0;
      font-size: 20px;
      font-weight: 700;
      background: #262624;
      border: none;
      transition: background 0.15s, color 0.15s;
      user-select: none;
      padding: 0;
      line-height: 1;
    }

    .cpi-zoom-pill-half:hover {
      background: #da7757;
      color: #fff;
    }

    .cpi-zoom-pill-half:active {
      background: #c4664a;
    }

    .cpi-zoom-pill-divider {
      width: 1px;
      background: #555;
    }

    #cpi-zoom-readout {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 2px 0;
    }

    #cpi-zoom-pct-label {
      color: #999;
      font-size: 10px;
      font-weight: 500;
    }

    #cpi-zoom-input {
      width: 36px;
      height: 18px;
      background: #1e1e1c;
      color: #e0e0e0;
      border: 1px solid #555;
      border-radius: 4px;
      font-size: 10px;
      text-align: center;
      padding: 0 2px;
      outline: none;
      font-family: inherit;
    }

    #cpi-zoom-input:focus {
      border-color: #da7757;
    }

    #cpi-zoom-set {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 18px;
      background: #da7757;
      color: #fff;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 9px;
      font-weight: 700;
      padding: 0 8px;
      line-height: 1;
      transition: background 0.15s;
    }

    #cpi-zoom-set:hover {
      background: #c4664a;
    }

    #cpi-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 3px;
      overflow-y: auto;
    }

    #cpi-grid.cpi-hidden {
      display: none;
    }

    .cpi-btn {
      position: relative;
      display: flex;
      align-items: center;
      width: 100%;
      padding: 4px 5px;
      padding-top: 6px;
      min-height: 32px;
      background: #262624;
      color: #e0e0e0;
      border: 1px solid #333;
      border-radius: 6px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
      text-align: left;
      transition: all 0.15s;
      line-height: 1.3;
    }

    .cpi-btn:hover {
      background: #30302e;
      border-color: #da7757;
      transform: translateX(-3px);
    }

    .cpi-btn:active {
      transform: translateX(-1px);
      background: #3a3a38;
    }

    .cpi-btn-num {
      position: absolute;
      top: 2px;
      left: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      min-width: 14px;
      height: 14px;
      background: #da7757;
      color: #fff;
      border-radius: 3px;
      font-size: 7px;
      font-weight: 700;
      padding: 0 2px;
    }

    .cpi-btn-title {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 6px;
      padding-left: 16px;
      padding-right: 2px;
    }

    .cpi-flash {
      animation: cpi-flash-anim 0.4s ease-out;
    }

    @keyframes cpi-flash-anim {
      0% { background: #da7757; border-color: #da7757; }
      100% { background: #262624; border-color: #333; }
    }

    /* ---- Editor Overlay ---- */

    #cpi-editor-overlay {
      position: fixed;
      inset: 0;
      z-index: 100000;
      background: rgba(0, 0, 0, 0.75);
      display: flex;
      align-items: flex-start;
      justify-content: center;
      padding-top: 3vh;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    #cpi-editor-panel {
      background: #1e1e1c;
      border: 1px solid #555;
      border-radius: 10px;
      width: 100%;
      max-width: 700px;
      max-height: 90vh;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
    }

    #cpi-editor-topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      border-bottom: 1px solid #555;
      background: #262624;
      border-radius: 10px 10px 0 0;
      position: sticky;
      top: 0;
      z-index: 1;
    }

    #cpi-editor-topbar-title {
      color: #e0e0e0;
      font-size: 15px;
      font-weight: 700;
    }

    .cpi-editor-topbar-btns {
      display: flex;
      gap: 8px;
      align-items: center;
    }

    .cpi-editor-btn {
      padding: 5px 14px;
      border: 1px solid #555;
      border-radius: 5px;
      background: #262624;
      color: #e0e0e0;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }

    .cpi-editor-btn:hover {
      border-color: #da7757;
      color: #da7757;
    }

    .cpi-editor-btn--save {
      background: #da7757;
      border-color: #da7757;
      color: #fff;
    }

    .cpi-editor-btn--save:hover {
      background: #c4664a;
      border-color: #c4664a;
      color: #fff;
    }

    .cpi-editor-btn--close {
      background: none;
      border: none;
      color: #999;
      font-size: 20px;
      cursor: pointer;
      padding: 0 4px;
      line-height: 1;
    }

    .cpi-editor-btn--close:hover {
      color: #ff4444;
    }

    #cpi-editor-note {
      color: #999;
      font-size: 11px;
      padding: 10px 16px 4px;
      font-style: italic;
    }

    .cpi-editor-item {
      padding: 10px 16px;
      border-bottom: 1px solid #333;
    }

    .cpi-editor-item:last-child {
      border-bottom: none;
    }

    .cpi-editor-item-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 6px;
    }

    .cpi-editor-badge {
      display: flex;
      align-items: center;
      justify-content: center;
      min-width: 22px;
      height: 22px;
      background: #da7757;
      color: #fff;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 700;
      padding: 0 4px;
      flex-shrink: 0;
    }

    .cpi-editor-title-input {
      flex: 1;
      background: #262624;
      color: #e0e0e0;
      border: 1px solid #555;
      border-radius: 4px;
      padding: 5px 8px;
      font-size: 13px;
      font-family: inherit;
      outline: none;
    }

    .cpi-editor-title-input:focus {
      border-color: #da7757;
    }

    .cpi-editor-textarea {
      width: 100%;
      min-height: 120px;
      background: #262624;
      color: #e0e0e0;
      border: 1px solid #555;
      border-radius: 4px;
      padding: 8px;
      font-size: 12px;
      font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
      line-height: 1.4;
      resize: vertical;
      outline: none;
      box-sizing: border-box;
    }

    .cpi-editor-textarea:focus {
      border-color: #da7757;
    }

    .cpi-gear-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 18px;
      height: 18px;
      background: none;
      border: none;
      color: #e0e0e0;
      cursor: pointer;
      font-size: 13px;
      padding: 0;
      flex-shrink: 0;
      transition: color 0.15s;
    }

    .cpi-gear-btn:hover {
      color: #da7757;
    }

    /* ============================================================
       PHASE FORGE PANEL STYLES
       ============================================================ */

    #pf-toggle-btn {
      position: fixed;
      top: 50%;
      transform: translateY(-50%);
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: #da7757;
      color: #fff;
      border: 2px solid #c4664a;
      cursor: pointer;
      font-size: 13px;
      font-weight: 800;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 100001;
      transition: right 0.3s ease, background 0.15s, box-shadow 0.15s;
      box-shadow: 0 2px 8px rgba(0,0,0,0.4);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      letter-spacing: -0.5px;
    }

    #pf-toggle-btn:hover {
      background: #c4664a;
      box-shadow: 0 2px 12px rgba(218,119,87,0.5);
    }

    #pf-toggle-btn.pf-open {
      right: 350px;
    }

    #pf-toggle-btn.pf-closed {
      right: 16px;
    }

    #pf-panel {
      position: fixed;
      right: 0;
      top: 0;
      width: 340px;
      height: 100vh;
      background: #1e1e1c;
      border-left: 2px solid #da7757;
      z-index: 100000;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      display: flex;
      flex-direction: column;
      transition: transform 0.3s ease;
      overflow: hidden;
    }

    #pf-panel.pf-hidden {
      transform: translateX(100%);
    }

    #pf-panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      background: #262624;
      border-bottom: 1px solid #333;
      flex-shrink: 0;
    }

    #pf-panel-title {
      color: #da7757;
      font-size: 16px;
      font-weight: 800;
      letter-spacing: 0.5px;
    }

    #pf-project-input {
      flex: 1;
      margin-left: 12px;
      background: #1e1e1c;
      color: #e0e0e0;
      border: 1px solid #444;
      border-radius: 4px;
      padding: 4px 8px;
      font-size: 11px;
      outline: none;
      font-family: inherit;
    }

    #pf-project-input:focus {
      border-color: #da7757;
    }

    #pf-panel-body {
      flex: 1;
      overflow-y: auto;
      padding: 0;
    }

    /* Collapsible sections */
    .pf-section {
      border-bottom: 1px solid #333;
    }

    .pf-section-header {
      display: flex;
      align-items: center;
      padding: 10px 16px;
      cursor: pointer;
      background: #262624;
      transition: background 0.15s;
      user-select: none;
      gap: 8px;
    }

    .pf-section-header:hover {
      background: #30302e;
    }

    .pf-section-chevron {
      color: #da7757;
      font-size: 10px;
      flex-shrink: 0;
      width: 12px;
      transition: transform 0.2s;
    }

    .pf-section-chevron.pf-expanded {
      transform: rotate(90deg);
    }

    .pf-section-title {
      color: #e0e0e0;
      font-size: 13px;
      font-weight: 600;
      flex: 1;
    }

    .pf-section-lock {
      color: #666;
      font-size: 12px;
      flex-shrink: 0;
    }

    .pf-section-body {
      padding: 12px 16px;
      display: none;
    }

    .pf-section-body.pf-visible {
      display: block;
    }

    .pf-section.pf-locked .pf-section-header {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .pf-section.pf-locked .pf-section-title {
      color: #666;
    }

    /* Pill toggle (Questionnaire / Rant) */
    .pf-pill-toggle {
      display: flex;
      width: 100%;
      height: 32px;
      border-radius: 16px;
      overflow: hidden;
      border: 1px solid #444;
      background: #1e1e1c;
      margin-bottom: 10px;
    }

    .pf-pill-option {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: #999;
      font-size: 11px;
      font-weight: 600;
      background: transparent;
      border: none;
      transition: all 0.2s;
      font-family: inherit;
      padding: 0;
    }

    .pf-pill-option.pf-active {
      background: #da7757;
      color: #fff;
    }

    .pf-pill-option:not(.pf-active):hover {
      background: #30302e;
      color: #e0e0e0;
    }

    /* Status indicators */
    .pf-status {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 10px;
      border-radius: 6px;
      font-size: 11px;
      margin: 6px 0;
    }

    .pf-status-info {
      background: #1a2a3a;
      color: #6ab0f3;
      border: 1px solid #2a3a4a;
    }

    .pf-status-success {
      background: #1a3a1a;
      color: #6af36a;
      border: 1px solid #2a4a2a;
    }

    .pf-status-warning {
      background: #3a3a1a;
      color: #f3d06a;
      border: 1px solid #4a4a2a;
    }

    /* Buttons in Phase Forge */
    .pf-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 6px 14px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid #444;
      background: #262624;
      color: #e0e0e0;
      transition: all 0.15s;
      font-family: inherit;
      gap: 4px;
    }

    .pf-btn:hover {
      border-color: #da7757;
      color: #da7757;
    }

    .pf-btn:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }

    .pf-btn:disabled:hover {
      border-color: #444;
      color: #e0e0e0;
    }

    .pf-btn-primary {
      background: #da7757;
      border-color: #da7757;
      color: #fff;
    }

    .pf-btn-primary:hover {
      background: #c4664a;
      border-color: #c4664a;
      color: #fff;
    }

    .pf-btn-primary:disabled {
      background: #5a3a2a;
      border-color: #5a3a2a;
    }

    .pf-btn-primary:disabled:hover {
      background: #5a3a2a;
      border-color: #5a3a2a;
      color: #fff;
    }

    .pf-btn-row {
      display: flex;
      gap: 8px;
      margin-top: 8px;
      flex-wrap: wrap;
    }

    /* Labels and inputs */
    .pf-label {
      color: #999;
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
      display: block;
    }

    .pf-select {
      width: 100%;
      background: #1e1e1c;
      color: #e0e0e0;
      border: 1px solid #444;
      border-radius: 4px;
      padding: 6px 8px;
      font-size: 12px;
      outline: none;
      font-family: inherit;
      cursor: pointer;
    }

    .pf-select:focus {
      border-color: #da7757;
    }

    .pf-input {
      width: 100%;
      background: #1e1e1c;
      color: #e0e0e0;
      border: 1px solid #444;
      border-radius: 4px;
      padding: 6px 8px;
      font-size: 12px;
      outline: none;
      font-family: inherit;
      box-sizing: border-box;
    }

    .pf-input:focus {
      border-color: #da7757;
    }

    .pf-textarea {
      width: 100%;
      min-height: 60px;
      background: #1e1e1c;
      color: #e0e0e0;
      border: 1px solid #444;
      border-radius: 4px;
      padding: 6px 8px;
      font-size: 11px;
      font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
      line-height: 1.4;
      resize: vertical;
      outline: none;
      box-sizing: border-box;
    }

    .pf-textarea:focus {
      border-color: #da7757;
    }

    /* Slider */
    .pf-slider-row {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 6px 0;
    }

    .pf-slider {
      flex: 1;
      -webkit-appearance: none;
      appearance: none;
      height: 6px;
      background: #333;
      border-radius: 3px;
      outline: none;
    }

    .pf-slider::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: #da7757;
      cursor: pointer;
      border: 2px solid #c4664a;
    }

    .pf-slider::-moz-range-thumb {
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: #da7757;
      cursor: pointer;
      border: 2px solid #c4664a;
    }

    .pf-slider-val {
      color: #da7757;
      font-size: 12px;
      font-weight: 700;
      min-width: 32px;
      text-align: right;
    }

    /* Checkboxes */
    .pf-check-row {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 4px 0;
    }

    .pf-check-row label {
      color: #e0e0e0;
      font-size: 12px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .pf-check-row label.pf-disabled {
      color: #666;
      cursor: not-allowed;
    }

    .pf-check-row input[type="checkbox"] {
      accent-color: #da7757;
      width: 14px;
      height: 14px;
      cursor: pointer;
    }

    .pf-budget-pct {
      color: #777;
      font-size: 10px;
      margin-left: auto;
    }

    /* Token budget display */
    .pf-token-budget {
      background: #1a1a18;
      border: 1px solid #333;
      border-radius: 6px;
      padding: 8px 10px;
      margin-top: 10px;
      font-size: 11px;
      color: #ccc;
      line-height: 1.6;
    }

    .pf-token-budget strong {
      color: #da7757;
    }

    /* Phase list */
    .pf-phase-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 10px;
      border: 1px solid #333;
      border-radius: 6px;
      margin-bottom: 6px;
      background: #262624;
      cursor: pointer;
      transition: border-color 0.15s, background 0.15s;
    }

    .pf-phase-item:hover {
      border-color: #da7757;
      background: #30302e;
    }

    .pf-phase-item.pf-phase-active {
      border-color: #da7757;
      background: #3a2a20;
    }

    .pf-phase-num {
      color: #da7757;
      font-size: 12px;
      font-weight: 700;
      flex-shrink: 0;
      min-width: 18px;
    }

    .pf-phase-status {
      font-size: 14px;
      flex-shrink: 0;
    }

    .pf-phase-preview {
      flex: 1;
      color: #ccc;
      font-size: 11px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    /* Progress bar */
    .pf-progress-bar-outer {
      width: 100%;
      height: 10px;
      background: #333;
      border-radius: 5px;
      overflow: hidden;
      margin: 8px 0;
    }

    .pf-progress-bar-inner {
      height: 100%;
      background: linear-gradient(90deg, #da7757, #e8956e);
      border-radius: 5px;
      transition: width 0.3s ease;
    }

    .pf-run-status {
      color: #ccc;
      font-size: 12px;
      text-align: center;
      padding: 4px 0;
      font-weight: 500;
    }

    .pf-run-complete {
      color: #6af36a;
      font-size: 14px;
      text-align: center;
      padding: 10px;
      font-weight: 700;
    }

    /* Phase edit modal */
    #pf-phase-modal-overlay {
      position: fixed;
      inset: 0;
      z-index: 100002;
      background: rgba(0, 0, 0, 0.75);
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    #pf-phase-modal {
      background: #1e1e1c;
      border: 1px solid #555;
      border-radius: 10px;
      width: 90%;
      max-width: 600px;
      max-height: 80vh;
      display: flex;
      flex-direction: column;
    }

    #pf-phase-modal-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      border-bottom: 1px solid #444;
      background: #262624;
      border-radius: 10px 10px 0 0;
    }

    #pf-phase-modal-header span {
      color: #e0e0e0;
      font-size: 14px;
      font-weight: 700;
    }

    #pf-phase-modal-body {
      padding: 16px;
      flex: 1;
      overflow-y: auto;
    }

    #pf-phase-modal-body textarea {
      width: 100%;
      min-height: 300px;
      background: #262624;
      color: #e0e0e0;
      border: 1px solid #444;
      border-radius: 6px;
      padding: 10px;
      font-size: 12px;
      font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
      line-height: 1.5;
      resize: vertical;
      outline: none;
      box-sizing: border-box;
    }

    #pf-phase-modal-body textarea:focus {
      border-color: #da7757;
    }

    #pf-phase-modal-footer {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      padding: 12px 16px;
      border-top: 1px solid #444;
    }

    /* Shared group spacing */
    .pf-group {
      margin-bottom: 12px;
    }

    .pf-group:last-child {
      margin-bottom: 0;
    }

    .pf-divider {
      border: none;
      border-top: 1px solid #333;
      margin: 10px 0;
    }

    /* Scrollbar styling for PF panel */
    #pf-panel-body::-webkit-scrollbar {
      width: 6px;
    }

    #pf-panel-body::-webkit-scrollbar-track {
      background: #1e1e1c;
    }

    #pf-panel-body::-webkit-scrollbar-thumb {
      background: #444;
      border-radius: 3px;
    }

    #pf-panel-body::-webkit-scrollbar-thumb:hover {
      background: #555;
    }
  `;
  document.head.appendChild(styles);


  // ================================================================
  // SECTION: INJECT TEXT INTO CHAT INPUT (preserved from v1)
  // ================================================================

  /**
   * Finds the active chat editor element on the page.
   * Supports Claude.ai (ProseMirror), ChatGPT, Gemini, and generic fallbacks.
   * @returns {{ el: HTMLElement, type: string } | null}
   */
  function getEditor() {
    // Claude.ai -- ProseMirror contenteditable
    let el = document.querySelector('.ProseMirror[contenteditable="true"]');
    if (el) return { el, type: 'prosemirror' };

    el = document.querySelector('div[data-placeholder][contenteditable="true"]');
    if (el) return { el, type: 'prosemirror' };

    // ChatGPT -- also contenteditable (ProseMirror)
    el = document.querySelector('#prompt-textarea');
    if (el) return { el, type: 'prosemirror' };

    // Gemini -- contenteditable rich text
    el = document.querySelector('.ql-editor[contenteditable="true"]');
    if (el) return { el, type: 'prosemirror' };

    // Generic contenteditable fallback
    el = document.querySelector('div[contenteditable="true"]');
    if (el) return { el, type: 'prosemirror' };

    // Plain textarea fallback
    el = document.querySelector('textarea');
    if (el) return { el, type: 'textarea' };

    return null;
  }

  /**
   * Injects the given text into the active chat editor.
   * Uses execCommand for ProseMirror editors, with a paste fallback.
   * @param {string} text - The text to inject
   * @returns {boolean} Whether injection succeeded
   */
  function injectPrompt(text) {
    const editor = getEditor();
    if (!editor) {
      console.warn('[Phase Forge] No chat input found on this page.');
      return false;
    }

    const { el, type } = editor;

    if (type === 'textarea') {
      // Simple textarea -- set value and fire input event
      const nativeSetter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
      ).set;
      nativeSetter.call(el, text + '\n\n');
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.focus();
      return true;
    }

    // ProseMirror / contenteditable approach
    el.focus();

    // Select all existing content
    const sel = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(el);
    sel.removeAllRanges();
    sel.addRange(range);

    // Try execCommand first (works for ProseMirror)
    const success = document.execCommand('insertText', false, text + '\n\n');

    if (!success) {
      // Fallback: paste simulation
      const clipboardData = new DataTransfer();
      clipboardData.setData('text/plain', text + '\n\n');
      el.dispatchEvent(new ClipboardEvent('paste', {
        clipboardData,
        bubbles: true,
        cancelable: true
      }));
    }

    return true;
  }

  // ================================================================
  // SECTION: ZOOM HELPERS
  // ================================================================

  function applyZoom(panel, zoom) {
    const scale = zoom / 100;
    panel.style.transform = 'translateY(-50%) scale(' + scale + ')';
  }

  function clampZoom(value) {
    return Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, value));
  }

  // ================================================================
  // SECTION: SEND BUTTON DETECTION
  // Finds and clicks the send button on Claude.ai, ChatGPT, or Gemini.
  // Uses multiple selectors with fallbacks for resilience.
  // ================================================================

  /**
   * Finds the send/submit button on the current AI chat page.
   * @returns {HTMLElement|null}
   */
  function findSendButton() {
    // Claude.ai: button with aria-label "Send Message" or a send icon
    let btn = document.querySelector('button[aria-label="Send Message"]');
    if (btn && !btn.disabled) return btn;

    btn = document.querySelector('button[aria-label="Send message"]');
    if (btn && !btn.disabled) return btn;

    // Claude.ai: look for the send button near the input area
    const claudeButtons = document.querySelectorAll('fieldset button[type="button"], form button[type="submit"]');
    for (const b of claudeButtons) {
      // The send button typically has an SVG icon and is not disabled
      if (!b.disabled && b.querySelector('svg') && b.offsetParent !== null) {
        const rect = b.getBoundingClientRect();
        // Only consider visible buttons of reasonable size
        if (rect.width > 20 && rect.width < 60 && rect.height > 20 && rect.height < 60) {
          return b;
        }
      }
    }

    // ChatGPT: data-testid="send-button"
    btn = document.querySelector('[data-testid="send-button"]');
    if (btn && !btn.disabled) return btn;

    // ChatGPT: button with aria-label "Send prompt"
    btn = document.querySelector('button[aria-label="Send prompt"]');
    if (btn && !btn.disabled) return btn;

    // Gemini: button with aria-label "Send message"
    btn = document.querySelector('button[aria-label="Send message"]');
    if (btn && !btn.disabled) return btn;

    // Generic: look for a submit-type button in a form near the editor
    const editor = getEditor();
    if (editor) {
      const form = editor.el.closest('form');
      if (form) {
        btn = form.querySelector('button[type="submit"]');
        if (btn && !btn.disabled) return btn;
      }
    }

    return null;
  }

  /**
   * Clicks the send button. Returns true if a button was found and clicked.
   * @returns {boolean}
   */
  function clickSendButton() {
    const btn = findSendButton();
    if (btn) {
      btn.click();
      return true;
    }
    return false;
  }

  // ================================================================
  // SECTION: COMPLETION DETECTION ENGINE
  // MutationObserver that watches the chat area for when the AI
  // finishes responding. Works across Claude.ai, ChatGPT, Gemini.
  // ================================================================

  /**
   * Watches for response completion by tracking DOM mutations.
   * Resolves when no mutations for the specified quiet period AND
   * the send button becomes available (indicating the AI has finished).
   *
   * @param {number} quietMs - Milliseconds of DOM quiet to wait (default 4000)
   * @param {number} timeoutMs - Maximum wait time before giving up (default 300000 = 5 min)
   * @returns {Promise<boolean>} Resolves true when complete, false on timeout
   */
  function waitForResponseComplete(quietMs, timeoutMs) {
    if (quietMs === undefined) quietMs = 4000;
    if (timeoutMs === undefined) timeoutMs = 300000;

    return new Promise(function (resolve) {
      let lastMutationTime = Date.now();
      let observer = null;
      let checkInterval = null;
      let timeoutHandle = null;

      // Find the chat messages container to observe
      // Try various selectors for different sites
      const chatContainer = document.querySelector(
        // Claude.ai
        '[class*="conversation"], [class*="messages"], ' +
        // ChatGPT
        '[class*="react-scroll-to-bottom"], main [role="presentation"], ' +
        // Gemini
        '[class*="response-container"], ' +
        // Generic fallback
        'main, [role="main"]'
      ) || document.body;

      function cleanup() {
        if (observer) {
          observer.disconnect();
          observer = null;
        }
        if (checkInterval) {
          clearInterval(checkInterval);
          checkInterval = null;
        }
        if (timeoutHandle) {
          clearTimeout(timeoutHandle);
          timeoutHandle = null;
        }
      }

      observer = new MutationObserver(function () {
        lastMutationTime = Date.now();
      });

      observer.observe(chatContainer, {
        childList: true,
        subtree: true,
        characterData: true
      });

      // Periodically check if we have been quiet long enough
      checkInterval = setInterval(function () {
        const elapsed = Date.now() - lastMutationTime;
        if (elapsed >= quietMs) {
          // Also check if the send button is available (indicating AI is done)
          const sendBtn = findSendButton();
          if (sendBtn) {
            cleanup();
            resolve(true);
          }
        }
      }, 500);

      // Timeout safety net
      timeoutHandle = setTimeout(function () {
        cleanup();
        resolve(false);
      }, timeoutMs);
    });
  }

  // ================================================================
  // SECTION: PRD MARKER DETECTION
  // MutationObserver that watches Claude's response for PRD markers:
  //   === PRD READY === ... content ... === END PRD ===
  // When detected, scrapes the PRD text and stores it.
  // ================================================================

  let prdObserver = null;

  /**
   * Starts watching the chat area for PRD markers.
   * When found, captures the PRD content and calls the callback.
   * @param {function} onCapture - Called with the captured PRD text
   */
  function startPrdWatcher(onCapture) {
    stopPrdWatcher(); // Clean up any existing watcher

    const chatContainer = document.querySelector(
      '[class*="conversation"], [class*="messages"], ' +
      '[class*="react-scroll-to-bottom"], main [role="presentation"], ' +
      '[class*="response-container"], ' +
      'main, [role="main"]'
    ) || document.body;

    function checkForPrd() {
      const text = chatContainer.innerText || chatContainer.textContent || '';
      const startMarker = '=== PRD READY ===';
      const endMarker = '=== END PRD ===';
      const startIdx = text.lastIndexOf(startMarker);
      const endIdx = text.lastIndexOf(endMarker);

      if (startIdx !== -1 && endIdx !== -1 && endIdx > startIdx) {
        const prdContent = text.substring(startIdx + startMarker.length, endIdx).trim();
        if (prdContent.length > 50) {
          // Valid PRD captured
          stopPrdWatcher();
          if (onCapture) onCapture(prdContent);
        }
      }
    }

    prdObserver = new MutationObserver(function () {
      // Debounce the check slightly
      clearTimeout(prdObserver._debounce);
      prdObserver._debounce = setTimeout(checkForPrd, 1000);
    });

    prdObserver.observe(chatContainer, {
      childList: true,
      subtree: true,
      characterData: true
    });
  }

  /** Stops the PRD watcher observer. */
  function stopPrdWatcher() {
    if (prdObserver) {
      clearTimeout(prdObserver._debounce);
      prdObserver.disconnect();
      prdObserver = null;
    }
  }

  // ================================================================
  // SECTION: TOKEN BUDGET CALCULATOR
  // ================================================================

  /**
   * Calculates the token budget breakdown based on current config.
   * @returns {{ total: number, available: number, builder: number, buffer: number, overhead: number, roles: Object }}
   */
  function calculateBudget() {
    const modelKey = pfState.config.model;
    const modelDef = MODELS[modelKey] || MODELS['claude-web-200k'];
    const totalTokens = modelDef.tokens;
    const contextPct = pfState.config.contextPercent / 100;
    const available = Math.floor(totalTokens * contextPct);

    // Calculate overhead (prompt framing, system messages) -- fixed 4% of available
    const overhead = Math.floor(available * 0.04);

    // Calculate active role budgets
    const roles = {};
    let totalRolePct = 0;
    const activeRoles = pfState.config.roles;
    for (const role in activeRoles) {
      if (activeRoles[role]) {
        const pct = ROLE_BUDGETS[role] || 0;
        totalRolePct += pct;
        roles[role] = Math.floor(available * pct);
      }
    }

    // Buffer is whatever remains after roles + overhead
    const usedByRoles = Object.values(roles).reduce(function (sum, v) { return sum + v; }, 0);
    const buffer = available - usedByRoles - overhead;

    return {
      total: totalTokens,
      available: available,
      builder: roles.builder || 0,
      buffer: Math.max(0, buffer),
      overhead: overhead,
      roles: roles
    };
  }

  /**
   * Formats a token count for display (e.g., 200000 -> "200K").
   * @param {number} n
   * @returns {string}
   */
  function formatTokens(n) {
    if (n >= 1000000) return (n / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
    return String(n);
  }

  // ================================================================
  // SECTION: AGENT ROLE DIRECTIVE TEMPLATES
  // When the Phase Runner sends a phase, it prepends active agent
  // role directives to the prompt.
  // ================================================================

  const ROLE_DIRECTIVES = {
    builder: 'Role: BUILDER (Primary)\nYou are the primary coding agent. Write all new code for this phase. Follow the PRD requirements exactly. Output complete, production-ready code with no placeholders or TODOs.',
    reviewer: 'Role: REVIEWER\nAfter writing each file, review it for logic errors, edge cases, security vulnerabilities, and consistency with the overall architecture. Flag any issues inline.',
    architect: 'Role: ARCHITECT\nBefore writing code, briefly outline the technical approach. Identify which files need to change, what patterns to use, and any potential architectural concerns.',
    tester: 'Role: TESTER\nAfter implementation, write tests for the code produced in the previous phase. Ensure critical paths have coverage. Report any regressions.',
    planner: 'Role: PLANNER\nAt the end of this phase, briefly scout the next phase. Identify prerequisites, potential blockers, and suggest an implementation order.'
  };

  /**
   * Builds the full prompt to send for a given phase index.
   * Combines agent directives, shared assets, and phase content.
   * @param {number} phaseIndex - Zero-based phase index
   * @returns {string}
   */
  function buildPhasePrompt(phaseIndex) {
    const phase = pfState.phases[phaseIndex];
    if (!phase) return '';

    const totalPhases = pfState.phases.length;
    const parts = [];

    // Agent directives (only active roles)
    const activeDirectives = [];
    for (const role in pfState.config.roles) {
      if (pfState.config.roles[role] && ROLE_DIRECTIVES[role]) {
        activeDirectives.push(ROLE_DIRECTIVES[role]);
      }
    }

    if (activeDirectives.length > 0) {
      parts.push('=== AGENT DIRECTIVES ===\n');
      parts.push(activeDirectives.join('\n\n'));
      parts.push('');
    }

    // Shared assets
    const hasTestingScript = pfState.sharedAssets.testingScript && pfState.sharedAssets.testingScript.trim().length > 0;
    const hasArchDoc = pfState.sharedAssets.architectureDoc && pfState.sharedAssets.architectureDoc.trim().length > 0;

    if (hasTestingScript || hasArchDoc) {
      parts.push('=== SHARED ASSETS ===\n');
      if (hasTestingScript) {
        parts.push('--- Testing Script ---');
        parts.push(pfState.sharedAssets.testingScript.trim());
        parts.push('');
      }
      if (hasArchDoc) {
        parts.push('--- Architecture Document ---');
        parts.push(pfState.sharedAssets.architectureDoc.trim());
        parts.push('');
      }
    }

    // Phase content with placeholders replaced
    let content = phase.content || '';
    if (hasTestingScript) {
      content = content.replace(/\{\{TESTING_SCRIPT\}\}/g, pfState.sharedAssets.testingScript.trim());
    }
    if (hasArchDoc) {
      content = content.replace(/\{\{ARCHITECTURE_DOC\}\}/g, pfState.sharedAssets.architectureDoc.trim());
    }

    parts.push('=== PHASE ' + (phaseIndex + 1) + ' of ' + totalPhases + ' ===\n');
    parts.push(content);

    return parts.join('\n');
  }


  // ================================================================
  // SECTION: EDITOR OVERLAY (preserved from v1)
  // Opens the full-screen prompt editor for the 20 prompt buttons.
  // ================================================================

  /**
   * Open the full-screen prompt editor overlay.
   * @param {function} onSave - callback invoked after saving (receives cleaned prompts array)
   * @param {function} onReset - callback invoked after resetting to defaults
   */
  function showEditor(onSave, onReset) {
    // Prevent duplicate overlays
    if (document.getElementById('cpi-editor-overlay')) return;

    const overlay = document.createElement('div');
    overlay.id = 'cpi-editor-overlay';

    const editorPanel = document.createElement('div');
    editorPanel.id = 'cpi-editor-panel';

    // Top bar
    const topbar = document.createElement('div');
    topbar.id = 'cpi-editor-topbar';

    const title = document.createElement('span');
    title.id = 'cpi-editor-topbar-title';
    title.textContent = 'Edit Prompts';

    const btns = document.createElement('div');
    btns.className = 'cpi-editor-topbar-btns';

    const resetBtn = document.createElement('button');
    resetBtn.className = 'cpi-editor-btn';
    resetBtn.textContent = 'Reset to Defaults';

    const saveBtn = document.createElement('button');
    saveBtn.className = 'cpi-editor-btn cpi-editor-btn--save';
    saveBtn.textContent = 'Save';

    const closeBtn = document.createElement('button');
    closeBtn.className = 'cpi-editor-btn--close';
    closeBtn.textContent = '\u00D7';
    closeBtn.title = 'Close without saving';

    btns.appendChild(resetBtn);
    btns.appendChild(saveBtn);
    btns.appendChild(closeBtn);
    topbar.appendChild(title);
    topbar.appendChild(btns);
    editorPanel.appendChild(topbar);

    // Note
    const note = document.createElement('div');
    note.id = 'cpi-editor-note';
    note.textContent = 'Paste anything \u2014 backticks are auto-removed on save.';
    editorPanel.appendChild(note);

    // Build an input row for each prompt
    const inputs = []; // { titleInput, textareaInput, id }
    activePrompts.forEach(function (p) {
      const item = document.createElement('div');
      item.className = 'cpi-editor-item';

      const hdr = document.createElement('div');
      hdr.className = 'cpi-editor-item-header';

      const badge = document.createElement('span');
      badge.className = 'cpi-editor-badge';
      badge.textContent = String(p.id);

      const titleInput = document.createElement('input');
      titleInput.className = 'cpi-editor-title-input';
      titleInput.type = 'text';
      titleInput.value = p.title;
      titleInput.placeholder = 'Prompt title';

      hdr.appendChild(badge);
      hdr.appendChild(titleInput);
      item.appendChild(hdr);

      const textarea = document.createElement('textarea');
      textarea.className = 'cpi-editor-textarea';
      textarea.value = p.prompt;
      textarea.placeholder = 'Enter prompt content...';
      item.appendChild(textarea);

      editorPanel.appendChild(item);
      inputs.push({ id: p.id, titleInput: titleInput, textarea: textarea });
    });

    overlay.appendChild(editorPanel);

    // Close helper
    function closeOverlay() {
      overlay.remove();
    }

    // Close on overlay background click (not on panel itself)
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeOverlay();
    });

    closeBtn.addEventListener('click', closeOverlay);

    // Save
    saveBtn.addEventListener('click', function () {
      const updated = inputs.map(function (inp) {
        return {
          id: inp.id,
          title: inp.titleInput.value,
          prompt: inp.textarea.value
        };
      });
      const cleaned = saveCustomPrompts(updated);
      activePrompts = cleaned;
      closeOverlay();
      if (onSave) onSave(cleaned);
    });

    // Reset to defaults
    resetBtn.addEventListener('click', function () {
      localStorage.removeItem(PROMPT_STORAGE_KEY);
      activePrompts = PROMPTS.map(function (p) { return { id: p.id, title: p.title, prompt: p.prompt }; });
      closeOverlay();
      if (onReset) onReset();
    });

    document.body.appendChild(overlay);
  }

  // ================================================================
  // SECTION: BUILD PROMPT INJECTOR PANEL (improved zoom pill)
  // ================================================================

  function buildPanel() {
    const panel = document.createElement('div');
    panel.id = 'cpi-panel';

    // If Phase Forge panel is open, shift left
    if (pfState.panelOpen) {
      panel.classList.add('cpi-shifted');
    }

    // ---- Improved Zoom Pill (full-width at top) ----
    const zoomPill = document.createElement('div');
    zoomPill.id = 'cpi-zoom-pill';

    const pillMinus = document.createElement('button');
    pillMinus.className = 'cpi-zoom-pill-half';
    pillMinus.textContent = '\u2212';
    pillMinus.title = 'Zoom out';

    const pillDivider = document.createElement('div');
    pillDivider.className = 'cpi-zoom-pill-divider';

    const pillPlus = document.createElement('button');
    pillPlus.className = 'cpi-zoom-pill-half';
    pillPlus.textContent = '+';
    pillPlus.title = 'Zoom in';

    zoomPill.appendChild(pillMinus);
    zoomPill.appendChild(pillDivider);
    zoomPill.appendChild(pillPlus);
    panel.appendChild(zoomPill);

    // Zoom readout row: current %, input, and Set button
    const zoomReadout = document.createElement('div');
    zoomReadout.id = 'cpi-zoom-readout';

    const zoomLabel = document.createElement('span');
    zoomLabel.id = 'cpi-zoom-pct-label';
    zoomLabel.textContent = currentZoom + '%';

    const zoomInput = document.createElement('input');
    zoomInput.id = 'cpi-zoom-input';
    zoomInput.type = 'text';
    zoomInput.value = String(currentZoom);
    zoomInput.title = 'Enter zoom %';

    const btnSet = document.createElement('button');
    btnSet.id = 'cpi-zoom-set';
    btnSet.textContent = 'Set';
    btnSet.title = 'Save zoom to localStorage';

    zoomReadout.appendChild(zoomLabel);
    zoomReadout.appendChild(zoomInput);
    zoomReadout.appendChild(btnSet);
    panel.appendChild(zoomReadout);

    // ---- Header bar (title + gear) ----
    const header = document.createElement('div');
    header.id = 'cpi-header';

    const label = document.createElement('span');
    label.id = 'cpi-header-label';
    label.textContent = 'Prompt Injector';
    label.title = 'Show/Hide prompt buttons';

    const gearBtn = document.createElement('button');
    gearBtn.className = 'cpi-gear-btn';
    gearBtn.textContent = '\u2699';
    gearBtn.title = 'Edit prompts';

    header.appendChild(label);
    header.appendChild(gearBtn);
    panel.appendChild(header);

    // Grid container for 2-column button layout
    const grid = document.createElement('div');
    grid.id = 'cpi-grid';

    // Toggle grid visibility when clicking the label
    label.addEventListener('click', function () {
      grid.classList.toggle('cpi-hidden');
    });

    // ---- Zoom event handlers ----

    function updateZoomDisplay() {
      zoomLabel.textContent = currentZoom + '%';
      zoomInput.value = String(currentZoom);
    }

    pillMinus.addEventListener('click', function () {
      currentZoom = clampZoom(currentZoom - ZOOM_STEP);
      updateZoomDisplay();
      applyZoom(panel, currentZoom);
    });

    pillPlus.addEventListener('click', function () {
      currentZoom = clampZoom(currentZoom + ZOOM_STEP);
      updateZoomDisplay();
      applyZoom(panel, currentZoom);
    });

    btnSet.addEventListener('click', function () {
      var parsed = parseInt(zoomInput.value, 10);
      if (!isNaN(parsed)) {
        currentZoom = clampZoom(parsed);
        updateZoomDisplay();
        applyZoom(panel, currentZoom);
      }
      localStorage.setItem(ZOOM_STORAGE_KEY, String(currentZoom));
    });

    zoomInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        btnSet.click();
      }
    });

    // Helper: populate grid with buttons from activePrompts
    function rebuildGrid() {
      // Remove all children from grid
      while (grid.firstChild) {
        grid.removeChild(grid.firstChild);
      }

      activePrompts.forEach(function (p) {
        var btn = document.createElement('button');
        btn.className = 'cpi-btn';
        btn.title = 'Click to inject: ' + p.title;

        var numSpan = document.createElement('span');
        numSpan.className = 'cpi-btn-num';
        numSpan.textContent = String(p.id);

        var titleSpan = document.createElement('span');
        titleSpan.className = 'cpi-btn-title';
        titleSpan.textContent = p.title;

        btn.appendChild(numSpan);
        btn.appendChild(titleSpan);

        btn.addEventListener('click', function () {
          var ok = injectPrompt(p.prompt);
          if (ok) {
            btn.classList.add('cpi-flash');
            setTimeout(function () { btn.classList.remove('cpi-flash'); }, 400);
          } else {
            btn.style.borderColor = '#ff4444';
            setTimeout(function () { btn.style.borderColor = '#333'; }, 800);
          }
        });
        grid.appendChild(btn);
      });
    }

    rebuildGrid();

    // Callback after editor save or reset: rebuild grid and flash header
    function onEditorChange() {
      rebuildGrid();
      header.classList.add('cpi-flash');
      setTimeout(function () { header.classList.remove('cpi-flash'); }, 400);
    }

    gearBtn.addEventListener('click', function () {
      showEditor(onEditorChange, onEditorChange);
    });

    panel.appendChild(grid);
    document.body.appendChild(panel);

    // Apply saved zoom on load
    applyZoom(panel, currentZoom);

    return panel;
  }


  // ================================================================
  // SECTION: BUILD PHASE FORGE PANEL
  // ================================================================

  /**
   * Creates a collapsible section for the Phase Forge panel.
   * @param {string} titleText - Section title
   * @param {boolean} locked - Whether section is locked
   * @param {string} lockReason - Tooltip for the lock icon
   * @returns {{ section: HTMLElement, body: HTMLElement, setLocked: function, setExpanded: function }}
   */
  function createSection(titleText, locked, lockReason) {
    var section = document.createElement('div');
    section.className = 'pf-section' + (locked ? ' pf-locked' : '');

    var headerEl = document.createElement('div');
    headerEl.className = 'pf-section-header';

    var chevron = document.createElement('span');
    chevron.className = 'pf-section-chevron';
    chevron.textContent = '\u25B6';

    var titleEl = document.createElement('span');
    titleEl.className = 'pf-section-title';
    titleEl.textContent = titleText;

    var lockIcon = document.createElement('span');
    lockIcon.className = 'pf-section-lock';
    lockIcon.textContent = locked ? '\uD83D\uDD12' : '';
    lockIcon.title = lockReason || '';

    headerEl.appendChild(chevron);
    headerEl.appendChild(titleEl);
    headerEl.appendChild(lockIcon);

    var body = document.createElement('div');
    body.className = 'pf-section-body';

    section.appendChild(headerEl);
    section.appendChild(body);

    var expanded = false;

    headerEl.addEventListener('click', function () {
      if (section.classList.contains('pf-locked')) return;
      expanded = !expanded;
      if (expanded) {
        chevron.classList.add('pf-expanded');
        body.classList.add('pf-visible');
      } else {
        chevron.classList.remove('pf-expanded');
        body.classList.remove('pf-visible');
      }
    });

    return {
      section: section,
      body: body,
      setLocked: function (isLocked, reason) {
        if (isLocked) {
          section.classList.add('pf-locked');
          lockIcon.textContent = '\uD83D\uDD12';
          lockIcon.title = reason || '';
        } else {
          section.classList.remove('pf-locked');
          lockIcon.textContent = '';
          lockIcon.title = '';
        }
      },
      setExpanded: function (expand) {
        expanded = expand;
        if (expanded) {
          chevron.classList.add('pf-expanded');
          body.classList.add('pf-visible');
        } else {
          chevron.classList.remove('pf-expanded');
          body.classList.remove('pf-visible');
        }
      }
    };
  }

  /**
   * Builds the entire Phase Forge panel and attaches it to the DOM.
   * Returns references to key elements for external updates.
   */
  function buildPhaseForgePanel() {
    // ---- Toggle Button (floating PF circle) ----
    var toggleBtn = document.createElement('button');
    toggleBtn.id = 'pf-toggle-btn';
    toggleBtn.textContent = 'PF';
    toggleBtn.title = 'Toggle Phase Forge panel';
    toggleBtn.className = pfState.panelOpen ? 'pf-open' : 'pf-closed';
    document.body.appendChild(toggleBtn);

    // ---- Main Panel ----
    var panel = document.createElement('div');
    panel.id = 'pf-panel';
    if (!pfState.panelOpen) {
      panel.classList.add('pf-hidden');
    }

    // Panel header
    var panelHeader = document.createElement('div');
    panelHeader.id = 'pf-panel-header';

    var panelTitle = document.createElement('span');
    panelTitle.id = 'pf-panel-title';
    panelTitle.textContent = 'PHASE FORGE';

    var projectInput = document.createElement('input');
    projectInput.id = 'pf-project-input';
    projectInput.type = 'text';
    projectInput.placeholder = 'Project name...';
    projectInput.value = pfState.projectName;

    projectInput.addEventListener('change', function () {
      pfState.projectName = projectInput.value;
      pfPersist();
    });

    panelHeader.appendChild(panelTitle);
    panelHeader.appendChild(projectInput);
    panel.appendChild(panelHeader);

    // Panel body (scrollable)
    var panelBody = document.createElement('div');
    panelBody.id = 'pf-panel-body';

    // ============================================================
    // SECTION 1: PRD BUILDER
    // ============================================================
    var prdSection = createSection('1. PRD Builder', false, '');

    // Pill toggle: Questionnaire | Rant Mode
    var pillToggle = document.createElement('div');
    pillToggle.className = 'pf-pill-toggle';

    var pillQuestionnaire = document.createElement('button');
    pillQuestionnaire.className = 'pf-pill-option' + (pfState.prdMode === 'questionnaire' ? ' pf-active' : '');
    pillQuestionnaire.textContent = 'Questionnaire';

    var pillRant = document.createElement('button');
    pillRant.className = 'pf-pill-option' + (pfState.prdMode === 'rant' ? ' pf-active' : '');
    pillRant.textContent = 'Rant Mode';

    pillToggle.appendChild(pillQuestionnaire);
    pillToggle.appendChild(pillRant);
    prdSection.body.appendChild(pillToggle);

    pillQuestionnaire.addEventListener('click', function () {
      pfState.prdMode = 'questionnaire';
      pillQuestionnaire.classList.add('pf-active');
      pillRant.classList.remove('pf-active');
    });

    pillRant.addEventListener('click', function () {
      pfState.prdMode = 'rant';
      pillRant.classList.add('pf-active');
      pillQuestionnaire.classList.remove('pf-active');
    });

    // PRD status display
    var prdStatus = document.createElement('div');
    prdStatus.className = 'pf-status pf-status-info';
    prdStatus.textContent = 'Ready to start PRD creation';

    function updatePrdStatus(text, type) {
      prdStatus.className = 'pf-status pf-status-' + (type || 'info');
      prdStatus.textContent = text;
    }

    prdSection.body.appendChild(prdStatus);

    // PRD captured indicator
    var prdCapturedIndicator = document.createElement('div');
    prdCapturedIndicator.className = 'pf-status pf-status-success';
    prdCapturedIndicator.textContent = 'PRD Captured \u2713';
    prdCapturedIndicator.style.display = pfState.prdCaptured ? 'flex' : 'none';
    prdSection.body.appendChild(prdCapturedIndicator);

    // Button row: Start / Next / Reset
    var prdBtnRow = document.createElement('div');
    prdBtnRow.className = 'pf-btn-row';

    var prdStartBtn = document.createElement('button');
    prdStartBtn.className = 'pf-btn pf-btn-primary';
    prdStartBtn.textContent = 'Start';

    var prdNextBtn = document.createElement('button');
    prdNextBtn.className = 'pf-btn';
    prdNextBtn.textContent = 'Next';
    prdNextBtn.disabled = true;

    var prdResetBtn = document.createElement('button');
    prdResetBtn.className = 'pf-btn';
    prdResetBtn.textContent = 'Reset PRD';

    prdBtnRow.appendChild(prdStartBtn);
    prdBtnRow.appendChild(prdNextBtn);
    prdBtnRow.appendChild(prdResetBtn);
    prdSection.body.appendChild(prdBtnRow);

    // PRD Start handler
    prdStartBtn.addEventListener('click', function () {
      var prompt = '';
      if (pfState.prdMode === 'questionnaire') {
        prompt = 'I\'m building a new app. Here are the details:\n\n' +
          '**Temporary Build Name:** (just for identification, NOT your final product name - we\'ll pick a real name later)\n' +
          '**What is it?** \n' +
          '**Who is it for?**\n' +
          '**What problem does it solve?**\n' +
          '**Why would anyone care about this?**\n' +
          '**Core features (list them):**\n' +
          '**How does it work (basic user flow)?**\n\n' +
          'Please fill in as much as you can, then click the NEXT button in the Phase Forge panel.';
      } else {
        prompt = 'I\'m going to describe my app idea freely. It might be messy, out of order, or incomplete. ' +
          'Just listen, absorb everything. Don\'t organize yet, don\'t interrupt. When I\'m done, I\'ll click NEXT in the Phase Forge panel.';
      }

      var ok = injectPrompt(prompt);
      if (ok) {
        pfState.prdStep = 1;
        prdNextBtn.disabled = false;
        updatePrdStatus('Step 1 - Waiting for your input...', 'info');
        // Start watching for PRD markers
        startPrdWatcher(function (prdText) {
          pfState.prd = prdText;
          pfState.prdCaptured = true;
          pfPersist();
          prdCapturedIndicator.style.display = 'flex';
          updatePrdStatus('PRD captured successfully!', 'success');
          // Unlock configure section
          configSection.setLocked(false);
          refreshPhasesLock();
        });
      }
    });

    // PRD Next handler
    prdNextBtn.addEventListener('click', function () {
      pfState.prdStep++;
      var stepNum = pfState.prdStep;
      var prompt = '';

      if (pfState.prdMode === 'rant' && stepNum === 2) {
        // First "next" after rant -- ask Claude to organize
        prompt = 'Now take everything I said and:\n' +
          '1) Organize into structured PRD format\n' +
          '2) Show what you understood\n' +
          '3) Rate completeness %\n' +
          '4) Ask targeted follow-up questions for gaps only\n\n' +
          'If the PRD is complete (90%+ coverage), output it between these exact markers:\n' +
          '=== PRD READY ===\n[the PRD]\n=== END PRD ===';
      } else {
        // Analysis/follow-up prompt
        prompt = 'Based on everything provided so far:\n\n' +
          '1) Rate the PRD completeness (0-100%)\n' +
          '2) If below 90%, ask the 2-3 most critical missing questions\n' +
          '3) If 90% or above, output the final PRD between these exact markers:\n\n' +
          '=== PRD READY ===\n[Complete, structured PRD with all sections]\n=== END PRD ===\n\n' +
          'Be thorough but concise. The PRD should cover: app identity, target users, core features, user flows, technical requirements, and success metrics.';
      }

      injectPrompt(prompt);
      updatePrdStatus('Step ' + stepNum + ' - Processing follow-up...', 'info');
    });

    // PRD Reset handler
    prdResetBtn.addEventListener('click', function () {
      pfState.prd = '';
      pfState.prdCaptured = false;
      pfState.prdStep = 0;
      pfPersist();
      prdCapturedIndicator.style.display = 'none';
      prdNextBtn.disabled = true;
      updatePrdStatus('Ready to start PRD creation', 'info');
      stopPrdWatcher();
      // Re-lock downstream sections
      configSection.setLocked(true, 'Capture PRD first');
      phasesSection.setLocked(true, 'Configure build first');
      runSection.setLocked(true, 'Define phases first');
    });

    panelBody.appendChild(prdSection.section);

    // ============================================================
    // SECTION 2: CONFIGURE BUILD
    // ============================================================
    var configSection = createSection('2. Configure Build', !pfState.prdCaptured, 'Capture PRD first');

    // Model dropdown
    var modelGroup = document.createElement('div');
    modelGroup.className = 'pf-group';

    var modelLabel = document.createElement('label');
    modelLabel.className = 'pf-label';
    modelLabel.textContent = 'Model';

    var modelSelect = document.createElement('select');
    modelSelect.className = 'pf-select';

    var modelKeys = Object.keys(MODELS);
    modelKeys.forEach(function (key) {
      var opt = document.createElement('option');
      opt.value = key;
      opt.textContent = MODELS[key].label;
      if (key === pfState.config.model) opt.selected = true;
      modelSelect.appendChild(opt);
    });

    // Custom token input (shown only when "custom" is selected)
    var customTokenGroup = document.createElement('div');
    customTokenGroup.className = 'pf-group';
    customTokenGroup.style.display = pfState.config.model === 'custom' ? 'block' : 'none';

    var customTokenLabel = document.createElement('label');
    customTokenLabel.className = 'pf-label';
    customTokenLabel.textContent = 'Custom Token Count';

    var customTokenInput = document.createElement('input');
    customTokenInput.className = 'pf-input';
    customTokenInput.type = 'number';
    customTokenInput.min = '10000';
    customTokenInput.max = '10000000';
    customTokenInput.value = String(MODELS['custom'].tokens);

    customTokenGroup.appendChild(customTokenLabel);
    customTokenGroup.appendChild(customTokenInput);

    modelSelect.addEventListener('change', function () {
      pfState.config.model = modelSelect.value;
      customTokenGroup.style.display = modelSelect.value === 'custom' ? 'block' : 'none';
      pfPersist();
      refreshBudgetDisplay();
    });

    customTokenInput.addEventListener('change', function () {
      var val = parseInt(customTokenInput.value, 10);
      if (!isNaN(val) && val > 0) {
        MODELS['custom'].tokens = val;
        pfPersist();
        refreshBudgetDisplay();
      }
    });

    modelGroup.appendChild(modelLabel);
    modelGroup.appendChild(modelSelect);
    configSection.body.appendChild(modelGroup);
    configSection.body.appendChild(customTokenGroup);

    // Context % slider
    var sliderGroup = document.createElement('div');
    sliderGroup.className = 'pf-group';

    var sliderLabel = document.createElement('label');
    sliderLabel.className = 'pf-label';
    sliderLabel.textContent = 'Context Window Budget';

    var sliderRow = document.createElement('div');
    sliderRow.className = 'pf-slider-row';

    var slider = document.createElement('input');
    slider.className = 'pf-slider';
    slider.type = 'range';
    slider.min = '35';
    slider.max = '65';
    slider.value = String(pfState.config.contextPercent);

    var sliderVal = document.createElement('span');
    sliderVal.className = 'pf-slider-val';
    sliderVal.textContent = pfState.config.contextPercent + '%';

    slider.addEventListener('input', function () {
      pfState.config.contextPercent = parseInt(slider.value, 10);
      sliderVal.textContent = pfState.config.contextPercent + '%';
      pfPersist();
      refreshBudgetDisplay();
    });

    sliderRow.appendChild(slider);
    sliderRow.appendChild(sliderVal);
    sliderGroup.appendChild(sliderLabel);
    sliderGroup.appendChild(sliderRow);
    configSection.body.appendChild(sliderGroup);

    // Agent Role checkboxes
    var rolesGroup = document.createElement('div');
    rolesGroup.className = 'pf-group';

    var rolesLabel = document.createElement('label');
    rolesLabel.className = 'pf-label';
    rolesLabel.textContent = 'Agent Roles';

    rolesGroup.appendChild(rolesLabel);

    var roleEntries = [
      { key: 'builder', label: 'Builder', pct: '40%', disabled: true },
      { key: 'reviewer', label: 'Reviewer', pct: '8%', disabled: false },
      { key: 'architect', label: 'Architect', pct: '8%', disabled: false },
      { key: 'tester', label: 'Tester (tests prev phase)', pct: '15%', disabled: false },
      { key: 'planner', label: 'Planner (scouts next)', pct: '5%', disabled: false }
    ];

    roleEntries.forEach(function (entry) {
      var row = document.createElement('div');
      row.className = 'pf-check-row';

      var lbl = document.createElement('label');
      if (entry.disabled) lbl.classList.add('pf-disabled');

      var cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.checked = pfState.config.roles[entry.key];
      if (entry.disabled) cb.disabled = true;

      var txt = document.createTextNode(entry.label);

      var pctSpan = document.createElement('span');
      pctSpan.className = 'pf-budget-pct';
      pctSpan.textContent = entry.pct;

      lbl.appendChild(cb);
      lbl.appendChild(txt);
      row.appendChild(lbl);
      row.appendChild(pctSpan);
      rolesGroup.appendChild(row);

      if (!entry.disabled) {
        cb.addEventListener('change', function () {
          pfState.config.roles[entry.key] = cb.checked;
          pfPersist();
          refreshBudgetDisplay();
        });
      }
    });

    configSection.body.appendChild(rolesGroup);

    // Token Budget Display
    var budgetDisplay = document.createElement('div');
    budgetDisplay.className = 'pf-token-budget';
    configSection.body.appendChild(budgetDisplay);

    function refreshBudgetDisplay() {
      var b = calculateBudget();
      var lines = [];
      lines.push('<strong>Available:</strong> ' + formatTokens(b.available) + ' of ' + formatTokens(b.total));
      for (var role in b.roles) {
        var roleName = role.charAt(0).toUpperCase() + role.slice(1);
        lines.push('<strong>' + roleName + ':</strong> ' + formatTokens(b.roles[role]));
      }
      lines.push('<strong>Buffer:</strong> ' + formatTokens(b.buffer));
      lines.push('<strong>Overhead:</strong> ' + formatTokens(b.overhead));
      budgetDisplay.innerHTML = lines.join(' | ');
    }

    refreshBudgetDisplay();

    // Shared Assets
    var divider = document.createElement('hr');
    divider.className = 'pf-divider';
    configSection.body.appendChild(divider);

    var assetsLabel = document.createElement('label');
    assetsLabel.className = 'pf-label';
    assetsLabel.textContent = 'Shared Assets';
    configSection.body.appendChild(assetsLabel);

    // Testing Script textarea
    var testGroup = document.createElement('div');
    testGroup.className = 'pf-group';

    var testLabel = document.createElement('label');
    testLabel.className = 'pf-label';
    testLabel.textContent = 'Testing Script ({{TESTING_SCRIPT}})';
    testLabel.style.fontSize = '9px';

    var testArea = document.createElement('textarea');
    testArea.className = 'pf-textarea';
    testArea.placeholder = 'Paste your testing script here. It will be appended to every phase via {{TESTING_SCRIPT}} placeholder.';
    testArea.value = pfState.sharedAssets.testingScript;

    testArea.addEventListener('change', function () {
      pfState.sharedAssets.testingScript = testArea.value;
      pfPersist();
    });

    testGroup.appendChild(testLabel);
    testGroup.appendChild(testArea);
    configSection.body.appendChild(testGroup);

    // Architecture Doc textarea
    var archGroup = document.createElement('div');
    archGroup.className = 'pf-group';

    var archLabel = document.createElement('label');
    archLabel.className = 'pf-label';
    archLabel.textContent = 'Architecture Doc ({{ARCHITECTURE_DOC}})';
    archLabel.style.fontSize = '9px';

    var archArea = document.createElement('textarea');
    archArea.className = 'pf-textarea';
    archArea.placeholder = 'Paste architecture document here. Grows each phase. Referenced via {{ARCHITECTURE_DOC}} placeholder.';
    archArea.value = pfState.sharedAssets.architectureDoc;

    archArea.addEventListener('change', function () {
      pfState.sharedAssets.architectureDoc = archArea.value;
      pfPersist();
    });

    archGroup.appendChild(archLabel);
    archGroup.appendChild(archArea);
    configSection.body.appendChild(archGroup);

    panelBody.appendChild(configSection.section);


    // ============================================================
    // SECTION 3: PHASES
    // ============================================================
    var hasConfig = pfState.prdCaptured; // phases unlocked when PRD is captured and config exists
    var hasPhases = pfState.phases.length > 0;
    var phasesSection = createSection('3. Phases', !hasConfig, 'Configure build first');

    // Phase count estimate
    var phaseEstimate = document.createElement('div');
    phaseEstimate.className = 'pf-status pf-status-info';

    function refreshPhaseEstimate() {
      if (pfState.prd.length > 0) {
        var budget = calculateBudget();
        var builderBudget = budget.builder || budget.available * 0.4;
        // Rough estimate: ~3 chars per token for PRD text, factor in code expansion
        var prdTokens = Math.ceil(pfState.prd.length / 3);
        var estimatedPhases = Math.max(1, Math.ceil(prdTokens / (builderBudget * 0.6)));
        phaseEstimate.textContent = 'Estimated phases needed: ~' + estimatedPhases + ' (based on PRD size + builder budget)';
      } else {
        phaseEstimate.textContent = 'Capture a PRD to estimate phases';
      }
    }

    refreshPhaseEstimate();
    phasesSection.body.appendChild(phaseEstimate);

    // Import button
    var importGroup = document.createElement('div');
    importGroup.className = 'pf-group';

    var importBtn = document.createElement('button');
    importBtn.className = 'pf-btn';
    importBtn.textContent = 'Import Phases';
    importBtn.title = 'Paste a document with --- PHASE 1 ---, --- PHASE 2 --- etc. markers';

    var autoCalcBtn = document.createElement('button');
    autoCalcBtn.className = 'pf-btn';
    autoCalcBtn.textContent = 'Auto-Calculate';
    autoCalcBtn.title = 'Ask AI to split the PRD into phases';

    var addPhaseBtn = document.createElement('button');
    addPhaseBtn.className = 'pf-btn';
    addPhaseBtn.textContent = '+ Phase';
    addPhaseBtn.title = 'Add a new empty phase';

    var importRow = document.createElement('div');
    importRow.className = 'pf-btn-row';
    importRow.appendChild(importBtn);
    importRow.appendChild(autoCalcBtn);
    importRow.appendChild(addPhaseBtn);
    phasesSection.body.appendChild(importRow);

    // Phase list container
    var phaseListEl = document.createElement('div');
    phaseListEl.style.marginTop = '8px';
    phasesSection.body.appendChild(phaseListEl);

    /** Rebuild the phase list UI from pfState.phases */
    function refreshPhaseList() {
      while (phaseListEl.firstChild) {
        phaseListEl.removeChild(phaseListEl.firstChild);
      }

      pfState.phases.forEach(function (phase, idx) {
        var item = document.createElement('div');
        item.className = 'pf-phase-item';
        if (pfState.runner.status === 'running' && pfState.runner.currentPhase === idx) {
          item.classList.add('pf-phase-active');
        }

        var numEl = document.createElement('span');
        numEl.className = 'pf-phase-num';
        numEl.textContent = String(idx + 1);

        var statusEl = document.createElement('span');
        statusEl.className = 'pf-phase-status';
        var statusIcons = { pending: '\u2B1C', running: '\uD83D\uDD04', complete: '\u2705', failed: '\u274C' };
        statusEl.textContent = statusIcons[phase.status] || statusIcons.pending;

        var previewEl = document.createElement('span');
        previewEl.className = 'pf-phase-preview';
        previewEl.textContent = (phase.content || '').substring(0, 50) + ((phase.content || '').length > 50 ? '...' : '');

        item.appendChild(numEl);
        item.appendChild(statusEl);
        item.appendChild(previewEl);

        // Click to edit phase in modal
        item.addEventListener('click', function () {
          showPhaseEditModal(idx);
        });

        phaseListEl.appendChild(item);
      });

      // Update run section lock
      refreshRunLock();
    }

    refreshPhaseList();

    // Import handler -- shows a modal with a textarea for pasting
    importBtn.addEventListener('click', function () {
      showPhaseImportModal();
    });

    // Auto-calculate handler -- injects prompt asking AI to split PRD
    autoCalcBtn.addEventListener('click', function () {
      if (!pfState.prd) {
        updatePrdStatus('No PRD captured yet', 'warning');
        return;
      }
      var budget = calculateBudget();
      var prompt = 'I have a PRD for my project. I need you to split it into implementation phases.\n\n' +
        'Each phase should be a self-contained chunk of work that can be built independently.\n' +
        'My builder budget per phase is approximately ' + formatTokens(budget.builder) + ' tokens.\n\n' +
        'Please output the phases in this EXACT format (one per phase):\n\n' +
        '--- PHASE 1 ---\n[Phase 1 content - what to build]\n\n' +
        '--- PHASE 2 ---\n[Phase 2 content]\n\n' +
        '(continue for all phases)\n\n' +
        'Here is the PRD:\n\n' + pfState.prd;
      injectPrompt(prompt);
    });

    // Add empty phase
    addPhaseBtn.addEventListener('click', function () {
      pfState.phases.push({ content: '', status: 'pending' });
      pfPersist();
      refreshPhaseList();
    });

    panelBody.appendChild(phasesSection.section);

    // ============================================================
    // SECTION 4: RUN
    // ============================================================
    var runSection = createSection('4. Run', !hasPhases, 'Define phases first');

    // Run controls row
    var runControlRow = document.createElement('div');
    runControlRow.className = 'pf-btn-row';
    runControlRow.style.justifyContent = 'center';

    var runStartBtn = document.createElement('button');
    runStartBtn.className = 'pf-btn pf-btn-primary';
    runStartBtn.textContent = '\u25B6 Start';

    var runPauseBtn = document.createElement('button');
    runPauseBtn.className = 'pf-btn';
    runPauseBtn.textContent = '\u23F8 Pause';
    runPauseBtn.disabled = true;

    var runStopBtn = document.createElement('button');
    runStopBtn.className = 'pf-btn';
    runStopBtn.textContent = '\u23F9 Stop';
    runStopBtn.disabled = true;

    runControlRow.appendChild(runStartBtn);
    runControlRow.appendChild(runPauseBtn);
    runControlRow.appendChild(runStopBtn);
    runSection.body.appendChild(runControlRow);

    // Progress bar
    var progressOuter = document.createElement('div');
    progressOuter.className = 'pf-progress-bar-outer';

    var progressInner = document.createElement('div');
    progressInner.className = 'pf-progress-bar-inner';
    progressInner.style.width = '0%';

    progressOuter.appendChild(progressInner);
    runSection.body.appendChild(progressOuter);

    // Status text
    var runStatusText = document.createElement('div');
    runStatusText.className = 'pf-run-status';
    runStatusText.textContent = 'Ready to run';
    runSection.body.appendChild(runStatusText);

    function refreshRunProgress() {
      var total = pfState.phases.length;
      var completed = pfState.phases.filter(function (p) { return p.status === 'complete'; }).length;
      var pct = total > 0 ? Math.round((completed / total) * 100) : 0;
      progressInner.style.width = pct + '%';

      if (pfState.runner.status === 'running') {
        runStatusText.textContent = 'Phase ' + (pfState.runner.currentPhase + 1) + '/' + total + ' - Running...';
        runStatusText.className = 'pf-run-status';
      } else if (pfState.runner.status === 'paused') {
        runStatusText.textContent = 'Paused at Phase ' + (pfState.runner.currentPhase + 1) + '/' + total;
        runStatusText.className = 'pf-run-status';
      } else if (completed === total && total > 0) {
        runStatusText.textContent = 'Build Complete!';
        runStatusText.className = 'pf-run-complete';
      } else {
        runStatusText.textContent = completed + '/' + total + ' phases complete';
        runStatusText.className = 'pf-run-status';
      }
    }

    refreshRunProgress();

    // ---- Auto-Send Runner Logic ----

    var runnerActive = false;

    /**
     * Executes a single phase: inject prompt, send, wait for completion.
     * @param {number} phaseIdx - Zero-based index of the phase to run
     * @returns {Promise<boolean>} Whether the phase completed
     */
    function executeSinglePhase(phaseIdx) {
      return new Promise(function (resolve) {
        if (phaseIdx < 0 || phaseIdx >= pfState.phases.length) {
          resolve(false);
          return;
        }

        // Mark phase as running
        pfState.phases[phaseIdx].status = 'running';
        pfState.runner.currentPhase = phaseIdx;
        pfState.runner.status = 'running';
        pfPersist();
        refreshPhaseList();
        refreshRunProgress();

        // Build the full prompt
        var fullPrompt = buildPhasePrompt(phaseIdx);

        // Inject into editor
        var injected = injectPrompt(fullPrompt);
        if (!injected) {
          pfState.phases[phaseIdx].status = 'failed';
          pfPersist();
          refreshPhaseList();
          refreshRunProgress();
          resolve(false);
          return;
        }

        // Wait 500ms then click send
        setTimeout(function () {
          var sent = clickSendButton();
          if (!sent) {
            // Try again after a short delay
            setTimeout(function () {
              var retrySent = clickSendButton();
              if (!retrySent) {
                pfState.phases[phaseIdx].status = 'failed';
                pfPersist();
                refreshPhaseList();
                refreshRunProgress();
                resolve(false);
                return;
              }
              waitForCompletion(phaseIdx, resolve);
            }, 1000);
            return;
          }
          waitForCompletion(phaseIdx, resolve);
        }, 500);
      });
    }

    function waitForCompletion(phaseIdx, resolve) {
      // Wait for response to complete
      waitForResponseComplete(4000, 300000).then(function (completed) {
        if (completed) {
          pfState.phases[phaseIdx].status = 'complete';
        } else {
          // Timeout -- mark as failed
          pfState.phases[phaseIdx].status = 'failed';
        }
        pfPersist();
        refreshPhaseList();
        refreshRunProgress();
        resolve(completed);
      });
    }

    /**
     * Main runner loop. Iterates through phases sequentially.
     */
    function runLoop() {
      if (!runnerActive) return;

      var currentIdx = pfState.runner.currentPhase;

      // Find next pending phase starting from currentIdx
      while (currentIdx < pfState.phases.length && pfState.phases[currentIdx].status === 'complete') {
        currentIdx++;
      }

      if (currentIdx >= pfState.phases.length) {
        // All done
        pfState.runner.status = 'stopped';
        runnerActive = false;
        pfPersist();
        refreshRunProgress();
        refreshRunButtons();
        return;
      }

      // Check if paused
      if (pfState.runner.status === 'paused') {
        runnerActive = false;
        refreshRunButtons();
        return;
      }

      pfState.runner.currentPhase = currentIdx;

      executeSinglePhase(currentIdx).then(function (success) {
        if (!runnerActive) return;

        if (success) {
          // Wait 2 seconds then move to next phase
          setTimeout(function () {
            pfState.runner.currentPhase = currentIdx + 1;
            pfPersist();
            runLoop();
          }, 2000);
        } else {
          // Phase failed -- check for retry indicators or stop
          pfState.runner.status = 'stopped';
          runnerActive = false;
          pfPersist();
          refreshRunProgress();
          refreshRunButtons();
          runStatusText.textContent = 'Phase ' + (currentIdx + 1) + ' failed. Fix and retry.';
        }
      });
    }

    function refreshRunButtons() {
      var isRunning = pfState.runner.status === 'running';
      var isPaused = pfState.runner.status === 'paused';
      runStartBtn.disabled = isRunning;
      runPauseBtn.disabled = !isRunning;
      runStopBtn.disabled = !isRunning && !isPaused;
      runStartBtn.textContent = isPaused ? '\u25B6 Resume' : '\u25B6 Start';
    }

    refreshRunButtons();

    // Start button
    runStartBtn.addEventListener('click', function () {
      if (pfState.phases.length === 0) return;

      runnerActive = true;
      pfState.runner.status = 'running';

      // If resuming from paused, keep current phase
      // If starting fresh, find first non-complete phase
      if (pfState.runner.currentPhase >= pfState.phases.length) {
        pfState.runner.currentPhase = 0;
      }

      pfPersist();
      refreshRunButtons();
      runLoop();
    });

    // Pause button
    runPauseBtn.addEventListener('click', function () {
      pfState.runner.status = 'paused';
      pfPersist();
      refreshRunProgress();
      refreshRunButtons();
    });

    // Stop button
    runStopBtn.addEventListener('click', function () {
      runnerActive = false;
      pfState.runner.status = 'stopped';
      pfPersist();
      refreshRunProgress();
      refreshRunButtons();
    });

    panelBody.appendChild(runSection.section);

    // ---- Assemble panel ----
    panel.appendChild(panelBody);
    document.body.appendChild(panel);

    // ---- Section lock refresh helpers ----

    function refreshPhasesLock() {
      var unlocked = pfState.prdCaptured;
      phasesSection.setLocked(!unlocked, 'Capture PRD first');
      refreshPhaseEstimate();
      refreshRunLock();
    }

    function refreshRunLock() {
      var unlocked = pfState.phases.length > 0;
      runSection.setLocked(!unlocked, 'Define phases first');
    }

    // ---- Toggle Panel ----

    toggleBtn.addEventListener('click', function () {
      pfState.panelOpen = !pfState.panelOpen;
      pfPersist();

      if (pfState.panelOpen) {
        panel.classList.remove('pf-hidden');
        toggleBtn.classList.remove('pf-closed');
        toggleBtn.classList.add('pf-open');
      } else {
        panel.classList.add('pf-hidden');
        toggleBtn.classList.remove('pf-open');
        toggleBtn.classList.add('pf-closed');
      }

      // Shift prompt injector panel
      var cpiPanel = document.getElementById('cpi-panel');
      if (cpiPanel) {
        if (pfState.panelOpen) {
          cpiPanel.classList.add('cpi-shifted');
        } else {
          cpiPanel.classList.remove('cpi-shifted');
        }
      }
    });

    return {
      refreshPhaseList: refreshPhaseList,
      refreshRunProgress: refreshRunProgress,
      refreshPhasesLock: refreshPhasesLock
    };
  }


  // ================================================================
  // SECTION: PHASE EDIT MODAL
  // Opens a modal to edit a single phase's content.
  // ================================================================

  /**
   * Shows a modal to edit the content of phase at given index.
   * @param {number} phaseIdx - Zero-based phase index
   */
  function showPhaseEditModal(phaseIdx) {
    if (document.getElementById('pf-phase-modal-overlay')) return;
    if (phaseIdx < 0 || phaseIdx >= pfState.phases.length) return;

    var overlay = document.createElement('div');
    overlay.id = 'pf-phase-modal-overlay';

    var modal = document.createElement('div');
    modal.id = 'pf-phase-modal';

    // Header
    var header = document.createElement('div');
    header.id = 'pf-phase-modal-header';

    var titleSpan = document.createElement('span');
    titleSpan.textContent = 'Edit Phase ' + (phaseIdx + 1);

    var closeBtn = document.createElement('button');
    closeBtn.className = 'cpi-editor-btn--close';
    closeBtn.textContent = '\u00D7';
    closeBtn.title = 'Close';

    header.appendChild(titleSpan);
    header.appendChild(closeBtn);
    modal.appendChild(header);

    // Body
    var body = document.createElement('div');
    body.id = 'pf-phase-modal-body';

    var textarea = document.createElement('textarea');
    textarea.value = pfState.phases[phaseIdx].content || '';
    textarea.placeholder = 'Enter phase content...';

    body.appendChild(textarea);
    modal.appendChild(body);

    // Footer
    var footer = document.createElement('div');
    footer.id = 'pf-phase-modal-footer';

    var deleteBtn = document.createElement('button');
    deleteBtn.className = 'pf-btn';
    deleteBtn.textContent = 'Delete Phase';
    deleteBtn.style.color = '#ff4444';
    deleteBtn.style.borderColor = '#ff4444';

    var saveBtn = document.createElement('button');
    saveBtn.className = 'pf-btn pf-btn-primary';
    saveBtn.textContent = 'Save';

    var cancelBtn = document.createElement('button');
    cancelBtn.className = 'pf-btn';
    cancelBtn.textContent = 'Cancel';

    footer.appendChild(deleteBtn);
    // Spacer
    var spacer = document.createElement('div');
    spacer.style.flex = '1';
    footer.appendChild(spacer);
    footer.appendChild(cancelBtn);
    footer.appendChild(saveBtn);
    modal.appendChild(footer);

    overlay.appendChild(modal);

    function closeModal() {
      overlay.remove();
    }

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeModal();
    });

    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    saveBtn.addEventListener('click', function () {
      pfState.phases[phaseIdx].content = textarea.value;
      pfPersist();
      closeModal();
      // Refresh the phase list if the PF panel refs are available
      var evt = new CustomEvent('pf-phases-changed');
      document.dispatchEvent(evt);
    });

    deleteBtn.addEventListener('click', function () {
      pfState.phases.splice(phaseIdx, 1);
      pfPersist();
      closeModal();
      var evt = new CustomEvent('pf-phases-changed');
      document.dispatchEvent(evt);
    });

    document.body.appendChild(overlay);

    // Focus the textarea
    setTimeout(function () { textarea.focus(); }, 100);
  }

  // ================================================================
  // SECTION: PHASE IMPORT MODAL
  // Shows a modal for pasting a multi-phase document.
  // ================================================================

  function showPhaseImportModal() {
    if (document.getElementById('pf-phase-modal-overlay')) return;

    var overlay = document.createElement('div');
    overlay.id = 'pf-phase-modal-overlay';

    var modal = document.createElement('div');
    modal.id = 'pf-phase-modal';

    // Header
    var header = document.createElement('div');
    header.id = 'pf-phase-modal-header';

    var titleSpan = document.createElement('span');
    titleSpan.textContent = 'Import Phases';

    var closeBtn = document.createElement('button');
    closeBtn.className = 'cpi-editor-btn--close';
    closeBtn.textContent = '\u00D7';

    header.appendChild(titleSpan);
    header.appendChild(closeBtn);
    modal.appendChild(header);

    // Body
    var body = document.createElement('div');
    body.id = 'pf-phase-modal-body';

    var hint = document.createElement('div');
    hint.style.color = '#999';
    hint.style.fontSize = '11px';
    hint.style.marginBottom = '8px';
    hint.textContent = 'Paste your document below. Use "--- PHASE 1 ---", "--- PHASE 2 ---" etc. as markers to separate phases.';
    body.appendChild(hint);

    var textarea = document.createElement('textarea');
    textarea.placeholder = '--- PHASE 1 ---\nFirst phase content...\n\n--- PHASE 2 ---\nSecond phase content...\n\n--- PHASE 3 ---\nThird phase content...';
    body.appendChild(textarea);
    modal.appendChild(body);

    // Footer
    var footer = document.createElement('div');
    footer.id = 'pf-phase-modal-footer';

    var importActionBtn = document.createElement('button');
    importActionBtn.className = 'pf-btn pf-btn-primary';
    importActionBtn.textContent = 'Import';

    var cancelBtn = document.createElement('button');
    cancelBtn.className = 'pf-btn';
    cancelBtn.textContent = 'Cancel';

    footer.appendChild(cancelBtn);
    footer.appendChild(importActionBtn);
    modal.appendChild(footer);

    overlay.appendChild(modal);

    function closeModal() {
      overlay.remove();
    }

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeModal();
    });

    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    importActionBtn.addEventListener('click', function () {
      var text = textarea.value;
      if (!text.trim()) {
        closeModal();
        return;
      }

      // Parse phases from the document using --- PHASE N --- markers
      var phaseRegex = /---\s*PHASE\s+\d+\s*---/gi;
      var markers = [];
      var match;
      while ((match = phaseRegex.exec(text)) !== null) {
        markers.push(match.index);
      }

      var newPhases = [];

      if (markers.length === 0) {
        // No markers found -- treat entire text as one phase
        newPhases.push({ content: text.trim(), status: 'pending' });
      } else {
        for (var i = 0; i < markers.length; i++) {
          var startIdx = markers[i];
          var endIdx = i + 1 < markers.length ? markers[i + 1] : text.length;
          var chunk = text.substring(startIdx, endIdx);
          // Remove the marker line itself
          var content = chunk.replace(/---\s*PHASE\s+\d+\s*---/i, '').trim();
          if (content.length > 0) {
            newPhases.push({ content: content, status: 'pending' });
          }
        }
      }

      if (newPhases.length > 0) {
        pfState.phases = newPhases;
        pfState.runner.currentPhase = 0;
        pfState.runner.status = 'stopped';
        pfPersist();
        var evt = new CustomEvent('pf-phases-changed');
        document.dispatchEvent(evt);
      }

      closeModal();
    });

    document.body.appendChild(overlay);
    setTimeout(function () { textarea.focus(); }, 100);
  }

  // ================================================================
  // SECTION: INITIALIZATION
  // Wait for page to be ready, then build both panels.
  // ================================================================

  var pfPanelRefs = null;

  function waitForPage() {
    var check = setInterval(function () {
      if (document.body) {
        clearInterval(check);

        // Build the Prompt Injector panel (left side / original)
        buildPanel();

        // Build the Phase Forge panel (right side / new)
        pfPanelRefs = buildPhaseForgePanel();

        // Listen for phase changes from modals
        document.addEventListener('pf-phases-changed', function () {
          if (pfPanelRefs) {
            pfPanelRefs.refreshPhaseList();
            pfPanelRefs.refreshRunProgress();
            pfPanelRefs.refreshPhasesLock();
          }
        });
      }
    }, 200);
  }

  waitForPage();

})();
