# Product Vision — Modular AI Pipeline Builder

## What This Product Is

A modular AI pipeline builder where every workflow is built from pre-made deterministic nodes (280+ already exist in Activepieces), and custom logic gets coded into isolated "Code Module" nodes that can be thrown away and rebuilt without breaking anything else. The builder is hidden behind a branded **Skin** so clients see a polished product, not a builder. An AI **Co-Pilot** builds entire pipelines from a plain English description by generating and injecting the correct flow JSON automatically.

---

## The Core Insight (The Stripe Minions Principle)

Every automation tool shares 90% of the same pieces: fetch data, clean it, call an LLM, filter or route the result, store or send it. Those 90% are **already built** in Activepieces — 280+ nodes, drag and drop, done.

The other 10% — the custom thing that makes your specific tool actually useful — goes into a **Code Module node**. That node is isolated. If it breaks, throw it away. Rebuild just that piece. Nothing else is affected.

The bones, joints, and wrists are all pre-built and reliable (deterministic). The custom AI logic lives at the tips of the fingers — replaceable without touching the skeleton.

---

## The Four Layers

### Layer 1: Foundation — Activepieces (Already Built)
- MIT license, self-hosted, 280+ pre-built deterministic nodes
- Every common automation pattern is already a node: scrape, HTTP, filter, transform, LLM call, Gmail, Slack, YouTube, Notion, Stripe, and 270 more
- Flows stored as JSON — the "blueprint" that is always the source of truth
- Full REST API including `IMPORT_FLOW` — inject a complete pipeline in two API calls

### Layer 2: AI Co-Pilot (You Build This)
- User describes what they want in plain English
- Claude reads the Activepieces piece schemas via Context7 (`activepieces/activepieces`, trust 9/10)
- Claude generates the complete flow JSON (`FlowVersion` format, schemaVersion "21")
- Two API calls: create empty flow → IMPORT_FLOW with the full definition
- Pipeline appears in the builder, fully built, all settings configured
- User confirms, iterates ("change Gmail to Slack", "add a filter before the LLM step")
- The AI never guesses settings — it reads the actual TypeScript schema before generating

### Layer 3: Skin + Hinge System (You Build This)
- **Skin**: A branded React shell over Activepieces. Client sees your product. No builder visible.
- **Hinge**: `BUILDER_MODE=true` flag. Flip it — builder slides in. Edit the pipeline. Flip it back. Client sees the update.
- **Skin Template**: Reusable boilerplate — copy it per client, change logo/colors, done.
- **Skin Builder**: Screenshot of any app → 5-page prompt system → generates complete CSS stylesheet + theme → applied to template automatically.

### Layer 4: Code Module Node (You Build This via CLI)
- A custom Activepieces piece built with `ap create-piece` and deployed with `ap publish`
- Has a **7-step deterministic form** as typed props (Monaco editor, VS Code quality)
- "Build It" button calls Claude scoped only to that node's code — can't touch anything else
- **Mechanism Library** (`/mechanisms/`) — Claude searches for reusable patterns before writing new code
- **Quality flags**: `draft` → `stable` → `promoted to built-in`
- Wrong module? Throw it away. Rebuild. Nothing else breaks.

---

## Why Nobody Has Done This

| Tool | Why It Falls Short |
|------|-------------------|
| n8n / Zapier / Make | Integration-first, not AI-first. Lock-in model (you can never leave). |
| Bubble / Webflow | Frontend only. No logic layer. Can't export. |
| Langflow | AI-first but no skin system, no mechanism library, no client deployment model. |
| Bolt / Lovable | Build entire apps from scratch. One bug can break everything. Scope is enormous. |
| Activepieces alone | Has the engine but no AI co-pilot, no skin/hinge, no code module node builder. |

**What's different here:** Custom code is scoped to one isolated node. The skin hides the builder from clients. The AI builds pipelines by generating correct JSON — not by clicking buttons. A mechanism library means you never write the same pattern twice.

---

## Use Cases

### Personal Tooling (Day 1)
- YouTube research: search → transcribe → LLM extract insights → SEO score → Slack digest
- Content validation pipelines, market research scrapers, lead enrichment flows
- Any automation built manually today — built in minutes with the AI co-pilot

### Client Work
- Build a custom automation tool for a client in hours
- Apply the skin — client sees a branded product
- They ask for a change → lift hinge → edit in 20 min → drop hinge back → done
- Client never knows it's built on a pipeline builder

### SaaS Products
- Build a vertical-specific tool (e.g., YouTube channel research SaaS)
- Apply skin → looks standalone
- Free: use the pipeline / Paid: AI co-pilot builds and modifies it for you

---

## Business Model

| Tier | What You Get |
|------|-------------|
| Free | Builder access, 280 nodes, drag and drop |
| Pro | AI co-pilot + skin/hinge system |
| Agency | Multi-client deployments, white label |
| Module Marketplace | Buy/sell tested Code Module nodes |

**The upgrade gate:** You can build pipelines yourself for free. Having the AI understand what you want, design the flow, configure every setting correctly, and inject it in two API calls — that's Pro. Nobody who uses it goes back to dragging nodes manually.

---

## Roadmap

### MVP
1. Activepieces self-hosted and working
2. AI Co-Pilot: plain English → flow JSON → IMPORT_FLOW → pipeline appears built
3. Skin template + hinge system
4. Basic mechanism library

### v1.5
5. Code Module node (7-step form + Monaco + Claude scoped to node)
6. 5-level testing layer
7. Skin Builder (screenshot → stylesheet)
8. MCP skills per node category

### v2
9. Module Marketplace
10. MCP Flows (pipelines as callable MCP tools)
11. Multi-tenant deployments
12. Community template library

---

## The Blueprint Rule — Non-Negotiable

The flow JSON is always the source of truth. The skin is just the presentation layer. The compiled output is an artifact like a PDF — you never edit the PDF, you edit the source and regenerate. The builder is always accessible via the hinge. Nothing is ever permanently locked in a way you can't edit.
