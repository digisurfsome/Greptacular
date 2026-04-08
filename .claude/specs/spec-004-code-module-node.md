# Spec 004 — Code Module Node

## What This Is
A custom Activepieces piece (node) built via the CLI that lets you drop in custom-coded logic anywhere in a pipeline. It has a guided 7-step form that captures exactly what the code needs to do, a Monaco code editor (VS Code quality), and a "Build It" button that calls Claude scoped only to that one node's code. Everything else in the pipeline is untouched.

## Why It Matters
This is what makes the system superior to Bolt/Lovable for AI automation. They build entire apps — one bug can break everything. The Code Module node builds one isolated function. Wrong? Throw it away. Rebuild. The pipeline keeps running. The scope of failure is one node.

The 7-step form is the other key piece: it runs every custom code request through a deterministic mechanism-discovery process before Claude writes a single line. This produces code that is architecturally correct before it's written — not debugged into correctness after.

---

## Building the Piece (CLI Commands)

```bash
# One-time setup
npm install -g @activepieces/cli
ap init   # enter your AP API key when prompted

# Create the piece
ap create-piece --name code-module --type custom

# This creates:
# packages/pieces/custom/code-module/
# ├── src/
# │   ├── index.ts
# │   └── lib/actions/
# ├── package.json
# └── tsconfig.json

# After writing the code:
ap publish   # deploys to your AP instance
```

---

## The Piece Definition (`src/index.ts`)

```typescript
import { createPiece } from '@activepieces/pieces-framework'
import { buildWithAI } from './lib/actions/build-with-ai'
import { runSavedModule } from './lib/actions/run-saved-module'

export const codeModule = createPiece({
  displayName: 'Code Module',
  description: 'Custom AI-built logic node. Isolated. Replaceable.',
  logoUrl: 'https://your-domain.com/code-module-icon.svg',
  auth: undefined,   // no auth needed at piece level
  actions: [buildWithAI, runSavedModule],
  triggers: []
})
```

---

## The 7-Step Form (The Core of the Node)

Each of the 7 questions maps to a `Property` in the piece definition. These questions mirror the deterministic mechanism-discovery system. Together they give Claude everything it needs to write correct, bounded, testable code.

```typescript
// src/lib/actions/build-with-ai.ts
import { createAction, Property } from '@activepieces/pieces-framework'

export const buildWithAI = createAction({
  name: 'build_with_ai',
  displayName: 'Build With AI',
  description: 'Describe what this node should do — AI writes the code.',
  props: {

    // STEP 1: What does this node do? (plain English, no jargon)
    purpose: Property.LongText({
      displayName: '1. What does this node do?',
      description: 'Describe in plain English. Example: "Takes a YouTube video URL and returns a cleaned transcript."',
      required: true
    }),

    // STEP 2: What comes in?
    input_description: Property.LongText({
      displayName: '2. What comes IN to this node?',
      description: 'Describe the data this node receives. Include shape/type. Example: "A JSON object with fields: url (string), title (string)"',
      required: true
    }),

    // STEP 3: What goes out?
    output_description: Property.LongText({
      displayName: '3. What goes OUT of this node?',
      description: 'Describe the data this node returns. Example: "A string containing the cleaned transcript text"',
      required: true
    }),

    // STEP 4: What are the walls? (what it will NOT do)
    constraints: Property.LongText({
      displayName: '4. What are the WALLS? (what this node should NOT do)',
      description: 'Hard limits. Example: "Do not call any external APIs. Do not modify the input object. Only process text under 10,000 chars."',
      required: false
    }),

    // STEP 5: What can cause failure? (the gates and guards)
    failure_cases: Property.LongText({
      displayName: '5. What can go WRONG? (failure cases to handle)',
      description: 'Example: "Input might be null. URL might be invalid. Transcript might be empty. List how to handle each."',
      required: false
    }),

    // STEP 6: Does it need AI steps inside? If so, describe them.
    ai_steps: Property.LongText({
      displayName: '6. Any AI steps INSIDE this node?',
      description: 'If this node calls an LLM, describe: what prompt, what model, what structured output. Leave blank if no AI needed.',
      required: false
    }),

    // STEP 7: What does "passing" look like?
    success_definition: Property.LongText({
      displayName: '7. What does SUCCESS look like?',
      description: 'Give a concrete example. Input: [example input]. Expected output: [example output]. This becomes your test case.',
      required: true
    }),

    // The actual code field (Monaco editor)
    generated_code: Property.LongText({
      displayName: 'Generated Code (auto-filled by Build It)',
      description: 'Filled automatically. You can also edit directly.',
      required: false
    }),

    // Quality flag
    quality_status: Property.StaticDropdown({
      displayName: 'Quality Status',
      required: true,
      defaultValue: 'draft',
      options: {
        options: [
          { label: 'Draft (untested)', value: 'draft' },
          { label: 'Stable (all tests passing)', value: 'stable' },
          { label: 'Promoted (production-ready)', value: 'promoted' }
        ]
      }
    })

  },

  async run(context) {
    const { generated_code, input_description, output_description } = context.propsValue

    if (!generated_code) {
      throw new Error('No code generated yet. Fill in the 7 questions and click Build It.')
    }

    // Execute the generated code in a sandboxed context
    // The code receives: context.propsValue (all node settings) + the flow's step data
    const fn = new Function('input', 'context', generated_code)
    return fn(context.propsValue, context)
  }
})
```

---

## The "Build It" Button — How Claude Gets Called

The Build It button is a secondary action in the skin's co-pilot panel, not inside Activepieces itself. When clicked:

1. Collects the 7 form answers from the current node's config
2. Searches the mechanism library for matching patterns (Spec 005)
3. Calls Claude with a scoped prompt
4. Fills the `generated_code` field with the result
5. Applies the UPDATE_ACTION operation to save it to the flow

### The Scoped Prompt for Code Generation
```
You are writing a single TypeScript/JavaScript function for one Activepieces Code Module node.

SCOPE: You are writing ONLY the code for this one function. You cannot see or modify 
any other part of the pipeline. Your function receives `input` and `context` as arguments.

FROM THE 7-STEP FORM:
Purpose: {purpose}
Input: {input_description}
Output: {output_description}
Walls (must NOT do): {constraints}
Failure cases: {failure_cases}
AI steps inside: {ai_steps}
Success definition: {success_definition}

MECHANISM LIBRARY MATCHES FOUND:
{matching_mechanisms}   ← searched from /mechanisms/ before this prompt was sent

RULES:
- Return ONLY executable JavaScript code (no import statements, no class wrappers)
- The code must work as: const fn = new Function('input', 'context', code)
- Handle all failure cases explicitly
- Match the output shape described exactly
- If AI steps are needed, use: await context.claude.call(prompt, model)
- Use mechanism library code directly if it matches — don't rewrite it
- The final return value must match the output description exactly

Write the function body only. Start with the logic, not with comments.
```

---

## How the Node Fits in a Flow

```
[YouTube Trigger]
      ↓
[HTTP: Get Transcript]    ← pre-built AP node
      ↓
[Code Module Node]        ← YOUR custom node
  Purpose: "Clean transcript — remove filler words, fix spacing"
  Input: {transcript: string}
  Output: {cleaned: string, word_count: number}
      ↓
[Claude: Summarize]       ← pre-built AP node (Anthropic piece)
      ↓
[Slack: Send Message]     ← pre-built AP node
```

The Code Module node slots in between existing nodes. It has typed inputs and outputs. The upstream node passes data in. The downstream node receives data out. If the Code Module is wrong, replace it — the upstream and downstream nodes are unaffected.

---

## The Quality Lifecycle

```
User fills 7-step form
         ↓
Claude searches mechanism library
         ↓
Claude writes code
         ↓
Code fills generated_code field  →  status = "draft"
         ↓
Run test cases (auto-generated from Step 7)
    ↓            ↓
 PASS          FAIL
  ↓              ↓
status=        Throw away.
"stable"       Fill form again.
  ↓            Claude tries again.
Used in
production
  ↓
status=
"promoted"
Code saved to
mechanism library
```

---

## Success Criteria

- [ ] `ap create-piece --name code-module` scaffolds the TypeScript structure
- [ ] `ap publish` deploys the piece and it appears in the AP builder node picker
- [ ] A "Code Module" node can be dropped into any flow position
- [ ] All 7 form questions appear as fields in the node settings panel
- [ ] "Build It" button (via skin co-pilot panel) fills `generated_code` from Claude
- [ ] The node executes the generated code with flow input data
- [ ] Quality status can be changed to `stable` after tests pass
- [ ] A wrong module can be deleted and recreated without affecting any other step
