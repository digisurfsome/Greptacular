# PRD Generator Plugin – /prd-new Command

This document outlines a **comprehensive Product Requirements Document (PRD) generation workflow** orchestrated through a multi-phase agent-driven system.

## Core Architecture

The plugin operates across **7 sequential phases**, each producing structured outputs that feed into the next stage:

1. **Initialize** – Set up progress tracking and a `context_packet` JSON object (held in memory throughout execution)
2. **Product Interrogation** – Conduct conversational, one-question-at-a-time interviews across 7 blocks (Identity, Business Model, Core Features, Regulatory, Integrations, Infrastructure, Stack Preference)
3. **Official Research & Validation** – Dispatch parallel researcher agents for identified technologies and regulations; validate findings with validator agents (max 3 requery cycles)
4. **Requirements Analysis** – Generate structured requirements via a dedicated analyst agent
5. **Architecture Design** – Produce system architecture, stack decisions, and ADRs; request user approval via AskUserQuestion
6. **Document Generation** – Execute four parallel agents (prd-writer, stack-guide-generator, skills-generator, cicd-generator), then apply project-docs skill in CREATE mode
7. **Commit** – Stage and commit all generated artifacts with standardized message format

## Critical Design Rules

- **Monorepo mandate**: All projects are hardcoded as monorepos; no user override allowed
- **Language handling**: Files in English; user communication in their detected language
- **Research discipline**: No forums, blogs, or social media sources; only official documentation
- **JSON-first flow**: Each phase produces structured JSON for downstream consumption
- **Parallel dispatch**: Research, validation, and document generation use simultaneous Agent calls

## Key Interrogation Blocks

The system captures:

- **Identity**: Product vision, target user, core problem, competitive landscape
- **Business**: Monetization model, KPIs, target scale
- **Features**: MVP features, real-time requirements, mobile needs
- **Regulatory**: Operating regions, data handling (GDPR/LGPD), payment processing, regulated sectors
- **Integrations**: External APIs, legacy system connections, authentication providers
- **Infrastructure**: Cloud provider, SLA targets, data residency, budget tier, VCS, branch strategy
- **Stack**: AI-assisted technology selection or user preferences, team size, deployment timeline

## Document Artifacts Generated

- **PRD.md** – Complete product requirements
- **ARCHITECTURE.md** – System design and ADRs
- **ER.md** – Entity-relationship diagrams (if applicable)
- **7 enforcement skills** – Guardian, Architecture, Domain Rules, Compliance, Docs-Stack, CI/CD, Project-Docs
- **Living documentation** – `docs/index.md` plus 6 sub-files (business, architecture, structure, development, tech-stack, local-setup)
- **Stack guides** – CLAUDE.md files for backend, frontend (if applicable), infrastructure
- **CI/CD pipeline** – Generated for GitHub, GitLab, or Bitbucket per user selection

## Research & Validation Loop

When technologies or regulations are identified:

1. Dispatch `official-researcher` agents in parallel with topic, context, and search goals
2. Run a `research-validator` agent batch to approve findings
3. On failure: re-dispatch and re-validate (up to 3 iterations per batch)
4. If unvalidated after 3 cycles: flag as partially validated and continue PRD generation with WARNING section

## Handoff & Evolution

The system concludes by:

- Verifying all expected files exist (27+ artifacts)
- Committing all outputs with standardized message format
- Directing users to `/prd-evolve` for scope change synchronization

This plugin is designed for **AI-assisted development** in teams of any size, with built-in enforcement skills to maintain architecture coherence and compliance throughout the product lifecycle.
