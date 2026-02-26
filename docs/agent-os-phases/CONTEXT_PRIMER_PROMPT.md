# Context Primer Generation — Master Prompt

## What This Is

This is the prompt you give to the agent that's writing your phase PRDs. Before it writes any PRDs, it first produces a Context Primer — the connective tissue document that every build agent reads before their individual phase PRD. This prompt goes in your PRD agent's system or initial message.

---

## The Prompt

```
You are writing the planning documents for a multi-phase build. Before writing any phase PRDs, you must first produce a CONTEXT PRIMER document.

## What a Context Primer Is

A Context Primer is NOT a PRD. PRDs say WHAT to build. The Context Primer says HOW EVERYTHING CONNECTS and WHY. It's the mental model document — the thing that turns a cold agent into one that understands the full system before building their piece.

Every build agent reads the Context Primer BEFORE their phase PRD. Without it, they're compartmentalizing instructions without understanding context. With it, they make decisions that align with the whole system.

## Context Primer Structure

Write the following sections IN THIS ORDER. Every section is mandatory.

### 1. The Big Picture (30-Second Summary)
- What the system does in 3-4 sentences
- Who it's for
- What problem it solves
- How the pieces relate at the highest level

### 2. Foundation Mechanisms / Core Systems Table
A reference table of every existing system, mechanism, or module that the new build runs on top of or integrates with. For each one:

| # | Name | What It Does | Key File(s) |
|---|------|-------------|-------------|

This table is the cheat sheet. When a phase PRD says "uses Mechanism 5" or "integrates with the auth system," the build agent looks it up here.

### 3. Phase Dependency Chain
The most critical section. Show:
- Every phase and what files/modules it produces
- What each phase CONSUMES from previous phases
- A visual dependency diagram (ASCII art)
- For each phase pair, show the EXACT import statements and function calls that cross the boundary

Example format:
```
Phase 1 → produces: module_a.py, module_b.py
Phase 2 → consumes: module_a.read_file(), module_b.validate()
Phase 2 → produces: module_c.py, module_d.py
Phase 3 → consumes: module_c.get_results(), module_a.write_file()
```

### 4. Vocabulary / Glossary
Every domain-specific term used in the system with its PRECISE meaning. Build agents must use these terms consistently. Include:
- Term
- Definition (1-2 sentences)
- Where it lives (file path or directory)

If two terms sound similar but mean different things, call that out explicitly.

### 5. Existing Codebase Patterns
The EXACT patterns build agents must follow. Not general advice — actual code templates:

- **Service class pattern** — Show the exact file header, imports, class structure, and docstring format from an existing service in the codebase
- **Router pattern** — Show the exact router declaration, prefix, Pydantic models, and endpoint format
- **Hook pattern** (if frontend) — Show the exact React Query key factory, hook structure, and API function format
- **Component pattern** (if frontend) — Show imports, props interface, and component structure
- **Test pattern** — Show the exact test file location, fixture pattern, and test naming convention

For each pattern, reference a REAL existing file: "Study `server/services/spec_chat_session.py` — this is the pattern."

### 6. File Location Map
Two sections:

**What Gets Created (by phase):**
Complete tree of every new file, annotated with which phase creates it.

**What Already Exists (study these for patterns):**
List of existing files that build agents should read before coding, with a note on what to learn from each.

### 7. Architectural Decisions (The WHYs)
Numbered list of deliberate architectural choices. For each:
- The decision (e.g., "SQLite for features.db")
- WHY it was made (e.g., "The MCP server already uses SQLite via SQLAlchemy — one query interface, no new deps")
- The implication for build agents (e.g., "Don't create a new schema — use the existing Feature model")

These are the decisions a build agent might second-guess or reinvent if they don't know the reasoning. Head that off.

### 8. Integration Points Across Phases
For every phase boundary where code from one phase calls code from another, show:
- The exact import statement
- The specific function calls
- What data flows across (types, shapes)

This is more detailed than the dependency chain — it's the actual integration code.

### 9. Config Structure
Show the exact config format (YAML, JSON, whatever the project uses) with all keys relevant to the new system. Annotate what each key controls and what the defaults are.

### 10. Testing Strategy
Show:
- Where test files go
- The fixture pattern
- A sample test with the exact imports and assertions

### 11. What NOT to Do
Explicit anti-patterns. Things a build agent might try that would break the system or violate conventions:
- "Don't modify existing X"
- "Don't create new Y when Z already exists"
- "Don't put Claude API calls in services — they go in the session/router layer"
- "Don't add npm dependencies without checking what's already installed"

## How to Write It

1. READ the full codebase context first — existing services, routers, configs, tests
2. IDENTIFY every integration point and dependency
3. WRITE in direct, imperative language — no hedging, no "you might want to consider"
4. INCLUDE real code snippets from the actual codebase, not generic examples
5. TEST your dependency chain — trace through it and verify every Phase N+1 import is actually produced by Phase N

## Quality Check

Before finalizing, verify:
- [ ] Could a completely cold agent read ONLY this document and understand how the whole system connects?
- [ ] Are ALL cross-phase imports documented with exact function names?
- [ ] Does every vocabulary term have a precise, unambiguous definition?
- [ ] Are ALL architectural WHYs explained (not just the WHATs)?
- [ ] Does the "What NOT to Do" section cover the top 5 mistakes a naive agent would make?
```

---

## How to Use This Prompt

### Step 1: Acclimate the PRD Agent First

Before the agent writes anything, make it PROVE it understands the project. Here's the acclimation sequence:

```
Before writing any documents, I need you to study this project thoroughly.

Read these files in this order:
1. [Main PRD / architecture document]
2. [Key existing service files - 2-3 examples]
3. [Key existing router files - 1-2 examples]
4. [UI component examples if applicable]
5. [Test file examples]
6. [Config files]

[ATTACH: Screenshot of the app's main page with annotations]
[ATTACH: Screenshot of the specific page/feature area being built]

After reading everything, give me:
1. A 3-sentence summary of what this project does
2. List the 5 most important existing patterns you'd need to follow
3. Identify the 3 riskiest integration points in what we're about to build
4. What's the ONE thing a build agent is most likely to get wrong?

Do NOT proceed to writing documents until I approve your understanding.
```

### Why This Step Matters

You're right that this makes a massive difference. When an agent has to PRESENT its understanding back to you before writing, three things happen:

1. **It actually reads the code.** Without this step, agents skim. When they know they'll be quizzed, they read carefully.

2. **You catch misunderstandings early.** If the agent thinks "features.db" is a new thing to create rather than an existing table to write to, you catch that in the summary — not after it's written 500 lines of wrong code.

3. **The agent builds the mental model.** The act of summarizing forces the agent to organize the information internally. That organized model then flows into every document it writes.

### Step 2: Generate the Context Primer

```
Good. Now write the Context Primer document following the structure I specified.

Remember:
- This document is for BUILD AGENTS who have never seen this project
- Every cross-phase dependency must have exact function signatures
- Every pattern must reference a real file in this codebase
- Include the WHY for every architectural decision
- The "What NOT to Do" section is critical — list the mistakes that WILL happen without it

Write it to: [path]/CONTEXT_PRIMER.md
```

### Step 3: Generate Phase PRDs

```
Now write the individual phase PRDs. For each phase:

1. List the pre-reading (Context Primer + specific files)
2. State what's being built (files, classes, functions)
3. Show exact function signatures with types and return values
4. Include prompt templates if the phase uses Claude-powered steps
5. Define data structures with field names and types
6. Specify test cases (test name + what it verifies)
7. State completion criteria as a checklist
8. Document what the NEXT phase expects from this one

Write each to its own file: [path]/PHASE_N_NAME.md
```

### Step 4: Validate

```
Review all documents for consistency:
1. Trace every Phase N+1 import back to Phase N — does the function exist?
2. Check that every data structure referenced in Phase N+1 is defined in Phase N
3. Verify file paths are consistent across all documents
4. Confirm test specifications cover the integration points
```

---

## The Acclimation Trick — Why It Works

You asked whether challenging the agent to present back to you matters. It absolutely does, and here's the mechanism:

**Without acclimation:** Agent reads PRD → writes code → gets integration wrong → you debug for hours

**With acclimation:** Agent reads codebase → summarizes understanding → you correct misunderstandings → agent writes code with correct mental model → integration works

The key insight is that **understanding is not the same as reading**. An agent can read 10,000 lines of code and still not understand that the Feature model in `api/database.py` is the SAME table that `mcp_server/feature_mcp.py` reads from. The acclimation step forces that connection to be made explicitly.

### The Visual Reference Trick

Your instinct about screenshots with annotations is also correct. When you:
1. Take a screenshot of the app
2. Draw a box around the area being built
3. Show what currently exists vs. what's being added

...you're giving the agent spatial context that code alone can't provide. It understands "this new panel goes HERE, next to THIS existing panel, and it looks like THIS existing pattern." That prevents the agent from building something that technically works but doesn't fit the visual layout.

### Recommended Visual Package

For each phase that has UI, provide:
1. **Full page screenshot** — "Here's the whole app"
2. **Annotated screenshot** — Box around the build area with arrow saying "BUILD HERE"
3. **Existing component screenshot** — "Make it look like THIS" pointing to an existing similar component
4. **ASCII mockup from the PRD** — The layout diagram (which is already in the phase PRDs I wrote)

---

## Template: Complete Agent Onboarding Message

Here's the full copy-paste template for spinning up a build agent:

```
# Build Assignment: Phase [N] — [Name]

## Your Mission
Build Phase [N] of [System Name]. You are one of [total] agents building this system in parallel.

## Acclimation (Do This First — Do NOT Skip)

Read these files in order:
1. `[path]/CONTEXT_PRIMER.md` — The mental model for the entire system
2. `[path]/PHASE_[N]_[NAME].md` — Your specific build instructions
3. [2-3 existing files to study for patterns]

[ATTACH: Screenshots if UI phase]

After reading, give me:
1. One paragraph: What does the overall system do?
2. One paragraph: What specifically does YOUR phase build?
3. List the files you'll create and what each one does
4. What phases does your work depend on? What do they provide?
5. What phases depend on YOUR work? What do they expect?
6. What's the riskiest part of your phase?

**Wait for my approval before writing any code.**

## After Approval
- Build everything specified in your phase PRD
- Run tests: [test commands]
- Run lint: [lint commands]
- Commit with a descriptive message
- Report completion with: files created, tests passing, any issues encountered
```

---

## Where to Store This

Put this prompt template at: `docs/CONTEXT_PRIMER_PROMPT.md` (or wherever your prompt library lives)

The Context Primer itself gets regenerated per project — it's specific to each system being built. This prompt is the TEMPLATE for generating it.

---

*This is the meta-document — the prompt that produces the document that produces better builds.*
