# Docs Directory Map

> **Read this BEFORE exploring docs/.** Most docs are reference material — you rarely need to read them.
> Only read a doc if your task specifically requires understanding that topic.

## Page PRDs (docs/page-prds/)

Every AutoForge UI page has a PRD folder. **Before modifying any page, check its PRD folder first.**

| Folder | Page | What's Inside |
|--------|------|-------------|
| `dashboard/` | DashboardPage | Dashboard feature PRDs |
| `workspace/` | WorkspacePage | Workspace chat PRDs |
| `dunkstack/` | DunkStackPage | DunkStack benchmarking PRDs |
| `arena/` | ArenaPage | Arena comparison PRDs |
| `yt-strategy-lab/` | YTStrategyLabPage | YouTube lab PRDs |
| `cli-scripter/` | CliScripterPage | CLI scripter PRDs |
| `meta-engine/` | MetaEnginePage | Meta-training PRDs |
| `monitor/` | MonitorPage | Monitoring PRDs |
| `prd-shredder/` | PRDShredderPage | PRD shredder PRDs |
| `prd-maker/` | (Pipeline — not a page yet) | **PRD Maker pipeline** — mechanism framework, archetype library, build game plan, research reference, stage extractions, skills |
| `role-library/` | RoleLibraryPage | Role library PRDs |
| `seo-tools/` | SEOToolsPage | SEO tools PRDs |
| `token-budget/` | TokenBudgetPage | Token budget PRDs |
| `tool-runner/` | ToolRunnerPage | Tool runner PRDs |
| `market-scraper/` | MarketScraperPage | Reddit market scraper — pain points, ad copy, research projects |
| `component-dashboard/` | ComponentDashboardPage | Component dashboard PRDs |
| `astro-theme/` | (External product — themedna.com) | **Astro Theme Generator / Theme DNA** — screenshot-to-theme pipeline, Elementor generator, WordPress plugin, pricing, marketing strategy. See full info doc: `docs/info/theme-dna-session-worksheet.md` |

**Index:** See `docs/page-prds/README.md` for the complete folder map.

---

## Key Reference Docs

Only read these if your task specifically needs them:

| Doc | When You Need It |
|-----|-----------------|
| **`ACTIVEPIECES.md`** | **Activepieces MCP, flows, auth, setup, bearer token, curl patterns** |
| `SUBSCRIPTION_AND_WEBSOCKET_GUIDE.md` | Working with Claude SDK auth or WebSocket connections |
| `SONNET_OPUS_OPTIMIZATION.md` | Build pipeline Sonnet/Opus agent assignment |
| `MODULARITY_GUIDE.md` | Understanding modular architecture patterns |
| `AGENT_OS_INTEGRATION_GUIDE.md` | Working with Agent OS features |
| `SWARM_ARCHITECTURE.md` | Multi-agent swarm system design |

---

## Docs You Almost Certainly Don't Need

These are research, brainstorming, or one-time documents. **Do NOT read them unless explicitly asked:**

- `COLD_EMAIL_*.md` — Cold email research (not part of the app)
- `PATENT_*.md` / `PROVISIONAL_PATENT_APPLICATION.md` — Patent documents
- `CAGEGUARD_MARKET_RESEARCH.md` — Market research
- `AI_AGENT_SAFETY_RESEARCH.md` — Safety research
- `normieforge-*.md` — NormieForge product concepts
- `OPENCLAW_PROTECTION_RESEARCH.md` — Legal research
- `TOOL-BANK-BUSINESS-STRATEGY.md` — Business strategy

---

## Other Docs Subdirectories

| Folder | What's Inside |
|--------|-------------|
| `research/` | **General research, strategy breakdowns, concept docs, non-page PRDs** — see [`research/README.md`](research/README.md) |
| `agent-briefs/` | Agent briefing documents for specific tasks |
| `agent-os-phases/` | Agent OS implementation phases |
| `references/` | External reference materials |
| `coding-structure-reference/` | Code structure references |
| `page-prds/prd-maker/` | PRD Maker pipeline (mechanism framework, archetypes, stage extractions, skills) |
| `yt-strategies/` | YouTube strategy documents |
| `patent-figures/` | Patent diagram files |

---

## Rules for Docs Tasks

1. **Do NOT read docs unless your task requires it.** Docs are reference material, not working code.
2. **New PRDs** go in `docs/page-prds/{page-name}/prd-{feature-name}.md`.
3. **New page?** Create a matching folder in `docs/page-prds/` from day one.
4. **Do NOT modify existing PRDs** unless specifically asked — they contain historical decisions.
