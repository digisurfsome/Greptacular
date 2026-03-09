# Claude SDK Boilerplates & Starter Templates

A curated list of public GitHub repos for building **local software** with the Anthropic Claude SDK. Organized by license — MIT-licensed repos listed first.

---

## MIT Licensed

### 1. anthropics/claude-quickstarts
- **URL:** https://github.com/anthropics/claude-quickstarts
- **Stars:** ~15,200
- **What it is:** Official Anthropic collection of starter projects for the Claude API
- **Includes:** Customer support agent, financial data analyst, computer use demo, autonomous coding agent (two-agent pattern)
- **Language:** Python, TypeScript
- **License:** MIT
- **Best for:** Getting started with Claude API apps — official and well-maintained

### 2. anthropics/claude-agent-sdk-demos
- **URL:** https://github.com/anthropics/claude-agent-sdk-demos
- **Stars:** ~1,600
- **What it is:** Official demo apps — hello-world, multi-agent research system (researchers + data analysts + report writers), spreadsheet demos
- **Language:** Python, TypeScript
- **License:** MIT
- **Best for:** Seeing real-world Agent SDK patterns before building your own

### 3. anthropics/anthropic-sdk-python
- **URL:** https://github.com/anthropics/anthropic-sdk-python
- **What it is:** Official Python SDK with built-in usage examples
- **Language:** Python
- **License:** MIT
- **Best for:** Python developers who want the core SDK with examples to build on

### 4. anthropics/claude-agent-sdk-python
- **URL:** https://github.com/anthropics/claude-agent-sdk-python
- **Stars:** ~704
- **What it is:** Official Python Agent SDK — build agents that edit files, run commands, use custom tools, and manage subagents. CLI bundled automatically.
- **Language:** Python
- **License:** MIT (with commercial ToS for products)
- **Best for:** Production agent development in Python — the core SDK

### 5. anthropics/claude-agent-sdk-typescript
- **URL:** https://github.com/anthropics/claude-agent-sdk-typescript
- **What it is:** Official TypeScript Agent SDK — same capabilities as Python version
- **Language:** TypeScript
- **License:** MIT (with commercial ToS for products)
- **Best for:** Node.js/TypeScript agent development

### 6. serpro69/claude-starter-kit
- **URL:** https://github.com/serpro69/claude-starter-kit
- **What it is:** Template repo with pre-configured MCP servers, skills, sub-agents, commands, and hooks
- **Language:** Markdown, Config files
- **License:** MIT
- **Best for:** Teams wanting a ready-to-go Claude Code dev environment they can share via git

### 7. davila7/claude-code-templates
- **URL:** https://github.com/davila7/claude-code-templates
- **What it is:** CLI tool + interactive web UI with 600+ agents, 200+ commands, 55+ MCPs, 60+ settings, 39+ hooks, and 14+ project templates
- **Language:** TypeScript
- **License:** MIT (individual components retain their original licenses)
- **Best for:** Browsing and installing ready-made Claude Code configurations — like a package manager for Claude Code

### 8. KunihiroS/claude-code-mcp
- **URL:** https://github.com/KunihiroS/claude-code-mcp
- **What it is:** MCP server that connects with Claude Code's local CLI — lets less capable LLMs use Claude's power through MCP
- **Language:** TypeScript (Node.js)
- **License:** MIT
- **Best for:** Building MCP server integrations that bridge Claude Code with other tools

### 9. kenneth-liao/claude-agent-sdk-intro
- **URL:** https://github.com/kenneth-liao/claude-agent-sdk-intro
- **What it is:** Tutorial repo teaching `query()` vs `ClaudeSDKClient`, custom tools, MCP servers, and multi-agent systems
- **Language:** Python
- **License:** MIT (check repo)
- **Best for:** Learning the Agent SDK step-by-step — great for beginners

---

## Unlicense / MIT Fallback

### 10. AndrewAltimit/template-repo
- **URL:** https://github.com/AndrewAltimit/template-repo
- **What it is:** Agent orchestration & security template with MCP tool building, agent-to-agent workflows, and multi-AI council (Claude, Gemini, Codex, OpenCode)
- **Language:** Python, TypeScript
- **License:** Unlicense (public domain) with MIT fallback
- **Best for:** Advanced users wanting multi-agent orchestration across different AI providers

---

## Community Desktop Apps & CLI Tools

### 11. Doriandarko/claude-engineer
- **URL:** https://github.com/Doriandarko/claude-engineer
- **Stars:** ~11,200
- **What it is:** Interactive CLI tool using the `anthropic` Python SDK. Claude can dynamically create and manage its own tools during conversation. Available as both CLI and web interface.
- **Language:** Python
- **License:** Check repo
- **Best for:** A full local agent framework — most popular community CLI agent

### 12. pheuter/claude-agent-desktop
- **URL:** https://github.com/pheuter/claude-agent-desktop
- **What it is:** Cross-platform desktop app (Electron) wrapping the Claude Agent SDK. Bundles Node, Python, Git, and bash tools so non-developers can use Claude as a local agent.
- **Language:** TypeScript (Electron)
- **License:** Check repo
- **Best for:** Using Claude Agent without a terminal — pre-built binaries for macOS and Windows

### 13. Fergana-Labs/claude_agent_desktop
- **URL:** https://github.com/Fergana-Labs/claude_agent_desktop
- **What it is:** Desktop GUI (Electron + React) for the Claude Agent SDK. API key stored locally. Includes additional Claude Skills.
- **Language:** TypeScript (Electron + React)
- **License:** Check repo
- **Best for:** GUI-based agent usage without installing Claude Code CLI

### 14. op7418/CodePilot
- **URL:** https://github.com/op7418/CodePilot
- **What it is:** Desktop GUI client for Claude Code built with Electron + Next.js. Supports multiple providers (Anthropic, OpenRouter, Bedrock, Vertex). Switch models mid-conversation.
- **Language:** TypeScript (Electron + Next.js)
- **License:** Check repo
- **Best for:** Visual project management with multi-provider support

### 15. baryhuang/claude-code-by-agents
- **URL:** https://github.com/baryhuang/claude-code-by-agents
- **What it is:** Desktop app + API for multi-agent Claude Code orchestration — coordinate local and remote agents through @mentions
- **Language:** TypeScript
- **License:** Check repo
- **Best for:** Running multiple Claude agents across different machines (no API key needed — uses your Claude subscription)

### 16. severity1/claude-agent-sdk-go
- **URL:** https://github.com/severity1/claude-agent-sdk-go
- **What it is:** Unofficial Go SDK for Claude Code CLI integration. Idiomatic Go API for file operations, shell commands, and tool integrations.
- **Language:** Go
- **License:** Check repo
- **Best for:** Go developers who want to build Claude agents natively

---

## Configuration & Project Starters

### 17. zbruhnke/claude-code-starter
- **URL:** https://github.com/zbruhnke/claude-code-starter
- **What it is:** Production-ready Claude Code configuration template with stack-specific presets (TypeScript, Python, Go, Rust, Ruby, Elixir), security defaults, custom skills, and specialized agents
- **Language:** Config/Markdown
- **License:** Check repo
- **Best for:** Quick project setup with your specific tech stack

### 18. TheDecipherist/claude-code-mastery-project-starter-kit
- **URL:** https://github.com/TheDecipherist/claude-code-mastery-project-starter-kit
- **What it is:** Scaffold template with commands, hooks, skills, agents, and documentation templates. Supports Classic and MDD (Document-Test-Code) workflows.
- **Language:** Config/Markdown
- **License:** Check repo
- **Best for:** Structured development workflows with Claude Code

### 19. halans/cc-marketplace-boilerplate
- **URL:** https://github.com/halans/cc-marketplace-boilerplate
- **What it is:** Minimal boilerplate for creating Claude Code marketplace plugins. Foundation for custom commands, agents, and hooks.
- **Language:** Config/Markdown
- **License:** Check repo
- **Best for:** Publishing your own Claude Code plugins

### 20. shinpr/ai-coding-project-boilerplate
- **URL:** https://github.com/shinpr/ai-coding-project-boilerplate
- **What it is:** TypeScript boilerplate optimized for Claude Code with sub-agent setup. Maximizes AI coding productivity.
- **Language:** TypeScript
- **License:** Check repo
- **Best for:** TypeScript projects with AI-first development

### 21. wshobson/agents
- **URL:** https://github.com/wshobson/agents
- **What it is:** Production-ready system with 112 specialized AI agents, 16 multi-agent workflow orchestrators, 146 skills, and 79 dev tools organized into 72 plugins
- **Language:** Config/Markdown
- **License:** Check repo
- **Best for:** Enterprise-scale agent configurations

---

## Subagent & Plugin Collections

### 22. VoltAgent/awesome-claude-code-subagents
- **URL:** https://github.com/VoltAgent/awesome-claude-code-subagents
- **What it is:** Collection of 100+ specialized subagent configs — read-only agents, research agents, code writers, documentation agents
- **Language:** Markdown, Config
- **License:** Check repo
- **Best for:** Copy-paste subagent definitions into your own projects

---

## MCP Server Templates

### 23. GenesisClawbot/mcp-server-starter
- **URL:** https://github.com/GenesisClawbot/mcp-server-starter
- **What it is:** 8 starter templates for MCP servers (GitHub integration, SQLite queries, etc.)
- **Language:** TypeScript
- **License:** Check repo
- **Best for:** Quickly building custom MCP tool servers without boilerplate hassle

### 24. punkpeye/awesome-mcp-servers
- **URL:** https://github.com/punkpeye/awesome-mcp-servers
- **What it is:** Large curated list of community MCP servers across many domains
- **Language:** Various
- **License:** Various
- **Best for:** Finding existing MCP servers to use or reference when building your own

---

## Curated Lists (Find More Here)

### 25. hesreallyhim/awesome-claude-code
- **URL:** https://github.com/hesreallyhim/awesome-claude-code
- **What it is:** Curated list of skills, hooks, slash-commands, agent orchestrators, apps, and plugins for Claude Code
- **Best for:** Discovering new Claude Code tools and integrations — regularly updated

---

## Quick Recommendation

| Goal | Start Here |
|---|---|
| Build a Claude API app fast | [claude-quickstarts](https://github.com/anthropics/claude-quickstarts) (MIT, ~15k stars) |
| See Agent SDK demos | [claude-agent-sdk-demos](https://github.com/anthropics/claude-agent-sdk-demos) (MIT, ~1.6k stars) |
| Set up Claude Code for your team | [claude-starter-kit](https://github.com/serpro69/claude-starter-kit) (MIT) |
| Browse 600+ ready-made configs | [claude-code-templates](https://github.com/davila7/claude-code-templates) (MIT) |
| Learn the Agent SDK | [claude-agent-sdk-intro](https://github.com/kenneth-liao/claude-agent-sdk-intro) |
| Build production agents (Python) | [claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python) (MIT) |
| Build production agents (TypeScript) | [claude-agent-sdk-typescript](https://github.com/anthropics/claude-agent-sdk-typescript) (MIT) |
| Desktop app (no terminal) | [claude-agent-desktop](https://github.com/pheuter/claude-agent-desktop) |
| Community CLI agent | [claude-engineer](https://github.com/Doriandarko/claude-engineer) (~11k stars) |
| Build custom MCP tools | [claude-code-mcp](https://github.com/KunihiroS/claude-code-mcp) (MIT) |
| Multi-provider support | [CodePilot](https://github.com/op7418/CodePilot) |

*Last updated: March 2026*
