# Build Planner — Google Sheet System Blueprint

> **What this is:** A complete Google Sheet design that serves as a reusable build planning tool.
> Users fill in project details, lock in their templates/rules, and press buttons to generate
> LLM prompts (or call Claude directly via Apps Script). Everything is editable and saveable.

---

## OVERVIEW: How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    GOOGLE SHEET: BUILD PLANNER                  │
│                                                                 │
│  TAB 1: "My Templates"          (their locked-in stuff)         │
│  ┌───────────────────────────────────────────────┐              │
│  │ Agent OS Framework        [editable text box]  │              │
│  │ Coding Rules              [editable text box]  │              │
│  │ PRD Template Format       [editable text box]  │              │
│  │ Phase-Split Instructions  [editable text box]  │              │
│  │ Testing Rules             [editable text box]  │              │
│  └───────────────────────────────────────────────┘              │
│  They buy yours → paste in → "locked in"                        │
│  They learn more → edit → save → new "locked in"                │
│                                                                 │
│  TAB 2: "New Build"             (per-project answers)           │
│  ┌───────────────────────────────────────────────┐              │
│  │ App name, description, features, etc.          │              │
│  │ (the 20 questions from the form)               │              │
│  └───────────────────────────────────────────────┘              │
│                                                                 │
│  TAB 3: "Generate"             (the magic buttons)              │
│  ┌───────────────────────────────────────────────┐              │
│  │ [BUTTON 1] → Make PRD Prompt                   │              │
│  │   Combines: answers + Agent OS + rules          │              │
│  │   Output: ready-to-paste LLM prompt             │              │
│  │                                                 │              │
│  │ [BUTTON 2] → Make Phase-Split Prompt            │              │
│  │   Takes PRD output + phase math (50% rule)      │              │
│  │   Output: ready-to-paste LLM prompt             │              │
│  │                                                 │              │
│  │ [BUTTON 3] → Make Build Scripts Prompt           │              │
│  │   Takes phases + rules + settings               │              │
│  │   Output: ready-to-paste LLM prompt             │              │
│  └───────────────────────────────────────────────┘              │
│                                                                 │
│  TAB 4: "Output"               (generated results)             │
│  ┌───────────────────────────────────────────────┐              │
│  │ PRD Prompt         [big text area]              │              │
│  │ PRD Result         [paste back or auto-fill]    │              │
│  │ Phase-Split Prompt [big text area]              │              │
│  │ Phase-Split Result [paste back or auto-fill]    │              │
│  │ Build Scripts      [final output]               │              │
│  └───────────────────────────────────────────────┘              │
│                                                                 │
│  TAB 5: "History"              (past builds)                   │
│  ┌───────────────────────────────────────────────┐              │
│  │ Date | App Name | PRD | Phases | Scripts       │              │
│  │ Save each build for reference                   │              │
│  └───────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## TAB 1: "My Templates" — The Locked-In Stuff

This is where they store their reusable templates. Buy yours → paste in. Learn more → edit → save.

### Cell Layout

| Row | Column A (Label) | Column B (Content Cell) | Notes |
|-----|-----------------|------------------------|-------|
| 1 | **MY BUILD TEMPLATES** | *Instructions: Edit these anytime. They get pulled into every build.* | Header row, merged |
| 3 | **Agent OS Framework** | `[Large merged cell B3:F20]` | The big one — the framework/format for how the PRD gets structured |
| 22 | **Coding Rules** | `[Large merged cell B22:F39]` | Their coding standards — what Claude follows in every file |
| 41 | **PRD Template Format** | `[Large merged cell B41:F58]` | The format/structure the PRD should follow |
| 60 | **Phase-Split Instructions** | `[Large merged cell B60:F72]` | Rules for how to divide PRD into phases (the 50% rule, etc.) |
| 74 | **Testing Rules** | `[Large merged cell B74:F86]` | Test commands, verification approach |
| 88 | **Additional Prompt Instructions** | `[Large merged cell B88:F100]` | Any extra stuff they want in every prompt |

**Free version:** All cells are blank. They fill them in themselves.
**Pro version:** Cells come pre-filled with your battle-tested content. They can still edit.

### How "Locking In" Works

Google Sheets doesn't have a literal lock button, but here's the UX:

1. **They edit the cell** → it auto-saves (Google Sheets always auto-saves)
2. **That's it** — it's "locked in" because it persists across every new build
3. **To change:** just edit the cell again, it auto-saves the new version
4. **To reset to your defaults:** You provide a "Reset to Defaults" button (Apps Script) that restores your original content

So "lock in, change, lock in" = just editing and saving. No special mechanism needed.

---

## TAB 2: "New Build" — Per-Project Answers

This is the 20-question worksheet, laid out as a form-like sheet.

### Cell Layout

| Row | Column A (Label) | Column B (Answer Cell) | Column C (Helper Text) |
|-----|-----------------|----------------------|----------------------|
| 1 | **NEW BUILD** | | *Fill in your project details below* |
| 3 | **App Name** | `[text input]` | *Keep it short — becomes your folder name* |
| 5 | **App Description** | `[large text]` | *2-3 sentences. What does it do, who is it for?* |
| 8 | **Tech Stack** | `[dropdown: React+Python, React+Node, Next.js, etc.]` | *Not sure? Pick React + Python* |
| 10 | **Custom Stack** | `[text, grayed if not "Other"]` | *Only if you picked Other above* |
| 13 | **FEATURES** | | |
| 14 | **Feature 1** | `[text]` | **Size:** `[dropdown: S/M/L]` |
| 15 | **Feature 2** | `[text]` | **Size:** `[dropdown: S/M/L]` |
| ... | *(up to 20 features)* | | |
| 35 | **Dependencies** | `[large text]` | *Which features depend on others?* |
| 38 | **BUILD SETTINGS** | | |
| 39 | **Model** | `[dropdown: Sonnet/Opus/Haiku]` | |
| 40 | **Turns per phase** | `[dropdown: 10/25/50/Unlimited]` | |
| 41 | **Phase transition** | `[dropdown: Pause/Auto/Prompt]` | |
| 42 | **Error handling** | `[dropdown: Retry+Skip/Stop/Skip]` | |
| 43 | **Git commits** | `[dropdown: Per feature/Per phase/Never]` | |
| 45 | **PHASE PLANNING** | | |
| 46 | **Number of phases** | `[dropdown: 2/3/4/5/6+]` | |
| 47 | **Phase assignments** | `[large text]` | *Which features in which phase?* |
| 50 | **Anything else** | `[large text]` | |

### Data Validation (Built into Google Sheets)

- Dropdowns use Data Validation → List of items
- Large text cells are merged across columns B-F
- Helper text in column C is gray italic
- Conditional formatting: grays out "Custom Stack" unless "Other" is selected

---

## TAB 3: "Generate" — The Magic Buttons

Three buttons. Each one assembles a prompt from the other tabs.

### Layout

```
Row 1:  ╔══════════════════════════════════════════════════════╗
        ║  STEP 1: GENERATE PRD                                ║
        ║                                                      ║
        ║  This combines your project answers (Tab 2) with     ║
        ║  your Agent OS framework and PRD template (Tab 1)    ║
        ║  into a prompt that tells an LLM to write your PRD.  ║
        ║                                                      ║
        ║  [ 🔨 GENERATE PRD PROMPT ]     ← Apps Script button ║
        ║                                                      ║
        ║  Output appears in Tab 4, Section 1.                 ║
        ║  Copy it → paste into Claude/ChatGPT → paste result  ║
        ║  back into Tab 4, Section 1 "PRD Result" box.        ║
        ╚══════════════════════════════════════════════════════╝

Row 15: ╔══════════════════════════════════════════════════════╗
        ║  STEP 2: SPLIT INTO PHASES                           ║
        ║                                                      ║
        ║  Takes your PRD (from Step 1) and splits it into     ║
        ║  phases using the 50% rule and your phase settings.  ║
        ║                                                      ║
        ║  [ 🔨 GENERATE PHASE-SPLIT PROMPT ]                  ║
        ║                                                      ║
        ║  Output appears in Tab 4, Section 2.                 ║
        ╚══════════════════════════════════════════════════════╝

Row 29: ╔══════════════════════════════════════════════════════╗
        ║  STEP 3: GENERATE BUILD SCRIPTS                      ║
        ║                                                      ║
        ║  Takes your phases + coding rules + settings and     ║
        ║  generates the final bash scripts.                   ║
        ║                                                      ║
        ║  [ 🔨 GENERATE BUILD SCRIPTS PROMPT ]                ║
        ║                                                      ║
        ║  Output appears in Tab 4, Section 3.                 ║
        ╚══════════════════════════════════════════════════════╝
```

---

## TAB 4: "Output" — Where Results Land

### Layout

```
SECTION 1: PRD
┌─────────────────────────────────────────────┐
│ PRD PROMPT (auto-generated, read-only)       │
│ [Large cell - shows the assembled prompt]    │
│                                              │
│ ↓ Copy this, paste into Claude, paste back ↓ │
│                                              │
│ PRD RESULT (paste here or auto-filled)       │
│ [Large editable cell]                        │
└─────────────────────────────────────────────┘

SECTION 2: PHASE SPLIT
┌─────────────────────────────────────────────┐
│ PHASE-SPLIT PROMPT (auto-generated)          │
│ [Large cell]                                 │
│                                              │
│ PHASE-SPLIT RESULT (paste here)              │
│ [Large editable cell]                        │
└─────────────────────────────────────────────┘

SECTION 3: BUILD SCRIPTS
┌─────────────────────────────────────────────┐
│ BUILD SCRIPTS PROMPT (auto-generated)        │
│ [Large cell]                                 │
│                                              │
│ BUILD SCRIPTS RESULT (paste here)            │
│ [Large editable cell - final output]         │
└─────────────────────────────────────────────┘
```

---

## APPS SCRIPT CODE (The Glue)

This is Google Apps Script (JavaScript) that runs inside the Google Sheet.
Access via: Extensions → Apps Script

### Button 1: Generate PRD Prompt

```javascript
function generatePRDPrompt() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const templates = ss.getSheetByName('My Templates');
  const build = ss.getSheetByName('New Build');
  const output = ss.getSheetByName('Output');

  // Pull templates (Tab 1)
  const agentOS = templates.getRange('B3').getValue();
  const codingRules = templates.getRange('B22').getValue();
  const prdTemplate = templates.getRange('B41').getValue();
  const additionalInstructions = templates.getRange('B88').getValue();

  // Pull project answers (Tab 2)
  const appName = build.getRange('B3').getValue();
  const appDescription = build.getRange('B5').getValue();
  const techStack = build.getRange('B8').getValue();

  // Pull features (rows 14-33)
  let features = '';
  for (let i = 14; i <= 33; i++) {
    const feat = build.getRange('B' + i).getValue();
    const size = build.getRange('D' + i).getValue();
    if (feat) {
      features += `${i - 13}. ${feat} — ${size}\n`;
    }
  }

  const dependencies = build.getRange('B35').getValue();
  const anythingElse = build.getRange('B50').getValue();

  // Assemble the prompt
  const prompt = `You are a senior software architect. Your job is to create a detailed PRD
(Product Requirements Document) for the following application.

=== APPLICATION ===
Name: ${appName}
Description: ${appDescription}
Tech Stack: ${techStack}

=== FEATURES ===
${features}

=== FEATURE DEPENDENCIES ===
${dependencies}

=== ADDITIONAL CONTEXT ===
${anythingElse}

=== PRD FORMAT TO FOLLOW ===
Use this exact format/structure for the PRD:

${prdTemplate}

=== AGENT OS FRAMEWORK ===
Structure the PRD so it works with this framework:

${agentOS}

=== CODING STANDARDS (for reference) ===
The coder will follow these rules. Write the PRD knowing these constraints:

${codingRules}

=== ADDITIONAL INSTRUCTIONS ===
${additionalInstructions}

=== YOUR TASK ===
Create a comprehensive PRD following the format above. Include:
1. Every feature listed, with detailed acceptance criteria
2. Technical architecture decisions based on the tech stack
3. Data models and API endpoints
4. UI/UX flow descriptions
5. Edge cases and error handling requirements

Output the complete PRD. Do not summarize or abbreviate.`;

  // Write to Output tab
  output.getRange('B3').setValue(prompt);

  // Show confirmation
  SpreadsheetApp.getUi().alert(
    'PRD Prompt Generated!',
    'Go to the Output tab → Section 1 to see your prompt.\n\n' +
    'Copy it, paste into Claude or ChatGPT, then paste the result back into the "PRD Result" box.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}
```

### Button 2: Generate Phase-Split Prompt

```javascript
function generatePhaseSplitPrompt() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const templates = ss.getSheetByName('My Templates');
  const build = ss.getSheetByName('New Build');
  const output = ss.getSheetByName('Output');

  // Pull the PRD result (they pasted it back)
  const prdResult = output.getRange('B8').getValue();

  if (!prdResult) {
    SpreadsheetApp.getUi().alert(
      'Missing PRD!',
      'You need to paste your PRD result into Tab 4, Section 1 first.\n\n' +
      'Steps:\n1. Copy the PRD Prompt from Tab 4\n2. Paste into Claude\n3. Copy Claude\'s response\n4. Paste into "PRD Result" in Tab 4',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    return;
  }

  // Pull settings
  const phaseCount = build.getRange('B46').getValue();
  const phaseAssignments = build.getRange('B47').getValue();
  const phaseSplitRules = templates.getRange('B60').getValue();
  const turnsPerPhase = build.getRange('B40').getValue();

  // Pull features for counting
  let featureCount = 0;
  for (let i = 14; i <= 33; i++) {
    if (build.getRange('B' + i).getValue()) featureCount++;
  }

  // Calculate phase math
  const featuresPerPhase = Math.ceil(featureCount / parseInt(phaseCount) || 3);

  const prompt = `You are a build planning expert. Your job is to split this PRD into
${phaseCount} build phases that will each run as a separate Claude Code session.

=== THE PRD ===
${prdResult}

=== PHASE SPLITTING RULES ===
${phaseSplitRules}

=== THE 50% RULE ===
Phase 1 gets UP TO 50% of the context window for setup instructions and coding rules.
The remaining phases get lighter instructions (just "read existing code and continue").
This means Phase 1 should have FEWER features (2-3 max) because the prompt is already heavy.

=== USER'S PREFERRED ASSIGNMENTS ===
${phaseAssignments || 'No preference — use your best judgment based on dependencies.'}

=== CONSTRAINTS ===
- Total features: ${featureCount}
- Target phases: ${phaseCount}
- Suggested features per phase: ${featuresPerPhase} (adjust based on complexity)
- Max turns per phase: ${turnsPerPhase}
- Phase 1 MUST include: project skeleton setup, dependency installation, base layout
- Dependencies: features that depend on others go in LATER phases
- Each phase must be completable in a single Claude Code session

=== YOUR TASK ===
Output a detailed phase plan:

For each phase, provide:
1. Phase number and name (e.g., "Phase 1: Foundation & Auth")
2. Which features are included (by number and name)
3. What the phase prompt should emphasize
4. Expected complexity (light / medium / heavy)
5. Any special instructions for that phase

Then provide a summary table showing the phase distribution.`;

  output.getRange('B15').setValue(prompt);

  SpreadsheetApp.getUi().alert(
    'Phase-Split Prompt Generated!',
    'Go to the Output tab → Section 2.\n\nCopy → paste into Claude → paste result back.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}
```

### Button 3: Generate Build Scripts Prompt

```javascript
function generateBuildScriptsPrompt() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const templates = ss.getSheetByName('My Templates');
  const build = ss.getSheetByName('New Build');
  const output = ss.getSheetByName('Output');

  // Pull the phase-split result
  const phasePlan = output.getRange('B20').getValue();

  if (!phasePlan) {
    SpreadsheetApp.getUi().alert(
      'Missing Phase Plan!',
      'Complete Step 2 first — paste your phase-split result into Tab 4, Section 2.',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    return;
  }

  // Pull all templates
  const agentOS = templates.getRange('B3').getValue();
  const codingRules = templates.getRange('B22').getValue();
  const testingRules = templates.getRange('B74').getValue();
  const additionalInstructions = templates.getRange('B88').getValue();

  // Pull settings
  const model = build.getRange('B39').getValue();
  const turnsPerPhase = build.getRange('B40').getValue();
  const phaseTransition = build.getRange('B41').getValue();
  const errorHandling = build.getRange('B42').getValue();
  const gitCommits = build.getRange('B43').getValue();
  const appName = build.getRange('B3').getValue();

  // Map settings to script values
  const modelMap = { 'Sonnet': 'sonnet', 'Opus': 'opus', 'Haiku': 'haiku' };
  const turnsMap = { '10': '10', '25': '25', '50': '50', 'Unlimited': '0' };

  const prompt = `You are a build automation expert. Generate bash scripts for a phased
Claude Code build based on the following plan and settings.

=== PHASE PLAN ===
${phasePlan}

=== BUILD SETTINGS ===
- App name: ${appName}
- Model: ${model} (use: ${modelMap[model] || 'sonnet'})
- Max turns per phase: ${turnsPerPhase} (use: ${turnsMap[turnsPerPhase] || '25'})
- Between phases: ${phaseTransition}
- On error: ${errorHandling}
- Git: ${gitCommits}

=== CODING RULES (include in Phase 1 prompt, summarize in Phase 2+) ===
${codingRules}

=== TESTING RULES (include in Phase 2+ prompts) ===
${testingRules}

=== AGENT OS FRAMEWORK ===
${agentOS}

=== ADDITIONAL INSTRUCTIONS ===
${additionalInstructions}

=== YOUR TASK ===
Generate the following files:

1. **phase1.sh** through **phaseN.sh** — One script per phase
   - Each calls: claude --model ${modelMap[model] || 'sonnet'} --max-turns ${turnsMap[turnsPerPhase] || '25'} --print "..."
   - Phase 1 prompt includes: full coding rules, setup instructions, Phase 1 features
   - Phase 2+ prompts include: "Read ALL existing code first", abbreviated rules, that phase's features
   - Each prompt references the Agent OS framework structure

2. **run_all.sh** — Master script that runs phases in order
   - Between phases: ${phaseTransition === 'Pause' ? 'echo "Phase X complete. Review and press Enter to continue..." && read' : phaseTransition === 'Auto-continue' ? 'echo "Phase X complete. Starting next phase in 5 seconds..." && sleep 5' : 'read -p "Continue to next phase? (y/n) " && [[ $REPLY == "y" ]]'}
   - Git commits: ${gitCommits === 'After each feature' ? 'After each phase script completes' : gitCommits}

3. **README.md** — Quick-start instructions

Output each file with its complete contents. Use code blocks with filenames.`;

  output.getRange('B27').setValue(prompt);

  SpreadsheetApp.getUi().alert(
    'Build Scripts Prompt Generated!',
    'Go to the Output tab → Section 3.\n\nThis is the final step — copy the prompt, paste into Claude, and you\'ll get your build scripts!',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}
```

### Menu Setup (runs once)

```javascript
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Build Planner')
    .addItem('Step 1: Generate PRD Prompt', 'generatePRDPrompt')
    .addItem('Step 2: Generate Phase-Split Prompt', 'generatePhaseSplitPrompt')
    .addItem('Step 3: Generate Build Scripts Prompt', 'generateBuildScriptsPrompt')
    .addSeparator()
    .addItem('Reset Templates to Defaults', 'resetTemplates')
    .addItem('Save Build to History', 'saveBuildToHistory')
    .addItem('Clear New Build Form', 'clearBuildForm')
    .addToUi();
}
```

### Reset Templates (restores your defaults)

```javascript
function resetTemplates() {
  const ui = SpreadsheetApp.getUi();
  const response = ui.alert(
    'Reset Templates?',
    'This will replace all your templates with the original defaults. Your current templates will be lost. Continue?',
    ui.ButtonSet.YES_NO
  );

  if (response !== ui.Button.YES) return;

  const templates = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('My Templates');

  // These are YOUR defaults — the pro content they paid for
  // Replace these strings with your actual template content

  templates.getRange('B3').setValue(
    '--- PASTE YOUR AGENT OS FRAMEWORK DEFAULT HERE ---\n' +
    'This is where your Agent OS / PRD format goes.\n' +
    'Pro users get this pre-filled with your battle-tested framework.'
  );

  templates.getRange('B22').setValue(
    '--- PASTE YOUR CODING RULES DEFAULT HERE ---\n' +
    'Pro users get 50-100 lines of battle-tested coding standards.'
  );

  templates.getRange('B41').setValue(
    '--- PASTE YOUR PRD TEMPLATE DEFAULT HERE ---\n' +
    'The structure/format that PRDs should follow.'
  );

  templates.getRange('B60').setValue(
    '--- PASTE YOUR PHASE-SPLIT RULES DEFAULT HERE ---\n' +
    'The 50% rule, dependency ordering, phase sizing logic.'
  );

  templates.getRange('B74').setValue(
    '--- PASTE YOUR TESTING RULES DEFAULT HERE ---\n' +
    'Test commands, verification approach, quality gates.'
  );

  templates.getRange('B88').setValue(
    '--- PASTE YOUR ADDITIONAL INSTRUCTIONS DEFAULT HERE ---'
  );

  ui.alert('Templates reset to defaults.');
}
```

### Save Build to History

```javascript
function saveBuildToHistory() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const build = ss.getSheetByName('New Build');
  const output = ss.getSheetByName('Output');
  let history = ss.getSheetByName('History');

  if (!history) {
    history = ss.insertSheet('History');
    history.appendRow(['Date', 'App Name', 'Description', 'Tech Stack', 'Features', 'PRD', 'Phase Plan', 'Build Scripts']);
  }

  history.appendRow([
    new Date().toLocaleDateString(),
    build.getRange('B3').getValue(),
    build.getRange('B5').getValue(),
    build.getRange('B8').getValue(),
    build.getRange('B14').getValue(), // First feature as summary
    output.getRange('B8').getValue().substring(0, 500), // PRD excerpt
    output.getRange('B20').getValue().substring(0, 500),
    output.getRange('B33').getValue().substring(0, 500)
  ]);

  SpreadsheetApp.getUi().alert('Build saved to History tab!');
}
```

---

## TWO VERSIONS: FREE vs PRO

### FREE Version (Lead Magnet)

What they get:
- The Google Sheet with all 5 tabs
- All 3 buttons work
- All Apps Script code works
- **Templates tab is BLANK** — they have to fill in their own rules

What's missing:
- No coding rules (generic "use latest stable versions")
- No PRD template (they wing it)
- No phase-split rules (they guess)
- No Agent OS framework

The free version WORKS. They can build stuff. But the output quality depends entirely on their template quality, which will be... okay at best.

### PRO Version ($97-$495)

Same sheet, but:
- **Templates tab is PRE-FILLED** with your battle-tested content
- Agent OS framework: your actual framework
- Coding rules: your 50-100 lines of standards
- PRD template: your proven format
- Phase-split rules: the 50% rule, dependency logic, sizing
- Testing rules: your verification approach

The "Reset to Defaults" button restores YOUR content (not blank).

### DELUXE Version ($495-$1,495)

Same as Pro, PLUS:
- Direct Claude API integration (no copy-paste needed)
- They add their API key to a Settings tab
- Buttons call Claude directly and write results back
- One-click end-to-end: answers → PRD → phases → scripts

---

## OPTIONAL: DIRECT API INTEGRATION (Deluxe)

For the deluxe version, replace the "copy-paste" flow with direct API calls.
Users add their Claude API key to a Settings tab.

```javascript
function callClaudeAPI(prompt) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const settings = ss.getSheetByName('Settings');
  const apiKey = settings.getRange('B3').getValue(); // Their API key

  if (!apiKey) {
    SpreadsheetApp.getUi().alert(
      'API Key Required',
      'Add your Claude API key to the Settings tab (cell B3) to use direct generation.\n\n' +
      'Get one at: console.anthropic.com',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    return null;
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
    SpreadsheetApp.getUi().alert('API Error: ' + json.error.message);
    return null;
  }

  return json.content[0].text;
}

// Direct generation version of Button 1
function generatePRDDirect() {
  // Build the same prompt as generatePRDPrompt()...
  // Then call Claude directly:
  const result = callClaudeAPI(prompt);
  if (result) {
    const output = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Output');
    output.getRange('B3').setValue(prompt);  // Show the prompt
    output.getRange('B8').setValue(result);  // Auto-fill the result
    SpreadsheetApp.getUi().alert('PRD generated! Check the Output tab.');
  }
}
```

---

## THE WORKFLOW (User's Perspective)

### Free User

```
1. Get the free Google Sheet (make a copy)
2. Tab 1: Templates are blank — fill in what you know
3. Tab 2: Fill in project details (app name, features, etc.)
4. Tab 3: Click "Generate PRD Prompt"
5. Tab 4: Copy the prompt → paste into Claude → paste result back
6. Tab 3: Click "Generate Phase-Split Prompt"
7. Tab 4: Copy → Claude → paste back
8. Tab 3: Click "Generate Build Scripts Prompt"
9. Tab 4: Copy → Claude → get your scripts!

They realize: "My rules suck. My PRD came out generic. I need better templates."
→ Upsell to Pro
```

### Pro User

```
1. Get the Pro Google Sheet (templates pre-filled with your content)
2. Tab 1: Review templates — maybe tweak for their project
3. Tab 2: Fill in project details
4-9: Same flow, but WAY better output because templates are pro-grade

They realize: "This copy-paste flow is tedious. I wish it was automated."
→ Upsell to Deluxe or the One-Pager App
```

### Deluxe User

```
1. Get the Deluxe Google Sheet
2. Tab Settings: Add their Claude API key
3. Tab 1: Templates pre-filled (editable)
4. Tab 2: Fill in project details
5. Tab 3: Click "Generate PRD" → auto-fills result
6. Tab 3: Click "Split Phases" → auto-fills result
7. Tab 3: Click "Generate Scripts" → done!

They realize: "This is great but I want a real app interface."
→ Upsell to the One-Pager web app
```

---

## FUNNEL RECAP

```
FREE Google Sheet (blank templates)
  ↓ "My output is generic, I need better rules"
PRO Google Sheet ($97-$495, pre-filled templates)
  ↓ "Copy-paste is tedious"
DELUXE Google Sheet ($495-$1,495, direct API calls)
  ↓ "I want a real app, not a spreadsheet"
ONE-PAGER WEB APP ($29-$49/mo)
  ↓ "I want full automation with dashboard"
BUILD ORCHESTRATOR ($79-$149/mo)
```

Each tier solves a real pain point from the tier below.
Each tier is a genuine "damn, that's worth it" upgrade.
