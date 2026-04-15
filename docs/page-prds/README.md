# Page PRDs

Organized PRD storage for each AutoForge UI page. When you want to improve a specific page, look in its folder for existing PRDs and plans.

## Folder Map

| Folder | Page Component | Description |
|--------|---------------|-------------|
| `dashboard/` | DashboardPage.tsx | Main AutoForge dashboard |
| `workspace/` | WorkspacePage.tsx | Workspace chat and project management |
| `yt-strategy-lab/` | YTStrategyLabPage.tsx | YouTube Strategy Lab - video analysis, PRD ingestion, tool factory |
| `dunkstack/` | DunkStackPage.tsx | DunkStack benchmarking |
| `arena/` | ArenaPage.tsx, ArenaChatPage.tsx | Arena comparison chat |
| `cli-scripter/` | CliScripterPage.tsx | CLI script builder |
| `meta-engine/` | MetaEnginePage.tsx | Meta training engine |
| `monitor/` | MonitorPage.tsx | System monitoring |
| `prd-shredder/` | PRDShredderPage.tsx | PRD analysis and shredding |
| `role-library/` | RoleLibraryPage.tsx | Role/prompt library |
| `seo-tools/` | SEOToolsPage.tsx | SEO optimization tools |
| `token-budget/` | TokenBudgetPage.tsx | Token budget management |
| `tool-runner/` | ToolRunnerPage.tsx | Tool execution runner |
| `market-scraper/` | MarketScraperPage.tsx | Reddit market scraper — pain points, ad copy, phrase frequency, research projects |
| `component-dashboard/` | ComponentDashboardPage.tsx | Component overview dashboard |
| `prd-maker/` | (planned) | PRD Maker — 10-stage pipeline turning app rants into buildable specs |
| `dunkstack/` | DunkStackPage.tsx | DunkStack walkie-talkie system — file-based context, agent chaining, cross-pollination. **Master PRD for Archon port:** `PRD_WALKIE_TALKIE_ARCHON.md` |

## How to Use

1. Drop PRDs into the relevant page folder
2. Name them descriptively: `prd-feature-name.md`
3. Agents looking to improve a page check here first
