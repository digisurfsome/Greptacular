# Replit PRD Generator

A Claude skill for generating sequential, dependency-ordered PRD prompt sequences optimized for Replit Agent development.

## Why This Skill?

Traditional PRDs don't work well with AI coding agents. They're monolithic, lack dependency ordering, and assume human interpretation. This skill generates **phased prompt sequences** that:

- Establish context before building (Plan Mode → Build Mode)
- Order tasks by dependency (database schema before queries)
- Create testable checkpoints after each phase
- Protect existing functionality with explicit constraints

## Installation

### Claude Code (Local)

```bash
# Personal use
git clone https://github.com/YOUR_USERNAME/replit-prd-skill.git ~/.claude/skills/replit-prd

# Project use (committed to repo)
git clone https://github.com/YOUR_USERNAME/replit-prd-skill.git .claude/skills/replit-prd
```

### Claude.ai (Pro/Team)

Upload the skill folder to your Claude.ai account under Skills settings.

## Usage

The skill activates automatically when you mention:

- "build with Replit"
- "Replit Agent"
- "Replit PRD"
- "vibe coding"
- "create a PRD for Replit"

### Example

> "I want to build an audio library app with Replit Agent. Can you create a PRD?"

Claude will:

1. **Research** current Replit capabilities (mandatory web search)
2. **Clarify** your requirements and constraints
3. **Sequence** features by dependency order
4. **Deliver** Prompt 0 (Plan Mode) + Prompts 1-N (Build Mode)
5. **Adapt** if you return with changes mid-project

## Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Research   │ ──▶ │   Clarify   │ ──▶ │  Sequence   │
│  (search)   │     │  (gather)   │     │  (order)    │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
       ┌───────────────────────────────────────┘
       ▼
┌─────────────┐     ┌─────────────┐
│   Deliver   │ ──▶ │    Adapt    │
│  (prompts)  │     │  (changes)  │
└─────────────┘     └─────────────┘
```

## Key Principles

| Principle | Description |
|-----------|-------------|
| Research before recommending | Always search current Replit capabilities |
| Native over external | Prefer Replit Database and App Storage |
| Plan Mode first | Establish context before building |
| Sequence by dependency | Foundations before features |
| Testable phases | Each prompt ends with verifiable functionality |
| Checkpoint discipline | Recommend saves after each phase |

## Replit Agent Modes

**Plan Mode**: Discuss architecture without modifying code. No charges. Use for initial planning (Prompt 0).

**Build Mode**: Write and modify code. Creates automatic checkpoints. Use for implementation (Prompts 1-N).

## File Structure

```
replit-prd/
├── SKILL.md                 # Main skill instructions
├── references/
│   ├── research.md          # Pre-PRD research checklist
│   ├── templates.md         # Prompt structures and examples
│   └── adaptation.md        # Mid-project change patterns
├── marketplace.json         # SkillsMP metadata
├── README.md               
└── LICENSE                  
```

## Output Format

The skill generates copyable prompt blocks:

```markdown
## Prompt 1: Foundation

> **Use Build Mode**

[OBJECTIVE]
Set up project structure, database schema, and storage.

[REQUIREMENTS]
1. Initialize React + Vite frontend with Express backend
2. Configure Replit Database with Drizzle ORM
3. Create all database tables

[DO NOT CHANGE]
- (none for first prompt)

**Acceptance Criteria:**
- [ ] App runs without errors
- [ ] Database tables accessible
- [ ] Layout displays correctly

**Create checkpoint: "Foundation"**
```

## Background

This skill was developed based on research into agentic coding practices (June 2025 – January 2026) and documented in the article "[Product Specification as Source Code: A PM's Guide to Writing PRDs for AI Agentic Development](https://example.com/article)."

Key findings:
- Sequential, phased approaches outperform monolithic PRDs
- Research-before-specification prevents integration failures
- Testable checkpoints enable confident rollback
- Explicit protection patterns prevent AI scope creep

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Test with Claude Code or Claude.ai
4. Submit a pull request

## License

MIT License — see [LICENSE](LICENSE) for details.

## Author

Created by [haberlah](https://github.com/haberlah)

---

*Compatible with Claude Code, OpenAI Codex CLI, and other tools supporting the SKILL.md standard.*
