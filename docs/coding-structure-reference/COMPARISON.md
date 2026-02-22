# Coding Structure Comparison: AutoForge (Leon) vs VidAi (Martin)

A side-by-side analysis of two distinct approaches to structuring AI-assisted coding projects. AutoForge represents a highly governed autonomous agent factory, while VidAi represents a pragmatic SaaS application development workflow. Both leverage Claude as the coding agent but differ significantly in scope, governance depth, and operational philosophy.

---

## Table of Contents

1. [Document Inventory](#document-inventory)
2. [Project Scope and Purpose](#project-scope-and-purpose)
3. [Tech Stack Comparison](#tech-stack-comparison)
4. [Document Architecture](#document-architecture)
5. [Agent Governance and Workflow](#agent-governance-and-workflow)
6. [Coding Standards and Verification](#coding-standards-and-verification)
7. [Security Model](#security-model)
8. [Design System and UI Framework](#design-system-and-ui-framework)
9. [Testing Strategy](#testing-strategy)
10. [TypeScript and Type Safety](#typescript-and-type-safety)
11. [Context Management](#context-management)
12. [Architecture Documentation](#architecture-documentation)
13. [Git and Version Control Practices](#git-and-version-control-practices)
14. [Database and Backend Patterns](#database-and-backend-patterns)
15. [Shared Best Practices](#shared-best-practices)
16. [Unique Strengths](#unique-strengths)

---

## Document Inventory

| Aspect | AutoForge (Leon) | VidAi (Martin) |
|--------|-------------------|-----------------|
| **Total documents** | 3 | 2 |
| **Combined size** | ~1,071 lines | ~23KB + ~25 lines |
| **Primary reference** | `CLAUDE.md` (509 lines) | `CLAUDE.md` (~23KB) |
| **Agent persona** | `coder.md` (133 lines) | N/A |
| **Operational instructions** | `coding_prompt.template.md` (429 lines) | `AI_RULES.md` (~25 lines) |
| **Prescriptiveness** | Very high | Moderate |

### AutoForge Documents

| Document | Lines | Purpose |
|----------|-------|---------|
| `CLAUDE.md` | 509 | Master project reference: architecture, module map, tech stack, testing commands, security model, WebSocket protocols, prompt loading chain, agent session flow, parallel orchestration, MCP feature management |
| `coder.md` | 133 | Coder agent persona: elite software architect identity, mandatory 3-phase workflow (Research, Implementation, Verification), 8 non-negotiable rules, project-specific context |
| `coding_prompt.template.md` | 429 | Operational instructions for every autonomous coding session: context budget management, 9-step workflow, 15 coding standards, 50+ verification checklist items, mock data detection, server restart persistence testing |

### VidAi Documents

| Document | Size | Purpose |
|----------|------|---------|
| `CLAUDE.md` | ~23KB | Comprehensive architecture reference: dev commands, environment setup (Supabase, Stripe, fal.ai, Resend), auth system, layout system, route structure, shadcn/ui integration, email architecture, database schema, admin system, migrations, troubleshooting |
| `AI_RULES.md` | ~25 lines | Concise tech stack rules: React + TypeScript mandate, file organization, shadcn/ui and Tailwind CSS, production-ready code requirements, git commit rules, pre-installed packages list |

---

## Project Scope and Purpose

| Aspect | AutoForge (Leon) | VidAi (Martin) |
|--------|-------------------|-----------------|
| **Project type** | Autonomous coding agent factory | Standard SaaS application |
| **Core function** | Builds complete applications autonomously over multiple sessions using a two-agent pattern | Video AI platform with user management, payments, and media processing |
| **Agent model** | Two-agent pattern (Initializer + Coding Agent) with parallel orchestration | Single agent with lightweight rules |
| **Autonomy level** | Fully autonomous multi-session execution | Developer-guided single-session work |
| **Complexity** | High (agent orchestration, MCP servers, feature state machines, process management) | Moderate (standard SaaS with auth, payments, admin) |

AutoForge is fundamentally a meta-system: it is software that builds other software. This recursive nature demands far more governance because the coding agent operates without human oversight across multiple sessions. VidAi is a conventional application where the developer is present and can course-correct in real time.

---

## Tech Stack Comparison

### Frontend

| Technology | AutoForge | VidAi |
|------------|-----------|-------|
| **React** | React 19 | React (version unspecified) |
| **TypeScript** | Yes | Yes |
| **Bundler** | Vite 7 | Vite |
| **State management** | TanStack Query | TanStack Query |
| **CSS framework** | Tailwind CSS v4 | Tailwind CSS |
| **Component library** | Radix UI | shadcn/ui (built on Radix UI) |
| **Icons** | Lucide (implied via Radix) | Lucide React |
| **Design philosophy** | Neobrutalism (custom) | Slate theme (shadcn defaults) |
| **Graph/visualization** | dagre (graph layout) | N/A |
| **Terminal** | xterm.js | N/A |
| **Routing** | Hash-based (`/#/docs`) | React Router (routes in App.tsx) |

### Backend

| Technology | AutoForge | VidAi |
|------------|-----------|-------|
| **Language** | Python 3.11+ | TypeScript (Supabase functions) |
| **Framework** | FastAPI | Supabase (BaaS) |
| **ORM** | SQLAlchemy | Supabase client |
| **Database** | SQLite | PostgreSQL (Supabase) |
| **Auth** | N/A (agent system) | Supabase Auth (implicit flow) |
| **Payments** | N/A | Stripe |
| **Email** | N/A | Resend |
| **Media** | N/A | fal.ai |
| **Real-time** | WebSocket (custom) | Supabase real-time |
| **API style** | REST + WebSocket | REST (Supabase auto-generated) |

### Shared Technologies

Both projects use: React, TypeScript, Vite, TanStack Query, Tailwind CSS, Radix UI (directly or via shadcn/ui), and Lucide icons.

---

## Document Architecture

The two systems take fundamentally different approaches to organizing their coding instructions.

### AutoForge: Layered Separation

AutoForge separates concerns across three documents with distinct responsibilities:

```
CLAUDE.md                        -- WHAT the project is (reference)
  |
  +-- coder.md                   -- WHO the agent is (persona + principles)
  |
  +-- coding_prompt.template.md  -- HOW the agent works (operational steps)
```

- **CLAUDE.md** serves as the static knowledge base: architecture, modules, APIs, patterns.
- **coder.md** defines behavioral identity: the agent is an "elite software architect" with 20+ years of experience, meticulous and uncompromising.
- **coding_prompt.template.md** provides the session-by-session playbook: exact steps, budget limits, verification checklists.

This layered approach means each document can evolve independently. The persona stays stable while operational instructions change per session type.

### VidAi: Consolidated Pragmatism

VidAi consolidates almost everything into a single comprehensive `CLAUDE.md`:

```
CLAUDE.md       -- WHAT + HOW (architecture reference + embedded patterns)
  |
  +-- AI_RULES.md  -- Guardrails (concise do/don't rules)
```

- **CLAUDE.md** combines architecture documentation with development patterns, troubleshooting, and migration guides.
- **AI_RULES.md** acts as a short, punchy ruleset -- easy to scan and enforce.

This approach is simpler to maintain and works well when a developer is present to provide additional guidance.

---

## Agent Governance and Workflow

This is where the two systems diverge most dramatically.

### AutoForge: Deep Autonomous Governance

AutoForge's agent operates without human oversight and therefore requires extensive governance:

| Governance Mechanism | Description |
|---------------------|-------------|
| **Context budget system** | 45% target utilization, 48% hard stop. Agent must monitor and manage its own context window. |
| **3-phase mandatory workflow** | Phase 1: Research (explore codebase, identify patterns, research dependencies). Phase 2: Implementation (code quality, security, performance, modularity). Phase 3: Verification (lint, type check, format, test). |
| **9-step operational workflow** | Branch setup, orient, start servers, get feature, implement, verify with browser, update status, commit/push, update progress. |
| **8 non-negotiable rules** | Cannot be overridden. Examples: never skip research, never leave code that fails checks, always verify before finishing. |
| **Feature state machine** | Features move through states (pending, in_progress, passing, failing) via MCP tools with atomic claims for parallel execution. |
| **Turn counting** | Agent monitors how many turns it has used within a session. |
| **Phase gates** | Agent cannot proceed to implementation without completing research. Cannot mark features passing without verification. |
| **Mock data detection** | Agent must detect and eliminate mock/placeholder data. |
| **Server restart persistence** | Agent must verify that changes survive server restarts. |

### VidAi: Lightweight Developer-Guided Rules

VidAi trusts the developer to guide the agent, so rules are minimal:

| Governance Mechanism | Description |
|---------------------|-------------|
| **Tech stack mandate** | React + TypeScript, no exceptions. |
| **File organization** | `src/pages/`, `src/components/` conventions. |
| **UI framework** | shadcn/ui and Tailwind CSS required. |
| **Production-ready mandate** | No workarounds, no placeholder code. |
| **Git hygiene** | No Claude mentions in commit messages. |
| **Package awareness** | Pre-installed packages listed to prevent redundant installs. |

### Comparison Table

| Aspect | AutoForge | VidAi |
|--------|-----------|-------|
| **Workflow steps** | 9 explicit steps per session | No prescribed workflow |
| **Verification checks** | 50+ checklist items | General "production-ready" mandate |
| **Context management** | Budget system with percentage targets | Not addressed |
| **Agent persona** | Defined (elite architect, 20+ years) | Not defined |
| **Phase gates** | Yes (Research -> Implementation -> Verification) | No |
| **Feature tracking** | MCP server with atomic state transitions | Not applicable |
| **Session continuity** | Auto-continue with 3-second delay | Single session |
| **Parallel execution** | Up to 5 concurrent agents with dependency-aware scheduling | N/A |

---

## Coding Standards and Verification

### AutoForge: 15 Explicit Standards + 50+ Verification Checks

AutoForge prescribes coding standards across multiple dimensions:

**Coding Standards (15 rules, examples):**
- Self-documenting code with clear, descriptive names
- Comments that explain WHY, not WHAT
- Functions small and focused on a single responsibility
- Meaningful variable names that reveal intent
- No magic numbers or strings -- use named constants
- Handle all error cases explicitly
- Validate inputs at system boundaries
- Defensive programming techniques

**Verification Checklist (50+ items, examples):**
- Lint passes (ruff for Python, eslint for TypeScript)
- Type checks pass (mypy for Python, tsc for TypeScript)
- Browser automation verification (Playwright)
- Mock data detection and elimination
- Server restart persistence testing
- Feature status updated via MCP tools
- Branch created and pushed
- Commit message follows conventions

### VidAi: ~12 Concise Rules

VidAi's rules are shorter and more prescriptive about technology choices than process:

- React + TypeScript for all code
- React Router with routes defined in App.tsx
- Pages in `src/pages/`, components in `src/components/`
- shadcn/ui for all UI components
- Tailwind CSS for all styling
- Production-ready code only (no workarounds)
- No Claude mentions in git commits
- Use pre-installed packages (listed explicitly)

### Side-by-Side

| Dimension | AutoForge | VidAi |
|-----------|-----------|-------|
| **Number of explicit rules** | 15 coding + 50+ verification | ~12 total |
| **Focus** | Process and quality gates | Technology choices and conventions |
| **Error handling** | "Handle all error cases explicitly" | Implicit (production-ready mandate) |
| **Comments** | "Explain WHY, not WHAT" | Not specified |
| **Function size** | "Small and focused" | Not specified |
| **Magic numbers** | Explicitly banned | Not specified |
| **Input validation** | Required at system boundaries | Not specified |
| **Defensive programming** | Mandated | Not specified |

---

## Security Model

### AutoForge: Defense-in-Depth

AutoForge implements a multi-layered security model because agents execute bash commands autonomously:

| Layer | Mechanism |
|-------|-----------|
| **OS-level sandbox** | Bash commands run in sandboxed environment |
| **Filesystem restriction** | Agent confined to project directory only |
| **Hierarchical bash allowlist** | 5-level priority system for command validation |
| **Hardcoded blocklist** | Commands like `dd`, `sudo`, `shutdown` are never allowed |
| **Org-level blocklist** | `~/.autoforge/config.yaml` -- cannot be overridden by projects |
| **Org-level allowlist** | Available to all projects |
| **Global allowlist** | Default commands (npm, git, curl, etc.) |
| **Project-level allowlist** | `.autoforge/allowed_commands.yaml` with exact match and wildcard patterns |
| **Extra read paths** | Validated absolute paths with sensitive directory blocklist (.ssh, .aws, .gnupg, etc.) |
| **Per-command limits** | Max 100 commands per project config |
| **No hardcoded secrets** | Enforced via coding standards |

**Command Hierarchy (highest to lowest priority):**
1. Hardcoded Blocklist (NEVER allowed)
2. Org Blocklist (cannot be overridden)
3. Org Allowlist (available to all projects)
4. Global Allowlist (default commands)
5. Project Allowlist (project-specific)

### VidAi: Platform-Delegated Security

VidAi delegates most security concerns to its platform services:

| Layer | Mechanism |
|-------|-----------|
| **Auth** | Supabase Auth with implicit flow |
| **Row-level security** | Supabase RLS policies |
| **Environment variables** | Secrets stored in `.env` (gitignored) |
| **Admin access** | Admin system with audit logging |
| **Payment security** | Stripe handles PCI compliance |
| **No hardcoded secrets** | Enforced via AI_RULES.md |

### Comparison

| Aspect | AutoForge | VidAi |
|--------|-----------|-------|
| **Primary threat model** | Autonomous agent executing arbitrary commands | Standard web application threats |
| **Bash command control** | Hierarchical allowlist with 5 priority levels | Not applicable |
| **Filesystem access** | Restricted to project directory + validated extra paths | Standard development access |
| **Sensitive directory protection** | Explicit blocklist (.ssh, .aws, .gnupg, etc.) | Not applicable |
| **Auth system** | N/A (agent system) | Supabase Auth with implicit flow |
| **Database security** | N/A (local SQLite) | Supabase RLS policies |
| **Secrets management** | Env vars + coding standard enforcement | Env vars |
| **Audit logging** | Agent output logging | Admin audit logging |
| **Security testing** | 12 unit tests + 9 integration tests for security | Not specified |

---

## Design System and UI Framework

### AutoForge: Custom Neobrutalism

AutoForge implements a distinctive neobrutalism design system:

- Custom CSS variables defined in `ui/src/styles/globals.css` via `@theme` directive
- Custom animations: `animate-slide-in`, `animate-pulse-neo`, `animate-shimmer`
- Color tokens: `--color-neo-pending` (yellow), `--color-neo-progress` (cyan), `--color-neo-done` (green)
- Semantic color system tied to feature states
- Built directly on Radix UI primitives

### VidAi: shadcn/ui with Slate Theme

VidAi uses the popular shadcn/ui component library:

- Pre-built component library with consistent styling
- Slate color theme (shadcn default)
- Tailwind CSS for utility styling
- Radix UI under the hood (via shadcn)
- Standard component patterns (buttons, forms, dialogs, etc.)

### Comparison

| Aspect | AutoForge | VidAi |
|--------|-----------|-------|
| **Design philosophy** | Neobrutalism (bold, distinctive) | Clean, professional (slate theme) |
| **Component source** | Custom-built on Radix UI | shadcn/ui pre-built components |
| **CSS approach** | Custom CSS vars via @theme + Tailwind v4 | Tailwind CSS + shadcn defaults |
| **Animations** | Custom (slide-in, pulse-neo, shimmer) | Standard/minimal |
| **Color system** | Semantic tokens tied to application state | Slate theme palette |
| **Customization effort** | High (everything custom) | Low (pre-built library) |
| **Visual identity** | Highly distinctive | Professional standard |

---

## Testing Strategy

### AutoForge: Multi-Layer Mandatory Testing

| Test Type | Tool | Description |
|-----------|------|-------------|
| Python lint | ruff | `ruff check .` |
| Python types | mypy | `mypy .` (strict return types) |
| Security unit tests | unittest | 12 tests in `test_security.py` |
| Security integration | unittest | 9 tests in `test_security_integration.py` |
| Client tests | pytest | 20 tests in `test_client.py` |
| Dependency resolver | pytest | 12 tests in `test_dependency_resolver.py` |
| Rate limit utils | pytest | 22 tests in `test_rate_limit_utils.py` |
| JS lint | eslint | `npm run lint` |
| JS build/types | Vite/tsc | `npm run build` |
| E2E tests | Playwright | `npm run test:e2e` |
| Browser verification | Playwright MCP | Agent verifies features in browser |
| Mock data detection | Manual/automated | Agent checks for placeholder data |
| Server restart tests | Manual/automated | Agent verifies persistence across restarts |
| CI/CD | GitHub Actions | Python job (ruff + security) + UI job (eslint + tsc) |

### VidAi: Referenced but Less Prescriptive

VidAi references testing but provides fewer specifics:

- Tests are mentioned but not elaborated in detail
- No explicit browser automation verification
- No mock data detection requirements
- No server restart persistence testing
- Production-ready mandate implies testing but does not prescribe methods

### Comparison

| Aspect | AutoForge | VidAi |
|--------|-----------|-------|
| **Explicit test commands** | 7+ distinct test suites | Referenced but not enumerated |
| **Browser automation** | Playwright MCP (mandatory for feature verification) | Not specified |
| **Mock data detection** | Explicit requirement | Not specified |
| **Server restart testing** | Explicit requirement | Not specified |
| **CI/CD pipeline** | GitHub Actions (Python + UI jobs) | Not specified |
| **Security-specific tests** | 21 dedicated tests | Not specified |
| **E2E tests** | Playwright | Not specified |

---

## TypeScript and Type Safety

| Aspect | AutoForge | VidAi |
|--------|-----------|-------|
| **TypeScript strict mode** | Implied strict (mypy strict on Python side) | `strict: false` |
| **noImplicitAny** | Standard (likely true) | `false` (relaxed) |
| **Python type checking** | mypy with strict return types | N/A (no Python) |
| **Type check in CI** | Yes (build step) | Not specified |
| **Philosophy** | Maximum type safety across both languages | Pragmatic flexibility over strictness |

AutoForge treats type safety as a non-negotiable quality gate. VidAi relaxes TypeScript strictness, presumably to reduce friction during rapid development. This is a meaningful philosophical difference: AutoForge optimizes for long-term maintainability at the cost of initial velocity, while VidAi optimizes for development speed.

---

## Context Management

### AutoForge: Sophisticated Budget System

AutoForge implements explicit context window management for its autonomous agents:

- **45% target utilization**: Agent should aim to use no more than 45% of available context
- **48% hard stop**: Agent must stop and hand off if context reaches 48%
- **Turn counting**: Agent tracks turns consumed within a session
- **Auto-continue**: Sessions chain with 3-second delays, allowing work to span multiple context windows

This is necessary because AutoForge agents run autonomously. Without context management, an agent could exhaust its context window mid-feature, leaving the codebase in an inconsistent state.

### VidAi: Not Addressed

VidAi does not address context management. This is reasonable because:

- A developer is present to manage conversation flow
- Sessions are typically single-turn or short multi-turn
- The developer can manually reset context when needed

### Why This Matters

Context management is one of the clearest indicators of the autonomy gap between the two systems. Any system that runs agents without human oversight must solve the "context cliff" problem -- where an agent runs out of context mid-task. AutoForge's budget system is a direct response to this challenge.

---

## Architecture Documentation

| Aspect | AutoForge | VidAi |
|--------|-----------|-------|
| **Architecture location** | Separate ARCHITECTURE.md (mandated) + CLAUDE.md | Embedded in CLAUDE.md |
| **Module map** | Detailed (every file and its purpose) | Route and component structure |
| **Database schema** | SQLAlchemy models documented | Supabase schema with CASCADE DELETE documented |
| **API documentation** | Router-by-router breakdown | Endpoint patterns described |
| **Service layer** | Explicit services directory with descriptions | Service patterns via Supabase |
| **Layout system** | Component hierarchy documented | 3-layout system (Public/Auth/Dashboard) |
| **Migration strategy** | JSON-to-SQLite migration utility + legacy path support | Database migrations documented |
| **Troubleshooting** | Not in main docs | Dedicated troubleshooting section |

---

## Git and Version Control Practices

| Aspect | AutoForge | VidAi |
|--------|-----------|-------|
| **Branch naming** | Elaborate conventions (feature branches, naming patterns) | Not specified |
| **Commit messages** | Conventions specified | "No Claude mentions" is the primary rule |
| **Push requirements** | Mandatory push after feature completion | Not specified |
| **CI integration** | GitHub Actions on push/PR to master | Not specified |
| **Branch per feature** | Yes (part of 9-step workflow) | Not specified |

---

## Database and Backend Patterns

| Aspect | AutoForge | VidAi |
|--------|-----------|-------|
| **Database** | SQLite (local, per-project) | PostgreSQL (Supabase hosted) |
| **ORM** | SQLAlchemy | Supabase client SDK |
| **Schema management** | Code-defined models + migration utility | Supabase migrations |
| **Cascade behavior** | Not specified | CASCADE DELETE documented |
| **Auth storage** | N/A | Supabase Auth tables |
| **Admin system** | N/A | User management, invitations, audit logging |
| **Payment data** | N/A | Stripe with two-way sync |
| **Real-time** | Custom WebSocket | Supabase real-time subscriptions |

---

## Shared Best Practices

Despite their different scopes and approaches, both systems agree on several fundamental principles:

### Technology Choices

1. **React + TypeScript** -- Both mandate React with TypeScript for frontend development
2. **Tailwind CSS** -- Both use Tailwind CSS as the primary styling approach
3. **Radix UI foundations** -- Both build on Radix UI primitives (AutoForge directly, VidAi via shadcn/ui)
4. **TanStack Query** -- Both use TanStack Query for server state management
5. **Lucide icons** -- Both use Lucide for iconography
6. **Vite** -- Both use Vite as the build tool

### Security Principles

7. **No hardcoded secrets** -- Both explicitly prohibit hardcoding credentials, API keys, or secrets in source code
8. **Environment variable management** -- Both rely on `.env` files for sensitive configuration

### Code Quality

9. **Production-ready code** -- Both demand production-quality code, not prototypes or workarounds
10. **Service layer separation** -- Both employ service layers and separation of concerns in their architectures
11. **Component-based UI** -- Both organize UI code into reusable, focused components

### Development Practice

12. **Clear file organization** -- Both specify where different types of code should live (pages, components, services)
13. **Linting** -- Both include linting in their workflows (eslint for TypeScript, ruff for Python)
14. **Consistent patterns** -- Both emphasize following established codebase patterns rather than introducing new ones

---

## Unique Strengths

### AutoForge: Strengths for Autonomous Agent Systems

| Strength | Why It Matters |
|----------|----------------|
| **Context budget management** | Prevents agents from exhausting context mid-task, ensuring graceful handoffs between sessions. Essential for unsupervised operation. |
| **3-phase mandatory workflow** | Research -> Implementation -> Verification flow prevents the common agent failure mode of jumping straight to code without understanding the codebase. |
| **Defense-in-depth security** | Multi-layered bash command validation prevents autonomous agents from executing dangerous commands. The hierarchical allowlist (5 levels) provides granular control. |
| **Feature state machine via MCP** | Atomic state transitions (pending -> in_progress -> passing/failing) prevent race conditions in parallel agent execution and provide clear progress tracking. |
| **50+ verification checklist** | Comprehensive quality gates catch issues that a human reviewer would catch, compensating for the absence of human oversight. |
| **Mock data detection** | Agents can generate convincing-looking but fake data. Explicit detection requirements prevent this common failure mode. |
| **Server restart persistence testing** | Catches the subtle bug class where features work in development but fail after restart (missing migrations, in-memory-only state, etc.). |
| **Parallel orchestration** | Dependency-aware scheduling of up to 5 concurrent agents with process limits is a sophisticated approach to accelerating large projects. |
| **Agent persona definition** | The "elite software architect" persona with 20+ years of experience primes the model for careful, thorough work rather than quick-and-dirty solutions. |
| **Session continuity** | Auto-continue with 3-second delays allows multi-session feature implementation without human intervention. |

### VidAi: Strengths for Developer-Guided SaaS Development

| Strength | Why It Matters |
|----------|----------------|
| **Concise, scannable rules** | ~25 lines of AI_RULES.md can be read in 30 seconds. Low cognitive overhead means rules are more likely to be followed consistently. |
| **Comprehensive architecture-in-CLAUDE.md** | Having architecture, troubleshooting, and patterns in one file means the agent always has full context without needing to load multiple documents. |
| **Platform-delegated security** | Leveraging Supabase RLS and Stripe's PCI compliance is more maintainable than building custom security layers for a SaaS application. |
| **Pre-installed package list** | Explicitly listing available packages prevents the common agent behavior of installing redundant or conflicting dependencies. |
| **Troubleshooting section** | Dedicated troubleshooting guidance helps the agent self-diagnose common issues (auth flows, Stripe sync, email delivery) without developer intervention. |
| **shadcn/ui standardization** | Using a well-known component library reduces decision fatigue and ensures visual consistency with minimal custom CSS. |
| **Layout system documentation** | The 3-layout system (Public/Auth/Dashboard) provides clear architectural boundaries that prevent layout-related bugs. |
| **Pragmatic TypeScript** | Relaxed strictness (`strict: false`, `noImplicitAny: false`) reduces friction during rapid feature development while still providing basic type safety. |
| **Admin system with audit logging** | Built-in administrative capabilities with audit trails provide operational visibility without custom tooling. |
| **Two-way Stripe sync** | Documented sync patterns between Stripe and Supabase prevent the common SaaS bug of payment state inconsistency. |

---

## Summary Matrix

| Dimension | AutoForge (Leon) | VidAi (Martin) |
|-----------|-------------------|-----------------|
| **Project type** | Autonomous agent factory | SaaS application |
| **Document count** | 3 | 2 |
| **Total instruction volume** | ~1,071 lines | ~23KB + ~25 lines |
| **Agent autonomy** | Fully autonomous, multi-session | Developer-guided, single-session |
| **Governance depth** | Deep (budgets, phases, gates, checklists) | Light (concise rules) |
| **Security model** | Defense-in-depth, 5-level command hierarchy | Platform-delegated (Supabase RLS) |
| **Design system** | Custom neobrutalism | shadcn/ui slate theme |
| **Testing rigor** | 75+ tests, browser automation, mock detection | Production-ready mandate |
| **TypeScript strictness** | Strict | Relaxed |
| **Context management** | Budget system (45%/48%) | Not addressed |
| **Coding standards** | 15 explicit + 50+ verification | ~12 concise rules |
| **Best for** | Unsupervised agent execution at scale | Rapid developer-guided SaaS building |

---

*Document created: 2026-02-21. This comparison is based on the document structures and contents as described. Both approaches are valid for their respective use cases -- the right choice depends on the level of agent autonomy and the nature of the project being built.*
