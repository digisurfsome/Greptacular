# Claude SDK Boilerplates & Starter Templates

A curated list of public GitHub repos for building **local software** with the Anthropic Claude SDK. Organized by license — MIT-licensed repos listed first.

**Total: 40+ repos** across official starters, desktop apps, CLI tools, MCP servers, chat apps, and config templates.

---

## MIT Licensed

### 1. anthropics/claude-quickstarts
- **URL:** https://github.com/anthropics/claude-quickstarts
- **Stars:** ~15,200
- **What it is:** Official Anthropic starter projects — customer support agent, financial data analyst, computer use demo, autonomous coding agent (two-agent pattern)
- **Language:** Python, TypeScript
- **Best for:** The single best official starting point for Claude API apps

### 2. anthropics/claude-agent-sdk-demos
- **URL:** https://github.com/anthropics/claude-agent-sdk-demos
- **Stars:** ~1,600
- **What it is:** Official demo apps — email agent, Excel demo, hello world, multi-agent research system with parallel subagents
- **Language:** TypeScript (88%), Python
- **Best for:** Seeing real Agent SDK patterns (multi-agent orchestration, tool use, file handling)

### 3. anthropics/anthropic-sdk-python
- **URL:** https://github.com/anthropics/anthropic-sdk-python
- **What it is:** Official Python SDK with built-in usage examples
- **Language:** Python
- **Best for:** Python developers who want the core SDK with examples to build on

### 4. anthropics/claude-agent-sdk-python
- **URL:** https://github.com/anthropics/claude-agent-sdk-python
- **Stars:** ~704
- **What it is:** Official Python Agent SDK — `query()` for one-off tasks, `ClaudeSDKClient` for conversations with custom tools/hooks. CLI bundled automatically.
- **Language:** Python
- **Best for:** Production agent development in Python

### 5. anthropics/claude-agent-sdk-typescript
- **URL:** https://github.com/anthropics/claude-agent-sdk-typescript
- **What it is:** Official TypeScript Agent SDK — autonomous agents that read codebases, edit files, run commands
- **Language:** TypeScript
- **Best for:** Node.js/TypeScript agent development

### 6. Doriandarko/claude-engineer
- **URL:** https://github.com/Doriandarko/claude-engineer
- **Stars:** ~11,200
- **What it is:** Interactive CLI agent that dynamically creates and manages its own tools during conversation. Available as CLI and web interface.
- **Language:** Python (92%)
- **Best for:** Most popular community CLI agent — self-improving tool generation

### 7. davila7/claude-code-templates
- **URL:** https://github.com/davila7/claude-code-templates
- **Stars:** ~22,600
- **What it is:** CLI tool + web UI (aitmpl.com) with 600+ agents, 200+ commands, 55+ MCPs, 60+ settings, 39+ hooks, 14+ project templates
- **Language:** Python (47%), TypeScript
- **Best for:** Package manager for Claude Code — browse and install ready-made configs

### 8. op7418/CodePilot
- **URL:** https://github.com/op7418/CodePilot
- **Stars:** ~3,400
- **What it is:** Desktop GUI for Claude Code (Electron + Next.js). Supports multiple providers (Anthropic, OpenRouter, Bedrock, Vertex). Run as browser app or full desktop app.
- **Language:** TypeScript (99%)
- **Best for:** Best Electron + Claude desktop starter — multi-provider support

### 9. serpro69/claude-starter-kit
- **URL:** https://github.com/serpro69/claude-starter-kit
- **What it is:** Minimal template with pre-configured MCP servers (Context7, Serena, Task Master), skills, sub-agents, hooks. Supports template sync.
- **Language:** Config (YAML/JSON/Shell)
- **Best for:** Clean, minimal starting point for teams — shareable via git

### 10. TheDecipherist/claude-code-mastery-project-starter-kit
- **URL:** https://github.com/TheDecipherist/claude-code-mastery-project-starter-kit
- **Stars:** ~226
- **What it is:** Scaffold with 27 slash commands, hooks, documentation templates, and two workflows (Classic and MDD Document-Test-Code)
- **Language:** TypeScript
- **Best for:** Structured development workflows with Claude Code

### 11. shinpr/ai-coding-project-boilerplate
- **URL:** https://github.com/shinpr/ai-coding-project-boilerplate
- **Stars:** ~184
- **What it is:** TypeScript boilerplate with specialized sub-agents, context engineering, and zero context exhaustion design
- **Language:** TypeScript
- **Best for:** TypeScript projects solving the context window management problem

### 12. KunihiroS/claude-code-mcp
- **URL:** https://github.com/KunihiroS/claude-code-mcp
- **What it is:** MCP server that connects with Claude Code's local CLI — lets less capable LLMs use Claude's power through MCP
- **Language:** TypeScript (Node.js)
- **Best for:** Building MCP server integrations bridging Claude Code with other tools

### 13. kenneth-liao/claude-agent-sdk-intro
- **URL:** https://github.com/kenneth-liao/claude-agent-sdk-intro
- **What it is:** Tutorial repo teaching `query()` vs `ClaudeSDKClient`, custom tools, MCP servers, conversation loops, and multi-agent systems
- **Language:** Python
- **Best for:** Learning the Agent SDK step-by-step — great for beginners

### 14. developersdigest/Anthropic-Claude-Clone-in-Next.JS-and-Langchain
- **URL:** https://github.com/developersdigest/Anthropic-Claude-Clone-in-Next.JS-and-Langchain
- **Stars:** ~108
- **What it is:** AI chat app with Next.js, LangChain, and Supabase for data storage
- **Language:** TypeScript (96%)
- **Best for:** Local-first chat apps with persistence (LangChain + Supabase pattern)

### 15. megmogmog1965/example-mcp-server
- **URL:** https://github.com/megmogmog1965/example-mcp-server
- **What it is:** Absolute minimum viable MCP server for Claude Desktop integration
- **Language:** JavaScript
- **Best for:** Understanding the MCP protocol without noise

### 16. jw782cn/Claude-Streamlit
- **URL:** https://github.com/jw782cn/Claude-Streamlit
- **What it is:** Simple Streamlit chatbot combining ChatGPT and Claude APIs
- **Language:** Python
- **Best for:** Local Claude chat UI running in 5 minutes

---

## Apache 2.0 Licensed

### 17. anthropics/skills
- **URL:** https://github.com/anthropics/skills
- **Stars:** ~88,200
- **What it is:** Official skill definitions with a `template-skill` you can copy. Covers creative/design, dev/technical, enterprise, and document creation.
- **Language:** Python (84%)
- **Best for:** Building your own Claude skills from the official template

### 18. Dev-GOM/claude-code-marketplace
- **URL:** https://github.com/Dev-GOM/claude-code-marketplace
- **Stars:** ~76
- **What it is:** 15 productivity plugins — auto git backups, TODO collection, code complexity monitoring, documentation generation, session tracking
- **Language:** JavaScript
- **Best for:** Small, self-contained plugin examples to study and build on

### 19. cyanheads/mcp-ts-template
- **URL:** https://github.com/cyanheads/mcp-ts-template
- **Stars:** ~118
- **What it is:** Feature-complete MCP server template with declarative tools, pluggable auth (none/JWT/OAuth), multi-backend storage, and OpenTelemetry observability
- **Language:** TypeScript
- **Best for:** Production-quality MCP servers with auth and monitoring built in

---

## Unlicense / MIT Fallback

### 20. AndrewAltimit/template-repo
- **URL:** https://github.com/AndrewAltimit/template-repo
- **What it is:** Agent orchestration & security template with MCP tools, agent-to-agent workflows, and multi-AI council (Claude, Gemini, Codex, OpenCode)
- **Language:** Python, TypeScript
- **Best for:** Multi-agent orchestration across different AI providers

---

## ISC Licensed

### 21. aashari/boilerplate-mcp-server
- **URL:** https://github.com/aashari/boilerplate-mcp-server
- **Stars:** ~69
- **What it is:** MCP server boilerplate with IP lookup example, CLI support, DNS rebinding protection, localhost-only binding
- **Language:** TypeScript
- **Best for:** Production-ready MCP servers with security measures built in

---

## GPL-3.0 Licensed

### 22. siteboon/claudecodeui (CloudCLI)
- **URL:** https://github.com/siteboon/claudecodeui
- **Stars:** ~8,100
- **What it is:** Web/mobile UI for managing Claude Code, Cursor CLI, Codex, and Gemini CLI sessions remotely. File explorer, Git integration, shell terminal, plugin system.
- **Language:** TypeScript (66%)
- **Best for:** Full-featured management interface for AI agents (note: GPL license)

---

## License Not Specified (Check Repos)

### 23. ChrisWiles/claude-code-showcase
- **URL:** https://github.com/ChrisWiles/claude-code-showcase
- **Stars:** ~5,500
- **What it is:** Comprehensive Claude Code config example with hooks, skills, agents, commands, and GitHub Actions workflows
- **Language:** JavaScript/TypeScript
- **Best for:** Best practices for structuring a Claude Code project

### 24. punkpeye/fastmcp
- **URL:** https://github.com/punkpeye/fastmcp
- **Stars:** ~3,000
- **What it is:** TypeScript framework for building MCP servers — the "Express.js of MCP servers." Supports OAuth, SSE, tool annotations, structured content.
- **Language:** TypeScript
- **Best for:** Fastest way to build production MCP servers in TypeScript

### 25. centminmod/my-claude-code-setup
- **URL:** https://github.com/centminmod/my-claude-code-setup
- **Stars:** ~2,000
- **What it is:** Starter template with CLAUDE.md memory bank system, MCP server integrations, and framework guides
- **Language:** Markdown/Config
- **Best for:** Persistent context across sessions (memory bank pattern)

### 26. jeremylongshore/claude-code-plugins-plus-skills
- **URL:** https://github.com/jeremylongshore/claude-code-plugins-plus-skills
- **Stars:** ~1,600
- **What it is:** 270+ plugins with 1,537 agent skills, production orchestration, 11 Jupyter notebook tutorials, CCPI package manager
- **Language:** JavaScript/TypeScript
- **Best for:** Both learning resource (notebooks) and practical toolkit (CCPI installer)

### 27. wshobson/agents
- **URL:** https://github.com/wshobson/agents
- **What it is:** 112 specialized AI agents, 16 multi-agent workflow orchestrators, 146 skills, 79 dev tools in 72 plugins
- **Language:** Config/Markdown
- **Best for:** Enterprise-scale agent configurations

### 28. pheuter/claude-agent-desktop
- **URL:** https://github.com/pheuter/claude-agent-desktop
- **What it is:** Cross-platform Electron desktop app wrapping the Agent SDK. Bundles Node, Python, Git, bash tools. Pre-built binaries for macOS/Windows.
- **Language:** TypeScript (Electron)
- **Best for:** Using Claude Agent without a terminal

### 29. Fergana-Labs/claude_agent_desktop
- **URL:** https://github.com/Fergana-Labs/claude_agent_desktop
- **What it is:** Desktop GUI (Electron + React) for the Claude Agent SDK. API key stored locally. Includes Claude Skills.
- **Language:** TypeScript (Electron + React)
- **Best for:** GUI-based agent usage without CLI

### 30. baryhuang/claude-code-by-agents
- **URL:** https://github.com/baryhuang/claude-code-by-agents
- **What it is:** Desktop app + API for multi-agent orchestration — coordinate local and remote agents through @mentions
- **Language:** TypeScript
- **Best for:** Multi-machine agent coordination (no API key needed — uses subscription)

### 31. severity1/claude-agent-sdk-go
- **URL:** https://github.com/severity1/claude-agent-sdk-go
- **What it is:** Unofficial Go SDK for Claude Code CLI integration. Idiomatic Go API for file ops, shell commands, tool integrations.
- **Language:** Go
- **Best for:** Go developers building Claude agents natively

### 32. disler/claude-code-is-programmable
- **URL:** https://github.com/disler/claude-code-is-programmable
- **Stars:** ~293
- **What it is:** Shows how to use Claude Code programmatically from Python/JS scripts with permission config for Edit, Replace, Bash, Create tools
- **Language:** Python (96%)
- **Best for:** Embedding Claude Code as a component inside your own local app

### 33. zbruhnke/claude-code-starter
- **URL:** https://github.com/zbruhnke/claude-code-starter
- **What it is:** Production-ready config template with stack-specific presets (TypeScript, Python, Go, Rust, Ruby, Elixir), security defaults
- **Language:** Config/Markdown
- **Best for:** Quick project setup for your specific tech stack

### 34. halans/cc-marketplace-boilerplate
- **URL:** https://github.com/halans/cc-marketplace-boilerplate
- **What it is:** Minimal boilerplate for creating Claude Code marketplace plugins
- **Language:** Python
- **Best for:** Publishing your own Claude Code plugins

### 35. scotthavird/claude-code-template
- **URL:** https://github.com/scotthavird/claude-code-template
- **What it is:** Barebones starter with devcontainer support and hook logging for data science analysis
- **Language:** Python (65%)
- **Best for:** Researchers studying Claude Code behavior

### 36. vercel-labs/ai-sdk-reasoning-starter
- **URL:** https://github.com/vercel-labs/ai-sdk-reasoning-starter
- **Stars:** ~181
- **What it is:** Next.js + Vercel AI SDK chatbot for reasoning models. Supports Anthropic (default), OpenAI, xAI, Deepseek. Uses shadcn/ui.
- **Language:** TypeScript (97%)
- **Best for:** Most polished Next.js + Claude chatbot starter

### 37. extrawest/anthropic-claude-chat-bot
- **URL:** https://github.com/extrawest/anthropic-claude-chat-bot
- **What it is:** Node.js chatbot with conversation memory using LangChain JS and Claude 3.5 Sonnet. Streaming responses.
- **Language:** JavaScript
- **Best for:** LangChain + Claude + streaming in Node.js

### 38. zvictor/anthropic-chatbot
- **URL:** https://github.com/zvictor/anthropic-chatbot
- **What it is:** Minimal Next.js chatbot with Vercel AI SDK and Claude Haiku
- **Language:** TypeScript (99%)
- **Best for:** Minimal viable chatbot without extra complexity

---

## Curated Lists (Find Even More)

### 39. hesreallyhim/awesome-claude-code
- **URL:** https://github.com/hesreallyhim/awesome-claude-code
- **What it is:** Curated list of skills, hooks, slash-commands, agent orchestrators, apps, and plugins
- **Best for:** Discovering new Claude Code tools — regularly updated

### 40. punkpeye/awesome-mcp-servers
- **URL:** https://github.com/punkpeye/awesome-mcp-servers
- **What it is:** Large curated list of community MCP servers across many domains
- **Best for:** Finding existing MCP servers to use or reference

### 41. ComposioHQ/awesome-claude-skills
- **URL:** https://github.com/ComposioHQ/awesome-claude-skills
- **What it is:** Curated list of practical Claude Skills for Claude.ai, Claude Code, and the Claude API
- **Best for:** Skills-focused discovery (includes MCP Builder skill)

### 42. VoltAgent/awesome-claude-code-subagents
- **URL:** https://github.com/VoltAgent/awesome-claude-code-subagents
- **What it is:** 100+ specialized subagent configs — read-only, research, code writer, documentation agents
- **Best for:** Copy-paste subagent definitions into your projects

---

## Quick Recommendation

| Goal | Start Here | License |
|---|---|---|
| Build a Claude API app fast | [claude-quickstarts](https://github.com/anthropics/claude-quickstarts) | MIT |
| See Agent SDK demos | [claude-agent-sdk-demos](https://github.com/anthropics/claude-agent-sdk-demos) | MIT |
| Build your own Claude skills | [anthropics/skills](https://github.com/anthropics/skills) | Apache 2.0 |
| Browse 600+ ready configs | [claude-code-templates](https://github.com/davila7/claude-code-templates) | MIT |
| Set up Claude Code for your team | [claude-starter-kit](https://github.com/serpro69/claude-starter-kit) | MIT |
| Learn the Agent SDK | [claude-agent-sdk-intro](https://github.com/kenneth-liao/claude-agent-sdk-intro) | MIT |
| Production agents (Python) | [claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python) | MIT |
| Production agents (TypeScript) | [claude-agent-sdk-typescript](https://github.com/anthropics/claude-agent-sdk-typescript) | MIT |
| Desktop app (no terminal) | [CodePilot](https://github.com/op7418/CodePilot) | MIT |
| Community CLI agent | [claude-engineer](https://github.com/Doriandarko/claude-engineer) | MIT |
| Build MCP servers fast | [fastmcp](https://github.com/punkpeye/fastmcp) | Check repo |
| Embed Claude Code in your app | [claude-code-is-programmable](https://github.com/disler/claude-code-is-programmable) | Check repo |

*Last updated: March 2026*
