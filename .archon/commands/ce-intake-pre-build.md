---
description: "Compound Engineering — Pre-Build Intake: Capture PRD or new app idea from scratch"
argument-hint: <paste your PRD, describe your app idea, or say "interactive" to be guided through questions>
---

# Compound Engineering: Pre-Build Intake

**Artifacts Directory**: $ARTIFACTS_DIR
**User Input**: $ARGUMENTS

## Context Loading

Before executing, check if `$ARTIFACTS_DIR/context-packet/` exists. If prior outputs exist, read them. For Pre-Build mode, this is typically the first stage so the directory may be empty.

---

## Mode Declaration

You are operating in **Pre-Build Mode**. This means: no existing codebase, no prior code to analyze. The user either has a PRD, an app idea, or a rough concept they want built from scratch.

State this clearly to the user:
> "Running in Pre-Build mode. I'll capture your app idea or PRD, ask a few clarifying questions, then package everything for the planning stage."

---

## Process

### Step 1: Capture the Idea

Check `$ARGUMENTS` first. If the user already provided their idea or PRD there, use it directly. If `$ARGUMENTS` is empty or just contains a trigger phrase, prompt:

> "Describe your app idea. You can paste a full PRD, a rough description, bullet points, or a brain dump. The more detail you provide, the fewer questions I'll need to ask."

Capture EVERYTHING the user provides verbatim. Do not summarize, reorganize, or filter.

### Step 2: Classify Input Type

Determine what was provided:
- **Full PRD**: Has sections like "Requirements", "User Stories", "Architecture", etc.
- **Rough Description**: Paragraph-style description of what the app does
- **Bullet Points**: Feature list or scattered notes
- **Minimal**: Under 3 sentences with vague intent

Record the classification as `input_type` in the context packet.

### Step 3: Ask Clarifying Questions

Ask 3-5 targeted questions based on gaps in the input. Select from these categories:

**Tech Stack** (ask if not specified):
- "Do you have a preferred tech stack? (e.g., React + Node, Python + FastAPI, etc.) If not, I'll recommend one based on the requirements."

**Scale Expectations** (ask if not specified):
- "What scale are you targeting? Personal project, small team tool, or public-facing product with many users?"

**Must-Have vs Nice-to-Have** (always ask):
- "Which features are absolute must-haves for a first version, and which are nice-to-haves you'd add later?"

**Reference Apps** (ask if not mentioned):
- "Are there existing apps that are similar to what you're building? What do you like or dislike about them?"

**Deployment Target** (ask if not specified):
- "Where will this run? Local only, cloud-hosted, self-hosted, or undecided?"

Do NOT ask more than 5 questions. Do NOT ask about things already clearly stated in the input.

### Step 4: Summarize Confirmed Requirements

After receiving answers, produce a clear summary:

```
## Confirmed Requirements

**App Name/Working Title**: [from user or "Untitled"]
**Description**: [2-3 sentence summary of what the app does]
**Tech Stack**: [confirmed or recommended stack]
**Target Scale**: [personal / team / public]

### Must-Have Features
1. [feature]
2. [feature]
...

### Nice-to-Have Features
1. [feature]
2. [feature]
...

### Reference Apps
- [app]: [what user likes/dislikes about it]

### Constraints or Preferences
- [any mentioned constraints: budget, timeline, platform, etc.]
```

Present this to the user for confirmation. If interactive, wait for approval. If autonomous, proceed.

### Step 5: Write Context Packet

Create `$ARTIFACTS_DIR/context-packet/context-packet.json` with this structure:

```json
{
  "mode": "pre-build",
  "input_type": "full_prd | rough_description | bullet_points | minimal",
  "app_description": "2-3 sentence summary",
  "tech_stack": {
    "frontend": "framework or null",
    "backend": "framework or null",
    "database": "type or null",
    "auth": "method or null",
    "hosting": "target or null"
  },
  "requirements": {
    "must_have": ["feature 1", "feature 2"],
    "nice_to_have": ["feature 1", "feature 2"]
  },
  "reference_apps": [
    {"name": "app name", "liked": "what", "disliked": "what"}
  ],
  "target_scale": "personal | team | public",
  "constraints": ["any constraints mentioned"],
  "raw_input": "complete verbatim user input",
  "captured_at": "ISO 8601 timestamp"
}
```

Ensure the directory exists before writing. Create `$ARTIFACTS_DIR/context-packet/` if it does not exist.

### Step 6: Validate and Signal

Validate the context packet:
1. `app_description` is non-empty and describes an actual application
2. `requirements.must_have` has at least 1 item
3. `tech_stack` has at least one non-null field
4. `raw_input` is preserved verbatim

If validation passes, emit:
<promise>INTAKE_COMPLETE</promise>

If validation fails (user provided no actionable information after prompting), report what's missing and ask once more. If still insufficient, write what you have and emit the promise anyway with a note in `constraints` about gaps.
