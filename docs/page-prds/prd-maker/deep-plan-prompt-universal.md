# Deep Plan Prompt — Universal Version

> Works in: Claude Web, Claude Desktop, Claude Code, AutoForge Workspace Chat
> Copy everything below the line and paste it. Replace {YOUR_IDEA} with your concept.

---

```
I need you to do a deep multi-perspective analysis of this app idea. Do NOT just start planning. Follow this exact 5-phase process:

## My Idea

{YOUR_IDEA}

---

## Phase 1: Exploration (Do this FIRST, silently)

Before you design anything, answer these questions internally:
- What category of app is this? (SaaS, marketplace, tool, game, social, etc.)
- What existing apps are closest to this? What do they get right/wrong?
- What are the 3-5 core mechanisms that make this app WORK? (not features — mechanisms. The engine parts.)
- What's the hardest technical challenge here?
- What does the user do in their FIRST 60 seconds?
- What makes someone come back tomorrow?

## Phase 2: Three Perspectives (Do ALL three — not just one)

Now design this app from THREE different angles. Each one is a complete approach. Do not combine them yet.

### Perspective A: Simplicity-First
Design the simplest possible version that delivers the core value. Minimum features, minimum complexity, minimum files. What's the fastest path to "this works and people want it"? Cut everything that isn't essential. If you can use an existing library/service instead of building it, do that.

### Perspective B: User-Experience-First
Design the version that feels incredible to use. What makes the first interaction magical? What micro-interactions matter? Where does friction kill retention? What would make someone screenshot this and share it? Don't worry about engineering complexity — focus on what the user FEELS.

### Perspective C: Scale-Ready
Design the version built for growth. What data model handles 100x users without a rewrite? Where do you need clean abstractions from day one? What are the integration points? What's the API-first architecture? Think about what breaks at scale and prevent it now.

## Phase 3: Consolidation

Now MERGE the three perspectives into ONE plan. For each part of the app:
- Take the simplicity approach UNLESS the UX or scale version is clearly worth the extra complexity
- Flag where you chose a more complex approach and WHY
- Identify the 1-2 things from each perspective that are non-negotiable

## Phase 4: Output (Use this EXACT structure)

# Deep Plan: [App Name]

## 1. One-Sentence Pitch
[What is this, for whom, and why they care — ONE sentence]

## 2. Core Mechanisms
[The 3-5 engine parts that make this app work. Not features. Mechanisms.]

| # | Mechanism | What It Does | Why It's Essential |
|---|-----------|-------------|-------------------|
| 1 | ... | ... | ... |

## 3. User Journey (First 60 Seconds)
[Step-by-step: what happens from the moment they land to the moment they get value]

## 4. Architecture Overview
| Layer | Technology | Why This Choice |
|-------|-----------|----------------|
| Frontend | ... | ... |
| Backend | ... | ... |
| Database | ... | ... |
| Auth | ... | ... |
| Hosting | ... | ... |

## 5. Page Map
| Page | Purpose | Key Components |
|------|---------|---------------|
| ... | ... | ... |

## 6. Data Model (Core Tables/Collections)
[Just the essential ones — not every table, just the ones that define the app]

## 7. Implementation Phases
Break the build into phases. Each phase should be independently deployable and testable.

### Phase 1: [Name] (X days)
- What gets built
- What's usable after this phase
- Files created/modified

### Phase 2: [Name] (X days)
...

## 8. Risks & Hard Parts
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ... | Low/Med/High | Low/Med/High | ... |

## 9. What I Chose NOT to Build (and Why)
[From the three perspectives, what got cut and the reasoning]

## 10. Competitive Edge
[What makes this different from the 2-3 closest existing apps]

## Phase 5: Honest Assessment

End with:
- **Difficulty:** X/10
- **Time to MVP:** X days/weeks
- **Biggest risk:** [one sentence]
- **Will people pay for this?** [honest yes/no/maybe with reasoning]
- **If I could only build ONE feature, it would be:** [the atomic core]
```
