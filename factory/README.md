# The App Factory - Car Wash Pipeline

## What Is This?

Think of a car wash. You drive in dirty, you come out clean and shiny. This is the same thing, but for app ideas.

You dump your raw ideas, rants, voice transcripts, napkin sketches, half-baked prompts -- whatever you have -- into the **inbox**. The system reads everything, figures out what you're actually trying to build, and routes each piece to the right stage of the pipeline. Ideas go in one end, polished apps come out the other.

## How It Works

### 1. Dump Everything in the Inbox

Drop any file into `factory/inbox/`. Text files, markdown, whatever. Don't organize it. Don't clean it up. Just dump it in. The messier the better -- that's what the engine is for.

### 2. Run the Intake Engine

```bash
# See what the engine recommends (dry run)
python factory/engine/intake.py

# Actually mount ideas to pipeline stages
python factory/engine/intake.py --auto-mount
```

The engine reads your inbox, reads what's already in the pipeline, and figures out:
- What's the core concept in each idea?
- Which pipeline stage does it belong to?
- Does it overlap with something already there?
- Should it be merged, split, or mounted as-is?

### 3. Ideas Flow Through the Pipeline

Once mounted, ideas move through 8 stages -- like stations in a car wash:

| Stage | What Happens |
|-------|-------------|
| **01 - Idea Intake** | Raw capture. Voice-to-text, rant extraction, brain dumps. |
| **02 - PRD Generation** | Turn ideas into a real product spec. |
| **03 - Architecture** | System design, tech stack, file structure. |
| **04 - Code Generation** | First pass coding. Scaffold and build. |
| **05 - Security Review** | Harden it. Find vulnerabilities. |
| **06 - Testing & QA** | Unit tests, integration tests, linting. |
| **07 - Computer Use Testing** | Browser testing, visual verification, manual flows. |
| **08 - Polish & Delivery** | Final polish, docs, user manual, handoff. |

## Directory Layout

```
factory/
  engine/          ← The brains - intake, sorting, mounting
  pipeline/        ← The 8 car wash stations
  inbox/           ← Drop zone - dump raw ideas here
  mounted/         ← Processed ideas after the engine sorts them
```

## Key Commands

```bash
# Process inbox and get recommendations
python factory/engine/intake.py

# Auto-mount ideas to pipeline stages
python factory/engine/intake.py --auto-mount

# Check for duplicates and gaps
python factory/engine/sorter.py

# Mount a specific idea to a stage
python factory/engine/mounter.py --idea "my_idea.md" --stage 03-architecture
```

## The Philosophy

- **No organizing required.** Dump everything, the engine thinks for you.
- **Overlap is OK.** The engine finds duplicates and merges the good parts.
- **Gaps are visible.** You can see which pipeline stages are empty and need attention.
- **Everything is tracked.** Each stage has a manifest showing what's mounted and why.
