# PRD: Tool Execution Engine — Making YT Lab Tools Actually DO Things

**Created: 2026-03-14 — Session 10b**
**Status: Ready to build**
**Priority: HIGHEST — This is the owner's best product. Get it right.**
**Reference: YT Lab pipeline code in `server/services/sheet_blueprint.py`, `server/services/sheet_deployer.py`**

---

## What This Is

The YT Lab tool factory already creates incredible 8-12 step prompt chains from YouTube videos. The prompts are production-quality. The chain structure exists. The Google Sheets deployment works.

**The problem:** Every step is text generation only. Steps classified as `action` just generate text ABOUT doing the action — they don't actually DO it.

**This PRD:** Adds a Hybrid Execution Engine that makes every step type actually execute its intended action — text generation, API calls, browser automation, file creation, and tool-to-tool linking.

---

## Why It Matters

- Current state: Tools generate instructions (text). User must manually execute actions.
- After this: Tools execute end-to-end autonomously. Generation steps generate. Action steps act. API steps call APIs. Browser steps navigate and interact.
- The owner can then automate any process extracted from any YouTube video — fully end-to-end.
- 50 tools × 8-12 steps × linked chains = an automation operating system.

---

## Architecture: Hybrid Execution Engine

### Core Principle: Right Tool For Each Step Type

| Step Type | Execution Method | Token Cost | Speed |
|---|---|---|---|
| `generation` | Claude API (text in/text out) | Normal | Fast (5-30s) |
| `research` | Claude API + WebSearch/WebFetch | Normal | Medium (15-60s) |
| `api_call` (NEW) | Direct HTTP call to external API | Zero AI tokens | Instant |
| `browser_action` | Computer use (Claude) OR Playwright | High (computer use) or Zero (Playwright) | Slow (computer use) or Fast (Playwright) |
| `file_create` | Claude generates content → write to disk/Drive | Normal | Fast |
| `manual` | Pause chain, notify user, wait for approval | Zero | Human-dependent |
| `webhook` (NEW) | POST step output to a URL | Zero | Instant |

### Step Type Auto-Detection Enhancement

Current `classify_step()` in `sheet_blueprint.py` only classifies into 4 types. Expand to 7:

```
Keywords for classification:
- generation: "write", "create", "generate", "draft", "compose" (and no browser/API indicators)
- research: "research", "analyze", "find", "identify", "discover", "evaluate"
- api_call: "API", "endpoint", "POST", "GET", "webhook", any known API name
- browser_action: "navigate", "go to", "click", "upload", "log in", "sign in", "fill out", "submit", "open"
- file_create: "save as", "export", "download", "create file", "write to file", "PDF", "CSV", "HTML"
- manual: "review", "approve", "verify", "check", "confirm", "decide"
- webhook: "send to", "notify", "trigger", "post to webhook"
```

### Execution Modes

Each step in Chain Config gets a new column: **Execution Mode**

| Mode | Description |
|---|---|
| `ai_only` | Current behavior — send prompt to Claude/OpenAI, get text back |
| `ai_then_act` | AI generates the content, then an action handler executes it |
| `direct_action` | No AI needed — directly call API, navigate URL, write file |
| `computer_use` | Claude computer use — sees screen, interacts with UI |
| `human_checkpoint` | Pause and wait for user approval before continuing |

---

## Phase 1: Execution Engine Core (In AutoForge, Not Sheets)

### 1.1 Tool Runner Page

**What:** A new page in AutoForge UI that runs tool chains inside the app instead of Google Sheets.

**Why not keep it in Sheets?** The Apps Script Chain Runner is limited to OpenAI API calls. It can't do browser automation, file creation, or computer use. The AutoForge server has access to all of these.

**UI Layout:**
- Left panel: Chain steps (numbered, with status indicators)
- Center panel: Current step execution (showing prompt, output, actions taken)
- Right panel: Variables panel (editable inputs)
- Bottom bar: Run All / Run Step / Pause / Resume / Stop controls

**File:** `ui/src/pages/ToolRunnerPage.tsx`
**Route:** `/#/tools/:toolId/run`

**Note:** The `.claude/plans/tool-runner.md` plan already exists with 8 steps. This PRD supersedes it with the hybrid execution model.

### 1.2 Tool Runner Backend

**What:** A new service that orchestrates step execution based on step type and execution mode.

**File:** `server/services/tool_runner.py`

**Core class: `ToolRunner`**

```
class ToolRunner:
    def __init__(self, blueprint: SheetBlueprint, variables: dict, config: RunConfig)

    async def run_all(self) -> AsyncGenerator[StepResult]:
        for step in blueprint.steps:
            result = await self.execute_step(step)
            yield result
            # Pass output to next step as {{previousOutput}}

    async def execute_step(self, step: ChainConfigRow) -> StepResult:
        # Resolve variables and previousOutput in prompt template
        resolved_prompt = self.resolve_template(step.prompt_template)

        match step.execution_mode:
            case "ai_only":
                return await self._execute_ai(resolved_prompt, step)
            case "ai_then_act":
                ai_result = await self._execute_ai(resolved_prompt, step)
                return await self._execute_action(ai_result, step)
            case "direct_action":
                return await self._execute_action(resolved_prompt, step)
            case "computer_use":
                return await self._execute_computer_use(resolved_prompt, step)
            case "human_checkpoint":
                return await self._wait_for_human(resolved_prompt, step)
```

### 1.3 AI Execution Handler

**What:** Calls Claude API for text generation steps. Replaces the Google Sheets OpenAI call.

**Uses:** Existing `_call_via_sdk()` pattern from `yt_processor.py` — subscription auth, logging, rate_limit_event recovery.

**Model selection per step:** Each step already has a `recommended_model` field. Use it.

---

## Phase 2: Action Handlers

### 2.1 API Call Handler

**What:** Makes direct HTTP calls to external APIs using step output as the payload.

**How:**
1. Blueprint already detects which APIs are needed (13 known patterns)
2. API keys are stored in the tool's variables (from Setup tab)
3. Each known API gets an adapter:

```
API_ADAPTERS = {
    "openai": OpenAIAdapter,      # POST to chat completions
    "anthropic": AnthropicAdapter, # POST to messages
    "meta_marketing": MetaAdsAdapter,  # Facebook/Instagram ads
    "zapier": ZapierWebhookAdapter,    # POST to webhook URL
    "airtable": AirtableAdapter,       # CRUD on bases/tables
    "sendgrid": SendGridAdapter,       # Send emails
    "twilio": TwilioAdapter,           # Send SMS
    "stripe": StripeAdapter,           # Create payments/products
    "google_ads": GoogleAdsAdapter,    # Ad management
    "apollo": ApolloAdapter,           # Lead enrichment
    "instantly": InstantlyAdapter,     # Email outreach
    "phantombuster": PhantomBusterAdapter, # Social automation
    "canva": CanvaAdapter,             # Design generation
}
```

**Adapter interface:**
```
class APIAdapter:
    def __init__(self, api_key: str)
    async def execute(self, action: str, payload: dict) -> dict
    def validate_key(self) -> bool
```

**For unknown APIs:** Fall back to a generic HTTP adapter that accepts method, URL, headers, body.

### 2.2 Webhook Handler

**What:** POSTs step output to a webhook URL after completion.

**How:** Add a `webhook_url` field to step config. After step completes, POST the output JSON to that URL. Works with Zapier, Make, n8n, or any webhook receiver.

**This is the simplest win** — even without browser automation, webhooks let you trigger real-world actions through Zapier/Make's 5000+ app integrations.

### 2.3 File Creation Handler

**What:** Takes AI-generated content and writes it to actual files.

**Outputs:**
- Google Drive (auth already exists via `google_auth.py`)
- Local filesystem (project directory)
- Google Docs/Sheets (via existing Sheets API)

**How:** AI generates the content (HTML, CSV, markdown, etc.) as text. File handler detects the format from the step's `expected_output` field and writes it appropriately.

---

## Phase 3: Browser Automation

### 3.1 Computer Use Integration

**What:** For steps that need to interact with third-party websites — navigating, clicking, filling forms, uploading files.

**How Claude Computer Use works:**
1. A real browser window is opened (not headless — computer use needs screenshots)
2. Claude receives a screenshot of the current screen
3. Claude decides what to click/type/scroll
4. The action is executed
5. New screenshot is taken
6. Repeat until the task is complete

**Integration:**
- Each `browser_action` step gets its own computer use session
- The step's resolved prompt becomes the instruction
- Previous step's output provides context (e.g., "upload THIS ad copy")
- Computer use session runs until Claude signals completion
- Final state/output captured and passed to next step

**Requirements:**
- A display server (virtual display on Linux, or real display on Windows)
- Chrome/Chromium browser
- Claude computer use API access (check if available on subscription)

### 3.2 Playwright Fallback

**What:** For known, repeated browser tasks where computer use is overkill.

**When to use Playwright instead of computer use:**
- The target site is YOUR site (you control the DOM)
- The task is the same every time (upload file, fill form, click submit)
- Speed matters (Playwright is 10-100x faster than computer use)
- You want to save tokens

**How:** Each API adapter can optionally include Playwright scripts for common actions. For example, the MetaAdsAdapter might have a Playwright script for uploading ad creatives that runs in 5 seconds instead of 60 seconds of computer use.

**Playwright is already referenced in the AutoForge codebase** — the testing infrastructure uses it.

### 3.3 Browser Session Management

**What:** Manages browser instances for action steps.

- One browser instance per tool run (shared across steps)
- Login state persists across steps (login once, use for multiple steps)
- Cookie/session storage between runs (don't re-login every time)
- Screenshot capture at key moments (for audit trail)
- Error recovery: if a step fails, capture screenshot + HTML for debugging

---

## Phase 4: Tool Linking (Chain of Chains)

### 4.1 Tool Output → Tool Input

**What:** The output of one tool's final step becomes the input variables for another tool.

**How:**
- Each tool already has defined `user_variables` (from the Setup tab)
- Add a new config: `linked_tools` — maps output fields from one tool to input variables of another

```yaml
links:
  - source_tool: "listicle-forge"
    source_step: 8  # final step
    target_tool: "social-media-publisher"
    mappings:
      - source_field: "article_content"
        target_variable: "content_to_publish"
      - source_field: "target_keywords"
        target_variable: "hashtags"
```

### 4.2 Tool Chain Runner

**What:** Orchestrates running multiple tools in sequence.

**UI:** A new "Workflows" page where users can:
1. Drag tools into a sequence
2. Draw connections between tool outputs and inputs
3. Run the entire workflow end-to-end
4. See progress across all tools in the chain

**File:** `ui/src/pages/WorkflowsPage.tsx`

### 4.3 Conditional Branching

**What:** Route to different tools based on step output.

**Example:**
- Tool A: Research competitors → outputs competitor list
- IF competitors have strong social media → Route to Tool B (Social Strategy)
- IF competitors have weak social media → Route to Tool C (Social Domination)

**How:** Add `conditions` to tool links:
```yaml
links:
  - source_tool: "competitor-research"
    conditions:
      - field: "social_presence_score"
        operator: ">"
        value: 7
        target_tool: "social-strategy"
      - field: "social_presence_score"
        operator: "<="
        value: 7
        target_tool: "social-domination"
```

---

## Phase 5: Sub-Steps (Complex Steps)

### 5.1 Nested Step Execution

**What:** Each step can have sub-steps that execute internally before the step completes.

**Why:** Some steps are too complex for a single prompt. "Build a landing page" might need:
1. Generate copy
2. Generate HTML layout
3. Add styling
4. Upload images
5. Deploy to hosting

**How:** The `sub_steps` field already exists in the UI (shown in the step detail view). Make it functional:
- Sub-steps execute sequentially within the parent step
- Each sub-step has its own type, prompt, and execution mode
- Sub-step outputs chain together via `{{previousSubOutput}}`
- Parent step's output is the final sub-step's output

### 5.2 Step Templates (Reusable Complex Steps)

**What:** Pre-built step templates for common complex operations.

**Examples:**
- "Create and Deploy Landing Page" (5 sub-steps)
- "Research and Write Blog Post" (4 sub-steps)
- "Create and Schedule Social Media Campaign" (6 sub-steps)
- "Build Email Sequence" (4 sub-steps)

**Storage:** `server/templates/step_templates/` — YAML files defining sub-step chains

---

## Phase 6: Enhanced Google Sheets Chain Runner

### 6.1 Upgrade Apps Script

Even though the main execution moves to AutoForge, keep the Sheets Chain Runner as a lightweight option. Upgrades:

1. **Switch from OpenAI to Claude** — Use Anthropic API instead of GPT-4o-mini
2. **Add webhook output** — After each step, optionally POST to a webhook URL
3. **Add execution mode column** — Steps marked `manual` pause and highlight for user
4. **Better error handling** — Retry with exponential backoff, resume from failed step
5. **Progress dashboard** — Summary row at top showing completed/total/failed

### 6.2 Sheets ↔ AutoForge Sync

**What:** Tools deployed to Sheets can sync their chain config back to AutoForge for execution via the full engine.

**How:** A "Run in AutoForge" button in the Sheet that calls the AutoForge API with the tool ID, triggering the Tool Runner with the hybrid execution engine.

---

## Implementation Order and Dependencies

```
Phase 1 (Core) → Phase 2 (Actions) → Phase 3 (Browser) → Phase 4 (Linking) → Phase 5 (Sub-steps)
                                                           Phase 6 (Sheets upgrade, independent)
```

| Phase | Difficulty | Depends On | What It Gets You |
|---|---|---|---|
| 1: Tool Runner core | 5/10 | Nothing | Run chains in AutoForge with Claude instead of GPT-4o-mini |
| 2: Action handlers | 5/10 | Phase 1 | API calls, webhooks, file creation actually happen |
| 3: Browser automation | 7/10 | Phase 1 | Computer use + Playwright for web interactions |
| 4: Tool linking | 5/10 | Phase 1 | Chain tools together into workflows |
| 5: Sub-steps | 4/10 | Phase 1 | Complex steps with internal step chains |
| 6: Sheets upgrade | 3/10 | Nothing | Better Sheets runner (independent track) |

**Total estimated difficulty: ~29/60. Six phases. Each phase is a standalone commit.**

---

## Files To Create

| File | Phase | Purpose |
|---|---|---|
| `ui/src/pages/ToolRunnerPage.tsx` | 1 | Tool execution UI |
| `server/services/tool_runner.py` | 1 | Execution orchestrator |
| `server/routers/tool_runner.py` | 1 | REST + WebSocket endpoints |
| `server/services/api_adapters/` | 2 | Per-API adapter modules |
| `server/services/api_adapters/base.py` | 2 | Base adapter interface |
| `server/services/api_adapters/webhook.py` | 2 | Generic webhook handler |
| `server/services/api_adapters/meta.py` | 2 | Meta Marketing API |
| `server/services/api_adapters/zapier.py` | 2 | Zapier webhook |
| `server/services/browser_executor.py` | 3 | Computer use + Playwright orchestration |
| `ui/src/pages/WorkflowsPage.tsx` | 4 | Workflow builder UI |
| `server/services/workflow_runner.py` | 4 | Multi-tool orchestration |
| `server/templates/step_templates/` | 5 | Reusable complex step definitions |

## Files To Modify

| File | Phase | Changes |
|---|---|---|
| `server/services/sheet_blueprint.py` | 1 | Expand classify_step() to 7 types, add execution_mode |
| `server/services/sheet_deployer.py` | 6 | Upgrade Chain Runner Apps Script |
| `server/models/tool_factory.py` | 1 | Add ExecutionMode enum, expand StepType |
| `ui/src/App.tsx` | 1 | Add ToolRunner route |
| `server/routers/tool_factory.py` | 1 | Add run endpoints |

---

## Success Criteria

1. **Phase 1:** Tool Runner page loads a tool's chain and executes all `generation` steps using Claude (subscription auth)
2. **Phase 2:** A step that says "send this email via SendGrid" actually sends the email
3. **Phase 3:** A step that says "upload this ad to Meta Ads Manager" opens a browser and does it
4. **Phase 4:** Tool A's output feeds into Tool B's input automatically
5. **Phase 5:** A step with 5 sub-steps executes them all internally before completing
6. **End state:** User clicks "Run" on a linked workflow of 5 tools, walks away, comes back to everything done

---

## The Vision

50 tools × 8-12 steps × linked workflows × sub-steps × hybrid execution =
An automation operating system that can replicate any process from any YouTube video,
execute it end-to-end without human intervention, and chain multiple processes together
into complex business workflows.

Built by one person with a $200/month subscription and a really good PRD maker.
