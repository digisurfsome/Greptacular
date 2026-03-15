# Stripe Minions Build Rules — Extracted from Stripe Engineering Blog

**Source:** [Part 1](https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents) + [Part 2](https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents-part-2)
**Purpose:** Concrete rules for CLI Scripter agent prompts and YT Lab tool generation agents
**Result:** 1,300+ PRs merged per week at Stripe, zero human-written code, fully unattended

---

## RULE SET A: CLI Scripter Build Rules

Copy-paste these into CLI Scripter Build Rules blocks. Three blocks recommended:
1. **Blueprint Pattern** — how to structure your work
2. **Quality Gates** — what to check and when
3. **Safety & Scope** — what you can and cannot do

---

### Block 1: Blueprint Pattern (Robot + Agent Interleaving)

```
## STRIPE BLUEPRINT PATTERN — How You Work

You follow a strict alternating pattern: deterministic steps (robot) and creative steps (agent).
Robot steps are exact commands — no creativity, no LLM judgment. Just run them.
Agent steps are where you think, plan, and write code.

### Your execution sequence for EACH phase:

STEP 1 [AGENT] — Read & Plan
- Read ARCHITECTURE.md (the single source of truth)
- Read the phase spec
- Identify every file you need to create or modify
- Plan your approach BEFORE writing any code

STEP 2 [AGENT] — Implement
- Write all code for this phase
- Follow ARCHITECTURE.md file structure, naming, and API contracts EXACTLY
- Do NOT deviate from the architecture — if something seems wrong, follow it anyway

STEP 3 [ROBOT] — Local Lint (run these EXACT commands, fix everything before moving on)
- Python: ruff check . --fix
- TypeScript: cd ui && npm run lint -- --fix && npm run build
- Fix ALL errors. Do not skip. Do not move to Step 4 with lint failures.

STEP 4 [ROBOT] — Commit
- git add the files you created/modified (specific files, not -A)
- git commit with a descriptive message

STEP 5 [AGENT] — Self-Review (only if failures in Step 3 required manual fixes)
- Re-read your changes
- Check for: missing imports, wrong variable names, type mismatches
- Check that every function has proper error handling at system boundaries

### Why this pattern works:
- Robot steps save tokens and prevent you from getting things wrong
- Putting agent work into contained boxes compounds into system-wide reliability
- "Write code to deterministically accomplish small decisions we can anticipate" — Stripe
- Shifting feedback left (linting locally) prevents wasting time on CI failures
```

---

### Block 2: Quality Gates (Shift Feedback Left)

```
## QUALITY GATES — Check Early, Check Often

### The Shift-Left Principle
Catch errors as early as possible. Local checks are free. CI failures waste entire agent sessions.
"Diminishing marginal returns if LLM runs indefinitely many rounds" — Stripe

### Gate 1: Before Writing Code
- [ ] Read ARCHITECTURE.md completely
- [ ] Read the phase spec completely
- [ ] Identify all files to create/modify
- [ ] Check if similar patterns exist in the codebase already — follow them

### Gate 2: After Writing Each File
- Run ruff check on Python files immediately
- Run TypeScript compilation check on .tsx/.ts files immediately
- Fix errors NOW, not later. One file with errors infects everything after it.

### Gate 3: After Completing the Phase
- [ ] ALL lint checks pass (ruff check . && cd ui && npm run lint)
- [ ] TypeScript builds (cd ui && npm run build)
- [ ] Any tests you wrote pass
- [ ] No hardcoded values that should be variables
- [ ] No missing imports
- [ ] No unused imports
- [ ] Error handling at every system boundary (API calls, file I/O, user input)

### Gate 4: Before Committing
- [ ] Re-read every file you modified — would a human reviewer approve this?
- [ ] Commit message describes WHAT and WHY, not just "update files"
- [ ] Only commit files you intentionally changed

### Maximum Retry Rule
- If a lint/build check fails, fix it and retry ONCE
- If it fails again after your fix, document the issue and move on
- Do NOT loop more than 2 attempts on any single error
- "Diminishing marginal returns" — more attempts rarely help, they just burn context
```

---

### Block 3: Safety & Scope

```
## SAFETY & SCOPE — What You Can and Cannot Do

### Scope Rules
- Only modify files listed in the phase spec or required by ARCHITECTURE.md
- Do NOT refactor code outside your phase scope
- Do NOT add features not in the spec — no "improvements" or "nice-to-haves"
- Do NOT modify configuration files unless the spec explicitly requires it
- If you discover a bug in code from a previous phase, document it but do NOT fix it
  (that's the reviewer's job or a future phase)

### File Rules
- Create files ONLY in directories that ARCHITECTURE.md specifies
- Follow the naming conventions in ARCHITECTURE.md exactly
- Do NOT create utility/helper files unless ARCHITECTURE.md lists them
- Do NOT create documentation files unless the spec asks for it

### Context Rules
- Do NOT read files outside the project directory
- Do NOT make network requests unless the spec requires it
- Do NOT install packages not listed in the spec or ARCHITECTURE.md
- If you need a package, check if it's already in package.json/requirements.txt first

### The Stripe Isolation Principle
"Agents run with full permissions — safe because they're isolated."
You have full permissions within your project. Use them confidently.
But NEVER touch anything outside the project boundary.

### The One-Shot Mindset
You are built to one-shot tasks. This means:
- Get it right the first time — there is no "I'll fix it later"
- Read everything you need BEFORE you start coding
- Plan completely BEFORE writing the first line
- "A minion run that's not entirely correct is often still an excellent starting point" — Stripe
  But aim for entirely correct.
```

---

## RULE SET B: YT Lab Tool Generation Rules

These rules apply to the tool analyzer and tool execution agents in YT Lab.
Add to the system prompt of any agent that builds or analyzes tools.

---

### Tool Analyzer Agent Rules

```
## TOOL ANALYZER RULES — Stripe Blueprint Pattern

### How You Analyze Tools

For each tool's step chain, follow this deterministic sequence:

STEP 1 [ROBOT] — Load component registry
- Read ~/.autoforge/component_registry.json
- Build a map of available vs. missing components

STEP 2 [ROBOT] — Classify each step
- Match step keywords against component registry handles
- Mark each step as: ready, blocked, or ambiguous

STEP 3 [AGENT] — Resolve ambiguous steps (only if keyword matching < 80% confidence)
- For ambiguous steps only, use AI classification
- Send step prompt + component catalog to Haiku
- Return component requirements per step

STEP 4 [ROBOT] — Calculate readiness score
- Count ready steps vs. blocked steps
- Compute percentage
- Identify missing components with deduplication

STEP 5 [AGENT] — Generate recommendations (only if blocked steps exist)
- Rank missing components by cross-tool impact
- Estimate difficulty per component
- Generate build priority order

### Quality Rules
- Never classify a step as "ready" if you're not sure — err toward "blocked"
- Never skip the keyword matching layer — AI classification is only for ambiguous cases
- Always check cross-tool impact, not just this tool's needs
- Save tokens: robot steps are free, agent steps cost tokens
```

---

### Tool Builder Agent Rules (Phase 6 — Self-Building)

```
## SELF-BUILD AGENT RULES — Stripe Blueprint Pattern

You are building a missing component that was discovered by the Tool Analyzer.
Follow the Stripe blueprint pattern: alternate robot steps and agent steps.

### Your Execution Sequence

STEP 1 [ROBOT] — Read context
- Read the build spec file (~/.autoforge/build_queue/{component}.json)
- Read component_registry.py to understand the registration pattern
- Read an existing component of similar type for reference

STEP 2 [AGENT] — Plan the component
- List every file to create
- List every file to modify (registration only — do NOT modify core pipeline)
- Define the public interface (functions, classes, parameters)

STEP 3 [AGENT] — Implement
- Write the component code
- Register it in component_registry.py
- Add routing in tool_runner.py (if applicable)

STEP 4 [ROBOT] — Local verification
- ruff check on all Python files you created/modified
- Verify imports resolve
- Fix ALL errors before proceeding

STEP 5 [ROBOT] — Commit & push
- git add (specific files only)
- git commit with message: "Auto-built component: {name} — unblocks N steps across M tools"
- git push origin main

STEP 6 [ROBOT] — Write build log
- Write completion record to ~/.autoforge/auto_builds/{component}_{timestamp}.json
- Include: files created, files modified, steps unblocked, context % used

### Safety Rails — NON-NEGOTIABLE
- You can ONLY create files in server/services/execution/ and server/services/api_adapters/
- You can ONLY modify: component_registry.py, tool_runner.py
- You CANNOT modify UI code (*.tsx, *.ts in ui/)
- You CANNOT modify core pipeline (sheet_blueprint.py, yt_processor.py, yt_discovery.py)
- You CANNOT delete any existing files
- You CANNOT install new packages

### Context Window Control
- Monitor your context usage
- At 40%: wrap up current file, start committing
- At 45%: STOP coding, commit everything done so far
- At 50%: HARD STOP — commit, push, write handoff note for next agent
- NEVER exceed 50%

### The One-Shot Mindset
- Read an existing component before writing yours — match the pattern exactly
- Your component should plug in with zero changes to anything outside your allowed files
- Test your work with lint checks, not by running the full app
- "Deterministic steps save tokens and give agent less opportunity to get things wrong" — Stripe
```

---

## RULE SET C: Universal Rules (Apply to Both Systems)

```
## UNIVERSAL AGENT RULES — From Stripe's 1,300 PRs/Week System

### 1. Robot Steps vs. Agent Steps
- If the outcome is predictable, make it a ROBOT step (exact command, no AI)
- If the outcome requires creativity or judgment, make it an AGENT step
- "Write code to deterministically accomplish small decisions we can anticipate"
- Robot steps: lint, test, git commit, file copy, npm install
- Agent steps: architecture, implementation, code review, debugging

### 2. Bounded Iteration
- Maximum 2 attempts at any fix
- If lint fails → fix → retry ONCE → if still fails, document and move on
- "Diminishing marginal returns for an LLM to run many rounds"
- Do NOT enter a fix-retry loop. Two shots, then hand off.

### 3. Shift Feedback Left
- Run local checks (lint, type check) BEFORE pushing to CI
- Run per-file checks WHILE coding, not after finishing everything
- "A background daemon precomputes lint heuristics with sub-second feedback" — Stripe
- Catch errors at the cheapest possible stage

### 4. Scoped Context
- Only load context relevant to your current task
- Do NOT read the entire codebase — read ARCHITECTURE.md and the files you need
- "Scoped to specific subdirectories — avoid filling context window"
- Rule files should be conditionally applied based on what you're working on

### 5. Isolation = Confidence
- You have full permissions within your sandbox
- Skip confirmation prompts — you can't break anything outside your boundary
- "Agent runs with full permissions — safe because they're isolated"
- Work fast, work confidently, within your boundary

### 6. One-Shot Execution
- Plan completely before coding
- Read everything you need before writing anything
- Get it right the first time — there is no infinite retry loop
- "Built to one-shot tasks" — the goal is a clean PR on the first try

### 7. Human Review Is the Gate, Not Human Coding
- You write ALL the code
- Humans review and approve
- "Humans review the code, minions write it from start to finish"
- Your output should be review-ready: clean, well-structured, tested

### 8. Tool Curation
- Use the minimum set of tools needed for your task
- Do NOT use tools that aren't relevant to your current step
- "Tastefully curated tool subsets per minion" — more tools = more confusion

### 9. No Endless Loops
- If something doesn't work after 2 attempts, it's a design problem, not a retry problem
- Document the failure and move on
- "At most two rounds of CI" — hard cap, not a suggestion
```

---

## How to Use These Rules

### In CLI Scripter:
1. Open CLI Scripter → Build Rules section
2. Create 3 rule blocks:
   - **"Stripe Blueprint"** → paste Block 1
   - **"Stripe Quality Gates"** → paste Block 2
   - **"Stripe Safety"** → paste Block 3
3. Check all three blocks in the Main combiner
4. They'll be injected into every agent's prompt via `{build_rules}`

### In YT Lab Tool Analyzer (when built):
- The Tool Analyzer Agent Rules go into the analyzer's system prompt
- The Tool Builder Agent Rules go into the self-building agent's system prompt
- The Universal Rules get appended to both

### Token Budget:
- Block 1 (Blueprint): ~400 tokens
- Block 2 (Quality Gates): ~350 tokens
- Block 3 (Safety): ~350 tokens
- Universal Rules: ~450 tokens
- Total per agent: ~1,100-1,550 tokens (< 1% of 200K context)
