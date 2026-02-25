# The Operational Truth v3: File-Based Agent Architecture
# Integrated with Agent OS + Martin's Build Standards

## System Architecture Overview

The system operates as a layered architecture where Agent OS provides the structural format and file-based context management provides the operational mechanism.

```
+---------------------------------------------------+
|              HUMAN INTERFACE                        |
|  Rant Intake > Walkie-Talkie > Notifications       |
+---------------------------------------------------+
|              PROCESS ENGINE                         |
|  PRD Machine > Build Engine > Test > Ship           |
+---------------------------------------------------+
|          AGENT OS FORMAT LAYER                      |
|  Standards / Product / Specs (3-layer structure)    |
+---------------------------------------------------+
|        FILE-BASED CONTEXT MANAGEMENT                |
|  Index > Selective Read > Working Memory > Bridge   |
+---------------------------------------------------+
|              API LAYER                              |
|  Thin status channel (3 sentences max)              |
+---------------------------------------------------+
```

---

## How AI Actually Processes Information

### Context Window Consumption
- System prompt (permanent): 2K-8K tokens
- Tool definitions (permanent): 3K-10K tokens
- Conversation history (accumulates): every message + response
- File reads (accumulates): every file read injected into context
- Agent output (accumulates): everything written back

### Real Usable Context
- 200K model: ~184,000 usable after overhead
- At 50% utilization: ~92,000 working tokens
- At 85% utilization (file-based): ~156,000 working tokens
- 70% more effective capacity, same model, same price

### Output Token Economics
Output costs 3-5x more than input. Redirecting verbose output to files saves both context AND money.

---

## Fundamental Rule: Files Over API Response

All substantive output writes to files. API responses contain ONLY brief status (3-sentence max). Both directions: human writes detailed input to files too. The chat channel is a thin status feed. Even 2-sentence responses accumulate across hundreds of exchanges.

---

## Agent OS Directory Structure (The Format Standard)

```
project/
+-- agent-os/
|   +-- standards/           # STANDARDS LAYER
|   |   +-- index.yml        # Smart index for selective injection
|   |   +-- global/
|   |   |   +-- tech-stack.md
|   |   +-- api/
|   |   +-- database/
|   |   +-- frontend/
|   |   +-- backend/
|   |   +-- testing/
|   |   +-- css/
|   |   +-- ui-ux-standards.md  # Martin's build standards
|   |
|   +-- product/             # PRODUCT LAYER
|   |   +-- mission.md       # Problem, target users, solution
|   |   +-- roadmap.md       # Phase 1 MVP, Phase 2, future
|   |   +-- tech-stack.md    # Full technology decisions
|   |   +-- mechanisms.md    # Functional systems described
|   |   +-- ui_vision.md     # Layout, flow, look-and-feel
|   |   +-- data_model.md    # What gets stored, relationships
|   |   +-- integrations.md  # External services, APIs
|   |   +-- business_rules.md # Logic, constraints, validation
|   |
|   +-- specs/               # SPECS LAYER
|   |   +-- YYYY-MM-DD-HHMM-feature-slug/
|   |   |   +-- plan.md
|   |   |   +-- shape.md
|   |   |   +-- standards.md
|   |   |   +-- references.md
|   |   |   +-- visuals/
|   |   +-- [more features]/
|   |
|   +-- mechanisms/          # Decision records
|       +-- [mechanism].md   # Full analysis with scoring
|
+-- .agent/                  # FILE-BASED CONTEXT SYSTEM
|   +-- index.md             # Master navigation map
|   +-- working_memory.md    # Agent's current state
|   +-- bridge.md            # Session continuity data
|   |
|   +-- comms/               # Communication channels
|   |   +-- to_human.md      # Agent > Human (append-only)
|   |   +-- from_human.md    # Human > Agent (human writes)
|   |   +-- control.md       # Mode: idle | continue | autopilot
|   |
|   +-- intake/              # Human file delivery staging
|   |   +-- raw_rant.md      # Voice/text dumps
|   |   +-- references/      # Documents, research
|   |   +-- brand/           # Colors, style guides
|   |   +-- prior_work/      # Previous versions
|   |
|   +-- progress/            # Build tracking (append-only)
|   |   +-- build_log.md     # What was built, by whom, when
|   |   +-- decisions.md     # Runtime decisions with rationale
|   |   +-- issues.md        # Problems found, workarounds
|   |   +-- test_results.md  # Test outcomes
|   |
|   +-- output/              # Completed deliverables
|   |   +-- documentation/
|   |   +-- marketing/
|   |   +-- tutorials/
|   |
|   +-- settings/            # Adjustable levers
|       +-- config.yml
|
+-- [project source code]
```

---

## Adjustable Levers Dashboard

```yaml
# .agent/settings/config.yml
version: 1

prd_machine:
  dual_build_threshold: 15        # % gap for building both options
  coverage_auto_fill: 70          # % coverage before using defaults
  developer_choice_minimum: 75    # % confidence for auto-select
  question_batch_size: 5          # Questions presented at once

context_management:
  utilization_target: 85          # % of window to use
  working_memory_frequency: 3     # Update every N turns
  file_read_budget: 4000          # Max tokens per turn on reads
  api_response_max_sentences: 3   # Max sentences in chat response

session:
  idle_cycle_seconds: 300         # Wait between heartbeats
  bridge_on_end: true             # Auto-save state on session end

build:
  dependency_parallelism: 3       # Max parallel independent features
  test_after_feature: true        # Continuous testing toggle

notifications:
  twilio_urgency: blocker         # What triggers text + flash
  pushover_urgency: status        # What triggers notification
  pushover_flash: completion      # What triggers flash notification
  telegram_updates: all           # What sends to telegram

swarm:
  swarm_size: 5                   # Agents in swarm
  manager_ratio: 5                # Workers per manager
```

---

## The Auto-Bridge System (Session Continuity)

### Trigger Conditions
- Human signals departure
- Session approaching timeout
- Emergency disconnect

### Bridge Save Sequence
1. Write complete state to bridge.md (current task, progress, active context, next steps)
2. Update working_memory.md with final state
3. Update index.md if any new files created
4. Append session summary to progress/build_log.md
5. Brief chat: "State saved. Safe to end session."

### Resume Sequence
1. Read index.md (~500 tokens)
2. Read working_memory.md (~400 tokens)
3. Read bridge.md if exists (~500-800 tokens), then delete it
4. Read comms/from_human.md for offline messages
5. Read comms/control.md for mode
6. Resume work

### Cost
- Save: ~800-1,200 output tokens
- Restore: ~1,400-1,700 input tokens
- Total: ~2,500-3,000 tokens per bridge cycle
- Recommendation: bridge on session end only, not proactively (test to confirm)

---

## The PRD Machine: Integrated with Agent OS

### Pre-Stage: Standards Discovery
For existing codebases: scan and extract coding patterns into agent-os/standards/.

### Stage 1: Intake
Human rants. Raw text to .agent/intake/raw_rant.md. Split into paragraphs and tag each.

### Stage 2: Categorization into Agent OS Product Layer
Map to 8 targets: mission.md, roadmap.md, tech-stack.md, mechanisms.md, ui_vision.md, data_model.md, integrations.md, business_rules.md.

### Stage 3: Technical Refinement
Layman to precise technical language. Always reference original for verification.

### Stage 4: Coverage Assessment
Score each file for completeness. Detailed user: 65-70%. Average: 10-30%.

### Stage 5: Recalibration
Review assembled picture as whole. Identify contradictions. Resolve before questions.

### Stage 6: Gap-Fill Q&A
Merge coverage gaps with Agent OS plan-product questionnaire. Developer's Choice with confidence percentages. Priority: Blockers > Architecture > Refinements. Learning over 5-10 projects reduces questions to unique ~13%.

### Stage 7: Full Puzzle Assembly
All Agent OS product files fully populated. Cross-referenced for consistency.

### Stage 8: Mechanism Analysis
Ranked NUMERICALLY, HIGHEST SCORE FIRST. Numbers not letters. Dual-build trigger at configurable threshold (default 15%). Developer's Choice auto-select above confidence minimum.

### Stage 9: Spec Generation (Agent OS shape-spec format)
Each mechanism becomes a spec folder with plan.md, shape.md, standards.md, references.md.

### Stage 10: Final Blueprint with Build Learnings
Mechanism learnings, backup briefs, concern flags, opportunity flags, contextual build notes.

### Stage 11: Golden Orange Feature Extraction
Exhaustive feature backlog at spec level. Natural extensions, cross-mechanism, competitive, scale, monetization, delight features. Utopia line marked explicitly.

---

## Dependency Graph Integration

### Why Critical
Build order must respect dependencies. Determines single-agent sequence, multi-agent parallelism, and swarm scheduling.

### Constitution File: dependency_map.md

Tiers of dependencies (Tier 0: no deps, build first). Parallelism map per tier. Critical path (minimum build time regardless of agents). Uses topological sort (Kahn's algorithm) with cycle detection.

---

## Notification Architecture

- **Twilio**: Text messages + screen-flashing for blockers and emergencies
- **Pushover**: App notifications for status and completion (two tiers: normal and flash)
- **Telegram**: App control, dashboard monitoring, Claude bot style

Channel choice automatic based on event type and urgency in config.yml.

---

## The Full Production Pipeline

1. Standards Discovery (if existing codebase)
2. PRD Creation (Stages 1-11)
3. Constitution Generation (Agent OS structure + .agent/ files)
4. Boilerplate Deployment (copy project boilerplate as foundation)
5. Dependency Resolution (build order, parallelism map, critical path)
6. Code Mode (per-turn: index > working_memory > targeted reads > code > update files)
7. Continuous Testing (test each component as built)
8. Final Test Suite (unit > integration > e2e > edge cases > computer-use)
9. Documentation (restructure build artifacts for users)
10. Tutorial Generation (voice AI + Playwright screen capture)
11. Landing Page + Marketing with Automated GIFs (Playwright drives app, captures 3-5s loops)
12. Golden Orange Feature Extraction (exhaustive backlog at spec level)

---

## Scaling Path

1. Single agent, 200K subscription - prove file-based + Agent OS
2. 2-3 agents, 200K subscription - prove file-based coordination + dependency scheduling
3. Single agent, 1M API - full-scale builds, 900K effective working space
4. Swarm (5-25 agents), 1M API - specialized roles, dependency-driven parallelism
5. Multi-swarm (5x25) - management layer connecting teams, unlimited scaling

---

## Boilerplate Strategy

### Current Assets
- Flutter mobile app boilerplate (commercial rights, Supabase DB, free lifetime updates)
- Martin's web boilerplate (personal use only, Supabase DB, cannot sell commercially)

### Gap
- Need commercial web boilerplate with Supabase for selling web apps
- Options: buy from Martin, find commercial boilerplate, or clean-room build

### Integration
- Boilerplate copy is first step in Code Mode (Step 4 in pipeline)
- Already automated in AutoForge pattern (copies from GitHub repo)
- Same mechanism applies to Flutter boilerplate

---

## Key Licenses

- **Agent OS**: MIT License - full commercial use, modification, distribution
- **AutoForge**: Requires source code disclosure - cannot sell directly, must clean-room for commercial use
- **Martin's web boilerplate**: Personal use only - cannot sell apps built on it
- **Flutter boilerplate**: Full commercial rights - can sell apps built on it

---

## Martin's Build Standards Summary

Stored in agent-os/standards/ui-ux-standards.md. Key mandates:

### Mandatory Components
Modal, ConfirmModal, Toast, ToastContext, Skeleton, EmptyState, ErrorBoundary, Button (with loading), Avatar (with fallback)

### Banned Patterns
alert(), confirm(), prompt(), console.log for feedback, text-only empty states, edit-first navigation, inline styles

### Navigation Flow
List View > Detail View > Create View / Edit View. Always separate read-only from edit.

### Responsive
Mobile-first. 44px minimum touch targets. Sidebar hidden on mobile with hamburger toggle.

### Loading States
Skeleton for lists (not spinners). Spinner inside buttons during async. Never just "Loading..." text.

### Polish
Modal fade + scale animations. Toast slide-in. Card hover lift. Button press scale. Keyboard navigation. Focus states. Screen reader support. Date formatting (relative time). Text truncation. Back navigation on all detail pages.

### Tech Defaults
React + TypeScript + Tailwind CSS. Lucide React icons. CSS variables for theme (light/dark). React Context for state. Service layer for all DB calls.
