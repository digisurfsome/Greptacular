# Tool Factory — User Manual

> **What is the Tool Factory?** It turns YouTube strategy videos and PRD documents into deployable Google Sheet tools. You define the steps, it builds the blueprint, you pick a theme, and it deploys a formatted, multi-tab Google Sheet that runs your strategy.

---

## Table of Contents

1. [Getting There](#getting-there)
2. [Creating a Tool from YouTube Strategy](#creating-a-tool-from-youtube-strategy)
3. [Creating a Tool from a PRD Document](#creating-a-tool-from-a-prd-document)
4. [The Blueprint Preview](#the-blueprint-preview)
5. [Picking a Theme](#picking-a-theme)
6. [Deploying to Google Sheets](#deploying-to-google-sheets)
7. [Managing Your Tools](#managing-your-tools)
8. [Batch Generation (Multi-Tool)](#batch-generation)
9. [Analytics Dashboard](#analytics-dashboard)
10. [Troubleshooting](#troubleshooting)

---

## Getting There

Two entry points:

- **Tool Manager** — Go to `/#/tools` (or click "Tool Factory" in the sidebar). This is the home base where all your tools live.
- **YT Strategy Lab** — Go to `/#/yt-lab`. This is where you define strategies from YouTube videos, then generate tools from them.

---

## Creating a Tool from YouTube Strategy

This is the main flow — you watched a YouTube video (or several), captured the strategy steps, and now you want to turn it into a working tool.

### Step 1: Define Your Strategy in YT Lab

1. Open **YT Strategy Lab** (`/#/yt-lab`)
2. Create a new project (give it a name like "AI SEO Tool" or "Content Repurposing System")
3. Add steps — each step represents one thing the tool should do. For each step, fill in:
   - **Title** — What this step does (e.g., "Research competitor keywords")
   - **Description** — More detail about the step
   - **Prompt** — The actual instruction the AI will follow when running this step
   - **Expected Output** — What should come out (e.g., "A list of 20 keywords with search volume")
   - **Notes** — Any extra context
4. The system auto-classifies each step as one of four types:
   - **Research** — Investigating, analyzing, gathering data
   - **Generation** — Creating content, writing, designing
   - **Action** — Uploading, sending, deploying
   - **Manual** — Human review needed (the tool pauses here)

### Step 2: Generate the Tool

1. Click the **"Generate Tool"** button on your project
2. The system processes your steps:
   - Validates and cleans up your steps
   - Detects which APIs/services your tool needs (OpenAI, Google Ads, etc.)
   - Finds variables in your prompts (anything in `{{double braces}}`)
   - Rewrites prompts for consistency using Claude
   - Assembles everything into a blueprint
3. This takes 10-30 seconds depending on how many steps you have

### Step 3: Review the Blueprint

See [The Blueprint Preview](#the-blueprint-preview) below.

### Step 4: Pick a Theme

See [Picking a Theme](#picking-a-theme) below.

### Step 5: Deploy

See [Deploying to Google Sheets](#deploying-to-google-sheets) below.

---

## Creating a Tool from a PRD Document

Already have a written document describing what the tool should do? Skip the YouTube step.

1. Open **Tool Manager** (`/#/tools`)
2. Click **"New Tool"** → **"From PRD"**
3. The PRD Upload modal opens
4. Paste your document into the text area
5. Give it a filename (just for your reference)
6. Optionally add context — tell the system anything extra about what you want
7. Click **Upload**
8. Claude reads your PRD and extracts the steps automatically
9. You'll see the extracted steps — review them, edit if needed
10. From here, the flow is the same: Blueprint Preview → Theme → Deploy

**What makes a good PRD for this?** Anything with a clear sequence of steps. Bullet lists work great. Something like:
- Step 1: Research the topic using Google Trends
- Step 2: Generate 10 content ideas based on the research
- Step 3: Write outlines for the top 3 ideas
- Step 4: Create social media posts from each outline

---

## The Blueprint Preview

After generation, you see the full blueprint before deploying. This is your chance to review and edit.

### What You See

Each step is displayed as a card in a vertical chain, connected by arrows showing the flow:

- **Step type badge** — Color-coded: Research (blue), Generation (purple), Action (green), Manual (yellow)
- **Title** — What this step does
- **Prompt** — The full instruction the AI will follow (you can edit this inline)
- **Input source** — Where this step gets its data (user input, or output from a previous step)
- **Output destination** — Where the result goes (next step, or final output)
- **Model** — Which AI model runs this step (Sonnet for most, Opus for complex reasoning)
- **Required APIs** — Services this step needs (with signup links if you don't have them)
- **Gate flag** — If enabled, the tool pauses here for your review before continuing

### What You Can Do

- **Edit any prompt** — Click on the prompt text to modify it directly
- **Review the chain** — Make sure steps flow logically (Step 1's output feeds Step 2, etc.)
- **Check API requirements** — The system detected which services you'll need API keys for
- **Proceed to deploy** — Click "Deploy" when you're satisfied

---

## Picking a Theme

Themes control how your Google Sheet looks — colors, fonts, spacing. This is cosmetic but makes a real difference for professional-looking output.

### 10 Built-In Themes

| Theme | Vibe |
|-------|------|
| Arctic Frost | Clean blues and whites, icy minimalism |
| Botanical Garden | Greens and earth tones, organic feel |
| Desert Rose | Warm pinks and sandy neutrals |
| Forest Canopy | Deep greens and browns, nature-inspired |
| Golden Hour | Warm yellows and oranges, sunset vibes |
| Midnight Galaxy | Dark purples and blues, dramatic |
| Modern Minimalist | Neutral grays and whites, clean (default) |
| Neon Dreams | Bright neons on dark background, bold |
| Ocean Depths | Deep blues and teals, professional |
| Sunset Valley | Orange-to-purple gradient feel, warm |

### Extract Theme from Image

Got a brand style guide or a screenshot of a design you like?

1. Click **"Upload Screenshot"** in the theme picker
2. Upload any image
3. The system extracts colors, fonts, and styling from the image
4. Creates a custom theme based on what it finds

### Skip Theme

Don't care about styling? Click **"Skip"** and it uses Modern Minimalist (clean and professional).

### Swap Theme Later

Already deployed? You can change the theme anytime from the Tool Detail view. Go to the Theme tab and click "Change Theme."

---

## Deploying to Google Sheets

### First Time: Connect Google

The first time you deploy, you need to authorize the app to create Google Sheets on your behalf.

1. Click **Deploy**
2. You'll see a "Connect Google" prompt
3. Click the link — it opens Google's OAuth screen
4. Sign in and grant permission to manage spreadsheets
5. You're redirected back — now you're connected
6. This only happens once. Future deploys use the saved authorization.

### What Gets Created

Your Google Sheet has **5 tabs**:

| Tab | What's In It |
|-----|-------------|
| **Guide** | Overview of the tool — what it does, how to use it, key instructions |
| **Setup** | Environment variables and API keys you need to configure (fill these in before running) |
| **Chain Config** | The actual steps — this is the tool itself. Each row is one step with its prompt, input, output |
| **Output History** | Execution log — every time you run the tool, results are logged here |
| **Chain Runner** | Helper code and notes for running the chain |

### After Deployment

- The sheet opens in a new tab
- The tool status changes from **Draft** → **Active**
- You can find it anytime in the Tool Manager
- The sheet URL is saved — click "Open Sheet" to go back to it

---

## Managing Your Tools

### Tool Manager Home (`/#/tools`)

This is where all your tools live. You see a grid of cards, one per tool.

**Each card shows:**
- Tool name
- Status badge (Draft, Active, Error, Archived)
- Theme color swatches
- Source icon (YouTube camera or document icon)
- How many times it's been run
- When it was last run

### Filtering & Search

- **Status filters** — Click chips at the top: All, Active, Draft, Error, Archived
- **Search** — Type in the search bar to find tools by name, description, or tags
- **Sort** — Dropdown: Newest First, Last Run, Name A-Z

### Tool Detail View

Click any tool card to open the detail view. Four tabs:

#### Blueprint Tab
Shows the full chain visualization — every step, its inputs/outputs, the flow. Same as the preview you saw during creation, but read-only now.

#### Theme Tab
Shows the current theme with color swatches and font preview. Click **"Change Theme"** to swap to a different preset or upload a new image.

#### History Tab
Table of every execution:
- When it ran
- How many tokens it used
- Duration
- Status (success/error)
- Output preview

#### Settings Tab
- **Rename** — Change the tool's display name
- **Tags** — Add tags for organization
- **Archive** — Soft-delete the tool (moves to Archived status, can be restored)

### Tool Lifecycle

```
DRAFT ──→ DEPLOYING ──→ ACTIVE
              │
              └──→ ERROR (deployment failed)

Any status ──→ ARCHIVED (soft-delete, recoverable)
```

---

## Batch Generation

Have multiple YouTube strategy projects you want to turn into tools at once? Batch generation handles this.

### How to Run a Batch

1. Make sure you have multiple projects in YT Lab with strategies defined
2. Go to **Tool Manager** → Click **"New Tool"** → **"Batch"**
3. Select the projects you want to generate tools from
4. Optionally pick a default theme (applied to all tools)
5. Toggle **"Auto-deploy"** if you want them deployed to Google Sheets immediately
6. Click **"Start Batch"**

### What Happens

- Tools are generated **one at a time** (sequential, not parallel) to respect API limits
- Each tool is independent — if one fails, the others still complete
- You see a progress modal with real-time updates:
  - Which tool is currently being generated
  - Success/error status for each
  - Overall progress bar

### After the Batch

- All generated tools appear in the Tool Manager
- If auto-deploy was on, each one has a Google Sheet link
- Failed tools show an error message — you can retry them individually

---

## Analytics Dashboard

The analytics tab (in Tool Manager) shows your usage stats.

### What You See

- **All-Time Stats** — Total tools created, total deployments, total executions, total tokens used
- **Monthly Usage Chart** — Bar chart showing tools generated, deployed, and executed per month
- **Tier Usage Gauge** — How much of your monthly quota you've used (relevant for Free tier)
- **Trending Charts** — Sparklines showing usage trends

### Tier Limits

| Tier | Tools/Month | Themes | Batch | API Access |
|------|-------------|--------|-------|------------|
| Free | 5 | Presets only | No | No |
| Pro | Unlimited | All (including image extraction) | Yes | No |
| Enterprise | Unlimited | All | Yes | Yes |

---

## Troubleshooting

### "No Anthropic API key configured"
The backend needs an API key to run Claude for prompt conversion and PRD extraction. Set `ANTHROPIC_API_KEY` in your environment or registry settings.

### Blueprint generation fails
- Check that your steps have actual prompts (not just titles)
- Make sure at least 2 steps are defined
- If prompts are very long, try shortening them — there's a token limit per request

### Google Sheets deployment fails
- Re-authenticate: go to Tool Manager → any tool → Deploy. If auth expired, it'll prompt you again
- Check your Google account has permission to create spreadsheets
- If you get a quota error, wait a minute and try again (Google limits 100 requests per 100 seconds)

### Theme extraction doesn't match my image
- Use images with clear, distinct colors (not photos with lots of detail)
- Brand style guides or UI screenshots work best
- Solid color palettes or design mockups give the best results
- If extraction is off, just pick a preset and move on

### Tool shows "Error" status
- Click the tool to see the error message in the detail view
- Most common: Google API auth expired, or the sheet was deleted from Google Drive
- Fix: re-authenticate and redeploy, or archive the tool and create a new one

### Batch generation is slow
- Each tool takes 10-30 seconds to generate
- Deployment adds another 5-10 seconds per tool
- A batch of 10 tools = roughly 3-5 minutes total
- This is by design — going faster would hit Google's API rate limits

---

## Quick Reference

| Action | Where | How |
|--------|-------|-----|
| Create tool from YouTube | YT Lab → Generate Tool | Define steps, click generate |
| Create tool from PRD | Tool Manager → New → From PRD | Paste document, upload |
| Preview blueprint | Auto-shown after generation | Review chain, edit prompts |
| Pick theme | Auto-shown after blueprint | Click preset or upload image |
| Deploy to Sheets | Blueprint preview → Deploy | Authenticate Google, click deploy |
| View all tools | Tool Manager (`/#/tools`) | Browse grid, search, filter |
| Change theme | Tool Detail → Theme tab | Click "Change Theme" |
| View run history | Tool Detail → History tab | See all executions |
| Batch generate | Tool Manager → New → Batch | Select projects, start |
| Check usage | Tool Manager → Analytics tab | View stats and tier |
| Archive a tool | Tool Detail → Settings tab | Click "Archive" |
