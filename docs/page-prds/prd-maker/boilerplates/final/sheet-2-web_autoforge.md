# Exact Reality Sheet 2: web_autoforge (AutoForge SDK Subscription Bolt-On)

> **Variant**: Base boilerplate + modular AutoForge connection
> **Boilerplate**: DevToDollars Web-BoilerPlate-D2D (Next.js 16 + Supabase + Stripe + Tailwind v4 + PostHog)
> **What is active**: UI framework, styling, landing page components + AutoForge SDK subscription connection
> **What is dormant**: Database, Auth, Payments, Analytics -- same as Sheet 1
> **What is new vs Sheet 1**: AutoForge bolted on as URL/page endpoint(s) using SDK subscription model (NOT API key)
> **Design philosophy**: "Guitar + amp" -- modular, minimal connections, easy to disconnect without breaking anything
>
> **This is a DELTA document.** This sheet inherits ALL statuses from Sheet 1 (web_base).
> Only rules that CHANGE from Sheet 1 are documented below. For all unchanged rules, see Sheet 1.

---

## Boilerplate Identity

| Field | Value |
|-------|-------|
| **Base** | Everything from Sheet 1 (web_base) -- Next.js 16 + React 19 + TypeScript + Tailwind CSS v4 |
| **AutoForge Connection** | SDK subscription model via `~/.claude/.credentials.json` (OAuth) |
| **Auth Model** | `force_subscription=True` -- clears `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` at runtime |
| **Permission Mode** | `"acceptEdits"` + settings file (NEVER `"bypassPermissions"` -- crashes Bun runtime on Windows, exit code 3) |
| **Connection Pattern** | Tool pages at `app/tools/[tool-name]/page.tsx` -- one page per AutoForge tool |
| **Disconnection Cost** | Delete `app/tools/`, remove nav link, remove `AUTOFORGE_URL` env var. Nothing else breaks. |

---

## AutoForge Connection Spec

### Connection Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  D2D Boilerplate (Next.js)                                      │
│                                                                  │
│  app/                                                            │
│    page.tsx (landing)              <-- unchanged from Sheet 1    │
│    account/page.tsx                <-- unchanged from Sheet 1    │
│    auth/[id]/page.tsx              <-- unchanged from Sheet 1    │
│    tools/                          <-- NEW: AutoForge pages      │
│      [tool-name]/page.tsx          <-- each tool = 1 route       │
│                                                                  │
│  No new npm dependencies. No new database tables.                │
│  AutoForge runs on its own server (port 8888).                   │
│  The boilerplate just provides URL endpoints.                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  AutoForge Server (Python, port 8888)                            │
│                                                                  │
│  - Runs independently, own process, own lifecycle                │
│  - Claude Agent SDK with subscription auth                       │
│  - Builds features via MCP feature server                        │
│  - Uses boilerplate's UI components for visual consistency       │
│  - Does NOT read/write boilerplate's database                    │
│  - Does NOT use boilerplate's auth system                        │
│  - Does NOT interact with Stripe or PostHog                      │
└─────────────────────────────────────────────────────────────────┘
```

### SDK Subscription Model (NOT API Key)

Per `CLAUDE.md` and `registry.py` line ~792 (`get_effective_sdk_env()`):

| Setting | Value | Why |
|---------|-------|-----|
| `force_subscription` | `True` | Always use subscription auth. Never burns API credits on subscription models. |
| `ANTHROPIC_API_KEY` | Cleared at runtime by `get_effective_sdk_env()` | Forces CLI to fall back to OAuth credentials instead of API key |
| `ANTHROPIC_AUTH_TOKEN` | Cleared at runtime by `get_effective_sdk_env()` | Same reason -- forces OAuth fallback |
| Credential source | `~/.claude/.credentials.json` | Subscription OAuth tokens from Claude Max subscription |
| `permission_mode` | `"acceptEdits"` | NEVER `"bypassPermissions"` -- causes Bun runtime crash on Windows (exit code 3). 20+ agents failed to diagnose this. |
| Settings file | `{"permissions": {"defaultMode": "acceptEdits", "allow": []}}` | Required alongside permission_mode for SDK client to work |

### SDK Client Pattern (3 Mandatory Safeguards)

Any code that calls AutoForge's SDK must implement these three patterns. Reference implementation: `server/services/yt_processor.py._call_via_sdk()`.

**1. Permission mode**: Use `"acceptEdits"` + settings file. Never `"bypassPermissions"`.

**2. Real-time logging**: Every `_call_via_sdk()` call must have a `_log()` helper writing to BOTH `logger.info()` AND the `on_progress()` callback. SDK calls take 120-200 seconds. Without streaming logs to the browser, failures are undiagnosable.

**3. Rate limit exception recovery**: The SDK throws `"Unknown message type: rate_limit_event"` as an EXCEPTION after the full response has been collected. Always wrap `receive_response()` in try/except and recover the text:

```python
try:
    async for msg in client.receive_response():
        # ... collect full_text ...
except Exception as exc:
    if full_text.strip() and "unknown message type" in str(exc).lower():
        pass  # Use the text we already have
    elif full_text.strip():
        pass  # Try to use what we have
    else:
        raise  # No text -- re-raise
```

### What "Bolting On" Means

AutoForge is NOT integrated into the boilerplate's data layer. It is a separate service:

1. **Runs independently** on port 8888 (its own Python server, own process)
2. **Builds pages** that get deployed into the boilerplate's `app/tools/` directory
3. **Uses the boilerplate's UI components** (shadcn/ui, Tailwind, Lucide icons) for visual consistency
4. **Does NOT touch** the boilerplate's auth, database, or payment systems
5. **Can be removed** by deleting `app/tools/` -- nothing else breaks

### Minimum Connection Points

| Connection | What | Files Touched |
|------------|------|---------------|
| Route | `app/tools/[name]/page.tsx` | 1 new file per tool page |
| Nav link | Optional link in `Navbar.tsx` to `/tools` | 1 line in existing file |
| Env var | `AUTOFORGE_URL=http://localhost:8888` (optional, for API calls from tool pages) | `.env.example` only |

**Total existing files modified: 2** (Navbar.tsx + .env.example)
**Total files added: 1 per tool page**
**Total npm dependencies added: 0**
**Total database migrations: 0**

---

## Changed Rules vs Sheet 1

This section uses the same table format as Sheet 5. Only rules whose STATUS changes from Sheet 1 are listed. Categories with zero changes are noted but not expanded.

---

### PART 1: Martin's Structural Checklist -- Changed Rules Only

---

#### Category: Stack (Mandatory) -- 1 rule changed

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| S8 | No custom backend | STANDARD | No custom server-side code; all backend via BaaS or serverless | HANDLED | AutoForge runs as a separate service on port 8888. The boilerplate itself still has no custom Express/FastAPI backend. AutoForge is a bolt-on service, not an embedded backend. The Next.js app's backend remains Supabase serverless (dormant) | None -- AutoForge is external. The boilerplate's "no custom backend" principle is preserved because AutoForge runs outside the boilerplate process |

**Sheet 1 status for S8 was**: PRESENT_NOT_WIRED (Supabase Edge Functions exist but need config)
**Sheet 2 status**: HANDLED (AutoForge provides a working backend service, even though Supabase remains dormant)

---

#### Category: File Structure -- 1 rule changed

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| FS2 | Feature folders for grouping | STANDARD | Related components in `components/[FeatureName]/` directories | HANDLED | Existing: `components/landing/`, `components/misc/`, `components/ui/`, `components/icons/`. New: `app/tools/` for AutoForge-built tool pages | None -- `app/tools/` follows existing directory pattern. Agent creates tool-specific subdirectories as `app/tools/[tool-name]/` |

**Sheet 1 status**: HANDLED (same). No actual status change -- the directory structure just gains a new folder. Included for completeness.

---

#### Category: Configuration / Module System -- 1 rule changed

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| CM10 | Optional AI SDK import | STANDARD | If using AI SDK, add via standard dependency management | PARTIAL | AutoForge uses the Claude Agent SDK on its own Python server. The Next.js app does NOT import any AI SDK -- it communicates with AutoForge via HTTP/WebSocket to `localhost:8888`. No `ai` or `@anthropic-ai/sdk` package in `package.json` | If tool pages need to call AutoForge's API directly, agent adds a thin API client to `utils/autoforge.ts`. No AI SDK needed in the Next.js app -- AutoForge handles all AI calls server-side |

**Sheet 1 status**: NOT_PRESENT (no AI SDK at all)
**Sheet 2 status**: PARTIAL (AI SDK exists in the system via AutoForge, but not in the Next.js app itself)

---

#### Categories with NO changes from Sheet 1

The following Martin's Checklist categories have ZERO status changes in Sheet 2. See Sheet 1 for all rules in these categories:

- **Authentication Context** (AC1-AC7) -- No changes. Auth remains dormant. AutoForge does not use the boilerplate's auth.
- **Theme Context / Dark Mode** (TC1-TC4) -- No changes.
- **Route Guards** (RG1-RG5) -- No changes. Tool pages can be public since auth is dormant.
- **Data Structure** (DS1-DS4) -- No changes. AutoForge does not add database tables.
- **Data Service Layer** (DSL1-DSL4) -- No changes.
- **Data/API Patterns** (DAP1-DAP9) -- No changes.
- **Authentication/Security** (AS1-AS7) -- No changes.
- **Routing Structure** (RS1-RS4) -- No changes. New tool routes follow existing Next.js App Router convention.
- **Database/Storage** (DBS1-DBS3) -- No changes.
- **Error Handling** (EH1-EH4) -- No changes.
- **Pagination** (P1-P4) -- No changes.
- **Deployment/Hosting** (DH1-DH5) -- No changes.
- **UX Patterns** (UX1-UX23) -- No changes.
- **Build Instructions** (BI1-BI30) -- No changes.
- **Miscellaneous** (MISC1-MISC18) -- No changes.
- **Banned Patterns** (BAN1-BAN43) -- No changes.

---

### PART 2: Industry Standards Supplement -- Changed Rules Only

---

#### IS Category 2: Config Externalization -- 1 rule changed

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 208 | No hardcoded environment URLs | CRITICAL | All URLs from env vars; no hardcoded http:// in source | HANDLED | Sheet 1 has `NEXT_PUBLIC_SITE_URL`, Supabase URL via env var. Sheet 2 adds `AUTOFORGE_URL=http://localhost:8888` to `.env.example`. All AutoForge endpoint references must use this env var, not hardcoded URLs | Agent must use `process.env.AUTOFORGE_URL` (or `NEXT_PUBLIC_AUTOFORGE_URL` if called client-side) for any AutoForge API calls. Never hardcode `localhost:8888` |

**Sheet 1 status**: HANDLED (same status, just one more env var to manage). Included because the agent needs to know about the new env var.

---

#### IS Categories with NO changes from Sheet 1

The following Industry Standards categories have ZERO status changes in Sheet 2. See Sheet 1 for all rules:

- **IS Category 1: Internationalization (i18n)** (200-207) -- No changes.
- **IS Category 3: Environment Parity** (215-220) -- No changes.
- **IS Category 4: Logging Strategy** (221-228) -- No changes. AutoForge has its own logging; it does not affect the boilerplate's logging posture.
- **IS Category 5: Dependency Management** (229-235) -- No changes. No new npm dependencies.
- **IS Category 6: Legal/Compliance** (236-243) -- No changes.
- **IS Category 7: Deep Accessibility (WCAG AA)** (244-253) -- No changes.
- **IS Category 8: API Versioning** (254-258) -- No changes.
- **IS Category 9: Architecture Decision Records** (259-263) -- No changes.
- **IS Category 10: Error Recovery / Retry Strategy** (264-270) -- No changes. AutoForge handles its own retry logic internally.

---

### PART 3: Mechanism Categories -- 2 categories changed

| ID | Category | Sheet 1 Status | Sheet 2 Status | What Changed | Agent Action Required |
|----|----------|---------------|---------------|-------------|----------------------|
| H | Integration | PRESENT_NOT_WIRED | PARTIAL | AutoForge is now an active external integration (running on port 8888). Stripe, PostHog, Loops remain dormant. One integration active out of four coded. | Agent must add `AUTOFORGE_URL` to `.env.example`. If tool pages make API calls to AutoForge, create `utils/autoforge.ts` as a thin client |
| N | Infrastructure | PRESENT_NOT_WIRED | PARTIAL | AutoForge server is a new infrastructure component. Runs as a separate Python process on port 8888. Supabase, Stripe, PostHog, Vercel infra remains dormant/unconfigured. | Agent should document AutoForge as an infrastructure dependency in README. Start command: `start_ui.bat` (Windows) or `./start_ui.sh` (macOS/Linux) |

**Unchanged mechanism categories**: A, B, C, D, E, F, G, I, J, K, L, M -- all retain Sheet 1 status.

---

## AutoForge-Specific Rules (New for Sheet 2)

These rules do not exist in Sheet 1. They apply ONLY when the AutoForge bolt-on is present.

| # | Rule | Severity | Spec | Status | Implementation | Agent Action Required |
|---|------|----------|------|--------|---------------|----------------------|
| AF1 | Subscription auth only | CRITICAL | All Claude model calls use subscription auth (`force_subscription=True`). Never use API keys for subscription models. `get_effective_sdk_env()` in `registry.py` is the single source of truth. | MANDATORY | `registry.py` line ~792 clears `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` when `force_subscription=True` | Agent must NEVER set `ANTHROPIC_API_KEY` for Claude subscription models. If API key is set, the user burns credits on models covered by their subscription |
| AF2 | Permission mode acceptEdits | CRITICAL | SDK client uses `permission_mode="acceptEdits"` with a settings file. NEVER use `"bypassPermissions"` -- it causes Bun runtime crash on Windows (exit code 3). | MANDATORY | Copy pattern from `workspace_chat_session.py` line ~565 or `client.py`. Settings file: `{"permissions": {"defaultMode": "acceptEdits", "allow": []}}` | Agent must use `"acceptEdits"` for any new SDK client. 20+ agents failed before this was diagnosed |
| AF3 | Rate limit exception recovery | CRITICAL | `receive_response()` loop wrapped in try/except. The SDK throws `"Unknown message type: rate_limit_event"` as an exception AFTER the full response is collected. Must recover the text, not discard it. | MANDATORY | Reference: `server/services/yt_processor.py._call_via_sdk()` | Agent must wrap every `receive_response()` in try/except with text recovery logic |
| AF4 | Tool pages in app/tools/ | STANDARD | AutoForge-built tool pages live in `app/tools/[tool-name]/page.tsx`. One page per tool. Never place AutoForge pages in the root `app/` directory or mix with boilerplate pages. | MANDATORY | `app/tools/` directory | Agent creates one subdirectory per tool. Each has its own `page.tsx` |
| AF5 | Modular disconnect | STANDARD | Removing AutoForge must require ONLY: (1) delete `app/tools/`, (2) remove nav link from Navbar, (3) remove `AUTOFORGE_URL` env var. No other file should break. | MANDATORY | Verify by checking: does the app build and run after deleting `app/tools/`? | Agent must never create dependencies from non-tool code to tool-page code. Imports flow ONE direction: tool pages import from boilerplate, never the reverse |
| AF6 | Real-time progress logging | STANDARD | Every SDK `_call_via_sdk()` call has a `_log()` helper that writes to BOTH `logger.info()` AND the `on_progress()` callback. SDK calls take 120-200s. Without streaming logs, failures are undiagnosable. | MANDATORY | Reference: `server/services/yt_processor.py._call_via_sdk()` | Agent must implement dual logging for any new SDK client |

---

## Summary: All Unchanged Rules

Every rule not listed above retains its Sheet 1 status exactly. The AutoForge bolt-on is intentionally minimal:

- **No new database tables** -- AutoForge uses its own SQLite (`features.db`) in `.autoforge/`
- **No new auth flows** -- AutoForge uses SDK subscription auth, not the boilerplate's Supabase Auth
- **No new npm dependencies** added to `package.json`
- **No modifications** to the Supabase schema, Stripe integration, or PostHog setup
- **No modifications** to any existing component except optionally Navbar (one link)

---

## Summary Statistics (Delta from Sheet 1)

| Status | Sheet 1 Count | Sheet 2 Count | Delta | What Changed |
|--------|--------------|--------------|-------|-------------|
| HANDLED | 41 | 42 | +1 | S8 (No custom backend): AutoForge provides working backend service |
| PRESENT_NOT_WIRED | 40 | 38 | -2 | H (Integration) and N (Infrastructure) promoted to PARTIAL |
| PARTIAL | 23 | 25 | +2 | H, N promoted from PRESENT_NOT_WIRED; CM10 promoted from NOT_PRESENT |
| NOT_PRESENT | 65 | 64 | -1 | CM10 promoted to PARTIAL |
| N/A | 7 | 7 | 0 | No change |
| **New AF rules** | 0 | 6 | +6 | AF1-AF6: AutoForge-specific rules |

**The delta is intentionally tiny.** AutoForge is bolted on, not welded in. The boilerplate's surface area changes by 3 rule statuses and gains 6 new AutoForge-specific rules.

---

## What an Agent Needs to Know

1. **This is Sheet 1 + a bolt-on.** Everything from Sheet 1 applies. Read Sheet 1 first.
2. **Do NOT wire up Supabase/Stripe/PostHog** -- they stay dormant in this variant, same as Sheet 1.
3. **AutoForge pages go in `app/tools/`** -- one page per tool, never in root `app/`.
4. **Use SDK subscription auth** -- `force_subscription=True`. Never API keys for subscription models. If you set an API key, the user burns credits.
5. **Use `permission_mode="acceptEdits"`** -- NEVER `"bypassPermissions"`. It crashes on Windows. This bug took 20+ agents to diagnose.
6. **Wrap `receive_response()` in try/except** -- the `rate_limit_event` exception is expected and contains a complete response that must be recovered.
7. **Stream progress logs** -- SDK calls take 2-3 minutes. Without real-time logs to the browser, nobody can diagnose failures.
8. **The boilerplate's UI components are available** -- tool pages use shadcn/ui, Tailwind, Lucide icons for visual consistency.
9. **To disconnect AutoForge**: delete `app/tools/`, remove nav link, remove `AUTOFORGE_URL` env var. Three steps. Nothing else breaks.
10. **Import direction is one-way**: tool pages may import from the boilerplate (components, utils, styles). The boilerplate must NEVER import from `app/tools/`.
