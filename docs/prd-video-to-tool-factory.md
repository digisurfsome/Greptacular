# Video-to-Tool Factory Pipeline -- Product Requirements Document

## Document Info

| Field        | Value                                    |
|--------------|------------------------------------------|
| Author       | AutoForge Team                           |
| Status       | Draft                                    |
| Created      | 2026-03-11                               |
| Last Updated | 2026-03-11                               |
| Target       | YT Strategy Lab + Google Sheets Platform |

---

## 1. Problem Statement

### What Happens Today

YT Strategy Lab already does something powerful: it takes a YouTube video, extracts the transcript, and uses AI to produce a structured project with numbered strategy steps. Each step has a title, description, prompt, expected output, model assignment, and sub-steps (`YTStrategyStep[]`).

But then... nothing. The user reads the blueprints on screen and has to manually build the tool that executes the strategy. That manual step kills the entire pipeline. The extraction is fast (minutes), but turning it into a working tool takes hours or days of custom work.

Meanwhile, the owner has a separate proven pattern: the **Google Sheets Tool Factory**. A Google Sheet serves as a no-code framework where each row in a "Chain Config" tab defines one prompt chain step. An Apps Script backend calls the Claude API, and a Web App frontend renders the steps, runs them in sequence, and feeds each output into the next input. The Build Planner Google Sheet was built using this pattern in approximately 10 minutes.

### The Gap

These two systems are disconnected. The extraction pipeline produces structured data (`YTStrategyStep[]`) that maps almost 1:1 to the Chain Config rows in a Google Sheet tool. But there is no bridge. The transformation is done by hand.

### What We Want Instead

**Every video that enters YT Strategy Lab should be able to produce a fully functional Google Sheet tool as its output.** Not just blueprints -- a working, runnable prompt-chain tool that the user can open, add their API keys, and start executing immediately.

```
YouTube Video
    |
    v
YT Strategy Lab (already built)
    |
    v
YTStrategyStep[] (structured data -- already produced)
    |
    v
*** THE GAP WE ARE FILLING ***
    |
    v
Google Sheet Tool (Chain Config populated, Apps Script deployed, ready to run)
    |
    v
User adds API keys, clicks "Run" -- strategy executes step by step
```

---

## 2. Pipeline Architecture

### Full Pipeline Overview

```
+-------------------+     +----------------------+     +------------------------+
|  STAGE 1          |     |  STAGE 2             |     |  STAGE 3               |
|  Video Ingestion  | --> |  Strategy Extraction | --> |  Sheet Blueprint       |
|  (ALREADY BUILT)  |     |  (ALREADY BUILT)     |     |  Generation (NEW)      |
+-------------------+     +----------------------+     +------------------------+
                                                               |
                                                               v
                          +----------------------+     +------------------------+
                          |  STAGE 5             |     |  STAGE 4               |
                          |  Tool Activation     | <-- |  Sheet Deployment      |
                          |  (NEW)               |     |  (NEW)                 |
                          +----------------------+     +------------------------+
```

### Stage Breakdown

| Stage | Name                   | Status        | Input                        | Output                              |
|-------|------------------------|---------------|------------------------------|--------------------------------------|
| 1     | Video Ingestion        | ALREADY BUILT | YouTube URL                  | Transcript, metadata, screenshots   |
| 2     | Strategy Extraction    | ALREADY BUILT | Transcript + user context    | `YTStrategyStep[]`                  |
| 3     | Sheet Blueprint Gen    | **NEW**       | `YTStrategyStep[]`           | Sheet Blueprint JSON                |
| 4     | Sheet Deployment       | **NEW**       | Sheet Blueprint JSON         | Live Google Sheet + Web App URL     |
| 5     | Tool Activation        | **NEW**       | Live Sheet + user API keys   | Running prompt chain tool           |

---

## 3. The Transformation Engine (Stage 3)

This is the core intellectual work. Converting an array of `YTStrategyStep` objects into a Google Sheet tool configuration.

### 3.1 Input: The YTStrategyStep Type

From `ui/src/lib/types.ts`:

```typescript
interface YTStrategyStep {
  id: string
  projectId: string
  order: number
  title: string
  description: string        // "What To Do" -- the human-readable instruction
  prompt: string             // The AI prompt for this step
  expectedOutput: string     // What the step should produce
  notes: string              // Additional context, enhancements
  aiOutput: string           // Results from execution (initially empty)
  status: 'pending' | 'in_progress' | 'complete'
  model: string              // e.g., "Sonnet 4.6 Balanced"
  role: string               // Agent role assignment
  subSteps: YTStrategySubStep[]
}
```

### 3.2 Output: Sheet Blueprint JSON

The transformation engine produces a JSON document that fully describes the Google Sheet to be created:

```json
{
  "metadata": {
    "source_video": "https://youtube.com/watch?v=...",
    "project_name": "GTM Engineering Pipeline",
    "generated_at": "2026-03-11T14:30:00Z",
    "total_steps": 10,
    "api_keys_required": ["perplexity", "meta_ads", "apollo", "instantly"],
    "estimated_run_time": "2-4 hours"
  },
  "tabs": {
    "setup": { ... },
    "chain_config": { ... },
    "results": { ... },
    "history": { ... }
  },
  "apps_script": {
    "web_app_html": "...",
    "server_code": "...",
    "config": { ... }
  }
}
```

### 3.3 Transformation Rules

Each `YTStrategyStep` maps to a row in the Chain Config tab. The mapping is:

```
YTStrategyStep Field        Chain Config Column
-----------------------     ----------------------------
order                   --> Step Number
title                   --> Step Name
description             --> What This Step Does
prompt                  --> Prompt Template
expectedOutput          --> Expected Output Description
model                   --> Model Assignment
notes                   --> Notes / Context
subSteps[].description  --> Helper Instructions (concatenated)
[derived]               --> Step Type (research | generation | action)
[derived]               --> Input Source (manual | previous_step_N)
[derived]               --> Required API Keys
[derived]               --> {{previousOutput}} injection points
```

### 3.4 Step Type Classification

The engine must classify each step into one of three types. Classification drives how the prompt is structured in the generated Sheet.

```
+------------------+----------------------------------------+---------------------------+
| Step Type        | Detection Signals                      | Prompt Treatment          |
+------------------+----------------------------------------+---------------------------+
| RESEARCH         | Keywords: "research", "find", "search",| Add search/scrape tool    |
|                  | "analyze", "scrape", "discover",       | instructions. Output      |
|                  | "identify", "study", "investigate"     | format: structured data.  |
+------------------+----------------------------------------+---------------------------+
| GENERATION       | Keywords: "create", "generate", "write"| Structure as Claude       |
|                  | "build", "design", "produce", "draft", | prompt with clear I/O.    |
|                  | "compose", "craft"                     | Add {{previousOutput}}.   |
+------------------+----------------------------------------+---------------------------+
| ACTION           | Keywords: "upload", "deploy", "send",  | Generate API call         |
|                  | "submit", "configure", "connect",      | template with placeholder |
|                  | "publish", "launch", "install"         | variables and auth.       |
+------------------+----------------------------------------+---------------------------+
| MANUAL           | Keywords: "sign up", "create account", | Flag as manual step.      |
|                  | "set up [service]", "open browser"     | Provide instructions,     |
|                  | OR requires human judgment/approval    | not automation.           |
+------------------+----------------------------------------+---------------------------+
```

### 3.5 Input/Output Chaining

The engine determines how each step receives its input:

```
Step 1: Input = MANUAL (user provides initial context)
Step 2: Input = {{step_1_output}}    (ICP research feeds ad copy generation)
Step 3: Input = {{step_2_output}}    (ad copy feeds bulk generation)
Step 4: Input = {{step_3_output}}    (generated ads feed upload)
...

Detection logic:
  1. If step.prompt references output of a prior step explicitly --> chain to that step
  2. If step.description says "using the [X] from step N"      --> chain to step N
  3. If step.order > 1 AND no explicit reference                --> chain to step.order - 1 (default)
  4. If step is clearly independent (setup, config)             --> input = MANUAL
```

The chaining is injected into the prompt template as a `{{previousOutput}}` variable that the Apps Script runtime replaces at execution time with the actual output from the prior step.

### 3.6 Smart Prompt Conversion

Video-extracted prompts are often conversational or high-level. The engine refines them:

**For RESEARCH steps:**
```
ORIGINAL (from video):
  "Research ICP pain points using Reddit and forums"

CONVERTED (for Chain Config):
  "You are a market researcher. Search for pain points experienced by
   {{target_audience}} in the {{niche}} space.

   Sources to analyze:
   - Reddit threads in relevant subreddits
   - Forum posts on industry sites
   - Review sites and complaint boards

   For each pain point found, extract:
   1. The exact language customers use (verbatim quotes)
   2. The emotional intensity (1-10)
   3. Whether it's a money problem, time problem, or trust problem

   Output as a structured list with at least 15 pain points.
   Format: JSON array with fields: quote, source, intensity, category"
```

**For GENERATION steps:**
```
ORIGINAL:
  "Generate 40+ ad copy variations"

CONVERTED:
  "Using the customer pain points and language below as your source material:

   {{previousOutput}}

   Generate 40 ad copy variations for {{niche}} targeting {{target_audience}}.

   For each variation:
   - Headline (max 40 chars)
   - Body copy (max 125 chars)
   - Call to action
   - Which pain point it addresses (reference by number)

   Use the EXACT customer language from the research -- do not sanitize
   or corporate-ify the words. The rawness is the point.

   Output as a numbered list, 1-40."
```

**For ACTION steps:**
```
ORIGINAL:
  "Upload to Meta Ads Manager"

CONVERTED:
  "This step requires the Meta Ads API. API Key: {{api_key_meta_ads}}

   Using the ad copy variations from the previous step:
   {{previousOutput}}

   Generate the API request bodies for creating a Meta Ads campaign:
   - Campaign objective: TRAFFIC
   - Daily budget: $33.33 (=$100 over 3 days)
   - Ad set targeting: {{target_audience}} demographics
   - Create one ad per variation

   Output: Array of Meta Ads API request objects (JSON)
   NOTE: User must execute these API calls manually or via the Meta
   Business SDK. This step generates the payloads, not the API calls."
```

---

## 4. API Key Registry

### 4.1 Detection Engine

The system scans all `YTStrategyStep.prompt` and `YTStrategyStep.description` fields for mentions of external services that require API keys.

**Known Service Patterns:**

| Service         | Detection Keywords                                        | Signup URL                                    |
|-----------------|-----------------------------------------------------------|-----------------------------------------------|
| Perplexity      | "perplexity", "pplx"                                     | https://perplexity.ai/settings/api            |
| Meta/Facebook   | "meta ads", "facebook ads", "meta business"               | https://developers.facebook.com               |
| Apollo          | "apollo", "apollo.io"                                     | https://app.apollo.io/#/settings/integrations |
| Instantly       | "instantly", "instantly.ai"                                | https://app.instantly.ai/app/settings/api     |
| Google Ads      | "google ads", "adwords"                                   | https://ads.google.com/aw/apicenter           |
| Search Console  | "search console", "google indexing"                       | https://console.cloud.google.com              |
| PhantomBuster   | "phantombuster", "phantom"                                | https://phantombuster.com/account              |
| Million Verifier| "million verifier", "email verif"                         | https://app.millionverifier.com               |
| Strappy         | "strappy"                                                  | https://strappy.com                            |
| Railway         | "railway"                                                  | https://railway.app                            |
| OpenAI          | "openai", "gpt", "chatgpt"                               | https://platform.openai.com/api-keys          |
| Claude/Anthropic| "claude", "anthropic"                                     | https://console.anthropic.com                 |
| Stripe          | "stripe", "payment"                                       | https://dashboard.stripe.com/apikeys          |

### 4.2 Generated "Setup" Tab Structure

```
+---+------------------+------------------------------------+-----------+------------------+
| # | Service          | Where to Get Key                   | Used In   | Status           |
+---+------------------+------------------------------------+-----------+------------------+
| 1 | Claude API       | console.anthropic.com              | Steps 2-9 | [ NOT SET ]      |
| 2 | Perplexity       | perplexity.ai/settings/api         | Step 1    | [ NOT SET ]      |
| 3 | Meta Ads         | developers.facebook.com            | Step 5    | [ NOT SET ]      |
| 4 | Apollo.io        | app.apollo.io/#/settings           | Step 8    | [ NOT SET ]      |
| 5 | Instantly AI     | app.instantly.ai/app/settings/api  | Step 8    | [ NOT SET ]      |
+---+------------------+------------------------------------+-----------+------------------+

API Key Entry (paste keys in column D):
  Row 1: claude_api_key        = [paste here]
  Row 2: perplexity_api_key    = [paste here]
  Row 3: meta_ads_api_key      = [paste here]
  ...
```

The Apps Script reads keys from this tab at runtime and injects them into prompt templates via `{{api_key_SERVICE_NAME}}` variables.

---

## 5. The Generated Sheet Structure

### 5.1 Tab Layout

Every generated Sheet follows the same five-tab structure, regardless of the source video:

```
+============================================================================+
|  [Setup]  |  [Chain Config]  |  [Run]  |  [Results]  |  [History]         |
+============================================================================+
```

### Tab 1: Setup

Purpose: API keys, project settings, and environment configuration.

```
+----+-------------------+------------------------------------------+---------+
|    | A: Setting        | B: Value                                 | C: Info |
+----+-------------------+------------------------------------------+---------+
|  1 | Project Name      | GTM Engineering Pipeline                 |         |
|  2 | Source Video       | https://youtube.com/watch?v=...          |         |
|  3 | Target Niche      | [USER FILLS IN]                          | Required|
|  4 | Target Audience   | [USER FILLS IN]                          | Required|
|  5 | ---               | --- API KEYS ---                         |         |
|  6 | claude_api_key    | [PASTE HERE]                             | Required|
|  7 | perplexity_key    | [PASTE HERE]                             | Step 1  |
|  8 | meta_ads_key      | [PASTE HERE]                             | Step 5  |
|  9 | apollo_key        | [PASTE HERE]                             | Step 8  |
| 10 | instantly_key     | [PASTE HERE]                             | Step 8  |
+----+-------------------+------------------------------------------+---------+
```

### Tab 2: Chain Config

Purpose: One row per strategy step. This is the prompt chain definition.

```
+----+-----+------------------+--------+------------------------+------------------+-------+
|    | Step| Name             | Type   | Prompt Template        | Expected Output  | Model |
+----+-----+------------------+--------+------------------------+------------------+-------+
|  1 |  1  | Research ICP     | RSCH   | You are a market re... | 15+ pain points  | sonnet|
|  2 |  2  | Generate Ad Copy | GEN    | Using the customer...  | 40 ad variations | sonnet|
|  3 |  3  | Bulk Generate    | GEN    | Take the ad copy ...   | Image files      | sonnet|
|  4 |  4  | Upload to Meta   | ACTION | This step requires...  | Campaign IDs     | sonnet|
|  5 |  5  | Analyze Winners  | RSCH   | Pull campaign data...  | Top 5 winners    | opus  |
|  6 |  6  | Landing Pages    | GEN    | Generate landing...    | HTML pages       | sonnet|
|  7 |  7  | SEO Submission   | ACTION | Submit to Google...    | Indexed URLs     | haiku |
|  8 |  8  | LinkedIn Pipeline| ACTION | Multi-API chain:...    | Contact list     | sonnet|
|  9 |  9  | KPI Dashboard    | GEN    | Generate dashboard...  | Dashboard config | sonnet|
+----+-----+------------------+--------+------------------------+------------------+-------+

Additional columns (not shown above):
  - Input Source: "manual" | "step_N"
  - Required APIs: comma-separated service names
  - Helper Instructions: concatenated sub-step descriptions
  - Status: pending | running | complete | error
  - Run Duration: time taken (filled after execution)
```

### Tab 3: Run

Purpose: The Web App dashboard. This is not a static sheet tab -- it is an Apps Script Web App that renders as an interactive UI.

```
+============================================================================+
|  GTM Engineering Pipeline                          [Run All] [Run Step]    |
|                                                                            |
|  Step 1 of 9: Research ICP Pain Points             Status: PENDING        |
|  +------------------------------------------------------------------+    |
|  | Prompt (editable):                                                |    |
|  | You are a market researcher. Search for pain points...            |    |
|  +------------------------------------------------------------------+    |
|  | Input: [Target Niche] [Target Audience]                           |    |
|  +------------------------------------------------------------------+    |
|  | Output:                                                           |    |
|  | [empty -- will be filled after execution]                         |    |
|  +------------------------------------------------------------------+    |
|                                                                            |
|  Step 2 of 9: Generate 40+ Ad Copy Variations      Status: PENDING        |
|  +------------------------------------------------------------------+    |
|  | Prompt: Using the customer pain points and language below...       |    |
|  | Input: {{step_1_output}} [auto-chained]                           |    |
|  +------------------------------------------------------------------+    |
|  ...                                                                       |
+============================================================================+
```

Features of the Run tab:
- **Run All**: Executes steps 1 through N in sequence, chaining outputs
- **Run Step**: Execute a single step (useful for re-running after edits)
- **Editable prompts**: User can modify any prompt before running
- **Auto-chaining**: `{{previousOutput}}` replaced with actual output at runtime
- **Status indicators**: Pending / Running (spinner) / Complete (green) / Error (red)
- **Manual step flags**: Steps classified as MANUAL show instructions instead of a Run button

### Tab 4: Results

Purpose: Stores the output from each step execution.

```
+----+-----+------------------+---------------------+--------------------------+
|    | Step| Name             | Completed At        | Output                   |
+----+-----+------------------+---------------------+--------------------------+
|  1 |  1  | Research ICP     | 2026-03-11 14:32:00 | [full output text]       |
|  2 |  2  | Generate Ad Copy | 2026-03-11 14:35:00 | [full output text]       |
|  3 |  3  | Bulk Generate    |                     |                          |
|  ...                                                                         |
+----+-----+------------------+---------------------+--------------------------+
```

### Tab 5: History

Purpose: Audit log of every run, including re-runs.

```
+----+---------------------+------+--------+-----------+--------+
|    | Timestamp           | Step | Action | Duration  | Status |
+----+---------------------+------+--------+-----------+--------+
|  1 | 2026-03-11 14:30:01 |  1   | RUN    | 2m 14s    | OK     |
|  2 | 2026-03-11 14:32:15 |  2   | RUN    | 3m 02s    | OK     |
|  3 | 2026-03-11 14:35:20 |  2   | RE-RUN | 2m 58s    | OK     |
|  ...                                                           |
+----+---------------------+------+--------+-----------+--------+
```

---

## 6. Sheet Deployment (Stage 4)

### 6.1 Google Sheets API Integration

The deployment stage takes the Sheet Blueprint JSON and creates a real Google Sheet via the Google Sheets API v4.

**Required Google APIs:**
- Google Sheets API (create spreadsheet, write data)
- Google Drive API (set sharing permissions)
- Apps Script API (create and deploy the Web App)

**Authentication:** OAuth 2.0 with the following scopes:
- `https://www.googleapis.com/auth/spreadsheets`
- `https://www.googleapis.com/auth/drive.file`
- `https://www.googleapis.com/auth/script.projects`

### 6.2 Deployment Sequence

```
Step 1: Create Spreadsheet
  API: spreadsheets.create()
  - Set title: "{project_name} - Tool"
  - Create 5 tabs (Setup, Chain Config, Results, History, Run)

Step 2: Populate Setup Tab
  API: spreadsheets.values.update()
  - Write API key registry rows
  - Write project metadata
  - Apply formatting (headers bold, key cells highlighted)

Step 3: Populate Chain Config Tab
  API: spreadsheets.values.update()
  - One row per YTStrategyStep
  - Apply conditional formatting (step type color coding)
  - Set data validation on Type column (RSCH, GEN, ACTION, MANUAL)

Step 4: Create Apps Script Project
  API: script.projects.create()
  - Attach to the spreadsheet
  - Upload server-side code (Chain runner, API caller, output writer)
  - Upload Web App HTML (Run tab UI)

Step 5: Deploy Web App
  API: script.projects.updateContent() + script.projects.deployments.create()
  - Deploy as Web App ("Execute as me, accessible to anyone with link")
  - Return the Web App URL

Step 6: Set Permissions
  API: drive.permissions.create()
  - Share sheet with the user's email (editor access)
  - Optionally make view-only link for sharing
```

### 6.3 Apps Script Template

The deployed Apps Script follows a standard pattern. The template is stored in the YT Lab backend and populated with project-specific values at deployment time.

**Server-side code (Code.gs):**
```
function doGet() --> serves the Web App HTML
function runStep(stepNumber) --> reads prompt from Chain Config, calls Claude API, writes output
function runAll() --> iterates through all steps in order
function getConfig() --> reads Setup tab for API keys and settings
function writeResult(step, output) --> writes to Results tab
function logHistory(step, action, duration, status) --> writes to History tab
function resolveChaining(prompt, stepNumber) --> replaces {{previousOutput}} with actual data
```

**Client-side code (WebApp.html):**
```
Renders each chain step as a card
Run / Re-run buttons per step
Status indicators with live polling
Editable prompt text areas
Output display areas
"Run All" button at top
Progress bar showing X of N steps complete
```

---

## 7. Cody Schneider Video -- Concrete Transformation Example

This section walks through exactly how the "GTM Engineering" video (from the Human in the Loop show) would be transformed end-to-end.

### 7.1 Input: Extracted YTStrategySteps

```
Step  1: "Set Up Your Local Agent Workspace"
Step  2: "Research ICP Pain Points"
Step  3: "Build a Bulk Ad Creative Generator"
Step  4: "Generate 40+ Ad Copy Variations"
Step  5: "Bulk Generate and Export Ad Images"
Step  6: "Upload Ads and Run CPC Test Campaign"
Step  7: "Build Keyword-Matched Landing Pages"
Step  8: "Build LinkedIn Engagement Pipeline"
Step  9: "Set Up a Real-Time Performance Pipeline"
Step 10: "Systematize and Document Everything"
```

### 7.2 Step-by-Step Transformation

```
STEP 1: "Set Up Your Local Agent Workspace"
  Classification: MANUAL
  Sheet Mapping:  Tab 1 (Setup) -- pre-populated .env template
  Chain Config:   SKIPPED (not a prompt chain step)
  Rationale:      This is environment setup. The generated Sheet's
                  Setup tab replaces this step entirely. The API key
                  registry covers .env configuration.

STEP 2: "Research ICP Pain Points"
  Classification: RESEARCH
  Chain Config:   Row 1
  Prompt:         Structured research prompt with Perplexity/Reddit targeting
  Input:          MANUAL (user provides niche + target audience)
  Output:         JSON array of pain points with customer language
  APIs Required:  Perplexity (optional -- Claude can do this without external API)
  Model:          Sonnet (fast, good at structured extraction)

STEP 3: "Build a Bulk Ad Creative Generator"
  Classification: MANUAL (flagged as "requires custom build")
  Chain Config:   Row 2 (with MANUAL flag)
  Treatment:      This step asks the user to build a React component.
                  The Sheet cannot automate this. Instead:
                  - Provide a pre-built HTML template for ad creatives
                  - Or link to Canva/Figma templates
                  - Or generate the React component code via Claude
                    and instruct user to run it locally
  Alternative:    Generate a sub-Sheet that serves as a simple ad
                  template configurator (background color, text placement,
                  logo position) -- simpler than a React app but functional.

STEP 4: "Generate 40+ Ad Copy Variations"
  Classification: GENERATION
  Chain Config:   Row 3
  Prompt:         Takes ICP research output, generates 40 variations
  Input:          {{step_2_output}} (the pain points from research)
  Output:         Numbered list of 40 ad copy sets (headline + body + CTA)
  APIs Required:  Claude (core)
  Model:          Sonnet

STEP 5: "Bulk Generate and Export Ad Images"
  Classification: GENERATION + MANUAL hybrid
  Chain Config:   Row 4
  Treatment:      Claude generates the image specifications (text overlays,
                  dimensions, color schemes) from the ad copy. Actual image
                  generation requires either:
                  a) A template system (HTML-to-canvas, built in Step 3)
                  b) An image generation API (DALL-E, Midjourney)
                  c) Manual creation in Canva using the specs
  Input:          {{step_4_output}} (the 40 ad copy variations)
  Output:         Image specifications or direct image URLs
  Model:          Sonnet

STEP 6: "Upload Ads and Run CPC Test Campaign"
  Classification: ACTION
  Chain Config:   Row 5
  Prompt:         Generate Meta Ads API request payloads
  Input:          {{step_5_output}} (ad images/specs)
  Output:         Campaign configuration JSON + API request bodies
  APIs Required:  Meta Ads API
  Model:          Sonnet
  Note:           Sheet generates the payloads. User executes via Meta
                  Business SDK or manually through Ads Manager.
                  Budget: $100 over 3 days ($33.33/day).

STEP 7: "Build Keyword-Matched Landing Pages"
  Classification: GENERATION
  Chain Config:   Row 6
  Prompt:         Generate landing page HTML/content from winning ad data
  Input:          Manual (user inputs winning ad data after 3-day test)
                  OR {{step_6_output}} if campaign data is available via API
  Output:         Landing page HTML templates with keyword matching
  APIs Required:  Strappy CMS (optional), Google Search Console
  Model:          Sonnet

STEP 8: "Build LinkedIn Engagement Pipeline"
  Classification: ACTION (multi-API chain)
  Chain Config:   Row 7
  Prompt:         Generate the pipeline configuration for:
                  PhantomBuster (LinkedIn scraping) -->
                  Apollo (enrichment) -->
                  Million Verifier (email validation) -->
                  Instantly AI (cold email sequences)
  Input:          Manual (user provides LinkedIn search criteria)
  Output:         Pipeline config for each service + email templates
  APIs Required:  PhantomBuster, Apollo, Million Verifier, Instantly
  Model:          Sonnet
  Note:           This is a complex multi-service step. The Sheet generates
                  configuration for each service. User sets up each service
                  separately. Consider breaking into 4 sub-rows.

STEP 9: "Set Up a Real-Time Performance Pipeline"
  Classification: GENERATION
  Chain Config:   Row 8
  Prompt:         Generate KPI dashboard configuration and tracking setup
  Input:          {{step_6_output}} + {{step_7_output}} (campaign + landing page data)
  Output:         Dashboard config (Google Data Studio template or Sheet-based)
  APIs Required:  Google Analytics (optional)
  Model:          Sonnet

STEP 10: "Systematize and Document Everything"
  Classification: GENERATION
  Chain Config:   Row 9
  Prompt:         Generate SOPs, runbooks, and documentation for the entire
                  pipeline so it can be repeated for new niches
  Input:          All previous outputs ({{step_1_output}} through {{step_9_output}})
  Output:         Complete documentation package
  APIs Required:  None
  Model:          Opus (complex synthesis task)
```

### 7.3 Resulting Chain Config Summary

```
+------+---------------------------+--------+------------------------+----------------+
| Row  | Step Name                 | Type   | Input Source            | APIs Needed    |
+------+---------------------------+--------+------------------------+----------------+
|  1   | Research ICP Pain Points  | RSCH   | Manual (niche, ICP)    | Perplexity     |
|  2   | Ad Creative Template      | MANUAL | --                     | --             |
|  3   | Generate 40+ Ad Copy      | GEN    | Row 1 output           | Claude         |
|  4   | Bulk Generate Images      | GEN    | Row 3 output           | Claude         |
|  5   | Upload to Meta Ads        | ACTION | Row 4 output           | Meta Ads       |
|  6   | Build Landing Pages       | GEN    | Manual (winner data)   | Strappy        |
|  7   | LinkedIn Pipeline         | ACTION | Manual (search params) | 4 services     |
|  8   | Performance Dashboard     | GEN    | Rows 5+6 output        | Google Anlytcs |
|  9   | Document Everything       | GEN    | All previous outputs   | Claude         |
+------+---------------------------+--------+------------------------+----------------+

Note: Original Step 1 (workspace setup) is absorbed into the Setup tab.
      Original Step 11 (deploy server) is flagged as infrastructure guidance.
      10 video steps --> 9 chain config rows + 1 setup absorption.
```

---

## 8. Tool Activation (Stage 5)

Once the Sheet is deployed, the user needs to activate it. This is intentionally simple.

### 8.1 Activation Checklist (generated in Setup tab)

```
[ ] 1. Open the generated Google Sheet
[ ] 2. Go to the "Setup" tab
[ ] 3. Fill in your target niche and audience
[ ] 4. Paste your Claude API key (required for all steps)
[ ] 5. Paste API keys for optional services (Perplexity, Meta, etc.)
[ ] 6. Go to the "Run" tab (or open the Web App URL)
[ ] 7. Click "Run Step 1" to test
[ ] 8. Review output, edit prompt if needed, re-run if needed
[ ] 9. Click "Run All" to execute the full chain
```

### 8.2 First-Run Validation

Before executing any chain step, the Apps Script validates:
1. Claude API key is present and valid (test call)
2. Required API keys for the current step are present
3. Input from previous step exists (if chained)
4. Warn if a MANUAL step was skipped

---

## 9. Data Flow Diagram

### End-to-End Pipeline

```
                    USER
                     |
                     | (1) Pastes YouTube URL
                     v
            +------------------+
            |   YT STRATEGY    |
            |      LAB         |
            |   (React UI)     |
            +--------+---------+
                     |
                     | (2) Sends URL to backend
                     v
            +------------------+
            |   YT PROCESSOR   |
            |   (Python)       |
            |                  |
            | - Extract trans. |
            | - AI processing  |
            | - Structure steps|
            +--------+---------+
                     |
                     | (3) Returns YTStrategyStep[]
                     v
            +------------------+
            |  TRANSFORMATION  |        +-------------------+
            |     ENGINE       | -----> | SHEET BLUEPRINT   |
            |   (NEW - Python) |        |    (JSON)         |
            |                  |        +-------------------+
            | - Classify steps |                |
            | - Chain I/O      |                | (4) Blueprint JSON
            | - Detect APIs    |                v
            | - Convert prompts|        +-------------------+
            +------------------+        | SHEET DEPLOYER    |
                                        |  (NEW - Python)   |
                                        |                   |
                                        | - Sheets API      |
                                        | - Apps Script API |
                                        | - Drive API       |
                                        +--------+----------+
                                                 |
                                                 | (5) Creates real Sheet
                                                 v
                                        +-------------------+
                                        | GOOGLE SHEET      |
                                        |   (Live)          |
                                        |                   |
                                        | [Setup]           |
                                        | [Chain Config]    |
                                        | [Run / Web App]   |
                                        | [Results]         |
                                        | [History]         |
                                        +--------+----------+
                                                 |
                                                 | (6) User adds API keys, clicks Run
                                                 v
                                        +-------------------+
                                        |  APPS SCRIPT      |
                                        |  RUNTIME          |
                                        |                   |
                                        | For each step:    |
                                        |  Read prompt      |
                                        |  Inject {{vars}}  |
                                        |  Call Claude API  |
                                        |  Write output     |
                                        |  Feed to next     |
                                        +-------------------+
```

### Internal Transformation Flow

```
YTStrategyStep[]
       |
       +---> [Step Classifier]
       |         |
       |         +---> RESEARCH / GENERATION / ACTION / MANUAL
       |
       +---> [API Scanner]
       |         |
       |         +---> List of required API keys + signup URLs
       |
       +---> [Chain Analyzer]
       |         |
       |         +---> Input/output dependency graph
       |         |
       |         +---> {{previousOutput}} injection map
       |
       +---> [Prompt Converter]
       |         |
       |         +---> Refined prompts with proper structure
       |         |
       |         +---> Template variables ({{niche}}, {{target_audience}}, etc.)
       |
       +---> [Blueprint Assembler]
                 |
                 +---> Sheet Blueprint JSON (complete specification)
```

---

## 10. Technical Implementation Plan

### 10.1 New Backend Components

```
server/
  routers/
    tool_factory.py          # REST endpoints for blueprint generation + deployment
  services/
    sheet_blueprint.py       # Transformation engine (YTStrategyStep[] -> Blueprint JSON)
    sheet_deployer.py        # Google Sheets API integration (Blueprint -> Live Sheet)
    step_classifier.py       # Step type classification (RESEARCH/GEN/ACTION/MANUAL)
    api_scanner.py           # API key detection from prompt text
    prompt_converter.py      # Smart prompt refinement
    chain_analyzer.py        # Input/output dependency analysis
  templates/
    apps_script/
      Code.gs.template       # Server-side Apps Script template
      WebApp.html.template    # Client-side Web App template
```

### 10.2 New UI Components

```
ui/src/
  components/yt-lab/
    ToolFactoryPanel.tsx      # "Generate Tool" button + status in YT Lab
    BlueprintPreview.tsx      # Preview of the Sheet structure before deployment
    DeploymentStatus.tsx      # Progress indicator during Sheet creation
    ActivationChecklist.tsx   # Post-deployment checklist
```

### 10.3 New API Endpoints

```
POST   /api/yt/projects/{id}/generate-blueprint
  Input:  project_id (has YTStrategyStep[] in database)
  Output: Sheet Blueprint JSON
  Notes:  Can be called multiple times to regenerate

POST   /api/yt/projects/{id}/deploy-sheet
  Input:  project_id + user's Google OAuth token
  Output: { sheet_url, web_app_url }
  Notes:  Requires OAuth flow for Google APIs

GET    /api/yt/projects/{id}/blueprint
  Input:  project_id
  Output: Current blueprint JSON (if generated)

GET    /api/yt/projects/{id}/deployment-status
  Input:  project_id
  Output: { status, sheet_url, web_app_url, error }
```

### 10.4 Google OAuth Flow

The user needs to grant Google API access once. The flow:

```
1. User clicks "Generate Google Sheet Tool" in YT Lab UI
2. If no Google token cached:
   a. Redirect to Google OAuth consent screen
   b. Request scopes: spreadsheets, drive.file, script.projects
   c. Receive authorization code
   d. Exchange for access token + refresh token
   e. Store refresh token securely (encrypted in registry.db)
3. If token cached:
   a. Use refresh token to get new access token
   b. Proceed directly to deployment
```

### 10.5 Dependencies

**Python packages (add to requirements.txt):**
```
google-api-python-client>=2.100.0    # Google Sheets + Drive + Apps Script APIs
google-auth-oauthlib>=1.2.0          # OAuth 2.0 flow
google-auth>=2.25.0                  # Google auth base
```

**No new npm packages needed** -- the UI additions are standard React components.

---

## 11. SaaS Vision and Monetization

### 11.1 Tier Structure

```
+-------------------+---------------------------+----------------------------+
| Tier              | What You Get              | Price                      |
+-------------------+---------------------------+----------------------------+
| FREE              | - Extract & view steps    | $0/mo                      |
|                   | - Blueprint preview       |                            |
|                   | - Up to 3 projects        |                            |
+-------------------+---------------------------+----------------------------+
| PRO               | - Everything in Free      | $29/mo or $249/yr          |
|                   | - Auto-generate Sheets    |                            |
|                   | - Unlimited projects      |                            |
|                   | - Prompt refinement AI    |                            |
|                   | - Blueprint editing       |                            |
+-------------------+---------------------------+----------------------------+
| ENTERPRISE        | - Everything in Pro       | $99/mo or $899/yr          |
|                   | - Auto-deploy Sheets      |                            |
|                   | - API key validation      |                            |
|                   | - Custom branding         |                            |
|                   | - Team sharing            |                            |
|                   | - Run history analytics   |                            |
|                   | - Priority support        |                            |
+-------------------+---------------------------+----------------------------+
```

### 11.2 Unit Economics

```
Cost per tool generation:
  - Claude API call for prompt refinement: ~$0.05-0.15
  - Google Sheets API calls: free (within quota)
  - Apps Script deployment: free

Revenue per Pro user:
  - $29/mo, generates ~5-20 tools/month
  - Cost: ~$1-3/month in API calls
  - Gross margin: ~90%+

Scale target:
  - 1,000 Pro users = $29K/mo MRR
  - 100 Enterprise users = $9.9K/mo MRR
  - Combined: ~$39K/mo = ~$468K ARR
```

### 11.3 Subscription Model with Local SDK

For users who prefer to run everything locally (no SaaS dependency):

```
- User has their own Claude subscription (Pro/Max)
- YT Lab runs locally via AutoForge
- Sheet generation uses user's own Google account
- No per-API-call costs to us
- Monetization: one-time license or annual subscription for the software itself
- Price: $199 one-time or $49/yr for updates
```

---

## 12. Scale Opportunity

### 12.1 Volume Projections

```
"Hundreds per day" target:

YouTube publishes ~500 hours of video per minute.
Business/strategy content: ~5% = 25 hours/minute of potential source material.

Conservative funnel:
  - 100 users each process 3 videos/day = 300 tools/day
  - 1,000 users each process 2 videos/day = 2,000 tools/day
  - 10,000 users at 1 video/day = 10,000 tools/day

Each tool is a Google Sheet. Google Sheets has no meaningful quota limit
for creating sheets (standard API quota: 300 requests/minute per user).
The bottleneck is Claude API calls for prompt refinement, which scales
linearly with user count (each user uses their own key).
```

### 12.2 Tool Marketplace

Generated tools can be shared and potentially sold:

```
Creator Flow:
  1. Creator finds a high-value strategy video
  2. Processes it through Video-to-Tool Factory
  3. Refines the prompts and tests the chain
  4. Publishes the tool to the marketplace
  5. Other users clone the tool (fork the Sheet)
  6. Creator earns a share of the clone fee

Marketplace Structure:
  - Browse by category (marketing, sales, ops, dev)
  - Search by niche (real estate, SaaS, e-commerce)
  - Sort by: most cloned, highest rated, newest
  - Each listing shows: source video, step count, required APIs, rating
  - Clone fee: $5-25 per tool (creator gets 70%, platform gets 30%)
```

---

## 13. Integration Points

### 13.1 System Integration Map

```
+-------------------+          +-------------------+
|   YT STRATEGY     |  ------> | VIDEO-TO-TOOL     |
|      LAB          |  Step[]  |    FACTORY         |
| (existing system) |          | (this PRD)        |
+-------------------+          +--------+----------+
                                        |
                         +--------------+---------------+
                         |              |               |
                         v              v               v
                 +-------------+ +-------------+ +-------------+
                 | GOOGLE      | | GOOGLE      | | CLAUDE      |
                 | SHEETS API  | | APPS SCRIPT | | API         |
                 |             | | API         | |             |
                 | Create sheet| | Deploy      | | Prompt      |
                 | Write data  | | Web App     | | refinement  |
                 | Format      | | Server code | | (Stage 3)   |
                 +-------------+ +-------------+ +-------------+
                         |              |
                         v              v
                 +-----------------------------+
                 |    GENERATED GOOGLE SHEET   |
                 |                             |
                 |  +-------+  +-----------+  |
                 |  | Setup |  | Chain Cfg |  |
                 |  +-------+  +-----------+  |
                 |  +-----+  +---------+      |
                 |  | Run |  | Results |      |
                 |  +-----+  +---------+      |
                 |  +---------+               |
                 |  | History |               |
                 |  +---------+               |
                 +-----------------------------+
                         |
                         | (at runtime, calls)
                         v
                 +-----------------------------+
                 |  CLAUDE API (user's key)    |
                 |  Per-step prompt execution  |
                 +-----------------------------+
```

### 13.2 External Service Integrations

| Integration          | Purpose                          | Required | Notes                          |
|----------------------|----------------------------------|----------|--------------------------------|
| Google Sheets API v4 | Create and populate sheets       | YES      | Core deployment target         |
| Google Drive API v3  | Set sharing permissions          | YES      | Paired with Sheets API         |
| Google Apps Script   | Deploy Web App runtime           | YES      | Runs the prompt chains         |
| Claude API           | Prompt refinement (Stage 3)      | YES      | Used during blueprint gen      |
| Claude API           | Runtime execution (in Sheet)     | YES      | User's own API key             |
| Style Set            | Theme generated Web App          | NO       | Optional branding layer        |
| YT Lab Database      | Read YTStrategyStep data         | YES      | Existing SQLite / localStorage |

### 13.3 Connection to Existing YT Lab Vision

This PRD aligns with the Vision document's concept of **Mode 1 (Simple Step-by-Step)** templates. The Google Sheet tool IS the template -- it is a structured, repeatable, shareable workflow that anyone can run without technical knowledge.

The Video-to-Tool Factory is also a natural fit for the **Breakaway Architecture**. A generated Sheet tool that proves itself (runs successfully for multiple niches, gets cloned in the marketplace) is a candidate for breakaway into its own standalone product -- potentially with a custom web UI instead of Google Sheets as the runtime.

```
Progression:
  Video --> YT Lab Blueprint --> Google Sheet Tool --> Proven Tool --> Standalone SaaS App
                                                          |
                                                          +-- This is the "breakaway signal"
                                                              from VISION.md
```

---

## 14. Risks and Mitigations

| Risk                                    | Impact | Mitigation                                    |
|-----------------------------------------|--------|-----------------------------------------------|
| Google Apps Script API is restrictive   | HIGH   | Test deployment flow early. Have fallback:     |
|                                          |        | generate Sheet + provide script for manual     |
|                                          |        | paste into Apps Script editor.                 |
| Prompt refinement produces bad prompts  | MEDIUM | Allow user editing in Blueprint Preview before |
|                                          |        | deployment. Include "regenerate" per step.     |
| Step classification is wrong            | MEDIUM | Let users override classification in preview.  |
|                                          |        | Default to GENERATION if unsure.               |
| Google OAuth UX is confusing            | MEDIUM | Provide clear walkthrough. Consider using      |
|                                          |        | service account for simpler auth.              |
| API key management in Sheets is insecure| HIGH   | Document security implications clearly.        |
|                                          |        | Recommend using Google Apps Script Properties   |
|                                          |        | Service instead of plain cell values. Add      |
|                                          |        | warning in Setup tab about not sharing sheet   |
|                                          |        | with API keys filled in.                       |
| Apps Script execution time limits (6min)| MEDIUM | Break long Claude calls into async patterns.   |
|                                          |        | Use Apps Script triggers for long-running steps.|
| Rate limiting on Claude API from Sheet  | LOW    | Add retry logic with exponential backoff in    |
|                                          |        | the Apps Script template. Show clear error.    |

---

## 15. Implementation Phases

### Phase 1: Blueprint Generation (Week 1-2)

**Goal:** Given a YT Lab project with steps, produce a Sheet Blueprint JSON.

Deliverables:
- Step classifier (RESEARCH / GENERATION / ACTION / MANUAL)
- API key scanner
- Chain analyzer (input/output mapping)
- Prompt converter (basic refinement)
- Blueprint assembler
- Blueprint Preview UI component in YT Lab
- REST endpoint: `POST /api/yt/projects/{id}/generate-blueprint`

**Exit criteria:** User can click "Generate Blueprint" on any YT Lab project and see a structured preview of what the Sheet will look like.

### Phase 2: Sheet Deployment (Week 3-4)

**Goal:** Take a Blueprint JSON and create a real Google Sheet.

Deliverables:
- Google OAuth flow in YT Lab UI
- Sheet creation via Sheets API
- Data population (Setup + Chain Config tabs)
- Formatting and conditional formatting
- REST endpoint: `POST /api/yt/projects/{id}/deploy-sheet`

**Exit criteria:** User can click "Deploy Sheet" and get a real Google Sheet URL with all tabs populated and formatted.

### Phase 3: Apps Script Runtime (Week 5-6)

**Goal:** The deployed Sheet can actually execute prompt chains.

Deliverables:
- Apps Script template (Code.gs + WebApp.html)
- Template population with project-specific data
- Apps Script API integration for deployment
- Web App deployment and URL generation
- First-run validation logic

**Exit criteria:** User can open the generated Sheet, paste their Claude API key, click "Run Step 1", and get a real AI-generated output that flows into Step 2.

### Phase 4: Polish and Marketplace (Week 7-8)

**Goal:** Production-quality UX and sharing capability.

Deliverables:
- Deployment status tracking in UI
- Activation checklist component
- Error handling and retry logic
- Tool sharing / clone flow
- Run history analytics in the Sheet
- Documentation and user guide

**Exit criteria:** A non-technical user can go from YouTube URL to running prompt chain tool in under 5 minutes (excluding API key setup time).

---

## 16. Success Metrics

| Metric                              | Target              | How Measured                        |
|--------------------------------------|---------------------|--------------------------------------|
| Time from video to working tool     | < 5 minutes         | Timestamp: URL paste to first run   |
| Blueprint generation success rate   | > 95%               | Successful JSON generation / total  |
| Sheet deployment success rate       | > 90%               | Successful Sheet creation / total   |
| Chain execution completion rate     | > 80%               | Steps that complete without error   |
| User prompt edit rate               | < 30%               | Steps where user edits prompt       |
| Tool clone rate (marketplace)       | > 5% of published   | Clones / published tools            |
| Monthly tools generated (at scale)  | > 10,000            | Total across all users              |

---

## 17. Open Questions

1. **Should the Apps Script call Claude directly or go through a proxy?** Direct is simpler but exposes the API key in client-side Apps Script. A proxy adds latency but improves security.

2. **What happens when a video has steps that span multiple days?** (e.g., "Run the ad campaign for 3 days, then analyze results.") Should the chain pause and resume, or split into separate runs?

3. **Should we support Sheet templates beyond Google Sheets?** Excel Online, Notion databases, and Airtable are all potential targets with similar API capabilities.

4. **How do we handle steps that require file I/O?** (e.g., "Generate 40 PNG images.") Google Sheets cannot store binary files. Options: Google Drive folder alongside the Sheet, or external storage links.

5. **What is the fallback if Google Apps Script API access is denied?** Not all Google Workspace accounts allow programmatic script deployment. We may need a manual deployment path where we generate the script code and the user pastes it.

6. **Should generated tools phone home?** Usage analytics from deployed tools would be valuable for the marketplace, but raises privacy concerns. Opt-in only.

---

## Appendix A: YTStrategyStep Type Reference

From `ui/src/lib/types.ts`:

```typescript
type YTStrategyStepStatus = 'pending' | 'in_progress' | 'complete'

interface YTStrategySubStep {
  id: string
  stepId: string
  order: number
  title: string
  description: string
  prompt: string
  status: YTStrategyStepStatus
}

interface YTStrategyStep {
  id: string
  projectId: string
  order: number
  title: string
  description: string
  prompt: string
  expectedOutput: string
  notes: string
  aiOutput: string
  status: YTStrategyStepStatus
  model: string
  role: string
  subSteps: YTStrategySubStep[]
}

interface YTStrategyProject {
  id: string
  name: string
  sourceUrl: string
  niche: string
  description: string
  tags: string[]
  status: 'draft' | 'in-progress' | 'complete'
  createdAt: string
  updatedAt: string
}
```

## Appendix B: Google Sheets Build Planner Pattern Reference

The existing Build Planner Sheet demonstrates the pattern this system will replicate at scale:

```
Build Planner Sheet Structure:
  Tab: "Chain Config"
    - Column A: Step Number
    - Column B: Step Name
    - Column C: Prompt Template (may include {{variables}})
    - Column D: Input Fields (comma-separated variable names)
    - Column E: Model (sonnet / opus / haiku)
    - Column F: Options (JSON config)
    - Column G: Status

  Tab: "Web App" (served via doGet())
    - Renders each chain step as a card
    - Text areas for input and output
    - "Run" button per step
    - Output from step N auto-populates input for step N+1

  Apps Script:
    - doGet(): serves the HTML
    - runStep(n): reads prompt from Chain Config row N,
      replaces {{variables}}, calls Claude API, returns output
    - getApiKey(): reads from Properties Service
    - saveResult(n, output): writes to Results tab
```

The Video-to-Tool Factory automates the creation of this exact structure, populated with data from any processed YouTube video.
