---
name: stage-1-idea-capture
description: Capture raw app idea brain dump with zero filtering. Outputs raw_input, word count, format, corrections.
---

## Purpose

Capture the user's raw, unstructured app idea exactly as given — preserving contradictions, tangents, filler words, and repetitions — so Stage 2 (Gap Analysis) receives complete, unfiltered raw material to work with.

## When to Use

Activate when: the user provides a raw app idea, brain dump, rant, voice transcript, scattered notes, or stream-of-consciousness description AND `context_packet.stage_0.platform_profile` exists (Stage 0 is complete). Trigger phrases: "describe your app", "here's my idea", "I want to build", "brain dump", "idea capture", "raw idea".

Do NOT activate for: gap analysis questions (Stage 2), structuring/organizing ideas (Stage 3), mechanism extraction (Stage 4), or any request to "clean up" or "organize" raw input.

## Input Format

```json
{
  "stage_0": {
    "platform_profile": {
      "boilerplate_id": "string",
      "boilerplate_name": "string",
      "description": "string"
    },
    "tech_stack": {
      "framework": "string",
      "database": "string",
      "auth_provider": "string",
      "hosting": "string"
    }
  },
  "metadata": {
    "pipeline_version": "string",
    "current_stage": 0,
    "status": "in_progress"
  }
}
```

The primary input is the **user's free-form idea description** — no structure required.

## Process

### Step 1: Present Intake Prompt

Read `context_packet.stage_0.platform_profile` and `stage_0.tech_stack.framework` to lightly tailor the prompt. See `references/intake-prompt-templates.md` for platform-specific variations.

Present a low-friction prompt that:
- Invites the user to describe their app idea however they want
- States explicitly: no wrong answers, no forms, no required format
- Encourages verbosity: "The more detail you give now, the fewer questions later"
- Gives 1-2 gentle contextual cues based on platform (e.g., "pages and flows" for web, "screens and gestures" for mobile)
- Welcomes contradictions, tangents, and repetitions

**Do NOT** present a form, template, questionnaire, or structured input. The user talks however they want.

### Step 2: Capture Everything Verbatim

Accept whatever the user provides and store the complete text as `raw_input`.

**Capture rules — all mandatory:**
- Do NOT summarize, paraphrase, or condense
- Do NOT reorganize into sections or categories
- Do NOT correct grammar, spelling, or formatting
- Do NOT remove filler words ("um", "like", "you know")
- Do NOT resolve contradictions — both versions stay in raw_input
- DO preserve exact words, sentence structure, and flow
- DO preserve formatting artifacts from pasted content

If the user provides input across multiple messages, concatenate all messages in order with a blank line between each, preserving everything.

### Step 3: Detect Input Format

Classify `input_format` using textual signals:

| Format | Signals |
|--------|---------|
| `"voice_transcript"` | Filler words, run-on sentences, self-corrections mid-sentence, informal speech, lack of punctuation |
| `"typed"` | Complete sentences, proper punctuation, paragraph breaks, no filler words |
| `"pasted_notes"` | Bullet points, numbered lists, formatting artifacts (markdown, HTML), mixed formatting |
| `"mixed"` | Combination of above patterns in the same input |

Default to `"typed"` if uncertain.

### Step 4: Detect Explicit Corrections

Scan `raw_input` for correction markers. See `references/correction-detection-patterns.md` for the full pattern list.

Common markers: "actually", "wait", "no", "I mean", "scratch that", "instead", "not X, Y", "oh wait", "I forgot", "let me change that".

For each detected correction, record:
- `original`: What the user first said
- `correction`: What they changed it to
- `context`: (optional) Why they corrected

**Both the original AND correction remain in `raw_input`.** The corrections array is metadata ABOUT the input, not a replacement. Resolution happens in Stage 3.

If no corrections detected, set `explicit_corrections` to `[]`.

### Step 5: Count and Timestamp

- `word_count`: Split `raw_input` on whitespace, count tokens
- `char_count`: Total character length of `raw_input`
- `captured_at`: Current ISO 8601 timestamp (e.g., `"2026-04-03T10:22:40Z"`)

### Step 6: Validate Minimum Viability

If `word_count >= 20`: proceed to Step 7.

If `word_count < 20`: prompt the user for more detail:
> "I have your idea captured, but it's quite brief. The more you tell me now, the fewer questions I'll need to ask next. Could you add more about what the app does, who it's for, or the main features you envision?"

If user adds more: re-capture (append to raw_input), re-count. If user declines: proceed with what you have — expect lower confidence score.

### Step 7: Score Confidence and Write Output

Run the confidence scoring (see Confidence Scoring section below). Then:

- **Score >= 90**: Write output to context packet. Proceed to Stage 2.
- **Score 70-89**: Write output with warning. Add low-scoring dimensions to metadata notes.
- **Score < 70**: Prompt user for more detail once. If still < 70 after retry, trigger escape hatch.

## Output Format

Written to `context_packet.stage_1`:

```json
{
  "raw_input": "string — complete unedited user brain dump",
  "input_format": "typed | voice_transcript | pasted_notes | mixed",
  "captured_at": "ISO 8601 timestamp string",
  "word_count": 168,
  "char_count": 892,
  "explicit_corrections": [
    {
      "original": "string — what user originally said",
      "correction": "string — what they changed it to",
      "context": "string (optional) — why they corrected"
    }
  ]
}
```

Written to `context_packet.metadata`:

```json
{
  "current_stage": 1,
  "updated_at": "ISO 8601 timestamp",
  "confidence_scores": {
    "1": {
      "score": 92,
      "dimensions": {
        "completeness": 18,
        "accuracy": 20,
        "consistency": 18,
        "specificity": 18,
        "handoff_readiness": 18
      },
      "gate_result": "pass | flag | fail"
    }
  },
  "stage_timestamps": {
    "1": "ISO 8601 timestamp"
  }
}
```

**Validation before writing:**
1. All required fields populated: `raw_input`, `input_format`, `captured_at`, `word_count`, `char_count`
2. `raw_input` is non-empty
3. `input_format` is one of: `"typed"`, `"voice_transcript"`, `"pasted_notes"`, `"mixed"`
4. `captured_at` is valid ISO 8601
5. `word_count` matches actual word count within 5% tolerance
6. Confidence score computed and gate_result set

**Output contains ONLY the structured JSON data. No conversational preamble, no "Here is what I captured:", no prose.**

## Edge Cases

### Missing or Insufficient Input

- **Under 20 words**: Prompt for more detail. If user declines after one prompt, proceed but flag `gate_result: "flag"` if score is 70-89, or trigger escape hatch if < 70.
- **Empty input**: Trigger escape hatch immediately.
- **Non-app input** (e.g., "hello", "test", random characters): Trigger escape hatch. The input contains no identifiable app concept.

### Pre-Structured Input

User pastes markdown with headers, numbered lists, or organized sections. **Capture it exactly as-is.** Set `input_format` to `"pasted_notes"`. Do NOT strip formatting. Downstream stages handle structure — Stage 1 preserves everything.

### Scope Overflow

User asks Stage 1 to organize, analyze, or improve their idea. **Decline politely.** Say: "I'll capture everything you've said as-is. The next stage will ask follow-up questions and organize things. For now, just keep describing your idea." Capture whatever they said, including the request to organize.

### Missing Stage 0 Data

If `context_packet.stage_0.platform_profile` is missing or malformed: use the generic intake prompt (no platform-specific cues). Log a warning but do NOT block capture. Stage 0 data is used for tailoring, not gating.

### Extremely Long Input

If `raw_input` exceeds 10,000 words: capture all of it. No truncation. Set `input_format` based on content signals as normal. Note: extremely long input almost guarantees a high confidence score.

## Confidence Scoring

Score each dimension 0-20 after producing output:

**1. Completeness (0-20):**
- 0-5: raw_input empty or under 10 words; required fields missing
- 6-10: 10-19 words; all fields present but minimal
- 11-15: 20-100 words; all fields populated; at least one app concept identifiable
- 16-20: 100+ words with rich detail; multiple concepts, context, and user intent

**2. Accuracy (0-20):**
- 0-5: raw_input was edited, summarized, or rewritten
- 6-10: Mostly faithful but some paraphrasing detected
- 11-15: Preserves user's language faithfully; minor formatting differences OK
- 16-20: Verbatim capture including filler phrases, self-corrections, informal language

**3. Consistency (0-20):**
- 0-5: raw_input contradicts input_format (e.g., format says voice but text is structured markdown)
- 6-10: word_count off by >10%
- 11-15: Metadata matches content; word_count accurate within 5%
- 16-20: All metadata precisely matches; zero discrepancies

**4. Specificity (0-20):**
- 0-5: So vague no app concept identifiable ("I want to make something cool")
- 6-10: App concept present but no features, users, or context
- 11-15: App concept + 2-3 feature ideas or user descriptions
- 16-20: App concept + multiple features + target users + contextual details

**5. Handoff Readiness (0-20):**
- 0-5: Stage 2 cannot determine app type
- 6-10: Stage 2 can identify rough app type but needs fundamental questions
- 11-15: Stage 2 can identify app type and start gap analysis; gaps are in specifics, not core
- 16-20: Stage 2 can identify app type, match archetype, generate targeted gap questions

**Total = sum of all 5 (/100)**

| Score | Gate Result | Action |
|-------|-------------|--------|
| >= 90 | `"pass"` | Proceed to Stage 2 automatically |
| 70-89 | `"flag"` | Proceed with warning; note low dimensions |
| < 70 | `"fail"` | Trigger escape hatch |

## Escape Hatch

**Trigger when:**
- User provides fewer than 20 words and declines to add more
- raw_input contains no identifiable app concept
- Confidence score < 70 after one retry
- Stage 0 platform_profile is missing AND user provides no usable input

**Save:**
- Current context_packet with partial `stage_1` output
- Stage number (1) and step where halt occurred
- What was attempted and what failed

**Signal:**
```json
{
  "status": "needs_human",
  "stage": 1,
  "problem": "specific problem description",
  "suggested_questions": [
    "Could you describe what your app does in a few more sentences?",
    "Who is this app for? What problem does it solve?",
    "What are the main features you envision?"
  ]
}
```

Set `metadata.status = "needs_human"` and append to `metadata.escape_hatches[]`:
```json
{
  "stage": 1,
  "timestamp": "ISO 8601",
  "status": "NEEDS_HUMAN",
  "progress_summary": "what was captured so far",
  "problem": "specific reason",
  "attempted": ["list of what was tried"],
  "partial_output": {},
  "suggested_actions": ["action 1", "action 2"],
  "resume_from": "step_name",
  "confidence_at_failure": 45,
  "scope_creep_detected": false
}
```

## Example

**User input:**

> I want to build a task manager app. Like Todoist but simpler. Users can create projects and add tasks to them. Tasks have due dates, priorities (high/medium/low), and you can assign them to other people on your team. I want a kanban board view where you drag tasks between columns like To Do, In Progress, and Done. Also a regular list view sorted by due date. Users need to sign up with email or Google. Oh wait, not just Google — also GitHub login since this is for developer teams. There should be notifications when someone assigns you a task or when a due date is coming up. Maybe email and in-app notifications. I want it to look clean and modern, not cluttered. Dark mode would be nice. Teams should be able to create workspaces and invite members. Oh and I forgot — there should be a simple dashboard showing how many tasks are done vs pending, maybe a chart.

**Output written to context_packet.stage_1:**

```json
{
  "raw_input": "I want to build a task manager app. Like Todoist but simpler. Users can create projects and add tasks to them. Tasks have due dates, priorities (high/medium/low), and you can assign them to other people on your team. I want a kanban board view where you drag tasks between columns like To Do, In Progress, and Done. Also a regular list view sorted by due date. Users need to sign up with email or Google. Oh wait, not just Google — also GitHub login since this is for developer teams. There should be notifications when someone assigns you a task or when a due date is coming up. Maybe email and in-app notifications. I want it to look clean and modern, not cluttered. Dark mode would be nice. Teams should be able to create workspaces and invite members. Oh and I forgot — there should be a simple dashboard showing how many tasks are done vs pending, maybe a chart.",
  "input_format": "typed",
  "captured_at": "2026-04-03T10:22:40Z",
  "word_count": 168,
  "char_count": 892,
  "explicit_corrections": [
    {
      "original": "Google login only",
      "correction": "Google AND GitHub login",
      "context": "User initially said Google, then added GitHub for developer teams"
    }
  ]
}
```

**Confidence: 92/100** (completeness: 18, accuracy: 20, consistency: 18, specificity: 18, handoff_readiness: 18) — `gate_result: "pass"`. Proceeds to Stage 2.
