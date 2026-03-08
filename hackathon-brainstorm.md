# GitLab AI Hackathon Brainstorm

> Hackathon: https://gitlab.devpost.com/
> Deadline: March 25, 2026 @ 2:00pm EDT (17 days)
> Prize Pool: $65,000 USD

---

## Hackathon Requirements Summary

- **Must build on GitLab Duo Agent Platform** (custom agents or flows)
- **Must be an AGENT** (reacts to triggers, takes action) — NOT a chatbot
- **Deliverables:** Public GitLab repo + text description + 3-min YouTube demo
- **Judging:** Tech implementation, Design/Usability, Impact, Originality
- **Key prizes:**
  - Grand Prize: $15,000
  - Most Technically Impressive: $5,000
  - Most Impactful: $5,000
  - Easiest to Use: $5,000
  - GitLab & Anthropic Grand Prize: $10,000
  - GitLab & Anthropic Runner-Up: $3,500
  - GitLab & Google Grand Prize: $10,000

---

## Existing Ideas → Hackathon Fit Analysis

### Idea 1: Rant-to-Spec Engine → GitLab Issue Agent ⭐ TOP PICK

**Source:** `handoffs/rant_to_spec_engine.md`

**GitLab Agent Version:**
- Trigger: Issue created with `rant` or `idea` label
- Agent processes raw issue text through 5-stage pipeline
- Output: Structured spec in issue, child issues for features, milestone, dependencies, labels
- Deep decisions become discussion issues for team input

**Prize targets:** Anthropic Grand ($10K), Grand Prize ($15K), Easiest to Use ($5K)

**Effort:** ~1 week (engine design already complete)

**Demo hook:** Brain dump → label → 15+ structured issues appear. Visual. Memorable.

---

### Idea 2: Upstream Feature Watcher → GitLab MR Flow

**Source:** `handoffs/upstream-feature-watcher.md`

**GitLab Flow Version:**
- Trigger: Scheduled pipeline (every N hours)
- Agent 1: Monitor upstream for merged MRs
- Agent 2: Analyze each MR against your fork (divergence, relevance, effort)
- Agent 3: Auto-create adapted MRs for approved features

**Prize targets:** Most Technically Impressive ($5K), Grand Prize ($15K)

**Effort:** ~1.5 weeks

**Demo hook:** Upstream commits → analysis cards → approve → adapted MR appears

---

### Idea 3: Build Intelligence → Pipeline Learning Agent

**Source:** `.claude/handoffs/build-intelligence-handoff.md`

**GitLab Agent Version:**
- Trigger: Pipeline failure or MR creation
- On failure: Logs pattern, root cause, fix to knowledge base
- On MR: Scans diff against known failure patterns, comments warnings
- Gets smarter over time with measurable metrics

**Prize targets:** Most Impactful ($5K), Pipeline Observability (aspirational journey)

**Effort:** ~1.5 weeks

**Demo hook:** Show agent learning from failures and preventing them in future MRs

---

### Idea 4: PRD Quality Scorer → Spec Review Agent

**Source:** `.claude/handoffs/build-intelligence-handoff.md` (Feature 2)

**GitLab Agent Version:**
- Trigger: MR containing spec/PRD files
- Agent scores the spec on completeness, clarity, buildability
- Comments with specific improvements and a quality score
- Can also trigger on issue descriptions

**Prize targets:** Easiest to Use ($5K)

**Effort:** ~3-4 days (simplest to build)

**Demo hook:** Push a mediocre spec → agent comments with score + actionable fixes

---

## Recommendation: Rant-to-Spec Issue Agent

**Why this one wins:**

1. **Fastest path** — engine architecture already fully designed
2. **Best 3-min demo** — the before/after is visually stunning
3. **Most original** — nobody else is doing rant-to-spec on GitLab
4. **Anthropic prize eligible** — $10K + $3.5K for using Claude
5. **"Non-coder" narrative** — differentiator, not a weakness
6. **Easiest to Use** — add a label, that's it

**What to strip out (keep it focused):**
- No UI needed (it's all GitLab-native)
- No save/resume (single-pass for hackathon)
- Simplified priority profiles (2-3 presets, not the full weighter)
- No "Developer's Choice" complexity in v1 — just make good auto-decisions

**Build timeline:**
- Days 1-3: Learn GitLab Duo Agent Platform, set up project
- Days 4-7: Build core engine (parse → classify → create issues)
- Days 8-10: Polish (dependencies, labels, milestone creation)
- Days 11-13: Testing, edge cases, documentation
- Days 14-15: Record demo video, write description
- Days 16-17: Buffer

---

## Presentation Strategy

The stuff being internal/process-oriented is NOT a problem when repackaged:

1. **Standalone GitLab agent** — not part of AutoForge, anyone can install it
2. **Demo shows GitLab UI** — issues appearing, labels, milestones — inherently visual
3. **Public repo is the deliverable** — docs, license, install instructions
4. **Story angle:** "I don't code. I built this with AI. It turns anyone's brain dump into a buildable project plan."
