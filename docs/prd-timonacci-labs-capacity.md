# Timonacci Labs: Capacity Management & Anti-Clog Logic

> **Status:** Standalone section -- will be merged into `prd-timonacci-labs.md` when the main PRD is created.

---

## CRITICAL: Capacity Management -- Don't Clog the System

### The Problem

Every output destination has limits. If the Diverter just keeps creating skills, reference files, prompts, and tools without restraint, it will:
- Create 200 skills when Claude can only effectively trigger from ~30-40
- Stuff skill descriptions past character limits (YAML descriptions have a sweet spot)
- Add 50 reference files to one skill when the context window can only handle 5-10
- Generate duplicate prompts that overlap with existing ones
- Create tools that duplicate existing tool chamber capabilities
- Flood the PRD Shredder queue with low-priority items

### The Solution: Per-Destination Capacity Limits + Self-Optimization

Each destination the Diverter routes to gets **hard limits, soft limits, and smart consolidation logic.**

#### Skills (.claude/skills/)
- **Hard limit:** 40 active skills max (beyond this, activation accuracy drops because descriptions compete)
- **Soft limit:** 25 skills (warning zone -- start consolidating)
- **Description limit:** ~200 chars for YAML description (longer = worse triggering)
- **Self-optimization:**
  - When approaching soft limit, AI analyzes: "Can any 2-3 skills be MERGED into one broader skill?"
  - Track activation rates -- skills that never trigger get flagged for removal or merger
  - Skills with <10% activation after 2 weeks -> auto-archive
  - Before creating a new skill, check: "Does an existing skill already cover 80%+ of this?" -> enhance existing skill instead of creating new one

#### Reference Files (skill context)
- **Hard limit:** 8 reference files per skill (context window budget)
- **Total size limit:** ~50KB per skill's reference files combined
- **Self-optimization:**
  - When a skill hits 8 files, AI must MERGE the least-used two before adding a new one
  - Track which reference files actually get used in outputs -- unused files get flagged
  - Consolidate overlapping reference files: "tone-of-voice.md" + "brand-voice.md" -> merge into one

#### Prompts (prompt library)
- **Hard limit:** 100 prompts per category
- **Dedup check:** Before creating a new prompt, semantic similarity check against existing prompts
  - >85% similar -> don't create, enhance the existing one
  - 60-85% similar -> flag for human review: "This is similar to prompt X -- merge or keep both?"
  - <60% similar -> create new prompt
- **Self-optimization:**
  - Track prompt usage frequency -- unused prompts get archived after 30 days
  - Merge prompts that always get used together

#### Tool Chamber Connectors
- **Hard limit:** Based on the component registry -- don't create duplicate connectors
- **Dedup check:** Before building a new connector, check: "Does the component registry already have something that handles this?"
- **Self-optimization:**
  - Track tool usage -- connectors that never get selected by the AI router get flagged
  - Consolidate tools that do similar things

#### PRD Shredder Queue
- **Hard limit:** 10 items in queue max (prevent overwhelming overnight builds)
- **Priority scoring:** Each PRD gets a priority score based on:
  - How many other things it unblocks
  - How many truth documents reference it
  - How recently the topic was ingested
- **Self-optimization:**
  - Low-priority PRDs that sit in queue for 7+ days get auto-archived
  - PRDs that fail to build twice get removed and flagged for human review

#### Truth Documents
- **Size limit:** 5,000 words max per truth document (beyond this, it's too long for effective use)
- **When approaching limit:** AI must DISTILL -- cut redundancies, merge similar points, tighten language
- **Version limit:** Keep last 5 versions only (save disk space)
- **Self-optimization:**
  - Track which sections of truth docs actually get used downstream
  - Sections never referenced in skills/prompts/tools -> candidates for trimming
  - Periodic "spring cleaning" pass: "Can this 4,500 word doc be tightened to 3,000 without losing value?"

### The Capacity Dashboard

A simple view showing health of each destination:

```
SYSTEM CAPACITY
===============================================
Skills:          23/40  ||||||||||||........  58%  [Healthy]
Ref Files (avg): 4.2/8  |||||||||..........  53%  [Healthy]
Prompts:         67/100 |||||||||||||......  67%  [Watch]
Tool Connectors: 6/15   |||||||............  40%  [Healthy]
Shredder Queue:  3/10   ||||||.............  30%  [Healthy]
Truth Docs:      12     (no hard limit)      -   [Healthy]

ACTIONS NEEDED:
- 2 skills have <10% activation -- consider archiving
- 3 reference files unused in 14 days -- review
- Prompt category "marketing" at 89/100 -- consolidation recommended
```

### The Core Rule: ENHANCE BEFORE CREATE

The #1 anti-clog rule across ALL destinations:

**Before creating anything new, ALWAYS check: can we make something existing better instead?**

- New skill idea? -> Check if existing skill can absorb it
- New reference file? -> Check if existing file can be extended
- New prompt? -> Check if existing prompt covers it
- New tool? -> Check if existing tool handles this case
- New truth doc? -> Check if an existing topic is close enough to merge

This is the difference between a hoarder and an optimizer. The system should get SHARPER, not BIGGER. Quality over quantity at every level.

### Self-Optimization Loops (Capacity-Specific)

Add these binary assertions to the overnight Karpathy loops:

**Skills capacity loop:**
- "Total active skills < 40" -> binary
- "No skill has < 10% activation rate" -> binary
- "No skill description exceeds 200 chars" -> binary
- "No two skills have > 80% description overlap" -> binary

**Reference files capacity loop:**
- "No skill has > 8 reference files" -> binary
- "No skill's reference files total > 50KB" -> binary
- "No reference file has been unused for > 14 days" -> binary

**Truth doc capacity loop:**
- "No truth doc exceeds 5,000 words" -> binary
- "All truth docs have been used in at least one downstream output" -> binary
- "No two truth docs have > 70% topic overlap" -> binary
