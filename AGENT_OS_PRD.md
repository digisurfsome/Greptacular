# Agent OS System — Full PRD

## What This Document Is

This is the comprehensive PRD for the Agent OS system as integrated into DunkStack. Agent OS is the structured context management and PRD creation system that serves as the **front door** to DunkStack builds. It takes unstructured human input (ideas, rants, requirements) and transforms it into the 3-layer structured context that build agents consume.

This document describes the FULL system — the interactive CLI-based tool that walks users through creating structured PRDs, not just the document format. The format (Standards / Product / Specs) is documented here, but the real value is the system that CREATES, MANAGES, and SERVES that format to build agents.

## Relationship to Other Documents

- **BASE_BUILD_PRD.md** — The file-based context engine (Mechanisms 1-12). Agent OS runs ON TOP of this.
- **OPERATIONAL_TRUTH_v3.md** — The master architecture vision. Agent OS is one component of that vision.
- **rant-to-prd-spec.md** — The 7-stage terminal pipeline for PRD creation. Agent OS incorporates elements of this but is a different, integrated approach.

## Why This Matters

**The problem:** Every time a user starts a build, they have to manually prepare structured context for the agent. They write specs, organize standards, define features. This is tedious, error-prone, and requires the user to think like an engineer about how to structure information for an AI. Most users can't do this well, which means the agent starts with poor context, which means poor output, which means the user thinks the tool is broken.

**The solution:** Agent OS is an interactive system that does the structuring FOR the user. The user talks naturally — describes what they want, rants about requirements, provides references — and Agent OS transforms that into the 3-layer context format that build agents consume optimally. The user never has to think about file structures, context management, or prompt engineering.

**The result:** The gap between "I have an idea" and "the agent is building it correctly" shrinks from hours of manual prep to a guided 15-30 minute interactive session. The structured output is consistent, complete, and optimized for AI consumption.

---

## The 3-Layer Model

### Layer 1: Standards

**What it is:** The user's coding conventions, architecture patterns, UI/UX requirements, quality standards, and technology stack preferences. These are PERSISTENT — they apply to every project the user builds, not just the current one.

**What it contains:**

```
agent-os/standards/
├── coding-conventions.md      # Language style, naming, file organization
├── architecture-patterns.md   # How code is structured (MVC, repository, etc.)
├── ui-ux-standards.md         # Martin's build standards, component requirements
├── quality-standards.md       # Testing, documentation, performance requirements
├── security-requirements.md   # Auth patterns, input validation, OWASP compliance
└── technology-stack.md        # Approved frameworks, libraries, tools
```

**Key characteristics:**
- Created ONCE, reused across all projects
- Updated when the user's preferences evolve
- Loaded by the build agent at the start of every session
- NOT put into the system prompt (too large) — loaded via selective file reads
- Versioned — changes tracked so you can see how standards evolved

**How it's created:**
1. Agent OS asks the user about their tech stack, preferences, patterns
2. If the user has existing projects, Agent OS can ANALYZE them to infer standards
3. The user reviews and approves the generated standards
4. Standards are stored globally (not per-project) at `~/.autoforge/agent-os/standards/` or project-level at `agent-os/standards/`

### Layer 2: Product

**What it is:** The vision, target users, use cases, roadmap, and business context for a specific project. This is PER-PROJECT — different for each thing being built.

**What it contains:**

```
.agent/product/
├── vision.md                  # What this project is and why it exists
├── target-users.md            # Who uses this and what they need
├── use-cases.md               # Core user flows and scenarios
├── roadmap.md                 # Phases, priorities, what's now vs. later
├── constraints.md             # Budget, timeline, technical, regulatory limits
└── competitive-context.md     # What else exists, how this is different
```

**Key characteristics:**
- Created per project, typically during the first interactive session
- Relatively stable — updated when strategy changes, not every build session
- Gives the build agent the "WHY" behind decisions
- Prevents the agent from making choices that conflict with business goals
- Links to the Specs layer (features trace back to use cases)

**How it's created:**
1. User describes what they want to build in natural language
2. Agent OS asks clarifying questions about target users, goals, constraints
3. Agent OS generates the product layer documents
4. User reviews and approves
5. Documents are saved to the project's `.agent/product/` directory

### Layer 3: Specs

**What it is:** Detailed feature specifications that the build agent implements. Each spec is a self-contained document describing one feature with enough detail for an agent to build it without asking questions.

**What it contains:**

```
.agent/specs/
├── feature-001-auth.md
├── feature-002-dashboard.md
├── feature-003-settings.md
└── ...
```

**Each spec contains:**

```markdown
# Feature [ID]: [Name]

## Overview
[1-2 sentence description of what this feature does]

## Requirements
### Functional
1. [What the feature must do — user-visible behavior]
2. [...]

### Technical
1. [How it must work — architecture, data model, API design]
2. [...]

## User Stories
- As a [user type], I want to [action] so that [benefit]

## Acceptance Criteria
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]

## Technical Specification
- **API Endpoints:** [Routes, methods, request/response formats]
- **Data Models:** [Fields, types, relationships]
- **Components:** [UI components needed]
- **Dependencies:** [What must exist before this can be built]
- **Edge Cases:** [What to handle]

## Standards References
- See coding-conventions.md section [X] for [pattern to follow]
- See ui-ux-standards.md for [component requirements]

## Success Metrics
[How we measure if this worked]
```

**Key characteristics:**
- Created during the PRD session (Layer 2 → Layer 3 is the main workflow)
- Maps 1:1 to features in features.db (each spec = one feature entry)
- Consumed by the build agent via selective file reads
- Updated after build if implementation diverged from spec (living document)
- Dependencies between specs are reflected in the dependency graph

**How it's created:**
1. After the Product layer is established, Agent OS identifies the feature set
2. For each feature, Agent OS generates a draft spec based on product context + standards
3. User reviews each spec, provides corrections, adds detail
4. Agent OS refines specs based on feedback
5. Final specs are saved and corresponding features.db entries are created

---

## Project Intake Dock (File Staging System)

Before the interactive PRD workflow begins, the user needs a place to dump all their project files — reference docs, PRDs, screenshots, specs, competitor analyses, design mockups, whatever they have. The Intake Dock is that place.

### What It Does

A staging area (UI panel/tab) where the user:
1. **Dumps files** — Drag & drop, paste, or upload. Any format: .md, .txt, .pdf, .png, .docx, whatever.
2. **Tags each file** — Assigns it to a category so the system knows where it goes.
3. **Sees a readiness checklist** — Visual indicator of what's been provided vs. what's still needed.
4. **Hits "Process"** — System distributes files to proper locations and kicks off Agent OS.

### Why It's Critical

Without this, the user has to manually create directories, name files correctly, and place them in the right spots. That's a developer task. The whole point of this system is that the user is NOT a developer. They have ideas, documents, and references — they just need somewhere to put them and a way to say "this one is my coding standards, this one is my product vision, these three are feature ideas."

### How It Works

**The Intake Dock UI:**

```
┌─────────────────────────────────────────────────┐
│  PROJECT INTAKE DOCK                            │
│  Project: My Task App                           │
├─────────────────────────────────────────────────┤
│                                                 │
│  📁 Drop files here or click to upload          │
│  ─────────────────────────────────────────      │
│                                                 │
│  STAGED FILES:                                  │
│                                                 │
│  ✅ my-ideas.md          [Product ▼]            │
│  ✅ ui-standards.md      [Standards ▼]          │
│  ✅ competitor-notes.txt [Reference ▼]          │
│  ⚠️ auth-spec.md         [Tag needed ▼]         │
│  ✅ mockup.png           [Reference ▼]          │
│                                                 │
│  ─────────────────────────────────────────      │
│  READINESS CHECKLIST:                           │
│                                                 │
│  ✅ Standards    2 files tagged                  │
│  ✅ Product      1 file tagged                   │
│  ⚠️ Specs        0 files tagged (optional)       │
│  ✅ Reference    2 files tagged                  │
│                                                 │
│  ⚠️ 1 file needs a tag                          │
│                                                 │
│  [Process & Start Agent OS →]                   │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Tag categories:**

| Tag | Where it goes | What it means |
|-----|--------------|---------------|
| **Standards** | `agent-os/standards/` | Coding conventions, architecture patterns, UI requirements, quality standards |
| **Product** | `.agent/product/` | Vision, users, use cases, roadmap, competitive context |
| **Spec** | `.agent/specs/` | Feature specifications, technical requirements |
| **Reference** | `.agent/knowledge/` | Background material the agent should know about but isn't a direct input (competitor docs, research, examples) |
| **Intake** | `.agent/intake/` | Raw unstructured input for Agent OS to process (rants, braindumps, conversation transcripts) |

**Auto-detection:**

The system attempts to auto-tag files based on content analysis:
- Contains "coding conventions," "style guide," "architecture" → suggest **Standards**
- Contains "vision," "users," "roadmap," "problem we solve" → suggest **Product**
- Contains "requirements," "acceptance criteria," "user stories" → suggest **Spec**
- Contains "competitor," "research," "analysis," "reference" → suggest **Reference**
- Doesn't match any pattern → suggest **Intake** (let Agent OS figure it out)

User can always override the auto-suggestion with one click.

**Readiness checklist:**

| Category | Minimum for green | Notes |
|----------|------------------|-------|
| Standards | 0 files (can be created during workflow) | Green if any tagged, or if global standards exist |
| Product | 1 file | At minimum, need SOMETHING describing what to build |
| Specs | 0 files (generated by Agent OS) | Optional — if user has specs, great; if not, Agent OS generates them |
| Reference | 0 files | Purely optional enrichment material |
| Intake | 0 files | Alternative to Product — raw braindump that Agent OS will structure |

**Minimum to proceed:** At least 1 file tagged as Product OR Intake. Everything else is optional — Agent OS will ask questions to fill gaps.

**The "Process" action:**

When the user hits "Process & Start Agent OS":
1. Files are copied from the staging area to their tagged destinations
2. Large files (>50 lines) get a summary generated and added to index.md
3. The readiness state is recorded in `.agent/progress/intake_log.md`
4. Agent OS Stage 1 (Intake) begins with all placed files as input
5. The staging area shows "Processed ✅" on each file

**Per-project persistence:**

Each project has its own intake dock state. When switching between projects:
- Staged files are saved per-project
- Tags persist across sessions (don't re-tag if you come back later)
- Processed files show their destination path
- New files can be added at any time (triggers the Feature Addition Engine)

**Copy-paste support:**

Not everything is a file. The user might want to paste:
- A conversation transcript from another AI chat
- A Slack thread about requirements
- A section of a competitor's website
- Notes from a phone call

The dock supports "paste as new file" — paste text, give it a name, tag it, done. The system creates the .md file from the pasted content.

### Integration with Agent OS Workflow

The Intake Dock is **Stage 0** — it happens before the interactive workflow begins:

```
Stage 0: Intake Dock (file staging + tagging)
    ↓
Stage 1: Intake (Agent OS processes all staged files)
    ↓
Stage 2: Standards Check (uses files tagged as Standards)
    ↓
Stage 3: Product Discovery (uses files tagged as Product + Intake)
    ↓
... remaining stages ...
```

If the user provides comprehensive files (detailed standards, full product docs, specs for every feature), Agent OS can skip entire stages. The more the user provides upfront, the less the interactive Q&A needs to cover.

If the user provides almost nothing (one braindump file tagged as Intake), Agent OS runs the full interactive workflow to build everything from scratch.

---

## The Interactive PRD Creation Workflow

This is the core of Agent OS — the guided process that takes a user from "I have an idea" to "the agent has everything it needs to build."

### Stage 1: Intake

**What happens:** The user provides their initial input. This can be anything:
- A conversational description ("I want to build a task management app")
- A rant ("So basically the problem is that every tool out there sucks because...")
- A reference document (paste a PRD, a competitor's feature list, a mockup description)
- A combination of all of the above

**System behavior:**
1. Accept all input without interruption
2. Classify the input type (casual description, formal spec, reference material, mixed)
3. Extract key entities: product name, target users, core features, constraints
4. Identify GAPS — what's missing that we need to ask about

**Output:** Internal classification + extracted entities + gap list

### Stage 2: Standards Check

**What happens:** Before diving into the product, check if the user has Standards defined.

**System behavior:**
1. Check for existing standards at `~/.autoforge/agent-os/standards/` or `agent-os/standards/`
2. If standards exist: load them, confirm they're still current
3. If no standards exist: run the Standards Creation sub-flow (see below)
4. If standards exist but are incomplete for this project type: identify gaps and ask targeted questions

**Output:** Complete Standards layer ready for reference

### Stage 3: Product Discovery

**What happens:** Through targeted questions, Agent OS builds the Product layer from the user's input.

**Question flow (adaptive — skip questions the intake already answered):**

1. **Vision:** "In one sentence, what does this product do for the user?" (Forces clarity)
2. **Target users:** "Who specifically uses this? Give me a real person or role." (Prevents vague "everyone" answers)
3. **Core problem:** "What's the #1 pain point this solves?" (Forces prioritization)
4. **Competitive context:** "What do people use today instead? What's wrong with it?" (Establishes differentiation)
5. **Constraints:** "Any hard constraints? Budget, timeline, technology, regulatory?" (Prevents impossible specs)
6. **Success definition:** "If this works perfectly, what happens? What does success look like?" (Establishes acceptance criteria)

**System behavior:**
- Ask ONE question at a time (don't overwhelm)
- Accept natural language answers (don't require structure from the user)
- After each answer, update the internal product model
- Show the user a brief "here's what I understand so far" summary after every 3 questions
- Stop asking when the product model has sufficient coverage (no critical gaps)

**Output:** Complete Product layer documents written to `.agent/product/`

### Stage 4: Feature Extraction

**What happens:** Agent OS analyzes the Product layer and extracts a feature list with priorities and dependencies.

**System behavior:**
1. Identify all implied features from the product description
2. Categorize by priority: MUST HAVE (MVP), SHOULD HAVE (v1.1), NICE TO HAVE (future)
3. Identify dependencies between features (e.g., "auth must exist before user profiles")
4. Estimate relative complexity (small/medium/large — not time estimates)
5. Present the feature list to the user for review

**User interaction:**
- "Here are the features I extracted. Review this list:"
- Show each feature with priority, category, and estimated complexity
- User can: add features, remove features, change priorities, change dependencies
- User can: accept the list as-is

**Output:** Feature list ready for spec generation

### Stage 5: Gap Analysis

**What happens:** Before generating specs, Agent OS checks for gaps — things that are referenced but not defined, contradictions, missing technical details.

**Gap types:**
- **Missing technical detail:** "The auth feature references 'social login' but doesn't specify which providers"
- **Contradictions:** "The vision says 'simple for small teams' but feature 12 requires enterprise-grade permissions"
- **Unstated dependencies:** "Feature 5 assumes a notification system exists, but no notification feature is defined"
- **Standards conflicts:** "The requested tech stack (React) conflicts with your standard (Vue.js)"
- **Scope creep signals:** "22 features for MVP is aggressive — consider moving features 15-22 to v1.1"

**System behavior:**
1. Run gap analysis across all three layers (Standards ↔ Product ↔ Features)
2. Rank gaps by severity (blocking, important, minor)
3. Present BLOCKING gaps first — these must be resolved before spec generation
4. For each gap, provide a recommendation with a confidence score
5. If confidence > 85%, suggest auto-filling: "I'd recommend PostgreSQL here (87% confidence). Accept or specify different?"

**User interaction:**
- Blocking gaps require user input
- High-confidence recommendations can be auto-accepted
- Minor gaps are noted but don't block spec generation

**Output:** All blocking gaps resolved, gap resolution log saved

### Stage 6: Spec Generation

**What happens:** For each feature, Agent OS generates a detailed spec document.

**System behavior:**
1. For each feature in priority order:
   a. Generate the spec using the template format (see Layer 3 above)
   b. Cross-reference against Standards (ensure patterns match)
   c. Cross-reference against Product (ensure feature aligns with vision)
   d. Cross-reference against other specs (ensure consistency)
   e. Flag any spec-level gaps (edge cases, unclear requirements)
2. Present specs to user for review (one at a time or batch)
3. User approves, requests changes, or adds detail
4. Iterate until user is satisfied

**Quality checks during generation:**
- Every spec must reference at least one user story from the Product layer
- Every spec must identify its dependencies
- Every spec must list acceptance criteria that are testable
- Every spec must reference relevant Standards sections
- No spec can exceed the build agent's reasonable capacity (if too large, split it)

**Output:** Complete spec documents in `.agent/specs/`, one per feature

### Stage 7: Feature Database Population

**What happens:** The approved specs are converted into features.db entries with the dependency graph.

**System behavior:**
1. Create a features.db entry for each spec (name, description, priority, category, steps)
2. Set up dependencies between features based on the dependency analysis
3. Verify the dependency graph is acyclic (no circular dependencies)
4. Calculate build order using topological sort
5. Present the final build plan to the user

**Output:** features.db populated, dependency graph valid, build order established

### Stage 8: Handoff to Build Agent

**What happens:** Agent OS packages everything the build agent needs and initiates the first build session.

**Handoff package:**
1. Standards layer → `agent-os/standards/` (or global location)
2. Product layer → `.agent/product/`
3. Spec files → `.agent/specs/`
4. Features database → `.agent/features.db`
5. Scope boundary → `.agent/scope_boundary.md` (auto-generated from feature priorities)
6. Build agent system prompt → `.agent/system_prompt.md` (includes file protocol + selective reading rules)
7. Analytics config → `.agent/settings/config.yml`

**The build agent starts with:**
- Read index.md (knows where everything is)
- Read scope_boundary.md (knows what to build in this phase)
- Read the first ready feature's spec from `.agent/specs/`
- Reference standards selectively as needed during implementation
- Begin building

---

## Standards Creation Sub-Flow

When a user doesn't have Standards defined yet, Agent OS runs this targeted questionnaire:

### Technology Stack
1. "What programming language(s) do you use?" (or "What should this project use?")
2. "Frontend framework preference?" (React, Vue, Svelte, Next.js, none)
3. "Backend framework?" (Express, FastAPI, Django, Rails, none)
4. "Database?" (PostgreSQL, SQLite, MongoDB, none yet)
5. "Any other tools or libraries you always use?"

### Coding Style
1. "Do you follow a specific style guide?" (Airbnb, PEP 8, Google, custom, none)
2. "Functional or class-based components?" (for frontend)
3. "How do you organize files?" (by feature, by type, other)
4. "Naming conventions?" (camelCase, snake_case, kebab-case for files)

### Quality
1. "Testing requirements?" (unit tests, integration tests, E2E, none for MVP)
2. "Documentation requirements?" (JSDoc, docstrings, inline comments, none)
3. "Performance requirements?" (response times, load handling, none)

### UI/UX (if frontend)
1. "Design system or component library?" (Tailwind, MUI, Shadcn, custom, none)
2. "Mobile responsive required?" (yes, no, mobile-first)
3. "Accessibility requirements?" (WCAG level, none)
4. "Any mandatory UI patterns?" (loading states, error handling, modals)

### Architecture
1. "API style?" (REST, GraphQL, tRPC, none)
2. "State management?" (Redux, Zustand, Context, none)
3. "Authentication pattern?" (JWT, sessions, OAuth, none)
4. "Deployment target?" (Vercel, AWS, self-hosted, don't know)

**System behavior:**
- Ask questions ONE at a time
- Skip questions that aren't relevant to the project type
- For each answer, generate the corresponding standards document section
- After all questions: present the complete standards for review
- User approves or adjusts

**For users with existing projects:**
- Agent OS can ANALYZE an existing codebase to infer standards
- "I see you use React with TypeScript, Tailwind CSS, and functional components. Your naming convention appears to be camelCase for variables and PascalCase for components. Is this correct?"
- This is much faster than manual questionnaire

---

## Mechanism Analysis System

When the spec generation stage encounters a technical decision point where multiple approaches are viable, Agent OS runs a mechanism analysis:

### What It Does
Evaluates competing technical approaches for a feature, scores them, and recommends the best fit based on the user's standards and constraints.

### How It Works

1. **Identify the decision point:** "Feature 3 needs real-time updates. Options: WebSocket, Server-Sent Events, or polling."

2. **Score each option against criteria:**

| Criterion | WebSocket | SSE | Polling |
|-----------|-----------|-----|---------|
| Complexity | Medium | Low | Low |
| Bidirectional | Yes | No | No |
| Standards match | High | Medium | High |
| Scalability | High | Medium | Low |
| Browser support | 98% | 95% | 100% |
| **Overall Score** | **82%** | **71%** | **58%** |

3. **Apply the confidence threshold:**
   - If top option scores > 85%: Auto-select with notification ("Chose WebSocket — 82% match. See analysis in decisions.log")
   - If top two options are within 15%: Present both to user for decision
   - If all options score < 60%: Flag as needing human input — may indicate a gap in requirements

4. **Record the decision:** Write to decisions.log with full analysis

### Configurable Thresholds

```yaml
mechanism_analysis:
  auto_select_threshold: 85      # Auto-pick if top option scores above this
  present_alternatives_gap: 15   # Show alternatives if gap between top two is less than this
  min_viable_score: 60           # Flag for human input if all options below this
  max_options_to_evaluate: 4     # Don't analyze more than this many options
```

---

## The Developer's Choice System

For decisions where multiple options are close in score, Agent OS can apply a "Developer's Choice" heuristic — biasing toward options that:
1. Match the user's existing patterns (from Standards layer)
2. Have broader community adoption (less risk of abandonment)
3. Are simpler to implement (YAGNI principle)
4. Have better documentation (easier for future maintenance)

This is NOT a replacement for user judgment on critical decisions. It's a tiebreaker for close calls where the user says "just pick one."

### Config

```yaml
developers_choice:
  enabled: true
  bias_toward_standards: 0.3     # Weight toward matching existing patterns
  bias_toward_simplicity: 0.2    # Weight toward simpler option
  bias_toward_adoption: 0.2      # Weight toward popular/well-maintained
  bias_toward_docs: 0.1          # Weight toward better documented
  # Remaining 0.2 is raw technical score
```

---

## Feature Addition Engine

After the initial PRD is created, the user may want to add features. This is the "expand project" workflow:

### How It Works

1. **User describes new feature(s)** — Natural language, same as initial intake
2. **Agent OS checks against existing context:**
   - Does this conflict with any existing feature?
   - Does this require changes to existing specs?
   - What existing features does this depend on?
   - Does this align with the Product layer vision?
3. **Generate new spec(s)** using the same template
4. **Update dependency graph** — add new features, update dependencies
5. **Update scope boundary** — add to appropriate phase
6. **Regenerate build order** if dependencies changed

### Safeguards
- New features can't modify existing specs without explicit user approval
- If a new feature would require changing a feature that's already BUILT, flag it prominently
- Maximum features per expansion: configurable (default: 5) to prevent scope explosion

---

## Codebase Reality Engine

For existing projects where the user wants to add Agent OS context AFTER code has been written:

### How It Works

1. **Analyze the codebase:**
   - Scan file structure, detect framework, language, patterns
   - Read key files (package.json, requirements.txt, config files)
   - Identify architecture patterns (routing, data models, component structure)
   - Map existing features and functionality

2. **Generate Standards from code:**
   - Infer coding conventions from actual code style
   - Document the architecture pattern that's already in use
   - List the technology stack from dependencies
   - Identify testing patterns from existing tests

3. **Generate Product layer from code:**
   - Infer the product purpose from README, comments, and functionality
   - Map existing features as completed
   - Identify partially implemented features

4. **Generate Specs for existing features:**
   - Reverse-engineer specs from implementation
   - Mark all existing features as "passing" in features.db
   - Identify undocumented features and gaps

5. **Present for review:** User validates that the inferred context is accurate

**This enables:** Adding DunkStack + Agent OS to ANY existing project, not just greenfield builds.

---

## Integration with DunkStack Mechanisms

Agent OS integrates directly with the base DunkStack system (BASE_BUILD_PRD.md Mechanisms 1-12):

| Agent OS Component | DunkStack Integration |
|---|---|
| Standards files | Loaded via Mechanism 1 (selective reading rules) — agent reads standards ONLY when doing relevant work |
| Product files | Loaded once per session at startup via Mechanism 5 (bridge resume) |
| Spec files | Read per-feature via Mechanism 1 — agent reads the spec for the feature it's currently building |
| Feature database | Direct integration with DunkStack features.db — specs populate features, build agent marks them passing |
| Gap analysis log | Written to `.agent/progress/decisions.log` (Mechanism 8) |
| Mechanism analysis | Written to `.agent/progress/decisions.log` (Mechanism 8) |
| Scope boundary | Auto-generated from feature priorities → `.agent/scope_boundary.md` (Mechanism 9) |
| Feature changes | Tracked in `.agent/progress/changes.md` (Mechanism 10) |
| Build analytics | All builds measured by Mechanism 11 analytics system |
| Lever optimization | Build quality feeds back into Mechanism 12 optimizer |

---

## File Structure (Complete)

With Agent OS integrated into DunkStack:

```
project-root/
├── agent-os/
│   └── standards/                      # Layer 1: Persistent standards
│       ├── coding-conventions.md
│       ├── architecture-patterns.md
│       ├── ui-ux-standards.md
│       ├── quality-standards.md
│       ├── security-requirements.md
│       └── technology-stack.md
│
├── .agent/
│   ├── index.md                        # Master file index
│   ├── working_memory.md               # Agent's current state
│   ├── scope_boundary.md               # In/out of scope
│   ├── bridge.md                       # Session continuity (temporary)
│   ├── system_prompt.md                # Agent's operating instructions
│   │
│   ├── product/                        # Layer 2: Project-specific context
│   │   ├── vision.md
│   │   ├── target-users.md
│   │   ├── use-cases.md
│   │   ├── roadmap.md
│   │   ├── constraints.md
│   │   └── competitive-context.md
│   │
│   ├── specs/                          # Layer 3: Feature specifications
│   │   ├── feature-001-auth.md
│   │   ├── feature-002-dashboard.md
│   │   └── ...
│   │
│   ├── comms/
│   │   ├── to_human.md
│   │   ├── from_human.md
│   │   └── control.md
│   │
│   ├── knowledge/
│   │   └── [topic].md
│   │
│   ├── output/
│   │   └── [deliverable].md
│   │
│   ├── progress/
│   │   ├── build_log.md
│   │   ├── decisions.log
│   │   └── changes.md
│   │
│   ├── analytics/
│   │   ├── session_{timestamp}.json
│   │   ├── aggregate.json
│   │   ├── lever_registry.yml
│   │   └── reports/
│   │       ├── session_{timestamp}_report.md
│   │       ├── comparison_{project}.md
│   │       └── optimization_{timestamp}.md
│   │
│   ├── settings/
│   │   └── config.yml
│   │
│   └── features.db
│
└── CLAUDE.md                           # System prompt for Claude Code
```

---

## UI Components

The Agent OS interactive workflow needs UI in the App Builder page:

### PRD Creation Chat Panel

A chat-like interface where the user interacts with Agent OS to create the PRD:

- **Input area:** User types naturally, pastes documents, drops files
- **Agent OS responses:** Structured questions, summaries, confirmations
- **Progress indicator:** Shows which stage the workflow is in (Intake → Standards → Product → Features → Gaps → Specs → Database → Handoff)
- **Layer preview:** Side panel showing the current state of each layer as it's being built
- **Spec cards:** Visual cards for each feature showing status (draft, reviewed, approved)
- **Dependency graph:** Visual graph of feature dependencies (reuse existing DependencyGraph component)
- **Standards panel:** Collapsible view of current standards for reference during spec review

### Settings for Agent OS

```yaml
agent_os:
  auto_select_threshold: 85
  present_alternatives_gap: 15
  min_viable_score: 60
  max_features_per_expansion: 5
  standards_location: global          # global | project
  infer_standards_from_code: true     # Analyze existing code for standards
  gap_analysis_severity: blocking     # blocking | all (show all gaps or only blocking)
```

---

## Config Settings (Complete)

Combined config.yml with all DunkStack + Agent OS settings:

```yaml
# Agent Settings - Adjustable Levers
version: 2

mode:
  type: subscription
  model_family: claude-sonnet

api:
  key_env_var: ANTHROPIC_API_KEY
  model_id: claude-sonnet-4-6
  max_tokens_output: 16000

context_management:
  utilization_target: 85
  working_memory_frequency: 3
  file_read_budget: 4000
  api_response_max_sentences: 3

session:
  idle_cycle_seconds: 300
  bridge_on_end: true

safety:
  warning_threshold_pct: 45
  handoff_threshold_pct: 47.5
  hard_stop_threshold_pct: 50
  post_stop_review: true
  model_limit: 200000

build:
  test_after_feature: true

analytics:
  enabled: true
  per_turn_logging: true
  auto_report: true
  comparison_frequency: 5
  baseline_mode: false
  retention_sessions: 100

optimization:
  enabled: true
  auto_recommend: true
  auto_apply: false
  min_sessions_before_first: 3
  sessions_between_changes: 3
  max_levers_per_cycle: 1
  revert_on_constraint_violation: true

agent_os:
  auto_select_threshold: 85
  present_alternatives_gap: 15
  min_viable_score: 60
  max_features_per_expansion: 5
  standards_location: global
  infer_standards_from_code: true
  gap_analysis_severity: blocking

mechanism_analysis:
  auto_select_threshold: 85
  present_alternatives_gap: 15
  min_viable_score: 60
  max_options_to_evaluate: 4

developers_choice:
  enabled: true
  bias_toward_standards: 0.3
  bias_toward_simplicity: 0.2
  bias_toward_adoption: 0.2
  bias_toward_docs: 0.1
```

---

## Build Sequence for Agent OS

### Phase A: Standards Management
1. Create standards file templates
2. Build the Standards Creation questionnaire logic
3. Build the Codebase Reality Engine (infer standards from existing code)
4. Build the standards storage and retrieval system (global vs. project)
5. Wire to UI: Standards editor panel

### Phase B: Product Discovery
1. Build the intake classifier (categorize user input)
2. Build the entity extractor (pull key info from natural language)
3. Build the adaptive question flow (skip answered questions)
4. Build the product document generator
5. Wire to UI: PRD Creation Chat Panel

### Phase C: Feature & Spec Generation
1. Build the feature extraction engine (product → feature list)
2. Build the gap analysis engine (cross-layer gap detection)
3. Build the mechanism analysis engine (scoring competing approaches)
4. Build the spec generator (feature → detailed spec document)
5. Build the Developer's Choice tiebreaker system
6. Wire to UI: Feature cards, spec review, dependency graph

### Phase D: Database & Handoff
1. Build the features.db population from specs
2. Build the dependency graph generator (specs → dependency entries)
3. Build the scope_boundary auto-generator
4. Build the handoff package assembler
5. Build the build-order calculator
6. Wire to UI: Build plan view, handoff confirmation

### Phase E: Feature Addition & Maintenance
1. Build the feature addition engine (expand workflow)
2. Build the spec update workflow (modify existing specs)
3. Build the cross-reference checker (new features vs. existing)
4. Wire to UI: Expand modal, spec diff view

---

## Notes for the Build Agent

If a fresh agent is executing this build:

1. **Read this entire document first** before creating any files
2. **Read BASE_BUILD_PRD.md** — Agent OS depends on the base mechanisms
3. **The interactive workflow (Stages 1-8) is the core** — the file format is just output
4. **Build Phase A first** — Standards are the foundation for everything else
5. **The UI is important but secondary** — the logic should work via file I/O first, UI wraps it later
6. **Don't over-engineer the questionnaire** — adaptive questions can start simple (if/else) and get smarter later
7. **The Codebase Reality Engine is complex** — it can be a separate phase if needed
8. **Test with a real project** — after building Phase A+B, use it to create a real Product layer for a test app
9. **The mechanism analysis and Developer's Choice systems are configurable** — ship with reasonable defaults, let the optimizer tune them

---

## What This Enables

With Agent OS + DunkStack base mechanisms:

1. **Complete build pipeline:** User idea → structured PRD → build agent → working software → analytics proof
2. **Consistency across builds:** Same standards, same quality, every time
3. **Knowledge accumulation:** Standards evolve based on what works, decisions are logged, patterns are captured
4. **Scale path:** Single agent with Agent OS context → multi-agent swarm with shared Agent OS context
5. **Commercial product:** The interactive PRD creation workflow IS the user-facing product experience
6. **Competitive moat:** The combination of structured context + file-based build + analytics + self-optimization is the full system — no single piece is the innovation, the integration is

---

## Phase Breakdown for Build Agents

### Sizing Constraints

Each build agent session must stay under 50% context window (100K tokens on 200K model). Based on typical DunkStack builds:
- System prompt + file protocol overhead: ~8K tokens
- Reading reference files (BASE_BUILD_PRD, existing code): ~15-25K tokens
- Actual coding output: ~20-40K tokens per session
- Working budget per session: ~50-70K tokens of productive work
- Safe capacity per session: ~300-500 lines of new code + tests

Agent OS is estimated at ~2,500-3,500 lines of new code total. That's 5-8 build sessions minimum.

### Phase Schedule

**Phase 1: Foundation & Standards Management (1 session)**

What gets built:
- `server/services/agent_os_file_utils.py` (~150 lines) — File I/O for agent-os/ and .agent/product/ and .agent/specs/ directories. Create/read/update standards files, product files, spec files. Template rendering for empty files.
- `server/services/agent_os_standards.py` (~200 lines) — Standards creation logic. Questionnaire flow (ordered questions, skip logic). Standards inference from existing codebase (scan package.json, requirements.txt, file structure, code patterns). Standards validation and merge.
- Standards file templates — All markdown templates for the 6 standards files
- Unit tests (~100 lines)

Why one session: These are file utilities and questionnaire logic — straightforward, no complex dependencies. The standards inference is the most complex part but it's pattern-matching on known file types.

Mini-PRD reference: AGENT_OS_PRD.md → Phase A (steps 1-4)

---

**Phase 2: Product Discovery Engine (1 session)**

What gets built:
- `server/services/agent_os_intake.py` (~200 lines) — Input classifier (detect: casual description, formal spec, reference doc, mixed). Entity extractor (product name, target users, features, constraints from natural language). Gap detector (what's missing from the input).
- `server/services/agent_os_product.py` (~250 lines) — Adaptive question flow engine. Product document generator (vision.md, target-users.md, use-cases.md, roadmap.md, constraints.md, competitive-context.md from answers). Summary generator (intermediate "here's what I understand so far" output).
- Product file templates — All markdown templates for the 6 product files
- Unit tests (~100 lines)

Why one session: The intake classifier and entity extractor are Claude-powered (the system prompt tells the agent how to classify and extract). The question flow is branching logic. Document generation is template filling from extracted data.

Mini-PRD reference: AGENT_OS_PRD.md → Phase B (steps 1-4)

---

**Phase 3: Feature Extraction & Gap Analysis (1 session)**

What gets built:
- `server/services/agent_os_features.py` (~300 lines) — Feature extraction from product layer (analyze product docs, identify implied features, categorize by priority). Gap analysis engine (cross-reference Standards ↔ Product ↔ Features, detect missing info, contradictions, unstated deps). Gap severity ranking and resolution tracking.
- `server/services/agent_os_mechanism.py` (~200 lines) — Mechanism analysis engine (score competing technical approaches). Developer's Choice tiebreaker (weighted scoring with configurable biases). Decision recording to decisions.log.
- Unit tests (~120 lines)

Why one session: Feature extraction is Claude-powered analysis. Gap analysis is cross-referencing documents. Mechanism analysis is a scoring system. All are moderate complexity, no UI dependencies.

Mini-PRD reference: AGENT_OS_PRD.md → Phase C (steps 1-3, 5)

---

**Phase 4: Spec Generation & Database Population (1 session)**

What gets built:
- `server/services/agent_os_specs.py` (~250 lines) — Spec generator (feature → detailed spec document using template). Cross-reference validator (specs reference standards, specs align with product, specs are consistent with each other). Spec quality checker (has user stories, has acceptance criteria, has dependencies, not too large).
- `server/services/agent_os_handoff.py` (~200 lines) — Features.db population from specs. Dependency graph generator (specs → dependency entries using existing dependency_resolver patterns). Scope boundary auto-generator. Build order calculator. Handoff package assembler.
- Spec file template
- Unit tests (~120 lines)

Why one session: Spec generation is template-based with Claude-powered detail filling. Database population reuses existing DunkStack patterns. The dependency graph logic is already built in DunkStack features.

Mini-PRD reference: AGENT_OS_PRD.md → Phase C (step 4) + Phase D (all steps)

---

**Phase 5: Router & WebSocket Integration (1 session)**

What gets built:
- `server/routers/agent_os.py` (~350 lines) — REST endpoints for: standards CRUD, product CRUD, specs CRUD, feature list management, gap analysis trigger, mechanism analysis trigger, handoff trigger. WebSocket endpoint for interactive PRD creation session (chat-style).
- WebSocket session management — Manage the interactive Agent OS session (intake → questions → generation → review flow over WebSocket).
- Integration with existing DunkStack router — Agent OS endpoints live alongside DunkStack endpoints.
- Integration tests (~100 lines)

Why one session: Router is REST + WebSocket boilerplate following existing patterns. The WebSocket session is the most complex part but follows the same pattern as workspace_chat_session.py.

Mini-PRD reference: All phases → router endpoints

---

**Phase 6: UI — Intake Dock & PRD Creation Chat Panel (2 sessions)**

**Session 6a: Intake Dock**

What gets built:
- `ui/src/components/appbuilder/IntakeDock.tsx` (~250 lines) — File staging area with drag & drop, paste support. File list with tag dropdowns. Auto-detection of file type. Readiness checklist with green/amber indicators. "Process & Start" action button.
- `server/services/agent_os_intake_dock.py` (~150 lines) — Backend for file staging. File storage, tag persistence, auto-detection logic, file distribution to proper directories on "Process."
- Router endpoints for intake dock CRUD — Add to `server/routers/agent_os.py`
- `ui/src/hooks/useAgentOS.ts` (~150 lines) — React Query hooks for all Agent OS endpoints.

**Session 6b: Agent OS Chat & Auxiliary Panels**

What gets built:
- `ui/src/components/appbuilder/AgentOSChat.tsx` (~200 lines) — Chat-like interface for the interactive PRD workflow. Input area, Agent OS responses, stage progress indicator.
- `ui/src/components/appbuilder/StandardsPanel.tsx` (~150 lines) — Standards viewer/editor. Shows current standards, allows editing.
- `ui/src/components/appbuilder/ProductPanel.tsx` (~100 lines) — Product layer viewer. Shows vision, users, use cases, roadmap.
- `ui/src/components/appbuilder/SpecCards.tsx` (~150 lines) — Feature spec cards. Show spec status (draft, reviewed, approved), allow review.
- `ui/src/components/appbuilder/GapAnalysisPanel.tsx` (~100 lines) — Gap display with severity, recommendations, resolution status.
- WebSocket hook for interactive Agent OS session.
- Integration with AppBuilderPage.tsx — Wire all panels into the existing page layout.

Why 2 sessions: The Intake Dock is its own complete feature (drag & drop, auto-detection, file distribution, readiness checklist). The chat panel + auxiliary panels are another complete feature set. Splitting ensures neither session gets overloaded.

Mini-PRD reference: Intake Dock section + Phase A step 5, Phase B step 5, Phase C step 6, Phase D step 6

---

**Phase 7: Feature Addition & Codebase Reality Engine (1 session)**

What gets built:
- `server/services/agent_os_expand.py` (~200 lines) — Feature addition engine (new features against existing context). Cross-reference checker (new vs. existing features). Spec update workflow. Dependency graph updater.
- `server/services/agent_os_codebase.py` (~250 lines) — Codebase Reality Engine. Scan existing codebase, detect framework/language/patterns. Generate Standards from code analysis. Generate Product layer from README/comments. Reverse-engineer specs from implementation.
- `ui/src/components/appbuilder/ExpandPanel.tsx` (~100 lines) — UI for feature expansion workflow.
- Unit tests (~100 lines)

Why one session: Feature addition is simpler than initial creation (fewer stages). Codebase analysis is file scanning + pattern matching. Both are moderate complexity.

Mini-PRD reference: AGENT_OS_PRD.md → Phase E + Codebase Reality Engine section

---

### Summary

| Phase | Focus | Est. Lines | Sessions |
|-------|-------|-----------|----------|
| 1 | Foundation & Standards | ~450 | 1 |
| 2 | Product Discovery | ~550 | 1 |
| 3 | Features & Gap Analysis | ~620 | 1 |
| 4 | Spec Gen & Database | ~570 | 1 |
| 5 | Router & WebSocket | ~450 | 1 |
| 6a | UI — Intake Dock | ~550 | 1 |
| 6b | UI — Agent OS Chat & Panels | ~700 | 1 |
| 7 | Expansion & Codebase Engine | ~650 | 1 |
| **Total** | | **~4,540** | **8 sessions** |

### Build Order

```
Phase 1 (Standards) ─────────────┐
                                  ├──→ Phase 5 (Router) ──→ Phase 6 (UI)
Phase 2 (Product) ───────────────┤
                                  │
Phase 3 (Features & Gaps) ───────┤
                                  │
Phase 4 (Specs & Database) ──────┘

Phase 7 (Expansion & Codebase) ──── can run after Phase 5
```

Phases 1-4 are backend logic with no UI dependencies. They CAN be built in parallel (different sessions working on different phases simultaneously) since they operate on different files. Phase 5 (Router) depends on all backend phases. Phase 6 (UI) depends on Phase 5. Phase 7 can run after Phase 5.

**Critical path:** Phases 1-4 (parallel) → Phase 5 → Phase 6 → Phase 7

**If running sequentially:** 7-8 sessions × ~45 minutes each = ~5-6 hours of build time

**If running Phases 1-4 in parallel:** Total build time drops to ~4-5 sessions on the critical path

### Mini-PRD Generation

Each phase above becomes its own mini-PRD document that a fresh build agent receives. The mini-PRD contains:
1. The specific section of this document relevant to that phase
2. The file structure it needs to create
3. The reference files it should study (from existing DunkStack code)
4. The integration points with other phases
5. The test criteria for completion

Mini-PRDs would be generated at: `.agent/specs/agent-os-phase-{N}.md`

---

*End of Agent OS PRD.*
