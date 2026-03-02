// ==UserScript==
// @name         Cloud Prompt Injector
// @namespace    https://github.com/digisurfsome/Greptacular
// @version      1.6
// @description  Floating sidebar with prompt buttons that inject into Claude/ChatGPT/Gemini chat input
// @author       AutoForge
// @match        https://claude.ai/*
// @match        https://chatgpt.com/*
// @match        https://chat.openai.com/*
// @match        https://gemini.google.com/*
// @grant        GM_info
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';
  console.log('[Prompt Injector v1.6] Script running in', GM_info.scriptHandler, 'on', window.location.href);

  // ============================================================
  // PROMPT DEFINITIONS — Edit these to change button content
  // ============================================================

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
1. Read \`AGENT_BRIEFING.md\` at project root — master architecture overview
2. Read \`docs/agent-briefs/{FEATURE_BRIEF}.md\` — specific to your task
### Step 2: Read ONLY Files You Will Edit
- Read ONLY the files listed in "Files You Will Modify" below
- Do NOT read files "just to understand" — the briefings cover that
- Do NOT read types.ts or api.ts in full — search for the specific interface/function you need
- Maximum 5 files read directly by you
### Step 3: Use Subagents for Everything Else
- **Need to understand how another component works?** → Spawn an Explore subagent
- **Need to find where something is imported?** → Spawn an Explore subagent
- **Need to check what pattern a similar component uses?** → Spawn an Explore subagent
- **Need to search for a string across the codebase?** → Spawn an Explore subagent
- NEVER run Glob/Grep yourself unless it's a single targeted search for a specific file
- The subagent's context is separate from yours — use this to your advantage
### Step 4: Context Budget
- Stop coding at 50% context usage
- If you hit 45%, wrap up current work, commit, and save progress notes
- Never start a new feature if you're above 40%
---
## Your Task
{DESCRIBE THE SPECIFIC TASK — be detailed about what to build, not how}
## Feature Brief to Read
docs/agent-briefs/{BRIEF_NAME}.md
## Files You Will Modify
- {path/to/file1}
- {path/to/file2}
- {path/to/file3}
## Files You Might Need to Reference (use subagent)
- {path/to/reference1} — {why you might need it}
- {path/to/reference2} — {why you might need it}
## Acceptance Criteria
- {What "done" looks like — specific, testable}
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

  // ============================================================
  // ZOOM STATE
  // ============================================================

  const ZOOM_STORAGE_KEY = 'cpi-zoom-level';
  const DEFAULT_ZOOM = 100;
  const ZOOM_STEP = 10;
  const ZOOM_MIN = 30;
  const ZOOM_MAX = 300;

  // ============================================================
  // PROMPT STORAGE
  // ============================================================

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
      // Corrupted data — fall back to defaults
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

  // ============================================================
  // STYLES
  // ============================================================

  const PANEL_WIDTH = 180;

  const styles = document.createElement('style');
  styles.textContent = `
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

    #cpi-zoom-controls {
      display: flex;
      align-items: center;
      gap: 2px;
      flex-shrink: 0;
    }

    .cpi-zoom-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 16px;
      height: 16px;
      background: #262624;
      color: #e0e0e0;
      border: 1px solid #555;
      border-radius: 3px;
      cursor: pointer;
      font-size: 10px;
      font-weight: 700;
      padding: 0;
      line-height: 1;
      transition: all 0.15s;
    }

    .cpi-zoom-btn:hover {
      background: #da7757;
      border-color: #da7757;
      color: #fff;
    }

    #cpi-zoom-input {
      width: 30px;
      height: 16px;
      background: #1e1e1c;
      color: #e0e0e0;
      border: 1px solid #555;
      border-radius: 3px;
      font-size: 8px;
      text-align: center;
      padding: 0 1px;
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
      height: 16px;
      background: #da7757;
      color: #fff;
      border: none;
      border-radius: 3px;
      cursor: pointer;
      font-size: 7px;
      font-weight: 700;
      padding: 0 4px;
      line-height: 1;
      transition: all 0.15s;
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
  `;

  function injectStyles() {
    if (document.head) {
      document.head.appendChild(styles);
    } else if (document.documentElement) {
      document.documentElement.appendChild(styles);
    }
    console.log('[Prompt Injector] Styles injected');
  }

  // ============================================================
  // INJECT TEXT INTO CHAT INPUT
  // ============================================================

  function getEditor() {
    // Claude.ai — ProseMirror contenteditable
    let el = document.querySelector('.ProseMirror[contenteditable="true"]');
    if (el) return { el, type: 'prosemirror' };

    el = document.querySelector('div[data-placeholder][contenteditable="true"]');
    if (el) return { el, type: 'prosemirror' };

    // ChatGPT — also contenteditable (ProseMirror)
    el = document.querySelector('#prompt-textarea');
    if (el) return { el, type: 'prosemirror' };

    // Gemini — contenteditable rich text
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

  function injectPrompt(text) {
    const editor = getEditor();
    if (!editor) {
      console.warn('[Prompt Injector] No chat input found on this page.');
      return false;
    }

    const { el, type } = editor;

    if (type === 'textarea') {
      // Simple textarea — set value and fire input event
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

  // ============================================================
  // ZOOM HELPERS
  // ============================================================

  function applyZoom(panel, zoom) {
    const scale = zoom / 100;
    panel.style.transform = `translateY(-50%) scale(${scale})`;
  }

  function clampZoom(value) {
    return Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, value));
  }

  // ============================================================
  // EDITOR OVERLAY
  // ============================================================

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
    activePrompts.forEach((p) => {
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
      inputs.push({ id: p.id, titleInput, textarea });
    });

    overlay.appendChild(editorPanel);

    // Close helper
    function closeOverlay() {
      overlay.remove();
    }

    // Close on overlay background click (not on panel itself)
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) closeOverlay();
    });

    closeBtn.addEventListener('click', closeOverlay);

    // Save
    saveBtn.addEventListener('click', () => {
      const updated = inputs.map((inp) => ({
        id: inp.id,
        title: inp.titleInput.value,
        prompt: inp.textarea.value
      }));
      const cleaned = saveCustomPrompts(updated);
      activePrompts = cleaned;
      closeOverlay();
      if (onSave) onSave(cleaned);
    });

    // Reset to defaults
    resetBtn.addEventListener('click', () => {
      localStorage.removeItem(PROMPT_STORAGE_KEY);
      activePrompts = PROMPTS.map((p) => ({ id: p.id, title: p.title, prompt: p.prompt }));
      closeOverlay();
      if (onReset) onReset();
    });

    document.body.appendChild(overlay);
  }

  // ============================================================
  // BUILD THE UI
  // ============================================================

  function buildPanel() {
    const panel = document.createElement('div');
    panel.id = 'cpi-panel';

    // Header bar — full-width, spans both columns
    const header = document.createElement('div');
    header.id = 'cpi-header';

    // Left side: clickable label to toggle grid
    const label = document.createElement('span');
    label.id = 'cpi-header-label';
    label.textContent = 'Prompt Injector';
    label.title = 'Show/Hide prompt buttons';

    // Right side: zoom controls
    const zoomControls = document.createElement('div');
    zoomControls.id = 'cpi-zoom-controls';

    const btnMinus = document.createElement('button');
    btnMinus.className = 'cpi-zoom-btn';
    btnMinus.textContent = '\u2212';
    btnMinus.title = 'Zoom out';

    const zoomInput = document.createElement('input');
    zoomInput.id = 'cpi-zoom-input';
    zoomInput.type = 'text';
    zoomInput.value = String(currentZoom);
    zoomInput.title = 'Current zoom %';

    const btnPlus = document.createElement('button');
    btnPlus.className = 'cpi-zoom-btn';
    btnPlus.textContent = '+';
    btnPlus.title = 'Zoom in';

    const btnSet = document.createElement('button');
    btnSet.id = 'cpi-zoom-set';
    btnSet.textContent = 'Set';
    btnSet.title = 'Save zoom to localStorage';

    zoomControls.appendChild(btnMinus);
    zoomControls.appendChild(zoomInput);
    zoomControls.appendChild(btnPlus);
    zoomControls.appendChild(btnSet);

    // Gear button — opens prompt editor overlay
    const gearBtn = document.createElement('button');
    gearBtn.className = 'cpi-gear-btn';
    gearBtn.textContent = '\u2699';
    gearBtn.title = 'Edit prompts';

    header.appendChild(label);
    header.appendChild(gearBtn);
    header.appendChild(zoomControls);
    panel.appendChild(header);

    // Grid container for 2-column button layout
    const grid = document.createElement('div');
    grid.id = 'cpi-grid';

    // Toggle grid visibility when clicking the label
    label.addEventListener('click', () => {
      grid.classList.toggle('cpi-hidden');
    });

    // Zoom: decrease by ZOOM_STEP
    btnMinus.addEventListener('click', () => {
      currentZoom = clampZoom(currentZoom - ZOOM_STEP);
      zoomInput.value = String(currentZoom);
      applyZoom(panel, currentZoom);
    });

    // Zoom: increase by ZOOM_STEP
    btnPlus.addEventListener('click', () => {
      currentZoom = clampZoom(currentZoom + ZOOM_STEP);
      zoomInput.value = String(currentZoom);
      applyZoom(panel, currentZoom);
    });

    // Zoom: save to localStorage
    btnSet.addEventListener('click', () => {
      const parsed = parseInt(zoomInput.value, 10);
      if (!isNaN(parsed)) {
        currentZoom = clampZoom(parsed);
        zoomInput.value = String(currentZoom);
        applyZoom(panel, currentZoom);
      }
      localStorage.setItem(ZOOM_STORAGE_KEY, String(currentZoom));
    });

    // Allow pressing Enter in the zoom input to apply and save
    zoomInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        btnSet.click();
      }
    });

    // Helper: populate grid with buttons from activePrompts
    function rebuildGrid() {
      grid.innerHTML = '';
      activePrompts.forEach((p) => {
        const btn = document.createElement('button');
        btn.className = 'cpi-btn';
        btn.title = `Click to inject: ${p.title}`;
        btn.innerHTML = `
          <span class="cpi-btn-num">${p.id}</span>
          <span class="cpi-btn-title">${p.title}</span>
        `;
        btn.addEventListener('click', () => {
          const ok = injectPrompt(p.prompt);
          if (ok) {
            btn.classList.add('cpi-flash');
            setTimeout(() => btn.classList.remove('cpi-flash'), 400);
          } else {
            btn.style.borderColor = '#ff4444';
            setTimeout(() => { btn.style.borderColor = '#333'; }, 800);
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
      setTimeout(() => header.classList.remove('cpi-flash'), 400);
    }

    gearBtn.addEventListener('click', () => {
      showEditor(onEditorChange, onEditorChange);
    });

    panel.appendChild(grid);
    document.body.appendChild(panel);

    // Apply saved zoom on load
    applyZoom(panel, currentZoom);
  }

  // ============================================================
  // INIT — Wait for page to be ready
  // ============================================================

  function waitForPage() {
    console.log('[Prompt Injector] Waiting for page...');
    const check = setInterval(() => {
      if (document.body) {
        clearInterval(check);
        try {
          injectStyles();
          buildPanel();
          console.log('[Prompt Injector] Panel built successfully');
        } catch (e) {
          console.error('[Prompt Injector] Error building panel:', e);
        }
      }
    }, 200);
  }

  waitForPage();

})();
