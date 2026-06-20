# Coding Factory Operations Manual

**Version:** 0.1 (Foundation Draft)
**Created:** 2026-03-07
**Status:** Living document — iterate and expand as knowledge grows

---

## Mission Statement

Build a systematic coding factory where every application produced meets the standard of an elite professional developer — not because the operator is a coder, but because the system itself enforces professional-grade practices at every step.

The goal is to eliminate reliance on human memory. Instead of hoping someone remembers to check security, write tests, update documentation, or follow coding standards, the factory embeds expert knowledge into specialized agent roles that automatically enforce their domain. The result: any app that goes to market has been reviewed by the equivalent of a mastermind group of 20 specialists, each demanding excellence in their area.

This is not about being perfect on day one. It's about building a structure that covers every angle, can always be improved, and gives real confidence that the homework has been done before anything goes live.

---

## Part 1: Understanding the Technology Stack

### The Three Layers of Claude (API vs CLI vs SDK)

This is the foundation you need to understand before anything else.

#### Layer 1: Claude API (Raw REST) — The Bare Metal

**What it is:** HTTP calls to `api.anthropic.com/v1/messages`. Text in, text out.

**What you get built-in:**
- Model-level safety (refuses harmful requests from training)
- Rate limiting and spending caps from the Anthropic Console
- That's it. Nothing else.

**What you DON'T get:**
- No file access, no code execution, no tools
- No system prompt (you write your own from scratch)
- No agent loop (you build the entire "think, act, observe" cycle)
- No sandboxing, no permissions, no hooks
- No CLAUDE.md or instruction file discovery

**Plain language:** This is like hiring a genius consultant who can only talk. They can't touch your computer, can't run anything, can't read files. You have to show them everything manually and do everything they suggest yourself. Maximum control, maximum work.

#### Layer 2: Claude Code CLI — The Full Agent

**What it is:** The `claude` command you use in the terminal. An interactive agent with 18 built-in tools (Read, Write, Edit, Bash, Grep, Glob, WebSearch, etc.).

**What you get built-in:**
- 110+ system prompt components covering coding style, tool usage, safety, response format
- OS-level sandboxing (Linux bubblewrap, macOS Seatbelt)
- Permission system (manual, auto-approve edits, auto-approve all)
- Hook system for deterministic guardrails (runs YOUR code before/after tool calls)
- CLAUDE.md auto-discovery (project + user + parent directories)
- Context compaction (automatic when context window fills up)
- MCP server support (extend capabilities with custom tools)
- Sub-agent spawning (Task tool + `.claude/agents/*.md` files)
- Session persistence and resumption

**What you control:**
- `--system-prompt` / `--append-system-prompt` to customize instructions
- `--allowed-tools` to restrict which tools are available
- `--permission-mode` for approval behavior
- Settings files at project/user/enterprise levels
- Hooks to block/modify any tool call

**Plain language:** This is like having a developer sitting at your computer with full access to your project. They can read files, write code, run commands, search the web. They follow a massive instruction manual (the 110+ prompt components) that tells them how to behave. You control what they're allowed to do via permissions and hooks.

#### Layer 3: Claude Agent SDK — The Programmable Wrapper

**What it is:** A Python/TypeScript library that launches the Claude Code CLI as a subprocess and controls it programmatically. This is what AutoForge uses.

**Critical insight:** The SDK does NOT talk to the API directly. It spawns the actual Claude Code CLI binary. So you get everything the CLI provides, plus programmable control.

**What you get built-in:**
- Everything from Layer 2 (it IS the CLI under the hood)
- BUT the system prompt is minimal by default (gives you more context budget)
- Must explicitly opt into the full CLI prompt with `system_prompt={"type": "preset", "preset": "claude_code"}`
- Must explicitly enable CLAUDE.md loading with `setting_sources=["project"]`

**What you control (beyond CLI options):**
- `system_prompt` — replace, append, or use preset
- `allowed_tools` — restrict tool access per agent
- `max_turns` — cap conversation length
- `max_budget_usd` — cap API spending
- `mcp_servers` — attach custom tool servers
- `agents` — define sub-agents with their own tools, prompts, and models
- Hooks as Python functions (not just shell commands)
- Programmatic settings file generation

**How AutoForge uses it:**
- Sets a simple custom system prompt: "You are an expert full-stack developer..."
- Loads project CLAUDE.md via `setting_sources=["project"]`
- Attaches Feature MCP server (SQLite-backed progress tracking)
- Attaches Playwright MCP server (browser testing)
- Bash security hook validates every command against hierarchical allowlist
- Different tool restrictions per agent type (coding vs testing vs initializer)
- Turn limits per agent type (coding=150, testing=75, initializer=200)
- Spawns parallel agents as separate processes (not SDK sub-agents)

**Plain language:** This is like having a factory floor manager who can spin up developer workstations on demand, each configured differently. One workstation has access to the feature tracker and browser testing. Another only has read access for code review. The manager controls what each developer can see, touch, and how long they work.

### What This Means for Spawning New Agents

When AutoForge (or any workspace system) creates a new agent, here's what you can control:

| Control | What It Does | Current AutoForge Setting |
|---------|-------------|--------------------------|
| System prompt | The agent's core personality and instructions | Simple one-liner + CLAUDE.md |
| Allowed tools | Which tools the agent can access | Varies by agent type |
| MCP servers | Custom tool servers (feature tracking, browser, etc.) | Feature MCP + Playwright |
| Max turns | How many back-and-forth exchanges before stopping | 75-250 depending on role |
| Max budget | Dollar cap on API costs | Not currently set |
| Hooks | Code that runs before/after every tool call | Bash command validation |
| Filesystem access | What directories can be read/written | Project dir + extra read paths |
| Model selection | Which Claude model to use | Configurable (Opus/Sonnet/Haiku) |
| Agent definitions | Named sub-agents with restricted capabilities | coder, code-review, deep-dive |

**The CLAUDE.md equivalent for spawned agents:** Each agent inherits the project's CLAUDE.md (if `setting_sources=["project"]` is set). Additionally:
- The system prompt acts as the agent's "personality"
- The user message (prompt) acts as the agent's "mission briefing"
- Sub-agent definitions in `.claude/agents/*.md` provide pre-built roles
- MCP tools define what the agent can interact with beyond the filesystem

### How Claude Code CLI Compares to What You've Been Using (Claude Code Web)

You've been using Claude Code through the web interface. Here's what's the same and different:

**Same:**
- Same underlying model (Opus 4.6, Sonnet 4.6, etc.)
- Same tool capabilities (Read, Write, Edit, Bash, etc.)
- Same CLAUDE.md loading
- Same context compaction
- Same hook system

**Different in the SDK/Factory setup:**
- You can spawn MULTIPLE agents simultaneously (parallel mode)
- Each agent can have different tools, prompts, and restrictions
- Programmatic control over every aspect (no clicking, no UI prompts)
- MCP servers extend capabilities beyond built-in tools
- Budget and turn limits prevent runaway agents
- Security hooks provide deterministic enforcement (no relying on the model to "be careful")
- Session handoff — one agent's work feeds into the next automatically

---

## Part 2: Multi-CLI Coexistence (Claude + Codex + Gemini)

### The Situation

You have three AI CLIs in your environment. Here's how they actually work together:

| Feature | Claude Code | OpenAI Codex | Google Gemini |
|---------|------------|--------------|---------------|
| Instruction file | `CLAUDE.md` | `AGENTS.md` | `GEMINI.md` |
| Sandbox ON by default | Yes | Yes | **No** |
| Reads other CLIs' files | No | Optional (can add CLAUDE.md as fallback) | No |
| File access outside project | Yes (read-only) | Yes (read-only in sandbox) | No |
| Network control | Configurable allowlist | Binary on/off | Unrestricted or blocked |
| Known vulnerabilities | None reported for this attack | None reported | Prompt injection bug (fixed v0.1.14) |

### Key Findings

1. **They all access the same files.** All three CLIs, when launched in the same directory, can read and write the same project files. There is NO cross-CLI locking.

2. **They do NOT read each other's instruction files.** Claude ignores AGENTS.md and GEMINI.md. Codex ignores CLAUDE.md and GEMINI.md (unless configured). Gemini ignores the others. This isolation is actually good.

3. **The weakest link problem is real.** Your security is only as strong as the least restrictive CLI. If Gemini is running without sandbox enabled, a prompt injection reaching Gemini can execute arbitrary commands — even if Claude and Codex are locked down tight.

4. **Concurrent execution creates race conditions.** If two CLIs try to edit the same file simultaneously, the second write overwrites the first. No locking exists.

5. **Prompt injection via artifacts is the subtle risk.** If CLI A writes a file containing instructions, and CLI B later reads that file, CLI B could be influenced by those embedded instructions.

### Recommendations for Multi-CLI Setup

1. **Enable sandboxing on ALL CLIs.** Especially Gemini CLI (sandbox is OFF by default — use `--sandbox` flag).

2. **Use git worktree isolation.** Give each CLI its own worktree branch. Merge results. This eliminates race conditions.

3. **Canonical instruction file.** Create `.ai/INSTRUCTIONS.md` as the single source of truth. Use a sync script to generate CLAUDE.md, AGENTS.md, and GEMINI.md from it. Add CI check to prevent drift.

4. **Don't run them concurrently on the same files.** Either separate by worktree, or orchestrate sequentially (Claude does feature A, then Codex does feature B).

5. **Audit trail.** Each CLI logs differently. Set up a unified logging approach so you can trace "who changed what."

---

## Part 3: The Mastermind Group — 20 Expert Agent Roles

These are the 20 disciplines that, together, cover everything a professional development team would enforce. Each one maps to a potential specialized AI agent.

### Tier 1 — Core (Every Project Needs These)

#### 1. Software Architect
Owns high-level system structure, component boundaries, and technology selection. Enforces SOLID principles, separation of concerns, loose coupling, and no circular dependencies.

#### 2. Security Engineer
Prevents and mitigates vulnerabilities across the stack. Enforces OWASP Top 10 (2025): access control, security config, supply chain, crypto, injection, auth, integrity, logging, error handling. Checks for secrets in code.

#### 3. Code Quality & Standards Engineer
Owns readability, consistency, and maintainability. Enforces chosen style guide (Airbnb, Google, PEP 8), naming conventions, small functions, no dead code, magic numbers extracted to constants, automated linting.

#### 4. Testing & QA Engineer
Ensures correctness through systematic verification. Unit tests on business logic (80%+ coverage on critical paths), integration tests on component interactions, E2E tests on user journeys, deterministic tests, edge cases covered.

#### 5. Frontend / UI Engineer
Builds performant, responsive interfaces. Modular components, predictable state management, responsive design, form validation, optimized images, code splitting, cross-browser testing, loading/empty/error states.

### Tier 2 — Infrastructure (Most Production Systems Need These)

#### 6. DevOps & CI/CD Engineer
Automates build, test, and deployment. Every commit triggers CI, reproducible builds, environment parity, secrets management, automated reversible deployments, security scanning in pipeline.

#### 7. Database Engineer
Owns data modeling, schema design, and query optimization. Normalized schemas, proper constraints, consistent naming, targeted indexes, versioned reversible migrations, encrypted sensitive data, connection pooling.

#### 8. API Designer
Designs clean interfaces between systems. RESTful conventions, consistent naming, versioning strategy, pagination/filtering/sorting, consistent error responses, OpenAPI spec maintained, rate limiting.

#### 9. Performance Engineer
Owns speed and resource utilization. Profile before optimizing, no N+1 queries, proper indexing, pagination for large datasets, caching with invalidation, compressed assets, memory leak testing, load testing.

#### 10. Error Handling & Resilience Engineer
Ensures graceful degradation under failure. Timeouts on all external calls, exponential backoff with jitter, circuit breakers, fallback values, error boundaries in UI, errors categorized and logged with context.

### Tier 3 — Production Maturity (Scaling and Operating at Quality)

#### 11. Observability & Monitoring Engineer
Makes system state visible and debuggable. Structured JSON logging, consistent log levels, correlation IDs, no PII in logs, four golden signals (latency/traffic/errors/saturation), actionable alerts, distributed tracing.

#### 12. Documentation Engineer
Ensures the codebase is understandable without tribal knowledge. README with setup instructions, API docs generated from code, ADRs for decisions, complex logic commented with "why," CHANGELOG maintained.

#### 13. Dependency & Supply Chain Engineer
Manages third-party code safely. Lockfiles committed, dependencies pinned, vulnerability scanning in CI, new deps require justification, license compatibility verified, transitive tree reviewed.

#### 14. Release & Version Management Engineer
Coordinates what ships and how. Semantic versioning, CHANGELOG updated per release, feature flags gate experiments, automated release process, backwards compatibility within major versions, rollback tested.

#### 15. Developer Experience Engineer
Makes development fast and friction-free. Local setup under 10 minutes, hot reload configured, isolated dev dependencies, shared editor configs, pre-commit hooks, common tasks automated, .env.example documented.

### Tier 4 — Specialized (Domain-Dependent)

#### 16. Accessibility Engineer
Ensures usability for people with disabilities (WCAG 2.2 AA). Alt text on images, keyboard accessible interactions, visible focus, color contrast ratios, associated form labels, ARIA used correctly, screen reader tested.

#### 17. Internationalization Engineer
Prepares for multiple languages/regions. All strings externalized, locale-aware date/number/currency formatting, correct pluralization, RTL layout support, UTF-8 everywhere, timezone handling (store UTC, display local).

#### 18. Data Privacy & Compliance Engineer
Handles personal data lawfully. Minimize collection, obtain consent, defined retention with automated deletion, export/delete capabilities, encrypted PII, access logging, documented third-party processors.

#### 19. Concurrency & Distributed Systems Engineer
Ensures correctness in multi-threaded/distributed environments. Minimize shared mutable state, prevent race conditions, idempotent distributed operations, appropriate transaction isolation, dead-letter handling.

#### 20. UX / Design Systems Engineer
Bridges design and engineering. Design tokens in code, consistent component APIs, visual regression testing, performant animations, dark mode support, consistent spacing scale, documented interactive states.

---

## Part 4: The CLAUDE.md Gap and Systematic Reviews

### The Problem You Identified

Nobody tells you to update your CLAUDE.md as features are added. Nobody systematically reviews security. Nobody checks if documentation is current. The human can only hold 3-5 things in active memory, so important practices fall through the cracks.

### The Solution: Automated Checkpoints

Every agent session should include systematic checks, not just "build the feature." Here's what should happen:

#### Per-Feature Checks (Every Feature Implementation)
- [ ] Does this feature warrant a CLAUDE.md update? (new patterns, new commands, new dependencies)
- [ ] Are there new security surfaces? (new endpoints, new user inputs, new external integrations)
- [ ] Are tests written and passing?
- [ ] Does the code follow the project's established patterns?

#### Periodic Reviews (Every N Features or Every Session)
- [ ] CLAUDE.md accuracy review — does it reflect current project state?
- [ ] Security audit — any new OWASP Top 10 exposures?
- [ ] Dependency check — any known vulnerabilities in deps?
- [ ] Documentation freshness — does README match current setup process?
- [ ] Performance regression — any new N+1 queries or unbounded data loads?

#### Pre-Market Checklist (Before Going Live)
- [ ] Full security review by Security Engineer agent
- [ ] Accessibility audit (WCAG 2.2 AA compliance)
- [ ] Performance testing under realistic load
- [ ] Error handling review — what happens when things fail?
- [ ] Privacy review — what data is collected, where is it stored, who can access it?
- [ ] Dependency audit — licenses compatible, no known vulnerabilities
- [ ] API review — consistent, documented, versioned
- [ ] Documentation complete — someone new can set up and understand the project

---

## Part 5: The Anthropic Connection to AutoForge

### The Origin Story

Anthropic published "Effective Harnesses for Long-Running Agents" in November 2025. It described a two-agent pattern:

1. **Initializer Agent** (Session 1) — Creates a feature list and initial project structure
2. **Coding Agent** (Sessions 2+) — Picks one feature, implements it, verifies it, marks it done

Key insight: external artifacts (feature list file, git history) become the agent's memory across sessions.

Leon (AutoForge creator) took this exact pattern and added:
- A full React UI with kanban board and dependency graph
- Parallel orchestration (up to 5 concurrent agents)
- SQLite-backed feature management (instead of flat JSON)
- MCP-based feature tracking (atomic claiming, status updates)
- Dependency-aware scheduling (agents skip blocked features)
- Multi-feature batching
- YOLO mode for rapid prototyping
- Multi-provider support (Claude, Vertex AI, Ollama, etc.)

The architecture is fundamentally sound because it was designed by Anthropic's own engineering team. AutoForge is the production-grade implementation of their reference architecture.

---

## Part 6: Search Strategy for Knowledge Sources

### What We're Looking For

Open-source, free educational content that breaks down professional coding practices by discipline — content we can digest and turn into agent role definitions.

### Best Search Patterns

| Pattern | Example Search | What It Finds |
|---------|---------------|---------------|
| Role + Checklist | `"security code review checklist"` | Actionable checklists for specific roles |
| Standard + Guide | `"OWASP secure coding quick reference guide"` | Official standards in digestible format |
| Awesome Lists | `"awesome-security" site:github.com` | Community-curated resource collections |
| Free Courses | `"[topic] free course" site:freecodecamp.org` | Structured learning content |
| Industry Practice | `"how Netflix handles resilience"` | Real-world implementation examples |
| Roadmaps | `site:roadmap.sh [topic]` | Learning paths by discipline |

### Top Sources Already Identified

**Universal Standards:**
- Google Style Guides (all languages): google.github.io/styleguide
- Airbnb JavaScript Style Guide: github.com/airbnb/javascript
- PEP 8 (Python): peps.python.org/pep-0008

**Security:**
- OWASP Top 10 (2025): owasp.org/Top10/2025
- OWASP Secure Coding Practices: owasp.org/www-project-secure-coding-practices-quick-reference-guide
- PortSwigger Web Security Academy: portswigger.net/web-security
- Snyk Learn: learn.snyk.io

**Architecture:**
- Twelve-Factor App: 12factor.net
- Clean Architecture (Robert C. Martin): blog.cleancoder.com
- System Design Primer: github.com/donnemartin/system-design-primer

**Accessibility:**
- WCAG 2.2: w3.org/TR/WCAG22
- WebAIM Checklist: webaim.org/standards/wcag/checklist

**API Design:**
- Google API Design Guide: cloud.google.com/apis/design
- Microsoft REST API Guidelines: github.com/microsoft/api-guidelines

**Meta-Collections:**
- Awesome Guidelines: github.com/Kristories/awesome-guidelines
- awesome-software-architecture: github.com/mehdihadeli/awesome-software-architecture

### Strategy for Building Agent Roles

1. **Start with the 20 roles listed above** — they cover the full spectrum
2. **For each role, find the 2-3 most authoritative sources** using the search patterns
3. **Extract the checklist/principles** from each source
4. **Condense into a 1-2 paragraph agent role definition** that captures the essence
5. **Test each role** by having it review a sample project
6. **Iterate** — add sub-roles where a discipline is too broad, merge where overlap exists

---

## Part 7: Implementation Roadmap

### Phase 1: Foundation (Now)
- [x] Document the technology stack (API vs CLI vs SDK)
- [x] Identify the 20 specialist roles
- [x] Understand multi-CLI coexistence
- [x] Create this operational document
- [ ] Review and refine this document with feedback

### Phase 2: Agent Role Definitions
- [ ] Write system prompts for Tier 1 roles (Architect, Security, Quality, Testing, Frontend)
- [ ] Create `.claude/agents/` files for each role
- [ ] Define per-role tool restrictions and checklists
- [ ] Test each role on a sample project

### Phase 3: Factory Integration
- [ ] Build automated checkpoint system (per-feature + periodic reviews)
- [ ] Create pre-market audit workflow
- [ ] Integrate CLAUDE.md auto-update prompts into feature workflow
- [ ] Set up canonical `.ai/INSTRUCTIONS.md` for multi-CLI projects

### Phase 4: Optimization
- [ ] Orchestrator agent that coordinates the specialists
- [ ] Mediator agent that resolves conflicts between specialist opinions
- [ ] Feedback loop — track which checks catch real issues vs noise
- [ ] Knowledge base growth — continuously add new sources and refine roles

---

## Appendix: Key Technical References

### AutoForge Agent Configuration (How It Works Today)

| Agent Type | Max Turns | MCP Tools Available |
|------------|-----------|-------------------|
| Coding | 150 | 10 feature tools + Playwright |
| Testing | 75 | 5 feature tools + Playwright |
| Initializer | 200 | 5 feature tools |
| Reviewer | 100 | Read-only feature tools |
| QA | 250 | Full feature tools + Playwright |

### SDK Sub-Agent Definition Format

```python
agents={
    "security-reviewer": AgentDefinition(
        description="Use when security review is needed",
        prompt="You are a security engineer specializing in OWASP Top 10...",
        tools=["Read", "Grep", "Glob"],  # Read-only
        model="opus",
    )
}
```

Or as a file at `.claude/agents/security-reviewer.md`:
```markdown
---
description: Use when security review is needed
tools: [Read, Grep, Glob]
model: opus
---

You are a security engineer specializing in OWASP Top 10...
```

### Instruction File Cross-Reference

| CLI | File | Auto-loaded | Hierarchical | Global Config |
|-----|------|-------------|--------------|---------------|
| Claude | CLAUDE.md | Yes | Parent + child dirs | ~/.claude/CLAUDE.md |
| Codex | AGENTS.md | Yes | Git root to cwd | ~/.codex/AGENTS.md |
| Gemini | GEMINI.md | Yes | Ancestors + subdirs + tool-triggered | ~/.gemini/GEMINI.md |
