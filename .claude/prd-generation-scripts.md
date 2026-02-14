# PRD Generation Scripts

## How To Use

1. Open a new Claude agent (Claude Code, claude.ai, whatever)
2. Copy the **MASTER PROMPT** below as your first message
3. Then in the same message (or immediately after), paste the **AGENT-SPECIFIC FILES** section for the agent you're running
4. The agent will read the context doc + handoffs and produce app_spec.txt files

---

## MASTER PROMPT (Same for ALL agents — copy this first)

```
I need you to convert AutoForge handoff documents into properly formatted app_spec.txt PRD files.

FIRST, read the AutoForge PRD context document that contains everything you need to know about the system, coding standards, and the exact XML output format:

File: .claude/autoforge-prd-context.md

Read that ENTIRE file before doing anything else. It contains:
- AutoForge architecture (how the agent loop works)
- Coding standards (25 build rules)
- The exact app_spec.txt XML format you must output
- Step-by-step conversion instructions
- Quality checklist
- Complete examples

THEN, read each handoff file listed below and convert it into a complete app_spec.txt PRD.

For each handoff:
1. Read the full handoff document
2. Break it into atomic, independently-buildable features (max 15-20 per spec)
3. Write concrete, actionable steps for each feature
4. Set proper dependencies (foundation first, then layers)
5. Output a complete app_spec.txt in the XML format from the context doc
6. Save each app_spec.txt to: .claude/generated-prds/[handoff-name]-spec.xml

IMPORTANT RULES:
- Each feature must be completable in one agent session (30-60 min)
- Steps must be specific: "Create file X with function Y" not "implement the feature"
- Dependencies must form a DAG (no cycles)
- Foundation features (database, core API) have no dependencies
- Every feature must be independently testable
- Run the quality checklist from the context doc before finalizing each PRD
- These are ADDITIONS to the existing AutoForge codebase, not standalone apps (except where noted)

HANDOFF FILES TO CONVERT:
```

---

## AGENT-SPECIFIC FILES (Copy ONE of these after the master prompt)

### AGENT 1 — QA Pipeline (BUILD THIS FIRST)
```
1. .claude/handoffs/qa-pipeline-handoff.md
2. .claude/handoffs/computer-use-qa-handoff.md

These two are ONE combined PRD — the QA Pipeline with Computer Use as the final phase.
Output: .claude/generated-prds/qa-pipeline-spec.xml
```

### AGENT 2 — Pre-Build Intelligence
```
1. .claude/handoffs/pre-build-intelligence-handoff.md

This adds smart spec analysis and architecture planning before builds start.
Output: .claude/generated-prds/pre-build-intelligence-spec.xml
```

### AGENT 3 — Build Intelligence
```
1. .claude/handoffs/build-intelligence-handoff.md

This adds build history tracking, PRD quality scoring, and prompt improvement.
Output: .claude/generated-prds/build-intelligence-spec.xml
```

### AGENT 4 — Post-Build Reports
```
1. .claude/handoffs/post-build-reports-handoff.md

This adds auto-generated docs, performance profiling, and security audit after builds.
Output: .claude/generated-prds/post-build-reports-spec.xml
```

### AGENT 5 — DevOps + VPS Deploy
```
1. .claude/handoffs/devops-pipeline-handoff.md
2. .claude/handoffs/self-deploy-vps-handoff.md

These are TWO related PRDs about infrastructure — CI/CD pipeline generation and one-click VPS deployment.
Output: .claude/generated-prds/devops-pipeline-spec.xml
Output: .claude/generated-prds/self-deploy-vps-spec.xml
```

### AGENT 6 — Credit-Based Pricing System
```
1. .claude/handoffs/credit-pricing-system-handoff.md

This adds the monetization layer — credits, BYOK, Stripe integration, usage metering.
Output: .claude/generated-prds/credit-pricing-spec.xml
```

### AGENT 7 — Platform Marketplace
```
1. .claude/handoffs/platform-marketplace-handoff.md

This adds boilerplate, style, and plugin marketplaces.
Output: .claude/generated-prds/platform-marketplace-spec.xml
```

### AGENT 8 — Knowledge Base + Idea Integration
```
1. .claude/handoffs/knowledge-base-tutorial-handoff.md
2. .claude/handoffs/idea-code-integration-handoff.md

These are TWO related PRDs — auto-generated docs/tutorials and mentor's style guide integration.
Output: .claude/generated-prds/knowledge-base-spec.xml
Output: .claude/generated-prds/idea-code-integration-spec.xml
```

### AGENT 9 — Style Features Bundle
```
1. .claude/handoffs/style-preview-grid-handoff.md
2. .claude/handoffs/color-customization-handoff.md
3. .claude/handoffs/color-picker-preview-task.md
4. .claude/handoffs/style-mixing-handoff.md
5. .claude/handoffs/screenshot-style-extractor-handoff.md

These are FIVE related features about the style system — preview grid, color customization, color picker, style mixing, and screenshot-to-style extraction. They can be ONE combined PRD since they all modify the style picker UI.
Output: .claude/generated-prds/style-features-spec.xml
```

### AGENT 10 — StyleVault Giveaway App
```
1. .claude/handoffs/style-picker-giveaway-spec.md

This is a STANDALONE APP (not an AutoForge addition). It's a lead-magnet giveaway app for showcasing the 12 design styles with 25 curated color palettes.
Output: .claude/generated-prds/stylevault-giveaway-spec.xml

NOTE: This is a separate React app, not a modification to AutoForge. The app_spec should reflect a new project build.
```

### AGENT 11 — Domain Finder Tool
```
1. .claude/handoffs/domain-finder-handoff.md

This is a STANDALONE APP — a domain availability checker tool.
Output: .claude/generated-prds/domain-finder-spec.xml

NOTE: This is a separate app, not a modification to AutoForge.
```
