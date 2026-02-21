# Coding Structure Reference

This directory contains the controlling documents from two production applications, collected for analysis and comparison to build a standardized coding protocol.

## Purpose

These documents represent the coding structures and AI agent governance from two experienced developers:

1. **Leon (AutoForge)** - An autonomous coding agent factory with a React UI. Complex multi-agent system with sophisticated governance.
2. **Martin (VidAi)** - A text-to-video SaaS application. Clean, production-ready boilerplate with practical AI rules.

The goal is to extract the best practices from both and merge them into a universal coding standard that can be applied to any new application.

## Directory Structure

```
coding-structure-reference/
├── README.md                    # This file
├── COMPARISON.md                # Side-by-side analysis of both approaches
├── autoforge/                   # Leon's AutoForge documents
│   ├── 01-CLAUDE.md             # Master project reference (architecture, stack, patterns)
│   ├── 02-coder-agent.md        # Coder agent persona and 3-phase workflow
│   └── 03-coding-prompt-template.md  # Operational instructions for coding sessions
└── vidai/                       # Martin's VidAi documents
    ├── 01-CLAUDE.md             # Architecture reference (auth, layouts, DB, Stripe)
    └── 02-AI_RULES.md           # Concise tech stack and AI behavior rules
```

## Document Hierarchy

### AutoForge (3 Main Documents)
| Doc | Purpose | Controls |
|-----|---------|----------|
| CLAUDE.md | Master reference | Architecture, tech stack, security, patterns |
| coder.md | Agent persona | WHO the agent is, HOW it works (Research > Implement > Verify) |
| coding_prompt.template.md | Session instructions | WHAT to do each session (9 steps, 15 coding rules, 50+ checks) |

### VidAi (2 Main Documents)
| Doc | Purpose | Controls |
|-----|---------|----------|
| CLAUDE.md | Architecture reference | Full system architecture, auth, DB, Stripe, email, admin |
| AI_RULES.md | AI coding rules | Tech stack, file organization, styling, quality standards |

## Key Insight

Leon's approach is **deeply layered** (identity > principles > procedures) designed for autonomous multi-agent orchestration. Martin's approach is **lean and direct**, designed for interactive AI-assisted development. Both produce high-quality production code - the difference is in the level of autonomous governance needed.

## Next Steps

These documents will be combined with additional build prompts to create a universal standardized coding protocol.
