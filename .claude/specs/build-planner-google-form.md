# Build Planner — Google Forms Blueprint

> **What this is:** A field-by-field blueprint for creating the Google Form. Copy each section into Google Forms using the field types noted. The form collects everything needed to generate phase-separated build scripts with Claude Code.
>
> **The funnel:** Free form → they fill it out → they realize they need rules/PRD/templates → upsell offer on the thank-you page and confirmation email.

---

## FORM SETTINGS

- **Title:** AI Build Planner — Build Any App With Claude Code
- **Description:** Answer these 20 questions and get a complete, phase-separated build plan for your next app. Works with Claude Code CLI ($20/month subscription). Takes 15-30 minutes to fill out.
- **Collect email:** YES (this is your list)
- **Confirmation message:** (see THANK YOU PAGE section at bottom)
- **Response destination:** Google Sheet (for easy export)

---

## SECTION 1: Project Basics
**Section description:** "Let's start with the basics. What are you building?"

---

### Q1 — App Name
- **Type:** Short text
- **Question:** What's your app called?
- **Helper text:** Keep it short — this becomes your project folder name. Example: "HabitTracker" or "TeamDash"
- **Required:** Yes
- **Validation:** None

---

### Q2 — App Description
- **Type:** Long text (paragraph)
- **Question:** Describe your app in 2-3 sentences. What does it do and who is it for?
- **Helper text:** Example: "A habit tracking app for busy parents. Users log daily habits, see streaks, and get weekly summary emails. Mobile-friendly web app."
- **Required:** Yes

---

### Q3 — Tech Stack
- **Type:** Multiple choice (radio buttons)
- **Question:** What tech stack do you want?
- **Options:**
  - React + Python (Most popular — React frontend, FastAPI backend, SQLite database)
  - React + Node (JavaScript everywhere — React frontend, Express backend, PostgreSQL)
  - Next.js (Best for SEO — full-stack React with server-side rendering)
  - React Only (No backend — single-page app with local storage)
  - Vue + Python (Vue frontend, FastAPI backend)
  - Other (I'll specify below)
- **Helper text:** Not sure? Pick "React + Python" — it's the most common stack with the most tutorials online.
- **Required:** Yes

---

### Q3b — Custom Stack (conditional)
- **Type:** Long text (paragraph)
- **Question:** You picked "Other" — describe your custom tech stack.
- **Helper text:** List the frameworks, languages, and databases you want. Example: "SvelteKit with Prisma and PostgreSQL, deployed on Vercel"
- **Required:** No
- **Show only if:** Q3 = "Other"

---

## SECTION 2: Build Rules
**Section description:** "These are the rules Claude follows while building your app. Think of them as instructions for a contractor building your house. The more specific you are, the better the result."

---

### Q4 — Tech Stack Rules
- **Type:** Long text (paragraph)
- **Question:** What specific versions, libraries, or patterns should Claude always use?
- **Helper text:** This goes into EVERY phase of your build. Be specific. Example: "Use React 19 with TypeScript strict mode. Tailwind CSS v4 for styling. shadcn/ui for all form components. TanStack Query for API calls. Only functional components — never class components."  If you don't have preferences, write "Use latest stable versions of everything."
- **Required:** Yes

---

### Q5 — Project Setup Rules
- **Type:** Long text (paragraph)
- **Question:** What should happen FIRST before any features get built? (folder structure, dependencies, boilerplate)
- **Helper text:** This goes into PHASE 1 ONLY. Example: "Create with Vite. Folders: src/components, src/pages, src/hooks, src/lib. Install all deps. Basic layout with header, sidebar, main area. Set up routing. Theme file with my colors. Don't build features yet — just the skeleton."
- **Required:** Yes

---

### Q6 — Testing Rules
- **Type:** Multiple choice (radio buttons)
- **Question:** How should Claude verify its work? (This applies to Phase 2 onward — Phase 1 is just setup.)
- **Options:**
  - Full testing — Claude writes and runs tests for every feature (Best for real apps you'll ship)
  - Lint + type-check only — Just verifies code compiles without errors (Good enough for most builds)
  - No testing / YOLO — Build fast, verify nothing (Only for throwaway prototypes)
  - Custom — I'll provide my own test commands below
- **Required:** Yes

---

### Q6b — Custom Test Commands (conditional)
- **Type:** Long text (paragraph)
- **Question:** Paste your custom test commands here.
- **Helper text:** These run exactly as written after each feature. Example: "npm run lint && npm run typecheck && npm run test -- --coverage"
- **Required:** No
- **Show only if:** Q6 = "Custom"

---

### Q7 — Code Style Rules
- **Type:** Long text (paragraph)
- **Question:** Any specific coding patterns Claude should follow in every file?
- **Helper text:** Optional — skip if you don't have preferences. Examples: "kebab-case file names. API routes under /api/v1/. Zod for form validation. Every component needs loading + error states. Never hardcode URLs — use env variables."
- **Required:** No

---

### Q8 — Additional Rules / Secret Sauce
- **Type:** Long text (paragraph)
- **Question:** Any additional rules, techniques, or instructions? (This is where you paste stuff from YouTube tutorials, blog posts, or your own experience.)
- **Helper text:** Common additions: prompting techniques from creators you follow, security rules ("never store passwords in plain text"), accessibility rules ("all images need alt text"), performance rules ("lazy load images"), design references ("match this Figma"). Paste as much as you want.
- **Required:** No

---

### Q9 — Phase Scoping
- **Type:** Checkbox grid
- **Question:** For each rule block above, which phases should it apply to?
- **Rows:** Tech Stack Rules (Q4) | Project Setup Rules (Q5) | Testing Rules (Q6) | Code Style Rules (Q7) | Additional Rules (Q8)
- **Columns:** Phase 1 Only | Phase 2+ Only | All Phases
- **Helper text:** "Phase 1 Only" = setup rules not needed later. "Phase 2+ Only" = rules for feature-building phases (like testing). "All Phases" = universal rules. When in doubt, pick "All Phases."
- **Required:** Yes

---

## SECTION 3: Features — What to Build
**Section description:** "Now list everything your app needs to do. Be specific — 'user auth' is too vague. 'Login page with email/password, signup with email verification, forgot password with reset link' is good."

---

### Q10 — Feature List
- **Type:** Long text (paragraph)
- **Question:** List every feature your app needs. One per line, numbered. Include a size estimate: S (small), M (medium), or L (large) after each.
- **Helper text:** Sizes: S = one file, simple, under 100 lines (e.g., About page). M = multiple files, some logic, 100-500 lines (e.g., login form, data table). L = many files, complex, 500+ lines (e.g., dashboard with charts, payment system). Example list:
1. Login + signup with email/password — M
2. User profile page with avatar upload — M
3. Dashboard with stats cards and charts — L
4. Settings page with notification preferences — S
5. Admin panel with user management — L
- **Required:** Yes

---

### Q11 — Feature Dependencies
- **Type:** Long text (paragraph)
- **Question:** Which features depend on other features being built first?
- **Helper text:** Use the numbers from your feature list. Example: "Feature 3 (dashboard) depends on Feature 1 (login) because you need to be logged in. Feature 5 (admin) depends on Feature 1 (login) and Feature 4 (settings)." If nothing depends on anything, write "None — all independent."
- **Required:** Yes

---

### Q12 — Existing PRD
- **Type:** Multiple choice (radio buttons)
- **Question:** Do you already have a detailed PRD or app spec written?
- **Options:**
  - No — my feature list above is my spec (that's fine!)
  - Yes — I'll paste it below
  - Yes — I have a file (I'll attach or link it)
- **Required:** Yes

---

### Q12b — PRD Content (conditional)
- **Type:** Long text (paragraph)
- **Question:** Paste your PRD or app spec here.
- **Helper text:** Include as much detail as you have. The more detail, the better Claude builds.
- **Required:** No
- **Show only if:** Q12 = "Yes — I'll paste it below"

---

### Q12c — PRD File Link (conditional)
- **Type:** Short text
- **Question:** Link to your PRD file (Google Doc, Notion, GitHub, etc.)
- **Required:** No
- **Show only if:** Q12 = "Yes — I have a file"

---

## SECTION 4: Build Settings
**Section description:** "How should Claude run your build? These are the knobs and dials. Every option has a recommended default — if you're not sure, just go with the recommendations."

---

### Q13 — AI Model
- **Type:** Multiple choice (radio buttons)
- **Question:** Which Claude model should build your app?
- **Options:**
  - Sonnet (Recommended — fast, great quality, handles 90% of builds)
  - Opus (Smartest but slowest — best for complex architecture or tricky logic)
  - Haiku (Fastest but least capable — only for tiny simple features)
- **Helper text:** Pick Sonnet unless you have a specific reason not to.
- **Required:** Yes

---

### Q14 — Turns Per Phase
- **Type:** Multiple choice (radio buttons)
- **Question:** How many back-and-forth turns should Claude get per phase?
- **Options:**
  - 10 turns (Small phases, 1-2 simple features)
  - 25 turns — Recommended (Most phases — enough to build and fix issues)
  - 50 turns (Large phases with complex features)
  - Unlimited (Let Claude keep going until done — uses more subscription)
- **Helper text:** A "turn" = one exchange where Claude tries something, checks the result, and adjusts.
- **Required:** Yes

---

### Q15 — Phase Transition
- **Type:** Multiple choice (radio buttons)
- **Question:** What should happen between phases?
- **Options:**
  - Pause — Recommended (Script stops. You review. You manually start the next phase. Safest.)
  - Auto-continue (Next phase starts immediately. Hands-off but risky — broken code snowballs.)
  - Prompt me (Script asks "Continue? y/n" before each new phase.)
- **Required:** Yes

---

### Q16 — Error Handling
- **Type:** Multiple choice (radio buttons)
- **Question:** What happens when Claude hits an error?
- **Options:**
  - Retry once then skip — Recommended (Tries once more. If still broken, skips and moves on.)
  - Stop everything (Build halts. You investigate. Safest but slowest.)
  - Skip immediately (Don't retry. Move on. Fast but might miss easy fixes.)
- **Required:** Yes

---

### Q17 — Git Commits
- **Type:** Multiple choice (radio buttons)
- **Question:** Should Claude save to git automatically?
- **Options:**
  - After each feature — Recommended (Safest — roll back one feature if something breaks.)
  - After each phase (Fewer commits. More risk — lose all phase work if it breaks.)
  - Never (You handle git yourself. Only if you know git well.)
- **Helper text:** Git is like a save button for your code. More frequent saves = safer.
- **Required:** Yes

---

## SECTION 5: Phase Planning
**Section description:** "This is the most important part. You're deciding how to split your build into chunks. Each chunk becomes its own script with its own fresh Claude session."

---

### Q18 — Number of Phases
- **Type:** Multiple choice (radio buttons)
- **Question:** How many phases should your build have?
- **Options:**
  - 2 phases (3-5 features total: setup + build)
  - 3 phases (6-10 features: setup + core + extras)
  - 4 phases (11-15 features)
  - 5 phases (16-20 features)
  - 6+ phases (20+ features — specify exact number below)
- **Helper text:** When in doubt, pick MORE phases. Each phase gets a fresh context window, so smaller chunks = better results. Phase 1 is always project setup + foundation features.
- **Required:** Yes

---

### Q18b — Custom Phase Count (conditional)
- **Type:** Short text
- **Question:** How many phases? (number)
- **Required:** No
- **Show only if:** Q18 = "6+ phases"

---

### Q19 — Phase Assignments
- **Type:** Long text (paragraph)
- **Question:** Which features go in which phase? Use the numbers from your feature list (Q10).
- **Helper text:** Rules: (1) If Feature B depends on Feature A, A goes in an earlier phase. (2) Don't overload — 3-5 medium features per phase max. (3) Phase 1 = project setup + foundation features (auth, database, base layout). Example:
Phase 1: Project setup + Features 1, 2 (auth and profile — foundation)
Phase 2: Features 3, 4 (dashboard and settings — core app)
Phase 3: Features 5 (admin panel — depends on everything else)
- **Required:** Yes

---

### Q20 — Anything Else?
- **Type:** Long text (paragraph)
- **Question:** Anything else we should know? Special requirements, deployment targets, design references, or context that doesn't fit above?
- **Helper text:** Optional. Examples: "Deploy to Vercel", "Must work on mobile", "Match the design at this Figma link: ...", "This is a rebuild of an existing app at [link]"
- **Required:** No

---

## THANK YOU PAGE (After Form Submission)

**Title:** Your Build Plan Is Ready to Generate!

**Body:**

```
Thanks for filling out the Build Planner! Here's what to do next:

📋 STEP 1: Get your answers
Check your email — we sent you a copy of your responses.
Or click "View your responses" below.

📋 STEP 2: Generate your build scripts
Open Claude.ai, start a new chat, and paste this prompt:

---
I filled out the Build Planner Worksheet. Here are my answers.
Please read through everything, then generate:

1. One bash script per phase (phase1.sh, phase2.sh, etc.)
2. Each script calls: claude --model [my model] --max-turns [my turns] --print "..."
3. Inside each script's prompt, include:
   - My rule blocks that apply to that phase (based on my scoping answers)
   - The features for that phase
   - Phase 1 gets: "Set up the project skeleton FIRST. Don't skip ahead."
   - Phase 2+ gets: "Read ALL existing code first. Follow established patterns."
4. A run_all.sh master script with [my pause/auto/prompt preference] between phases

My answers:
[Paste your form responses here]
---

📋 STEP 3: Run it
Save the scripts Claude generates, make them executable (chmod +x *.sh),
and run: bash scripts/run_all.sh


🔥 WANT BETTER RESULTS? Here's what the pros use:

You just built the recipe. But the INGREDIENTS make or break the dish.

The #1 reason AI builds fail? Vague rules and thin PRDs.

Your Section B answers (build rules) and Section C answers (features/PRD)
are doing 80% of the heavy lifting. Generic rules get generic code.

I spent 6 months testing what actually works. The result:

✅ Battle-tested coding standards (the rules that eliminate 90% of AI mistakes)
✅ PRD templates that give Claude exactly the context it needs
✅ Phase-scoped instruction blocks for Phase 1 setup and Phase 2+ building
✅ Pre-built templates for common app types (SaaS, e-commerce, dashboards)
✅ The exact prompting techniques used to build production apps

👉 [GET THE PRO TEMPLATES →] (link to sales page)

One-time purchase. Use on every build, forever.
No subscription. No recurring fees.
```

---

## CONFIRMATION EMAIL

**Subject:** Your Build Plan answers + next steps

**Body:**

```
Hey [Name],

Your Build Planner responses are attached below.

QUICK START:
1. Copy your responses
2. Open Claude.ai → new chat
3. Paste the generation prompt (below) + your responses
4. Claude generates your bash scripts
5. Run them

GENERATION PROMPT (copy this):
[Same prompt as thank-you page]

YOUR RESPONSES:
[Auto-inserted by Google Forms]

---

💡 PRO TIP: Your build is only as good as your rules.

Most people fill in Section B (build rules) with one or two sentences.
The people getting incredible results? They use 50-100 lines of
battle-tested coding standards per block.

The difference between "Claude built something weird" and "Claude
nailed it first try" is almost always the quality of your instruction
blocks.

I packaged the exact rules, PRD templates, and phase-scoped blocks
I use on every build:

👉 [GET THE PRO TEMPLATES →] (link to sales page)

Happy building,
[Your name]
```

---

## GOOGLE SHEET STRUCTURE (Response Destination)

When responses flow into Google Sheets, columns will be:

| Column | Maps To | Notes |
|--------|---------|-------|
| Timestamp | Auto | When they submitted |
| Email | Auto | Your lead list |
| A | Q1 | App name |
| B | Q2 | App description |
| C | Q3 | Tech stack |
| D | Q3b | Custom stack (if other) |
| E | Q4 | Tech stack rules |
| F | Q5 | Setup rules |
| G | Q6 | Testing approach |
| H | Q6b | Custom test commands |
| I | Q7 | Code style rules |
| J | Q8 | Additional rules |
| K | Q9 | Phase scoping grid |
| L | Q10 | Feature list with sizes |
| M | Q11 | Dependencies |
| N | Q12 | Has PRD? |
| O | Q12b | PRD content |
| P | Q12c | PRD link |
| Q | Q13 | Model choice |
| R | Q14 | Turns per phase |
| S | Q15 | Phase transition |
| T | Q16 | Error handling |
| U | Q17 | Git commits |
| V | Q18 | Phase count |
| W | Q18b | Custom phase count |
| X | Q19 | Phase assignments |
| Y | Q20 | Anything else |

---

## UPSELL PRODUCT TIERS (Reference for Sales Page)

| Tier | Price Point | What They Get |
|------|------------|---------------|
| **Free** | $0 | This form + the generation prompt + setup guide |
| **Pro Templates** | $97-$495 | Battle-tested instruction blocks (coding standards, security rules, testing contracts, component patterns), PRD templates for 7 app types, phase-scoped blocks ready to paste into Section B |
| **Build Planner App** | $29-$49/mo | The one-pager tool that does all of this automatically — no copy-pasting, no manual script assembly, token calculator built in, template library, save/load projects |
| **Build Orchestrator** | $79-$149/mo | Multi-page deluxe: wave orchestration, role configs, prompt library, AI-powered PRD decomposition, live build dashboard, quality gates |

**Funnel path:**
Free form → "Wow this is amazing but my rules suck" → Pro Templates ($97-$495 one-time) → "This is great but doing it manually is tedious" → Build Planner App ($29-$49/mo) → "I want the full automation" → Build Orchestrator ($79-$149/mo)
