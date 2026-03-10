# Build Orchestrator — Full System Description (v2)

## What This Is

A build orchestration platform inside AutoForge's existing navigation (alongside DunkStack, Workspace, Dashboard). One main nav item opens the system. Inside, four sub-tabs across the top — each tab is its own page with its own focused AI chat room (one objective per room). Together, they form a complete pipeline: from raw rules and a PRD, all the way through phased builds with live monitoring.

All tabs link together as one project. Past projects are saved and browsable. Each tab's work product feeds into the next.

```
[Main AutoForge Nav Bar]
  DunkStack | Workspace | Dashboard | BUILD ORCHESTRATOR | YT Lab | Monitor

[Inside Build Orchestrator — Sub-tabs]
  Tab 1              Tab 2             Tab 3            Tab 4
  Rule Set Builder    Build Planner     Phase Chunker    Operations Dashboard
```

---

## Why This Order Matters

You can't chunk phases until you know everything that goes into them. The Phase Chunker does token math — it needs to know:

- How big the rule sets are (from Tab 1)
- How many agents are involved, what hooks run, what testing strategy is used (from Tab 2)
- Whether this is a fresh build (big first-phase rules) or a feature add (lighter rules)

All of that affects token budget. So the logical flow is:

1. **Tab 1 — Rule Set Builder:** Create the reusable rule sets. These are the documents that get injected into every agent session. You need to know how big they are before you can do any math.
2. **Tab 2 — Build Planner:** Define agent roles, build sequence, hooks, testing strategy. This determines what happens inside each phase, which directly affects how much token space each phase needs beyond just the PRD chunk.
3. **Tab 3 — Phase Chunker:** NOW you have all the inputs. Rule sets (with their first-phase vs remaining-phase variants), build plan overhead, and the PRD. The math can be done accurately. The AI can chunk intelligently.
4. **Tab 4 — Operations Dashboard:** Everything is configured. Run it and watch.

Tabs 1 and 2 are essentially "settings" — things you configure before the real calculation happens. Tab 3 is where the math happens. Tab 4 is where the execution happens.

---

## Tab 1: Rule Set Builder

**Purpose:** Take separate source documents (coding rules, contract templates, design specs, style guides — whatever you bring) and merge them into reusable rule sets that get attached to build phases.

### Critical Concept: First-Phase vs Remaining-Phase Rule Sets

Rule sets are NOT one-size-fits-all. The output of this tab is TWO rule set slots per build type:

**For a fresh full build:**
- **First-phase rule set (~1,000 lines):** The big one. Sets the tone for the entire build. Covers the full framework — how everything should be structured, architecture decisions, coding standards, the complete picture. This only goes into Phase 1 because Phase 1 is laying the foundation.
- **Remaining-phase rule set (~300 lines):** A lighter version that references what the first phase already established. The framework is already built into the code at this point, so this just reinforces key standards and points back to what's already there.

**For adding features to an existing build:**
- **First-phase rule set (much smaller):** Maybe just some extra rules about how to approach the existing codebase. You don't need the thousand-line framework doc because the software already has its structure.
- **Remaining-phase rule set:** Could be identical to the first, or even lighter. The codebase is the documentation at this point.

**For an identical-rules build (all phases the same):**
- First and remaining are set to the exact same content. The UI just lets you put the same one in both slots.

The point: when these rule sets get pulled into Tab 3's math, the Phase Chunker knows Phase 1 has a different token footprint than Phases 2+. That changes how the PRD gets divided.

### Layout — Top to Bottom

**Top Section — The Originals**

- Text boxes across the page, each holding one source document
- Import from files or paste in directly
- These are your untouched originals — they never get modified, always preserved and visible
- Could be 3, could be 12 — however many sources you bring

**The AI Chat (Own Room, Own MD)**

- ONE job: help you merge these originals intelligently
- You explain the objective — what you're building, how this connects to PRD phases, the big picture
- AI sees ALL originals at once before doing anything
- It proposes: "These 2 should merge, these 3 should merge, this one stands alone"
- **It does NOT just go do it** — it proposes, you approve
- You can reject, adjust, re-ask until you're happy

**Middle Section — The Merge View**

- Side by side: original boxes on the left, merged result boxes on the right
- Each merged box shows which originals fed into it (e.g., "Merged from Box 1, Box 3, Box 5")
- Visual progression: 7 originals might become 4 merged blocks
- You see the reduction happening

**Bottom Section — The Placeholder Map**

- Mind map / outline view
- Each merged block gets a placeholder label (first, second, third...)
- Drag and reorder
- AI writes connecting sentences between placeholders — intros that frame each section
- Drop-downs expand/collapse to read contents
- AI can auto-organize the order, or you do it manually

**Final Output — Two Slots**

- The assembled document gets saved into the appropriate slot: first-phase rule set, remaining-phase rule set, or both
- You choose which slot(s) this output goes into
- Each slot shows its token count so you can see the size difference
- Saved as a reusable entity per build type (full build, feature add, etc.)

**Key Principles:**
- Originals always preserved and visible
- AI proposes, you approve
- Visual progression from many sources to grouped merges to final document
- Two output slots (first-phase, remaining-phase) per build type
- Saved, reusable, versionable

---

## Tab 2: Build Planner

**Purpose:** Define the agent roles, build sequence, hooks, testing strategy, and all configurable parameters for the build. This determines what happens inside each phase — which directly affects how much token space each phase needs. Must come before Phase Chunking because the chunker needs this data.

### Why This Comes Before Chunking

Every agent role, every hook, every testing step consumes tokens or affects the structure of what gets sent to the model. If you have a Coder + Reviewer + Tester sequence, that's different overhead than just a Coder + Tester. The Phase Chunker needs to account for all of this when calculating how big each coding chunk can be.

### Agent Roles — Full Parameter Breakdown

Each role is a card/panel you can configure:

| Parameter | Control Type | Description |
|-----------|-------------|-------------|
| **Role name** | Text input | What this agent is called (Coder, Reviewer, Tester, etc.) |
| **Role description** | Large text box | Plain-language description of what this agent does |
| **MD instructions** | Large text box / file import | The actual MD file content sent to this agent — its focused instructions |
| **Model selection** | Dropdown | Which AI model this role uses (Opus 4.6, Sonnet 4.6, Haiku 4.5, etc.) |
| **Execution order** | Drag handle / number | Where in the sequence this role runs (1st, 2nd, 3rd...) |
| **Enabled/Disabled** | Toggle | Turn a role on or off without deleting it |
| **Token budget for this role's MD** | Read-only (auto-calculated) | How many tokens this role's instructions consume — feeds into chunker math |

**Default roles for a full build:**
- **Coder** — Gets the phase package, builds it
- **Reviewer** — Follows behind the coder, checks the code before testing (reduces tester workload)
- **Tester(s)** — Runs verification. Could be multiple: unit tester, integration tester, etc.

You can add, remove, duplicate, and customize roles.

### Build Sequence — Full Parameter Breakdown

The step-by-step order of operations for each phase, visualized and editable:

| Parameter | Control Type | Description |
|-----------|-------------|-------------|
| **Step name** | Text input | What this step is (Code, Review, Test, Commit, etc.) |
| **Assigned role** | Dropdown | Which agent role handles this step |
| **Step enabled/disabled** | Toggle | Skip this step without removing it |
| **Step order** | Drag to reorder | Rearrange the sequence |
| **Timeout** | Number (minutes) | How long before the step is considered stuck |
| **Retry on failure** | Number (0-3) | How many times to retry if this step fails |
| **On failure action** | Dropdown: Retry / Skip / Stop / Ask Me | What happens after retries are exhausted |
| **Pass output forward** | Toggle | Whether this step's output gets included in the next phase's context |
| **Output summary style** | Dropdown: Brief / Detailed / Full | How much of this step's output carries forward |

**Default sequence for a full build:**
1. Coder gets phase package (rules + coding chunk + context from previous phase), builds it
2. Reviewer checks what coder built, writes up findings
3. Tester runs testing — each chunk verified thoroughly so assembled phases have fewer bugs
4. Summary agent writes a review of what was built — passed forward to next phase
5. Commit — checkpoint
6. Next phase starts with previous summary injected

### Hooks — Full Parameter Breakdown

| Parameter | Control Type | Description |
|-----------|-------------|-------------|
| **Hook name** | Text input | Descriptive name (e.g., "Lint before commit") |
| **Trigger point** | Dropdown | When it fires: Pre-phase / Post-step / Pre-commit / Post-commit / On-failure / Post-phase |
| **Hook command** | Text input / script editor | The actual command or script to run |
| **Enabled/Disabled** | Toggle | Turn on/off |
| **Blocking** | Toggle | Does the build wait for this hook, or fire-and-forget? |
| **Fail action** | Dropdown: Ignore / Warn / Stop Build | What happens if the hook itself fails |

**Common hooks:**
- Pre-commit: lint check, type check
- Post-phase: run regression suite
- On-failure: notify via webhook, save error log
- Post-build: deploy, send completion notification

### Testing Strategy — Full Parameter Breakdown

| Parameter | Control Type | Description |
|-----------|-------------|-------------|
| **Test types enabled** | Multi-select checkboxes | Unit / Integration / E2E / Lint / Type-check |
| **Testing token budget per phase** | Number (tokens) | Tokens reserved for testing — feeds directly into chunker math |
| **Test coverage threshold** | Slider (0-100%) | Minimum pass rate before phase is considered done |
| **Testing timeout** | Number (minutes) | Max time for testing step |
| **Retry failed tests** | Number (0-3) | Rerun count for failed tests |
| **YOLO mode** | Toggle | Skip all testing (rapid prototyping only) |

### Context Management — Full Parameter Breakdown

How information flows between phases:

| Parameter | Control Type | Description |
|-----------|-------------|-------------|
| **Carry-forward enabled** | Toggle | Whether completed phase summaries get injected into the next phase |
| **Summary max tokens** | Number | Cap on carry-forward summary size (affects chunker math) |
| **Summary style** | Dropdown: Brief / Detailed / Comprehensive | How thorough the auto-generated phase summary is |
| **Include previous test results** | Toggle | Whether test pass/fail details carry forward |
| **Include reviewer notes** | Toggle | Whether code review findings carry forward |

### Commit Strategy — Full Parameter Breakdown

| Parameter | Control Type | Description |
|-----------|-------------|-------------|
| **Auto-commit after each phase** | Toggle | Checkpoint after every completed phase |
| **Commit message format** | Text template | Template with variables like {phase_number}, {feature_name}, {status} |
| **Branch strategy** | Dropdown: Single branch / Branch per phase / Branch per feature | How git branching works |
| **Auto-push** | Toggle | Push to remote after commit, or just local |

### Error Handling — Full Parameter Breakdown

| Parameter | Control Type | Description |
|-----------|-------------|-------------|
| **On phase failure** | Dropdown: Retry phase / Skip phase / Stop build / Ask me | Default behavior when a phase fails |
| **Max retries per phase** | Number (0-5) | How many times to retry a failed phase |
| **Retry delay** | Number (seconds) | Wait time between retries |
| **Save failure snapshots** | Toggle | Capture state when something fails for debugging later |
| **Notify on failure** | Toggle + text input | Send webhook/notification when something breaks |

### Quality Gates — Full Parameter Breakdown

Thresholds that must pass before moving to the next phase:

| Parameter | Control Type | Description |
|-----------|-------------|-------------|
| **Lint must pass** | Toggle | Block next phase if lint fails |
| **Type-check must pass** | Toggle | Block next phase if type-check fails |
| **Minimum test pass rate** | Slider (0-100%) | e.g., 95% of tests must pass |
| **Custom gate command** | Text input | Any custom script/command that must return success |
| **Gate fail action** | Dropdown: Retry / Stop / Ask me | What happens when a gate fails |

### Presets and Versioning

**Different build types = different presets:**
- **Full software build** — all roles, full testing, big first-phase rules
- **Adding a feature** — lighter roles, focused scope, smaller rules
- **Reverse engineering spaghetti code** — different agent sequence, analysis-first approach
- **Clean room reverse engineering** — its own specialized roles and flow

When you open Build Planner, pick a preset. It loads all settings. Customize per project or save as a new version.

**Versioning:**
- Each preset can have multiple versions (V1, V2, V3...)
- Choose which version is the default
- If the new version isn't working, switch back — nothing is lost
- Save customizations as a new version or as project-specific overrides

### What This Tab Produces

Two things that feed into Tab 3:
1. **The complete build configuration** — every parameter above, saved and versioned
2. **The token overhead calculation** — total tokens consumed by agent MDs, hooks, carry-forward summaries, and testing budgets. The Phase Chunker subtracts this from available space to figure out how big each coding chunk can be.

---

## Tab 3: Phase Chunker

**Purpose:** Where everything comes together mathematically. Take the rule sets (from Tab 1), the build overhead (from Tab 2), and the PRD, and calculate exactly how to divide the PRD into properly sized phases. Then have AI do the actual chunking.

### Why This Must Come Last (Before Dashboard)

You CANNOT chunk accurately without knowing:
- **Rule set sizes** — Phase 1 might have a 1,000-line rule set; Phases 2+ might have 300 lines. Different token footprints.
- **Build overhead** — Agent MDs, hooks, testing budgets, carry-forward summaries from Tab 2. All eats into available space.
- **The PRD itself** — The thing being divided.

If you chunked first and configured the build second, your chunk sizes would be wrong.

### Part A — The Token Calculator (Deterministic, No AI)

Pure math. Python script. No AI guessing.

**Inputs pulled automatically from previous tabs:**
- First-phase rule set token count (from Tab 1)
- Remaining-phase rule set token count (from Tab 1)
- Agent MD token totals (from Tab 2)
- Testing token budget per phase (from Tab 2)
- Carry-forward summary budget (from Tab 2)
- Hook overhead estimate (from Tab 2)

**Inputs you set here (all editable):**
- **Model:** Which model (e.g., Opus 4.6 = 200K context window)
- **Target percentage:** How much context to use (e.g., 50% = 100K usable tokens)
- **Hard stop percentage:** Absolute maximum — if it hits this, something's wrong (e.g., 65%)

**What it calculates and shows transparently:**

*Phase 1 breakdown:*
| Component | Tokens | % of Model |
|-----------|--------|-----------|
| First-phase rule set | 15,000 | 7.5% |
| Agent MDs (coder + reviewer + tester) | 4,000 | 2.0% |
| Testing budget | 5,000 | 2.5% |
| Carry-forward summary (none for Phase 1) | 0 | 0% |
| **Available for PRD coding chunk** | **76,000** | **38.0%** |
| **Phase 1 Total** | **100,000** | **50.0%** |

*Phases 2+ breakdown:*
| Component | Tokens | % of Model |
|-----------|--------|-----------|
| Remaining-phase rule set | 4,500 | 2.25% |
| Agent MDs (coder + reviewer + tester) | 4,000 | 2.0% |
| Testing budget | 5,000 | 2.5% |
| Carry-forward summary from previous phase | 2,000 | 1.0% |
| **Available for PRD coding chunk** | **84,500** | **42.25%** |
| **Phases 2+ Total** | **100,000** | **50.0%** |

Phase 1 has less room for the actual coding chunk because its rule set is bigger. The calculator handles this automatically.

**Bottom line output:** "Your PRD needs to be split into N phases. Phase 1 gets X tokens of PRD content. Phases 2-N each get Y tokens of PRD content."

**The visual:**
- Percentage bars for each component, stacked
- Phase 1 bar looks different from Phases 2+ bar (bigger rules section, no carry-forward)
- All numbers are live-editable — change any input and everything recalculates
- Warning if the math doesn't work (e.g., rule sets + overhead already exceed the target)

### Part B — The AI Chunking Room (Own AI, Own MD)

Separate AI from Tabs 1 and 2. Own focused MD file.

**Its ONLY job:** Take this PRD and break it into the exact number of chunks that Part A calculated, respecting the token sizes Part A determined.

**The MD tells it:**
- Your sole job is to split this app spec into properly sized phases
- Phase 1 gets a larger coding chunk (X tokens) — this is the foundation
- Phases 2+ each get Y tokens of coding content
- Each phase must be fully testable on its own — don't cut in the middle of a feature
- Format so the coding agent can build and verify each phase cleanly
- Chunks must be logical units of work, not arbitrary cuts at a token boundary

**What you see after chunking:**

Each phase shown as a card:
- Phase number
- The actual PRD content for that phase
- Token count (should match the calculator's target)
- Which rule set it uses (first-phase or remaining-phase)
- What the complete "phase package" looks like assembled: rule set + coding chunk + testing budget = total

**This is a preview of exactly what gets sent to the agent.** You can read every phase package before anything runs.

### What This Tab Produces

The final phase packages — ready to execute. Each one contains:
- The appropriate rule set (first-phase for Phase 1, remaining-phase for the rest)
- The PRD coding chunk for that phase
- The build sequence configuration from Tab 2
- Token budget allocations

These feed directly into Tab 4.

---

## Tab 4: Operations Dashboard (Mission Control)

**Purpose:** NASA's control room. Live monitoring, queue management, and build history.

### Top Bar — Always Visible

- **Phase progress dots:** Filled/colored for completed, highlighted for current, empty for remaining (●●●●○○○)
- **Current agent role indicator:** Which agent is active (Coder? Reviewer? Tester?)
- **Live token gauge:** Real-time counter showing token usage as a percentage. Climbing toward target (50%). If it creeps to 52-53%, probably fine. Hits 60%, 65%, 77% — something's wrong, you can intervene.
- **Hard stop marker:** Visual line on the gauge showing the hard stop percentage from Tab 3.

### Live Log

Real-time scrolling feed of what the agent is doing right now.

### Phase Detail View

Click any phase dot to drill into it:
- What was built
- Reviewer findings
- Test results
- Summary passed to the next phase
- Token usage breakdown (actual vs budgeted)

### The Queue

Multiple builds prepped in Tabs 1-3, lined up and ready:
- **Current build** running — visible live
- **Next builds** queued below, in order
- When current finishes, next starts automatically
- Click into any queued build to review while current runs
- Reorder queue, push things back or forward
- Organize the next build while one is running

### History

- Pull up any past completed build
- See all phases, step into any for details
- Compare past builds to current
- Mini-viewer showing each tab's output in sequence

---

## My Analysis: What I'd Do Differently, What's Missing, What to Add

### What You Got Right

**Separation of concerns.** One AI per objective is the right call. Mixing "merge my rules" with "chunk my PRD" in one conversation produces worse results for both. Focused agents with focused MDs outperform generalist ones.

**"AI proposes, you approve."** Most people skip this. Having a human checkpoint — especially for rule merging and phase chunking — prevents compounding errors. One bad merge or one bad chunk ruins everything downstream.

**Making the math visible.** Highest-value decision in the whole system. Most build tools are black boxes. Showing where every token goes lets you learn, adjust, and catch problems before they become expensive failures.

**Presets with versioning.** Right architecture. You'll iterate fast on configurations, and being able to roll back without losing experiments is crucial.

### What I'd Add

**1. Phase Package Preview (sub-view in Tab 3)**

Before hitting go, see the fully assembled package for every phase — the literal content that will be sent to the model. Not just token math, but actual text. Rule set + coding chunk + agent MD + carry-forward = what the Coder agent will see. Like a print preview. You'd catch problems here that numbers alone won't reveal.

**2. Context Decay Indicator (in Tabs 3 and 4)**

Even within your 50% target, model attention degrades over long contexts. Tokens at position 10,000 don't get the same attention as tokens at position 1,000. A simple indicator showing high-attention vs low-attention zones helps you decide what goes at the TOP of each phase package (most important first). Rule sets and critical instructions at the beginning, carry-forward summaries later.

**3. Phase Dependency Map (sub-view in Tab 3)**

Phases are currently linear: 1 then 2 then 3 then 4. But sometimes Phase 3 and Phase 4 are independent and could run in parallel. A simple dependency view (this phase needs that phase first, but these two are independent) lets you parallelize when possible. AutoForge already has parallel mode — this would flag which phases can overlap.

**4. Overhead Audit (summary panel in Tab 2)**

After configuring all build parameters, show one summary: "Your total non-coding overhead per phase is X tokens (Y%)." If agent MDs, hooks, testing budget, and carry-forward eat 40% of your budget, you only have 10% left for actual coding — you'd want to know that before reaching the chunker. A warning like "Your overhead exceeds 30% — consider simplifying" saves headaches.

**5. What-If Mode (toggle in Tab 3)**

Compare scenarios without committing: "What if I use Sonnet instead of Opus? What if I target 60%? What if I shrink the remaining-phase rule set?" Side-by-side comparison showing how phase count and chunk sizes change. Cheap to implement (just re-running math), extremely valuable for decisions.

**6. Cost Estimation (in Tabs 3 and 4)**

Every API call costs money. You know the token counts. Show estimated cost per phase and total build cost. Even rough: "This 12-phase build will cost approximately $X." When queuing multiple builds, knowing total queue cost matters.

**7. Error Recovery Strategy (settings in Tab 2, controls in Tab 4)**

If Phase 4 of 8 fails, do you:
- Retry Phase 4 from scratch?
- Retry with a modified chunk (maybe it was too big)?
- Roll back to Phase 3 checkpoint and try different chunking?
- Skip Phase 4 and try Phase 5 (if they're independent)?

Should be configurable in Tab 2 and show recovery options in the Dashboard when failure happens.

**8. Build Comparison View (sub-view in Tab 4 history)**

Side-by-side comparison of two builds. Same PRD, different rule sets — what changed? Same rules, different chunking — how did test results differ? This is how you learn which configurations actually produce better code.

**9. Rule Set Analytics (sub-view in Tab 1 after builds exist)**

After several builds, surface data: "Builds using Rule Set V3 had 40% fewer test failures than V2." Turns versioning from gut feeling into data-driven decisions.

**10. Carry-Forward Editor (pause point in Tab 4)**

The auto-generated summary passed between phases is critical. If it's bad, the next phase starts confused. Add the ability to edit the carry-forward before the next phase starts. Optional toggle in Tab 2 — the Dashboard pauses between phases and shows "Approve / Edit / Regenerate."

**11. Token Usage History (chart in Tab 4)**

After builds complete, show budgeted vs actual tokens per phase. Tells you whether your 5,000-token testing budget was right, or if testing consistently used 8,000. Over time, calibrate budgets with real data instead of guessing.

### Summary of Additions

| Addition | Where It Lives | Why |
|----------|---------------|-----|
| Phase Package Preview | Sub-view in Tab 3 | See exactly what gets sent before running |
| Context Decay Indicator | Gauge in Tabs 3 and 4 | Know where attention drops off |
| Phase Dependency Map | Sub-view in Tab 3 | Enable parallel phases |
| Overhead Audit | Summary panel in Tab 2 | Catch bloated configs early |
| What-If Comparisons | Mode toggle in Tab 3 | Compare configurations side-by-side |
| Cost Estimation | Shown in Tabs 3 and 4 | Know what the build will cost |
| Error Recovery Config | Settings in Tab 2, controls in Tab 4 | Handle failures intelligently |
| Build Comparison | Sub-view in Tab 4 history | Learn from past builds |
| Rule Set Analytics | Sub-view in Tab 1 | Data-driven rule set improvement |
| Carry-Forward Editor | Pause point in Tab 4 | Human checkpoint between phases |
| Token Usage History | Chart in Tab 4 | Calibrate budgets with real data |

---

## The Complete Flow — End to End

```
PREPARATION PHASE (Tabs 1-3, done before any code runs)

Tab 1: Rule Set Builder
  Import source documents (originals preserved)
  AI proposes merges, you approve
  Assemble into final documents
  OUTPUT: First-phase rule set + Remaining-phase rule set
    |
    v
Tab 2: Build Planner
  Choose preset (Full Build / Feature Add / Reverse Engineer / etc.)
  Configure agent roles (Coder, Reviewer, Tester — names, MDs, models)
  Set build sequence (step order, timeouts, failure handling)
  Configure hooks (pre-commit, post-phase, on-failure)
  Set testing strategy (types, budget, coverage threshold)
  Set context management (carry-forward, summary style)
  Set commit and error handling strategies
  Overhead audit: see total non-coding token cost
  OUTPUT: Complete build configuration + token overhead totals
    |
    v
Tab 3: Phase Chunker
  INPUTS: Rule sets (Tab 1) + Build config and overhead (Tab 2) + PRD
  Token calculator shows the math:
    Phase 1: rules(15K) + agents(4K) + testing(5K) + coding(76K) = 100K (50%)
    Phase 2+: rules(4.5K) + agents(4K) + testing(5K) + carry(2K) + coding(84.5K) = 100K (50%)
  AI chunks the PRD into N phases respecting these budgets
  Phase package preview: see exactly what each phase sends to the model
  OUTPUT: N ready-to-execute phase packages
    |
    v

EXECUTION PHASE (Tab 4)

Tab 4: Operations Dashboard
  Phase progress dots
  Live token gauge with hard stop marker
  Current agent role indicator
  Live log of agent activity
  Phase detail view (click any dot)
  Optional carry-forward editor between phases
  Build queue (auto-advance, reorder, preview next)
  Cost tracking (estimated vs actual)
  Build history with comparison view
  OUTPUT: Completed software + build data for future calibration
```

---

## Future Addition: PRD Maker

Will be built as one of the first projects using this system. Once complete, it becomes Tab 0 — the starting point before the Rule Set Builder. The full pipeline then becomes:

**PRD Maker -> Rule Set Builder -> Build Planner -> Phase Chunker -> Operations Dashboard**

---

## Glossary

| Term | Meaning |
|------|---------|
| **Rule set** | Merged document of coding standards/rules injected into agent sessions |
| **First-phase rule set** | Larger rule set used only in Phase 1 (sets the foundation) |
| **Remaining-phase rule set** | Lighter rule set used in Phases 2+ (references what's already built) |
| **Phase package** | Complete bundle sent to the model: rule set + PRD chunk + agent MD + carry-forward summary |
| **Token budget** | Tokens allocated for a specific component (testing, rules, coding, etc.) |
| **Target percentage** | The percent of model context you aim to use per phase (e.g., 50% of 200K = 100K) |
| **Hard stop** | Absolute maximum percent — if usage crosses this, something is wrong |
| **Carry-forward** | Summary from a completed phase injected into the next phase's context |
| **Overhead** | Total tokens consumed by everything that is not the PRD coding chunk |
| **Preset** | Saved build configuration for a specific build type |
| **Phase package preview** | Ability to see exactly what will be sent to the model before running |
