# prd-generator-plugin

A Claude Code plugin that automates the creation of comprehensive Product Requirements Documents (PRDs) with supporting architecture, enforcement mechanisms, and CI/CD infrastructure. Given a product concept, it conducts structured interviews, researches official sources, validates findings, designs technology stacks, and generates enforcement skills to guide AI-assisted development.

## Key Workflow Phases

The `/prd-new` command executes seven phases:

1. **Interactive Interrogation** — Seven-block interview covering identity, business model, core features, regulatory requirements, integrations, infrastructure preferences, and technology stack
2. **Official Research** — Parallel researcher agents consult only vendor documentation, standards bodies, and regulatory portals (blocking forums, blogs, social media)
3. **Validation** — Independent auditor in fresh context verifies research accuracy without prior project knowledge
4. **Requirements Analysis** — Structures functional/non-functional requirements, domain rules, and compliance criteria
5. **Architecture Design** — Proposes modern, compatible technology stack with justifications and diagrams
6. **Artifact Generation** — Produces PRD, architecture documentation, ER diagrams, layer-specific guides, six enforcement skills, and CI/CD pipelines in parallel
7. **Evolution** — Incrementally updates only affected artifacts when scope changes via `/prd-evolve`

## Generated Artifacts

The plugin creates:
- **docs/prd/** — PRD.md, ARCHITECTURE.md, ER.md (source of truth documents)
- **Stack Guides** — CLAUDE.md files per layer applying Clean Code, Clean Architecture, DDD, and Pragmatic Programmer principles
- **.claude/skills/** — Seven project-specific enforcement skills preventing development drift
- **CI/CD Pipeline** — GitHub/GitLab/Bitbucket workflows with monorepo path-filtering
- **docs/stack/** — Local documentation cache preventing redundant web searches

## Mandatory Constraints

All generated projects are **monorepos** with services as top-level directories (backend, frontend, infrastructure, docs). The `project-guardian` skill enforces this as a hard block.

## Research Validation Philosophy

The validator operates in "fresh context" without prior session memory, eliminating confirmation bias. It consults only official sources—blocking Reddit, Stack Overflow, Medium, dev.to, blogs, wikis, and similar platforms—ensuring accuracy and reducing hallucinations.

## Project Evolution

The `/prd-evolve` command applies delta-based updates: analyzing what changed, researching new topics if needed, updating only affected artifacts, and versioning all skills to track synchronization with the PRD.

## Commands

- `/prd-new` — Generate a complete PRD from scratch (7-phase workflow)
- `/prd-evolve` — Incrementally update artifacts after scope changes

## Agents

- **product-interrogator** — Conducts structured interviews and identifies information gaps
- **requirements-analyst** — Transforms context into structured requirements (full/delta modes)
- **architecture-designer** — Designs production-ready architectures (full/update modes)
- **prd-writer** — Generates engineering-grade documentation (full/update modes)
- **skills-generator** — Creates seven enforcement skills for AI-assisted development

## Skills

- **prd-guardian** — Enforces PRD consultation before implementation, architecture, or review work
