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


---

## REFERENCE: correction-detection-patterns

# Correction Detection Patterns

Linguistic markers for detecting explicit self-corrections in user input. Used by Stage 1, Step 4.

---

## High-Confidence Markers

These almost always indicate the user is correcting a previous statement:

| Marker | Example |
|--------|---------|
| `"actually"` | "I want Google login. Actually, also GitHub login." |
| `"wait"` / `"oh wait"` | "Oh wait, not just email — also SMS." |
| `"no,"` / `"no —"` | "No, not a chat app. More like a task board." |
| `"I mean"` | "I want it in Python. I mean TypeScript." |
| `"scratch that"` | "Add a calendar view. Scratch that, just a list view." |
| `"instead"` | "Instead of Google login, use magic links." |
| `"not X, Y"` / `"not just X"` | "Not just admin users — all users can create projects." |
| `"let me change that"` | "Let me change that — make it a SPA, not multi-page." |
| `"correction:"` / `"edit:"` | Explicit meta-correction labels in pasted notes. |

---

## Medium-Confidence Markers

These may indicate corrections but could also be additive statements. Look for surrounding context:

| Marker | Example | Additive or Corrective? |
|--------|---------|-------------------------|
| `"also"` | "Also add GitHub login" | Additive if new info; corrective if contradicts prior |
| `"I forgot"` / `"oh and"` | "Oh and I forgot — there should be a dashboard" | Usually additive, but record if it contradicts something |
| `"but"` | "I want it simple but also feature-rich" | Tension/contradiction — record both sides |
| `"well,"` | "Well, maybe not three tiers. Just two." | Often a softened correction |
| `"on second thought"` | "On second thought, skip the mobile version" | Almost always a correction |

---

## Contradiction Without Markers

Sometimes the user says X, then later says Y without explicit correction language:

- "I want it to be free" ... (later) ... "Users pay $10/month"
- "No login required" ... (later) ... "Users sign in with Google"

**Rule:** Only record in `explicit_corrections` if the user uses a correction marker. Implicit contradictions (no marker) are preserved in `raw_input` but NOT tagged in `explicit_corrections`. Implicit contradiction resolution is Stage 3's job.

---

## Recording Format

For each detected correction:

```json
{
  "original": "exact phrase or paraphrase of what they first said",
  "correction": "exact phrase or paraphrase of the correction",
  "context": "optional — why they corrected (if they said)"
}
```

**Rules:**
- Keep `original` and `correction` concise — extract the relevant clause, not the full paragraph
- `context` is optional — only include if the user explained why they changed their mind
- Both the original statement AND the correction remain verbatim in `raw_input`
- When in doubt about whether something is a correction, do NOT record it — err on the side of fewer entries


---

## REFERENCE: example-captures

# Example Captures

Realistic Stage 1 captures at different detail levels. Each shows raw user input and the resulting `stage_1` output.

---

## Example 1: Minimal Input (2-3 sentences)

**User says:**
> I want a recipe app where people can save recipes and search by ingredient.

**stage_1 output:**

```json
{
  "raw_input": "I want a recipe app where people can save recipes and search by ingredient.",
  "input_format": "typed",
  "captured_at": "2026-04-03T11:00:00Z",
  "word_count": 14,
  "char_count": 71,
  "explicit_corrections": []
}
```

**Confidence: 52/100** — Fails minimum viability (14 words < 20). Prompt user for more detail. If user declines, trigger escape hatch.

**After prompting, user adds:**
> It should have categories like breakfast, lunch, dinner. Users can rate recipes and leave comments. Maybe a meal planner for the week.

**Updated stage_1:**

```json
{
  "raw_input": "I want a recipe app where people can save recipes and search by ingredient.\n\nIt should have categories like breakfast, lunch, dinner. Users can rate recipes and leave comments. Maybe a meal planner for the week.",
  "input_format": "typed",
  "captured_at": "2026-04-03T11:01:30Z",
  "word_count": 41,
  "char_count": 213,
  "explicit_corrections": []
}
```

**Confidence: 74/100** — Flag (low specificity and completeness). Proceeds with warning.

---

## Example 2: Average Input (5-8 sentences)

**User says:**
> I'm thinking of a fitness tracking app for personal trainers. They can create workout plans for their clients, track progress over time, and see charts of improvement. Clients get a separate view where they log their workouts and see what's assigned. I want Google login for both trainers and clients. It should work on mobile since people use it at the gym. Something like Trainerize but less expensive and more customizable.

**stage_1 output:**

```json
{
  "raw_input": "I'm thinking of a fitness tracking app for personal trainers. They can create workout plans for their clients, track progress over time, and see charts of improvement. Clients get a separate view where they log their workouts and see what's assigned. I want Google login for both trainers and clients. It should work on mobile since people use it at the gym. Something like Trainerize but less expensive and more customizable.",
  "input_format": "typed",
  "captured_at": "2026-04-03T11:05:00Z",
  "word_count": 82,
  "char_count": 460,
  "explicit_corrections": []
}
```

**Confidence: 88/100** — Flag (handoff_readiness slightly low — trainer/client permissions not fully described). Proceeds with warning.

---

## Example 3: Verbose Input (40+ sentences)

**User says:**
> OK so I've been thinking about this for a while. I want to build a freelancer management platform. Think of it like a mix between Upwork and Notion. Freelancers sign up, create a profile with their skills, hourly rate, portfolio links. Companies post gigs — not full job listings, more like project briefs. So a company says "I need a landing page designed" and freelancers can bid on it. But here's the thing — I don't want it to be a race to the bottom on pricing like Fiverr. I want quality matching. So maybe there's a rating system based on completed work, and the platform suggests matches based on skills and past work quality. Companies can also create teams of freelancers they work with regularly, like a favorites list. Payments should be handled through the platform — escrow style. Company pays upfront, money is held, released when work is approved. Disputes go to mediation. I want Stripe for payments. Users sign up with email. Actually wait, also Google and LinkedIn since it's a professional platform. The dashboard for companies shows active projects, pending invoices, team performance. Freelancers see their pipeline, earnings chart, upcoming deadlines. There should be a messaging system between freelancers and companies, with file sharing. Not real-time chat necessarily — more like threaded conversations per project. Notifications for new messages, project updates, payment received. I want it to feel professional, not startup-y. Clean design, maybe a blue and white color scheme. Oh and I forgot — there should be a public profile page for freelancers that they can share as a portfolio link. And companies should have a public page too showing their posted gigs. SEO matters for these pages.

**stage_1 output:**

```json
{
  "raw_input": "OK so I've been thinking about this for a while. I want to build a freelancer management platform. Think of it like a mix between Upwork and Notion. Freelancers sign up, create a profile with their skills, hourly rate, portfolio links. Companies post gigs — not full job listings, more like project briefs. So a company says \"I need a landing page designed\" and freelancers can bid on it. But here's the thing — I don't want it to be a race to the bottom on pricing like Fiverr. I want quality matching. So maybe there's a rating system based on completed work, and the platform suggests matches based on skills and past work quality. Companies can also create teams of freelancers they work with regularly, like a favorites list. Payments should be handled through the platform — escrow style. Company pays upfront, money is held, released when work is approved. Disputes go to mediation. I want Stripe for payments. Users sign up with email. Actually wait, also Google and LinkedIn since it's a professional platform. The dashboard for companies shows active projects, pending invoices, team performance. Freelancers see their pipeline, earnings chart, upcoming deadlines. There should be a messaging system between freelancers and companies, with file sharing. Not real-time chat necessarily — more like threaded conversations per project. Notifications for new messages, project updates, payment received. I want it to feel professional, not startup-y. Clean design, maybe a blue and white color scheme. Oh and I forgot — there should be a public profile page for freelancers that they can share as a portfolio link. And companies should have a public page too showing their posted gigs. SEO matters for these pages.",
  "input_format": "typed",
  "captured_at": "2026-04-03T11:10:00Z",
  "word_count": 271,
  "char_count": 1534,
  "explicit_corrections": [
    {
      "original": "email login only",
      "correction": "email AND Google AND LinkedIn login",
      "context": "User initially said email, then added Google and LinkedIn since it's a professional platform"
    }
  ]
}
```

**Confidence: 96/100** — Pass. Rich detail, multiple features, target users, comparisons, technical preferences, and contextual detail.

---

## Example 4: Voice Transcript (with filler words and self-corrections)

**User says (transcribed from voice):**
> um ok so like I want to make this app right where uh people can like track their habits you know like drinking water exercising reading whatever um and it shows you like streaks so if you do it every day your streak goes up and if you miss a day it resets well actually maybe not resets completely like maybe it just you know shows a gap and you can still see your overall progress um I think it should be really simple like not a lot of buttons just open it check off what you did today see your streaks maybe some stats like how many times you exercised this month um I don't know about login maybe just use the phone no wait it should sync between devices so yeah login with Apple or Google I guess um and like maybe there's a social thing where you can share your streaks with friends but that's not the main thing the main thing is just tracking your own habits simply

**stage_1 output:**

```json
{
  "raw_input": "um ok so like I want to make this app right where uh people can like track their habits you know like drinking water exercising reading whatever um and it shows you like streaks so if you do it every day your streak goes up and if you miss a day it resets well actually maybe not resets completely like maybe it just you know shows a gap and you can still see your overall progress um I think it should be really simple like not a lot of buttons just open it check off what you did today see your streaks maybe some stats like how many times you exercised this month um I don't know about login maybe just use the phone no wait it should sync between devices so yeah login with Apple or Google I guess um and like maybe there's a social thing where you can share your streaks with friends but that's not the main thing the main thing is just tracking your own habits simply",
  "input_format": "voice_transcript",
  "captured_at": "2026-04-03T11:15:00Z",
  "word_count": 170,
  "char_count": 837,
  "explicit_corrections": [
    {
      "original": "streak resets when you miss a day",
      "correction": "streak shows a gap but overall progress still visible",
      "context": "User reconsidered full reset as too punishing"
    },
    {
      "original": "no login, just use the phone",
      "correction": "login with Apple or Google for device sync",
      "context": "User realized syncing between devices requires login"
    }
  ]
}
```

**Confidence: 90/100** — Pass. Filler words preserved, corrections detected, app concept clear despite informal language.


---

## REFERENCE: intake-prompt-templates

# Intake Prompt Templates

Platform-tailored intake prompts for Stage 1: Idea Capture. Each template is a gentle, low-friction invitation — NOT a questionnaire.

---

## Web App (framework: Next.js, React, Vue, Svelte, etc.)

> Tell me about the app you want to build. Describe it however makes sense to you — a few sentences, a full brain dump, bullet points, whatever works.
>
> Think about things like: What pages or screens would it have? What happens when someone visits? What can users do? Who is it for?
>
> There are no wrong answers. Contradictions are fine — just keep talking. The more detail you give me now, the fewer questions I'll need to ask later.

---

## Mobile App (framework: Flutter, React Native, SwiftUI, Kotlin)

> Tell me about the app you want to build. Describe it however makes sense to you — a few sentences, a full rant, scattered notes, whatever.
>
> Think about things like: What screens would someone swipe through? What happens when they tap something? Are there gestures like drag, swipe, or pull-to-refresh? Who would download this?
>
> No wrong answers. Contradictions are welcome — both versions get captured. The more you describe, the less I need to ask later.

---

## Dual Platform (web + mobile)

> Tell me about the app you want to build. Describe it however makes sense to you — there's no template or form to fill out.
>
> Since this is for both web and mobile: think about what happens on a big screen vs. a phone. Are the features the same on both, or does one get a simpler version? What do people do on desktop vs. on the go?
>
> Just talk. Tangents, repetitions, contradictions — all welcome. More detail now means fewer questions later.

---

## No Boilerplate / Raw Checklist / Unknown Platform

> Tell me about the app you want to build. Just describe it in your own words — a few sentences, a long rant, bullet points, voice notes, whatever comes naturally.
>
> What does it do? Who is it for? What are the main things a user can do with it? Are there any apps out there that are similar to what you're imagining?
>
> There's no form to fill out. No wrong answers. Contradictions are fine — just keep going. The more you tell me, the less I'll need to ask later.

---

## Usage Notes

- Read `context_packet.stage_0.tech_stack.framework` to select the appropriate template
- If framework is unrecognized, use the "No Boilerplate" template
- These are starting prompts only — if the user starts talking, do NOT interrupt with more prompting
- Never convert these into a numbered questionnaire or form
- The contextual cues (pages/screens/gestures) are suggestions, not requirements
