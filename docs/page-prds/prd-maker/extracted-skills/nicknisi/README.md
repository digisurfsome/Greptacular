# nicknisi/claude-plugins -- Ideation Plugin

> Source: https://github.com/nicknisi/claude-plugins
> Extracted: 2026-04-01

## Overview

A Claude Code plugin marketplace containing multiple plugins. The **ideation** plugin transforms unstructured brain dumps into actionable implementation artifacts through a confidence-gated workflow, producing contracts, phased PRDs, and implementation specs with built-in feedback loops.

## Installation

```bash
/plugin marketplace add nicknisi/claude-plugins
/plugin install ideation@nicknisi
```

## Ideation Plugin Structure

```
plugins/ideation/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   ├── reviewer.md
│   └── scout.md
├── skills/
│   ├── execute-spec/
│   │   └── SKILL.md
│   └── ideation/
│       ├── SKILL.md
│       ├── examples/
│       │   ├── contract-example.md
│       │   ├── prd-example.md
│       │   └── spec-example.md
│       └── references/
│           ├── confidence-rubric.md
│           ├── contract-template.md
│           ├── feedback-loop-guide.md
│           ├── prd-template.md
│           ├── spec-template.md
│           └── workflow-example.md
└── README.md
```

## Core Skills

### ideation

Primary skill for converting brain dumps into structured specs. 8-step workflow:

1. **Intake** -- Accept unstructured input without judgment
2. **Anti-sycophancy challenge** -- Contest vague claims; flag undefined terms
3. **Codebase exploration** -- Map existing patterns and conventions
4. **Confidence scoring** -- 5 dimensions (0-100), conservative scoring
5. **Clarifying questions** -- Deploy if confidence < 95%
6. **Contract** -- Generate with Supersedes lineage tracking
7. **Phasing and specs** -- Determine phases; include failure mode catalogs and feedback loops
8. **Execution handoff** -- Write execution plan; present summary

### ideation:execute-spec

Manages implementation execution with:
- Scout agents for codebase exploration
- Per-component feedback loops
- Spec-aware Verify-Review-Fix cycles
- Up to 3 review cycles before escalation

## Agents

### scout

Read-only codebase explorer that produces context maps. Scores confidence across 5 dimensions (scope clarity, pattern familiarity, dependency awareness, edge case coverage, test strategy). GO verdict at >= 70%, HOLD below.

### reviewer

Spec-aware code reviewer comparing diffs against specifications. Produces structured findings with severities (critical/high/medium/low) and categories (spec-deviation, pattern-mismatch, logic, security, performance, testing). PASS = zero critical + zero high.

## Anti-Sycophancy Rules

**Banned phrases:** "That's an interesting approach," "There are many ways to think about this," "That could work"

**Required behaviors:** Take direct positions, challenge weak premises, name undefined concepts, flag hypothetical users, score conservatively when pushback reveals gaps.

## Confidence Scoring (5 x 20 = 100)

| Dimension | Question |
|-----------|----------|
| Problem Clarity | Do I understand what problem we're solving? |
| Goal Definition | Are goals specific and measurable? |
| Success Criteria | Can I write tests for "done"? |
| Scope Boundaries | What's in and out of scope? |
| Consistency | Any contradictions to resolve? |

Thresholds: <70 = major gaps, 70-84 = moderate, 85-94 = minor, >= 95 = ready for contract

## Output Artifacts

Located in `./docs/ideation/{project-name}/`:
- `contract.md` -- Problem, goals, success criteria, scope, execution plan
- `prd-phase-N.md` -- Phase requirements (optional)
- `spec-phase-N.md` -- Implementation specs with failure modes and feedback loops
- `spec-template-{pattern}.md` -- Reusable templates for repeatable patterns

## Other Plugins in Marketplace

consultant, content, developer-experience, essentials, meta, sandbox, spec-driven, workos

## Version

0.10.0

## License

MIT
