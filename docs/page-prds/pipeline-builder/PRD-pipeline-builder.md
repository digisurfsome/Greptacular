# Pipeline Builder — Agent OS PRD
**Version:** 1.0  
**Date:** 2026-04-08  
**Status:** Active — Build This Now

---

## AGENT OS CONTEXT

Use this file as your complete context for every session building this product.
Read it in full before writing a single line of code.

---

# LAYER 1: STANDARDS

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Pipeline Engine | Activepieces (MIT, self-hosted via Docker) |
| Skin Frontend | React 19, TypeScript, Vite, Tailwind CSS v4 |
| Skin Backend (API bridge) | FastAPI (Python 3.11+) |
| Code Editor (in node) | Monaco Editor (same as VS Code) |
| Auth | Activepieces built-in (reused, not rebuilt) |
| Database | Activepieces built-in PostgreSQL (reused) |
| Container | Docker + Docker Compose |
| Blueprint Storage | JSON files + Activepieces flow storage |

## Architecture Rules — Non-Negotiable

1. **The blueprint is always the source of truth.** The pipeline graph JSON is the master document. The skin is an output. The compiled app (future) is an output. Never edit outputs — always edit the blueprint.
2. **The builder never touches the client.** In skin mode, the Activepieces builder UI is inaccessible to client users. Period. No exceptions.
3. **Never rebuild what Activepieces already built.** Auth, database, pipeline execution engine, node runner — all of this exists. Extend it. Never replace it.
4. **The skin is a shell, not a fork.** The skin calls Activepieces APIs. It does not duplicate logic. It does not hold state. Activepieces holds all state.
5. **Every custom node has a typed interface.** Input schema and output schema are defined before any code is written. No untyped nodes.
6. **The Code Module is sandboxed.** Custom user code never has access to the host system, other pipelines, or auth credentials.
7. **BUILDER_MODE is the only gate.** One env var controls whether the builder is exposed. Nothing else. No role hacks, no route tricks.

## Code Conventions

- All skin components: functional React, TypeScript strict mode
- API calls: all in `src/lib/api.ts` — never inside components
- Types: all in `src/lib/types.ts` — never inline in components
- Env vars: prefixed `VITE_` for frontend, unprefixed for backend
- Node templates: one file per node type in `nodes/`
- Blueprint JSON: always validated against schema before save

---

# LAYER 2: PRODUCT

## Vision

**Build any AI automation pipeline in an afternoon. Ship it to clients looking like a locked SaaS. Edit it in 20 minutes whenever they call.**

## The Problem

Every automation tool forces a choice:
- **Build it custom** (months of coding, everything from scratch)
- **Use a platform** (Zapier/Make/n8n — locked in forever, no real code, no client-facing skin)

Neither option is right for someone who builds AI tools for themselves or for clients at speed. Custom is too slow. Platforms are too rigid and look like platforms.

## What This Is

A modular drag-and-drop AI pipeline builder with three operating modes:

### Mode 1: Raw Builder
Full Activepieces interface. You build, test, iterate. This is your dev environment. Nobody else ever sees this.

### Mode 2: Skin Mode (The Skirt)
A custom React shell wraps the Activepieces backend. Client sees a polished branded app. Under the hood the pipeline is still running in Activepieces — fully editable at any time via the hinge. Client never knows.

### Mode 3: Compiled App (v2 — not now)
Pipeline exports to standalone deployable code. No Activepieces dependency. For SaaS products you hand off completely. This is future work.

## The Moat

**The Hinge.** You can flip from skin mode to builder mode and back with one env var. The underlying pipeline, database, users — nothing changes. You make edits in 20 minutes, flip back. Client sees an updated app. This is not possible with any existing tool.

**The Code Module.** A node type that lets you drop custom code anywhere in a pipeline, with a 7-step guided form that structures the problem before you write a word of code. Claude writes the implementation. The rest of the pipeline is untouched.

**The Skin Template.** One boilerplate, reused for every client project. New project = copy template, configure branding, point at pipeline backend, done. Heat shrink over any pipeline shape.

## Target Users

1. **You (the builder)** — building your own AI tools (YouTube Lab, scraping workflows, research pipelines). Use raw builder mode. Never skin needed.
2. **Client work** — building custom automation for a business. Use skin mode. Looks locked. You hold the hinge key.
3. **SaaS products** — something with real market traction that needs to stand alone. Use compiled app (v2).

## What We Are NOT Building

- A Zapier competitor (we don't care about 1,000 SaaS integrations)
- A visual frontend builder (we're not Webflow)
- A general purpose coding tool (we're not Replit)
- A standalone LLM wrapper (we're not a chatbot)
- A compiled app exporter (that's v2 — not now)

## Core Use Cases

### Use Case 1: YouTube Research Pipeline
Trigger: manual or cron → YouTube search → transcript pull → LLM summarizer → SEO scorer → email report  
Mode: Raw builder for yourself. Skin if you sell it.

### Use Case 2: Client Scraping Automation
Scrape competitor site → parse product data → normalize → diff against last run → notify on change  
Mode: Skin. Client sees "Competitor Monitor" app. You built it in 2 hours.

### Use Case 3: Content Pipeline
RSS feed → filter by keyword → LLM rewriter → tone adjustment → publish to CMS  
Mode: Skin or raw builder.

### Use Case 4: Lead Enrichment
CSV upload → for each row: search LinkedIn → extract company data → score lead → write to CRM  
Mode: Skin. Client sees "Lead Enricher." Under the hood: 6 nodes, one Code Module for the scoring logic.

## Roadmap

### MVP (Now — Days to Build)
- Activepieces self-hosted via Docker
- Skin template boilerplate (auth, branding, API bridge, BUILDER_MODE hinge)
- Code Module node (Monaco editor, 7-step form, Claude button, quality flag)
- 10 priority AI nodes (LLM call, prompt template, scraper, YouTube pull, structured extractor, classifier, chunker, loop, conditional, webhook)

### v1.5 (After MVP Proves Out)
- Full AI node library (all 40+ node types from the taxonomy)
- Skin template v2 (better branding system, multi-tenant)
- Module quality promotion system (draft → stable → promoted to built-in)
- Blueprint versioning UI

### v2 (When a Pipeline Deserves to Stand Alone)
- Pipeline compiler (graph JSON → standalone FastAPI + React app)
- Per-node code templates
- Dependency resolver
- Docker export

---

# LAYER 3: SPECS

---

## SPEC-001: Activepieces Foundation

### Purpose
Get Activepieces running self-hosted. This is the engine. Everything else depends on it.

### What It Does
- Runs the pipeline execution engine
- Hosts the drag-and-drop builder UI (for raw builder mode)
- Manages users and auth
- Stores pipeline blueprints (flows)
- Exposes REST API that the skin consumes

### Technical Approach

**Docker Compose setup:**
```yaml
# docker-compose.yml
version: '3'
services:
  activepieces:
    image: activepieces/activepieces:latest
    ports:
      - "8080:80"
    environment:
      - AP_ENGINE_EXECUTABLE_PATH=dist/packages/engine/main.js
      - AP_ENCRYPTION_KEY=${AP_ENCRYPTION_KEY}
      - AP_JWT_SECRET=${AP_JWT_SECRET}
      - AP_POSTGRES_DATABASE=activepieces
      - AP_POSTGRES_HOST=postgres
      - AP_POSTGRES_PORT=5432
      - AP_POSTGRES_USERNAME=postgres
      - AP_POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - AP_REDIS_URL=redis://redis:6379
      - AP_FRONTEND_URL=${AP_FRONTEND_URL}
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: activepieces
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

**Environment file:**
```env
AP_ENCRYPTION_KEY=<generate-32-char-random>
AP_JWT_SECRET=<generate-32-char-random>
AP_FRONTEND_URL=http://localhost:8080
POSTGRES_PASSWORD=<strong-password>
```

### File Structure
```
pipeline-builder/
├── docker-compose.yml
├── .env
├── .env.example
└── README.md
```

### Success Criteria
- `docker compose up` starts successfully
- Activepieces UI accessible at `localhost:8080`
- Can create a test flow and run it
- API accessible at `localhost:8080/api/v1`

---

## SPEC-002: Skin Template System

### Purpose
A reusable React shell that wraps any Activepieces backend. Apply it to any project in minutes. The client sees your UI, not Activepieces.

### What It Does
- Presents a polished branded app to the client
- Proxies all pipeline operations through to Activepieces API
- Exposes a BUILDER_MODE flag (the hinge) that reveals the raw builder
- Reuses Activepieces auth (JWT tokens, same login system)
- Is fully templatable — copy it, configure it, done

### The Hinge
One environment variable: `BUILDER_MODE=true|false`

When `false` (default):
- Client sees only the skin UI
- No Activepieces builder routes are accessible
- The `/builder` path returns 404 or redirects home

When `true` (admin only):
- An "Edit Pipeline" button appears in the skin
- Clicking it opens the Activepieces builder in a modal or new tab
- Admin makes changes, saves, closes
- Sets back to `false` for client

### File Structure
```
skin-template/
├── src/
│   ├── App.tsx                  # Main app shell
│   ├── lib/
│   │   ├── api.ts               # All Activepieces API calls
│   │   ├── types.ts             # TypeScript types
│   │   └── auth.ts              # Auth helpers (wraps AP JWT)
│   ├── pages/
│   │   ├── HomePage.tsx         # Main client-facing page
│   │   ├── LoginPage.tsx        # Login (calls AP auth)
│   │   └── BuilderPage.tsx      # BUILDER_MODE only — shows AP builder
│   ├── components/
│   │   ├── SkinShell.tsx        # Branded wrapper (logo, nav, colors)
│   │   ├── PipelineRunner.tsx   # Trigger runs, show status
│   │   ├── RunHistory.tsx       # Past run results
│   │   └── HingeButton.tsx      # Admin-only "Edit Pipeline" button
│   └── styles/
│       └── brand.css            # Override here: colors, fonts, logo
├── .env
│   ├── VITE_AP_URL=http://localhost:8080
│   ├── VITE_BUILDER_MODE=false
│   └── VITE_BRAND_NAME=My App
├── package.json
├── vite.config.ts
└── Dockerfile
```

### API Bridge (api.ts pattern)
```typescript
const AP_URL = import.meta.env.VITE_AP_URL

export async function triggerPipeline(flowId: string, data: Record<string, unknown>) {
  const res = await fetch(`${AP_URL}/api/v1/webhooks/${flowId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  return res.json()
}

export async function getRunHistory(flowId: string) {
  const res = await fetch(`${AP_URL}/api/v1/flow-runs?flowId=${flowId}`, {
    headers: { Authorization: `Bearer ${getToken()}` }
  })
  return res.json()
}
```

### How to Apply to a New Project
1. `cp -r skin-template/ my-client-project-skin/`
2. Edit `.env`: set `VITE_AP_URL`, `VITE_BRAND_NAME`
3. Edit `brand.css`: set colors, logo
4. Edit `HomePage.tsx`: add client-specific UI
5. `npm run build` → `docker compose up`
6. Done. Client sees their app.

### Success Criteria
- Skin runs and shows branded UI
- Login works using Activepieces credentials
- Pipeline trigger button fires a run
- Run history shows past executions
- BUILDER_MODE=true reveals "Edit Pipeline" button
- BUILDER_MODE=false hides it completely

---

## SPEC-003: Code Module Node

### Purpose
The one custom node type we build. Drops anywhere in a pipeline. Contains custom code written by the user or generated by Claude. Fully sandboxed. Does not affect surrounding nodes.

### What It Does
- Accepts typed input from the left (defined by user via 7-step form)
- Executes custom Python or JavaScript code in a sandbox
- Passes typed output to the right
- Has a Monaco code editor embedded in the node UI
- Has a "Build with Claude" button that opens a scoped Claude Code session
- Has a quality flag: `draft` | `stable` | `promoted`

### The 7-Step Deterministic Mechanism Form
Before any code editor opens, the user fills out 7 questions. This is mandatory. These answers auto-generate the input/output schema and a starter code template.

**Step 1 — The Wall (Input)**
> "What data is coming INTO this node?"
- Field name, type (string / number / array / object / boolean), required y/n
- Can add multiple fields
- This becomes the input schema

**Step 2 — The Output**
> "What must come OUT of this node?"
- Same field definition UI
- This becomes the output schema

**Step 3 — The Ceiling (Failure Modes)**
> "What can go wrong? List every way this can fail."
- Free text, one per line
- Becomes the error handling checklist
- Claude uses this to write try/catch blocks

**Step 4 — The Gates (Validation Rules)**
> "What conditions must be true before this runs?"
- e.g., "input.url must start with https"
- e.g., "input.count must be between 1 and 100"
- Becomes input validation code

**Step 5 — The Steps (Execution Order)**
> "In plain English, what does this node do, step by step?"
- Ordered list, plain language
- e.g., "1. Call the API. 2. Parse the JSON. 3. Filter results by date."
- This is the spec Claude codes from

**Step 6 — The Connection Points**
> "What node comes before this? What node comes after?"
- Dropdown of existing nodes in the pipeline
- Validates that input schema matches upstream output
- Validates that output schema matches downstream input
- Shows mismatch warnings before code is written

**Step 7 — The Quality Standard**
> "When is this done?"
- Checkbox list auto-generated from Steps 3 & 4
- Must check all boxes before quality flag upgrades from `draft` to `stable`

### Auto-Generated Starter Template
After form completion, the node pre-fills with:
```python
# AUTO-GENERATED — Edit below
# Input: { url: string, limit: number }
# Output: { results: array, count: number }

def run(input: dict) -> dict:
    # Validate inputs
    assert input.get('url', '').startswith('https'), "url must start with https"
    assert 1 <= input.get('limit', 0) <= 100, "limit must be between 1 and 100"
    
    # TODO: Step 1 — Call the API
    # TODO: Step 2 — Parse the JSON
    # TODO: Step 3 — Filter results by date
    
    return {
        "results": [],
        "count": 0
    }
```

### "Build with Claude" Button
- Opens a panel with a Claude Code session
- Context injected automatically:
  - The 7-step form answers
  - The starter template
  - The input/output schema
  - The surrounding node context (what feeds in, what goes out)
- Claude writes the implementation
- User reviews, accepts, closes panel
- Code appears in Monaco editor

### Quality Flag System
| Flag | Meaning | Upgrade Condition |
|------|---------|------------------|
| `draft` | Works, probably. Don't trust it fully. | Default on creation |
| `stable` | Tested, all quality checklist items pass | Manual promotion after testing |
| `promoted` | Abstracted into a built-in node available to all pipelines | Owner decision |

### Sandboxing
- Code executes in an isolated subprocess
- No filesystem access outside `/tmp/node-sandbox/`
- No network access (must be explicitly enabled per-node)
- Timeout: 30 seconds default, configurable up to 5 minutes
- Memory limit: 512MB default

### File Structure (Activepieces piece extension)
```
pieces/
└── code-module/
    ├── index.ts              # Piece definition
    ├── actions/
    │   └── run-code.ts       # The run action
    ├── sandbox/
    │   ├── runner.py         # Python sandbox executor
    │   └── runner.js         # JS sandbox executor
    └── ui/
        ├── SevenStepForm.tsx # The 7-question form
        ├── MonacoNode.tsx    # Monaco editor in node
        └── ClaudePanel.tsx   # Build with Claude panel
```

### Success Criteria
- 7-step form completes and generates starter template
- Monaco editor loads and is editable
- "Build with Claude" opens panel with correct context injected
- Code executes and output passes to next node
- Quality flag is visible and manually upgradeable
- Bad code in the module does NOT crash the pipeline — it fails gracefully with an error on that node only

---

## SPEC-004: AI Node Library (Priority Build Order)

### Node Interface Standard
Every node must implement:
```typescript
interface PipelineNode {
  name: string
  description: string
  version: string
  inputSchema: JSONSchema
  outputSchema: JSONSchema
  run(input: unknown): Promise<unknown>
  onError(error: Error, input: unknown): Promise<ErrorOutput>
}
```

### Priority 1 — Build These First (MVP)
These cover 80% of real-world AI pipeline use cases.

| Node | Input | Output | Notes |
|------|-------|--------|-------|
| **LLM Call** | prompt: string, model: enum | response: string, tokens: number | Supports Claude, GPT-4o, Gemini |
| **Prompt Template** | template: string, variables: object | prompt: string | Handlebars-style `{{variable}}` |
| **Structured Extractor** | text: string, schema: JSONSchema | extracted: object | LLM extracts structured data |
| **Web Scraper (static)** | url: string, selector: string | html: string, text: string | Cheerio-based |
| **YouTube Pull** | videoId or url: string | transcript: string, metadata: object | Uses yt-dlp |
| **Chunker** | text: string, chunkSize: number | chunks: string[] | For long docs before LLM |
| **Loop** | items: array, subflow: flowId | results: array | Runs subflow for each item |
| **Conditional Branch** | condition: expression | routes to branch A or B | If/else logic |
| **HTTP Request** | url, method, headers, body | response: object, status: number | Generic API call |
| **Code Module** | defined by user | defined by user | See SPEC-003 |

### Priority 2 — Build After MVP
| Node | Category |
|------|---------|
| Web Scraper (headless) | Acquisition |
| Search (Google/YouTube/Reddit) | Acquisition |
| File Ingest (CSV/JSON/PDF) | Acquisition |
| Classifier | AI/LLM |
| Summarizer | AI/LLM |
| Rewriter | AI/LLM |
| Embedding Generator | AI/LLM |
| Semantic Search | AI/LLM |
| Batch LLM | AI/LLM |
| DB Write | Storage |
| Vector Store | Storage |
| Rate Limiter | Control Flow |
| Retry with Backoff | Control Flow |
| Human Approval Gate | Control Flow |
| Transcription | Enrichment |
| Entity Extraction | Enrichment |
| Email Send | Delivery |
| Slack/Discord | Delivery |
| Google Sheets Sync | Delivery |

---

## SPEC-005: Blueprint Management

### Purpose
Every pipeline is a blueprint. The blueprint is a JSON document. It is the source of truth for everything. Skin it, compile it, share it — the blueprint never changes unless you intentionally edit it.

### Blueprint JSON Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema",
  "type": "object",
  "required": ["id", "name", "version", "nodes", "edges"],
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "name": { "type": "string" },
    "version": { "type": "integer", "minimum": 1 },
    "created_at": { "type": "string", "format": "date-time" },
    "updated_at": { "type": "string", "format": "date-time" },
    "nodes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "type", "config"],
        "properties": {
          "id": { "type": "string" },
          "type": { "type": "string" },
          "config": { "type": "object" },
          "position": {
            "type": "object",
            "properties": {
              "x": { "type": "number" },
              "y": { "type": "number" }
            }
          }
        }
      }
    },
    "edges": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["from", "to"],
        "properties": {
          "from": { "type": "string" },
          "to": { "type": "string" },
          "fromPort": { "type": "string" },
          "toPort": { "type": "string" }
        }
      }
    }
  }
}
```

### Versioning
- Every save increments `version` by 1
- Previous versions stored in `blueprints/history/{id}/{version}.json`
- Any version can be loaded into the builder
- The "current" version is always `blueprints/{id}/latest.json`
- Versions are never deleted automatically

### Storage Structure
```
blueprints/
├── {blueprint-id}/
│   ├── latest.json          # Current version (always up to date)
│   ├── meta.json            # Name, tags, created_at, owner
│   └── history/
│       ├── v1.json
│       ├── v2.json
│       └── v3.json
```

### How the Skin Points to a Blueprint
The skin's `.env` contains:
```env
VITE_FLOW_ID=<activepieces-flow-id>
```
The skin calls Activepieces APIs using this flow ID. The blueprint JSON is the Activepieces flow definition. They are the same thing — Activepieces stores it, we reference it by ID.

### Success Criteria
- Every pipeline save creates a version entry
- Any past version loads cleanly into the builder
- Blueprint JSON validates against schema on every save
- Skin correctly triggers and reads the flow it's pointed at

---

# BUILD ORDER

Do these in sequence. Each one depends on the previous.

```
1. SPEC-001: Get Activepieces running in Docker           (~30 min)
2. SPEC-002: Build skin template boilerplate              (~2-3 hours)
3. SPEC-003: Build Code Module node                       (~3-4 hours)
4. SPEC-004: Build Priority 1 AI nodes                   (~2-3 hours)
5. SPEC-005: Blueprint versioning system                  (~1 hour)
```

Total: One solid session. Less with AI coding.

---

# STARTING A SESSION

When starting a new Claude Code session on this project, say:

> "Read `/docs/page-prds/pipeline-builder/PRD-pipeline-builder.md` in full. We are building the Pipeline Builder. We are on [SPEC-00X]. Here is what's done: [list]. Build [next thing]."

That's it. The PRD has everything the agent needs.
