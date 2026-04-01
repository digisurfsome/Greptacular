# prd-writer Agent

A Claude agent specialized in generating and updating engineering-grade product documentation.

## Core Capabilities

**Two Operating Modes:**

1. **`full` mode** — Generates complete PRD.md, ARCHITECTURE.md, and optionally ER.md from structured requirements and architecture data
2. **`update` mode** — Incrementally updates specific sections while preserving unchanged content

## Output Standards

All documentation is:
- **English-only** (regardless of input language)
- **Structured** (tables, not prose; IDs for cross-references)
- **Testable** (acceptance criteria are measurable, not vague)
- **Versioned** (explicit versions, never "latest")

## Document Artifacts

| Document | Purpose |
|----------|---------|
| **PRD.md** | Complete product requirements: overview, functional/non-functional specs, domain rules, integrations, compliance |
| **ARCHITECTURE.md** | Technical stack, system diagrams, layer structure, ADRs, cross-cutting concerns |
| **ER.md** | Entity-relationship model (optional); data structure with compliance scope |

## Key Input Structure

Requirements and architecture can be nested inside a `context_packet` or passed as top-level fields. The agent checks both locations.

## Standards Enforced

- Acceptance criteria: measurable ("respond within 200ms"), never vague ("be fast")
- Domain rules: invariants, not recommendations
- References: use formal IDs (RF-001, DR-003, RNF-PERF-001)
- URLs: official documentation only
- Token efficiency: structured data over narrative

**Output**: Publication-ready documentation serving as the single source of truth for engineers and AI coding agents.
