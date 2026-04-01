# PRD Maker — 10-Step Build Plans

> A 10-stage pipeline that takes a raw app idea (rant, transcript, notes) and produces a complete, phased, buildable technical spec.

## Pipeline Overview

| Stage | Name | What It Does |
|-------|------|-------------|
| 1 | **Idea Capture** | Raw rant/description → structured concept document |
| 2 | **Gap Analysis** | Structured concept → filled gaps via intelligent questions |
| 3 | **Agent OS Structuring** | Raw organized info → standardized format for pipeline |
| 4 | **Mechanism Extraction** | Structured app description → discrete moving parts/mechanisms |
| 5 | **7-Question Scaffolding** | Mechanisms → Wall/Door/Room classification using 7 questions |
| 6 | **Layout + Mockups + Style** | Classified mechanisms → visual structure (pages, navigation, style) |
| 7 | **Phase Sequencing** | Complete spec → math-based phase split with file sandboxes and build order |
| 8 | **Protocol Injection** | Phases → checkpoints (pulse/seam/full) and violation handling |
| 9 | **Verification Agent Setup** | Protocols → independent checker with decision authority |
| 10 | **Output Generator** | Everything → phase files + bash script + CLAUDE.md + BUILD_RULES.md |

## Core IP: Wall/Door/Room Classification

- **WALL** — Deterministic, must happen exactly one way, enforced by code
- **DOOR** — Constrained choice, AI can operate but within strict boundaries
- **ROOM** — Creative freedom, AI can be flexible

## The 7 Questions (Stage 5 Engine)

Applied to every mechanism:
1. What happens here?
2. Is there only one way to do this, or can it vary?
3. What must be true before this step can start?
4. What are all possible outcomes?
5. For each outcome, where do you go next?
6. How do you verify this step was done correctly?
7. Can this step be skipped?

## Files in This Folder

| File | Description |
|------|-------------|
| `README.md` | This file — pipeline overview |
| `research-reference.md` | Full research notes, source inventory, skill mapping, and build plan |
| `extract-stages.sh` | Bash script that extracts stage info from master-source.md using Claude |
| `stage-extractions/` | 10 individual stage dossiers (one per pipeline stage) |

### Stage Extractions

Each file in `stage-extractions/` is a detailed dossier covering one stage:

- `stage-01-extraction.md` — Idea Capture
- `stage-02-extraction.md` — Gap Analysis
- `stage-03-extraction.md` — Agent OS Structuring
- `stage-04-extraction.md` — Mechanism Extraction
- `stage-05-extraction.md` — 7-Question Scaffolding (Wall/Door/Room)
- `stage-06-extraction.md` — Layout + Mockups + Style
- `stage-07-extraction.md` — Phase Sequencing
- `stage-08-extraction.md` — Protocol Injection
- `stage-09-extraction.md` — Verification Agent Setup
- `stage-10-extraction.md` — Output Generator

Each dossier includes: Purpose, Inputs, Process, Outputs, Rules & Constraints, Examples, Edge Cases & Debates, and Connections to Other Stages.

## Source

Original docs: [digisurfsome/Vid-Gen-OG/docs](https://github.com/digisurfsome/Vid-Gen-OG/tree/main/docs)
