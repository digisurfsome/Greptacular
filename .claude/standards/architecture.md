# Architecture Standards — Modular AI Pipeline Builder

## The Non-Negotiable Rules

### Rule 1: The Blueprint Is Always the Source of Truth
The Activepieces flow JSON is the master document. It lives in Activepieces forever.
- The skin is a presentation layer over it — NOT a replacement for it
- The deployed output is an artifact — like a PDF — never edit the artifact directly
- Every change goes through the builder via the hinge
- Never try to reconstruct flow JSON from a deployed output — always go back to the source

### Rule 2: The Skin Never Exposes the Builder to Clients
The client-facing URL shows your branded skin. Period.
- `BUILDER_MODE=false` (default): client sees skin only
- `BUILDER_MODE=true` (admin only, never shared): builder slides in for edits
- The Activepieces UI URL is never given to clients
- The hinge is an admin tool, not a client feature

### Rule 3: Custom Code Lives Only in Code Module Nodes
- Never modify Activepieces core files
- Never add custom logic directly to a flow's trigger or action config
- All custom code = a `CodeAction` or a published custom piece built via `ap create-piece`
- This keeps everything hot-swappable and isolates blast radius to one node

### Rule 4: Search the Mechanism Library Before Writing New Code
When building a Code Module node, Claude MUST:
1. Search `/mechanisms/` by tags and input/output types
2. If a matching mechanism exists — use it directly
3. Only write new code if nothing suitable exists
4. After writing new code that works — add it to `/mechanisms/` with proper metadata

### Rule 5: No Node Gets Promoted Without Passing All Tests
Quality gate is strict:
- `draft`: built, untested
- `stable`: passed all 5 test levels (schema validation, mock mode, unit tests, regression gate, integration test)
- `promoted`: stable + used successfully in production at least once
A node cannot appear in the "production ready" library unless it is `stable`. Period.

### Rule 6: All Flow Generation Uses Context7 for Schemas
- Never guess at Activepieces piece settings or field names
- Always pull the current schema via Context7 library `activepieces/activepieces`
- The schema defines: pieceName, actionName, required input fields, field types, valid values
- Generated flow JSON must pass schema validation before being sent to IMPORT_FLOW

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT-FACING LAYER                          │
│                                                                     │
│   yourdomain.com  →  Skin (React branded shell)                     │
│                       ↑                                             │
│                   BUILDER_MODE=false (default)                      │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ API calls
┌─────────────────────────────▼───────────────────────────────────────┐
│                         API LAYER                                   │
│                                                                     │
│   Your thin API (10-20 endpoints)                                   │
│   - Triggers pipeline runs                                          │
│   - Returns results to skin                                         │
│   - Handles auth (reuses Activepieces user system)                  │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│                      ACTIVEPIECES ENGINE                            │
│                                                                     │
│   - Pipeline executor (runs flows)                                  │
│   - Flow storage (all blueprints live here)                         │
│   - 280+ pieces available                                           │
│   - REST API: POST /v1/flows/{id} (IMPORT_FLOW)                     │
│   - User database, auth, webhooks                                   │
│                                                                     │
│   ┌─────────────────────────────────────────┐                       │
│   │         Your Custom Pieces              │                       │
│   │   - Code Module Node (ap publish)       │                       │
│   │   - Any other custom pieces you build   │                       │
│   └─────────────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────┘

                         ADMIN ONLY
┌─────────────────────────────────────────────────────────────────────┐
│                          HINGE LAYER                                │
│                                                                     │
│   BUILDER_MODE=true  →  Activepieces builder UI exposed             │
│   Admin edits pipeline  →  Saves to Activepieces (blueprint)       │
│   BUILDER_MODE=false →  Skin takes over again                       │
└─────────────────────────────────────────────────────────────────────┘

                      AI CO-PILOT LAYER
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   User describes pipeline in plain English                          │
│        ↓                                                            │
│   Claude pulls schemas from Context7 (activepieces/activepieces)    │
│        ↓                                                            │
│   Claude generates complete FlowVersion JSON                        │
│        ↓                                                            │
│   POST /v1/flows  (create empty)                                    │
│   POST /v1/flows/{id}  (IMPORT_FLOW with full definition)           │
│        ↓                                                            │
│   Pipeline appears in builder — fully built, all settings filled    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## What Goes Where

| Thing | Where It Lives | Why |
|-------|---------------|-----|
| Flow definitions (blueprints) | Activepieces database | Source of truth |
| Custom node code | `ap publish` → Activepieces pieces registry | Isolated, hot-swappable |
| Reusable code patterns | `/mechanisms/` folder | Searchable, tagged, reusable |
| Skin UI | Separate React app | Decoupled from builder |
| Mechanism metadata | Header comment in each mechanism file | Collocated with code |
| Node test cases | Auto-generated from 7-step form at build time | Tied to specific node version |
| Theme/stylesheet | Generated by Skin Builder, stored in skin template | Per deployment |

---

## What NOT to Do

- DO NOT fork Activepieces core and modify it — upgrade path becomes a nightmare
- DO NOT build a decompiler (reconstruct flow JSON from deployed output) — unnecessary complexity, prone to drift
- DO NOT give clients access to the Activepieces builder URL — ever
- DO NOT write custom code outside of a Code Module node
- DO NOT skip mechanism library search before writing new node code
- DO NOT promote a node to stable without running all 5 test levels
- DO NOT hard-code API keys or credentials inside flow JSON — use Activepieces connections system
- DO NOT put multiple independent pipelines inside one flow — one flow per use case
