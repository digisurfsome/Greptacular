# TASK: Generate Bridge Website Spec XML

## What You're Doing

Converting the website-side features (Features 1-9, 11) from the bridge handoff into a generated PRD XML spec. This is a straightforward conversion job — the handoff document has all the details, you just need to reformat it into the XML spec format that AutoForge understands.

## Why This Is Needed

The bridge handoff (`boilerplate-autoforge-bridge-handoff.md`) describes features split across two projects. Features 1-9 and 11 are for the **website** (autoforge.com, built on the Gen-Ai SaaS boilerplate). Feature 10 is for AutoForge itself (separate project, already handled). The website features were never converted to an XML spec, so there's no `app_spec.txt` for AutoForge to consume.

## Exact Steps

### Step 1: Read the context document
```
Read file: .claude/autoforge-prd-context.md
```
Read the ENTIRE file. It contains the XML format, coding standards, quality checklist, and conversion instructions. This is your reference for how the output must be structured.

### Step 2: Read an existing generated spec for reference
```
Read file: .claude/generated-prds/self-deploy-vps-spec.xml
```
This is the other website PRD that was already converted. Use it as a style/format reference. Your output should look like this structurally.

### Step 3: Read the bridge handoff
```
Read file: .claude/handoffs/boilerplate-autoforge-bridge-handoff.md
```
Read the ENTIRE file. It's long. You need ALL of it.

### Step 4: Extract ONLY the website-side features

From the bridge handoff, you are converting these features:

| Feature # | Name | What It Does |
|-----------|------|-------------|
| 1 | Build Orchestrator Service | VM pool management, build assignment, health monitoring, teardown, queue |
| 2 | WebSocket Proxy | Real-time progress streaming from worker to browser |
| 3 | Build Artifact Delivery | Package project files to cloud storage, download links |
| 4 | Multi-Tenant Isolation | Per-user build isolation, data separation, resource limits |
| 5 | Authentication Bridge | Supabase JWT validation, per-build auth tokens |
| 6 | Build Dashboard | Frontend UI for build status, logs, progress, history |
| 7 | Build Callbacks | Worker-to-web-app notifications (progress, completion, failure) |
| 8 | Worker Health Monitoring | Detect crashed/stuck builds, auto-recovery |
| 9 | Spec Creation Chat (SaaS) | Spec creation through proxy to worker |
| 11 | Project Expand & Assistant (SaaS) | Expand/assistant through proxy to worker |

**DO NOT include Feature 10** (AutoForge Server Modifications). That belongs to the other project.

### Step 5: Convert to XML spec format

Follow the exact XML format from the context doc (Step 1). Key points:

- **project_name:** `autoforge-website-bridge`
- **technology_stack:** This is a website built on the Gen-Ai SaaS boilerplate (React 18 + Vite + Tailwind + Supabase Auth + Stripe). NOT the AutoForge Python/FastAPI stack.
- **feature_count:** Should be 15-20 atomic features broken out from the 10 bridge features above. Some bridge features (like Build Orchestrator) are too big for one agent session and need to be split into 2-3 smaller features.
- **dependencies:** Foundation first (database tables, auth), then services, then UI.
- **database_schema:** Include the SQL schemas from the handoff (builds, build_workers, user_specs tables). These go into Supabase, not SQLite.
- The handoff has detailed SQL schemas, API endpoint definitions, and implementation guidance — use all of it.

### Step 6: Save the output
```
Save to: .claude/generated-prds/bridge-website-spec.xml
```

### Step 7: Verify quality

Run through these checks before saving:
- [ ] Every feature is completable in one agent session (30-60 min)
- [ ] Steps are specific ("Create file X with function Y"), not vague
- [ ] Dependencies form a DAG with no cycles
- [ ] Foundation features (DB tables, auth middleware) have no dependencies
- [ ] Feature 10 (AutoForge modifications) is NOT included
- [ ] The tech stack reflects the Gen-Ai boilerplate (React/Supabase/Stripe), not AutoForge (Python/FastAPI)
- [ ] SQL schemas from the handoff are included in the database_schema section
- [ ] API endpoints from the handoff are listed in the api_endpoints_summary

### Step 8: Update the landing page build doc

After generating the spec, update `.claude/landing-page-build.md` to reference the new file:
- Change "No generated PRD yet" to the actual file path
- Note that the spec is now ready to feed to AutoForge

## What NOT To Do

- Do NOT modify the bridge handoff file itself
- Do NOT include Feature 10 (AutoForge Server Modifications)
- Do NOT use the AutoForge Python/FastAPI stack — this is a Gen-Ai boilerplate app (React + Supabase)
- Do NOT create features that are too large for one agent session — split big ones
- Do NOT skip reading the context doc — it has the exact XML format you must follow
