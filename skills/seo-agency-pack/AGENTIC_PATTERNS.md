# Agentic Patterns: 5 Ways to Run Claude Code

> **Source:** Two videos from Caleb - first after agent teams launched, second is the refined "5 patterns" framework
> **Why this matters:** When a business says "I want X done," we need to know WHICH pattern to use. This is the decision engine.

---

## The 5 Patterns at a Glance

| # | Pattern | Agents | Communication | Best For | Token Cost |
|---|---------|--------|--------------|----------|-----------|
| 1 | **Sequential Flow** | 1 | You ↔ Claude | Simple tasks, iterative refinement | 1x (baseline) |
| 2 | **The Operator** | Multiple (manual) | You coordinate between terminals | Independent parallel tasks | 1x per terminal |
| 3 | **Split & Merge** | 1 + sub-agents | Sub-agents → Main agent only (hub & spoke) | Parallel research, build + validate | 2-3x |
| 4 | **Agent Teams** | 1 + teammates | Teammates ↔ each other via shared task list | Complex builds needing collaboration | 4-7x |
| 5 | **Headless** | 1 (no human) | No human in loop, runs via `-p` flag | Scheduled tasks, batch processing | 1x per run |

---

## Pattern 1: Sequential Flow

**What it is:** One terminal, one conversation, tasks build on each other.

**How it works:**
```
You → Task 1 → Task 2 → Task 3 → Done
         ↓ context grows ↓ context grows ↓
```

**Built-in sub-agents Claude uses automatically (you don't control these):**
| Agent | Model | Access | Purpose |
|-------|-------|--------|---------|
| Explore | Haiku (cheapest) | Read-only | Fast file searching, codebase scanning |
| Plan | Haiku | Read-only | Research before presenting strategy (activated by /plan or shift+tab x2) |
| General Purpose | Sonnet | Read + Write | Complex multi-step tasks, multi-file changes |

**Ceiling:** Context window fills up → context rot → Claude forgets things, drifts.

**Fix:** Skills with progressive disclosure, /clear, /compact, one task per session.

**Use when:** Task is simple, linear, doesn't need parallelization.

---

## Pattern 2: The Operator

**What it is:** YOU open multiple terminals manually, each with its own Claude instance.

**How it works:**
```
Terminal 1: claude -w "new onboarding flow"     → own branch, own context
Terminal 2: claude -w "fix checkout bug"        → own branch, own context  
Terminal 3: claude -w "redesign user settings"  → own branch, own context
         ↑ YOU coordinate between them ↑
```

**The `-w` flag:** Creates a "work tree" - a separate copy of the project with its own branch. Claude drops straight into it. When you close the session, if nothing changed it auto-cleans up. If there's work, it asks what to do.

**Ceiling:** 4-5 terminals max before you're just flicking between windows losing track.

**Use when:** Tasks are independent (don't depend on each other), you want maximum control, clean context per task.

---

## Pattern 3: Split & Merge

**What it is:** WITHIN a single session, Claude spins up sub-agents that run in parallel, then merges results.

**How it works:**
```
You → Main Agent → fans out to sub-agents
                    ├── Sub-agent 1 (competitor A research)
                    ├── Sub-agent 2 (competitor B research)
                    ├── Sub-agent 3 (competitor C research)
                    └── Sub-agent 4 (competitor D research)
                              ↓ all report back to main ↓
                    Main Agent synthesizes → Final Report
```

**Limits:**
- Max 10 sub-agents at once (extras get queued)
- Sub-agents can ONLY report back to main agent
- Sub-agents CANNOT talk to each other
- Hub and spoke model: main agent is the bottleneck

**The Builder-Validator Chain:**
```
Main Agent → Sub-agent 1 (BUILDS) → reports back → 
Main Agent → Sub-agent 2 (REVIEWS build) → reports back →
Main Agent delivers reviewed output
```
Built-in quality check without you reviewing.

**Custom sub-agents:** You can create your own in `.claude/agents/` folder. Each has a name, description, and tool access level. Claude reads these and decides when to use them (or you specify which one).

**Use when:** Multiple independent research tasks, build + validate chains, anything that's parallelizable but doesn't need cross-agent communication.

---

## Pattern 4: Agent Teams

**What it is:** A team of agents that can communicate WITH EACH OTHER through a shared task list.

**How it works:**
```
You → Team Lead → spawns teammates
                    ├── Teammate 1 (blog writer)     ←→ Shared Task List ←→
                    ├── Teammate 2 (carousel writer)  ←→ Shared Task List ←→
                    └── Teammate 3 (newsletter writer) ←→ Shared Task List ←→
                    
Teammates can: see each other's tasks, send messages to each other,
               check each other's files, coordinate directly
```

**Setup:**
1. Add to settings.json: `"claude_code_experimental_agent_teams": true`
2. Make sure Claude is version 2.1.32+
3. In your prompt, specifically say "create an agent team"
4. Claude spawns teammates, each gets their own context window

**Controls:**
- Shift+Up / Shift+Down to navigate between teammates
- Can message individual teammates directly
- Can interrupt specific teammates
- With tmux: each agent gets its own visible terminal pane

**The "Walkie Talkie" Technique:** All teammates share access to the same files. They can read what others have written, check for consistency, and coordinate through the shared task list. Like a team with walkie-talkies - everyone can hear everyone.

**When to use (complexity scale):**

| Score | Example | Use Teams? |
|-------|---------|-----------|
| 2/10 | Write LinkedIn + Instagram posts independently | No - use sub-agents |
| 6/10 | Repurpose video into blog + carousel + newsletter (need consistent messaging) | Maybe - cross-checking matters |
| 8/10 | Build SaaS app: frontend + backend + testing suite (must coordinate) | Yes - constant cross-collaboration |

**Limitations:**
- No context inheritance (teammates don't get conversation history - team lead must pass context)
- Permissions propagate (bypass permissions = all teammates get bypass)
- 4-7x token cost vs single session
- File conflicts if multiple teammates edit the same file
- Still experimental (research preview)

**Use when:** Complex builds where agents MUST coordinate. Frontend + backend + testing. Multi-piece content that must be consistent. Anything where the hub-and-spoke bottleneck of sub-agents would slow you down.

---

## Pattern 5: Headless (Claude Without You)

**What it is:** Claude runs autonomously with no human in the loop. No terminal window needed.

**How it works:**
```
claude -p "process this transcript and create social media posts" --dangerously-skip-permissions
  → Claude works autonomously
  → Saves output to file
  → You come back and review
```

**Power moves:**
- **Scheduled tasks:** Plug into cron/Mac scheduler → runs at 7am daily
- **Chained workflows:** Pull transcript → run through skill → generate posts → save to file
- **Skills in headless:** Add skill invocations to the prompt
- **Guard rails:** Use `--allowed-tools` to restrict what Claude can do (read-only, specific tools only)
- **Ralph Loop:** Feed same prompt back repeatedly so Claude iterates on its own work until quality threshold met

**Examples:**
- Morning report: Review yesterday's work, write summary → ready when you wake up
- Content pipeline: Pull video transcript → generate social posts → save as drafts
- Overnight builds: Ship entire features while you sleep

**Limitation:** Trust. No human verification at each step. Best for tasks where output is easy to verify.

**Use when:** Batch processing, scheduled tasks, anything where you'd just be watching and approving anyway.

---

## The Decision Engine

### For Us (Choosing Which Pattern for a Client's Task)

```
Is it a single, simple task?
  → YES → Pattern 1: Sequential Flow
  → NO ↓

Can tasks run independently (no dependencies)?
  → YES → How many tasks?
           → 2-4 tasks → Pattern 2: Operator (manual parallel)
           → 5+ tasks → Pattern 3: Split & Merge (auto parallel)
  → NO ↓

Do tasks need to share information with each other?
  → YES → Is it just checking consistency, or active collaboration?
           → Just consistency checks → Pattern 3: Split & Merge with validator
           → Active back-and-forth collaboration → Pattern 4: Agent Teams
  → NO ↓

Does it need to run without human involvement?
  → YES → Pattern 5: Headless
  → NO → Pattern 1 or 2 (keep it simple)
```

### For a Business Assessment

When evaluating what a business needs, map their workflows:

| Their Workflow | Pattern | Why |
|---------------|---------|-----|
| "Write me a blog post" | 1: Sequential | Single task, one output |
| "Write 5 product descriptions" | 3: Split & Merge | Same task x5, independent |
| "Monthly reports for all 10 clients" | 5: Headless + scheduled | Batch, repeatable, easy to verify |
| "Build a landing page with copy, design, and SEO" | 4: Agent Teams | Copy, design, and SEO need to coordinate |
| "Research 3 competitors then write a proposal" | 3: Split & Merge | Research parallel, then synthesize |
| "Daily social media posts from our content" | 5: Headless + cron | Automated, daily, low-risk |

---

## The Deterministic Wall Question

You asked: can you put walls so certain agents only see certain information?

**Physical walls:** Not natively. All teammates in an agent team see everything the main agent has access to (claude.md, MCPs, files).

**Practical solutions:**

1. **Separate work trees (Pattern 2):** Each terminal literally has its own branch. Physical isolation. Agent A can't see Agent B's files because they're in different directories.

2. **Custom sub-agent definitions:** When creating agents in `.claude/agents/`, you can restrict their tool access. A reviewer agent could be set to read-only so it can't edit.

3. **Skill-level scoping:** In each skill.md, specify ONLY the reference files relevant to that skill. Claude follows the instructions and loads only what the skill tells it to. This is "mental" scoping - not enforced, but Claude follows it reliably.

4. **File structure as walls:** Put client A's data in `/clients/client-a/` and client B's in `/clients/client-b/`. Skills reference only the relevant client folder. Combined with instructions in claude.md saying "only access files within the active client folder," this creates a practical boundary.

5. **Headless with --allowed-tools:** Restrict what tools a headless session can use. Read-only sessions can't write. Specific tool whitelists prevent unintended access.

**Bottom line:** You can't build hard deterministic walls between teammates in an agent team. But you CAN:
- Use separate terminals (Pattern 2) for hard isolation
- Use sub-agents (Pattern 3) where each has its own context and only reports back
- Use skill scoping to control what gets loaded when
- Use file structure + instructions to create practical boundaries

For most business use cases, skill scoping + file structure is sufficient. For anything truly sensitive (different clients' data), use Pattern 2 with separate work trees.

---

## How This Maps to Our Service

### The Skill Wizard / Automation Builder Concept

You mentioned building a tool that helps decide which pattern to use. Here's the flow:

```
INPUT (from business owner):
┌─────────────────────────────────────────┐
│ 1. What's the task? [text input]        │
│ 2. How many subtasks? [dropdown: 1-10+] │
│ 3. Do subtasks depend on each other?    │
│    [dropdown: independent / need to     │
│     coordinate / sequential]            │
│ 4. How often? [once / daily / weekly /  │
│    monthly / on-demand]                 │
│ 5. Need human review? [yes / no /       │
│    just spot-check]                     │
│ 6. Sensitivity? [low / medium / high]   │
└─────────────────────────────────────────┘
           ↓ Agent analyzes ↓

OUTPUT:
┌─────────────────────────────────────────┐
│ Recommended Pattern: [3: Split & Merge] │
│ Why: [5 independent research tasks,     │
│       no cross-dependency, moderate     │
│       sensitivity]                      │
│                                         │
│ Skills needed:                          │
│ - Competitor Gap Analysis (existing)    │
│ - Content Brief Generator (existing)    │
│                                         │
│ Estimated setup: 2 hours               │
│ Estimated run time: 15 min per cycle    │
│ Token cost: ~$2 per run                │
│                                         │
│ [Build This Automation] button          │
└─────────────────────────────────────────┘
           ↓ Skill maker builds it ↓
```

This could be:
- A page in your dashboard
- A skill itself (meta-skill that builds other skills)
- A lead magnet / free tool that demonstrates value
- The first step of the Business Assessment

### The Skill Maker Pipeline

```
Business describes what they want
  → Automation Builder determines pattern + skills needed
    → Skill Maker creates the skill files (Level 2 structure)
      → You add brand context (Level 4)
        → Run evals to verify (Level 5)
          → Add learnings loop (Level 6)
            → Wire into orchestrated system if needed (Level 7)
```

This is the full pipeline. The Automation Builder is the TOP of the funnel. Everything else flows from it.

---

## Quick Reference: When to Use What

| Scenario | Pattern | Agents | Cost |
|----------|---------|--------|------|
| Quick question / single task | Sequential (1) | 1 | $ |
| 3 independent tasks at once | Operator (2) | 3 manual | $$ |
| Research 5 competitors | Split & Merge (3) | 1 + 5 sub | $$ |
| Build + review chain | Split & Merge (3) | 1 + 2 sub | $$ |
| Multi-piece coordinated content | Agent Teams (4) | 1 + 3 teammates | $$$$ |
| Full app build (frontend + backend + tests) | Agent Teams (4) | 1 + 3 teammates | $$$$$ |
| Daily morning report | Headless (5) | 1 autonomous | $ per run |
| Monthly client reports (10 clients) | Headless (5) | 1 per client | $$ total |
| Overnight feature build | Headless (5) + Ralph Loop | 1 iterating | $$$ |
