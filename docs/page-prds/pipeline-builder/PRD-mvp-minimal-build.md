# Pipeline Builder — MVP Minimal Build
**Agent OS PRD**
**Version:** 1.0
**Date:** 2026-04-08
**Status:** BUILD THIS FIRST — nothing else until this is done

---

## AGENT OS CONTEXT

Use this file as complete context for the minimal build session.
Read it in full before writing a single line of code.
This is NOT the full pipeline builder. This is the minimum needed to run the 11-stage PRD Maker prompt chain.

---

# LAYER 1: STANDARDS

## Tech Stack — Minimal Build Only

| Layer | Technology |
|-------|-----------|
| Pipeline Engine | Activepieces (MIT) — self-hosted via Docker Compose |
| Skin Shell | React 19 + TypeScript + Vite + Tailwind CSS v4 |
| Skin API Bridge | FastAPI (Python 3.11+) — thin layer only |
| Auth | Activepieces built-in — do not rebuild |
| Database | Activepieces built-in PostgreSQL — do not touch |
| Claude Integration | Claude Code CLI via subscription (force_subscription=True) |
| Container Runtime | Docker Desktop (already installed on user machine) |
| Repo | New standalone GitHub repo — NOT inside Greptacular |

## Architecture Rules — Non-Negotiable

1. **Activepieces is the engine. Do not rebuild anything it already has.** Auth, DB, pipeline execution, node runner — all Activepieces. You extend, never replace.
2. **One env var controls the hinge.** `BUILDER_MODE=true` exposes the full Activepieces UI. `BUILDER_MODE=false` serves the skin only. Nothing else gates this.
3. **The skin calls Activepieces APIs.** It does not hold state. It does not duplicate logic. Activepieces holds all state.
4. **Claude subscription auth only.** Any LLM call in any node uses `force_subscription=True` / clears `ANTHROPIC_API_KEY`. No API key burns. Ever.
5. **Blueprint is always source of truth.** The pipeline graph JSON lives in Activepieces. The skin is an output. Never edit outputs.
6. **Minimal means minimal.** Do not build Code Module node, compiler, self-healing, or anything not in this PRD. Those are in the full PRD. Not now.

## Code Conventions

- Skin components: functional React, TypeScript strict mode
- All API calls: `src/lib/api.ts` — never inside components
- All types: `src/lib/types.ts` — never inline
- Env vars: `VITE_` prefix for frontend, unprefixed for backend
- No custom node types in this build — use Activepieces built-in nodes only

---

# LAYER 2: PRODUCT

## What This Build Is

The absolute minimum viable system to run the 11-stage PRD Maker prompt chain as a pipeline.

**Goal:** Wire up the 11 SKILL.md stages from `docs/page-prds/prd-maker/skills-complete/` as an Activepieces flow. Each stage becomes a node. Output from one feeds the next. Stages 0 and 1 are interactive (chat). Stages 2–10 run automatically.

**Why this and nothing else first:** Once this runs, you dump the entire pipeline builder concept through it and get the best PRD ever written for the full build. Then you build the full thing from that PRD.

## What "Done" Looks Like

1. Activepieces running at `localhost:8080` in Docker
2. Skin running at `localhost:3000` — branded shell, hinge works
3. Inside the skin: a chat interface connected to the pipeline
4. Pipeline Stage 0 (Foundation) asks 5 questions, user answers in chat
5. Pipeline Stage 1 (Idea Capture) accepts brain dump in chat
6. Stages 2–10 run automatically in sequence, output from each feeds next
7. Final output from Stage 10: complete Agent OS PRD document displayed in the skin
8. A Claude assistant is available inside the skin to help wire, debug, and adjust the prompt chain

## What Is NOT In This Build

- Code Module node (SPEC-003 in full PRD — later)
- AI node library beyond LLM + Prompt Template (SPEC-004 — later)
- Blueprint versioning (SPEC-005 — later)
- Self-healing agent (future)
- Compiler (future)
- Client deployment system (future)
- Stripe / billing (future)

---

# LAYER 3: SPECS

---

## SPEC-MVP-001: Repo + Docker Setup

### Purpose
New standalone repo. Activepieces running locally. Nothing built yet — just the engine running.

### Steps to Set Up (You Do These Before Coding Starts)

**Step 1: Create new GitHub repo**
```
Name: modular-pipeline-builder
Visibility: Private
Initialize with: README only
Clone to: wherever you keep projects locally
```

**Step 2: Create docker-compose.yml in repo root**
```yaml
version: "3.8"
services:
  activepieces:
    image: activepieces/activepieces:latest
    ports:
      - "8080:80"
    environment:
      - AP_ENGINE_EXECUTABLE_PATH=/usr/src/app/dist/packages/engine/main.js
      - AP_ENCRYPTION_KEY=changeme-32-char-encryption-key!!
      - AP_JWT_SECRET=changeme-jwt-secret-key-here-!!
      - AP_FRONTEND_URL=http://localhost:8080
      - AP_POSTGRES_DATABASE=activepieces
      - AP_POSTGRES_HOST=postgres
      - AP_POSTGRES_PORT=5432
      - AP_POSTGRES_USERNAME=activepieces
      - AP_POSTGRES_PASSWORD=changeme-db-password
      - AP_REDIS_URL=redis://redis:6379
      - AP_SANDBOX_RUN_TIME_SECONDS=30
      - AP_TELEMETRY_ENABLED=false
      - AP_TEMPLATES_SOURCE_URL=""
    depends_on:
      - postgres
      - redis
    volumes:
      - ap_data:/root/.activepieces

  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: activepieces
      POSTGRES_USER: activepieces
      POSTGRES_PASSWORD: changeme-db-password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    volumes:
      - redis_data:/data

volumes:
  ap_data:
  postgres_data:
  redis_data:
```

**Step 3: Start it**
```bash
docker compose up -d
```

**Step 4: Open `http://localhost:8080`**
- Create account (first account = admin)
- Confirm the dashboard loads

### Success Criteria
- Activepieces dashboard visible at `localhost:8080`
- Can create a blank flow
- No errors in `docker compose logs`

---

## SPEC-MVP-002: Skin Shell + Hinge

### Purpose
Thin React shell that wraps Activepieces. Looks like a real app. One env var flips between skin mode (what client/user sees) and builder mode (you see the full Activepieces UI).

### File Structure
```
skin/
├── .env.example
├── .env                        # gitignored
├── vite.config.ts
├── index.html
├── src/
│   ├── main.tsx
│   ├── App.tsx                 # Hinge logic lives here
│   ├── lib/
│   │   ├── api.ts              # All Activepieces API calls
│   │   └── types.ts            # TypeScript types
│   ├── pages/
│   │   └── PRDMakerPage.tsx    # The prompt chain UI
│   └── components/
│       ├── ChatBox.tsx         # Interactive chat for stages 0-1
│       ├── PipelineStatus.tsx  # Shows stage progress
│       └── OutputViewer.tsx    # Renders final PRD output
```

### The Hinge
`App.tsx` reads `VITE_BUILDER_MODE` at runtime:

```tsx
const BUILDER_MODE = import.meta.env.VITE_BUILDER_MODE === 'true'

export default function App() {
  if (BUILDER_MODE) {
    // Show full Activepieces iframe — you can build/edit
    return (
      <iframe
        src="http://localhost:8080"
        style={{ width: '100vw', height: '100vh', border: 'none' }}
      />
    )
  }
  // Show skin — user sees polished app
  return <PRDMakerPage />
}
```

`.env.example`:
```env
VITE_BUILDER_MODE=false
VITE_ACTIVEPIECES_URL=http://localhost:8080
VITE_AP_API_KEY=get-from-activepieces-settings
```

### How to Use the Hinge
- Edit pipelines: set `VITE_BUILDER_MODE=true` in `.env`, restart `npm run dev`
- User-facing mode: set `VITE_BUILDER_MODE=false`, restart
- Nothing in Activepieces changes. Only the UI shell switches.

### Commands
```bash
cd skin
npm install
npm run dev        # http://localhost:3000
```

### Success Criteria
- `VITE_BUILDER_MODE=true` → Activepieces fills the browser window
- `VITE_BUILDER_MODE=false` → PRDMakerPage renders
- Both point to the same Activepieces backend

---

## SPEC-MVP-003: The 11-Stage Prompt Chain Pipeline

### Purpose
Wire the 11 SKILL.md stages as an Activepieces flow. This is the whole point of the MVP.

### How the Pipeline Works

```
[Webhook Trigger]
      ↓
[Stage 0: Foundation Chat]     ← Interactive: asks 5 questions via ChatBox
      ↓
[Stage 1: Idea Capture Chat]   ← Interactive: accepts brain dump via ChatBox
      ↓
[Stage 2: Gap Analysis]        ← Automated: LLM call with Stage 1 output
      ↓
[Stage 3: Agent OS Structuring] ← Automated
      ↓
[Stage 4: Mechanism Extraction] ← Automated
      ↓
[Stage 5: Seven-Question Scaffolding] ← Automated
      ↓
[Stage 6: Layout + Style]       ← Automated
      ↓
[Stage 7: Phase Sequencing]     ← Automated
      ↓
[Stage 8: Protocol Injection]   ← Automated
      ↓
[Stage 9: Verification Setup]   ← Automated
      ↓
[Stage 10: Output Generator]    ← Automated → returns final PRD
      ↓
[Webhook Response → Skin]       ← OutputViewer renders the PRD
```

### Node Types Used (All Built Into Activepieces — No Custom Nodes)

| Node | Activepieces Type | Purpose |
|------|------------------|---------|
| Trigger | Webhook | Skin POSTs conversation state here |
| Stage 0–1 | Human Input / Loop back | Chat exchange until questions answered |
| Stage 2–10 | HTTP Request → Claude API | Each stage = one LLM call with stage prompt |
| Final | Webhook Response | Returns PRD JSON to skin |

### The Claude Node Configuration
Each Stage 2–10 node is an HTTP Request node hitting Claude:

```
URL: http://host.docker.internal:8888/api/claude/chat
Method: POST
Headers: Content-Type: application/json
Body:
{
  "system": "{{stage_N_system_prompt}}",
  "messages": [{"role": "user", "content": "{{previous_stage_output}}"}],
  "force_subscription": true
}
```

**Note:** Calls route through AutoForge's existing Claude proxy at port 8888 so subscription auth is already handled. No API key needed. No new auth code needed.

### Stage Prompt Sources
Each stage's system prompt = the content of the corresponding SKILL.md:

| Node | Prompt Source File |
|------|--------------------|
| Stage 0 | `docs/page-prds/prd-maker/skills-complete/stage-00-technical-foundation/SKILL.md` |
| Stage 1 | `docs/page-prds/prd-maker/skills-complete/stage-01-idea-capture/SKILL.md` |
| Stage 2 | `docs/page-prds/prd-maker/skills-complete/stage-02-gap-analysis/SKILL.md` |
| Stage 3 | `docs/page-prds/prd-maker/skills-complete/stage-03-agent-os-structuring/SKILL.md` |
| Stage 4 | `docs/page-prds/prd-maker/skills-complete/stage-04-mechanism-extraction/SKILL.md` |
| Stage 5 | `docs/page-prds/prd-maker/skills-complete/stage-05-seven-question-scaffolding/SKILL.md` |
| Stage 6 | `docs/page-prds/prd-maker/skills-complete/stage-06-layout-mockups-style/SKILL.md` |
| Stage 7 | `docs/page-prds/prd-maker/skills-complete/stage-07-phase-sequencing/SKILL.md` |
| Stage 8 | `docs/page-prds/prd-maker/skills-complete/stage-08-protocol-injection/SKILL.md` |
| Stage 9 | `docs/page-prds/prd-maker/skills-complete/stage-09-verification-agent-setup/SKILL.md` |
| Stage 10 | `docs/page-prds/prd-maker/skills-complete/stage-10-output-generator/SKILL.md` |

### Context Packet — Passed Between Stages
Every stage receives and extends the same JSON object:

```json
{
  "metadata": {
    "pipeline_version": "1.0.0",
    "current_stage": 2,
    "status": "in_progress"
  },
  "stage_0": { "platform_profile": {}, "tech_stack": {} },
  "stage_1": { "raw_input": "...", "word_count": 0 },
  "stage_2": { "gap_analysis": {}, "scope_contract": {} }
}
```

Each stage node takes the context packet as input, runs its LLM call, appends its output to the packet under `stage_N`, passes the full packet to the next node.

### Interactive Stages (0 and 1)

Stages 0 and 1 are not one-shot LLM calls — they're conversations. The mechanism:

1. Skin's `ChatBox.tsx` opens when pipeline starts
2. Stage 0 system prompt is injected — Claude asks the 5 foundation questions
3. User types answers in ChatBox
4. ChatBox sends answers back to webhook
5. Stage 0 node receives answers, validates, moves to Stage 1
6. Stage 1 repeats — Claude prompts for idea brain dump, user types it in
7. Once Stage 1 has `raw_input` with sufficient content, it advances automatically
8. Stages 2–10 run without any user input

**Implementation:** The ChatBox component maintains conversation history. Each user message POSTs to the pipeline webhook with `{"stage": 0, "message": "..."}`. The pipeline returns `{"reply": "...", "advance": false}` until all questions are answered, then `{"advance": true}` to move forward.

### Success Criteria
- Stages 0–1: user can have back-and-forth conversation in ChatBox
- Stage advancement: pipeline moves to Stage 2 automatically when Stage 1 is complete
- Stages 2–10: run without any user input, each output feeds the next
- Stage 10 output: full Agent OS PRD rendered in OutputViewer
- No node crashes the pipeline — errors show in PipelineStatus, don't kill the run

---

## SPEC-MVP-004: Claude Assistant Inside the Skin

### Purpose
A Claude assistant lives inside the skin to help you wire the pipeline, debug nodes, and adjust prompt chain settings. You talk to it in plain English. It knows the 11 stages and the Activepieces API.

### What It Can Do
- "Wire up Stage 3 to Stage 4" → gives you the exact node config to paste
- "Stage 5 is giving me empty output" → diagnoses and suggests a fix
- "What's the context packet look like after Stage 2?" → explains the JSON schema
- "Make Stage 1 ask one more question about budget" → generates updated prompt
- "Show me all 11 SKILL.md prompts" → surfaces them in the chat

### Implementation
This reuses AutoForge's existing `AssistantChat` component and WebSocket connection. No new backend code needed.

The assistant's system prompt (`assistant_system_prompt.md`) contains:
- Full description of the 11-stage pipeline architecture
- The context packet JSON schema
- Activepieces API reference (relevant endpoints only)
- All 11 SKILL.md file contents (injected at session start)
- Current pipeline state (what stages are wired, what's failing)

### File Location
```
skin/src/components/AssistantPanel.tsx   # Panel toggle (A key shortcut)
skin/assistant_system_prompt.md          # Context injected into assistant
```

### Success Criteria
- Assistant panel opens/closes with keyboard shortcut `A`
- Can describe a pipeline problem in plain English and get a working fix
- Assistant has read all 11 SKILL.md files — can reference any of them
- Fixes suggested by assistant can be applied by copy-pasting into Activepieces node config

---

# SETUP WALKTHROUGH — EXACT STEPS

## Before You Start a Coding Session

### Step 1: Create the GitHub Repo
1. Go to github.com → New repository
2. Name: `modular-pipeline-builder`
3. Private, initialize with README
4. Clone it locally

### Step 2: Start Activepieces
```bash
# In the repo root
# Paste the docker-compose.yml from SPEC-MVP-001
docker compose up -d

# Wait 60 seconds, then open:
# http://localhost:8080
# Create your admin account
```

### Step 3: Get Your API Key from Activepieces
```
Activepieces → Settings → API Keys → Generate Key
Copy it → paste into skin/.env as VITE_AP_API_KEY
```

### Step 4: Create the Skin
```bash
cd modular-pipeline-builder
npm create vite@latest skin -- --template react-ts
cd skin
npm install
npm install tailwindcss @tailwindcss/vite
npm run dev
# Opens at localhost:3000 (or 5173)
```

### Step 5: Start a Claude Code Session
In the repo, start a Claude Code session and say:

> "Read `docs/page-prds/pipeline-builder/PRD-mvp-minimal-build.md` in full.
> We are building the Pipeline Builder MVP.
> Activepieces is running at localhost:8080.
> Build SPEC-MVP-002 first: skin shell with hinge.
> Then SPEC-MVP-003: wire the 11-stage pipeline.
> Then SPEC-MVP-004: Claude assistant panel."

That's it. The agent builds from there.

---

## After the Build: Setting Up the Prompt Chain

Once all 4 SPECs are done and running, here's how you run the 11-stage PRD Maker for the first time:

### Step 1: Open the Skin
```
http://localhost:3000
VITE_BUILDER_MODE=false
```

### Step 2: Verify the Pipeline Is Wired
Flip `VITE_BUILDER_MODE=true`, open Activepieces, confirm all 11 stage nodes are connected and the webhook trigger is active.

### Step 3: Flip Back to Skin Mode
`VITE_BUILDER_MODE=false`, restart dev server.

### Step 4: Start the Chain
Click "Start PRD Maker" in the skin. ChatBox opens.

### Step 5: Answer Stage 0 (Foundation)
Claude asks 5 questions about your platform setup. Answer them. For the pipeline builder PRD run:
- New app? → Yes, greenfield
- Platform? → Web app
- Stack? → React + FastAPI + PostgreSQL (same as Activepieces skin)
- Repo? → New repo (already created)
- Deployment? → Self-hosted Docker

### Step 6: Answer Stage 1 (Idea Capture)
Claude prompts for a brain dump. Paste in the full concept from this chat — the skirt theory, the hinge, the modular nodes, the self-healing concept, the compiler vision, all of it. Don't filter. More is better.

### Step 7: Watch Stages 2–10 Run
PipelineStatus shows each stage completing. Takes 3–8 minutes total depending on Claude response times. Don't touch anything.

### Step 8: Read the Output
Stage 10 outputs a full Agent OS PRD in OutputViewer. This is the master document for building everything else.

### Step 9: Copy the PRD to the Repo
Save the Stage 10 output to:
```
docs/page-prds/pipeline-builder/PRD-full-build-generated.md
```
Commit it. This becomes the blueprint for the full build.

---

# TOKEN ESTIMATE FOR THIS BUILD

| SPEC | What Gets Built | Estimated Tokens |
|------|----------------|-----------------|
| SPEC-MVP-001 | docker-compose.yml only | ~5,000 |
| SPEC-MVP-002 | Skin shell + hinge (5 files) | ~25,000 |
| SPEC-MVP-003 | 11-node pipeline wired | ~40,000 |
| SPEC-MVP-004 | Assistant panel + system prompt | ~20,000 |
| **Total** | | **~90,000 tokens** |

One session. Well within a 200K context window. Likely under 60 minutes of wall-clock time with AI coding.

---

# SESSION START PROMPT

Copy this exactly to start your build session:

```
Read docs/page-prds/pipeline-builder/PRD-mvp-minimal-build.md in full.

We are building the Pipeline Builder MVP — the minimum system to run the 11-stage PRD Maker prompt chain.

Context:
- Activepieces is running at localhost:8080 in Docker (already set up)
- New repo: modular-pipeline-builder (already created on GitHub)
- AutoForge is running at localhost:8888 (use its Claude proxy for LLM calls)
- All 11 SKILL.md stage prompts are in: docs/page-prds/prd-maker/skills-complete/

Build order:
1. SPEC-MVP-002: Skin shell with hinge
2. SPEC-MVP-003: 11-stage pipeline wired in Activepieces
3. SPEC-MVP-004: Claude assistant panel

Start with SPEC-MVP-002.
```
