# rodrigorjsf/prd-generator-plugin

> Source: https://github.com/rodrigorjsf/prd-generator-plugin
> Extracted: 2026-04-01

## Overview

AI-powered PRD generator Claude Code plugin that transforms product ideas into comprehensive, research-backed PRDs with modern architecture design, enforcement skills, CI/CD pipelines, documentation caching, and self-evolving project documentation for AI-assisted development.

## Core Capabilities

- Conducts structured, sequential interviews across seven distinct blocks
- Automatically researches official documentation sources (excluding forums/blogs)
- Validates research findings in fresh, unbiased contexts to prevent hallucinations
- Proposes compatible, modern technology stacks as monorepos
- Generates complete PRD, architecture documents, and ER diagrams
- Creates seven project-specific Claude skills preventing AI violations during development
- Produces CLAUDE.md files per stack layer with Clean Code and Clean Architecture principles
- Generates lean CI/CD pipelines (GitHub/GitLab/Bitbucket) with monorepo path-filtering
- Atomically updates all documents and skills when product scope changes

## Installation

```bash
claude plugin install prd-generator-plugin
# or local:
git clone https://github.com/rodrigo/prd-generator-plugin
claude plugin install ./prd-generator-plugin
```

## Commands

| Command | Usage |
|---------|-------|
| `/prd-new` | Create new PRD from product description |
| `/prd-evolve` | Evolve existing PRD when scope changes |
| `/prd-docs` | Refresh project documentation |

## Repository Structure

```
prd-generator-plugin/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   ├── architecture-designer.md
│   ├── cicd-generator.md
│   ├── official-researcher.md
│   ├── prd-writer.md
│   ├── product-interrogator.md
│   ├── requirements-analyst.md
│   ├── research-validator.md
│   ├── skills-generator.md
│   └── stack-guide-generator.md
├── commands/
│   ├── prd-docs.md
│   ├── prd-evolve.md
│   └── prd-new.md
├── docs/
│   └── plans/
├── skills/
│   └── prd-guardian/
│       └── SKILL.md
├── .gitignore
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Workflow: /prd-new (7 Phases)

1. **Initialize** -- Set up context_packet JSON and progress tracking
2. **Product Interrogation** -- 7-block conversational interview (Identity, Business, Features, Regulatory, Integrations, Infrastructure, Stack)
3. **Official Research** -- Parallel researcher agents with blocked domains enforcement
4. **Research Validation** -- Independent auditor in fresh context (no prior session memory)
5. **Requirements Analysis** -- Structured RF/RNF/domain rules/compliance
6. **Architecture Design** -- Modern stack proposal with user approval gate
7. **Document Generation** -- Parallel generation of PRD, skills, guides, CI/CD

## Agent Reference

| Agent | Role | Model |
|-------|------|-------|
| product-interrogator | Gap analysis, research target identification | Sonnet |
| official-researcher | Official source searches with blocked_domains enforcement | Sonnet |
| research-validator | Independent audit, hallucination detection in fresh context | Sonnet |
| requirements-analyst | RF/RNF/domain rules/compliance structuring; delta mode for evolution | Sonnet |
| architecture-designer | Modern stack proposals, Mermaid diagrams, ADRs | Opus |
| prd-writer | PRD.md, ARCHITECTURE.md, ER.md generation | Sonnet |
| stack-guide-generator | Layer-specific CLAUDE.md, docs/stack/, .claude/settings.json | Sonnet |
| skills-generator | Seven project enforcement skill generation | Sonnet |
| cicd-generator | VCS-specific CI/CD pipeline generation with path-filtering | Sonnet |

## Generated Skills (7 Total)

1. `project-guardian` -- PRD compliance and monorepo rule enforcement
2. `project-architecture` -- Stack canonical reference and ADR enforcement
3. `project-domain-rules` -- Domain invariants and ubiquitous language
4. `project-compliance` -- Compliance checklist per regulation
5. `project-docs-stack` -- Local-first documentation cache enforcement
6. `project-cicd` -- Pipeline consistency and evolution triggers
7. `project-docs` -- Living documentation maintenance

## Blocked Research Domains

reddit.com, stackoverflow.com, medium.com, dev.to, hashnode.dev, hackernoon.com, dzone.com, freecodecamp.org, digitalocean.com, tutorialspoint.com, geeksforgeeks.org, w3schools.com, baeldung.com, towardsdatascience.com, quora.com, discord.com, twitter.com, linkedin.com, youtube.com, wikipedia.org

## Token Efficiency Design

- JSON context_packets instead of conversation history
- Slice delivery: agents receive only necessary context
- Parallel dispatch for concurrent research
- Selective evolution: only changed artifacts regenerated
- Compressed skills: tables and bullets, never lengthy paragraphs

## License

MIT
