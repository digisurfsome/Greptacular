# Skills Generator Agent

A Claude agent that generates **seven project-specific enforcement skills** to prevent AI-assisted development from contradicting PRD decisions, architecture, and compliance requirements.

## Core Function

Generate or update enforcement skills (`.claude/skills/*/SKILL.md`) that encode project constraints into reusable Claude instructions. All output is in English.

## Input Structure

```json
{
  "mode": "full" | "update",
  "context_packet": { "identity": {...}, "regulatory": {...} },
  "requirements": { "functional_requirements": [...], "domain_rules": [...], ... },
  "architecture": { "stack": {...}, "pattern": "..." },
  "prd_version": "1.0"
}
```

## The Seven Skills

| Skill | File | Purpose |
|-------|------|---------|
| **project-guardian** | `.claude/skills/project-guardian/SKILL.md` | Primary PRD enforcer — mandatory pre-implementation checklist |
| **project-architecture** | `.claude/skills/project-architecture/SKILL.md` | Canonical stack, layer rules, architectural constraints |
| **project-domain-rules** | `.claude/skills/project-domain-rules/SKILL.md` | Domain invariants, ubiquitous language, state machines |
| **project-compliance** | `.claude/skills/project-compliance/SKILL.md` | Regulatory requirements, data handling, audit trails |
| **project-docs-stack** | `.claude/skills/project-docs-stack/SKILL.md` | Local documentation cache protocol (prevent repeated web searches) |
| **project-cicd** | `.claude/skills/project-cicd/SKILL.md` | Pipeline consistency, service job mapping, evolution triggers |
| **project-docs** | `.claude/skills/project-docs/SKILL.md` | Living `docs/` tree generation (CREATE mode: first run; UPDATE mode: refresh) |

## Quality Standards

- **Product-specific** — Reference actual RF-/DR- IDs, real stack versions
- **Actionable** — State exactly what to check and what to do on violation
- **Token-efficient** — Tables and bullets only
- **Versioned** — `prd_version` in YAML frontmatter
- **No placeholders** — Zero curly-brace syntax in output

## Mode: `full`

Generate all seven skills from scratch. Used when PRD and architecture are finalized.

## Mode: `update`

Update only affected skills. Logic:

- **functional_requirements / domain_rules changed** → update project-guardian, project-domain-rules, project-docs
- **architecture / stack changed** → update project-architecture, project-guardian, project-docs
- **compliance_requirements changed** → update project-compliance, project-guardian, project-docs
- **architecture pivot** → update project-architecture, project-guardian, project-docs-stack, project-cicd, project-docs

Process: Read existing skills, bump `prd_version` + `last_evolved`, append Evolution Log entry, update only affected sections.

## Critical Rules

1. **project-docs Safety** — Environment variables in `docs/local-setup.md` use `YOUR_SERVICE_KEY_HERE` syntax only; never write actual credentials.

2. **project-docs-stack Protocol** — Check `docs/stack/` local cache *before* any web search; save fetched documentation locally to prevent redundant searches.

3. **project-guardian Hard Blocks** — Features removed from PRD §2, unauthorized stack technologies, domain rule violations, and PII without encryption are all **blocked**.

4. **Language** — All output in English. Default unless user specifies otherwise in `context_packet.meta.language`.

5. **No Generic Templates** — Every skill references actual project IDs (RF-001, DR-001, ADR-001) and real stack versions. Never use placeholder syntax in final output.
