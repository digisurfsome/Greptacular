# Claude SDK Boilerplates & Starter Templates

A curated list of public GitHub repos for building **local software** with the Anthropic Claude SDK. Organized by license — MIT-licensed repos listed first.

---

## MIT Licensed

### 1. anthropics/claude-quickstarts
- **URL:** https://github.com/anthropics/claude-quickstarts
- **What it is:** Official Anthropic collection of starter projects for the Claude API
- **Includes:** Customer support agent, financial data analyst, computer use demo, autonomous coding agent (two-agent pattern)
- **Language:** Python, TypeScript
- **License:** MIT
- **Best for:** Getting started with Claude API apps — official and well-maintained

### 2. anthropics/anthropic-sdk-python
- **URL:** https://github.com/anthropics/anthropic-sdk-python
- **What it is:** Official Python SDK with built-in usage examples
- **Language:** Python
- **License:** MIT
- **Best for:** Python developers who want the core SDK with examples to build on

### 3. serpro69/claude-starter-kit
- **URL:** https://github.com/serpro69/claude-starter-kit
- **What it is:** Template repo with pre-configured MCP servers, skills, sub-agents, commands, and hooks
- **Language:** Markdown, Config files
- **License:** MIT
- **Best for:** Teams wanting a ready-to-go Claude Code dev environment they can share via git

### 4. davila7/claude-code-templates
- **URL:** https://github.com/davila7/claude-code-templates
- **What it is:** CLI tool + interactive web UI with 600+ agents, 200+ commands, 55+ MCPs, 60+ settings, 39+ hooks, and 14+ project templates
- **Language:** TypeScript
- **License:** MIT (individual components retain their original licenses)
- **Best for:** Browsing and installing ready-made Claude Code configurations — like a package manager for Claude Code

### 5. KunihiroS/claude-code-mcp
- **URL:** https://github.com/KunihiroS/claude-code-mcp
- **What it is:** MCP server that connects with Claude Code's local CLI — lets less capable LLMs use Claude's power through MCP
- **Language:** TypeScript (Node.js)
- **License:** MIT
- **Best for:** Building MCP server integrations that bridge Claude Code with other tools

### 6. kenneth-liao/claude-agent-sdk-intro
- **URL:** https://github.com/kenneth-liao/claude-agent-sdk-intro
- **What it is:** Tutorial repo teaching `query()` vs `ClaudeSDKClient`, custom tools, MCP servers, and multi-agent systems
- **Language:** Python
- **License:** MIT (check repo)
- **Best for:** Learning the Agent SDK step-by-step — great for beginners

---

## Unlicense / MIT Fallback

### 7. AndrewAltimit/template-repo
- **URL:** https://github.com/AndrewAltimit/template-repo
- **What it is:** Agent orchestration & security template with MCP tool building, agent-to-agent workflows, and multi-AI council (Claude, Gemini, Codex, OpenCode)
- **Language:** Python, TypeScript
- **License:** Unlicense (public domain) with MIT fallback
- **Best for:** Advanced users wanting multi-agent orchestration across different AI providers

---

## Anthropic Commercial License

### 8. anthropics/claude-agent-sdk-python
- **URL:** https://github.com/anthropics/claude-agent-sdk-python
- **What it is:** Official Python Agent SDK — build agents that edit files, run commands, use custom tools, and manage subagents
- **Language:** Python
- **License:** Anthropic Commercial Terms
- **Best for:** Production agent development in Python — the core SDK

### 9. anthropics/claude-agent-sdk-typescript
- **URL:** https://github.com/anthropics/claude-agent-sdk-typescript
- **What it is:** Official TypeScript Agent SDK — same capabilities as Python version
- **Language:** TypeScript
- **License:** Anthropic Commercial Terms
- **Best for:** Node.js/TypeScript agent development

### 10. anthropics/claude-agent-sdk-demos
- **URL:** https://github.com/anthropics/claude-agent-sdk-demos
- **What it is:** Multiple demo projects showcasing different Agent SDK patterns
- **Language:** Python, TypeScript
- **License:** Anthropic Commercial Terms
- **Best for:** Seeing real-world Agent SDK usage patterns before building your own

---

## Community Tools & Multi-Agent Systems

### 11. baryhuang/claude-code-by-agents
- **URL:** https://github.com/baryhuang/claude-code-by-agents
- **What it is:** Desktop app + API for multi-agent Claude Code orchestration — coordinate local and remote agents through @mentions
- **Language:** TypeScript
- **License:** Check repo
- **Best for:** Running multiple Claude agents across different machines (no API key needed — uses your Claude subscription)

### 12. VoltAgent/awesome-claude-code-subagents
- **URL:** https://github.com/VoltAgent/awesome-claude-code-subagents
- **What it is:** Collection of 100+ specialized subagent configs — read-only agents, research agents, code writers, documentation agents
- **Language:** Markdown, Config
- **License:** Check repo
- **Best for:** Copy-paste subagent definitions into your own projects

---

## MCP Server Templates

### 13. GenesisClawbot/mcp-server-starter
- **URL:** https://github.com/GenesisClawbot/mcp-server-starter
- **What it is:** 8 starter templates for MCP servers (GitHub integration, SQLite queries, etc.)
- **Language:** TypeScript
- **License:** Check repo
- **Best for:** Quickly building custom MCP tool servers without boilerplate hassle

### 14. punkpeye/awesome-mcp-servers
- **URL:** https://github.com/punkpeye/awesome-mcp-servers
- **What it is:** Large curated list of community MCP servers across many domains
- **Language:** Various
- **License:** Various
- **Best for:** Finding existing MCP servers to use or reference when building your own

---

## Curated Lists (Find More Here)

### 15. hesreallyhim/awesome-claude-code
- **URL:** https://github.com/hesreallyhim/awesome-claude-code
- **What it is:** Curated list of skills, hooks, slash-commands, agent orchestrators, apps, and plugins for Claude Code
- **Best for:** Discovering new Claude Code tools and integrations — regularly updated

---

## Quick Recommendation

| Goal | Start Here |
|---|---|
| Build a Claude API app fast | [claude-quickstarts](https://github.com/anthropics/claude-quickstarts) (MIT) |
| Set up Claude Code for your team | [claude-starter-kit](https://github.com/serpro69/claude-starter-kit) (MIT) |
| Browse 600+ ready-made configs | [claude-code-templates](https://github.com/davila7/claude-code-templates) (MIT) |
| Learn the Agent SDK | [claude-agent-sdk-intro](https://github.com/kenneth-liao/claude-agent-sdk-intro) |
| Build production agents (Python) | [claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python) |
| Build production agents (TypeScript) | [claude-agent-sdk-typescript](https://github.com/anthropics/claude-agent-sdk-typescript) |
| Build custom MCP tools | [claude-code-mcp](https://github.com/KunihiroS/claude-code-mcp) (MIT) |

*Last updated: March 2026*
