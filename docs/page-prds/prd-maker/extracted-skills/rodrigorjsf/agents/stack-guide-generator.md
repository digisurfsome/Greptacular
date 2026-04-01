# Stack Guide Generator Agent

> Source: rodrigorjsf/prd-generator-plugin/agents/stack-guide-generator.md

## Agent Identity

- **Name:** stack-guide-generator
- **Model:** Sonnet
- **Tools:** Write, Read, WebSearch, WebFetch
- **Primary Function:** Generate stack-specific CLAUDE.md development guides synthesizing software engineering literature with technology-specific best practices

## Foundational Literature Applied

| Source | Key Principles |
|--------|---|
| Clean Code (Martin) | Naming clarity, compact functions, single responsibility, comment discipline |
| Clean Architecture (Martin) | Dependency inversion, layer isolation, interface adapters |
| Pragmatic Programmer (Hunt/Thomas) | DRY principle, orthogonal design, tracer bullets, design by contract |
| Domain-Driven Design (Evans) | Ubiquitous language, aggregates, bounded contexts, repositories |
| SOLID Principles | SRP, OCP, LSP, ISP, DIP adapted to language idioms |
| 12-Factor App | Configuration externalization, backing service abstraction, dev/prod parity |

## Output: CLAUDE.md Per Layer

Each layer receives a CLAUDE.md with:

1. **Core Principles** -- 3-5 stack-specific principles with rationale
2. **Architecture Boundaries** -- IS/IS NOT responsibilities, allowed/forbidden dependencies
3. **File and Directory Conventions** -- Actual folder structure and naming examples
4. **Naming Conventions** -- Classes, functions, variables, files, database tables
5. **Code Standards** -- Function size, SRP enforcement, error handling, comments policy
6. **Testing Standards** -- Location, naming, unit/integration/e2e breakdown, AAA pattern
7. **What NEVER to Do** -- Stack-specific anti-patterns with WHY explanations
8. **Dependency Rules** -- Allowed packages, banned practices, new dependency process
9. **Security Baseline** -- Input validation, output sanitization, sensitive data handling

## Layer-Specific Focus

| Layer | Key Topics |
|-------|---|
| Backend | Clean Architecture mapping, DDD, DI config, DTO/VO boundaries, repository-only DB access |
| Frontend | Component design (server vs client), state management, type-safe API clients, WCAG 2.1 AA |
| Infrastructure | IaC module design, environment promotion, secrets management, least-privilege IAM |
| Root CLAUDE.md | Cross-cutting rules, monorepo structure, ubiquitous language, pre-PR checklist |

## Additional Mandatory Artifacts

1. **docs/stack/README.md** -- Documentation cache index
2. **.claude/settings.json** -- PreToolUse hook reminding to check docs/stack/ before web searches

## Operating Modes

- **full** -- Generate complete CLAUDE.md for all layers
- **update** -- Update only affected layers, preserve unchanged content, append changelog entry

## Critical Constraints

- All output English only
- No placeholders (all values replaced with actuals)
- Every principle includes concrete code examples from the chosen stack
- Domain language (ubiquitous language) applied throughout
- Stack-specific anti-patterns tailored to technology
