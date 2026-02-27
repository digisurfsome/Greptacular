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

## Nested Sub-Projects (Templates Have Children)

A template isn't always a dead end. Some templates are **parent systems** that can hold 10, 20, or more sub-projects inside them — each following the same pattern but doing a different task.

**Example — The Automated Agency template:**
The original video built one automation: car dealership Facebook ads. But that same agency framework could automate dozens of different processes — real estate lead gen, restaurant review management, dental practice outreach, etc. Each of those is a sub-project nested inside the agency template, using the same tool (computer use) and the same structural pattern, just pointed at a different task.

**Example — The Claude Code Automation template:**
A video shows someone using Claude Code to build one-off automations (like running 50 ad variations to find audience avatars). Right now that person rebuilds the workflow from scratch every time. With our system, the base template captures the pattern, and each new automation task (audience discovery, landing page generation, competitor analysis) becomes a sub-project. Same CLI tool, same structural approach, different task each time.

```
Template: Automated Agency (computer use)
├── Sub-project: Car Dealership Facebook Ads
├── Sub-project: Real Estate Lead Gen
├── Sub-project: Restaurant Review Outreach
└── Sub-project: [next idea goes here]

Template: Claude Code Automations (CLI)
├── Sub-project: Audience Avatar Discovery (50 ad variations)
├── Sub-project: Landing Page A/B Generator
├── Sub-project: Competitor Analysis Pipeline
└── Sub-project: [next idea goes here]
```

The file system is nested — the parent template is the root, sub-projects live inside it. Each sub-project is its own mini-app but inherits the parent's tool type and structural pattern.

**The breakaway signal:** When a template accumulates enough successful sub-projects (10-20+), that's a strong indicator it should become its own standalone product. At that point you pull it out and give it its own dedicated UI.

---

## Breakaway Architecture (The Real Product Strategy)

> **YT Strategy Lab is the factory. The breakaway apps are the products.** This section is foundational — every architectural decision must support easy extraction. If a project can't cleanly leave the nest, we built it wrong.

### Why This Matters

YT Strategy Lab itself probably never gets sold. What gets sold are the 10+ standalone apps that grow out of it. The automated ad agency becomes its own SaaS. The audience avatar tool becomes its own product. The content pipeline becomes its own thing. Each of those is a business. So the architecture must treat breakaway as a **first-class feature**, not an afterthought.

### The Strip Mall Principle

Think of YT Lab as a strip mall. Each store (project) has its own walls, its own plumbing, its own electrical. The strip mall provides the shared parking lot and the roof. When a store gets successful enough, you pick it up and put it on its own lot — you don't have to rewire anything because it was already self-contained.

**This means every project must be built as if it's ALREADY a standalone app that just happens to live inside YT Lab.**

### Structural Rules for Breakaway-Ready Projects

#### Rule 1: Self-Contained Project Folders

Every project lives in ONE folder with EVERYTHING it needs. Nothing scattered across the main app.

```
projects/
├── automated-agency/              ← one project = one folder
│   ├── manifest.json              ← the blueprint (see Rule 2)
│   ├── steps/                     ← workflow definitions
│   │   ├── 01-style-sheet.json
│   │   ├── 02-research.json
│   │   └── 03-ad-creation.json
│   ├── prompts/                   ← AI prompts per step
│   ├── config/                    ← project-specific settings
│   ├── data/                      ← outputs, captures, results
│   ├── sub-projects/              ← nested child projects
│   │   ├── car-dealerships/
│   │   ├── real-estate/
│   │   └── dentists/
│   └── README.md                  ← human-readable description
```

**The test:** Can you zip this folder, hand it to someone, and they understand what the project does? If yes, it's self-contained. If no, something leaked outside the folder.

#### Rule 2: The Manifest File

Every project has a `manifest.json` at its root. This is the single source of truth — the blueprint an export tool reads to know exactly what to grab.

```json
{
  "name": "Automated Ad Agency",
  "slug": "automated-agency",
  "description": "End-to-end automation for creating and deploying social media ads for local businesses",
  "version": "1.0.0",
  "source_video": "https://youtube.com/watch?v=...",
  "mode": "full-automation",
  "tools_required": ["computer-use"],
  "steps_count": 9,
  "has_sub_projects": true,
  "sub_project_count": 3,
  "breakaway_ready": true,
  "created_at": "2026-02-27",
  "tags": ["ads", "agency", "facebook", "automation"]
}
```

When you break away, the export function reads this manifest and knows: grab this folder, grab the `computer-use` tool module, grab the core runtime. Done.

#### Rule 3: Tools Are Separate, Pluggable Modules

Tools live in their own directory, completely independent of any project. A project REFERENCES a tool — it never contains it inline.

```
tools/
├── computer-use/          ← one tool = one module
│   ├── index.js           ← entry point
│   ├── config.json        ← tool configuration
│   └── README.md          ← what this tool does
├── cli-automation/
├── api-integration/
└── file-generation/
```

A project says `"tools_required": ["computer-use"]`. It doesn't import computer-use code directly — it goes through a tool registry. When you break away, the export copies the tool module into the new app. Like unplugging a cable and plugging it into a new building.

#### Rule 4: The Core Runtime Is a Portable Starter Kit

There's a small, clean "core" that every app needs:

- **Step executor** — runs through steps in sequence
- **Chat interface shell** — the conversational UI wrapper
- **Tool adapter layer** — loads and runs whatever tools the manifest says
- **Data persistence** — stores results, state, history
- **Config system** — settings, API keys, preferences

This core is the same across YT Lab and every breakaway app. It's the foundation you never rewrite. When you export, it comes along as the base. The breakaway app builds ON TOP of it, never modifies it.

```
core/
├── executor/        ← step runner
├── chat/            ← chat UI shell
├── tools/           ← tool adapter/loader
├── data/            ← persistence layer
└── config/          ← settings management
```

#### Rule 5: No Cross-Project Dependencies

Project A never imports from Project B. Never. They share tools from the tool bank and they share the core runtime, but they don't know each other exist. If you delete Project A, Project B doesn't even notice.

#### Rule 6: The Export Function

This is the actual mechanism. A command (or UI button) that says: "Package this project as a standalone app."

What it does:
1. Reads the project's `manifest.json`
2. Copies the project folder to a new directory
3. Copies the tool modules listed in `tools_required`
4. Copies the core runtime
5. Generates a fresh `package.json` / project config
6. Produces a working, runnable standalone app

What you get:
```
my-ad-agency-app/               ← fresh standalone app
├── core/                       ← copied from YT Lab core
├── tools/
│   └── computer-use/           ← only the tools this project needs
├── project/                    ← the project folder, renamed
│   ├── manifest.json
│   ├── steps/
│   ├── prompts/
│   ├── sub-projects/
│   └── ...
├── package.json                ← generated, independent
└── README.md                   ← generated from manifest
```

**This app runs.** Without YT Lab. Without any other projects. It's independent.

### The Customization Phase (Post-Breakaway)

Once a project breaks away, you'll almost always want to add things that didn't make sense inside YT Lab:

- **Branding** — custom logo, colors, domain name
- **Billing** — Stripe, packages, client payment
- **Client-facing dashboard** — a UI their customers see
- **Niche-specific features** — things only this type of app needs
- **Onboarding flow** — getting new users set up

The breakaway flow:
```
1. Project thrives inside YT Lab (10-20 sub-projects, proven workflow)
2. Decision: "This should be its own product"
3. Export → standalone app in a fresh directory
4. Agent reads the manifest + all the project code
5. You describe customizations: "Add Stripe billing, client dashboard,
   custom branding for [business name]"
6. Agent builds on top of already-working code — not from scratch
7. Result: sellable product with the automation already proven
```

The key insight: **you're never starting from zero.** The automation already works. The steps are proven. The prompts are refined. You're just wrapping it in a product shell. That's a weekend, not a month.

---

## The CLI-to-Chat Bridge (Making It Accessible)

A lot of the powerful stuff people demonstrate in YouTube videos happens in a terminal. They're typing CLI commands, piping outputs, running scripts. The audience watching is often intimidated — they see the power but can't replicate it because they don't live in a terminal.

**YT Strategy Lab solves this by wrapping CLI workflows in a chat interface.** Under the hood, the system is still executing via CLI (we have full CLI access built in, and the dashboard pulls results back). But the user interacts through a friendly chat — type what you need like you're talking to a person, not a terminal.

This means:
- **Expert users** still get the full power — the CLI is there, the automation runs the same way
- **Normal users** ("normies") get a guided experience — the template tells them what to input at each step, the chat handles the rest
- **The scary terminal is hidden** — the person who was terrified watching the YouTube video can now actually DO the thing

This is a big part of the value proposition: you're taking expert-level CLI workflows and making them accessible to anyone through structured templates + chat UI.

---

## Guided Intake (The Video Isn't Processed Blind)

When a YouTube video enters the system, it doesn't get processed blindly. The person submitting the video provides **context alongside the URL**:

1. **The YouTube URL** — the source material
2. **A description of what you're trying to build from it** — the user's intent

This description is critical. It tells the AI:
- Sometimes only HALF the video is relevant — the description says which half
- Sometimes the whole video maps to one system — the description confirms that
- The specific angle or use case the user wants to extract

**The AI reads the description BEFORE processing the transcript.** This means it's laser-focused from the start — it knows exactly what it's looking for, what to extract, what to skip. It's not guessing. The description acts as the creative brief for template creation.

*Example: A 45-minute video covers 4 different automation topics. The user writes: "I want the audience avatar discovery process from the first 15 minutes — the part where he runs 50 ad variations and pulls out winning language." The AI ignores the other 30 minutes and builds a focused template for just that workflow.*

---

## What This Means for Building

When you're building features for YT Strategy Lab, keep this in mind:

1. **Don't hardcode for one use case.** The ad agency was the first video. It won't be the last. Build for ANY video, any workflow, any tool type.

2. **The template system is the core.** Steps + prompts + tool slots = the universal format. Every video maps to this structure regardless of what it's about.

3. **Tools are pluggable.** Computer-use is ONE tool. The architecture should support adding new tool types without rewriting the template system. Tools live in their own modules, projects reference them by name.

4. **Projects can nest.** A template can be a parent with sub-projects inside it. The data model and file system need to support this hierarchy — not just flat projects.

5. **Repeatability is the whole point.** A template that only works once is useless. Every project must be runnable with different inputs (different niche, different client, different market).

6. **The chat interface is as important as the automation.** Non-technical users need to be able to use these templates through a conversational UI. Don't build features that only work if someone knows CLI commands.

7. **Intake is guided, not blind.** The video processing pipeline always has user-provided context (a description of what to build). Design the intake flow to collect and use this context before touching the transcript.

8. **Every project must be breakaway-ready.** This is non-negotiable. Self-contained folder, manifest file, tool references (not inline tool code), no cross-project dependencies. If you can't export it with a single command, it's built wrong. The breakaway apps are the actual products — YT Lab is the factory. See the Breakaway Architecture section above.

9. **Core runtime stays thin and portable.** The step executor, chat shell, tool adapter, data layer, and config system are shared infrastructure. Keep them clean, keep them minimal, keep them independent of any specific project. Every breakaway app takes a copy of core.

---

## TL;DR

**YT Strategy Lab = YouTube video → reusable mini-app template → (optionally) standalone sellable app.**

Some templates are simple checklists. Some are fully automated workflows. All of them are repeatable. Templates can have nested sub-projects for variations of the same pattern. The tool bank grows over time. CLI power is wrapped in chat for accessibility. Video intake is guided by user-provided context, not blind processing.

**The business model:** YT Lab is the factory — it probably never gets sold. The breakaway apps are the products. Any project that proves itself (10-20+ sub-projects, proven workflow) can be exported as a standalone app in one command. The automation already works; you just wrap it in a product shell with billing, branding, and client-facing UI. That's why breakaway-ready architecture is Rule #1, not an afterthought.
