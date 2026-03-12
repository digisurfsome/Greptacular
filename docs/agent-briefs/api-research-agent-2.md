# API Research Engine — Agent 2: Frontend

## Read First
- `docs/prd-api-research-engine.md` — Full PRD with UI wireframes, data model, component layout
- `ui/WORKSPACE_STANDARDS.md` — UI standards (neobrutalism, Tailwind v4, Radix UI)
- `docs/SONNET_OPUS_OPTIMIZATION.md` — Build optimization rules

## What You're Building

**Phase 2: Frontend** — TypeScript types + API Analysis section on BlueprintPreview

## Tasks (in order)

### 1. Add TypeScript types to `ui/src/lib/types.ts`

Add interfaces matching the Pydantic models from Phase 1:

```typescript
interface APIAlternative {
  service_name: string
  category: string
  pricing_summary: string
  free_tier: string
  monthly_cost: string
  tradeoff: string
  signup_url: string
}

interface APIResearchResult {
  service_key: string
  service_name: string
  category: string
  pricing_summary: string
  pricing_tiers: string[]
  free_tier: string
  api_access_cost: string
  per_unit_cost: string
  alternatives: APIAlternative[]
  red_flags: string[]
  research_source: string  // "web_search" | "static_database"
  researched_at: string
}

interface BlueprintAPIResearch {
  results: APIResearchResult[]
  total_estimated_monthly_cost: string
  research_duration_seconds: number
}
```

Add `api_research?: BlueprintAPIResearch | null` to the `TFSheetBlueprint` interface (or whatever the existing blueprint type is called).

### 2. Add API Analysis section to `BlueprintPreview.tsx`

Read the existing `BlueprintPreview.tsx` to understand its structure. Add a new collapsible section between the chain visualization and the "Required APIs" links section.

**Section layout (see PRD wireframe):**
- Header: "API Cost Analysis" with total estimated monthly cost badge
- Research source badge ("Live research" vs "Cached data")
- One accordion card per API with:
  - Service name + category badge
  - Pricing summary line
  - API access cost (highlighted if expensive)
  - Per-unit cost
  - Red flags section with warning icons (expanded by default if red flags exist)
  - Alternatives table with name, price, tradeoff
  - Action buttons: "Get API key" link + "Use {alternative} instead" buttons

**Design rules:**
- Neobrutalism style — match existing components
- Orange accent color for warnings/red flags
- Tailwind CSS v4 classes
- Radix UI Accordion for collapsible sections
- Responsive layout

### 3. Handle empty/null states

- If `api_research` is null/undefined, don't render the section at all
- If a specific API has no alternatives, show "No alternatives found"
- If research source is "static_database", show a subtle "Cached data — may not reflect current pricing" note

### 4. Verify

- `cd ui && npm run build` — zero TypeScript errors
- `cd ui && npm run lint` — clean lint
- Commit with clear message

## Critical Rules

- Match existing patterns in BlueprintPreview.tsx — same component style, same imports
- Use Radix UI primitives (Accordion, Badge, etc.) — check what's already imported
- Don't modify any existing components — only ADD the new section
- Stage only files you created or modified — do NOT use `git add -A`
- Commit after completing all tasks with a clear message
