# DunkStack Full Feature Inventory

Compiled from all design documents, handoffs, blueprints, and iteration branches.
Two lists: (1) PRD Machine missing details, (2) Extra features beyond the current MVP.

---

## LIST 1: PRD Machine -- Missing Details, Fallen-Through-Cracks, Caveats

Everything below was described in various documents but is NOT currently captured
in the Agent OS implementation (`server/services/agent_os_*`).

---

### 1.1 The 11-Stage Pipeline (vs Current 8-Stage)

The current Agent OS session has 8 stages. OPERATIONAL_TRUTH_v3.md describes 11.
Three stages are missing entirely, plus one is incomplete:

| # | Stage | Status | Source |
|---|-------|--------|--------|
| 1 | Intake | Exists (55%) | agent_os_intake.py |
| 2 | Categorization into Product Layer | Exists (partial) | agent_os_intake_dock.py |
| **3** | **Technical Refinement** | **MISSING** | OPERATIONAL_TRUTH_v3 |
| 4 | Coverage Assessment | Exists (partial) | agent_os_features.py |
| **5** | **Recalibration** | **MISSING** | OPERATIONAL_TRUTH_v3 |
| 6 | Gap-Fill Q&A | Exists (70%) | agent_os_features.py |
| 7 | Full Puzzle Assembly | Exists (60%) | agent_os_product.py |
| 8 | Mechanism Analysis | Exists (70%) | agent_os_mechanism.py |
| 9 | Spec Generation | Exists (75%) | agent_os_specs.py |
| **10** | **Final Blueprint with Build Learnings** | **MISSING** | OPERATIONAL_TRUTH_v3 |
| **11** | **Golden Orange Feature Extraction** | **MISSING** | OPERATIONAL_TRUTH_v3 |

**Stage 3 -- Technical Refinement:**
> "Layman to precise technical language. Always reference original for verification."

This is the explicit babble-to-tech translation step. Not "implicit in Claude's behavior"
but a dedicated stage that produces `original_quote -> technical_translation` pairs with
provenance tracking. The rant-to-prd-spec calls this the hardest part.

**Stage 5 -- Recalibration:**
> "Review assembled picture as whole. Identify contradictions. Resolve before questions."

A dedicated contradiction-resolution pass BEFORE gap analysis. Currently the system goes
straight from coverage assessment to questions, which means contradictions get surfaced
as gaps rather than being resolved first.

**Stage 10 -- Final Blueprint with Build Learnings:**
> "Mechanism learnings, backup briefs, concern flags, opportunity flags, contextual build notes"

The companion sheet. Goes beyond the PRD itself to include:
- Mechanism learnings (what the scoring revealed about the app's nature)
- Backup briefs (for each close-call mechanism, what to do if the primary fails)
- Concern flags (things that could go wrong during implementation)
- Opportunity flags (things that emerged during analysis that could add value)
- Contextual build notes (implementation hints the builder should know)

**Stage 11 -- Golden Orange Feature Extraction:**
> "Exhaustive feature backlog at spec level. Natural extensions, cross-mechanism,
> competitive, scale, monetization, delight features. Utopia line marked explicitly."

This is the "Feature Imagination Phase" -- the system proactively generates every
possible feature, organized into categories:
- Natural extensions (obvious next features)
- Cross-mechanism features (features that combine multiple mechanisms)
- Competitive features (what competitors have that this app doesn't)
- Scale features (what you need when you grow)
- Monetization features (how to make money from this)
- Delight features (things that make users love it)
- **Utopia line** -- explicit marker where features cross from "practical value" to
  "diminishing returns." Everything above the line: build it. Below: nice to have.

---

### 1.2 Caveat Appendix -- 3+ Mechanism Edge Case

Current implementation only handles 2 options within 15%. The user explicitly called out:
what if 3 mechanisms are within 15% of each other?

**What needs to happen:**
- Detect N-way close calls (not just pairwise)
- Present all N options with relative scoring
- If 3+ are within 15%, spec out the top 2 AND preserve the 3rd in the Caveat Appendix
- Each entry needs: switch trigger, switch cost, affected files, dependencies affected
- If git worktree integration exists, proof-of-concept branches for alternatives

**Currently in addendum (lines 284-319) but not fully specified for N>2:**
The Caveat Appendix format only shows pairwise "Selected vs Alternative." Needs extension
for "Selected vs Alternative 1 vs Alternative 2" with cross-comparison.

---

### 1.3 Two Competing Architectures (Need Reconciliation)

There are TWO different rant-to-spec systems designed:

**Architecture A: Terminal Pipeline (docs/rant-to-prd-spec.md)**
- 7 stages, bash-orchestrated, CLI-native
- `claude -p` invocations per stage
- Files on disk (JSON per stage directory)
- DDR quality metrics, 87-item completeness checklist
- Deterministic (temperature 0)
- Provenance tracking matrix with 8 item types
- Cross-stage data integrity rules (8 rules)
- Hooks system (pre-stage, post-stage, post-write)

**Architecture B: Python Engine (handoffs/rant_to_spec_engine.md)**
- 5 stages, Python async API (`RantEngine` class)
- Pydantic models in memory + JSON serialization
- Developer's Choice with confidence scoring
- Priority Profiles with weighted dimensions
- 11 builder-layer dimensions
- Autopilot/Soft/Deep classification buckets
- Auto-promotion when scores exceed threshold
- 5 built-in profiles (bootstrapper, funded_startup, enterprise, solo_saas, prototype)

**What Architecture B has that A doesn't:**
- Developer's Choice principle (confidence-weighted pre-filled recommendations)
- Priority Profiles (9 weighted scoring dimensions)
- Dimension Relevance Mapping (auto-selects relevant dimensions per category)
- 11 builder-layer dimensions (vendor_lock_in, maintenance_burden, scaling_ceiling, etc.)
- Autopilot/Soft/Deep classification buckets
- Weighted scoring formula with auto-promotion

**What Architecture A has that B doesn't:**
- Detail Density Ratio (DDR) quality metric
- 87-item completeness checklist across 11 categories
- Item Type Taxonomy (8 types: mechanism, behavior, constraint, etc.)
- Provenance tracking matrix
- Cross-stage data integrity rules
- Hooks system

**Decision needed:** Merge the best of both into the Agent OS implementation. The Python
engine's Developer's Choice + Priority Profiles + the terminal pipeline's quality metrics
and provenance tracking.

---

### 1.4 Developer's Choice Scoring -- Missing Dimensions

Current `agent_os_mechanism.py` has 4 scoring dimensions:
`complexity`, `standards_match`, `scalability`, `maintainability`

The addendum specifies 6:
`implementation_speed` (20%), `maintainability` (20%), `user_experience` (20%),
`security` (15%), `cost` (10%), `brand_alignment` (15%)

The Python engine specifies 11 builder-layer dimensions:
`vendor_lock_in`, `maintenance_burden`, `scaling_ceiling`, `data_portability`,
`integration_ecosystem`, `team_learning_curve`, `security_implications`,
`regulatory_compliance`, `fallback_complexity`, `community_support`,
`monetization_compatibility`

**What's needed:**
- Expand to at minimum the 6-dimension model from the addendum
- Frame as "X% of developers would choose this" (not raw 0-1 scores)
- Priority Profiles that weight these dimensions differently per user type
- Dimension Relevance Mapping (not all dimensions matter for every decision)

---

### 1.5 Coverage Assessment Numbers

OPERATIONAL_TRUTH_v3 provides concrete expectations:
> "Detailed user: 65-70%. Average: 10-30%."

And a learning curve metric:
> "Learning over 5-10 projects reduces questions to unique ~13%."

These numbers should be surfaced to the user during the process ("You've described
approximately 45% of the app so far") and used to calibrate expectations.

---

### 1.6 PRD Quality Scoring (Post-Generation Gate)

From build-intelligence-handoff: Score the finished PRD on 1-5 across 6 dimensions:

| Dimension | Weight |
|-----------|--------|
| Completeness | 25% |
| Clarity | 20% |
| Consistency | 15% |
| Feasibility | 15% |
| Testability | 15% |
| Scope | 10% |

Build gating: <2.0 blocks build, 2.0-3.0 warning, 3.0-4.0 good, 4.0-5.0 excellent.
This is the quality gate between PRD generation and handing off to the builder.

---

### 1.7 Accuracy Review Step

From IdeaForge blueprints `00-accuracy-review.md`: After PRD generation, verify claims
against actual source code. Categorize findings as INCORRECT, INCOMPLETE, or CONFIRMED.

> "The issues are implementation details, not design flaws -- the kind of things that
> surface when you map a plan against actual code."

This should be a standard post-PRD verification stage.

---

### 1.8 Provenance Tags (Not Implemented)

Every item in the final PRD should carry:
- `[USER]` -- directly stated by user
- `[AUTO-FILL]` -- system inferred with high confidence
- `[USER-DECIDED]` -- user chose from options
- `[RECOMMENDED]` -- Developer's Choice, user accepted
- `[DETECTED]` -- reverse-engineered from code (Codebase Reality Engine)
- `[DESCRIBED]` -- user described existing code behavior
- `[INFERRED]` -- system inferred from code or description
- `[FEATURE-ADD-vN]` -- added in expansion round N

---

### 1.9 Context Window Chunking for Build System

The PRD output needs to be sized for the build system's context window:
- Feature specs should be individually loadable
- Phase sizing based on build system constraints
- The "3-layer structure" (standards/product/specs) enables selective loading
- Currently specs are per-feature (good) but no explicit chunking strategy

---

### 1.10 Cross-Project Learning

> "Learning over 5-10 projects reduces questions to unique ~13%."

The system should track which questions were asked across projects and which answers
were always the same. After enough projects, auto-fill the universally-answered questions
and only ask the truly unique ones.

---

### 1.11 Verification Agents (Stage N.5)

From the addendum: Quality-checking agents that verify each stage's output before
proceeding. "Stage 1.5: Transcription Verifier" ensures zero-loss translation.
None exist in either system. Each stage should have a lightweight verification pass.

---

### 1.12 LLM Orchestration (The Engine Connection)

The single biggest gap: the Agent OS services generate prompts but never send them
to Claude. Every `get_*_prompt()` method produces a beautifully structured prompt,
and every `process_*()` method can ingest the JSON response, but the actual
"send to Claude -> get response -> feed into process method" orchestration doesn't exist.

This is the car with no engine connected.

---

### 1.13 The 8 Categorization Targets

OPERATIONAL_TRUTH_v3 maps intake to 8 product-layer files:
`mission.md`, `roadmap.md`, `tech-stack.md`, `mechanisms.md`,
`ui_vision.md`, `data_model.md`, `integrations.md`, `business_rules.md`

Current agent_os_intake_dock.py maps to a different file structure. These should
be reconciled with the 3-layer model.

---

### 1.14 Anti-Pattern Documentation in PRD Output

The standards layer should include explicit anti-patterns:

> "Banned Patterns: alert(), confirm(), prompt(), console.log for feedback,
> text-only empty states, edit-first navigation, inline styles"

19 explicit anti-patterns documented in IdeaForge standards. These prevent agents
from making common mistakes and should be standard PRD output.

---

### 1.15 Cost-Driven Architecture in PRDs

Both the Walkie-Talkie and Holding Patterns PRDs include explicit cost math.
PRDs should calculate API cost implications:

> "Over a full workday with 20 task transitions, that's $18 in cold starts vs
> ~$0.003 in holding patterns."

Generated PRDs should include cost estimates for different implementation approaches.

---

### 1.16 Dependency Chains Between PRDs

Holding Patterns declares: "DEPENDS ON: Walkie-Talkie system."
The PRD machine should handle ordering between PRDs when building multiple systems.

---

## LIST 2: Extra Features -- Full Inventory Beyond Current MVP

Everything below was designed/discussed but is NOT in the current DunkStack.
Organized by category with source references.

---

### 2.1 SESSION INFRASTRUCTURE

**A. Bridge/Session Continuity System** `[OPERATIONAL_TRUTH_v3, BASE_BUILD_PRD]`
- `.agent/bridge.md` -- complete state save on session end
- `.agent/working_memory.md` -- rolling context the agent updates
- `.agent/index.md` -- master navigation map of all files
- Resume sequence: read index > working_memory > bridge > delete bridge
- Cost: ~2,500-3,000 tokens per bridge cycle (2.5-3% of 100K budget)
- Trigger: human departure, session timeout, emergency disconnect

**B. Walkie-Talkie Communication System** `[PRD_WALKIE_TALKIE_SYSTEM]`
- Bidirectional in-flight messaging (user talks to working agent)
- PreToolUse hook message injection
- Per-session async message queue
- Agent-initiated `[WAITING]` tags for questions
- CountdownTimerBar with auto-reply
- Walkie-talkie input bar (amber-themed)
- Check frequency settings (every_tool_call / per_feature / never)
- 3-5x cost reduction via sustained API calls

**C. Automated Holding Patterns** `[PRD_AUTOMATED_HOLDING_PATTERNS]`
- Zero-cost session persistence between tasks
- 4-tier strategy: WAITING pause > heartbeat micro-read > context summary > proactive check
- Hold signal file (filesystem-based task injection)
- Cost: ~$0.003/day vs $18/day in cold starts (6000x savings)
- Hold-aware walkie-talkie integration
- Configurable strategy, budget, max cycles

**D. Idle/Pause Modes** `[OPERATIONAL_TRUTH_v3, BASE_BUILD_PRD]`
- Three modes: `idle` | `continue` | `autopilot`
- Control via `.agent/comms/control.md`
- Token cost: ~1,200 tokens/hour (~1.2% of budget)

---

### 2.2 CONTEXT WINDOW MANAGEMENT

**E. Context Gauge (Real-Time Token Tracking)** `[BASE_BUILD_PRD]`
- Visual progress bar with color-coded zones (green/yellow/orange/red)
- Token Log Panel (scrollable per-call list with costs)
- Session Summary (totals, averages, cost)
- Data from Anthropic API exact token counts

**F. Context Safety System (3-Tier Protection)** `[BASE_BUILD_PRD]`
- Tier 1 -- WARNING (45%): inject awareness message
- Tier 2 -- HANDOFF (47.5%): stop work, write handoff file
- Tier 3 -- HARD STOP (50%): terminate session
- Post-stop code review via cheap model (Haiku)
- Configurable thresholds per model size (200K vs 1M)

**G. Compaction Recovery** `[BASE_BUILD_PRD]`
- Detect when conversation history was compacted
- "Trust the files, not conversation history"
- Auto re-read: index.md > working_memory.md > from_human.md

**H. Selective File Reading Budget** `[BASE_BUILD_PRD]`
- Budget: 4,000 tokens per turn for file reads
- <50 lines: read whole file. >50 lines: targeted line ranges
- Configurable with measurable impact

**I. 85% Utilization Thesis** `[OPERATIONAL_TRUTH_v3, BASE_BUILD_PRD]`
- Standard: 50% effective utilization (~92K of 200K)
- File-based: 85% effective utilization (~156K of 200K)
- 70% more effective capacity, same model, same price
- Output token redirection saves 3-5x (output costs more than input)

---

### 2.3 BUILD GOVERNANCE

**J. Decisions Log** `[BASE_BUILD_PRD]`
- Append-only `.agent/progress/decisions.log`
- Every non-trivial choice logged with reasoning
- Prevents revisiting settled questions (token waste)
- Swarm value: shared brain across agents
- "One agent's learning becomes every agent's learning"

**K. Scope Boundary File** `[BASE_BUILD_PRD]`
- IN SCOPE, OUT OF SCOPE, DEFER, QUALITY BOUNDARY, STOP SIGNALS
- Prevents gold-plating, feature drift, over-engineering
- Agent reads before starting any sub-task

**L. Structured Change Tracking** `[BASE_BUILD_PRD]`
- Semantic diffs: What changed + Why + Impact + Decision ref
- Goes beyond git diff by capturing intent
- Enables "why was this changed?" queries

**M. Build Analytics & Measurement** `[BASE_BUILD_PRD]`
- 30 metrics across 4 categories: Context Efficiency (8), Build Quality (8),
  Cost Efficiency (7), Session Lifecycle (7)
- Per-session JSON, aggregate JSON, automated reports
- Baseline comparison system (A/B with and without DunkStack)
- File-to-chat ratio as primary health metric (target: >10x)

**N. Self-Optimization Engine** `[BASE_BUILD_PRD]`
- Lever registry with bounds, step size, target metric, constraint
- Conservative hill-climbing: change ONE lever, wait 3 sessions, measure
- Constraint-guarded: "make X better but Y must not get worse"
- Explicitly not ML -- simple, auditable, transparent

---

### 2.4 INTELLIGENCE & LEARNING

**O. Build History Intelligence** `[build-intelligence-handoff]`
- `build_metrics` table per build (duration, quality, failures, tech stack)
- `feature_patterns` table aggregated across builds
- Pitfall warnings injected into coding prompts
- Time estimation from historical data
- Risk flagging (high/medium/low badges based on success rates)

**P. Continuous Improvement Pipeline** `[build-intelligence-handoff]`
- Prompt hashing and versioning
- A/B testing framework for prompts (statistical significance)
- Pattern Library auto-generation (at 100+ builds per category)
- Monthly analysis reports
- User feedback collection (post-build 1-5 star rating)

**Q. Cross-Project Learning** `[OPERATIONAL_TRUTH_v3]`
- Track questions and answers across projects
- Auto-fill universally-answered questions
- "5-10 projects reduces questions to unique ~13%"

**R. Confidence Scoring on File Reads** `[BASE_BUILD_PRD]`
- Track read depth: FULL, SECTION, SUMMARY, INDEX
- Tag downstream decisions with confidence level
- When things go wrong, trace to decisions made on partial reads
- Prevents "re-read everything and start over" pattern

**S. Agent Self-Verification Loops** `[BASE_BUILD_PRD]`
- Before major actions: write "I believe state is X"
- Then verify against actual files
- If mismatch: stop and reconcile before proceeding
- Cost: ~200-400 tokens per verification

**T. Semantic Compression on Working Memory** `[BASE_BUILD_PRD]`
- Recent (2-3 sessions): full detail
- Older: auto-compress to one-line summaries
- Ancient: category-level summaries
- Mirrors human memory (detailed recent, fuzzy distant)

---

### 2.5 NOTIFICATIONS & COMMUNICATIONS

**U. Notification Architecture** `[OPERATIONAL_TRUTH_v3]`
- Twilio: SMS + screen-flashing for blockers/emergencies
- Pushover: app notifications (normal + flash tiers)
- Telegram: app control, dashboard monitoring, Claude bot style
- Config.yml has the keys but no implementation exists

**V. Communications System (.agent/comms/)** `[OPERATIONAL_TRUTH_v3, BASE_BUILD_PRD]`
- `to_human.md` -- agent > human (append-only)
- `from_human.md` -- human > agent (human writes)
- `control.md` -- mode control (idle/continue/autopilot)
- Chat as "thin status feed" (3-sentence max)
- Both directions use files, not chat

---

### 2.6 RANT ENGINE DELIVERY MODES

**W. AutoForge Integration (Connection A)** `[rant_engine_connections]`
- New router `server/routers/rant_spec.py` (8 REST + 1 WebSocket)
- "Rant My Idea" toggle in project creation
- Decision review: Autopilot (collapsed), Soft (cards), Deep (full templates)
- "Accept All Developer's Choices" master button
- Priority profile selector

**X. Standalone Rant-to-Spec App (Connection B)** `[rant_engine_connections]`
- Independent web app, no AutoForge dependency
- Session library (save/resume rants)
- 4 export formats: AutoForge XML, plain text, markdown, JSON
- Simple local auth
- Custom priority profile save/edit
- Potential standalone SaaS product

**Y. Mobile/Web Admin Capture Panel (Connection C)** `[rant_engine_connections]`
- Ultra-minimal capture UI for on-the-go ideas
- Voice input via Web Speech API
- Offline capable (service worker + localStorage)
- Swipe gestures (right=save+new, left=discard)
- Tinder-style swipe for quick decisions
- Embeddable widget (`<RantCapture>` React component / iframe)
- Batch resolve via swipe

---

### 2.7 IDEAFORGE WORKSPACE

**Z. IdeaForge Million-Token Workspace** `[ideaforge-million-token-workspace, blueprints/]`
- Full-page `/#/workspace` route
- 1M token context window
- Full agent mode (Read/Write/Edit/Bash -- not read-only)
- Multi-conversation management with sidebar
- Context Budget Bar (segmented, real-time)
- Auto-summary system (every 50 messages via Haiku)
- Chat forking (branch from any message)
- Inject from another chat (cross-pollination)
- File Library (upload, organize, inject into context)
- GitHub repo connection (clone, browse, read/write, commit/push)
- Pin/star conversations, user-created categories
- Server-side search, export to markdown
- Standalone SaaS potential

---

### 2.8 UNIVERSAL DASHBOARD

**AA. Manifest-Driven Dashboard** `[universal-dashboard-spec]`
- `.swarm/manifest.yaml` declares system shape
- Dashboard renders purpose-built workspace from manifest
- Zero code changes for new system types
- Three-level navigation: Meta > System > Component
- 6 layout engines: pipeline, swarm, graph, kanban, tree, custom
- Type-aware component editors (agent, schema, script, hook, output)
- Persistent tabs with lateral navigation
- Command Palette (Ctrl+K)
- System Creation Wizard + Template Library
- Real-time pipeline monitoring
- Log streaming
- AI actions with diff confirmation
- Cross-system search
- Contextual AI (context switches with tabs)

---

### 2.9 AI ADVISORS

**AB. AI Setup Advisor** `[autoforge-roadmap-v2]`
- Chat agent analyzing project spec
- Recommends optimal build settings
- Non-hardcoded prompts (editable in Settings UI)
- "Accept All Recommendations" button

**AC. AI Design Advisor** `[autoforge-roadmap-v2]`
- Chat agent for visual style selection
- Understands 12 styles, 25 palettes, 4 accessibility modifiers
- Live style preview that updates with recommendations
- Side-by-side comparison
- Knowledge Auto-Updater (monthly RSS scraping from 8 design sources)
- Audience-specific design guidance

**AD. Care Levels 1-5** `[autoforge-roadmap-v2]`
- Level 1 (Autopilot): 2-3 min, AI decides everything
- Level 2 (Light Touch): 5-10 min, few questions
- Level 3 (Balanced): 15-25 min, current default
- Level 4 (Detailed): 25-40 min, full walkthrough
- Level 5 (Architect): 40-60+ min, review every feature item

---

### 2.10 POST-BUILD PIPELINE

**AE. Post-Build Reports** `[post-build-reports-handoff]`
- Docs Agent (generates documentation from code)
- Performance Agent (profiles and benchmarks)
- Security Agent (audits and penetration tests)
- All three run in parallel after QA passes

**AF. Pre-Build Intelligence** `[pre-build-intelligence-handoff]`
- Spec Analyzer (completeness score 1-5, blocks if <3)
- Architecture Planner (database, API, component tree)
- Outputs ARCHITECTURE.md referenced by all agents

---

### 2.11 FEATURE LIFECYCLE

**AG. Feature Addition Engine (F1-F7)** `[rant-to-prd-addendum, PHASE_7]`
- F1: Feature Transcriber (extract NEW features, deduplicate)
- F2: Impact Classifier (map to existing PRD sections)
- F3: Feature Gap Analyst (scoped completeness check)
- F4: Feature Decision Facilitator (interactive)
- F5: Feature Mechanism Analyst (compatibility + scoring)
- F6: PRD Merger (version incremented, provenance tags)
- F7: Autoforge Bridge (generate new features for builder)
- PRD as living document (v1.0 > v1.1 > v1.2)
- Batch additions with inter-feature conflict detection

**AH. Codebase Reality Engine** `[rant-to-prd-addendum, PHASE_7]`
- Mode A: With code access (scan, extract, generate AB-PRD)
- Mode B: Without code (questionnaire, inference, descriptive AB-PRD)
- Drift Report (what changed: same/changed/added/removed)
- Reconciled PRD = original + drift + reality

**AI. Upstream Feature Watcher** `[upstream-feature-watcher]`
- Monitor upstream repo for merged PRs (every 6 hours)
- Claude-powered divergence analysis
- Recommendation engine: PORT/SKIP/BOOKMARK/ALREADY_HAVE
- Auto-port via Claude Opus for trivial changes
- BLUEPRINT.md auto-update

---

### 2.12 SWARM ARCHITECTURE

**AJ. Swarm Role Specialization** `[BASE_BUILD_PRD, OPERATIONAL_TRUTH_v3]`
- Librarian: reads all files, maintains index (60K context budget)
- Builder: reads current feature + deps only, writes code (60K budget)
- Critic: reads changed files + tests, writes reviews (40K budget)
- "The Librarian answers 'where is X?' so the Builder never wastes context"

**AK. Scaling Path** `[OPERATIONAL_TRUTH_v3]`
1. Single agent, 200K subscription -- prove file-based + Agent OS
2. 2-3 agents, 200K subscription -- prove coordination
3. Single agent, 1M API -- full-scale builds
4. Swarm (5-25 agents), 1M API -- specialized roles
5. Multi-swarm (5x25) -- management layer, unlimited scaling

---

### 2.13 INFRASTRUCTURE

**AL. Boilerplate Strategy** `[OPERATIONAL_TRUTH_v3]`
- Template project deployment from GitHub repos
- Flutter mobile boilerplate (commercial rights, Supabase)
- Web boilerplate (personal use only, Supabase)
- Copy is first step in Code Mode

**AM. Production Pipeline Steps 10-12** `[OPERATIONAL_TRUTH_v3]`
- Step 10: Tutorial Generation (voice AI + Playwright screen capture)
- Step 11: Landing Page + Marketing with Automated GIFs
- Step 12: Golden Orange Feature Extraction

**AN. Configurable Agent Budget Levers** `[autoforge-roadmap-v2]`
- Replace 6 hardcoded constants with 9 configurable levers in SQLite
- Default budget drops from 45% to 30%
- Accessible from Settings UI

---

### 2.14 BONUS GOLD (Not Discussed Yet)

These are concepts that stood out as uniquely valuable and weren't explicitly part
of any conversation:

**AO. Baseline Runner for A/B Comparison** `[BASE_BUILD_PRD]`
> "Create a 'baseline mode' toggle that runs a standard agent session WITHOUT the
> DunkStack file protocol. Same task, same model, normal behavior. Generates control
> data for A/B comparison."

Self-proving software. The system scientifically proves its own value proposition.

**AP. Working Memory Frequency as Tunable Lever** `[BASE_BUILD_PRD]`
How often the agent saves state is a tunable parameter (every N turns). Too frequent =
wasted tokens. Too infrequent = data loss risk. Optimal is empirically discoverable.

**AQ. File-to-Chat Ratio as Health Metric** `[BASE_BUILD_PRD]`
> "file_vs_chat_ratio: 14.2x (target: >10x)"

Primary diagnostic metric. If this ratio drops, the file protocol is failing.

**AR. Compliance Reinforcement** `[BASE_BUILD_PRD]`
Common drift patterns the agent must catch itself on:
- "Let me explain..." -> write to file
- "Here's what I found..." -> write to file
- Providing code snippets in chat -> write to output/ file
- >3 sentences -> write to comms/to_human.md
- Human says "file mode" or "back to protocol" -> return to strict mode

**AS. Licensing Awareness Matrix** `[OPERATIONAL_TRUTH_v3]`
- Agent OS: MIT License (full commercial)
- AutoForge: Source code disclosure required
- Martin's web boilerplate: Personal use only
- Flutter boilerplate: Full commercial rights
- Important for what can be sold vs used internally

**AT. Subscription vs API Mode** `[BASE_BUILD_PRD]`
| Aspect | Subscription | API |
|--------|-------------|-----|
| Context source | CLAUDE.md | System message |
| Token tracking | Estimated | Exact |
| Compaction | Yes | No |
| Cost model | Flat monthly | Per-token |

Config.yml should adapt behavior based on which mode is active.

---

## SUMMARY COUNTS

| Category | Items |
|----------|-------|
| PRD Machine Missing Details (List 1) | 16 items |
| Session Infrastructure | 4 features (A-D) |
| Context Window Management | 5 features (E-I) |
| Build Governance | 5 features (J-N) |
| Intelligence & Learning | 6 features (O-T) |
| Notifications & Comms | 2 features (U-V) |
| Rant Engine Delivery | 3 features (W-Y) |
| IdeaForge Workspace | 1 feature set (Z) |
| Universal Dashboard | 1 feature set (AA) |
| AI Advisors | 3 features (AB-AD) |
| Post-Build Pipeline | 2 features (AE-AF) |
| Feature Lifecycle | 3 features (AG-AI) |
| Swarm Architecture | 2 features (AJ-AK) |
| Infrastructure | 3 features (AL-AN) |
| Bonus Gold | 6 features (AO-AT) |
| **TOTAL FEATURES** | **46 feature items** |
