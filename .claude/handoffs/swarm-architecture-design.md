# Swarm Architecture Design

## Overview
A hierarchical multi-agent system where a Commander orchestrates Managers, who each manage teams of Sub-Agents. All communication happens through the file system — no API calls between agents. Each agent uses Claude Code skills for specialization.

## Hierarchy
```
COMMANDER (1 agent — human or AI)
├── MANAGER 1: App Build (1 agent)
│   ├── Sub-Agent: Scaffolding/boilerplate
│   ├── Sub-Agent: Feature coding
│   ├── Sub-Agent: Testing (Playwright)
│   ├── Sub-Agent: Bug fixing
│   └── Sub-Agent: Code review
├── MANAGER 2: Documentation (1 agent)
│   ├── Sub-Agent: Knowledge base
│   ├── Sub-Agent: User manual
│   ├── Sub-Agent: Tutorial pages
│   └── Sub-Agent: API docs
├── MANAGER 3: Marketing (1 agent)
│   ├── Sub-Agent: Landing page
│   ├── Sub-Agent: Screenshot GIFs
│   ├── Sub-Agent: Sales copy
│   └── Sub-Agent: Social media posts
├── MANAGER 4: Video (1 agent)
│   ├── Sub-Agent: Script writing
│   ├── Sub-Agent: Screen recording
│   ├── Sub-Agent: Editing/compilation
│   └── Sub-Agent: Distribution
└── MANAGER 5: Launch Ops (1 agent)
    ├── Sub-Agent: SEO
    ├── Sub-Agent: Analytics
    └── Sub-Agent: Deployment
```

## File System Communication Protocol

```
.autoforge/swarm/
├── commander.md                 ← Master plan + current global status
├── inbox/                       ← Messages TO the commander
│   ├── manager-app-build.md     ← Status updates from each manager
│   ├── manager-docs.md
│   └── ...
├── managers/
│   ├── app-build/
│   │   ├── plan.md              ← Manager's plan for the team
│   │   ├── status.md            ← Current progress
│   │   ├── tasks/
│   │   │   ├── task-001-scaffold.md    ← Task assignment
│   │   │   ├── task-002-auth.md
│   │   │   └── ...
│   │   ├── results/
│   │   │   ├── task-001-done.md        ← Completed work
│   │   │   └── ...
│   │   └── agents/
│   │       ├── agent-scaffold/
│   │       │   ├── inbox.md            ← Messages TO this agent
│   │       │   └── outbox.md           ← Messages FROM this agent
│   │       └── ...
│   ├── documentation/
│   │   └── (same structure)
│   └── ...
├── shared/                      ← Cross-team knowledge (everyone reads)
│   ├── app-spec.md
│   ├── brand-guide.md
│   ├── feature-list.md
│   └── architecture-decisions.md
└── walkie-talkie/               ← Human can message ANY agent directly
    ├── to-agent-scaffold.md     ← Human → specific agent
    └── from-agent-scaffold.md   ← Agent → human
```

## Communication Rules
1. Agents READ their inbox file every tool call (polling)
2. Agents WRITE to their outbox when they have updates
3. Managers READ all agent outboxes + commander inbox
4. Commander READS all manager inboxes
5. Human can WRITE to any agent's inbox directly (walkie-talkie)
6. Shared folder is READ-ONLY for all agents, WRITE for commander only

## Token Economics
- Each sub-agent: ~50K-150K tokens per task (small, focused work)
- Each manager: ~100K-200K tokens (coordination + quality review)
- Commander: ~200K-400K tokens (orchestration + human communication)
- Total for full 25-agent pipeline: ~2-5M tokens
- With walkie-talkie savings: ~30-50% reduction
- Within 5-hour rate limit window: YES, if agents are small and focused

## What Needs Building
1. **Programmatic agent launcher** — Commander can start new Workspace chats via API (4/10)
2. **File polling protocol** — Standard inbox/outbox check every tool call (2/10)
3. **Swarm dashboard UI** — Tree visualization showing all agents, click to walkie-talkie (5/10)
4. **Claude Code skills per role** — One skill file per agent type (3/10)
5. **Status aggregation** — Commander sees all agents' progress in one view (3/10)

## First Test: 2-Manager, 6-Agent Swarm
- Commander: Human (you)
- Manager 1: App coding (3 sub-agents)
- Manager 2: Documentation (3 sub-agents)
- Shared: One app spec
- Goal: Build a simple app with full docs in one session
- Proof: All 6 agents complete independently, docs reference actual app features

## Why This Works
- File system = zero-cost communication (no API tokens for coordination)
- Claude Code skills = deterministic specialization (each agent does one thing well)
- Walkie-talkie = human can intervene at any level without burning tokens
- Session chaining = agents can be replaced/restarted without losing context
- Rate limits = distributed across small agents, not one huge context window
