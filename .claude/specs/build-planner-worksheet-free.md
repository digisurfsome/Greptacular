# Build Planner Worksheet — The Free Version

> **What this is:** A fill-in-the-blank questionnaire. Answer every numbered question, then hand your answers to Claude and it generates your phase-separated bash build scripts.
>
> **How to fill this out:** Write your answer below each numbered question. When done, save this file and upload it back to Claude with the prompt at the end.

---

## PART 1: SETUP (Do This First, One Time Only)

### Step 1: Get a Claude Account

1. Go to **claude.ai** and click "Sign Up"
2. Use email or Google/Apple sign-in
3. You now have a free account (limited messages)

### Step 2: Subscribe to Claude Pro (Required for Claude Code)

1. Once logged in at claude.ai, click your profile icon (bottom-left)
2. Click **"Upgrade to Pro"** or **"Subscribe"**
3. Choose **Claude Pro** — currently $20/month
4. Enter payment info and confirm
5. This gives you: extended usage limits + access to Claude Code

> **Why Pro?** Claude Code (the terminal tool) requires a Pro subscription minimum. Free accounts can't use it. The $20/month Pro plan is the cheapest way in.

### Step 3: Install Claude Code on Your Computer

**On Mac:**
```bash
# Open Terminal (search "Terminal" in Spotlight)
# Install Node.js first if you don't have it:
brew install node

# Then install Claude Code:
npm install -g @anthropic-ai/claude-code

# Verify it worked:
claude --version
```

**On Windows:**
```bash
# Open PowerShell (search "PowerShell" in Start menu)
# Install Node.js first: download from https://nodejs.org (LTS version), run the installer

# Then install Claude Code:
npm install -g @anthropic-ai/claude-code

# Verify it worked:
claude --version
```

**On Linux:**
```bash
# Install Node.js if needed:
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt-get install -y nodejs

# Then install Claude Code:
npm install -g @anthropic-ai/claude-code

# Verify it worked:
claude --version
```

### Step 4: Log In to Claude Code

```bash
claude
```

First time you run it, it opens a browser window asking you to log in with your Claude Pro account. Log in, authorize it, done.

### Step 5: Create Your Project Folder

```bash
mkdir ~/my-app
cd ~/my-app
```

### Step 6: Test That It Works

```bash
claude --print "Say hello and confirm you can see this project folder"
```

If Claude responds and mentions your folder, you're ready.

---

## PART 2: THE QUESTIONNAIRE

Fill in your answer below each numbered question. Questions marked ⚠️ need extra thought.

---

### SECTION A: Project Basics

**1. What is your app called?**
> Just a name. Keep it short. This becomes your folder name too.

Answer:


**2. Describe your app in 2-3 sentences. What does it do and who is it for?**
> Example: "A habit tracking app for busy parents. Users log daily habits, see streaks, and get weekly summary emails. Mobile-friendly web app."

Answer:


**3. What tech stack do you want?**
> Pick ONE option below. If you don't know, pick "React + Python" — it's the most common and has the most tutorials.
>
> Options:
> - **React + Python** — Full-stack web app. React frontend, FastAPI backend, SQLite database.
> - **React + Node** — JavaScript everywhere. React frontend, Express backend, PostgreSQL.
> - **Next.js** — Best for SEO-important sites. Full-stack React with server-side rendering.
> - **React only** — No backend. Single-page app with local storage. Good for simple tools.
> - **Vue + Python** — If you prefer Vue. Vue frontend, FastAPI backend.
> - **Custom** — Write your own stack.

Answer:


---

### SECTION B: Build Rules

These are the rules Claude follows while building. Think of them as instructions for a contractor building your house.

**4. Tech stack rules — What specific versions, libraries, or patterns should Claude always use?** ⚠️
> This goes into EVERY phase of your build. Be specific. If you don't care, write "Use latest stable versions of everything."
>
> Example: "Use React 19 with TypeScript strict mode. Use Tailwind CSS v4 for all styling. Use shadcn/ui for form components. Use TanStack Query for API calls. Only functional components with hooks — never class components."

Answer:


**5. Project setup rules — What should happen FIRST before any features get built?** ⚠️
> This goes into PHASE 1 ONLY. Think: folder structure, dependencies, config files, boilerplate.
>
> Example: "Create the project with Vite. Folder structure: src/components, src/pages, src/hooks, src/lib. Install all dependencies. Create a basic layout with header, sidebar, and main content area. Set up routing. Create a theme file with my colors. Don't build any features yet — just the skeleton."

Answer:


**6. Testing rules — How should Claude verify its work?**
> This goes into PHASE 2 AND ALL LATER PHASES (Phase 1 is just setup, testing starts in Phase 2).
>
> Pick ONE:
> - **Full testing** — Claude writes tests for every feature and runs them. Best for real apps you'll ship.
> - **Lint + type-check only** — Just verifies code compiles without errors. Good enough for most builds.
> - **No testing (YOLO)** — Build fast, verify nothing. Only for quick prototypes you'll throw away.
> - **Custom script** — You provide the exact test commands. Write them in your answer.

Answer:


**7. Code style rules — Any patterns Claude should follow in every file?**
> Goes into EVERY phase. Skip if you don't have preferences.
>
> Examples: "Use kebab-case for file names. Put API routes under /api/v1/. Use Zod for form validation. Every component needs a loading state and error state. Never hardcode URLs — use environment variables."

Answer:


**8. Additional rules or techniques — Your secret sauce.** ⚠️
> This is where you paste stuff from YouTube tutorials, blog posts, prompting techniques, or your own experience. Paste as much as you want.
>
> Common things people add:
> - Prompting techniques from creators they follow
> - Security rules ("never store passwords in plain text")
> - Accessibility rules ("all images need alt text")
> - Performance rules ("lazy load images, code-split routes")
> - Design rules ("match this Figma file" or "use this color palette")

Answer:


**9. Phase scope — For each rule block above, which phases should it go into?**
> Write the number (4-8) and the scope. If unsure, "All Phases" is the safe default.
>
> - **Phase 1 Only** = setup/scaffolding rules that aren't needed after the skeleton is built
> - **Phase 2+ Only** = rules that only matter once you're building features (like testing)
> - **All Phases** = universal rules that apply everywhere

| Question | Your Scope |
|----------|-----------|
| 4 (Tech stack) | |
| 5 (Project setup) | |
| 6 (Testing) | |
| 7 (Code style) | |
| 8 (Additional) | |

---

### SECTION C: Features (What to Build)

**10. List every feature your app needs.** ⚠️
> One per line. Be specific — "user auth" is too vague. "Login page with email/password, signup page with email verification, forgot password flow" is good. Don't worry about order — just get everything out of your head.

1.
2.
3.
4.
5.
6.
7.
8.
9.
10.
(add more if needed)


**11. Feature sizes — How big is each one?**
> Go back to question 10 and write S, M, or L next to each feature.
>
> - **S (Small)** = one file, simple, under 100 lines. Example: an "About" page, a simple button.
> - **M (Medium)** = multiple files, some logic, 100-500 lines. Example: a login form, a data table with sorting.
> - **L (Large)** = many files, complex, 500+ lines. Example: a full dashboard with charts, payment integration.

(Go mark S/M/L on your list in question 10)


**12. Dependencies — Which features need other features built first?** ⚠️
> Example: "Feature 4 (dashboard) depends on Feature 1 (user auth) because you need to be logged in."
>
> If nothing depends on anything, write "None — all independent."

Answer:


**13. Do you already have a detailed PRD or app spec?**
> If yes, paste it below or note where the file is. If no, your answers to 10-12 ARE your PRD — that's fine.

Answer:


---

### SECTION D: Build Settings

**14. Which AI model should do the building?**
> - **Sonnet** (recommended) — Fast, great quality for 90% of builds. Pick this if unsure.
> - **Opus** — Slower but smartest. Best for complex architecture or tricky logic.
> - **Haiku** — Fastest but least capable. Good for tiny simple features.

Answer:


**15. How many turns per phase?**
> A "turn" = one back-and-forth exchange where Claude tries something and checks the result.
>
> - **10** — Small phases, 1-2 simple features
> - **25** (recommended) — Most phases. Enough room to build and fix issues.
> - **50** — Large phases with complex features
> - **Unlimited** — Claude keeps going until done. Uses more of your subscription.

Answer:


**16. What happens between phases?**
> - **Pause** (recommended) — Script stops after each phase. You review, then manually run the next one. Safest — if something looks wrong, you can fix it before continuing.
> - **Auto-continue** — Next phase starts immediately. Hands-off but risky. If Phase 2 breaks something, Phase 3 builds on top of broken code.
> - **Prompt** — Script asks "Continue? (y/n)" before each new phase.

Answer:


**17. How should errors be handled?**
> - **Stop everything** — Build halts on any error. You investigate. Safest option.
> - **Retry once then skip** (recommended) — Claude tries once more. If still broken, skips that feature and continues.
> - **Skip immediately** — Don't retry, just move on. Fast but you might miss easy fixes.

Answer:


**18. Should Claude auto-commit to git?**
> - **After each feature** (recommended) — Safest. If something breaks, you roll back one feature.
> - **After each phase** — Fewer commits but more risk per chunk.
> - **Never** — You handle git yourself. Only pick this if you know git.

Answer:


---

### SECTION E: Phase Planning

**19. How many phases should your build have?** ⚠️
> Each phase gets its own bash script and its own fresh Claude session.
>
> **Rule of thumb:**
> - 3-5 features → **2 phases** (setup + build)
> - 6-10 features → **3 phases** (setup + core features + remaining features)
> - 11-15 features → **4 phases**
> - 16-20 features → **5 phases**
> - 20+ features → **6-8 phases**
>
> **Token math (if you want to be precise):**
> - Your rules from Section B: count the total lines. 100 lines ≈ 3,500 tokens.
> - Each feature description: ≈ 500-2,000 tokens depending on detail.
> - Target: keep each phase under 100,000 tokens total.
> - Phase 1 can hold ~3-5 medium features + your rules.
> - Phase 2+ can each hold ~4-6 medium features + your rules.
>
> When in doubt, more phases is safer. Each phase gets a fresh context window.

Answer:


**20. What features go in each phase?** ⚠️
> Use the feature numbers from question 10. Phase 1 is always project setup + foundation features (the stuff everything else depends on).
>
> Rules:
> - Dependencies go FIRST (if Feature 4 depends on Feature 1, Feature 1 goes in an earlier phase)
> - Don't overload — 3-5 medium features per phase max
> - Phase 1 should be: project skeleton + foundation (auth, database, base layout)

Phase 1:
Phase 2:
Phase 3:
Phase 4:
(add more if needed)

---

## PART 3: WHAT TO DO WITH YOUR ANSWERS

### Step 1: Save This File

Save your filled-out worksheet as a file (e.g., `my-app-worksheet.md` or `my-app-worksheet.txt`).

### Step 2: Upload to Claude and Generate Scripts

Go to **claude.ai** (the website, not the terminal). Start a new conversation. Upload your filled-out worksheet file, then paste this prompt:

---

**PROMPT 1 — Upload your worksheet with this message:**

```
I filled out the Build Planner Worksheet (attached). Please read through all
my answers and confirm you understand my app, my rules, my features, and my
phase plan. Summarize what you understood back to me so I can verify you got
it right before we generate scripts. If anything looks wrong, unclear, or
contradictory, tell me now.
```

Wait for Claude to summarize it back. Fix anything it got wrong. Then:

---

**PROMPT 2 — Generate the bash scripts:**

```
Great, that's all correct. Now generate my build scripts. Here's exactly what I need:

1. One bash script per phase: phase1.sh, phase2.sh, etc.
2. One master script: run_all.sh that runs them in sequence.

Each phase script must:
- Start with #!/bin/bash and set -e
- cd into the project directory
- Call: claude --model [use my answer to Q14] --max-turns [use my answer to Q15] --print "..."
- Inside the quoted prompt, include:
  a) My rule blocks that apply to this phase (check my Q9 scope answers)
  b) The features assigned to this phase (from my Q20 answers)
  c) Phase-specific guardrails:
     - Phase 1 gets: "Set up the project skeleton FIRST. Install dependencies. Create base layout and routing. Then build the foundation features. Do NOT skip ahead to later features."
     - Phase 2+ gets: "BEFORE writing any code, read ALL existing files in the project. Follow the patterns and structure already established in previous phases. Do NOT refactor or restructure previous code. Do NOT create duplicate files."

The run_all.sh must:
- Run each phase script in order
- [Use my Q16 answer for what happens between phases: pause/auto/prompt]
- Print clear status messages showing which phase is running

Output each script in a code block I can copy. Also tell me the exact terminal
commands to save and run them.
```

---

### Step 3: Save and Run the Scripts

After Claude generates your scripts:

```bash
# Create a scripts folder in your project:
cd ~/my-app
mkdir -p scripts

# Save each script Claude generated (copy-paste into files):
# (Or ask Claude to save them for you if you're in Claude Code terminal)

# Make them executable:
chmod +x scripts/*.sh

# Run the full build:
bash scripts/run_all.sh

# Or run one phase at a time:
bash scripts/phase1.sh
# review the code...
bash scripts/phase2.sh
# review again...
```

---

## TROUBLESHOOTING

**"claude: command not found"**
→ Node.js or Claude Code isn't installed. Go back to Setup Step 3.

**"Authentication required" or "Please log in"**
→ Run `claude` with no arguments. Log in through the browser. Try your script again.

**"Rate limited" or "Too many requests"**
→ You hit your subscription limit. Wait 10-15 minutes. Or reduce turns (Q15) to use less per phase.

**"Context window exceeded" or output cuts off**
→ Phase has too much content. Split it into two smaller phases. Move features to a later phase.

**Phase 2 broke what Phase 1 built**
→ This is why Pause mode (Q16) is recommended. Review each phase before starting the next. If something's wrong, fix it first.

**Claude built the wrong thing**
→ Your instructions (Section B) weren't specific enough. Add more detail. The more precise your rules, the better the output.

**"npm: command not found"**
→ Node.js isn't installed. Go to https://nodejs.org, download the LTS version, install it, restart your terminal.

**"brew: command not found" (Mac only)**
→ Homebrew isn't installed. Go to https://brew.sh, run the install command shown on the page, then retry.

---

## QUICK REFERENCE

| Question | What It Controls | When It's Used |
|----------|-----------------|----------------|
| 1-3 | Project identity & tech stack | Every phase (context) |
| 4 | Tech stack rules | Based on Q9 scope |
| 5 | Setup rules | Phase 1 only |
| 6 | Testing rules | Phase 2+ only |
| 7 | Code style rules | Based on Q9 scope |
| 8 | Additional techniques | Based on Q9 scope |
| 9 | Phase scoping | Controls which rules go where |
| 10-13 | Feature list & PRD | Split across phases |
| 14-18 | CLI settings | Every phase script |
| 19-20 | Phase plan | Determines number of scripts |
