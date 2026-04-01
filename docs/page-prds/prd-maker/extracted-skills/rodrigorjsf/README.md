# prd-generator-plugin

> An AI-powered Claude Code plugin that transforms a product idea into a complete, research-backed PRD with modern architecture design, enforcement skills, CI/CD pipeline, documentation cache infrastructure, and self-evolving project documentation — ready for AI-assisted development.

---

## What It Does

Given a product idea, this plugin:

1. **Interrogates** — conducts a structured, one-question-at-a-time interview covering business model, features, compliance, integrations, infrastructure, and VCS choice
2. **Researches** — automatically searches official documentation sources (never forums or blogs) for every technology and regulatory domain identified
3. **Validates** — audits research in a fresh, unbiased context to eliminate hallucinations and stale information
4. **Designs** — proposes a modern, compatible technology stack tailored to the product (not just what you know), structured as a monorepo
5. **Documents** — generates a complete PRD, architecture document, and ER diagram
6. **Enforces** — creates six project-specific Claude skills that prevent AI coding agents from violating your product decisions during development
7. **Guides** — produces CLAUDE.md files for each stack layer with best practices from Clean Code, Clean Architecture, DDD, and The Pragmatic Programmer; includes local documentation cache policy
8. **Pipelines** — generates a lean CI/CD pipeline for your VCS (GitHub/GitLab/Bitbucket) with path-filtering per monorepo service
9. **Evolves** — updates all documents, skills, and CI/CD pipeline atomically when the product scope changes

---

## Installation

Install via Claude Code plugin system:

```bash
claude plugin install prd-generator-plugin
```

Or clone and install locally:

```bash
git clone https://github.com/rodrigo/prd-generator-plugin
claude plugin install ./prd-generator-plugin
```

---

## Usage

### Create a new PRD

```bash
/prd-new
# or with an initial description:
/prd-new "A B2B SaaS platform for managing construction project budgets"
```

### Evolve the PRD when scope changes

```bash
/prd-evolve "Added Pix payment integration and BACEN compliance requirements"
/prd-evolve "Removed mobile app from scope, focusing on web-only MVP"
/prd-evolve "Changed database from MySQL to PostgreSQL for JSONB support"
```

---

## Complete Workflow — `/prd-new`

```mermaid
flowchart TD
    A(["/prd-new initial description"]) --> B

    subgraph PHASE1["Phase 1 — Interactive Interrogation"]
        B["Block 1: Identity\nname, vision, users, problem"]
        B --> C["Block 2: Business\nmonetization, KPIs, scale"]
        C --> D["Block 3: Core Features\nMVP list, real-time, mobile"]
        D --> E["Block 4: Regulatory\nGDPR/LGPD, payments, sector"]
        E --> F["Block 5: Integrations\nexternal APIs, auth providers"]
        F --> G["Block 6: Infrastructure\ncloud, SLA, budget, geo, VCS, branch strategy"]
        G --> H["Block 7: Stack Preference\nAI-suggested or user-defined"]
    end

    subgraph PHASE2["Phase 2 — Official Research (parallel)"]
        I["official-researcher × N\nparallel instances\nblocked: forums, blogs, wikis"]
        J["research-validator\nFRESH CONTEXT\nverifies accuracy + officiality"]
        K{Approved?}
        I --> J --> K
        K -->|"no (max 3x)"| I
    end

    subgraph PHASE3["Phase 3 — Analysis"]
        L["requirements-analyst\nRF / RNF / domain rules\ncompliance / acceptance criteria"]
    end

    subgraph PHASE4["Phase 4 — Architecture"]
        M["architecture-designer\nmodern stack selection\nMermaid diagrams + ADRs"]
        N{User approves\narchitecture?}
        M --> N
        N -->|"adjust"| M
    end

    subgraph PHASE5["Phase 5 — Generation (parallel)"]
        O["prd-writer\nPRD.md\nARCHITECTURE.md\nER.md"]
        P["stack-guide-generator\nbackend/CLAUDE.md\nfrontend/CLAUDE.md\ninfrastructure/CLAUDE.md\ndocs/stack/ + .claude/settings.json"]
        Q["skills-generator\nproject-guardian\nproject-architecture\nproject-domain-rules\nproject-compliance\nproject-docs-stack\nproject-cicd"]
        R2["cicd-generator\n.github/workflows/ci.yml\n(or .gitlab-ci.yml\nor bitbucket-pipelines.yml)"]
    end

    R[("git commit\nall artifacts")]

    B -->|"tech/domain identified"| I
    K -->|yes| L
    H --> L
    L --> M
    N -->|approved| O & P & Q & R2
    O & P & Q & R2 --> R
```

---

## Research Validation Loop

```mermaid
flowchart LR
    A["official-researcher\nWebSearch + WebFetch\nbanned: forums/blogs/social"] -->|research_refs| B
    B["research-validator\n🔴 FRESH CONTEXT\nno prior session memory"] --> C{Approved?}
    C -->|"✅ yes"| D[("research_refs\nvalidated")]
    C -->|"❌ issues found\nmax 3 iterations"| E["re-research\nwith correction\nguidance"]
    E --> A
    C -->|"3rd attempt fails"| F["mark as\npartially_validated\nlog issues for user"]
```

**Why fresh context?** The validator has no knowledge of the project, user preferences, or prior decisions. This eliminates confirmation bias — it cannot rationalize accepting bad research because "it fits what we decided."

**Official sources only:** Every WebSearch call uses `blocked_domains` to exclude Reddit, Medium, Stack Overflow, dev.to, blogs, wikis, and social media. Only vendor documentation, standards bodies, and government portals are accepted.

---

## Evolution Flow — `/prd-evolve`

```mermaid
flowchart TD
    A(["/prd-evolve 'change description'"]) --> B["Read current state\nPRD.md + ARCHITECTURE.md\n+ all project skills"]
    B --> C["requirements-analyst\nDELTA MODE\nwhat changed? what's affected?"]
    C --> D{New tech or\nregulation?}
    D -->|yes| E["official-researcher\n+ research-validator\nfor new topics only"]
    D -->|no| F
    E --> F{Architecture\nchanged?}
    F -->|yes| G["architecture-designer\npresent changes\nto user for approval"]
    F -->|no| H
    G --> H["Update ONLY affected artifacts\nin parallel"]
    H --> I[("git commit\nnew prd_version")]

    style H fill:#f9f,stroke:#333
```

**Selective updates — only what changed:**
| Change Type | Artifacts Updated |
|---|---|
| New feature | PRD.md §2, project-domain-rules |
| New domain rule | PRD.md §4, project-domain-rules, project-guardian |
| New technology | ARCHITECTURE.md, project-architecture, `{layer}/CLAUDE.md`, CI/CD pipeline, project-cicd |
| Architecture pivot | ARCHITECTURE.md, project-architecture, CI/CD pipeline, project-cicd |
| Compliance change | PRD.md §3.5, project-compliance |
| New integration | PRD.md §5, project-architecture |
| Feature removed | All — orphaned references cleared |

---

## Generated Artifacts

```mermaid
graph LR
    subgraph Plugin["Plugin (installed globally)"]
        CMD1["/prd-new"]
        CMD2["/prd-evolve"]
        SK["prd-guardian skill\nmeta-enforcer"]
    end

    subgraph Project["Your Project Repository"]
        subgraph Docs["docs/prd/"]
            D1["PRD.md\nsource of truth"]
            D2["ARCHITECTURE.md\nstack + ADRs + diagrams"]
            D3["ER.md\nentity model"]
        end

        subgraph Guides["Stack Development Guides"]
            G0["CLAUDE.md (root)\ncross-cutting rules"]
            G1["backend/CLAUDE.md\nClean Code + Clean Arch + DDD"]
            G2["frontend/CLAUDE.md\ncomponent standards"]
            G3["infrastructure/CLAUDE.md\nIaC + security baseline"]
        end

        subgraph Skills[".claude/skills/"]
            S1["project-guardian\nPRD compliance enforcer"]
            S2["project-architecture\nstack + layer rules"]
            S3["project-domain-rules\nbusiness invariants"]
            S4["project-compliance\nGDPR/LGPD/PCI/etc."]
        end
    end

    CMD1 -->|generates| Docs
    CMD1 -->|generates| Guides
    CMD1 -->|generates| Skills
    CMD2 -->|updates| Docs
    CMD2 -->|updates| Guides
    CMD2 -->|updates| Skills
```

---

## Project Skills — Self-Evolution

Each generated skill carries a version header:

```yaml
---
name: project-domain-rules
description: Use when implementing business logic in PayFlow
prd_version: 1.3
last_evolved: 2026-02-28
evolved_by: /prd-evolve "added Pix payment module"
---
```

When skills are out of sync with the PRD, the global `prd-guardian` skill warns:

> *"Project skills are stale (skill: v1.2, PRD: v1.3). Run `/prd-evolve` to sync before proceeding."*

### Evolution Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Active: /prd-new generates v1.0
    Active --> Active: feature development\nprd-guardian enforces
    Active --> Evolving: /prd-evolve called
    Evolving --> Active: delta applied\nskills updated to vX.Y
    Active --> Archived: product complete
```

---

## Component Reference

### Commands

| Command | Description |
|---|---|
| `/prd-new [description]` | Full interactive PRD generation workflow |
| `/prd-evolve [change]` | Incremental evolution — updates only affected artifacts |

### Agents

| Agent | Role | Model |
|---|---|---|
| `product-interrogator` | Analyzes partial context, identifies gaps and research targets | sonnet |
| `official-researcher` | Searches official sources with blocked_domains enforcement | sonnet |
| `research-validator` | Independent audit in fresh context — catches hallucinations | sonnet |
| `requirements-analyst` | Structures RF/RNF/domain rules/compliance from raw context | sonnet |
| `architecture-designer` | Proposes modern stack + Mermaid diagrams + ADRs | opus |
| `prd-writer` | Writes PRD.md, ARCHITECTURE.md, ER.md | sonnet |
| `stack-guide-generator` | Generates CLAUDE.md per stack layer; also generates `docs/stack/` and `.claude/settings.json` | sonnet |
| `skills-generator` | Generates 6 project enforcement skills | sonnet |
| `cicd-generator` | Generates lean CI/CD pipeline for GitHub/GitLab/Bitbucket with monorepo path-filtering | sonnet |

### Skills (shipped with plugin)

| Skill | Trigger |
|---|---|
| `prd-guardian` | Any project with `docs/prd/PRD.md` — enforces habit of checking project skills |

---

## Interrogation Blocks

The `/prd-new` command conducts a structured interview across 7 blocks:

```mermaid
flowchart LR
    A["Identity\nname · vision · users · problem"] -->
    B["Business\nmonetization · KPIs · scale"] -->
    C["Features\nMVP list · real-time · mobile"] -->
    D["Regulatory\nGDPR · LGPD · PCI · sector"] -->
    E["Integrations\nAPIs · auth · legacy systems"] -->
    F["Infrastructure\ncloud · SLA · budget · geo · VCS · branch strategy"] -->
    G["Stack\nAI-suggested or user preferences"]
```

Each block feeds into the `context_packet` JSON that flows through all downstream agents — never as prose, always structured.

---

## Stack Selection Philosophy

This plugin assumes AI-assisted development. Stack is chosen by the `architecture-designer` based on:

- **Product fit** — domain requirements, compliance needs, expected scale
- **AI coding coverage** — technologies with rich documentation and training data
- **Modern + compatible** — current stable versions, verified cross-component compatibility
- **Clean Architecture alignment** — stacks that enable proper layer separation

The user is always shown the proposal with justifications and can adjust before anything is written.

---

## Token Efficiency Design

The workflow is designed to minimize token consumption without losing context:

- **JSON context_packets** — agents receive structured data, not full conversation history
- **Slice delivery** — each agent receives only the context slice it needs
- **Parallel dispatch** — research agents run concurrently (not sequentially)
- **Selective evolution** — `/prd-evolve` regenerates only what changed
- **Compressed skills** — skills use tables and bullets, never paragraphs

---

## Literature Applied in Generated Guides

Every `CLAUDE.md` generated by `stack-guide-generator` applies:

| Book | Principles Applied |
|---|---|
| *Clean Code* — Robert C. Martin | Naming, function size, comments policy, single responsibility |
| *Clean Architecture* — Robert C. Martin | Dependency rule, layer structure, interface adapters |
| *The Pragmatic Programmer* — Hunt & Thomas | DRY, orthogonality, design by contract, tracer bullets |
| *Domain-Driven Design* — Eric Evans | Ubiquitous language, aggregates, repositories, bounded contexts |
| *SOLID Principles* | SRP, OCP, LSP, ISP, DIP adapted to the chosen language |
| *12-Factor App* | Config, backing services, dev/prod parity |

---

## Official Sources Enforcement

The `official-researcher` agent uses `blocked_domains` on every search:

**Blocked (never consulted):**
`reddit.com`, `stackoverflow.com`, `medium.com`, `dev.to`, `hashnode.dev`, `hackernoon.com`, `dzone.com`, `freecodecamp.org`, `digitalocean.com`, `tutorialspoint.com`, `geeksforgeeks.org`, `w3schools.com`, `baeldung.com`, `towardsdatascience.com`, `quora.com`, `discord.com`, `twitter.com`, `linkedin.com`, `youtube.com`, `wikipedia.org`

**Allowed:**
- Official vendor documentation (`docs.aws.amazon.com`, `nextjs.org/docs`, `docs.stripe.com`, etc.)
- Standards bodies (`rfc-editor.org`, `owasp.org`, `iso.org`, `pcisecuritystandards.org`)
- Government/regulatory portals (`gov.br/anpd`, `planalto.gov.br`, `bcb.gov.br`, `ec.europa.eu`, `gdpr.eu`)
- Official language/framework sites (`nodejs.org`, `python.org`, `go.dev`, `rust-lang.org`)

---

## Monorepo Structure (Mandatory)

All projects generated by prd-generator-plugin are **monorepos**. This is a plugin-level decision, not configurable. Services are top-level directories:

```
/project-root
├── backend/        ← API service
├── frontend/       ← Web/mobile app (if applicable)
├── infrastructure/ ← IaC
├── docs/
│   ├── index.md    ← Living documentation entry point
│   ├── business.md / architecture.md / structure.md / ...  ← Living docs sub-files
│   ├── prd/        ← Generated PRD, ARCHITECTURE, ER docs
│   └── stack/      ← Local documentation cache
└── .claude/
    ├── skills/     ← 7 project enforcement skills
    └── settings.json ← Claude Code hooks (PreToolUse for docs-stack)
```

The `project-guardian` skill enforces this as a Hard Block: creating a service in a separate repository is always blocked.

---

## Local Documentation Cache (`docs/stack/`)

Claude checks `docs/stack/` before any web search. The `project-docs-stack` skill enforces this protocol and a `PreToolUse` hook in `.claude/settings.json` reminds Claude before every `WebFetch`/`WebSearch`:

1. Before fetching: check `docs/stack/` index
2. If not found locally: fetch externally, then save to `docs/stack/`
3. If found but incomplete: fetch missing sections, update the local doc

This prevents repeated web searches across sessions for the same technologies.

---

## Generated Skills (v2.1 — 7 total)

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `project-guardian` | Before any implementation | PRD compliance, monorepo rule enforcement |
| `project-architecture` | When writing/reviewing code | Stack canonical reference, ADR enforcement |
| `project-domain-rules` | When implementing business logic | Domain invariants, ubiquitous language |
| `project-compliance` | When handling regulated data | Compliance checklist per regulation |
| `project-docs-stack` | Before any web search | Local-first docs cache, prevents redundant searches |
| `project-cicd` | On stack changes | Pipeline consistency, evolution triggers |
| `project-docs` | After any implementation change | Living docs maintenance — creates and updates docs/ tree |

---

## CI/CD Pipeline Generation

During `/prd-new`, Claude asks for your VCS and branch strategy (Block 6), then generates a lean pipeline:

| VCS | Output File | Path Filtering |
|-----|-------------|----------------|
| GitHub | `.github/workflows/ci.yml` | `dorny/paths-filter` action |
| GitLab | `.gitlab-ci.yml` | Native `rules:changes` |
| Bitbucket | `bitbucket-pipelines.yml` | Native `condition.changesets` |

Each service in the monorepo gets its own job, triggered only when its directory has changes. The `project-cicd` skill tracks consistency and `/prd-evolve` re-generates the pipeline when the stack changes.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Follow the existing agent/command file conventions
4. Test your changes with a real `/prd-new` invocation
5. Submit a pull request

---

## License

MIT
