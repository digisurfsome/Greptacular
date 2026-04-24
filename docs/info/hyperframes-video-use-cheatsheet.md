# Hyperframes + Video Use — Cheat Sheet

Source: Nate tutorial transcript. Goal: drop raw video → Claude trim + animate + render.

---

## 1. Stack Overview

| Piece | Job |
|-------|-----|
| **Claude Code** (desktop app or VS Code) | Orchestrator. Runs everything. |
| **video-use** (GitHub repo) | Transcribe + trim filler/retakes/silences. Also has Remotion skill for animation. |
| **hyperframes** (GitHub repo) | HTML-based motion graphics / liquid-glass cards. Nate prefers over Remotion. |
| **Transcription** | 11 Labs API (Nate's pick) OR OpenAI Whisper API OR local Whisper (free). |

Pipeline:
`raw file → video-use trims → transcript w/ timestamps → hyperframes animates → render`

Remotion = built into video-use. Hyperframes = separate, better looking. Both sync graphics to transcript timestamps.

---

## 2. One-Time Setup

### 2a. Install Claude Desktop app
- Go to Claude download page. Install for OS.
- Sign in. Need paid plan w/ Claude Code access.

### 2b. Pick working folder
- Open empty folder in Claude Desktop, **OR**
- Grab Nate's Hyperframe Student Kit from his free Skool community (easiest).

### 2c. Pull the two repos
Copy-paste this prompt into Claude Code:

> Hey, I'm setting up this project to be my video editing studio. Look at these two GitHub repos and pull in the skills + important info we need so I can give you a raw video file and you edit it, remove filler words, and add motion graphics:
> - [hyperframes repo URL]
> - [video-use repo URL]

Let Claude clone + wire the skills.

### 2d. Add API key (11 Labs method)
1. Go to 11labs.io → bottom-left → **Developers → API Keys → Create**.
2. Copy key.
3. In project root, create `.env` file (ask Claude Code to make it, or use VS Code).
4. Paste key into `.env`. Do NOT paste key into Claude chat (stays in history).

Whisper (local or OpenAI) also works. 11 Labs = Nate's pick for cut accuracy.

---

## 3. Per-Video Workflow (Step by Step)

### Step 1 — Drop raw file
- Put raw recording into the project folder (e.g. `edit-demo-raw.mp4`).

### Step 2 — Trim pass
In Claude chat, type `@` → pick the raw file. Then:

> Use the video-use tool to edit this video. Analyze it, remove filler words, silences, retakes. First task is trim only — we'll add motion graphics with hyperframes after.

Claude returns:
- What it plans to keep
- What it plans to cut
- Judgment-call questions (e.g. "leave trailing 'so' as breath?")

Reply: **"Make it as punchy as possible"** (or answer each call).

Output: `edited.mp4` + `transcripts/*.json` (word-by-word timestamps).

### Step 3 — Find the edited file
If Claude doesn't say path, ask:
> Give me the file path.

Paste into Explorer → watch to confirm edit is clean.

### Step 4 — Plan motion graphics (voice-to-text recommended)
Open the edited transcript. Use voice-to-text to dictate scene direction. Be very specific. Template:

> Add motion graphics using hyperframes. Directions:
> - At [phrase X], pop a liquid-glass card on [left/right/bottom]. Karaoke-style subtitles. Looks like a video title.
> - At [phrase Y], add card that says "[text]" + animation on [side] showing [concept].
> - At [phrase Z], transition facecam to vertical-cropped w/ rounded edges + drop shadow on right half. Left half = text "thanks for watching" on dark modern bg.
> Sync each to exact second where phrase is spoken.

### Step 5 — Switch to PLAN MODE
Before shooting off the big animate prompt — flip Claude Code to **plan mode**. Why: Claude drafts a beat-by-beat plan (cards, colors, anchor words, timings) BEFORE writing HTML. Saves tokens.

### Step 6 — Review the plan
Claude returns:
- Aesthetic direction + color palette
- Beat timeline (Beat A: 0–5s, Beat B: 5–12s, etc.)
- Anchor word per beat (the word that triggers the scene)
- Card contents, positions, fonts

Actions:
- Highlight any line in Claude chat → inline comment box appears. Use it for surgical tweaks.
- Click **Revise** to add/change scenes. Example:
  > Add one more scene at the end: last 5 sec, vertical-crop facecam w/ rounded edges + shadow, shift to right half. Left half = "thanks for watching" on dark bg.
- Approve when happy.

### Step 7 — Let it build
Claude writes HTML for each beat, renders scenes. Takes time + tokens (~238k for Nate's 30s video).

### Step 8 — Preview
- Top-right of Claude Desktop → **Preview** button (inline), **OR**
- Click the localhost tab for fullscreen.

Watch. Note issues.

### Step 9 — Iterate with specific notes
Paste back a bullet list of fixes. Example:
> - Beat 1 liquid glass covers my face — scale down + crop right side.
> - Grid-pattern overlay visible on whole video — remove, only show it in the bg-transition beat.
> - End transition cropped only right side — crop BOTH sides so facecam stays centered-vertical w/ rounded corners.
> Implement those, rest is good.

### Step 10 — Timeline editor tweaks (optional)
In Hyperframes dashboard timeline:
- Drag beats to shift timing.
- Shorten / extend.
- Delete beats.
- Changes write back to code → Claude sees them → reflects in final render.

### Step 11 — Render final
> Give me the render.

Final file drops into `final-renders/`. Done.

---

## 4. Project Folder Structure (after a run)

```
video-projects/
  {project-name}/
    assets/
      edited.mp4
    clips/
    transcripts/
      *.json          ← word-by-word timestamps
    compositions/     ← beat HTML files (the animation source)
    components/
    final-renders/
    screenshots/      ← Claude self-verifies by screenshotting
```

Every new video = new project folder. Past projects = training data for style consistency.

---

## 5. Prompt Patterns That Work

**Trim pass:**
> Use video-use to edit @file. Remove filler, silences, retakes. Trim only — hyperframes comes next.

**Animate pass (first time on a video type):**
> Add hyperframes motion graphics. [Scene-by-scene direction w/ exact phrases as anchors + position + visual concept.]

**Iterate:**
> Beat [N]: [problem]. Fix: [specific change]. Rest is good.

**Reusable style (after 3–5 videos of same type):**
> Build a `lesson-design.md` philosophy file from the compositions we've made. Next time I drop a lesson raw file, use that doc automatically.

---

## 6. Tips / Gotchas

- **Be specific** in plan phase. Vague prompts burn tokens on wrong-path HTML.
- **Plan mode first** — always. Cheaper than generate-then-redo.
- **Preview audio can be 3× loud** (localhost bug). Final render audio is fine.
- **Screenshot verify** — tell Claude to screenshot scenes to self-check. Catches layout fails.
- **Don't paste API keys in chat.** Use `.env`.
- **Hyperframes > Remotion** for premium look (Nate's opinion). Remotion works, just plainer.
- **End-to-end automation** only kicks in after you've built a style doc from ~5 similar videos.
- **Training data mindset** — each finished project = reference for future same-type videos.
- **Cost check:** ~238k tokens for a 30s video w/ multiple iterations. Budget accordingly.

---

## 7. Optional: Replace Recording Step

Nate mentioned: use **HeyGen** avatar → drop script → get raw file. Skips manual recording + trimming (avatar has no filler). Then jump straight to animate step.

---

**File:** `docs/info/hyperframes-video-use-cheatsheet.md` (info | cheat sheet)
