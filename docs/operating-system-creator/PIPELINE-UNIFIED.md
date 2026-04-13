# OS Automation Creator — Unified Pipeline

> **What this is:** The single source of truth for turning any manual process into a buildable CLAUDE.md file. This pipeline merges the original wizard questionnaire, the 18 gaps discovered during live testing, and the 10 stage skill files into one cohesive flow. Every question, every output, every handoff is defined here. The skill files in `skills/` remain as reference, but this document is what gets used.

---

## The 10 Stages

| # | Stage | One-Line Description |
|---|-------|---------------------|
| 0 | Process Capture | Raw intake — what is this, what does the human do, what breaks |
| 1 | 6-Step Mapping | Map to INPUT → PROCESS → OUTPUT → STATE → NOTIFY → SCHEDULE |
| 2 | Step Decomposition | Break every step into inputs, outputs, decisions, errors, repeats |
| — | Gap Analysis (Early) | Quick 2-minute scan of the 18 gaps — flag obvious misses |
| 3 | Automation Classification | Each step: deterministic code, AI-driven, hybrid, human, or external API |
| 4 | Environment Setup | Runtime, dependencies, API keys with walkthroughs, cost math, rate limits |
| 5 | Error Handling & Validation | Error matrix, quality gates, rollback, data retention, cascade failures |
| 6 | Dashboard Design | Terminal dashboard, key metrics, CLI commands, notification thresholds |
| 7 | Build Order | Dependency graph, build phases, file structure, module specs, MVP path |
| 8 | Test Cases & Health Checks | Real sample test, testing checklist, health commands, monitoring, regression |
| — | Gap Analysis (Final) | Full 18-point sweep — score coverage, flag anything still missing |
| 10 | CLAUDE.md Generator | Render the final build file from all stage outputs |

**Note:** Gap Analysis runs twice — a quick pass after Stage 2 and a thorough pass after Stage 8. It uses the same 18-point checklist both times, but the early pass is a 2-minute scan for showstoppers, not a deep audit.

---

## Stage 0: Process Capture

### Purpose

Raw intake. Get everything about the manual process on paper before organizing it. Capture contradictions, tangents, and repetitions — they reveal what the user actually cares about versus what they think they should say. This stage is about volume, not structure.

### Questions to Ask

**Identity:**
1. What do you call this process? Give it a simple name — "Lead generation," "Invoice processing," "Content publishing."
2. Walk me through what a human does today, step by step. Pretend you're training someone brand new. What's step 1? Then what? Don't skip the boring parts.
3. Is this a single-pass process, or does it have distinct phases? Could someone use just Phase 1 without Phase 2? How many phases are there?

**Frequency and Volume:**
4. How often does this run? (Multiple times a day / daily / weekly / monthly / on-demand / continuously)
5. How long does one full run take a human, start to finish?
6. How many items get processed per run? (e.g., "50 leads per day," "10 invoices per week")

**Data Flow:**
7. Where does the starting data come from? (Website, spreadsheet, email inbox, database, API, manual research, someone sends it to you — which?)
8. Where does the end result go? (Software tool, sent to a person, published somewhere, saved to file, database, delivered to client — which?)

**Tools:**
9. What tools and services are already being used? For each one, does it have an API?

| Tool/Service | What it's used for | Has API? |
|---|---|---|
| | | |

**Pain Points:**
10. What breaks most often? What goes wrong? What's the most expensive mistake?
11. What's the most tedious part? What do you dread about this process?

**Constraints:**
12. How will you trigger and interact with this system? (CLI command, web interface, chat bot, API call, scheduled/automatic, combination?)
13. Are there any legal or compliance requirements? (CAN-SPAM, HIPAA, GDPR, PCI, industry-specific, client contracts?)
14. Who can use this system? Just you, or others too? If others, can everyone do everything or do different people have different access levels?

### Output

- `process_name`: Short name for the system
- `raw_description`: Unedited step-by-step from the user
- `phase_count`: Single-phase or multi-phase (and how many)
- `trigger`: What causes the process to start
- `frequency`: How often it runs
- `duration_minutes`: How long one run takes a human
- `volume_per_run`: Items processed per run
- `data_source`: Where input comes from
- `data_destination`: Where output goes
- `tools_in_use`: List of tools with API availability
- `pain_points`: What breaks, what's tedious, what's dreaded
- `interaction_method`: CLI / web / bot / API / scheduled
- `compliance_requirements`: Legal or regulatory constraints
- `access_model`: Solo operator or multi-user with roles

### Done When

- Every question above has an answer or is explicitly marked "unknown"
- The step-by-step walkthrough is specific enough that you could train a new employee from it
- Pain points have been captured (at least 1, usually 3-5)
- Phase count is determined — single vs. multi-phase
- Interaction method is identified

### Hands Off To

Stage 1 needs the raw step-by-step description, the phase count, data source/destination, and tools list from Stage 0 to map the architecture pattern.

---

## Stage 1: 6-Step Mapping

### Purpose

Take the raw process from Stage 0 and map it to the universal pattern: INPUT → PROCESS → OUTPUT → STATE → NOTIFY → SCHEDULE. If the system has multiple phases, map each phase separately. This is the architectural skeleton — everything else hangs on this.

### Questions to Ask

**For each phase (or the whole process if single-phase):**

1. What type of INPUT is this? (API call for fresh data / database query for stored data / webhook from external system / file read / web scrape / manual entry / scheduled trigger)
2. What does the human brain DO with the data? (Generate content / classify-categorize / score-rank / analyze-extract / decide-route / transform format / compare against thresholds)
3. Where do results go? (API push to external service / database write / file export / send to a person / return to pipeline for next step / update settings in external tool)

**State tracking (feeds from wizard Section C):**
4. What statuses does an item move through? Map the lifecycle. (e.g., `new → enriched → scored → emailed → replied → booked`)
5. Do you need an audit trail? (Just current status / full event log with timestamps / both)
6. Could the same item get processed twice? If so, what field makes each item unique?

**Notifications (feeds from wizard Section C):**
7. Who needs to know when this runs? (Just me / my team / a client / nobody — fully silent)
8. What do they need to know? (Completion alert / error alert / summary stats / individual item alerts / daily digest)
9. How should they be notified? (Telegram / Slack / email / dashboard / SMS)

**Scheduling (feeds from wizard Section C):**
10. When should this run? (Every X minutes / once per day at specific time / specific days / when triggered by an event / manually for now)
11. What happens if it fails mid-run? (Start over / resume from where it left off / alert a human and wait)
12. What's the infrastructure? (Personal computer / cloud server / workflow platform / don't know yet)

**Multi-phase check:**
13. For multi-phase systems: how do the phases connect? What output from Phase 1 feeds Phase 2? Can phases run independently?

### Output

- `architecture_map`: INPUT/PROCESS/OUTPUT/STATE/NOTIFY/SCHEDULE types for the system (or per-phase if multi-phase)
- `phase_connections`: How phases link together (if multi-phase)
- `status_lifecycle`: Item status progression
- `dedup_key`: Unique identifier to prevent double-processing
- `notification_plan`: Who/what/how for alerts
- `schedule_plan`: When and how it runs
- `architecture_diagram`: Simple text flowchart of the full system

### Done When

- Every component of the 6-step pattern has a type assigned
- If multi-phase, each phase is mapped separately with connections documented
- State tracking has a status lifecycle defined
- A text architecture diagram exists showing the flow
- Schedule and notification plans are defined

### Hands Off To

Stage 2 needs the architecture map and phase breakdown from Stage 1 to know which steps to decompose. If multi-phase, Stage 2 runs once per phase.

---

## Stage 2: Step Decomposition

### Purpose

Break each step identified in Stage 1 into granular detail — inputs, outputs, decisions, error cases, timing, repeats, and extensibility. This is where "I do stuff" becomes "here's exactly what happens." For multi-phase systems, run this entire stage once per phase.

### Questions to Ask

**Repeat these for EACH step in the process:**

1. What does the human do in this step? Be exact. Not "they check the data" but "they compare bounce rate against 2% threshold and pause if exceeded."
2. What data does this step need to start? Where does it come from — previous step, a tool, a file, a person?
3. What decisions does the human make? What judgment calls happen here?
4. Could Claude make this decision instead? (Yes with clear rules — write them out / Yes but needs judgment — describe what "good" looks like / No, must stay human — why?)
5. What's the output of this step? A list? A score? A file? A yes/no?
6. Where does that output go? Next step / database / API / file / person / multiple destinations?
7. Is there an API-first tool that could handle this? Search "[what you need] API" — what exists, what does it cost?
8. What's the error case? What happens when this step fails? Skip / retry / alert / stop?
9. What if this step succeeds but the output is bad? Can the user redo just this step? What gets thrown away and what gets kept?
10. How long does this step take a human? Minutes per item.
11. Does this step run once per item, or can it repeat multiple times? If it repeats, what determines how many times? (User choice, data-driven, fixed count?)
12. Are the options in this step fixed, or do new options get added over time? If they grow, who adds them — the user or the system?

**After ALL steps are decomposed:**

13. Do items ever need to be processed together as a group? Can you combine multiple items through the same step to get one merged output?
14. Are there common combinations of choices/options that should be saved as reusable presets? What would Preset 1 be? Preset 2?
15. If you could only automate ONE step to start, which one gives the most relief? That's the MVP.

### Output

- `steps[]`: For each step:
  - `name`: Step name
  - `human_action`: Exact action description
  - `input_needed`: What data, from where
  - `decisions`: List of judgment calls
  - `claude_can_decide`: Yes with rules / yes with judgment / no
  - `decision_rules`: The actual rules (if yes)
  - `output`: What gets produced
  - `output_destination`: Where it goes
  - `api_tool`: Tool name, cost, notes
  - `error_case`: What fails and what to do
  - `redo_strategy`: How to handle bad-but-successful outputs
  - `human_time_minutes`: Time per item
  - `repeats`: Whether it runs N times and what controls N
  - `extensible_options`: Whether the option list grows
- `supports_batch`: Whether items can be processed together
- `presets`: Common combinations to save
- `mvp_step`: Which step to automate first and why

### Done When

- Every step has all 12 per-step questions answered
- Every decision the human makes is captured (missed decisions = silent wrong automation choices)
- MVP step is identified with reasoning
- Batch processing and preset questions are answered
- Error AND redo scenarios are documented for each step

### Hands Off To

Stage 3 needs the step list with all decisions, inputs, and outputs from Stage 2 to classify each step as code/AI/human. The Gap Analysis (Early) runs first as a quick check.

---

## Gap Analysis (Early Pass)

### Purpose

Quick 2-minute scan of the 18 known gaps against what's been captured so far. The goal is to catch showstoppers before investing in detailed design (Stages 3-8). Not thorough — just flag what's obviously missing.

### Questions to Ask

Scan each gap category and ask: "Do we know this yet? If not, is it a blocker?"

**Structural (gaps 1-5):**
- Did we catch multi-phase structure?
- Did we catch repeating steps?
- Did we catch growing option lists?
- Did we catch presets?
- Did we catch cross-item batch/merge needs?

**Practical blockers (quick check of gaps 6-11):**
- Do we know what API keys are needed? (Full details come in Stage 4, but showstoppers surface now)
- Do we know the interaction method? (CLI/web/bot — this changes everything)
- For AI-driven steps, do we have at least a rough idea of what the prompt should do?

### Output

- `pass_type`: "early"
- `showstoppers_found`: List of gaps that would block Stages 3-8
- `notes`: Quick notes on anything flagged
- `action`: "proceed" or "go back to Stage X to fill gap Y"

### Done When

- All 5 structural gaps have been scanned
- Practical blockers (keys, interaction, prompts) have been checked
- Any showstoppers are flagged with a specific action

### Hands Off To

If showstoppers are found, go back to the relevant stage. If clear, proceed to Stage 3 with the full step list from Stage 2.

---

## Stage 3: Automation Classification

### Purpose

For each step from Stage 2, determine HOW it gets automated — pure code with fixed rules, AI-driven with Claude, a hybrid, must stay human, or handled by an external API. For AI steps, capture the prompt skeleton. For code steps, capture the exact logic. This is where the architecture becomes concrete.

### Questions to Ask

**For each step:**

1. Is this step deterministic (same input always produces same output) or does it require judgment/language understanding?
2. If deterministic: what's the exact if/then logic? Any thresholds or lookup tables? Could this be a simple bash command?
3. If AI-driven: what's Claude being asked to do? (Classify, generate, analyze, score, extract, summarize?)
4. For AI steps — what should the prompt look like? Write out the key instructions Claude needs. What format should the output be in? Any specific rules or constraints?
5. For AI steps — what model fits? (Haiku for cheap/fast/simple, Sonnet for balanced, Opus for complex reasoning)
6. For AI steps — what data gets fed to Claude? (Raw text, JSON, structured fields?) What should Claude return? (JSON with specific fields, plain text, score?)
7. Could a third-party API handle this step entirely? (e.g., MillionVerifier for email validation, Google Vision for image analysis)
8. Does this step require a human no matter what? If so, why? (Subjective judgment, legal liability, relationship-dependent?)

### Output

- `classifications[]`: For each step:
  - `step_name`: Name
  - `classification`: deterministic / ai_driven / hybrid / human_required / external_api
  - `prompt_skeleton` (AI steps): task, input format, output format, model, cost estimate, one concrete example input/output
  - `deterministic_logic` (code steps): conditions, thresholds, lookup tables, bash possibility
- `ai_step_count`: How many steps use Claude
- `deterministic_step_count`: How many are pure code
- `human_step_count`: How many stay manual
- `estimated_cost_per_run`: Total Claude API cost based on model choices and volume

### Done When

- Every step has exactly one classification
- Every AI step has a prompt skeleton with task, input format, output format, and model choice
- Every deterministic step has the exact logic written out
- Cost-per-run estimate exists for AI steps
- No steps are left as "we'll figure it out later"

### Hands Off To

Stage 4 needs the classifications and tool list from Stage 3 to determine the full environment — which APIs, which runtimes, which dependencies.

---

## Stage 4: Environment Setup

### Purpose

Nail down everything needed to actually RUN this system — the runtime, every package, every API key with step-by-step setup instructions, the database schema, prerequisites in order, cost-per-run math, and rate limits. A developer reading this stage's output should be able to set up the environment from scratch.

### Questions to Ask

**Runtime:**
1. What runtime is this built on? (Node.js 20 / Python 3.11 / Bash / other)
2. What packages are needed? List every one with version.
3. Any system requirements? (Docker, specific OS, minimum RAM/disk?)

**API Keys and Credentials:**

For EACH external service identified in Stages 0-3:
4. What credential is needed? (API key, OAuth token, bearer token, service account, app password?)
5. Where do you get it? Step by step: "Log in → Settings → API → Copy key."
6. What plan is required? Free tier works, or need paid? Which tier?
7. What does it cost monthly?
8. What should the environment variable be named? (e.g., `SMARTLEAD_API_KEY`)
9. Any extra setup steps? (Create a bot, register an app, enable an API, verify a domain, configure DNS?)

**Database:**
10. What database? (Supabase / SQLite / PostgreSQL / JSON files / none)
11. What tables are needed? (From state tracking in Stage 1)
12. Is there seed data needed before first run?

**Prerequisites:**
13. What must be done, in order, before the system can run for the first time? Mark each as one-time setup or per-instance setup (done each time you add a new domain/mailbox/project).
14. What must already exist before this system can be BUILT? (Database tables, API accounts, other systems running, infrastructure?)

**Cost Math:**
15. For each API call in the pipeline: what does one call cost? How many calls per run? What's the daily and monthly estimate?

| Step | API Used | Cost Per Call | Calls Per Run | Monthly Cost |
|------|----------|--------------|---------------|-------------|
| | | | | |

**Rate Limits:**
16. For each API: what's the rate limit? (Requests/minute, requests/day, concurrent connections?) What happens when you hit it — queued, rejected, throttled? What delay between calls keeps you safe?

### Output

- `runtime`: Language and version
- `dependencies[]`: Every package with version
- `api_keys[]`: For each service: name, credential type, how to get it, plan required, monthly cost, env var name, setup steps
- `database`: Type, tables, schema SQL, seed data
- `prerequisites[]`: Setup steps in order, each marked one-time or per-instance
- `cost_per_run`: Itemized cost table
- `monthly_estimate`: Total projected monthly cost
- `rate_limits[]`: Per-API limit, usage pattern, and buffer strategy

### Done When

- Every API key has a complete "how to get it" walkthrough
- Cost math is itemized with real numbers, not "it's cheap"
- Rate limits are documented for every external API
- Prerequisites are in order — step 3 doesn't depend on step 5
- A developer who has never used any of these services could set up the environment from this output alone

### Hands Off To

Stage 5 needs the rate limits and API details from Stage 4 to design error handling. Stage 5 also pulls the step list from Stage 2 for per-step error cases.

---

## Stage 5: Error Handling & Validation

### Purpose

Define what happens when things go wrong AND when things "succeed" but produce bad output. This covers retries, rollback, quality gates, data retention lifecycle, and cascade failures for every step. A system without this stage will work on demo day and fail in production.

### Questions to Ask

**Error Matrix (for each step):**
1. What can fail? (API down, rate limited, bad data, timeout, auth expired, empty result)
2. How do you detect the failure? (HTTP status code, empty response, validation check, timeout)
3. What's the action? (Retry / skip this item / alert a human / pause everything / stop everything)
4. If retrying — how many times? With what delay? Exponential backoff?
5. Is there a fallback if the primary method fails?

**Quality Gates (for steps that produce output):**
6. How do you know the output is good? What does a "bad" output look like?
7. Should there be an automated quality check before the output is saved or delivered? (Validation rules, confidence score, format check?)
8. What happens on bad quality? (Retry with different parameters, flag for human review, skip?)

**Rollback and Redo:**
9. Can each step be re-run safely? (Idempotent — yes / has side effects — no / partially)
10. If a step needs to be redone, what gets thrown away and what gets kept?
11. When you improve how a step works (better prompt, better rules), do you want to reprocess old items with the new version? Or is the old output fine as-is?
12. How is versioning handled? (Overwrite / append with timestamp / keep all versions)

**Data Retention:**
13. How long should raw data be kept? (Forever / 90 days / 30 days / until processed)
14. How long should results be kept? (Forever / 1 year / until archived)
15. When does archiving or cleanup happen? (Never / monthly / when database exceeds X rows)
16. Is there personally identifiable information (PII) that needs special handling?

**Cascade Failures:**
17. If Step 2 fails, what happens to Steps 3, 4, 5? Map the cascade for each critical failure point.

### Output

- `error_matrix[]`: Per-step failure modes, detection, action, retry strategy, fallback
- `quality_gates[]`: Per-step quality criteria, bad output definition, bad quality action
- `rollback`: Which steps are idempotent, which have side effects, versioning approach
- `data_retention`: Raw data lifetime, results lifetime, archive trigger, PII flag
- `cascade_rules[]`: Per failure point: what breaks downstream, what action to take

### Done When

- Every step has at least one documented failure mode (if you think a step can't fail, think harder)
- Quality gates exist for every step that produces output
- Rollback strategy is defined — the user knows how to redo a bad-but-successful step
- Data retention has specific timeframes, not "we'll figure it out"
- Cascade failures are mapped — you know what happens when step N fails

### Hands Off To

Stage 6 needs the error handling rules and quality gates from Stage 5 to design what the operator sees on the dashboard. Stage 6 also uses the step list from Stage 2 and process identity from Stage 0.

---

## Stage 6: Dashboard Design

### Purpose

Define what the operator needs to SEE to know the system is healthy and whether they need to act. For automations, this is typically a terminal dashboard (not a web app). The dashboard should answer "do I need to do anything?" within 2 seconds of looking at it.

### Questions to Ask

1. What are the 3-5 most important things you'd want to see at a glance about this system? (e.g., "is it running," "how many items processed," "any errors," "cost so far")
2. What metrics actually matter for this specific automation? (Throughput, error rate, cost, quality score, trends?)
3. What CLI commands should exist? (View status, force a run, pause an item, view details, view history, export results?)
4. What should trigger a notification vs. just appearing on the dashboard?
   - What's "info" level? (Normal completion — dashboard only)
   - What's "warning" level? (Metric crosses threshold — dashboard + notification)
   - What's "critical" level? (Failure or dangerous metric — dashboard + notification + possible pause)
5. If this system has a dashboard, what does the layout look like? (Status bar, metrics panel, items table, alerts section)

### Output

- `key_metrics[]`: 3-5 metrics with name, example value, update frequency
- `dashboard_layout`: ASCII mockup of the terminal dashboard
- `cli_commands[]`: Each command with description and example usage
- `notification_thresholds[]`: Severity levels with conditions and actions
- `operator_actions`: What the operator can DO from the dashboard

### Done When

- 3-5 key metrics are defined (not more — details go in sub-commands)
- An ASCII mockup of the dashboard exists
- CLI commands are listed with descriptions
- Notification thresholds are defined with clear severity levels
- The dashboard answers "do I need to do anything?" at a glance

### Hands Off To

Stage 7 needs the CLI commands and dashboard design from Stage 6 to include them in the file structure and module specs. Stage 7 uses all previous stage outputs to plan the build.

---

## Stage 7: Build Order

### Purpose

Turn the complete design (Stages 0-6) into a construction plan — what gets built first, what depends on what, the exact file structure, module specifications, and the minimum viable path to get value. A developer follows this stage's output to build the system in order, testing as they go.

### Questions to Ask

1. What are all the modules/files that need to be built?
2. For each module, what does it depend on? (Config depends on nothing, DB depends on config, API client depends on config, step modules depend on DB and API clients, etc.)
3. What are the build phases? (Phase 1: foundation, Phase 2: notifications, Phase 3: API clients, Phase 4: core steps one at a time, Phase 5: dashboard/reporting, Phase 6: main CLI, Phase 7: scheduling)
4. What's the exact file structure tree?
5. For each file: what functions does it contain, what does each function take as input and return, what does it import?
6. What's the MVP path — the fewest modules needed to get real value? (Usually: config + db + one core step + basic CLI + notify)

### Output

- `dependency_graph[]`: Each module with what it depends on
- `build_phases[]`: Grouped modules, each phase independently testable with specific test criteria
- `file_structure`: Exact file tree
- `module_specs[]`: Per file: functions with signatures, imports, constants, rate limiting rules, error handling rules
- `mvp_path`: Ordered list of the minimum modules to build first
- `total_files`: Count
- `estimated_build_phases`: Count

### Done When

- Every file in the system is listed in the structure
- Every module has a dependency listed (even if it's "nothing")
- Build phases are ordered so each phase is testable before moving to the next
- Module specs include function signatures — not just "handles errors" but "retryWithBackoff(fn, maxRetries=3, baseDelay=1000) → Promise"
- MVP path is defined and is genuinely minimal

### Hands Off To

Stage 8 needs the file structure and module specs from Stage 7 to define test cases and health checks. Stage 8 also references all previous stages for comprehensive testing.

---

## Stage 8: Test Cases & Health Checks

### Purpose

Define exactly how to prove the system works — using real data, not hypotheticals. This stage produces the testing checklist, health check commands, ongoing monitoring plan, and regression test strategy. Someone who didn't build the system should be able to run these tests.

### Questions to Ask

1. Give me one specific, real example to test the whole pipeline with. What's the exact input? (A real URL, a real email address, a real data point.) What should happen at each step? What should the final output look like?
2. How do you verify the result? (Check the database? Check a file? Check Telegram? Check the dashboard?)
3. What's a good manual testing checklist? Walk through each command in order: setup, run, verify status, check specific behavior, intentionally trigger an error, verify dedup, test notifications, test export.
4. What commands can the operator run anytime to check system health? (Database connection, API connectivity, system status)
5. What should be checked regularly after deployment? (Error logs daily, API costs weekly, data volume monthly, spot-check output quality weekly)
6. After changing a prompt, a threshold, or adding a new step — what needs to be re-tested?

### Output

- `sample_test`: Real input, expected behavior at each step, expected final output, how to verify
- `testing_checklist[]`: Numbered steps with exact commands and expected results — pass/fail, not "looks right"
- `health_checks[]`: Commands with what they check and what "healthy" looks like
- `ongoing_monitoring[]`: Check name, frequency, what to look for
- `regression_tests[]`: For each type of change (prompt, threshold, new step, API version), what to re-test

### Done When

- The sample test case uses real data (not "test@example.com" — a real URL, a real query, a real input)
- The testing checklist is runnable by someone who didn't build the system
- Every test has a clear pass/fail criteria — no "check if it looks right"
- Health checks cover database, APIs, and system status
- Regression strategy exists for prompt changes, threshold changes, and new steps

### Hands Off To

The Gap Analysis (Final Pass) runs next to do a full 18-point sweep with everything now laid out. Stage 8's test case quality is one of the things gap analysis checks.

---

## Gap Analysis (Final Pass)

### Purpose

Full 18-point sweep across everything captured in Stages 0-8. Check every known gap category against the current design. Score coverage. Flag anything still missing. This is the quality gate before generating the final CLAUDE.md.

### The 18-Point Checklist

**Structural Gaps (1-5):**

| # | Gap | Check |
|---|-----|-------|
| 1 | Multi-phase structure | Is this one phase or multiple? Are phases documented separately? |
| 2 | Repeating steps | Does any step run N times? Is N fixed or variable? |
| 3 | Extensible options | Do options in any step grow over time? Can new types/filters/templates be added? |
| 4 | Presets | Are there common combinations that should be one-click? |
| 5 | Cross-item batch/merge | Can multiple items be processed together into one output? |

**Environment Gaps (6-10):**

| # | Gap | Check |
|---|-----|-------|
| 6 | API keys/credentials | Is every required key listed with step-by-step how-to-get instructions? |
| 7 | Dependencies | Are all packages, runtimes, and system requirements listed with versions? |
| 8 | Cost-per-run | Is the exact cost per run calculated? Monthly estimate? |
| 9 | Rate limits | Is every API rate limit documented with buffer strategy? |
| 10 | Prerequisites | Are setup steps listed in order with one-time vs per-instance marked? |

**Design Gaps (11-15):**

| # | Gap | Check |
|---|-----|-------|
| 11 | Prompt templates | For every AI step, is the prompt skeleton captured with task, format, model, and example? |
| 12 | User interaction | Is the interface defined? CLI commands? Dashboard? Bot? |
| 13 | Data retention | How long is data kept? When archived? When deleted? |
| 14 | Output quality | How do you know the output is correct? Quality gates defined? |
| 15 | Versioning/reprocessing | Can you rerun old items with a new prompt? How? |

**Operations Gaps (16-18):**

| # | Gap | Check |
|---|-----|-------|
| 16 | Sample test case | Is there a real, concrete test case with real data? Not hypothetical? |
| 17 | Rollback/undo | If output is wrong, how do you redo just that step? |
| 18 | Access control | Who can run this? Who can change settings? Does it matter for this system? |

### Questions to Ask

For each gap: "Is this covered? Where in the stages? If not covered, is it relevant to this system?"

After the standard 18: "Is there anything specific to THIS automation that doesn't fit any of the 18 categories above?" If yes, document it as gap #19+ and note which stage should have captured it.

### Output

- `gap_results[]`: For each of the 18 gaps: covered (yes/no), where it's covered, action needed if not
- `coverage_score`: X out of 18
- `rating`: COMPLETE (18/18) / NEAR_COMPLETE (15-17) / GAPS_FOUND (10-14) / INCOMPLETE (<10)
- `new_gaps_discovered[]`: Any process-specific gaps beyond the standard 18
- `actions_required[]`: Specific actions to fill remaining gaps

### Done When

- All 18 gaps have been checked and scored
- Coverage score is calculated
- If NEAR_COMPLETE: remaining gaps are filled or explicitly marked N/A with reasoning
- If GAPS_FOUND or INCOMPLETE: go back to the relevant stages and fill before proceeding
- Any new process-specific gaps are documented

### Hands Off To

Stage 10 only proceeds if the rating is COMPLETE or NEAR_COMPLETE. If gaps remain, go back to the relevant stages and fill them first. Stage 10 consumes ALL stage outputs (0-8 plus gap results) to render the final CLAUDE.md.

---

## Stage 10: CLAUDE.md Generator

### Purpose

Render everything from Stages 0-8 into a single, self-contained CLAUDE.md build file. This is the deliverable. No references to stages. No "see Stage 3 for details." A fresh Claude Code session with only this file builds the entire system.

### Questions to Ask

None. This stage is pure rendering — every decision was made upstream. If something is unclear during rendering, that means the gap analysis failed. Go back and fix it.

### Output

The CLAUDE.md file itself, following this structure:

```
# [System Name] — CLAUDE.md Build File

## Mission
[1 paragraph — what this system does and why, from Stage 0]

## API Keys Required
[Full .env template with every key, how to get each one, from Stage 4]

## Tech Stack
[Runtime, dependencies with versions, from Stage 4]

## Database Schema
[Full SQL or schema definition, from Stage 4]

## Pipeline Architecture
[Text diagram of the flow + CLI commands with examples, from Stages 1, 6]

## File Structure
[Exact tree of all files, from Stage 7]

## Module Specifications
[For each file: functions with signatures, imports, rate limiting,
 error handling, prompt skeletons for AI steps — from Stages 2, 3, 7]

## Rules
[Numbered list of all constraints: rate limits, save-incrementally,
 error handling defaults, quality gates, domain-specific rules — from Stages 3, 5]

## Dashboard
[ASCII mockup + CLI commands for status/health/report, from Stage 6]

## Testing Checklist
[Numbered checklist with real test data and commands, from Stage 8]

## Build Order
[Numbered build phases with test criteria per phase, from Stage 7]
```

### Done When

- A developer who has never seen this project can read the CLAUDE.md and build the system
- Every file is specified — no "figure it out" sections
- Every function is defined — inputs, outputs, behavior
- Every API interaction has rate limits and error handling
- The build order lets them test as they go, not just at the end
- The testing checklist uses real data, not hypotheticals
- The file is self-contained — no references to pipeline stages

### Hands Off To

The user. Drop this CLAUDE.md into a project folder, run `claude`, and it builds.

---

## Appendix: Source Materials

### Operations Layer Questions (from Wizard Section C)

These questions feed into Stage 1's 6-step mapping. They are asked during Stage 1, not as a separate section:

- State tracking: Item status lifecycle, audit trail needs, deduplication key
- Notifications: Who needs to know, what they need to know, how to notify them
- Scheduling: When to run, failure recovery, infrastructure choice

### Success Criteria (from Wizard Section D)

These feed into the Gap Analysis passes and Stage 8's testing:

- **Metrics**: What do you measure today? What's the current value? What's the target? (e.g., "leads/day: 10 → 50")
- **Human cost**: Hours per week this process takes. Dollar cost per month.
- **Tool budget**: Free (<$50/mo), moderate ($50-200), investment ($200-500), enterprise (>$500)
- **MVP**: Which single step, if automated, gives the most relief? (This feeds Stage 2's MVP identification)

### The 18 Gaps (Quick Reference)

Discovered during live testing. These are checked in both gap analysis passes:

1. Multi-phase structure
2. Repeating steps
3. Growing options library
4. Presets / saved combinations
5. Cross-item batch/merge
6. API keys / credentials checklist
7. Environment / dependency setup
8. Cost-per-run estimation
9. Rate limits / throttling
10. Prompt template capture
11. User interaction method
12. Data retention / storage lifecycle
13. Output quality validation
14. Versioning / reprocessing
15. Dependency chain / prerequisites
16. Sample test case
17. Rollback / undo
18. Access control / permissions
