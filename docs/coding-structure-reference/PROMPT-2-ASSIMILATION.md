# Prompt 2: Assimilation — Merging Extraction Results with Existing Analysis

> **Purpose**: Feed this prompt + the extraction output from Prompt 1 + the existing documents listed below to a fresh Opus 4.6 session (200K context). The agent will synthesize everything into a final unified coding structure document.

---

## Context for the Agent

You are a senior software architect and prompt engineer. You're working on a project to build the ultimate set of AI coding agent instructions by combining wisdom from three distinct sources:

### Source 1: AutoForge System (Leon's Autonomous Agent Framework)
An autonomous coding agent factory that uses Claude Agent SDK. Its key documents define:
- A layered governance system (CLAUDE.md → coder.md → coding_prompt.template.md)
- An "elite software architect" agent persona with mandatory 3-phase workflows
- 8 non-negotiable rules, 15 coding standards, 50+ verification checks
- Context budget management, feature state machines, phase gates
- Defense-in-depth security model

### Source 2: VidAi System (Martin's SaaS Application Workflow)
A pragmatic SaaS application built with React + TypeScript + Supabase. Its key documents define:
- A comprehensive architecture reference (CLAUDE.md ~23KB)
- Concise technology mandates (AI_RULES.md ~25 lines)
- Platform-leveraged security via Supabase RLS
- Practical developer productivity patterns

### Source 3: Instructor's Build Prompt (Extracted)
A ~1500-line build prompt refined over two months, originally targeting Gemini + Firebase but extracted into platform-agnostic wisdom by a prior agent. The extraction output you're receiving contains:
- **Category 1**: Fully agnostic rules (applicable to any AI agent, any platform, any database)
- **Category 2**: Genericized platform wisdom (Gemini-specific → universal AI agent patterns)
- **Category 3**: Genericized database wisdom (Firebase-specific → universal database patterns)
- **Category 4**: Platform-locked content (non-transferable, included for completeness)

Sources 1 and 2 have already been analyzed in a **Comparison Document** that maps their similarities and differences across 16 dimensions.

---

## Your Task

Produce **two output documents**:

### Output Document 1: Universal AI Coding Agent Rulebook

A comprehensive, opinionated rulebook that any AI coding agent should follow when building applications. This is the synthesis of ALL three sources — the best of AutoForge's governance, VidAi's pragmatism, and the instructor's battle-tested patterns.

**Structure:**

```markdown
# Universal AI Coding Agent Rulebook

## Philosophy
[2-3 paragraphs on the core philosophy distilled from all three sources]

## Agent Identity & Mindset
[How the agent should think about itself and its role — drawing from AutoForge's
"elite architect" persona and the instructor's agent management patterns]

## Workflow & Methodology
[Step-by-step workflow combining AutoForge's 3-phase/9-step approach with the
instructor's workflow patterns. Resolve conflicts by choosing the more thorough option.]

## Context Window Management
[CRITICAL SECTION. Hard rule: Target 45% context usage, never exceed 50%.
Combine AutoForge's context budget system with any context management
wisdom from the instructor's build prompt.]

## Code Quality Standards
[Merged coding standards from all three sources. Remove duplicates, keep
the most specific version when two sources say similar things differently.]

## Verification & Testing
[Combined verification checklists. AutoForge has 50+ checks — merge with
instructor's verification patterns and VidAi's practical testing approach.]

## Error Handling & Defensive Coding
[Unified error handling philosophy]

## File Organization & Architecture
[Combined architecture patterns]

## UI/UX Development Standards

### Design System Fundamentals (Theme & Style Sheet Agnostic)
[These rules apply regardless of which theme or style sheet is loaded.
They govern HOW agents interact with design systems, not what the design looks like.

Key areas to synthesize from all sources:
- Never hardcode colors, spacing, or typography — always reference design tokens/CSS variables
- Every interactive element must have hover, focus, active, and disabled states
- Spacing follows a consistent mathematical scale (e.g., 4/8/12/16/24/32/48px), never random values
- Typography uses a defined hierarchy (headings, body, caption, label) — never ad-hoc font sizes
- When a themed/pre-built component exists, USE IT — never create a parallel styled version
- Components are atomic: small, reusable, composable (Button, Card, Input, not PageWithFormAndTable)
- Layout and content are separate concerns (layout components vs content components)
- Responsive breakpoints are defined once in the theme/config and referenced everywhere
- Animation/transition values are consistent (same easing, similar durations)
- Color usage follows semantic roles (primary, secondary, accent, destructive, muted) not raw values
- Dark mode considerations: design with both modes in mind from the start, use semantic color tokens
- Accessibility: contrast ratios, focus indicators, screen reader support are non-negotiable]

### Working With Themes
[Rules for when a full theme (code-level enforcement) is present:
- Import and use themed components exclusively — do not style from scratch
- Extend the theme system for new components, don't work around it
- New components must use the theme's CSS variables/tokens, not introduce new ones
- If a component doesn't exist in the theme, build it USING the theme's design tokens
  so it looks native to the theme
- Never override theme values with inline styles or component-level !important
- Document any theme extensions so future agents maintain consistency]

### Working With Style Sheets (Prompt-Level Guidance)
[Rules for when only a style sheet (design token document) is present, no code-level theme:
- Reference tokens by name in every styling decision
- Create a CSS variables file as the FIRST styling task — convert the style sheet
  tokens into actual code before building any components
- When building components, check the style sheet for applicable tokens before choosing values
- If the style sheet doesn't specify a value, derive it from the existing token scale
  (e.g., if spacing is 8/16/24, a new spacing value should be 32, not 30)
- Maintain a single source of truth — don't duplicate token values across files]

### Progressive Formalization: Style Sheet → Theme
[IMPORTANT: Many projects start simple (one-page tool with a style sheet) and grow into
full applications that need a theme. The rules should address this lifecycle:

**Stage 1 — Simple Tool (1 page):**
Style sheet is sufficient. Define core tokens: colors, font, spacing scale, border-radius,
shadow. Put them in CSS variables. No component library needed.

**Stage 2 — Growing App (2-5 pages):**
When you hit 2+ pages, extract repeated UI patterns into reusable components.
Convert the CSS variables file into a proper Tailwind config or theme config.
Start building a small component library (Button, Card, Input, Modal at minimum).

**Stage 3 — Full Application (5+ pages):**
Full theme with comprehensive component library. All design tokens formalized.
Layout components defined. Every new page is composed from existing themed components.
At this stage, an agent building a new page should be ASSEMBLING components,
not designing new visual elements.

Key rule: When transitioning between stages, the EXISTING styling must be preserved
and promoted — not thrown away and rebuilt. Stage 2 wraps Stage 1's tokens.
Stage 3 wraps Stage 2's components. It's additive, not destructive.]

### What Goes in Project CLAUDE.md for UI
[Every project's CLAUDE.md should include a UI section that tells agents:
- Which design system stage the project is at (1, 2, or 3)
- Where to find the design tokens / CSS variables / theme files
- Which component library is in use (if any)
- The project's style identity (e.g., "neobrutalism with high-contrast accessible buttons")
- Any project-specific UI rules (e.g., "buttons must be minimum 48px tall for accessibility")
- Reference to the style sheet document if one exists
This section is the bridge between the universal UI rules here and the project-specific theme.]

## TypeScript & Language Standards
[Unified TypeScript standards from all sources]

## Database Patterns
[Genericized database wisdom — combine VidAi's Supabase patterns (generalized),
instructor's Firebase patterns (generalized from Category 3), and any
AutoForge database patterns]

## Security Principles
[Combined security model — AutoForge's defense-in-depth + VidAi's platform
security + instructor's security patterns]

## Git & Version Control
[Unified git practices]

## Communication & Progress Reporting
[How the agent should communicate — combine all sources]

## Performance & Optimization
[Combined performance rules]

## Debugging & Troubleshooting
[Unified debugging workflow]

## Meta-Rules: Prompt Engineering Insights
[The "rules about rules" — what makes AI coding instructions effective,
drawn from analyzing how all three prompt authors structured their instructions]
```

**Rules for this document:**
- Every rule must be specific and actionable. No vague advice like "write clean code."
- When two sources say the same thing differently, keep the more specific/opinionated version.
- When sources genuinely conflict, note both approaches and recommend one with reasoning.
- Number every rule for easy reference.
- Mark the origin of each rule: `[AF]` = AutoForge, `[VI]` = VidAi, `[BP]` = Build Prompt, `[ALL]` = all sources agree, `[AF+BP]` = AutoForge + Build Prompt agree, etc.
- The 45% context window rule is NON-NEGOTIABLE. It goes in as stated regardless of what any source says.

---

### Output Document 2: Source Traceability Matrix

A reference table mapping every rule in the Rulebook back to its source(s). This lets the user verify nothing was lost and understand the provenance of each rule.

**Format:**

```markdown
# Source Traceability Matrix

| Rule # | Rule Summary | Source(s) | Original Location | Notes |
|--------|-------------|-----------|-------------------|-------|
| W-1 | Research before coding | AF (coder.md), BP (Cat 1.1) | AF: Phase 1, BP: Rule 12 | Both sources independently emphasize this |
| CQ-3 | No any types | AF, VI, BP | All three sources | Universal consensus |
| DB-7 | Validate at boundaries | BP (Cat 3, item 4) | BP: Firebase rules section | Genericized from Firebase validation rules |
```

---

## Input Documents

You will receive the following documents. Read ALL of them before producing output.

### Already Analyzed (Summaries from Comparison):

**AutoForge Documents:**
1. `CLAUDE.md` — Master project reference (509 lines): architecture, module map, tech stack, testing commands, security model, parallel orchestration, MCP feature management
2. `coder.md` — Agent persona (133 lines): elite software architect identity, 3-phase mandatory workflow (Research → Implementation → Verification), 8 non-negotiable rules
3. `coding_prompt.template.md` — Operational playbook (429 lines): context budget management, 9-step workflow, 15 coding standards, 50+ verification checklist items

**VidAi Documents:**
1. `CLAUDE.md` — Comprehensive reference (~23KB): dev commands, environment setup, auth system, layout system, route structure, UI components, database schema, migrations, troubleshooting
2. `AI_RULES.md` — Technology mandates (~25 lines): React + TypeScript rules, file organization, component library, production-ready requirements, git rules

**Comparison Document:**
- `COMPARISON.md` — 16-section side-by-side analysis covering all dimensions

### New Input (From Prompt 1 Extraction):
- The extraction output from the instructor's build prompt (Categories 1-4)

---

## Critical Instructions

1. **Do not lose any rules.** If a rule appears in the extraction but has no equivalent in AutoForge or VidAi, it still goes in the Rulebook. The goal is the UNION of all wisdom, not the intersection.

2. **The 45% context window rule is sacred.** It appears as a user-added rule and overrides anything from any source that might suggest otherwise. Frame it exactly as: "Target 45% context usage. If you misjudge, you hit 48%. You must never exceed 50%. This is non-negotiable."

3. **Prefer specificity over generality.** If AutoForge says "verify your work" and the Build Prompt says "run the lint check, then the type check, then manually verify the 3 most complex functions you touched, then check for regressions in connected components" — use the specific version.

4. **Note when all three sources independently agree.** These are the highest-confidence rules. Mark them `[ALL]` and consider calling them out in a "Universal Consensus" subsection.

5. **Handle the AutoForge context management nuance.** AutoForge has its own context management built into its feature-chunking architecture. Note that the 45% rule is for general-purpose coding agents. AutoForge's system handles context differently because each agent session works on a single small feature, so context exhaustion is unlikely. This is not a contradiction — it's a scope difference.

6. **Preserve the instructor's battle-tested specificity.** The build prompt was refined over two months of real-world use. If it says something weirdly specific (like "always check X before Y"), there's probably a hard-won reason. Keep it.

7. **The output should be immediately usable.** Someone should be able to drop the Universal Rulebook into a CLAUDE.md or system prompt and have a well-governed AI coding agent. It's not a reference document — it's operational instructions.

8. **Keep it under 1000 lines.** Dense and actionable beats comprehensive and sprawling. If you're over 1000 lines, you're probably being redundant.

9. **The UI/UX section is critical — give it proper depth.** The user is building a complete system where coding rules (this Rulebook) and visual design (themes/style sheets created separately) work together. The Rulebook's UI section must cover the PRINCIPLES of working with design systems — not specific visual choices, but the rules about how agents interact with whatever theme or style sheet is loaded. Think of it as: the theme says "buttons are blue with 8px radius." The Rulebook says "never hardcode a color — use the token." Both are needed. Pay special attention to the Progressive Formalization pattern (style sheet → theme) as many projects start simple and grow. **The extraction from the Build Prompt (Category 1.6) will likely contain significant UI/design system wisdom** — the instructor had a dedicated style prompt and his methodology centers on visual consistency. Merge ALL of that into the Rulebook's UI section. Don't let UI rules get lost just because they came from the Build Prompt extraction rather than AutoForge or VidAi.

10. **Frame rules as applicable to projects at any scale.** Some users build one-page tools. Others build full SaaS platforms. The Rulebook should work for both. When a rule only applies at certain scales, note the threshold (e.g., "once your project exceeds 3 pages, extract a component library").

---

## What NOT To Do

- Don't create a fourth source analysis. The comparison work is done. Your job is SYNTHESIS.
- Don't water down opinionated rules into safe generalities.
- Don't add your own coding opinions. Synthesize what's there.
- Don't skip the Traceability Matrix. It's essential for verification.
- Don't put AutoForge-specific operational details (like MCP server commands or feature state machines) into the Universal Rulebook. Those are system-specific. Extract the PRINCIPLES behind them.

---

## Documents Follow Below

**[PASTE THE FOLLOWING IN ORDER:]**

1. The extraction output from Prompt 1
2. The AutoForge analysis documents (from `docs/coding-structure-reference/autoforge/`)
3. The VidAi analysis documents (from `docs/coding-structure-reference/vidai/`)
4. The Comparison document (`docs/coding-structure-reference/COMPARISON.md`)
