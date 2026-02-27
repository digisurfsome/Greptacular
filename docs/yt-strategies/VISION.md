# YT Strategy Lab — The Actual Vision

> **Every agent must read this before building anything.** This is the WHY behind the system. Without it, you'll build a YouTube-to-agency tool. That's not what this is.

---

## What This Actually Is

YT Strategy Lab is a **mini-app factory**. Each YouTube video that enters the system becomes its own small, self-contained application — a repeatable template with steps, prompts, and (when needed) automated tooling.

It is NOT just an AI ad agency builder. The first video we processed happened to be about building an automated ad agency for car dealerships. That video needed computer-use automation. But the next video might be about building a content pipeline, or a lead gen system, or a SaaS onboarding flow — and those might need completely different tools, or no automation tools at all.

**The system is a template maker that turns any YouTube video into a reusable mini-app.**

---

## How It Works (The Pipeline)

```
YouTube Video
    ↓
Ingest (transcript, metadata, screenshots)
    ↓
AI Processing (extract strategy, identify steps)
    ↓
Template Creation (structured steps + prompts + tool requirements)
    ↓
Mini-App (a self-contained, repeatable workflow you can run again and again)
```

Each mini-app is a project inside YT Strategy Lab. Each project is its own thing — its own steps, its own prompts, its own tool requirements.

---

## The Two Modes

### Mode 1: Simple Step-by-Step
The video walks through a process. The system extracts the steps, organizes them, and gives you a clean repeatable checklist with prompts you can use. No automation needed — just organized knowledge.

*Example: "How I grew my newsletter to 10K subscribers" → 8 steps with prompts and expected outputs.*

### Mode 2: Full Automation Template
The video demonstrates a process that CAN be automated. The system extracts the steps AND identifies which tools are needed to execute them autonomously.

*Example: "How I built an AI ad agency for car dealerships" → 9 steps, each with computer-use automation prompts, model selection, and role assignments. The agent literally does the work — researches competitors, creates ad copy, finds prospects, sends outreach.*

**Both modes produce the same thing: a reusable project template.** The difference is just how much tooling is involved.

---

## The Tool Bank (Why It Grows Over Time)

The first video (automated ad agency) needed computer-use as its tool. So we built computer-use support. The next video might need:
- API integrations (no browser needed, just API calls)
- File generation (PDFs, spreadsheets, documents)
- Data scraping (structured extraction from websites)
- Email/messaging automation
- Image/video generation
- Something we haven't thought of yet

Each new tool type gets built once and then becomes available to ALL future templates. Over time, the tool bank fills up. Eventually, every new video that comes in will map to tools that already exist — no new tooling needed, just a new template.

```
Video 1  → needs Computer Use     → build Computer Use tool    ✓
Video 2  → needs API Integration  → build API Integration tool ✓
Video 3  → needs File Generation  → build File Generation tool ✓
Video 4  → needs Computer Use     → already have it            ✓
Video 5  → needs API + Files      → already have both          ✓
...
Video 50 → needs nothing new      → all tools exist            ✓
```

---

## Each Project Is a Mini-App

Think of each processed video as creating a small standalone application within the larger system:

- It has its own **steps** (the workflow)
- It has its own **prompts** (the AI instructions per step)
- It has its own **tool requirements** (what it needs to execute)
- It has its own **data** (outputs, captures, results)
- It's **repeatable** — run it for a different niche, different client, different market

The automated ad agency template? Run it for car dealerships, then run it for dentists, then for real estate agents. Same template, different inputs. Each run produces real results.

---

## The Breakaway Potential

Here's the kicker: if any mini-app turns out to be really good — like the automated ad agency becomes a killer workflow — you can **pull it out** and make it a standalone product. It's already structured as its own application with steps, prompts, and tooling. Extracting it into its own dedicated software is just a matter of giving it its own UI and removing the YT Lab wrapper.

The ad agency mini-app could have 10-20 different automated processes added to it over time (competitor research, ad creation, outreach, reporting, client onboarding, etc.). Each of those is its own mini-app within the mini-app. And any of THOSE could be pulled out as standalone tools if they're good enough.

---

## What This Means for Building

When you're building features for YT Strategy Lab, keep this in mind:

1. **Don't hardcode for one use case.** The ad agency was the first video. It won't be the last. Build for ANY video, any workflow, any tool type.

2. **The template system is the core.** Steps + prompts + tool slots = the universal format. Every video maps to this structure regardless of what it's about.

3. **Tools are pluggable.** Computer-use is ONE tool. The architecture should support adding new tool types without rewriting the template system.

4. **Projects are independent.** Each video creates its own project. Projects don't share data. They might share tools from the tool bank, but their workflows are separate.

5. **Repeatability is the whole point.** A template that only works once is useless. Every project must be runnable with different inputs (different niche, different client, different market).

---

## TL;DR

**YT Strategy Lab = YouTube video → reusable mini-app template.**

Some templates are simple checklists. Some are fully automated workflows. All of them are repeatable. The tool bank grows over time. The best mini-apps can become standalone products. It's an app factory, not a single-purpose tool.
