# Agent Context Optimization — Universal Methodology

> **Purpose:** This document teaches you (or any AI agent) how to set up ANY codebase so that coding agents can do maximum work within their context window. This is not specific to Greptacular — apply this to every project you build.

---

## The Problem

AI coding agents have a fixed context window (~200K tokens). Every token spent *understanding* code is a token NOT spent *writing* code. In a complex codebase:

- Reading all source files to understand architecture: **40-60%** of context
- Leaving only **40-60%** for actual coding
- After 50% context usage, output quality degrades noticeably

**The 50% rule:** Stop coding at 50% context usage. Beyond that, you're debugging AI hallucinations, not shipping features. This isn't conservative — it's learned from months of real-world agent coding.

---

## The Solution: Layered Briefing System

Instead of agents reading raw source code to understand the system, give them pre-written briefing documents that compress thousands of lines into focused summaries.

### Layer 1: Architecture Map (`AGENT_BRIEFING.md`)

**One file at project root. ~2-3K tokens. Every agent reads this first.**

Contents:
1. **What this app is** — 3 sentences max
2. **Tech stack** — languages, frameworks, databases, key libraries
3. **Directory map** — every top-level folder with a 1-line description
4. **Database schema summary** — table names + what they store (not full DDL)
5. **API endpoint index** — route → what it does, grouped by feature
6. **Key patterns** — "we use SSE for streaming", "localStorage for X", etc.
7. **File naming conventions** — so agents can predict where things live

This gives an agent full architectural awareness for ~2K tokens instead of ~50K.

### Layer 2: Feature-Specific Briefs (`docs/agent-briefs/`)

**One file per major feature area. ~1-2K tokens each. Agent reads ONLY the one relevant to their task.**

Each brief covers:
1. **What this feature does** — 2-3 sentences
2. **Files involved** — exact paths to every file (frontend component, backend router, service, types, hooks)
3. **Data flow** — how data moves through the system for this feature
4. **Database tables** — which tables this feature uses and key columns
5. **API endpoints** — routes specific to this feature with request/response shapes
6. **Key patterns** — anything unusual about how this feature works
7. **Common modifications** — where to add new fields, new endpoints, new UI elements

### Layer 3: Task Handoff Template (`docs/agent-briefs/HANDOFF_TEMPLATE.md`)

**A copy-paste template for starting every coding session.** Tells the agent:
- Which docs to read (and which to skip)
- How to use subagents efficiently
- The specific task to perform
- Context budget rules

---

## Subagent Strategy

The main agent's job is to WRITE CODE. Everything else should be delegated.

### Rules for the Main Agent

1. **Read AGENT_BRIEFING.md** — ~2K tokens
2. **Read the relevant feature brief** — ~1.5K tokens
3. **Read ONLY the 2-3 files you will edit** — ~5-10K tokens
4. **Total understanding cost: ~15K tokens (7-8% of context)**
5. **Never read more than 5 files directly**
6. **Never explore the codebase with Glob/Grep yourself**

### Rules for Subagents

Spawn subagents (Explore type) for:
- "What pattern does component X use?" — subagent reads it, reports back in 1 paragraph
- "Find all files that import Y" — subagent searches, returns file list
- "How does the WebSocket connection work?" — subagent reads the hook, summarizes

The subagent's full exploration stays in ITS context, not the main agent's. Only the summary comes back.

### Anti-Patterns

| Bad | Good |
|-----|------|
| Main agent reads 20 files to understand the codebase | Main agent reads briefing + 3 files it will edit |
| Main agent runs Grep to find patterns | Subagent runs Grep, reports findings |
| Main agent reads a file "just to check" | Subagent checks, confirms in one sentence |
| Agent reads all types.ts (could be 2000+ lines) | Brief lists the specific interfaces needed |
| Agent re-reads files it already read | Agent trusts the briefing docs |

---

## How to Build This for a New Project

### Step 1: Build the Architecture Map

After your codebase is functional, have a research-only agent session:

```
Your task is RESEARCH ONLY — do not write any code.
Explore this entire codebase and create AGENT_BRIEFING.md at the project root.
Follow the template in docs/AGENT_CONTEXT_OPTIMIZATION.md Layer 1.
Read every directory, every major file, and compress it into a ~2-3K token summary.
This document will be read by future coding agents as their first orientation.
```

### Step 2: Build Feature Briefs

For each major feature area, have a research-only session:

```
Your task is RESEARCH ONLY — do not write any code.
Create docs/agent-briefs/{feature-name}.md covering the {feature} system.
Follow the template in docs/AGENT_CONTEXT_OPTIMIZATION.md Layer 2.
Read all files related to this feature and compress into a ~1-2K token brief.
```

### Step 3: Maintain the Docs

After every major feature addition or refactor:
- Update AGENT_BRIEFING.md if new directories/tables/endpoints were added
- Update the relevant feature brief
- Create a new feature brief if a new system area was added

---

## Context Budget Planning

| Activity | Tokens | % of 200K |
|----------|--------|-----------|
| AGENT_BRIEFING.md | ~2,000 | 1% |
| Feature brief (1) | ~1,500 | 0.75% |
| Reading 3 files to edit | ~10,000 | 5% |
| Subagent summaries (3-4) | ~2,000 | 1% |
| **Total understanding cost** | **~15,500** | **~8%** |
| **Available for coding** | **~84,500** | **~42%** |
| **Safety buffer (50% rule)** | **100,000** | **50%** |

Compare to without this system:

| Activity | Tokens | % of 200K |
|----------|--------|-----------|
| Exploring codebase (Glob, Grep, Read) | ~60,000 | 30% |
| Reading files to understand patterns | ~40,000 | 20% |
| **Total understanding cost** | **~100,000** | **~50%** |
| **Available for coding** | **~0** | **~0%** |

The briefing system gives you **5x more coding capacity**.

---

## The Handoff Prompt

Copy this into every coding session, filling in the blanks:

```
## Context Rules
- Read AGENT_BRIEFING.md first (mandatory)
- Read docs/agent-briefs/{FEATURE_BRIEF}.md second
- Read ONLY the files listed below that you will modify
- Do NOT explore the codebase with Glob/Grep — use Explore subagents instead
- Do NOT read files "just to check" — trust the briefing docs
- Stop at 50% context usage — save a bridge if needed

## Subagent Rules
- Use Explore subagents for ALL research (finding patterns, checking other files)
- Main agent context is for WRITING CODE only
- When you need to understand how another component works, spawn a subagent
- Keep subagent prompts focused: "Read X file and tell me Y"

## Your Task
{DESCRIBE THE SPECIFIC TASK}

## Files You Will Modify
- {path/to/file1.tsx}
- {path/to/file2.py}
- {path/to/file3.ts}

## Relevant Feature Brief
docs/agent-briefs/{FEATURE_BRIEF}.md
```

---

## Summary

1. **Write briefing docs** — compress your codebase into layered summaries
2. **Agents read briefs, not source** — 8% context instead of 50%+
3. **Subagents do research** — main agent only writes code
4. **50% hard stop** — quality degrades beyond this point
5. **Maintain the docs** — update after every major change
6. **Apply everywhere** — this works for any codebase, any framework, any language
