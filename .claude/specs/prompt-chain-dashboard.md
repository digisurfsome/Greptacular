# Prompt Chain Dashboard — Build Options

> **The idea:** Use Google Sheets (or a Sheet-powered web app) as a no-code prompt chaining
> dashboard. Users fill in boxes, hit buttons, AI processes each step, results feed into the
> next step. Looks like an app. Costs nothing to host. Built in minutes, not weeks.

---

## THE THREE OPTIONS

### Option 1: Styled Google Sheet (Simplest)

**What it is:** A Google Sheet that looks like a form/app. Users open the Sheet, fill in cells, click buttons.

**Hosting:** Share a Google Sheet link. They click "Make a copy." Done.

**Looks like:** A form with colored sections, input boxes, and buttons.

**Prompt chaining:** Apps Script behind each button reads cells, calls Claude API, writes result to next section.

**Can they edit/add chains?** No, not without knowing how to edit Apps Script. You'd build different versions for different use cases (3-chain, 4-chain, 5-chain) or they'd ask you to customize.

**Pros:**
- Builds in 30 minutes
- Free hosting (Google)
- No deployment, no server, no domain
- Users already know how to use spreadsheets
- Mobile-friendly (Google Sheets app)

**Cons:**
- Looks like a spreadsheet if you squint
- Not embeddable on your own site
- Each user needs their own copy
- Can't dynamically add/remove chains without editing the sheet

**Best for:** Lead magnet, cheap product, personal tools

---

### Option 2: Apps Script Web App (The Sweet Spot)

**What it is:** Google Apps Script deployed as a standalone web page. Custom HTML/CSS/JS frontend. Apps Script backend calls Claude API. Hosted on Google's servers for free.

**Hosting:** Gets a URL like `https://script.google.com/macros/s/ABC123/exec` — or you put it behind your own domain with an iframe or redirect.

**Looks like:** A REAL web app. Full HTML/CSS control. Tailwind, animations, whatever you want. Nobody knows it's powered by a spreadsheet.

**Prompt chaining:** Frontend sends form data to Apps Script → Apps Script calls Claude → returns result → frontend shows it and feeds it into the next chain step.

**Can they edit/add chains?** Two options:
- **Config-driven:** Store chain definitions in a Google Sheet. The web app reads the Sheet to know how many chains, what prompts, what inputs. To add a chain, they add a row to the config Sheet. No code editing needed.
- **UI editor:** Build a simple editor into the web app itself where they can add/remove/reorder chain steps. The editor saves to the config Sheet.

**Pros:**
- Looks like a real app (custom HTML/CSS)
- Free hosting on Google
- Can read/write to Google Sheets (data persistence for free)
- Can call any API (Claude, OpenAI, etc.)
- Shareable URL
- Can embed on your site via iframe
- Can use your Claude subscription (API key stored server-side in Apps Script properties)
- CAN be made user-editable (add/remove chains from a config sheet or in-app editor)

**Cons:**
- Slower than a real app (Apps Script has ~1-5 second cold starts)
- 6-minute execution time limit per call (fine for most prompts, not for huge ones)
- URL is ugly unless you iframe it
- Can't do real-time streaming (no WebSockets)
- Google account required to deploy (not to use)

**Best for:** The actual product. This is your prompt chaining dashboard.

---

### Option 3: AutoForge Page (Most Powerful, Most Work)

**What it is:** A real page inside AutoForge. Full React component. Full backend. Full control.

**Hosting:** Runs on your AutoForge instance (localhost:8888 or wherever you deploy it).

**Looks like:** A native part of AutoForge. Same design system, same nav, same feel.

**Prompt chaining:** React frontend → FastAPI backend → Claude API. Full streaming support. Real-time results appearing as Claude types.

**Can they edit/add chains?** YES — fully. You'd build a chain editor:
- Drag-and-drop chain steps
- Each step has: input fields, prompt template, output mapping
- Add/remove/reorder steps in the UI
- Save chain configs to SQLite
- Load/switch between saved chains
- Share chains with other users

**Pros:**
- Full app experience
- Real-time streaming
- No execution time limits
- Uses your existing Claude subscription (via Claude Code CLI)
- Fully editable chains in the UI
- Can integrate with AutoForge's existing features (projects, agents, etc.)
- No Google dependency

**Cons:**
- Requires AutoForge running
- More work to build (but AutoForge can build it for you)
- Self-hosted (not a sharable link unless you deploy somewhere)

**Best for:** Power users, your own workflow, premium product tier

---

## COMPARISON TABLE

| | Styled Sheet | Apps Script Web App | AutoForge Page |
|---|---|---|---|
| **Build time** | 30 min | 2-4 hours | 1-2 days |
| **Hosting cost** | Free | Free | Self-hosted |
| **Looks like** | Fancy spreadsheet | Real web app | Native app |
| **Prompt chaining** | Yes (buttons) | Yes (AJAX calls) | Yes (streaming) |
| **User-editable chains** | No | Yes (config sheet) | Yes (drag-drop UI) |
| **API streaming** | No | No | Yes |
| **Mobile friendly** | Yes (Sheets app) | Yes (responsive) | Depends on build |
| **Shareable URL** | Google link | Google URL / iframe | Deploy needed |
| **Embed on your site** | No | Yes (iframe) | Yes (deploy) |
| **Execution time limit** | 6 min/call | 6 min/call | None |
| **Needs Google account** | To copy | No (to use) | No |
| **Can sell as product** | Yes (template) | Yes (web app) | Yes (SaaS) |

---

## RECOMMENDATION: START WITH OPTION 2, UPGRADE TO OPTION 3

### Phase 1: Apps Script Web App (This Week)

Build the prompt chaining dashboard as an Apps Script Web App:

1. **I design the HTML/CSS** to look like a real app (dark mode, gradient buttons, clean typography)
2. **Chain definitions live in a Google Sheet** (one row per chain step: step number, prompt template, input fields, output field)
3. **The web app reads the config Sheet** at load time and renders the right number of chain steps
4. **Each step has:** input boxes, a "Run" button, and an output area
5. **Hitting "Run" on Step 1:** sends inputs + prompt to Claude API via Apps Script, shows result, auto-populates Step 2's input
6. **Hitting "Run" on Step 2:** takes Step 1's output + Step 2's inputs + Step 2's prompt, sends to Claude, shows result, populates Step 3
7. **And so on** for as many chains as the config Sheet defines
8. **To add a chain:** add a row to the config Sheet. Refresh the web app. New step appears.
9. **To edit a prompt template:** edit the cell in the config Sheet. Next run uses the new template.

### Phase 2: AutoForge Integration (Later)

When you want more power:
- Build it as an AutoForge page with the drag-drop editor
- Real-time streaming
- Save/load chain presets
- Premium product tier

### Phase 3: Sell Both

| Product | What They Get | Price |
|---------|--------------|-------|
| **Free** | Google Form (lead magnet) | $0 |
| **Starter** | Styled Google Sheet (blank templates) | $47 |
| **Pro** | Styled Google Sheet (your templates pre-filled) | $197-$495 |
| **Dashboard** | Apps Script Web App (prompt chaining tool) | $49-$99/mo |
| **Enterprise** | AutoForge page (full editor, streaming, presets) | $149-$299/mo |

---

## HOW THE APPS SCRIPT WEB APP WORKS (Technical)

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER'S BROWSER                        │
│                                                         │
│  ┌───────────────────────────────────────────────┐      │
│  │         Custom HTML/CSS/JS Frontend           │      │
│  │                                               │      │
│  │   ┌─────────┐  ┌─────────┐  ┌─────────┐     │      │
│  │   │ Chain 1  │→ │ Chain 2  │→ │ Chain 3  │    │      │
│  │   │ [inputs] │  │ [inputs] │  │ [inputs] │    │      │
│  │   │ [Run]    │  │ [Run]    │  │ [Run]    │    │      │
│  │   │ [output] │  │ [output] │  │ [output] │    │      │
│  │   └─────────┘  └─────────┘  └─────────┘     │      │
│  └───────────────────────────────────────────────┘      │
│         │ google.script.run.callChain(step, data)       │
└─────────┼───────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│              GOOGLE APPS SCRIPT (Server)                 │
│                                                         │
│  1. Reads chain config from Google Sheet                │
│  2. Assembles prompt: template + inputs + prev output   │
│  3. Calls Claude API (UrlFetchApp)                      │
│  4. Returns result to frontend                          │
│  5. Optionally logs to Google Sheet                     │
└─────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│              GOOGLE SHEET (Config + Data)                │
│                                                         │
│  Tab "Chain Config":                                    │
│  | Step | Name          | Prompt Template    | Inputs | │
│  |------|---------------|--------------------|--------| │
│  | 1    | Make PRD      | "You are a senior.."| app,   | │
│  |      |               |                    | feats  | │
│  | 2    | Split Phases  | "Take this PRD..." | phases | │
│  | 3    | Build Scripts | "Generate bash..." | model  | │
│  |------|---------------|--------------------|--------| │
│  | 4    | (add a row = add a chain step)      |        | │
│                                                         │
│  Tab "Run History":                                     │
│  | Date | Chain | Input Summary | Output Summary |      │
└─────────────────────────────────────────────────────────┘
```

### The Key Code

**HTML Frontend (served by Apps Script):**

```html
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    /* Modern app styling - dark mode, clean, professional */
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Inter', -apple-system, sans-serif;
      background: #0f0f0f;
      color: #e5e5e5;
      min-height: 100vh;
    }
    .header {
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
      padding: 24px 32px;
      border-bottom: 1px solid #2a2a4a;
    }
    .header h1 {
      font-size: 24px;
      font-weight: 700;
      background: linear-gradient(90deg, #00d2ff, #7b68ee);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .chain-container { padding: 32px; max-width: 900px; margin: 0 auto; }

    .chain-step {
      background: #1a1a1a;
      border: 1px solid #333;
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
      transition: border-color 0.3s;
    }
    .chain-step.active { border-color: #7b68ee; }
    .chain-step.complete { border-color: #00c853; }

    .step-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
    }
    .step-number {
      width: 32px; height: 32px;
      background: #7b68ee;
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-weight: 700; font-size: 14px;
    }
    .step-number.complete { background: #00c853; }
    .step-name { font-size: 18px; font-weight: 600; }

    .input-group { margin-bottom: 12px; }
    .input-group label {
      display: block;
      font-size: 13px;
      color: #888;
      margin-bottom: 4px;
    }
    .input-group textarea, .input-group input, .input-group select {
      width: 100%;
      background: #0f0f0f;
      border: 1px solid #333;
      border-radius: 8px;
      padding: 10px 14px;
      color: #e5e5e5;
      font-size: 14px;
      resize: vertical;
    }
    .input-group textarea:focus, .input-group input:focus {
      border-color: #7b68ee;
      outline: none;
    }

    .run-btn {
      background: linear-gradient(135deg, #7b68ee, #00d2ff);
      border: none;
      color: white;
      padding: 10px 24px;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      font-size: 14px;
      transition: opacity 0.2s;
    }
    .run-btn:hover { opacity: 0.9; }
    .run-btn:disabled { opacity: 0.5; cursor: not-allowed; }

    .output-area {
      background: #0a0a0a;
      border: 1px solid #222;
      border-radius: 8px;
      padding: 16px;
      margin-top: 12px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
      line-height: 1.6;
      white-space: pre-wrap;
      max-height: 400px;
      overflow-y: auto;
      color: #aaa;
    }
    .output-area.has-content { color: #e5e5e5; }

    .connector {
      display: flex;
      justify-content: center;
      padding: 8px 0;
      color: #444;
      font-size: 24px;
    }

    .spinner {
      display: inline-block;
      width: 16px; height: 16px;
      border: 2px solid #333;
      border-top-color: #7b68ee;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      margin-right: 8px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* Edit mode toggle */
    .edit-toggle {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #333;
      border: 1px solid #555;
      color: #e5e5e5;
      padding: 10px 16px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 13px;
    }

    .prompt-editor {
      display: none;
      margin-top: 8px;
    }
    .edit-mode .prompt-editor { display: block; }
    .prompt-editor textarea {
      width: 100%;
      min-height: 120px;
      background: #1a0a2e;
      border: 1px solid #7b68ee44;
      border-radius: 8px;
      padding: 10px;
      color: #c4b5fd;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>Build Planner — Prompt Chain Dashboard</h1>
    <p style="color:#666; font-size:13px; margin-top:4px;">Fill in each step, hit Run. Results feed into the next step automatically.</p>
  </div>

  <div class="chain-container" id="chainContainer">
    <!-- Chain steps rendered dynamically from config -->
    <p style="color:#666;">Loading chain configuration...</p>
  </div>

  <button class="edit-toggle" onclick="toggleEditMode()">Edit Prompts</button>

  <script>
    let chainConfig = [];
    let chainResults = {};
    let editMode = false;

    // Load chain config from Google Sheet on page load
    google.script.run
      .withSuccessHandler(renderChain)
      .withFailureHandler(e => {
        document.getElementById('chainContainer').innerHTML =
          '<p style="color:red;">Error loading config: ' + e.message + '</p>';
      })
      .getChainConfig();

    function renderChain(config) {
      chainConfig = config;
      const container = document.getElementById('chainContainer');
      container.innerHTML = '';

      config.forEach((step, i) => {
        const inputs = step.inputs.split(',').map(inp => inp.trim());

        let inputsHTML = inputs.map(inp => `
          <div class="input-group">
            <label>${inp}</label>
            ${inp.toLowerCase().includes('description') || inp.toLowerCase().includes('features') || inp.toLowerCase().includes('rules')
              ? `<textarea id="input-${i}-${inp}" rows="4" placeholder="Enter ${inp}..."></textarea>`
              : inp.toLowerCase().includes('select') || inp.toLowerCase().includes('model')
                ? `<select id="input-${i}-${inp}">
                    ${step.options ? step.options.split(',').map(o => `<option>${o.trim()}</option>`).join('') : ''}
                   </select>`
                : `<input type="text" id="input-${i}-${inp}" placeholder="Enter ${inp}...">`
            }
          </div>
        `).join('');

        const stepHTML = `
          <div class="chain-step" id="step-${i}">
            <div class="step-header">
              <div class="step-number" id="step-num-${i}">${i + 1}</div>
              <div class="step-name">${step.name}</div>
            </div>
            <p style="color:#888; font-size:13px; margin-bottom:12px;">${step.description || ''}</p>
            ${inputsHTML}
            <div class="prompt-editor">
              <label style="font-size:12px; color:#7b68ee;">Prompt Template (editable):</label>
              <textarea id="prompt-${i}">${step.promptTemplate}</textarea>
              <button onclick="savePrompt(${i})" style="margin-top:4px; background:#7b68ee33; border:1px solid #7b68ee; color:#c4b5fd; padding:4px 12px; border-radius:4px; cursor:pointer; font-size:12px;">Save</button>
            </div>
            <button class="run-btn" id="run-${i}" onclick="runStep(${i})">
              Run Step ${i + 1}
            </button>
            <div class="output-area" id="output-${i}">Output will appear here after running...</div>
          </div>
          ${i < config.length - 1 ? '<div class="connector">↓</div>' : ''}
        `;

        container.innerHTML += stepHTML;
      });
    }

    function runStep(stepIndex) {
      const step = chainConfig[stepIndex];
      const inputs = step.inputs.split(',').map(inp => inp.trim());
      const btn = document.getElementById(`run-${stepIndex}`);
      const outputEl = document.getElementById(`output-${stepIndex}`);
      const stepEl = document.getElementById(`step-${stepIndex}`);

      // Gather input values
      const inputValues = {};
      inputs.forEach(inp => {
        const el = document.getElementById(`input-${stepIndex}-${inp}`);
        if (el) inputValues[inp] = el.value;
      });

      // Include previous step's output
      if (stepIndex > 0 && chainResults[stepIndex - 1]) {
        inputValues['_previousOutput'] = chainResults[stepIndex - 1];
      }

      // Get current prompt template (might be edited)
      const promptEl = document.getElementById(`prompt-${stepIndex}`);
      const promptTemplate = promptEl ? promptEl.value : step.promptTemplate;

      // UI feedback
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span>Running...';
      stepEl.classList.add('active');
      stepEl.classList.remove('complete');
      outputEl.textContent = 'Calling Claude API...';
      outputEl.classList.remove('has-content');

      // Call Apps Script backend
      google.script.run
        .withSuccessHandler(result => {
          chainResults[stepIndex] = result;
          outputEl.textContent = result;
          outputEl.classList.add('has-content');
          btn.disabled = false;
          btn.innerHTML = `Re-run Step ${stepIndex + 1}`;
          stepEl.classList.remove('active');
          stepEl.classList.add('complete');
          document.getElementById(`step-num-${stepIndex}`).classList.add('complete');

          // Auto-populate next step's first input if it's a textarea
          if (stepIndex < chainConfig.length - 1) {
            const nextInputs = chainConfig[stepIndex + 1].inputs.split(',').map(i => i.trim());
            // Don't auto-fill — the backend handles chaining via _previousOutput
            // But scroll to next step
            document.getElementById(`step-${stepIndex + 1}`).scrollIntoView({
              behavior: 'smooth', block: 'start'
            });
          }
        })
        .withFailureHandler(err => {
          outputEl.textContent = 'ERROR: ' + err.message;
          btn.disabled = false;
          btn.innerHTML = `Retry Step ${stepIndex + 1}`;
          stepEl.classList.remove('active');
        })
        .executeChainStep(stepIndex, inputValues, promptTemplate);
    }

    function toggleEditMode() {
      editMode = !editMode;
      document.querySelector('.chain-container').classList.toggle('edit-mode', editMode);
      document.querySelector('.edit-toggle').textContent = editMode ? 'Hide Prompts' : 'Edit Prompts';
    }

    function savePrompt(stepIndex) {
      const promptEl = document.getElementById(`prompt-${stepIndex}`);
      google.script.run
        .withSuccessHandler(() => alert('Prompt saved!'))
        .savePromptTemplate(stepIndex, promptEl.value);
    }
  </script>
</body>
</html>
```

### Apps Script Backend (Code.gs)

```javascript
// ============================================================
// CONFIGURATION
// ============================================================

// Store API key in Script Properties (not in code!)
// Go to: Project Settings → Script Properties → Add:
//   Key: CLAUDE_API_KEY  Value: sk-ant-...
//   Key: CONFIG_SHEET_ID  Value: (your Google Sheet ID)

function getApiKey() {
  return PropertiesService.getScriptProperties().getProperty('CLAUDE_API_KEY');
}

function getConfigSheetId() {
  return PropertiesService.getScriptProperties().getProperty('CONFIG_SHEET_ID');
}

// ============================================================
// WEB APP ENTRY POINT
// ============================================================

function doGet() {
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle('Build Planner — Prompt Chain Dashboard')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// ============================================================
// CHAIN CONFIG (reads from Google Sheet)
// ============================================================

function getChainConfig() {
  const ss = SpreadsheetApp.openById(getConfigSheetId());
  const sheet = ss.getSheetByName('Chain Config');
  const data = sheet.getDataRange().getValues();

  // Skip header row
  const config = [];
  for (let i = 1; i < data.length; i++) {
    if (!data[i][0] && !data[i][1]) continue; // Skip empty rows
    config.push({
      step: data[i][0],           // Column A: Step number
      name: data[i][1],           // Column B: Step name
      description: data[i][2],    // Column C: Description
      promptTemplate: data[i][3], // Column D: Prompt template
      inputs: data[i][4],         // Column E: Comma-separated input field names
      options: data[i][5] || '',  // Column F: Options for dropdowns (optional)
      model: data[i][6] || 'claude-sonnet-4-6-20250514' // Column G: Model override
    });
  }

  return config;
}

// ============================================================
// EXECUTE A CHAIN STEP
// ============================================================

function executeChainStep(stepIndex, inputValues, promptTemplate) {
  const apiKey = getApiKey();
  if (!apiKey) throw new Error('No API key configured. Go to Script Properties and add CLAUDE_API_KEY.');

  // Build the prompt from template + inputs
  let prompt = promptTemplate;

  // Replace {{placeholders}} with input values
  for (const [key, value] of Object.entries(inputValues)) {
    if (key === '_previousOutput') {
      prompt = prompt.replace(/\{\{previousOutput\}\}/g, value);
      prompt = prompt.replace(/\{\{previous_output\}\}/g, value);
      prompt = prompt.replace(/\{\{PREVIOUS_OUTPUT\}\}/g, value);
    } else {
      const regex = new RegExp(`\\{\\{${key}\\}\\}`, 'g');
      prompt = prompt.replace(regex, value);
    }
  }

  // Call Claude API
  const response = UrlFetchApp.fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01'
    },
    payload: JSON.stringify({
      model: 'claude-sonnet-4-6-20250514',
      max_tokens: 8192,
      messages: [{
        role: 'user',
        content: prompt
      }]
    }),
    muteHttpExceptions: true
  });

  const json = JSON.parse(response.getContentText());

  if (json.error) {
    throw new Error(json.error.message);
  }

  const result = json.content[0].text;

  // Log to history
  logRun(stepIndex, prompt, result);

  return result;
}

// ============================================================
// SAVE EDITED PROMPT TEMPLATE
// ============================================================

function savePromptTemplate(stepIndex, newTemplate) {
  const ss = SpreadsheetApp.openById(getConfigSheetId());
  const sheet = ss.getSheetByName('Chain Config');

  // Step index is 0-based, rows are 1-based with header = row 1
  const row = stepIndex + 2; // +1 for header, +1 for 0-index
  sheet.getRange(row, 4).setValue(newTemplate); // Column D = prompt template
}

// ============================================================
// RUN HISTORY LOGGING
// ============================================================

function logRun(stepIndex, prompt, result) {
  const ss = SpreadsheetApp.openById(getConfigSheetId());
  let history = ss.getSheetByName('Run History');

  if (!history) {
    history = ss.insertSheet('Run History');
    history.appendRow(['Timestamp', 'Step', 'Prompt (first 500 chars)', 'Result (first 500 chars)']);
  }

  history.appendRow([
    new Date().toISOString(),
    stepIndex + 1,
    prompt.substring(0, 500),
    result.substring(0, 500)
  ]);
}

// ============================================================
// UTILITY: Test API connection
// ============================================================

function testApiConnection() {
  const apiKey = getApiKey();
  if (!apiKey) {
    Logger.log('No API key found in Script Properties');
    return;
  }

  const response = UrlFetchApp.fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01'
    },
    payload: JSON.stringify({
      model: 'claude-sonnet-4-6-20250514',
      max_tokens: 100,
      messages: [{ role: 'user', content: 'Say "API connected!" and nothing else.' }]
    }),
    muteHttpExceptions: true
  });

  Logger.log(response.getContentText());
}
```

---

## HOW TO ADD/REMOVE/EDIT CHAINS (No Code Needed)

### The "Chain Config" Google Sheet Tab

This is the control panel. Each row = one chain step.

```
| A: Step | B: Name          | C: Description                          | D: Prompt Template                    | E: Inputs              | F: Options        |
|---------|------------------|-----------------------------------------|---------------------------------------|------------------------|-------------------|
| 1       | Make PRD         | Turns your app idea into a detailed PRD | You are a senior architect...{{app}}  | App Name,Description,  |                   |
|         |                  |                                         | ...{{features}}...                    | Features,Tech Stack    |                   |
| 2       | Split Phases     | Divides PRD into build phases           | Take this PRD: {{previousOutput}}...  | Number of Phases       | 2,3,4,5           |
|         |                  |                                         | Split into {{Number of Phases}}...    |                        |                   |
| 3       | Build Scripts    | Generates the actual bash scripts       | Generate build scripts for:           | Model,Turns per Phase  | Sonnet,Opus,Haiku |
|         |                  |                                         | {{previousOutput}}...                 |                        |                   |
```

### To Add a Chain Step:

1. Open the Google Sheet
2. Go to "Chain Config" tab
3. Add a new row at the bottom
4. Fill in: step number, name, description, prompt template (with {{placeholders}}), input field names
5. Refresh the web app
6. New step appears automatically

### To Remove a Chain Step:

1. Delete the row from "Chain Config"
2. Refresh the web app
3. Step is gone

### To Edit a Prompt Template:

**Option A (Sheet):** Edit column D directly in the Sheet

**Option B (In-App):** Click "Edit Prompts" button in the web app, edit inline, click "Save"

### To Reorder Steps:

Move rows up/down in the Sheet. Update step numbers.

---

## EMBEDDING ON YOUR OWN SITE

### As an iframe:

```html
<iframe
  src="https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec"
  width="100%"
  height="900px"
  style="border: none; border-radius: 12px;"
></iframe>
```

### As an AutoForge page:

Create a React component that wraps the iframe, or port the HTML directly into a React component that calls your FastAPI backend instead of Apps Script.

```tsx
// ui/src/components/PromptChainDashboard.tsx
export function PromptChainDashboard() {
  return (
    <iframe
      src="https://script.google.com/macros/s/YOUR_ID/exec"
      className="w-full h-full border-0 rounded-xl"
      title="Prompt Chain Dashboard"
    />
  );
}
```

Or build it natively in React using the same patterns — input fields, step cards, API calls to your FastAPI backend which calls Claude. Same UX, no Google dependency.
