# PRD Maker Pipeline — Stage Contracts

> Completion criteria for every stage in the 10-stage pipeline.
> Each contract defines what "done" means, how to score confidence,
> and what happens when the threshold is not met.
>
> Scoring: 5 dimensions × 20 points = /100 per stage. Threshold: 90 to proceed.

---

## Overall Project Contract

### Problem Statement

The PRD Maker pipeline takes a non-coder's messy app description — as little as two sentences or as much as fifty — and produces a complete, buildable technical specification broken into phased build documents with testing protocols baked in at every seam.

Without this pipeline, non-coders face three outcomes: (a) they try to explain their idea to a developer or AI chatbot and lose critical details in translation, producing vague specs that the builder interprets (invents) rather than executes; (b) they use a single-prompt AI approach and get a "toy" — something that runs but is structurally unsound, missing auth, payments, error handling, and everything else the user assumed but never stated; or (c) they give up because the gap between "I have an idea" and "I have a buildable plan" is too wide.

The cost of not solving this is measured in builds that go rogue, features that drift, agents that improvise in empty rooms, and apps that look functional but collapse under real-world use. Every hour spent debugging a bad spec is an hour that correct specification would have prevented.

### Goals

1. **Buildability**: Every generated spec must pass a buildability check — a coding agent can start building from it without asking clarifying questions. Zero open questions remain by Stage 10.
2. **Input flexibility**: The pipeline must handle input ranging from 2-3 sentence descriptions (minimal viable input) to 50+ sentence detailed rants, producing proportionally complete outputs in both cases.
3. **Category coverage**: The final spec must address all relevant mechanism categories (A-N) from the master checklist for the detected app archetype. No structural gaps survive to the output.
4. **Phase-ready output**: The output package (phase files, build.sh, CLAUDE.md, BUILD_RULES.md) must be copy-paste executable — each phase file is self-contained with sandbox rules, build order, and embedded verification protocols.
5. **Deterministic scaffolding**: Every mechanism in the final spec has Wall/Door/Room classifications. The builder agent never operates in an unstructured space — it always knows what is deterministic (code), constrained (bounded AI), or creative (free AI).

### Success Criteria

- [ ] A coding agent can execute Phase 1 from the output package without requesting clarification
- [ ] Every mechanism in the spec has a Wall/Door/Room classification
- [ ] Every phase file contains file sandbox (ALLOWED/READ-ONLY/FORBIDDEN), build order, pulse/seam/full checkpoints, and violation handling
- [ ] Token math verifies: no phase exceeds 350,000 tokens (325,000 content + 25,000 overhead)
- [ ] The output supports multiple consumption paths: automated (bash build.sh), manual (copy-paste phase-N.md), and hybrid (resume after crash)
- [ ] Three test runs with different app ideas (dashboard, tool, marketplace archetypes) each produce buildable specs scoring ≥7/10 on completeness, accuracy, and handoff quality
- [ ] Every stage in the pipeline produces a confidence score ≥ 90 before passing data downstream

### Scope Boundaries

#### In Scope

- Greenfield app specification (new apps built from scratch)
- All 11 stages (0-10) of the pipeline with confidence gates between each
- Support for common app archetypes (Dashboard, Marketplace, Chat, CRUD/Tool, Social, Wizard, Landing, SaaS)
- Multi-platform output wrappers (Claude Code CLI, Claude Code Web, Codex CLI, Gemini CLI, Cursor, Bolt/Lovable, Generic)
- Context packet versioning (snapshot after each stage, rollback capability)
- Escape hatch protocol (save state, signal NEEDS_HUMAN, resume from saved state)

#### Out of Scope

- Existing app modification path (codebase analysis, incremental feature addition) — deferred to Phase 7+
- Runtime execution of the generated spec (the pipeline produces the spec, not the app)
- AI model selection or API key management — handled by the execution environment
- Graphic pack generation (logos, icons, social cards) — separate product feature
- Tier 1/Tier 2 product differentiation — pipeline produces Tier 2 quality; stripping for Tier 1 is a separate rendering concern

#### Future Considerations

- Existing app path: Stage 0 gets a CODEBASE ANALYSIS sub-step, Martin's checklist runs in CHECK mode, mechanisms are filtered to NEW only
- Self-building: The PRD Maker dashboard is the first app built with the PRD Maker pipeline
- App assessor: A post-build evaluation skill that scores the output against all stage contracts
- Feature addition engine: Re-enter the pipeline at Stage 2 with an existing spec to add new features

---

## Stage 0: Technical Foundation

### Purpose

Establish the platform context (framework, database, auth strategy, hosting, boilerplate) BEFORE any idea-specific work begins, so every downstream stage operates against a known technical stack rather than making assumptions.

### Inputs

- User's platform preferences (if any): framework choice, database preference, hosting target, auth strategy
- Available boilerplate library: list of supported stacks with their capabilities
- Default stack configuration: the recommended stack when user has no preference

### Outputs

Written to `context_packet.stage_0`:

- `platform_profile.framework`: Selected frontend/backend framework (e.g., "Next.js + Supabase", "React + Express + PostgreSQL")
- `platform_profile.database`: Database engine and access pattern
- `platform_profile.auth`: Authentication strategy (e.g., "Supabase Auth", "NextAuth.js", "Firebase Auth")
- `platform_profile.hosting`: Deployment target (e.g., "Vercel", "Railway", "AWS")
- `platform_profile.boilerplate_id`: Which boilerplate template to use
- `platform_profile.supported_mechanisms`: List of mechanism categories (A-N) that the chosen boilerplate natively supports
- `stack_confirmed`: Boolean — user has confirmed or accepted the default stack

### "Done When..." Criteria

1. A `platform_profile` object exists in the context packet with all 6 required fields populated (framework, database, auth, hosting, boilerplate_id, supported_mechanisms)
2. The selected boilerplate exists in the boilerplate library and is marked as active/supported
3. The `supported_mechanisms` list contains at least categories A (Core UI), B (Authentication), and C (Data Layer)
4. `stack_confirmed` is `true` — either the user explicitly chose a stack or accepted the default
5. If the user requested a stack not in the boilerplate library, the escape hatch was triggered with `NEEDS_HUMAN` status and a list of the closest available alternatives
6. No downstream stage field references (framework names, database functions, auth patterns) are left as placeholders or "TBD"

### Confidence Scoring

| Dimension | 0-5 | 6-10 | 11-15 | 16-20 |
|-----------|-----|------|-------|-------|
| Completeness | 3+ fields in platform_profile are empty or "TBD" | 1-2 fields missing; boilerplate_id present but supported_mechanisms incomplete | All fields populated but supported_mechanisms list may have gaps for edge-case categories | All 6 fields populated; supported_mechanisms covers every relevant category for the chosen stack |
| Accuracy | Selected stack does not exist in boilerplate library, or framework/database are incompatible (e.g., "React + MongoDB" when boilerplate requires PostgreSQL) | Stack exists but version or configuration details are wrong or outdated | Stack is valid and compatible; minor configuration details (e.g., hosting region) not specified | Stack is valid, compatible, version-correct, and configuration matches boilerplate expectations exactly |
| Consistency | platform_profile contradicts itself (e.g., framework says "Next.js" but auth says "Firebase Auth" when boilerplate is Supabase-based) | Minor mismatches between fields that could be resolved with one clarification | Fields are internally consistent; no contradictions | All fields align perfectly — framework, database, auth, and hosting form a coherent, tested stack combination |
| Specificity | Fields contain vague values like "a database" or "some framework" | Fields name technologies but lack version or configuration detail (e.g., "React" without specifying Next.js vs. Vite) | Fields specify exact technologies with versions; supported_mechanisms uses category codes (A-N) | Fields specify exact technology + version + configuration; supported_mechanisms includes per-category capability notes |
| Handoff Readiness | Stage 1 would need to ask "what stack are we building on?" before proceeding | Stage 1 could proceed but would need to guess at database patterns or auth flow | Stage 1 can proceed without questions; platform context is clear | Stage 1 and all downstream stages can reference platform_profile for any stack-specific decision without ambiguity |

### Threshold and Failure Handling

- **Score ≥ 90:** Pass to Stage 1 automatically.
- **Score 70-89:** Flag low-scoring dimensions. Present to user: "Your platform profile scored below 18 on [dimensions]. Should I proceed or let you adjust?" If no human available, retry Stage 0 once. If retry still scores 70-89, proceed with a warning flag in the context packet.
- **Score < 70:** Do NOT proceed. Save context packet, log the issue (likely: unsupported stack requested, contradictory preferences, or missing boilerplate). Signal NEEDS_HUMAN.

### What the Next Stage Expects

Stage 1 (Idea Capture) does not directly consume Stage 0's output — it captures raw user input regardless of stack. However, Stage 2 (Gap Analysis) uses the platform profile to generate stack-aware gap questions (e.g., "You chose Supabase — have you considered Row Level Security policies?"), and Stage 4 (Mechanism Extraction) uses `supported_mechanisms` to tag mechanisms as OBVIOUS when the boilerplate handles them natively. The platform profile persists through the entire pipeline and appears in the final output's CLAUDE.md and phase files.

---

## Stage 1: Idea Capture

### Purpose

Capture the user's raw, unstructured app idea — their rant, notes, or stream-of-consciousness — exactly as given, preserving everything including contradictions, repetitions, and tangents, so downstream stages have complete raw material to work with.

### Inputs

- User's raw idea description (voice transcript, typed notes, or free-form text)
- No required format or structure
- No fields to fill in

### Outputs

Written to `context_packet.stage_1`:

- `raw_input`: The user's complete, unfiltered description in their own words
- `word_count`: Integer count of words in the raw input
- `input_format`: How the input was provided (e.g., "typed", "voice_transcript", "pasted_notes")
- `contradictions_preserved`: Boolean — confirms contradictions were kept, not resolved
- `capture_timestamp`: When the capture was recorded

### "Done When..." Criteria

1. `raw_input` contains the user's complete description with zero filtering, structuring, or editorial changes applied
2. `word_count` is ≥ 20 words (minimum viable input — anything less triggers the escape hatch with a prompt for more detail)
3. `input_format` is set to one of the valid values: "typed", "voice_transcript", "pasted_notes", "chat_message"
4. If the user provided contradictory statements (e.g., "I want X" followed by "actually, not X"), both versions are present in `raw_input` — verified by scanning for correction markers ("actually", "I mean", "no wait", "instead")
5. No mechanism extraction, classification, or structuring has been applied to the text — `raw_input` reads as natural language, not organized sections
6. `capture_timestamp` is set to a valid ISO 8601 datetime

### Confidence Scoring

| Dimension | 0-5 | 6-10 | 11-15 | 16-20 |
|-----------|-----|------|-------|-------|
| Completeness | raw_input is empty or under 10 words; word_count or input_format missing | raw_input has 10-19 words; all fields present but word_count suggests minimal viable input | raw_input has 20-100 words; all fields populated; at least one app concept identifiable | raw_input has 100+ words with rich detail; all fields populated; multiple concepts, context, and user intent clearly present |
| Accuracy | raw_input has been edited, summarized, or rewritten — does not match what user actually said | raw_input is mostly faithful but some phrases appear paraphrased or reworded | raw_input preserves user's language faithfully; minor formatting differences (punctuation, line breaks) acceptable | raw_input is a verbatim or near-verbatim capture of user's exact words, including filler phrases, self-corrections, and informal language |
| Consistency | raw_input contradicts the input_format (e.g., format says "voice_transcript" but text is clearly structured markdown) | Minor metadata inconsistencies (e.g., word_count is off by >10%) | Metadata matches content; word_count is accurate within 5% | All metadata precisely matches the content; no discrepancies between fields |
| Specificity | raw_input is so vague no app concept can be identified (e.g., "I want to make something cool") | raw_input mentions an app concept but no features, users, or context | raw_input includes at least an app concept and 2-3 feature ideas or user descriptions | raw_input includes app concept, multiple feature ideas, target users, and contextual details (comparisons, constraints, preferences) |
| Handoff Readiness | Stage 2 cannot determine what type of app is being described | Stage 2 can identify a rough app type but would need to ask fundamental questions about the core concept | Stage 2 can identify the app type and start gap analysis immediately; gaps are in specific features, not the core concept | Stage 2 can identify the app type, match to an archetype, and generate highly targeted gap questions — most of the concept is already clear |

### Threshold and Failure Handling

- **Score ≥ 90:** Pass to Stage 2 automatically.
- **Score 70-89:** Flag concerns. Present to user: "Your idea capture scored below 18 on [dimensions]. Would you like to add more detail or proceed?" If no human available, retry once by prompting user for more input. If retry still scores 70-89, proceed with a warning flag.
- **Score < 70:** Do NOT proceed. Most likely cause: input under 20 words or so vague no app concept is identifiable. Trigger escape hatch. Present: "I need more information about your app idea to continue. Could you describe what the app does, who it's for, and the main features you envision?"

### What the Next Stage Expects

Stage 2 (Gap Analysis) receives `raw_input` and performs pattern matching to identify the app archetype, then compares what the user described against what that archetype typically requires. The MORE detail in `raw_input`, the FEWER gap questions Stage 2 needs to ask. Stage 2 does not expect any structure — it is designed to parse raw human language. Stage 2 also reads `word_count` to calibrate its questioning depth (short input = more questions, long input = fewer questions).

---

## Stage 2: Gap Analysis

### Purpose

Identify everything missing, ambiguous, or incomplete in the raw idea capture and fill those gaps through intelligent, adaptive questioning so downstream stages receive complete information rather than structuring around holes.

### Inputs

From `context_packet.stage_1`:

- `raw_input`: The user's unfiltered app description
- `word_count`: Used to calibrate questioning depth

From `context_packet.stage_0`:

- `platform_profile`: Used to generate stack-aware questions

### Outputs

Written to `context_packet.stage_2`:

- `matched_archetype`: The app archetype identified from raw input (e.g., "Dashboard", "Marketplace", "Chat", "CRUD/Tool", "Wizard")
- `archetype_confidence`: Float 0.0-1.0 indicating match confidence
- `mechanism_map`: Object with categories A-N, each classified as REQUIRED, OPTIONAL, or UNLIKELY for this app
- `gap_questions`: Array of questions asked, each with `question_text`, `category` (which A-N category it addresses), and `status` ("answered" | "unanswered" | "user_declined")
- `gap_answers`: Array of user responses matched to their questions
- `complete_raw_material`: The combined Stage 1 raw input + Stage 2 gap answers as a unified text block
- `unresolved_gaps`: Array of gaps where user declined to answer or answer was ambiguous — flagged for Stage 3 to handle

### "Done When..." Criteria

1. Every mechanism category (A-N) has a classification (REQUIRED, OPTIONAL, or UNLIKELY) in the `mechanism_map`
2. `matched_archetype` is set to one of the recognized archetypes and `archetype_confidence` is ≥ 0.7
3. All questions in `gap_questions` have `status` set to "answered" or "user_declined" — none remain "unanswered"
4. `complete_raw_material` contains both the original `raw_input` AND all gap answers combined into a single text block
5. If `word_count` from Stage 1 was < 50, at least 5 gap questions were asked; if ≥ 50, at least 2 gap questions were asked
6. For every category classified as REQUIRED in `mechanism_map`, at least one sentence in `complete_raw_material` addresses that category
7. `unresolved_gaps` explicitly lists any categories where the user declined to answer, with the default assumption noted (e.g., "User declined to specify auth method — defaulting to standard email/password per archetype default")

### Confidence Scoring

| Dimension | 0-5 | 6-10 | 11-15 | 16-20 |
|-----------|-----|------|-------|-------|
| Completeness | More than 4 A-N categories have no classification; archetype not identified | 2-4 categories unclassified; archetype identified but with low confidence (<0.5) | All categories classified; 1-2 REQUIRED categories have thin coverage in complete_raw_material | All categories classified; every REQUIRED category has substantive coverage; zero classification gaps |
| Accuracy | Archetype match is clearly wrong (e.g., "Marketplace" for a single-user note-taking app); categories misclassified | Archetype is plausible but not the best fit; 2-3 categories arguably misclassified | Archetype matches well; at most 1 borderline category classification | Archetype is the obvious best match; all category classifications are defensible and align with what user described |
| Consistency | gap_answers contradict raw_input and contradictions are not flagged | Some contradictions between raw_input and answers exist but are partially noted | Minor inconsistencies exist and are documented in unresolved_gaps | complete_raw_material is internally consistent; all contradictions from raw_input have been resolved through gap questions or flagged explicitly |
| Specificity | Questions asked were generic ("tell me more") rather than targeted at specific gaps | Questions targeted categories but were broad ("What about authentication?") | Questions referenced specific gaps and offered options ("Will authentication use email/password, OAuth, or magic links?") | Questions were precise, referenced what the user already said, offered 2-3 specific options per question, and minimized question count while maximizing information gained |
| Handoff Readiness | Stage 3 would need to ask "what is this app?" — the complete_raw_material is not sufficient to structure | Stage 3 can identify the concept but would struggle with 3+ sections due to missing information | Stage 3 can produce a structured document but 1-2 sections would be thin | Stage 3 can produce a fully fleshed structured concept document from complete_raw_material without needing any additional information |

### Threshold and Failure Handling

- **Score ≥ 90:** Pass to Stage 3 automatically.
- **Score 70-89:** Flag low-scoring dimensions. Present to user: "Gap analysis has some thin areas in [categories]. Want to add more detail or proceed?" If no human available, retry Stage 2 with a prompt to ask 2-3 more targeted questions about the weakest categories. If retry still scores 70-89, proceed with warning flag.
- **Score < 70:** Do NOT proceed. Likely cause: user refused to answer critical questions, or archetype could not be identified. Trigger escape hatch. Save context packet. Log: "Gap analysis incomplete — [specific categories] have no coverage."

### What the Next Stage Expects

Stage 3 (Agent OS Structuring) receives `complete_raw_material` and treats it as the authoritative raw information to structure. It expects this to be COMPLETE — it formats what it receives without checking for gaps. If Stage 2 missed a concept (like payments), Stage 3 will structure around the hole without noticing. Stage 3 also uses `matched_archetype` to inform how it frames the concept (a "Dashboard" gets different market context framing than a "Marketplace").

---

## Stage 3: Agent OS Structuring

### Purpose

Transform the complete raw information (Stage 1 capture + Stage 2 gap answers) from messy human language into a structured concept document organized into four sections — turning raw clay into a shaped block that downstream stages can process cleanly.

### Inputs

From `context_packet.stage_2`:

- `complete_raw_material`: Combined Stage 1 + Stage 2 output
- `matched_archetype`: App type for framing context
- `unresolved_gaps`: Items that could not be resolved — must be explicitly addressed

From `context_packet.stage_0`:

- `platform_profile`: Stack context for technical framing

### Outputs

Written to `context_packet.stage_3`:

- `concept_document`: Object containing four sections:
  - `concept_and_context`: What the product is, framed clearly (name, elevator pitch, core value proposition)
  - `target_user_and_market`: Who it is for, market positioning, competitive landscape
  - `feasibility_assessment`: Technical viability, resource requirements, risk factors
  - `problem_statement`: What pain point the product solves, stated in user-centric terms
- `ambiguities_resolved`: Array of ambiguities found in the raw material and how they were resolved (later statements override earlier ones)
- `ambiguities_flagged`: Array of ambiguities that could not be resolved without user input — tagged for downstream awareness
- `concept_document_word_count`: Integer word count of the full structured document

### "Done When..." Criteria

1. `concept_document` contains all four required sections (`concept_and_context`, `target_user_and_market`, `feasibility_assessment`, `problem_statement`), each with at least 50 words of substantive content
2. Every piece of information from `complete_raw_material` appears in at least one section of the concept document — nothing from the raw input was dropped during structuring
3. The concept document contains ONLY "what" and "why" — no mechanism decomposition ("how") has occurred. If the document mentions specific mechanisms by name and classifies them, the stage has overstepped
4. All contradictions from the raw material are resolved using the "later statements override earlier ones" rule, and each resolution is logged in `ambiguities_resolved`
5. Any ambiguities that could NOT be resolved (require user input) are listed in `ambiguities_flagged` with the specific question that needs answering
6. The document is readable as organized prose, not stream-of-consciousness — a human unfamiliar with the project could read it and understand the full concept

### Confidence Scoring

| Dimension | 0-5 | 6-10 | 11-15 | 16-20 |
|-----------|-----|------|-------|-------|
| Completeness | 2+ sections are empty or contain only placeholder text | All 4 sections exist but 1-2 are under 50 words or lack substance | All 4 sections have substantive content; minor information from raw_material may not be incorporated | All 4 sections are thorough; every concept from complete_raw_material is represented; concept_document_word_count reflects comprehensive coverage |
| Accuracy | concept_document misrepresents the user's idea (e.g., describes a different app than what was described) | concept_document captures the core idea but some details are inaccurate or embellished beyond what user said | concept_document faithfully represents the user's idea; no invented features or assumptions beyond what was stated | concept_document is a precise, faithful structuring of the user's idea with clear sourcing to raw input; nothing added, nothing lost |
| Consistency | Sections contradict each other (e.g., problem_statement says "for enterprises" but target_user says "for individuals") | Minor internal inconsistencies between sections | Sections are consistent with each other; ambiguities_resolved documents how contradictions were handled | All sections align perfectly; ambiguities_resolved is thorough; ambiguities_flagged is honest about remaining uncertainties |
| Specificity | Sections contain vague generalizations ("this will help people") without connecting to the specific app concept | Sections reference the specific app but use broad language ("it will have features for users") | Sections name specific features, specific users, and specific value propositions tied to the app concept | Sections are precise enough that two different readers would draw the same conclusions about what is being built and for whom |
| Handoff Readiness | Stage 4 would need to ask "what is this app?" before extracting mechanisms — the document does not describe the product clearly | Stage 4 can identify some mechanisms but the document's lack of clarity would cause some mechanisms to be missed or misidentified | Stage 4 can extract mechanisms cleanly; 1-2 edge-case mechanisms might need clarification | Stage 4 can extract every mechanism from this document without ambiguity; overlapping concepts are resolved; boundaries between features are clear |

### Threshold and Failure Handling

- **Score ≥ 90:** Pass to Stage 4 automatically.
- **Score 70-89:** Flag concerns. Present to user: "The structured concept scored below 18 on [dimensions]. Want me to revise or proceed?" If no human available, retry Stage 3 once. If retry still scores 70-89, proceed with warning flag and note which sections are thin.
- **Score < 70:** Do NOT proceed. Likely cause: raw material was too incomplete (Stage 2 failed its job) or ambiguities are too severe to resolve. Trigger escape hatch. Log specific sections that are inadequate and why.

### What the Next Stage Expects

Stage 4 (Mechanism Extraction) reads `concept_document` and breaks it into discrete mechanisms. It expects a document that describes the full product concept with enough specificity that every functional unit can be identified and named. If the document is vague about a feature area, Stage 4 will either miss that mechanism entirely or extract it with insufficient detail. Stage 4 also references `platform_profile` from Stage 0 to determine which mechanisms are OBVIOUS (handled natively by the boilerplate).

---

## Stage 4: Mechanism Extraction

### Purpose

Break the structured concept document into its discrete moving parts — individual mechanisms, features, and components — each tagged as OBVIOUS (one clear implementation path) or NEEDS_EVALUATION (multiple viable approaches), so every functional unit is identified before the deterministic scaffolding is applied.

### Inputs

From `context_packet.stage_3`:

- `concept_document`: The four-section structured concept

From `context_packet.stage_0`:

- `platform_profile`: Stack context, including `supported_mechanisms` to identify which mechanisms the boilerplate handles natively

From `context_packet.stage_2`:

- `mechanism_map`: A-N category classifications to cross-reference

### Outputs

Written to `context_packet.stage_4`:

- `mechanisms`: Array of mechanism objects, each containing:
  - `id`: Unique identifier (e.g., "mech_auth", "mech_payment")
  - `name`: Descriptive label (e.g., "Auth System", "Payment Flow")
  - `description`: What this mechanism does (2-5 sentences)
  - `category`: Which A-N category it belongs to
  - `classification`: "OBVIOUS" or "NEEDS_EVALUATION"
  - `is_core`: Boolean — is this the core mechanism that makes the app special?
  - `dependencies`: Array of mechanism IDs this mechanism depends on
  - `approaches` (if NEEDS_EVALUATION): Array of 2-3 viable implementation approaches, each with `name`, `pros`, `cons`, `score` (0-100)
  - `chosen_approach`: The selected implementation approach (auto-selected for OBVIOUS; highest-scoring or Developer's Choice for evaluated)
- `mechanism_count`: Total number of mechanisms extracted
- `core_mechanism_id`: ID of the mechanism identified as the core differentiator
- `dual_design_flags`: Array of mechanism IDs where two approaches scored within 15% of each other — both approaches are designed

### "Done When..." Criteria

1. `mechanism_count` is ≥ 3 (any real app has at least 3 discrete mechanisms) and every mechanism has all required fields populated (id, name, description, category, classification, chosen_approach)
2. Every mechanism tagged as NEEDS_EVALUATION has at least 2 approaches listed with pros, cons, and scores
3. Every REQUIRED category from Stage 2's `mechanism_map` has at least one mechanism extracted for it — no REQUIRED category is unrepresented
4. Exactly one mechanism has `is_core: true` — the core differentiator is identified
5. `dependencies` arrays form a valid directed acyclic graph (no circular dependencies)
6. Mechanism granularity is correct: no mechanism is a single button/field (too small) and no mechanism is "the whole dashboard" when it contains multiple independent functional areas (too big)
7. For mechanisms within 15% score range, both approaches are recorded in `dual_design_flags` and both have full approach objects

### Confidence Scoring

| Dimension | 0-5 | 6-10 | 11-15 | 16-20 |
|-----------|-----|------|-------|-------|
| Completeness | Fewer than 3 mechanisms extracted; REQUIRED categories have no mechanisms; multiple fields empty | 3+ mechanisms but 2+ REQUIRED categories are missing representation; some mechanisms lack descriptions | All REQUIRED categories represented; all mechanisms have complete fields; 1-2 mechanisms may need splitting or merging | All REQUIRED and OPTIONAL categories represented where relevant; every mechanism is properly sized; core mechanism identified; dependency graph is complete |
| Accuracy | Mechanisms describe features not in the concept document (hallucinated); classifications are clearly wrong | Most mechanisms match the concept document but 2-3 are misidentified or misclassified (OBVIOUS tagged as NEEDS_EVALUATION or vice versa) | Mechanisms accurately reflect the concept document; classifications are defensible; approach scores are reasonable | Every mechanism traces directly to something in the concept document; classifications are clearly correct; approach evaluations reflect genuine engineering tradeoffs |
| Consistency | Mechanisms overlap (same feature described twice as different mechanisms); dependencies are circular | Minor overlaps between 1-2 mechanisms; dependencies are mostly correct but 1-2 may be missing | No overlaps; dependency graph is valid; mechanism descriptions don't contradict each other | Mechanisms are cleanly separated; dependency graph is comprehensive and acyclic; each mechanism has a unique, non-overlapping scope |
| Specificity | Mechanism descriptions are vague ("handles user stuff"); no clear boundaries between mechanisms | Descriptions name the feature area but lack detail about what the mechanism actually does | Descriptions explain what the mechanism does, what it inputs/outputs, and what decisions it involves | Descriptions are precise enough that Stage 5 can immediately apply the 7 questions without asking "what exactly does this mechanism do?" |
| Handoff Readiness | Stage 5 would need to ask "what are the actual mechanisms?" — the list is too incomplete or vague to scaffold | Stage 5 can scaffold most mechanisms but 2-3 are too vague or poorly scoped | Stage 5 can scaffold all mechanisms; 1-2 might need minor clarification on scope boundaries | Stage 5 can immediately apply the 7-question framework to every mechanism without ambiguity — each mechanism's scope, inputs, outputs, and key decisions are crystal clear |

### Threshold and Failure Handling

- **Score ≥ 90:** Pass to Stage 5 automatically.
- **Score 70-89:** Flag concerns. Present to user: "Mechanism extraction scored below 18 on [dimensions]. [List specific mechanisms that need attention.] Proceed or revise?" If no human available, retry Stage 4 once. If retry still scores 70-89, proceed with warning flag.
- **Score < 70:** Do NOT proceed. Likely cause: concept document was too vague for clean extraction, or the app is too complex for the mechanism count. Trigger escape hatch. Consider whether Stage 3 output needs revision.

### What the Next Stage Expects

Stage 5 (7-Question Scaffolding) takes each mechanism from the `mechanisms` array and applies the seven questions to classify every step as Wall, Door, or Room. It expects each mechanism to have a clear enough description that the 7 questions can be answered without guessing. It also expects `chosen_approach` to be set so it knows WHICH implementation path to scaffold. For `dual_design_flags` mechanisms, Stage 5 scaffolds BOTH approaches.

---

## Stage 5: 7-Question Scaffolding

### Purpose

Apply the 7-question deterministic framework to every mechanism, classifying each step as WALL (deterministic — code handles), DOOR (constrained — AI within strict boundaries), or ROOM (creative — AI has freedom), producing the architectural blueprint that prevents builder agents from improvising in unstructured spaces.

### Inputs

From `context_packet.stage_4`:

- `mechanisms`: The full mechanism list with chosen approaches
- `dual_design_flags`: Mechanisms needing both approaches scaffolded

Martin's agnostic build rules: Used as the LENS (not injected later — the architect follows building code WHILE designing)

### Outputs

Written to `context_packet.stage_5`:

- `blueprints`: Array of blueprint objects, one per mechanism (plus duplicates for dual-design mechanisms), each containing:
  - `mechanism_id`: Reference to Stage 4 mechanism
  - `approach_id`: Which approach this blueprint is for (relevant for dual-design)
  - `phases`: Array of phase objects, each containing:
    - `phase_name`: Descriptive name
    - `entry_condition`: What must be true to enter this phase (WALL)
    - `exit_condition`: What must be true to leave this phase (WALL)
    - `steps`: Array of step objects, each containing:
      - `step_name`: Descriptive name
      - `classification`: "WALL" | "DOOR" | "ROOM"
      - `seven_question_answers`: Object with answers to all 7 questions
      - `validation`: How to verify this step was done correctly
      - `constraints` (for DOORs): What boundaries the AI must stay within
      - `skip_condition` (if skippable): Under what condition this step can be skipped
- `total_walls`: Count of WALL-classified steps across all blueprints
- `total_doors`: Count of DOOR-classified steps
- `total_rooms`: Count of ROOM-classified steps
- `wall_door_room_ratio`: String showing the ratio (e.g., "65/25/10")

### "Done When..." Criteria

1. Every mechanism from Stage 4 has a corresponding blueprint in `blueprints` — no mechanism was skipped
2. For every mechanism in `dual_design_flags`, TWO blueprints exist (one per approach)
3. Every step in every blueprint has a `classification` of "WALL", "DOOR", or "ROOM" — no step is unclassified, no "TBD", no "UNCLEAR"
4. Every step has all 7 questions answered in `seven_question_answers` — no question is blank or marked as "N/A" without explicit justification
5. Every WALL step has a `validation` method that can be checked by code (e.g., "file exists", "function exports X", "response matches schema") — not subjective criteria
6. Every DOOR step has explicit `constraints` defining the boundaries the AI must stay within
7. Every blueprint phase has both an `entry_condition` and `exit_condition` defined
8. Martin's build principles are reflected in the scaffolding: single responsibility per step, no state leakage between phases, imports flow downward

### Confidence Scoring

| Dimension | 0-5 | 6-10 | 11-15 | 16-20 |
|-----------|-----|------|-------|-------|
| Completeness | 3+ mechanisms have no blueprints; multiple steps lack classifications | All mechanisms have blueprints but 2+ have incomplete steps or missing 7-question answers | All mechanisms fully scaffolded; all steps classified; 1-2 steps have thin validation methods | Every mechanism has a thorough blueprint; every step has all 7 questions answered, a classification, validation, and constraints (for DOORs); dual-design mechanisms have both blueprints |
| Accuracy | Classifications are clearly wrong (e.g., "user authentication validation" marked as ROOM instead of WALL) | Most classifications are correct but 3+ steps are arguably misclassified | Classifications are defensible; at most 1-2 borderline cases | Every classification is the obvious correct choice; walls are genuinely deterministic, doors have genuine constraints, rooms have genuine creative freedom |
| Consistency | Blueprint steps contradict mechanism descriptions from Stage 4; entry/exit conditions don't connect across phases | Minor mismatches between blueprints and mechanism descriptions; most entry/exit conditions chain correctly | Blueprints are consistent with mechanisms; all entry/exit conditions chain across phases within a mechanism | Blueprints are perfectly consistent with Stage 4 mechanisms and with each other; cross-mechanism connections (dependencies) are reflected in entry/exit conditions |
| Specificity | Steps are vague ("handle the auth thing"); validations are generic ("check it works") | Steps name specific actions but lack detail; validations describe what to check but not how | Steps describe specific actions with specific inputs/outputs; validations name specific checks (e.g., "function exports loginUser, signupUser") | Steps are detailed enough to write code from; validations are machine-executable checks; constraints for DOORs specify exact boundaries with no wiggle room |
| Handoff Readiness | Stage 6 would not know what components to put on pages because the blueprints don't describe the functional units clearly | Stage 6 can identify major components but would guess at some connections between mechanisms | Stage 6 can lay out pages with known components and connections; 1-2 minor connections might need inference | Stage 6 can deterministically arrange pages — every mechanism's UI surface, every connection between rooms, and every wall's visual representation is clear from the blueprints |

### Threshold and Failure Handling

- **Score ≥ 90:** Pass to Stage 6 automatically.
- **Score 70-89:** Flag low-scoring dimensions. Present to user: "The scaffolding scored below 18 on [dimensions]. Specific concerns: [list mechanisms with issues]. Proceed or revise?" If no human available, retry Stage 5 once focusing on the weakest mechanisms. If retry still scores 70-89, proceed with warning flag.
- **Score < 70:** Do NOT proceed. Likely cause: mechanism descriptions from Stage 4 were too vague for the 7 questions to produce meaningful answers, or the mechanisms are so novel that standard patterns don't apply. Trigger escape hatch.

### What the Next Stage Expects

Stage 6 (Layout + Mockups + Style) uses the blueprints to determine what components go on which pages and how they connect. It expects to know exactly how many screens each mechanism requires, what UI elements are walls (fixed, non-configurable), which are doors (user-configurable within constraints), and which are rooms (creative/dynamic content). Stage 6 also expects the blueprints to make clear which mechanisms are user-facing (need UI) versus backend-only (no page needed).

---

## Stage 6: Layout + Mockups + Style

### Purpose

Arrange the classified mechanisms into visual structure — page layouts, navigation patterns, component placement, and style selection — using deterministic app-type-to-wireframe pattern matching rather than AI creativity for the structural decisions.

### Inputs

From `context_packet.stage_5`:

- `mechanism_blueprints`: Wall/Door/Room classifications for all mechanisms

From `context_packet.stage_4`:

- `mechanisms`: Mechanism list with names, descriptions, and dependencies

From `context_packet.stage_3`:

- `concept_and_context`: Product concept for context

From `context_packet.stage_2`:

- `archetype_matches`: App type for wireframe pattern lookup

### Outputs

Written to `context_packet.stage_6`:

- `sub_6a`: Arrangement selection:
  - `app_type_classification`: Confirmed app type used for wireframe selection
  - `arrangement_options`: Array of 2-3 layout options presented to user
  - `selected_arrangement_id`: User's chosen arrangement
  - `user_adjustments`: Any user modifications (or null)
- `sub_6b`: Page mockups:
  - `pages`: Array of page objects, each with:
    - `page_name`: Descriptive name
    - `route`: URL path (kebab-case)
    - `layout_pattern`: Layout pattern from selected arrangement
    - `components`: Array of component descriptions with `component_name`, `placement`, and `mechanism_ids`
    - `backend_services`: Array of mechanism IDs for backend-only mechanisms served by this page
    - `user_approved`: Boolean
  - `all_mechanisms_mapped`: Boolean — every mechanism from Stage 4 appears on at least one page
  - `pages_approved`: Boolean — user has approved all page layouts
- `sub_6c`: Style selection:
  - `style_options_presented`: Array of 3 curated style options
  - `selected_style_id`: One of the 12 predefined style IDs (or "custom")
  - `design_tokens`: Object with `colors`, `typography`, `spacing`, `border_radius`, `shadows`
  - `tailwind_config_overrides`: Tailwind config overrides
  - `audience_scores`: Object with `audience_fit`, `vibe_match`, `age_range_fit`

### "Done When..." Criteria

1. `sub_6b.pages` contains at least 2 pages (login/auth + one functional page) and every page has a `route`, `components` array with `mechanism_ids`, and `layout_pattern` defined
2. Every mechanism from Stage 4 appears in at least one page component's `mechanism_ids` array — `sub_6b.all_mechanisms_mapped` is `true`. No mechanism is "homeless"
3. `sub_6a.selected_arrangement_id` is set and matches a recognized pattern for the `app_type_classification`
4. `user_approved` is `true` for every page in `sub_6b.pages` — or, if running without human input, the layouts match the deterministic pattern for the app type
5. `sub_6c` contains a valid `selected_style_id` from the predefined set (or "custom" with full tokens provided), and `design_tokens` is populated with `colors`, `typography`, `spacing`, `border_radius`, and `shadows`
6. `sub_6b.pages_approved` is `true` — the overall layout has been confirmed

### Confidence Scoring

| Dimension | 0-5 | 6-10 | 11-15 | 16-20 |
|-----------|-----|------|-------|-------|
| Completeness | Page list has fewer than 2 pages; multiple mechanisms unmapped; style not selected | Pages cover most mechanisms but 2+ are missing from all pages; style selected but tokens incomplete | All mechanisms mapped to pages; all style tokens populated; 1-2 pages might have thin component lists | Every mechanism on a page; every page has complete component list with connections; style is fully specified with all tokens; navigation pattern selected and justified |
| Accuracy | Wireframe pattern does not match the app type (e.g., chat layout for a dashboard app); mechanisms placed on wrong pages | Pattern roughly matches app type; most mechanisms on correct pages; 2-3 component placements are questionable | Pattern correctly matches app type; mechanisms on correct pages; component placement follows standard UX conventions | Pattern is the obvious correct choice for the app type; every mechanism is on the page where users would expect it; style matches the target audience |
| Consistency | Page routes conflict; components reference mechanisms that don't exist in Stage 4; style contradicts app type | Minor route conflicts or redundant pages; most component→mechanism references are valid | No route conflicts; all component→mechanism references are valid; style is appropriate for app type | Routes are clean and follow conventions; every component→mechanism reference is bidirectionally valid; style, layout, and archetype form a coherent visual identity |
| Specificity | Pages described as "main page" and "settings" with no component details | Pages have names and routes but components are vague ("some buttons", "a form") | Pages have named components with placement descriptions and mechanism connections | Every component has exact placement, exact mechanism connection, and exact interaction description; a developer could build the page from this specification alone |
| Handoff Readiness | Stage 7 cannot determine what files are needed because pages and components are not defined | Stage 7 can estimate phase count but cannot assign specific files to phases because component specs are incomplete | Stage 7 can assign files to phases and calculate token estimates; minor details might require inference | Stage 7 can create exact file sandbox lists, build orders, and token estimates from the page/component specifications without any guesswork |

### Threshold and Failure Handling

- **Score ≥ 90:** Pass to Stage 7 automatically.
- **Score 70-89:** Flag concerns. Present to user: "Layout scored below 18 on [dimensions]. [Show which mechanisms lack pages or which pages lack detail.] Proceed or revise?" If no human available, retry Stage 6 once. If retry still scores 70-89, proceed with warning flag.
- **Score < 70:** Do NOT proceed. Likely cause: blueprints from Stage 5 were too abstract to map to pages, or the app concept doesn't fit standard layout patterns. Trigger escape hatch.

### What the Next Stage Expects

Stage 7 (Phase Sequencing) needs the FULL picture — mechanisms + scaffolding + wireframes + style — to intelligently split the build into phases. It expects to know every page, every file that will need to be created, and every connection between components. It uses the page/component specifications to create file sandbox lists (ALLOWED/READ-ONLY/FORBIDDEN) and build orders (core logic → state → UI → integration) within each phase.

---

## Stage 7: Phase Sequencing

### Purpose

Split the complete specification into buildable phases using math-based token budget calculations, each phase being a self-contained containment unit with its own file sandbox, build order, and dependency mapping.

### Inputs

From `context_packet.stage_3` through `stage_6`: Complete Agent OS document (concept + mechanisms + blueprints + wireframes + style)

Token budget constraints:
- Total budget: 500,000 tokens (50% of 1M context)
- Per-phase overhead: ~25,000 tokens (fixed, templated)
- Target per-phase content: 325,000 tokens (350,000 total minus 25,000 overhead)

### Outputs

Written to `context_packet.stage_7`:

- `phase_count`: Number of phases
- `total_estimated_tokens`: Estimated total token count of the full spec
- `phases`: Array of phase objects, each containing:
  - `phase_number`: Integer (1-based)
  - `phase_name`: Descriptive name (e.g., "Auth System", "Dashboard + Features")
  - `estimated_content_tokens`: Token estimate for this phase's content
  - `estimated_total_tokens`: Content + overhead (~25K)
  - `file_sandbox`: Object with:
    - `allowed`: Array of file paths this phase can create/modify
    - `read_only`: Array of file paths this phase can reference but NOT change
    - `forbidden`: Description of everything else (or explicit list for small projects)
  - `build_order`: Array of file paths in the forced linear sequence with rationale for each
  - `depends_on`: Array of phase numbers that must complete before this phase starts
  - `mechanisms_included`: Array of mechanism IDs built in this phase
- `no_mechanism_split`: Boolean — confirms no mechanism was split across multiple phases
- `token_math_verified`: Boolean — confirms every phase fits within budget

### "Done When..." Criteria

1. `phase_count` ≥ 1 and `total_estimated_tokens / 325000` rounded up equals `phase_count` (±1 phase for boundary adjustments)
2. Every phase's `estimated_total_tokens` is ≤ 350,000 (325,000 content + 25,000 overhead)
3. No mechanism from Stage 4 is split across multiple phases — every mechanism appears in exactly one phase's `mechanisms_included`
4. Every mechanism from Stage 4 appears in at least one phase's `mechanisms_included` — no mechanism was dropped
5. Every phase has a `file_sandbox` with all three tiers (allowed, read_only, forbidden) populated
6. Every phase has a `build_order` with at least 2 entries in the forced linear sequence
7. Phase dependencies form a valid directed acyclic graph — no circular dependencies
8. Build order within each phase follows the pattern: core logic → state management → UI components → integration/routing

### Confidence Scoring

| Dimension | 0-5 | 6-10 | 11-15 | 16-20 |
|-----------|-----|------|-------|-------|
| Completeness | Phase list is empty or missing sandbox/build_order fields; mechanisms not assigned to phases | Phases exist but 2+ are missing file sandboxes or build orders; some mechanisms unassigned | All phases have sandboxes and build orders; all mechanisms assigned; 1-2 phases have minimal build orders | Every phase has complete sandbox (3 tiers), detailed build order with rationales, explicit dependencies, and mechanism assignments; no gaps |
| Accuracy | Token estimates are clearly wrong (e.g., single-page app estimated at 900K tokens); mechanisms in wrong phases | Token estimates are roughly correct (±30%); mechanism-to-phase assignment is mostly logical | Token estimates are within ±15%; mechanism-to-phase assignments follow dependency order; build order follows correct pattern | Token estimates are within ±10%; mechanism assignments optimize for dependency resolution; build order precisely follows core→state→UI→integration pattern |
| Consistency | Phase dependencies are circular; file sandboxes overlap (same file in "allowed" for multiple phases); build orders reference files not in the sandbox | Minor sandbox overlaps on shared files; dependencies are acyclic; most build orders reference only sandbox files | No sandbox conflicts; dependencies are clean; all build order files are in the phase's sandbox; shared files handled via read_only | Sandboxes are perfectly partitioned; dependencies reflect actual build requirements; build orders are self-consistent and reference only allowed files; read_only files are correctly identified |
| Specificity | Sandboxes say "some files" or "the auth files"; build orders list vague entries | Sandboxes name directories but not specific files; build orders name files but not rationale | Sandboxes name specific files with paths; build orders include rationale for sequence | Sandboxes name exact file paths with file status (NEW vs MODIFY); build orders include specific rationale for each file's position and what it produces for subsequent files |
| Handoff Readiness | Stage 8 cannot inject protocols because the phases lack structure (no sandbox, no build order to inject checkpoints into) | Stage 8 can inject protocols but would need to infer where seam checks go because build order lacks connection points | Stage 8 can inject all three protocol tiers (pulse/seam/full) into the correct positions within each phase | Stage 8 can inject protocols mechanically — every pulse point, seam check position, and checkpoint location is obvious from the build order and sandbox |

### Threshold and Failure Handling

- **Score ≥ 90:** Pass to Stage 8 automatically.
- **Score 70-89:** Flag concerns. Present to user: "Phase sequencing scored below 18 on [dimensions]. Token math shows [details]. Proceed or adjust?" If no human available, retry Stage 7 once. If retry still scores 70-89, proceed with warning flag.
- **Score < 70:** Do NOT proceed. Likely cause: spec is too large or complex for phase splitting at mechanism boundaries, or the wireframe/component information from Stage 6 was insufficient to create file sandboxes. Trigger escape hatch.

### What the Next Stage Expects

Stage 8 (Protocol Injection) receives the phases and injects verification checkpoints directly into the build orders. It expects each phase to have a clear file sandbox (for pattern verification) and a build order (for pulse/seam check insertion points). Stage 8 does NOT change the phase structure — it adds enforcement on top of Stage 7's framework. The combined output of Stages 7 + 8 forms the complete phase specification.

---

## Stage 8: Protocol Injection

### Purpose

Take the phases from Stage 7 and inject testing/verification checkpoints INTO them — pulse checks after every file, seam checks at connection points, full checkpoints at phase boundaries — transforming raw build phases into self-verifying containment units.

### Inputs

From `context_packet.stage_7`:

- `phases`: Phase list with file sandboxes and build orders

Protocol templates:
- Pulse check template (~per-file, lightweight)
- Seam check template (~at connection points, medium)
- Full checkpoint template (~end of phase, comprehensive)
- Violation decision tree template

### Outputs

Written to `context_packet.stage_8`:

- `instrumented_phases`: Array of enriched phase objects, each containing everything from Stage 7's phase PLUS:
  - `pulse_points`: Array of {after_file, checks} objects — one per file in build order
  - `seam_checks`: Array of {location, checks} objects — at connection points between mechanisms
  - `full_checkpoint`: Object with:
    - `pattern_verification`: File diff comparison instructions
    - `functional_checks`: Array of specific functional tests (compile, render, navigate)
    - `gate_condition`: Pass/fail criteria before next phase starts
  - `violation_handling`: The embedded decision tree (LOW/MEDIUM/HIGH/CRITICAL severity with actions)
  - `overhead_tokens`: Actual token count of injected protocol content for this phase
- `total_overhead_tokens`: Sum of all phases' overhead
- `budget_verified`: Boolean — all phases still fit within token budget after injection

### "Done When..." Criteria

1. Every phase in `instrumented_phases` has at least one `pulse_point` (there must be at least one file in each build order)
2. Every phase has at least one `seam_check` at a point where two mechanisms or components interface
3. Every phase has a `full_checkpoint` with `pattern_verification`, `functional_checks`, and `gate_condition` all populated
4. Every phase has a `violation_handling` decision tree with all four severity levels defined (LOW, MEDIUM, HIGH, CRITICAL) and an action for each
5. `budget_verified` is `true` — every phase's `estimated_total_tokens` (from Stage 7) plus `overhead_tokens` is ≤ 350,000
6. The protocols are EMBEDDED inline in the build order, not attached as a separate appendix — pulse checks appear after their corresponding file, seam checks appear at connection points, full checkpoint appears at the end

### Confidence Scoring

| Dimension | 0-5 | 6-10 | 11-15 | 16-20 |
|-----------|-----|------|-------|-------|
| Completeness | Multiple phases missing pulse points, seam checks, or full checkpoints; violation handling absent | All phases have full checkpoints but pulse and/or seam checks are missing for 2+ phases | All three protocol tiers present in every phase; violation handling complete; 1-2 pulse points have generic checks | Every file has a specific pulse check; every mechanism interface has a seam check; full checkpoint has both pattern verification and functional checks; violation tree covers all severities |
| Accuracy | Pulse checks reference files not in the build order; seam checks placed at non-connection points; functional checks test wrong functionality | Most checks are correctly placed; 2-3 seam checks are at questionable locations | Checks are correctly placed; pulse checks match their files; seam checks are at genuine connection points; functional checks test the right things | Every check is precisely placed and precisely defined; pulse checks verify the specific exports of each file; seam checks verify the exact import/dependency relationships; functional checks cover all new functionality in the phase |
| Consistency | Protocol instructions contradict the build order (e.g., "verify file X exists" when file X isn't in the phase) | Minor inconsistencies between protocol checks and sandbox rules | Protocols are consistent with sandboxes and build orders; violation thresholds are uniform across phases | Protocols perfectly reflect the sandbox rules and build orders; violation severity classifications are consistent across all phases; gate conditions align with next-phase dependencies |
| Specificity | Checks are generic ("verify the file works"); violation handling says "take appropriate action" | Checks name what to verify but not how; violation handling distinguishes severities but actions are vague | Checks specify exact commands or conditions (e.g., "npm run build succeeds", "exports loginUser function"); violation actions are specific per severity | Checks are machine-executable (exact commands, exact function names, exact import paths); violation actions specify exact git commands for rollback; gate conditions are binary pass/fail with no interpretation needed |
| Handoff Readiness | Stage 9 cannot set up verification because the protocols are missing or malformed | Stage 9 can set up verification but would need to define some checks that Stage 8 missed | Stage 9 can configure the verifier agent using the embedded protocols without additional work | Stage 9 can mechanically translate protocols into verifier agent instructions — every check, every threshold, every rollback command is explicit and ready for agent B to execute |

### Threshold and Failure Handling

- **Score ≥ 90:** Pass to Stage 9 automatically.
- **Score 70-89:** Flag concerns. Present: "Protocol injection scored below 18 on [dimensions]. Some phases may have weak verification. Proceed or tighten?" If no human available, retry Stage 8 once. If retry still scores 70-89, proceed with warning flag.
- **Score < 70:** Do NOT proceed. Likely cause: phase structure from Stage 7 was too incomplete to inject protocols into, or token budget is exceeded after injection. Trigger escape hatch. Consider re-splitting phases in Stage 7.

### What the Next Stage Expects

Stage 9 (Verification Agent Setup) uses the instrumented phases to configure the independent verifier agent. It expects the violation decision tree, the pattern verification commands, and the functional checks to be fully defined so that Agent B (the verifier) knows exactly what to check, what severity to assign, and what rollback action to take. Stage 9 does NOT redefine verification — it defines WHO does the verification and what happens after violations are detected.

---

## Stage 9: Verification Agent Setup

### Purpose

Configure the independent verification agent (Agent B) that audits the builder agent's work after each phase — defining its role, instructions, decision authority, and the auto-retry logic that handles failures, ensuring the checker is NEVER the same agent as the builder.

### Inputs

From `context_packet.stage_8`:

- `instrumented_phases`: Phases with embedded protocols, violation handling, and gate conditions

From `context_packet.stage_7`:

- `phases`: File sandboxes and build orders

### Outputs

Written to `context_packet.stage_9`:

- `verifier_config`: Object containing:
  - `approach`: "automated" (bash/CLI — separate Agent B) or "manual" (Phase N+1 checks Phase N)
  - `verifier_prompt`: The complete prompt for Agent B (automated) or the validation preamble for Phase N+1 (manual)
  - `verifier_inputs`: What the verifier receives per phase (allowed file list, git diff output, functional check results, violation decision tree)
  - `verifier_token_budget`: Estimated tokens per verification (~10K for automated)
  - `retry_config`: Object with:
    - `max_retries`: Integer (default: 2 — two strikes then human)
    - `retry_action`: What happens on retry (git reset to baseline, fresh agent)
    - `escalation_action`: What happens when retries exhausted (stop for human review)
  - `persistent_verifier`: Boolean — whether Agent B persists across phases to accumulate pattern knowledge
- `checker_builder_consistency`: Boolean — verified that verifier instructions do not contradict builder instructions from Stage 8
- `verification_overhead_total`: Total estimated tokens for all verification across all phases

### "Done When..." Criteria

1. `verifier_config.approach` is set to "automated" or "manual" with the corresponding prompt fully written
2. `verifier_prompt` is a complete, self-contained prompt that a fresh agent can execute without additional context — includes what to check, how to classify violations, and what actions to take at each severity level
3. `verifier_inputs` lists exactly what the verifier receives — no more (no access to builder's reasoning or conversation), no less (file list, diff, check results are all present)
4. `retry_config` is fully defined with `max_retries`, `retry_action`, and `escalation_action`
5. `checker_builder_consistency` is `true` — verified by cross-referencing Stage 8's violation thresholds with Stage 9's verifier instructions; no case where the builder is told "this is acceptable" but the verifier is told "this is a violation" (or vice versa)
6. For the "manual" approach: the validation preamble for Phase N+1 references the specific checks from Phase N's full checkpoint — not generic "validate the previous phase"

### Confidence Scoring

| Dimension | 0-5 | 6-10 | 11-15 | 16-20 |
|-----------|-----|------|-------|-------|
| Completeness | Verifier config is empty or missing key fields (no prompt, no retry config) | Config exists but verifier_prompt is incomplete or retry logic is undefined | Config is complete; verifier_prompt covers all check types; retry logic defined; 1-2 edge cases in violation handling not addressed | Config is comprehensive; verifier_prompt handles all violation severities with specific actions; retry logic covers all outcomes; persistent verifier option configured; both automated and manual paths documented |
| Accuracy | Verifier instructions contradict builder rules (e.g., verifier rejects files the builder was told to create) | Minor contradictions in 1-2 areas; verifier_token_budget estimate is significantly off | No contradictions with builder rules; token budget estimate is within ±30%; retry logic is sound | Zero contradictions; token budget is within ±15%; retry logic handles every edge case (clean pass, minor drift, major drift, critical violation, two-strike escalation) correctly |
| Consistency | Verifier severity classifications don't match Stage 8's violation decision tree | Most severity levels align but 1-2 classifications differ between Stage 8 and Stage 9 | All severity levels match between builder and verifier; auto-retry actions are consistent with violation types | Perfect alignment: Stage 8's violation tree and Stage 9's verifier instructions use identical severity levels, identical thresholds, and compatible actions; cross-reference verified for every severity level |
| Specificity | Verifier prompt says "check the phase" without specifying what to check | Verifier prompt lists check types (file diff, build, lint) but doesn't specify expected outputs | Verifier prompt specifies exact commands to run and exact outputs to check against; severity thresholds are numeric or pattern-based | Verifier prompt includes exact git commands (git diff --name-only $SNAPSHOT), exact build commands (npm run build), exact comparison logic (diff output vs allowed list), and exact decision tree with specific actions per severity |
| Handoff Readiness | Stage 10 cannot produce a build.sh because verification flow is undefined | Stage 10 can produce basic phase files but build.sh would lack verification logic | Stage 10 can produce complete output package; build.sh includes verification steps; phase files include embedded checks | Stage 10 can mechanically render the output package — build.sh has complete verification, retry, and rollback logic; phase files have all protocols embedded; manual path has complete preambles; both consumption paths are ready |

### Threshold and Failure Handling

- **Score ≥ 90:** Pass to Stage 10 automatically.
- **Score 70-89:** Flag concerns. Present: "Verification setup scored below 18 on [dimensions]. The verifier may have gaps in [specific areas]. Proceed or tighten?" If no human available, retry Stage 9 once. If retry still scores 70-89, proceed with warning flag.
- **Score < 70:** Do NOT proceed. Likely cause: Stage 8's protocols were too vague for Stage 9 to build concrete verifier instructions, or builder/verifier rules are fundamentally inconsistent. Trigger escape hatch. May need to revise Stage 8.

### What the Next Stage Expects

Stage 10 (Output Generator) renders the final deliverable package. It uses Stage 9's verifier config to generate the build.sh (with verification, retry, and rollback logic for automated path) and to embed the validation preambles into phase files (for manual path). It expects the verifier prompt to be copy-paste ready — Stage 10 does not write new verification logic, it serializes what Stage 9 defined.

---

## Stage 10: Output Generator

### Purpose

Render all preceding work (Stages 0-9) into a deliverable package of copy-paste-ready files — phase documents, build script, CLAUDE.md, and BUILD_RULES.md — that a builder agent or human developer can execute without asking any questions. This stage is pure serialization, not design. Zero open questions remain.

### Inputs

Full context packet from all prior stages:

- `stage_0.platform_profile`: Stack context
- `stage_3.concept_and_context`: Product concept (for CLAUDE.md context sections)
- `stage_4.mechanisms`: Mechanism inventory
- `stage_5.mechanism_blueprints`: Wall/Door/Room classifications
- `stage_6.sub_6a` + `sub_6b` + `sub_6c`: Page layouts and visual design
- `stage_7.phases`: Phase structure with sandboxes and build orders
- `stage_8.instrumented_phases`: Phases with embedded protocols
- `stage_9.verifier_config`: Verification agent setup

Martin's distilled build rules (for CLAUDE.md and BUILD_RULES.md generation)

### Outputs

Written to `context_packet.stage_10` and rendered as files:

- `output_package`: Object containing:
  - `phase_files`: Array of complete phase document contents (one per phase), each copy-paste ready with:
    - Build rules preamble (~8K tokens)
    - File sandbox declaration (~2K tokens)
    - Build order with pulse points (~3K tokens)
    - Seam check definitions (~2K tokens)
    - Feature requirements and implementation instructions
    - Pattern references (file:line references for existing patterns)
    - Violation handling instructions (~2K tokens)
    - Full checkpoint at end (~5K tokens)
    - Gate condition
  - `build_script`: Complete build.sh content with snapshot/rollback, verification, retry logic
  - `claude_md`: CLAUDE.md content (quick-reference guardrails, <500 lines)
  - `build_rules_md`: BUILD_RULES.md content (detailed reference playbook)
  - `readme_md`: README.md content (what was built, how to continue)
- `platform_wrapper`: Platform-specific execution instructions for the user's chosen platform
- `internal_consistency_verified`: Boolean — every cross-reference in every file resolves to something that exists
- `total_output_tokens`: Token count of the complete output package

### "Done When..." Criteria

1. `phase_files` array has exactly `phase_count` entries (from Stage 7), each containing all 9 required sections (preamble, sandbox, build order, seam checks, requirements, pattern references, violation handling, full checkpoint, gate condition)
2. Every phase file is self-contained — it can be copy-pasted into a fresh agent context and executed without referencing other files (except READ-ONLY references which are in the codebase)
3. `build_script` contains snapshot logic (git rev-parse HEAD), post-build validation (npm run build, npm run lint), forbidden file detection (git diff against sandbox), and retry logic (two-strike rule)
4. `build_script` uses `&&` for phase chaining (not `;`) — failure in one phase stops the pipeline
5. `claude_md` is under 500 lines and contains: architecture principles, modification rules, testing protocol, file structure map, and pointers to BUILD_RULES.md sections
6. `internal_consistency_verified` is `true`: every file path in a sandbox exists in a build order somewhere; every mechanism referenced in a phase file exists in Stage 4; every import/reference pattern points to a file that another phase creates
7. Martin's build rules appear through architecture decisions and preambles — there is no standalone "Martin's Rules" section (they are distributed, not centralized)
8. `platform_wrapper` is set for the user's chosen platform with appropriate execution commands

### Confidence Scoring

| Dimension | 0-5 | 6-10 | 11-15 | 16-20 |
|-----------|-----|------|-------|-------|
| Completeness | Phase files missing; build.sh absent; CLAUDE.md not generated | Phase files exist but 2+ are missing required sections (no sandbox, no checkpoint); build.sh is skeletal | All phase files have all 9 sections; build.sh has core logic; CLAUDE.md and BUILD_RULES.md present; 1-2 phase files have thin requirement sections | Every file in the output package is complete; every phase file has comprehensive requirements with pattern references; build.sh has full verification and retry logic; CLAUDE.md + BUILD_RULES.md cover all relevant domains |
| Accuracy | Phase files contain instructions that reference mechanisms, files, or patterns not defined anywhere in the pipeline | Most instructions are accurate but 3+ references point to nonexistent files or misnamed mechanisms | All references resolve correctly; build.sh commands are valid for the chosen platform; CLAUDE.md rules accurately reflect the project architecture | Every reference resolves; build.sh is tested-ready; CLAUDE.md and BUILD_RULES.md rules are precise, actionable, and correct for the chosen stack; zero dangling references |
| Consistency | Phase files contradict each other (Phase 2 modifies a file Phase 1's sandbox forbids); build.sh commands conflict with phase instructions | Minor inconsistencies between phase files; build.sh mostly aligns with phase verification rules | Phase files are internally consistent; build.sh verification matches phase sandbox rules; CLAUDE.md doesn't contradict BUILD_RULES.md | Perfect consistency across all output files; sandbox rules are respected across phases; build.sh verification exactly mirrors the phase checkpoints; CLAUDE.md and BUILD_RULES.md are complementary without overlap |
| Specificity | Phase requirements say "build the auth system" without specifying components, patterns, or expected outputs | Phase requirements name components but lack implementation detail; build.sh uses placeholder paths | Phase requirements specify components with file paths, import patterns, and expected behavior; build.sh uses real paths and commands | Phase requirements are detailed enough for a coding agent to build without asking questions — exact file paths, exact exports, exact patterns to follow, exact validation criteria; build.sh is production-ready |
| Handoff Readiness | A coding agent would ask "what am I building?" before starting Phase 1 | A coding agent could start but would need clarification on 3+ implementation details within Phase 1 | A coding agent can complete Phase 1 asking at most 1 clarifying question; subsequent phases are equally clear | A coding agent can execute the entire build — all phases, in order — without asking a single question. The output package is the complete instruction set. |

### Threshold and Failure Handling

- **Score ≥ 90:** Output package is ready for delivery. The pipeline is complete.
- **Score 70-89:** Flag concerns. Present to user: "The output package scored below 18 on [dimensions]. Specific issues: [list files with problems]. Should I revise or deliver as-is?" If no human available, retry Stage 10 once. If retry still scores 70-89, deliver with a warning note documenting the weak areas.
- **Score < 70:** Do NOT deliver. The output package has structural issues that would cause build failures. Trigger escape hatch. Most likely cause: upstream stages produced insufficient or inconsistent data. Log which phases have issues and trace back to the originating stage.

### What the Final Consumer Expects

The final consumer is either a coding agent (automated path) or a human developer (manual path). They expect:

- **Coding agent**: A Phase 1 file that, when provided as a prompt, produces a working foundation (auth, core UI, database setup) without requiring any interpretation. The build.sh chains phases together with verification between each — the agent never operates without guardrails.
- **Human developer**: A package they can read through to understand the full architecture, then either run build.sh for automation or copy-paste individual phase files. The README.md explains the project and how to continue development after the initial build.
- **Both**: CLAUDE.md persists in the repo forever. Any future agent interaction — even a quick "fix this button" — reads CLAUDE.md and knows the project's rules. The system's quality extends beyond the initial build into the ongoing life of the codebase.

---

## Input/Output Alignment Verification

This section confirms that each stage's outputs match the next stage's expected inputs.

| From Stage | Output Field | To Stage | Expected Input | Aligned? |
|------------|-------------|----------|---------------|----------|
| 0 | `platform_profile` | 2, 4, 10 | Stack context for gap questions, mechanism tagging, output rendering | ✅ |
| 1 | `raw_input`, `word_count` | 2 | Raw description + length for question calibration | ✅ |
| 2 | `complete_raw_material`, `matched_archetype`, `mechanism_map` | 3 | Combined raw info, app type, category classifications | ✅ |
| 3 | `concept_document` | 4 | Structured concept for mechanism extraction | ✅ |
| 4 | `mechanisms`, `dual_design_flags` | 5 | Mechanism list with approaches for scaffolding | ✅ |
| 5 | `mechanism_blueprints` | 6 | Wall/Door/Room classifications for page layout | ✅ |
| 6 | `sub_6a`, `sub_6b`, `sub_6c` | 7 | Page layouts + style for phase splitting | ✅ |
| 7 | `phases` | 8 | Phase structure with sandboxes/build orders for protocol injection | ✅ |
| 8 | `instrumented_phases` | 9 | Protocol-injected phases for verifier setup | ✅ |
| 9 | `verifier_config` | 10 | Verification setup for output rendering | ✅ |
| 10 | `output_package` | Consumer | Deliverable files for coding agent or human developer | ✅ |
