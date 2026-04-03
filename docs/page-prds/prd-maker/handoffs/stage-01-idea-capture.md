# Build Stage 1 Skill: Idea Capture

> **Type:** Self-contained handoff prompt for a fresh Claude Code agent
> **Output:** `docs/page-prds/prd-maker/skills/stage-01-idea-capture/SKILL.md`

---

## System Overview: The 10-Stage PRD Maker Pipeline

You are building one skill for a 10-stage pipeline that transforms a non-coder's messy app description into a complete, buildable technical specification. Each stage is a separate Claude Code skill. The stages run in sequence, passing a JSON data object (the "context packet") from one to the next.

### The Pipeline at a Glance

| Stage | Name | Purpose | Key Output |
|-------|------|---------|------------|
| 0 | Technical Foundation | Establish platform context (framework, DB, auth, hosting) before any idea-specific work | Platform profile + agnostic checklist reference |
| 1 | **Idea Capture** | **Capture the user's raw brain dump with zero filtering or structure** | **Raw text, preserved contradictions, word count** |
| 2 | Gap Analysis | Match to archetype, identify missing mechanism categories (A-N), ask targeted questions | Complete mechanism map, archetype match, gap answers |
| 3 | Agent OS Structuring | Transform messy raw material into organized concept document | Product identity, problem statement, target users, feasibility |
| 4 | Mechanism Extraction | Break structured app into discrete moving parts tagged OBVIOUS or NEEDS_EVALUATION | Mechanism list with dependencies and evaluation tags |
| 5 | 7-Question Scaffolding | Classify every process step as WALL (deterministic) / DOOR (constrained AI) / ROOM (creative) | Per-mechanism W/D/R classification with verification methods |
| 6 | Layout + Mockups + Style | Define page layouts, wireframe patterns, and design system | Per-page component specs, style tokens, typography |
| 7 | Phase Sequencing | Split the spec into buildable phases within token budgets | Phase list with token estimates, file sandbox, build order |
| 8 | Protocol Injection | Configure verification system (pulse/seam/full checks) | Check configurations, violation thresholds, escalation rules |
| 9 | Verification Agent Setup | Configure separate checker agent with git diff rules | Checker config, two-strike rule, verification mode |
| 10 | Output Generator | Produce copy-paste-ready build files | Phase files, build script, CLAUDE.md, BUILD_RULES.md |

### How Stages Connect

Every stage reads from the context packet (a JSON object) and writes its output back to the packet. The packet is saved as a snapshot after each stage. If a stage fails, the pipeline rolls back to the previous snapshot and retries or asks a human for help.

**You are building Stage 1: Idea Capture.** It reads from Stage 0's output (the platform profile) and writes to its own namespace (`stage_1`) in the context packet.

---

## Your Stage: Idea Capture

### Purpose

Stage 1 captures the user's raw, unstructured brain dump -- their "rant," voice transcript, scattered notes, or stream-of-consciousness description of an app idea. Its job is NOT to structure, filter, or organize. It simply gets everything out of the user's head. The MORE the user says here, the LESS work Stage 2 (Gap Analysis) has to do.

This is the widest point of the funnel. Every subsequent stage REDUCES ambiguity. By Stage 10, there are ZERO open questions. But here at Stage 1, ambiguity is expected, welcomed, and preserved.

### Inputs (What This Stage Receives)

From the context packet:

```json
{
  "stage_0": {
    "platform_profile": {
      "platform_type": "web | mobile | dual",
      "framework": "react | vue | flutter | ...",
      "language": "typescript | python | dart | ...",
      "is_greenfield": true,
      "deployment_target": "vercel | aws | gcp | ..."
    }
  }
}
```

Stage 1 reads `context_packet.stage_0.platform_profile` ONLY to tailor its intake prompt to the platform context. For example, if the platform is mobile, the prompt might encourage the user to describe gestures or screen flows. If web, it might prompt for page descriptions. This is a LIGHT touch -- it does not constrain the user, only gives gentle contextual cues.

The primary input is the **user's raw idea description**, which arrives as free-form text through the skill invocation. This could be:
- A voice transcript (rant) -- messy, stream-of-consciousness, with filler words
- Typed notes -- bullet points mixed with paragraphs
- Pasted notes from a different tool -- may include formatting artifacts
- Mixed -- some typed, some pasted, some dictated
- As little as 2 sentences from a casual user
- As much as 50 sentences from a detailed/serious user

### Outputs (What This Stage Produces)

Written to `context_packet.stage_1`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `raw_input` | `string` | Yes | The complete, unedited user brain dump. Verbatim or near-verbatim. No filtering, no restructuring, no editorial changes. |
| `input_format` | `string` | Yes | How the input was provided. Enum: `"typed"`, `"voice_transcript"`, `"pasted_notes"`, `"mixed"` |
| `captured_at` | `string` | Yes | ISO 8601 timestamp of when the capture was recorded |
| `word_count` | `integer` | Yes | Word count of `raw_input`. Used by Stage 2 to calibrate questioning depth (short input = more questions, long input = fewer). |
| `char_count` | `integer` | Yes | Character count of `raw_input`. Retained for pipeline analytics and debugging. |
| `explicit_corrections` | `array` | No | Contradictions the user explicitly corrected. Each entry has: |
| `explicit_corrections[].original` | `string` | Yes | What the user originally said |
| `explicit_corrections[].correction` | `string` | Yes | What they corrected it to |
| `explicit_corrections[].context` | `string` | No | Surrounding context explaining the correction |

Also writes to metadata:

| Field | Value |
|-------|-------|
| `metadata.current_stage` | `1` |
| `metadata.updated_at` | ISO 8601 timestamp |
| `metadata.confidence_scores["1"]` | Confidence score object (see Confidence Scoring section) |
| `metadata.stage_timestamps["1"]` | ISO 8601 timestamp |

### Process

#### Step 1: Present the Intake Prompt

Present a low-friction, high-tolerance intake prompt. The prompt must:

- Invite the user to describe their app idea in whatever way is natural to them
- Explicitly state there are no wrong answers, no required fields, no forms to fill out
- Encourage verbosity -- "the more detail you give, the fewer questions we need to ask later"
- Tailor lightly to the platform context from Stage 0 (e.g., if mobile, mention screens/gestures; if web, mention pages/flows) without imposing structure
- Make it clear that contradictions, tangents, and repetitions are welcome -- they provide context

**Do NOT present a form, template, questionnaire, or structured input request.** The user talks however they want.

#### Step 2: Receive and Capture Everything

Accept whatever the user provides. Capture ALL of the following if present:

- The core idea/concept
- Mechanisms they envision (features, workflows, behaviors)
- Context about who it's for (target users, audience)
- Comparisons to existing products ("like Todoist but simpler")
- Technical preferences or constraints they mention ("I want it in React")
- Business context (monetization, scale, market positioning)
- Contradictions and corrections (user says X, then says "actually not X, Y")
- Repetitions and re-framings (user describes the same thing 2-3 ways for context)
- Tangents and side thoughts (may prove relevant in later stages)

**Capture rules:**
- Do NOT summarize, paraphrase, or condense
- Do NOT reorganize into sections or categories
- Do NOT correct grammar, spelling, or formatting
- Do NOT remove filler words from voice transcripts ("like", "um", "you know")
- Do NOT resolve contradictions -- both versions stay in `raw_input`
- DO preserve the user's exact words, sentence structure, and flow

#### Step 3: Detect Input Format

Classify the input format based on textual signals:

| Format | Detection Signals |
|--------|------------------|
| `"voice_transcript"` | Filler words (um, uh, like, you know), run-on sentences, self-corrections mid-sentence, informal speech patterns, lack of punctuation |
| `"typed"` | Complete sentences, proper punctuation, paragraph breaks, no filler words |
| `"pasted_notes"` | Bullet points, numbered lists, formatting artifacts (markdown, HTML), mixed formatting styles, possibly from a different document |
| `"mixed"` | Combination of the above patterns -- e.g., some paragraphs are clearly typed while others look dictated |

If uncertain, default to `"typed"`.

#### Step 4: Detect Explicit Corrections

Scan the raw input for correction patterns. These are places where the user says something, then explicitly reverses or modifies it. Look for markers:

- "actually", "wait", "no", "I mean", "scratch that", "instead", "not X, Y"
- "Oh wait, not just..." / "I forgot..." / "Let me change that..."
- Any statement that directly contradicts an earlier statement in the same input

For each detected correction:
1. Record the `original` statement
2. Record the `correction` (what they changed it to)
3. Record surrounding `context` if it helps explain why they corrected

**Important:** Both the original AND the correction remain in `raw_input`. The corrections array is metadata ABOUT the raw input, not a replacement for it. Resolution of contradictions is Stage 3's job, not Stage 1's.

If the user makes no explicit corrections, `explicit_corrections` is an empty array or omitted entirely.

#### Step 5: Count and Timestamp

- Count words in `raw_input` (split on whitespace, count tokens)
- Count characters in `raw_input` (total character length)
- Record the current timestamp in ISO 8601 format

#### Step 6: Validate Minimum Viability

Check if `word_count >= 20`. This is the minimum viable input.

- If `word_count >= 20`: Proceed to confidence scoring.
- If `word_count < 20`: Prompt the user for more detail. Say something like: "I have your idea captured, but it's quite short. The more detail you give me now, the fewer questions I'll need to ask in the next step. Could you tell me more about what the app does, who it's for, and the main features you envision?" If the user adds more, re-capture and re-count. If the user declines to add more, proceed with what you have but expect a lower confidence score.

### Rules and Constraints

1. **No filtering.** Everything the user says gets captured. Filtering, organizing, and structuring happen in later stages.

2. **No structure imposed.** The user talks however they want. There is no template, no required fields, no form to fill out during Stage 1.

3. **More is better.** The MORE the user says here, the LESS work Stage 2 has to do. The system should encourage verbosity, not constrain it.

4. **Contradictions preserved, not resolved.** If the user says "I want X" and then says "actually, not X, I want Y" -- both statements are captured in `raw_input`. The `explicit_corrections` array tags them, but resolution happens in Stage 3 (Agent OS Structuring), not here.

5. **No mechanism extraction.** Even if the user describes features clearly ("I want a kanban board with drag-and-drop"), Stage 1 does not attempt to identify or classify mechanisms. That is Stage 4's job.

6. **No architectural decisions.** Stage 1 does not decide on tech stack, database design, auth patterns, or anything architectural. It just captures whatever the user mentions about these topics.

7. **The funnel principle.** The pipeline narrows from wide (Stage 1) to precise (Stage 10):
   ```
   WIDE    -> Capture everything (Stage 1)
            -> Fill gaps (Stage 2)
             -> Structure (Stage 3)
              -> Break into parts (Stage 4)
               -> Define each part (Stage 5)
                -> Arrange visually (Stage 6)
                 -> Sequence the build (Stage 7)
                  -> Tag quality checks (Stage 8)
                   -> Configure checker (Stage 9)
   NARROW   -> Output the document (Stage 10)
   ```
   Stage 1 is the widest point. Every subsequent stage REDUCES ambiguity.

8. **Same across product tiers.** Both Tier 1 (subscription/exported PRD) and Tier 2 (internal build) get the same intake experience. "The intake isn't sauce -- it's the funnel. The value is in what happens AFTER the intake."

---

## Files to Read Before Building

Read ALL of these files completely before writing any skill content:

1. **`docs/page-prds/prd-maker/stage-extractions/stage-01-extraction.md`** -- The full extraction dossier for Stage 1. This is your primary source of truth for what the stage does, its edge cases, and its relationship to other stages.

2. **`docs/page-prds/prd-maker/context-packet-schema.md`** -- The data schema. Find Stage 1's namespace (section 2.3). Understand exactly which fields you read (`stage_0.platform_profile`) and write (`stage_1.*`). Also read the full example in section 4 to see what a completed Stage 1 output looks like in context.

3. **`docs/page-prds/prd-maker/stage-contracts.md`** -- Find Stage 1's contract (the "Stage 1: Idea Capture" section). Your skill must produce output that meets all six "Done When" criteria and passes the confidence scoring rubric.

4. **`docs/page-prds/prd-maker/martin-agnostic-checklist.md`** -- The structural checklist. Stage 1 does NOT apply this checklist, but understanding it helps you grasp what "structure" means so you can confirm Stage 1 is NOT imposing any of it prematurely.

5. **`docs/page-prds/prd-maker/nate-jones-skill-kit.md`** -- The skill-building methodology. Your SKILL.md must follow Nate's Prompt 2 output format and pass Nate's Prompt 3 agent-readiness criteria (trigger routing, output completeness, edge case handling, composability).

6. **`docs/page-prds/prd-maker/extracted-skills/nicknisi/skills/ideation/SKILL.md`** -- The ideation skill from nicknisi. This is your **intake pattern reference**. Study its Phase 1 (Intake) section: how it accepts scattered thoughts, voice dictation transcripts, bullet points mixed with rambling, contradictions, and unclear statements. The key line: "Don't require organization. The mess is the input." Adapt this pattern for Stage 1 while respecting the differences: nicknisi's skill goes all the way to contracts and specs; Stage 1 ONLY captures raw input and stops.

---

## Skill Building Instructions

You are building a Claude Code skill using the **Nate B. Jones Output-Extraction Method** (Prompt 2). This means you do NOT write a vague process description -- you reverse-engineer what GREAT output looks like and encode that into the skill.

### The Build Process

**Step 1: Understand the output.** Read the stage extraction dossier and the context packet schema example (section 4 shows a completed `stage_1` object for a task manager app). Understand what a PERFECT Stage 1 output looks like:
- `raw_input` is verbatim, natural-language, unstructured
- `input_format` correctly classifies the input type
- `word_count` and `char_count` are accurate
- `explicit_corrections` correctly tags contradictions without removing them from `raw_input`
- `captured_at` is a valid ISO 8601 timestamp

**Step 2: Extract the methodology.** From the extraction dossier and the nicknisi ideation skill, identify:
- **Structural patterns:** The output is flat -- just raw text plus metadata. No sections, no categories, no hierarchy within `raw_input`.
- **Decision patterns:** The only judgment calls are: (a) what is the input format? (b) did the user make explicit corrections? (c) is the input long enough to proceed?
- **Quality signals:** Great Stage 1 output preserves the user's voice, captures everything including tangents, and correctly detects corrections. Poor Stage 1 output summarizes, reorganizes, or filters.
- **Edge cases:** User gives 2 words. User gives 5,000 words. User contradicts themselves 10 times. User pastes structured markdown. User gives a voice transcript full of "um" and "like".

**Step 3: Build the SKILL.md.** Write the complete skill file following the format in the "Skill Format Requirements" section below.

**Step 4: Self-audit against the 4 Agent-Readiness Criteria** (Nate's Prompt 3):

1. **Trigger Description as Routing Table** -- Does your description contain specific trigger phrases ("raw idea", "brain dump", "idea capture", "describe your app")? Is it specific enough to avoid false matches with Stage 2 (gap analysis) or Stage 3 (structuring)? Does it specify what the skill PRODUCES (raw capture with word count and correction tags)?

2. **Output Format Completeness** -- Is every output field specified with exact name, type, and description? Could Stage 2 parse `stage_1` programmatically and immediately start gap analysis?

3. **Explicit Edge Case Handling** -- What happens when raw_input is under 20 words? When input_format is ambiguous? When the user provides pre-structured input (markdown with headers)? Are failure modes machine-readable?

4. **Composability** -- Could Stage 2 consume this skill's output cleanly? Does the output contain ONLY the structured `stage_1` data (no conversational preamble, no "Here is what I captured:")?

If ANY criterion fails, revise the skill before finalizing.

---

## Skill Format Requirements

### SKILL.md Structure

```markdown
---
name: stage-1-idea-capture
description: {{SINGLE LINE DESCRIPTION -- this is a YAML field, multi-line SILENTLY FAILS}}
---

## Purpose

{{1-2 sentences}}

## When to Use

{{Trigger conditions -- what input or request activates this skill}}

## Input Format

{{Exact JSON structure this skill expects from the context packet}}

## Process

### Step 1: {{Name}}
{{Detailed instructions with decision criteria}}

### Step 2: {{Name}}
{{...}}

[... as many steps as needed ...]

## Output Format

{{Exact JSON structure this skill writes to the context packet -- field names, types, validation rules}}

## Edge Cases

### Missing Input
{{What to do when required fields are empty or missing}}

### Ambiguous Input
{{What to do when input can be interpreted multiple ways}}

### Scope Overflow
{{What to do when the stage discovers work that belongs to a different stage}}

## Confidence Scoring

{{The 5 scoring dimensions from the stage contract, with self-scoring instructions}}

## Escape Hatch

{{When to trigger, what to save, how to signal NEEDS_HUMAN}}

## Example

{{One realistic example showing input -> process -> output for this stage}}
```

### Critical Format Rules

1. **YAML frontmatter `description` MUST be a single line.** Multi-line descriptions silently fail in Claude Code. Keep it under 120 characters.

2. **Total SKILL.md body MUST be under 500 lines / 5,000 tokens.** This is a hard limit from Claude Code's context window management. After compaction, skills are truncated to 5K tokens.

3. **Large reference material goes in a `references/` subfolder**, NOT in the SKILL.md body. Create files like:
   - `references/intake-prompt-templates.md` -- Platform-tailored intake prompt variations (web, mobile, dual)
   - `references/correction-detection-patterns.md` -- Extended list of correction markers and detection heuristics
   - `references/example-captures.md` -- Multiple example captures (minimal, average, verbose, voice transcript)

4. **Output must be structured data (JSON or strict Markdown).** No free-form prose in the output section. Every field must have a name, type, and description.

5. **No conversational text in output.** The skill's output is data for Stage 2, not a message for a human. No "Here is what I found:" or "I captured the following:".

---

## Context Packet Integration

### Reading Input

Your skill reads from the context packet like this:

```python
# Pseudocode -- the skill receives the full context_packet JSON
platform_profile = context_packet["stage_0"]["platform_profile"]
metadata = context_packet["metadata"]
```

Only read from Stage 0. Never read from stages after yours (they do not exist yet).

### Writing Output

Your skill writes to its own namespace:

```python
context_packet["stage_1"] = {
    "raw_input": "<the user's complete unedited brain dump>",
    "input_format": "typed",  # or "voice_transcript", "pasted_notes", "mixed"
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
context_packet["metadata"]["current_stage"] = 1
context_packet["metadata"]["confidence_scores"]["1"] = {
    "score": 92,
    "dimensions": {
        "completeness": 18,
        "accuracy": 20,
        "consistency": 18,
        "specificity": 18,
        "handoff_readiness": 18
    }
}
context_packet["metadata"]["stage_timestamps"]["1"] = "2026-04-03T10:22:40Z"
```

### Validation Before Writing

Before writing output, the skill MUST:
1. Verify all required output fields are populated (`raw_input`, `input_format`, `captured_at`, `word_count`, `char_count`)
2. Verify `raw_input` is non-empty and `word_count >= 20` (or escape hatch was triggered)
3. Verify `input_format` is one of the four valid enum values
4. Verify `captured_at` is a valid ISO 8601 string
5. Verify `word_count` matches actual word count of `raw_input` (within 5% tolerance)
6. Run the confidence scoring
7. If score < 70, trigger escape hatch instead of writing
8. If score 70-89, write but flag in metadata with low-scoring dimensions noted
9. If score >= 90, write normally

---

## Token Budget

Your skill will run within a Claude Code session with approximately 400,000-450,000 total tokens available (after accounting for system prompts, tools, and the context packet itself).

Budget allocation:
- SKILL.md: ~5,000 tokens (hard limit)
- References (combined): ~20,000 tokens max
- Context packet input: ~5,000-10,000 tokens (Stage 0 output is relatively small -- platform profile + checklist IDs + command allowlist)
- Working space for the agent: remaining tokens

Stage 1 is the lightest stage in terms of context packet size because it is the first idea-specific stage. The packet grows significantly in later stages.

Keep your skill lean. Do not repeat information available in the context packet. Reference it by field name instead.

---

## Escape Hatch Pattern

Include this in your SKILL.md:

```
When to trigger:
- User provides fewer than 20 words and declines to add more detail
- The raw_input contains no identifiable app concept (e.g., "hello" or "test" or random characters)
- Confidence score is below 70 after one retry (prompted user for more detail, they added some, still below 70)
- The platform_profile from Stage 0 is missing or malformed (cannot tailor intake prompt)

What to save:
- Current context_packet with whatever partial stage_1 output exists
- The stage number (1) and step where the halt occurred
- What was attempted and what failed (e.g., "user provided 8 words, prompted for more, user added 5 words, total 13 words, still below minimum")
- Suggested questions for the human:
  - "Could you describe what your app does in a few more sentences?"
  - "Who is this app for? What problem does it solve?"
  - "What are the main features you envision?"

How to signal:
- Set metadata.status = "needs_human"
- Add an entry to metadata.escape_hatches array:
  {
    "stage": 1,
    "step": "<step where halt occurred>",
    "reason": "<specific reason>",
    "partial_output": true/false,
    "suggested_actions": ["<action 1>", "<action 2>"]
  }
- Save context_packet snapshot to disk as context_packet_v1_partial.json
- Output a structured NEEDS_HUMAN message:
  {
    "status": "needs_human",
    "stage": 1,
    "problem": "<specific problem description>",
    "suggested_questions": ["<q1>", "<q2>", "<q3>"]
  }
```

---

## Confidence Gate Pattern

Include this self-scoring process in your SKILL.md:

```
After producing output, score each dimension 0-20:

1. Completeness (0-20):
   - 0-5:   raw_input is empty or under 10 words; word_count or input_format missing
   - 6-10:  raw_input has 10-19 words; all fields present but minimal viable input
   - 11-15: raw_input has 20-100 words; all fields populated; at least one app concept identifiable
   - 16-20: raw_input has 100+ words with rich detail; all fields populated; multiple concepts, context, and user intent clearly present

2. Accuracy (0-20):
   - 0-5:   raw_input has been edited, summarized, or rewritten -- does not match what user said
   - 6-10:  raw_input is mostly faithful but some phrases appear paraphrased or reworded
   - 11-15: raw_input preserves user's language faithfully; minor formatting differences acceptable
   - 16-20: raw_input is verbatim or near-verbatim capture including filler phrases, self-corrections, and informal language

3. Consistency (0-20):
   - 0-5:   raw_input contradicts input_format (e.g., format says "voice_transcript" but text is clearly structured markdown)
   - 6-10:  Minor metadata inconsistencies (word_count off by >10%)
   - 11-15: Metadata matches content; word_count accurate within 5%
   - 16-20: All metadata precisely matches content; no discrepancies between fields

4. Specificity (0-20):
   - 0-5:   raw_input is so vague no app concept can be identified (e.g., "I want to make something cool")
   - 6-10:  raw_input mentions an app concept but no features, users, or context
   - 11-15: raw_input includes at least an app concept and 2-3 feature ideas or user descriptions
   - 16-20: raw_input includes app concept, multiple features, target users, and contextual details (comparisons, constraints, preferences)

5. Handoff Readiness (0-20):
   - 0-5:   Stage 2 cannot determine what type of app is being described
   - 6-10:  Stage 2 can identify a rough app type but would need fundamental questions about the core concept
   - 11-15: Stage 2 can identify the app type and start gap analysis immediately; gaps are in specific features, not the core concept
   - 16-20: Stage 2 can identify the app type, match to an archetype, and generate highly targeted gap questions -- most of the concept is already clear

Total = sum of all 5 dimensions (/100)

>= 90: PASS -- proceed to Stage 2 automatically
70-89: WARN -- flag low dimensions, proceed with warning in metadata
< 70:  FAIL -- trigger escape hatch, do NOT pass output to Stage 2
```

---

## Output Location

Save the completed skill to:

```
docs/page-prds/prd-maker/skills/stage-01-idea-capture/SKILL.md
```

If you need reference files, save them to:

```
docs/page-prds/prd-maker/skills/stage-01-idea-capture/references/
```

Suggested reference files for this stage:
- `references/intake-prompt-templates.md` -- Platform-tailored intake prompt variations for web, mobile, and dual platforms, plus a generic fallback
- `references/correction-detection-patterns.md` -- Comprehensive list of linguistic markers for detecting explicit corrections in user input
- `references/example-captures.md` -- 3-4 example captures at different detail levels: minimal (2-3 sentences), average (5-8 sentences), verbose (40-50 sentences), and voice transcript (with filler words and self-corrections)

---

## Agent-Readiness Checklist (Must Pass ALL)

Before finalizing your SKILL.md, verify:

- [ ] **Trigger routing:** The `description` field in YAML frontmatter contains specific trigger phrases (e.g., "raw idea", "brain dump", "capture", "describe your app") and specifies what the skill produces (raw capture with word count, input format, and correction tags)
- [ ] **Output completeness:** Every output field has a name, type, and description. Stage 2 could parse the `stage_1` object programmatically and immediately start gap analysis with zero guessing.
- [ ] **Edge cases explicit:** Missing input (<20 words), ambiguous input format, pre-structured input (user pastes markdown with headers), and scope overflow (user asks Stage 1 to organize their ideas) all have defined behaviors with machine-readable responses
- [ ] **Composability:** The output contains ONLY the structured `stage_1` JSON object and metadata updates. No conversational text, no preamble, no "Here is what I captured." Stage 2 can consume the output as-is.
- [ ] **Under 500 lines:** The SKILL.md body (excluding frontmatter) is under 500 lines
- [ ] **Single-line description:** The YAML `description` field is exactly one line, under 120 characters
- [ ] **Confidence gate included:** The self-scoring process is documented with all 5 dimensions and their 4-tier rubrics
- [ ] **Escape hatch included:** Trigger conditions (under 20 words, no app concept, score < 70, missing Stage 0 data), save protocol, and signal method are documented
- [ ] **Example included:** At least one realistic input/output example showing a user's brain dump being captured into the `stage_1` JSON structure
- [ ] **Context packet fields match schema:** Every field read (`stage_0.platform_profile`) and written (`stage_1.raw_input`, `stage_1.input_format`, `stage_1.captured_at`, `stage_1.word_count`, `stage_1.char_count`, `stage_1.explicit_corrections`) matches context-packet-schema.md section 2.3 exactly

---

## Success Criteria

- [ ] SKILL.md exists at `docs/page-prds/prd-maker/skills/stage-01-idea-capture/SKILL.md`
- [ ] YAML frontmatter has `name: stage-1-idea-capture` and a single-line `description`
- [ ] SKILL.md body is under 500 lines
- [ ] All sections present: Purpose, When to Use, Input Format, Process, Output Format, Edge Cases, Confidence Scoring, Escape Hatch, Example
- [ ] Passes all 4 agent-readiness criteria (trigger routing, output completeness, edge cases, composability)
- [ ] Context packet fields match the schema document (section 2.3 for stage_1, section 2.2 for stage_0 reads)
- [ ] All 6 "Done When" criteria from stage-contracts.md are achievable by following the skill's process:
  1. `raw_input` contains user's complete description with zero filtering
  2. `word_count >= 20` (or escape hatch triggered)
  3. `input_format` is a valid enum value
  4. Contradictions preserved in `raw_input` with correction markers detected
  5. No mechanism extraction or structuring applied
  6. `captured_at` is valid ISO 8601
- [ ] Reference files (if any) are in the `references/` subfolder and total under 20K tokens
- [ ] The skill does NOT perform any work belonging to other stages: no gap analysis (Stage 2), no structuring (Stage 3), no mechanism extraction (Stage 4), no architectural decisions (Stage 0)
