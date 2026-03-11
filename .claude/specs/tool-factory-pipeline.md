# The Stack: What You Already Have & How It Connects

> **The realization:** You don't need to build new apps. You have Style Set (themes),
> Google Sheets (UI/forms), Apps Script (backend/AI calls), and AutoForge (hosting/SDK).
> These four pieces connect into a tool factory. Build any tool in minutes, not weeks.

---

## WHAT YOU HAVE RIGHT NOW

| Piece | What It Does | Status |
|-------|-------------|--------|
| **Style Set** | Screenshot → theme JSON → any format (CSS, WordPress, Astro, shadcn) | Built / nearly built |
| **Google Sheets** | Free UI framework — looks like an app when styled | Available now |
| **Apps Script** | Free backend — runs JavaScript, calls APIs, hosted by Google | Available now |
| **AutoForge** | Your platform — has SDK wrapper, Claude subscription, hosting | Built |
| **Theme-to-CSS converter** | Takes Style Set JSON → CSS variables | Spec'd (in theming-spec.md) |
| **Prompt chain logic** | Multi-step AI workflows with chaining | Spec'd (in prompt-chain-dashboard.md) |

---

## THE DYNAMIC UI TRICK (No AI Needed)

The "+" button to add/remove text boxes is pure JavaScript. Zero AI involvement.

### How It Works

```
User clicks [+] → JavaScript creates a new <textarea> element → done
User clicks [-] → JavaScript removes the last <textarea> → done
User clicks [Combine] → JavaScript reads ALL textareas → sends to AI → gets combined result
```

### The Code (Goes in the Apps Script Web App HTML)

```html
<div id="rules-container">
  <!-- Text boxes appear here dynamically -->
</div>

<div class="button-row">
  <button onclick="addBox()" class="icon-btn">+ Add Rule Block</button>
  <button onclick="removeBox()" class="icon-btn">- Remove Last</button>
  <button onclick="combineRules()" class="run-btn">Combine All Into One</button>
</div>

<div id="combined-output" class="output-area">
  Combined rules will appear here...
</div>

<script>
let boxCount = 0;

function addBox() {
  boxCount++;
  const container = document.getElementById('rules-container');

  const wrapper = document.createElement('div');
  wrapper.className = 'input-group';
  wrapper.id = 'rule-box-' + boxCount;

  const label = document.createElement('label');
  label.textContent = 'Rule Block ' + boxCount;

  const textarea = document.createElement('textarea');
  textarea.className = 'rule-input';
  textarea.rows = 4;
  textarea.placeholder = 'Paste or type a rule block here...';

  wrapper.appendChild(label);
  wrapper.appendChild(textarea);
  container.appendChild(wrapper);

  // Smooth scroll to the new box
  wrapper.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function removeBox() {
  if (boxCount === 0) return;
  const el = document.getElementById('rule-box-' + boxCount);
  if (el) el.remove();
  boxCount--;
}

function combineRules() {
  // Grab ALL text boxes, however many there are
  const inputs = document.querySelectorAll('.rule-input');
  const blocks = [];

  inputs.forEach((input, i) => {
    if (input.value.trim()) {
      blocks.push('Block ' + (i + 1) + ':\n' + input.value.trim());
    }
  });

  if (blocks.length === 0) {
    alert('Add some rule blocks first!');
    return;
  }

  const prompt = `I have ${blocks.length} separate rule blocks for an AI coding agent.
Combine them into ONE cohesive, non-redundant set of rules.
Remove duplicates. Resolve conflicts (later blocks take priority).
Keep the same level of detail. Output as a single formatted document.

${blocks.join('\n\n---\n\n')}`;

  // THIS is the only part that calls AI
  const outputEl = document.getElementById('combined-output');
  outputEl.textContent = 'Combining...';

  google.script.run
    .withSuccessHandler(result => {
      outputEl.textContent = result;
      outputEl.classList.add('has-content');
    })
    .withFailureHandler(err => {
      outputEl.textContent = 'Error: ' + err.message;
    })
    .callClaude(prompt);
}

// Start with 3 boxes
addBox(); addBox(); addBox();
</script>
```

### The Backend (One function in Apps Script)

```javascript
function callClaude(prompt) {
  const apiKey = PropertiesService.getScriptProperties().getProperty('CLAUDE_API_KEY');

  const response = UrlFetchApp.fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01'
    },
    payload: JSON.stringify({
      model: 'claude-sonnet-4-6-20250514',
      max_tokens: 4096,
      messages: [{ role: 'user', content: prompt }]
    }),
    muteHttpExceptions: true
  });

  const json = JSON.parse(response.getContentText());
  if (json.error) throw new Error(json.error.message);
  return json.content[0].text;
}
```

That's it. The entire "add more boxes" feature is ~40 lines of JavaScript.
No AI rebuilds the page. No code changes needed. Ever.

**Today it has 3 boxes. Tomorrow the user clicks [+] twice and now it has 5.**
**Next week they click [-] three times and now it has 2.**
**The "Combine" button always grabs however many boxes exist.**

---

## AUTOFORGE INTEGRATION: Two Options

### Option A: Embed the Google Sheet Web App in AutoForge (5 minutes)

Add a route in AutoForge that serves an iframe pointing to your Apps Script Web App.

```tsx
// ui/src/pages/ToolBuilder.tsx
export function ToolBuilder() {
  return (
    <div className="w-full h-screen">
      <iframe
        src="https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec"
        className="w-full h-full border-0"
        title="Tool Builder"
      />
    </div>
  );
}
```

**Pros:** Instant. No building. Uses Google's hosting.
**Cons:** Uses their API key (not your SDK wrapper). Looks slightly embedded.

### Option B: Build It Native in AutoForge (1-2 hours)

Take the same HTML/CSS/JS from the Apps Script Web App and make it a React component.
Instead of calling `google.script.run.callClaude()`, call your FastAPI backend.
Your backend uses the SDK wrapper (their subscription, not a separate API key).

```tsx
// ui/src/pages/ToolBuilder.tsx
import { useState } from 'react';

export function ToolBuilder() {
  const [boxes, setBoxes] = useState(['', '', '']);
  const [output, setOutput] = useState('');

  const addBox = () => setBoxes([...boxes, '']);
  const removeBox = () => setBoxes(boxes.slice(0, -1));

  const combine = async () => {
    setOutput('Combining...');
    // Calls YOUR FastAPI backend → uses SDK wrapper → Claude subscription
    const res = await fetch('/api/tools/combine-rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ blocks: boxes.filter(b => b.trim()) })
    });
    const data = await res.json();
    setOutput(data.result);
  };

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Rule Combiner</h1>

      {boxes.map((box, i) => (
        <div key={i} className="mb-4">
          <label className="text-sm text-gray-400">Block {i + 1}</label>
          <textarea
            className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white"
            rows={4}
            value={box}
            onChange={e => {
              const newBoxes = [...boxes];
              newBoxes[i] = e.target.value;
              setBoxes(newBoxes);
            }}
          />
        </div>
      ))}

      <div className="flex gap-3 mb-6">
        <button onClick={addBox} className="px-4 py-2 bg-gray-800 rounded-lg">
          + Add Block
        </button>
        <button onClick={removeBox} className="px-4 py-2 bg-gray-800 rounded-lg">
          - Remove
        </button>
        <button onClick={combine} className="px-4 py-2 bg-purple-600 rounded-lg font-semibold">
          Combine All
        </button>
      </div>

      <div className="bg-gray-950 border border-gray-800 rounded-lg p-4 font-mono text-sm whitespace-pre-wrap">
        {output || 'Combined output appears here...'}
      </div>
    </div>
  );
}
```

**Pros:** Native feel. Uses your SDK wrapper. No separate API key. Full control.
**Cons:** Slightly more work (but AutoForge can build it for you).

---

## THE TOOL FACTORY PIPELINE

Here's what you can now do in under 10 minutes:

```
STEP 1: Decide what the tool does (2 min)
  "I want a tool that takes 3 inputs and chains them through 2 AI prompts"

STEP 2: Describe the boxes (1 min)
  "Input 1: Business description (textarea)
   Input 2: Target audience (textarea)
   Input 3: Tone (dropdown: professional/casual/fun)
   Chain 1: Generate taglines from inputs → output
   Chain 2: Take taglines + refine with tone → final output"

STEP 3: Screenshot a site you like the look of (30 sec)
  Screenshot stripe.com or linear.app or whatever

STEP 4: Feed screenshot to Style Set (1 min)
  → Get theme JSON

STEP 5: Apply theme to the web app template (1 min)
  → Paste CSS variables into the template

STEP 6: Deploy (2 min)
  → Apps Script: Deploy → New Deployment → Web App → Done. URL ready.
  → AutoForge: Drop the component in, it's live.

STEP 7: Attach domain (2 min)
  → Point your domain to the URL (iframe or redirect)

TOTAL: Under 10 minutes. You have a themed, AI-powered tool on a live URL.
```

---

## WHAT THIS REPLACES

| Old Way | Time | Cost | Result |
|---------|------|------|--------|
| Bolt / Lovable / Cursor | 4-8 hours | $20-50/mo | App that looks AI-generated |
| Hire a designer | Days-weeks | $500-5000 | Nice but slow |
| WordPress plugin + theme | 2-4 hours | $50-200 | Clunky, bloated |
| Build from scratch | Days | Free | Looks like 2001 |

| New Way | Time | Cost | Result |
|---------|------|------|--------|
| Sheet + Style Set + Apps Script | 5-10 min | Free | Looks like any site you screenshot |

---

## HACKATHON ANGLE (Google Hackathon)

**The pitch (if you decide to enter):**

"We turned Google Sheets into a no-code AI app builder. Take a screenshot of any
website. Our tool extracts the design. Apply it to a Google Sheet deployed as a
web app. Add AI-powered prompt chains with a visual editor. Result: production-quality
AI tools in minutes, hosted free on Google infrastructure. No frameworks. No servers.
No design skills needed. Just Sheets + Apps Script + a screenshot."

**Why Google would love it:**
- Uses Google Sheets in a way nobody has thought of
- Uses Apps Script (their underrated platform)
- Free hosting on their infrastructure
- Promotes their ecosystem
- Creative, unexpected, practical

**What you'd demo:**
1. Screenshot stripe.com
2. Feed to Style Set → get theme
3. Open the Sheet template
4. Apply theme (paste CSS variables)
5. Deploy as web app
6. Show it running — looks like Stripe but does your custom AI workflow
7. Click [+] to add more chain steps live
8. Mind = blown

**Risk of sharing:** Other devs see the technique and copy it.
**Mitigation:** The Style Set tool is the moat — anyone can make a Sheet look nice manually, but extracting a design from a screenshot and auto-applying it? That's YOUR tool.

---

## THE MOAT

Anyone can learn the Google Sheet trick. The moat is:

1. **Style Set** — Screenshot → theme. Nobody else has this as a product.
2. **Your templates** — The pre-built prompt chains, coding rules, PRD formats.
3. **The combo** — Style Set + Sheets + prompt chains as one seamless workflow.
4. **Your knowledge** — 15-year-vet mentor's techniques baked into the templates.

The Sheet trick is the vehicle. Your content is the engine.
