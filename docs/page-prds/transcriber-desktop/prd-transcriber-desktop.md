# Transcriber Desktop App — PRD

**Status:** Draft — ready for review
**Owner:** Lober
**Working name:** Transcriber (rename TBD)

## Problem
YT Lab works, but the flow still requires opening a browser, navigating to AutoForge, starting the server, picking a page. When Lober sees a video in a notification (20+ per day across YouTube, Twitter/X, Zoom recordings, etc.), the friction kills the workflow. PowerShell command-by-command transcription also works but is multi-step and error-prone (hit the 25MB API limit last session, required a retry).

## Goal
A **local desktop app** that lives in the system tray. Hotkey → popup → paste URL → wait → get transcript + formatted worksheet. Zero browser tabs. Zero commands. Runs automations end-to-end. Uses Lober's Claude subscription instead of paid API for formatting.

---

## Locked-in Decisions

1. **Tech stack:** Electron (React frontend, Node main process, Python subprocess for yt-dlp/Whisper). Chosen over Tauri for maturity + AI training coverage after Lober's prior extension-build failures. Electron is open source (MIT), has full CLI tooling (`electron-forge`, `electron-builder`).
2. **Worksheet generation:** Claude via **Agent SDK using Lober's subscription** (OAuth, no API key). Zero per-call cost. Same pattern as AutoForge — see `docs/SUBSCRIPTION_AND_WEBSOCKET_GUIDE.md`.
3. **Transcription engine:** Local Whisper default (free). **Manual toggle** (not automatic) to switch to OpenAI Whisper API per-job or globally for speed. Paid only when user explicitly chooses.
4. **Storage:** Transcripts saved to user-chosen folder as `.md` files. Audio deleted immediately after transcription. No video downloads (same as YT Lab PRD).
5. **Upload size math:** App calculates compression bitrate **upfront** from video duration. Formula: `target_kbps = (25 × 8 × 1000) / duration_seconds × 0.9`. Compresses once, always lands under the 25MB API limit on first try. No retries.
6. **Format templates ("skills"):** Pluggable prompt library. User picks a template per-job OR leaves on auto-detect. Templates are editable, saveable, shareable.

---

## User Flow (Primary)

```
1. User sees a video somewhere (browser, phone pushed to desktop, etc.)
2. Copies URL to clipboard
3. Hits global hotkey (default: Ctrl+Shift+T)
4. Popup window appears (400x500px, centered)
5. URL field auto-fills from clipboard (or user pastes / drag-drops a file)
6. Dropdown: Format template (default: "Auto-detect")
7. Checkbox: "Use Whisper API (faster, costs ~50¢/hr)" — off by default
8. User hits Enter
9. Progress bar with phases:
   - Checking captions...
   - Downloading audio...
   - Compressing (target: X kbps)...
   - Transcribing...
   - Generating worksheet...
   - Done
10. Result view: Transcript (collapsible) + Worksheet (main view)
11. Buttons: Copy, Save As..., Send to YT Lab (if configured), Open in Editor
12. Close popup → icon stays in tray → ready for next video
```

## Secondary Flows

- **Tray icon menu:** Open popup / Recent transcriptions / Settings / Templates / Quit
- **Recent transcriptions:** Last 20 jobs, click to re-open worksheet
- **Settings:** API keys, default save folder, hotkey, default template, Whisper engine default
- **Templates:** List, edit, create, import, export

---

## Architecture

```
┌─────────────────────────────────────────────┐
│ Electron App                                │
│ ┌─────────────────────────────────────────┐ │
│ │ React Frontend (Renderer process)       │ │
│ │  - Popup window (URL input, progress)   │ │
│ │  - Tray menu                            │ │
│ │  - Settings / templates UI              │ │
│ └─────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────┐ │
│ │ Node Main Process                       │ │
│ │  - IPC between UI and backend           │ │
│ │  - Global hotkey registration           │ │
│ │  - File system (save transcripts)       │ │
│ │  - Claude Agent SDK (subscription auth) │ │
│ └─────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────┐ │
│ │ Python Subprocess (spawned on demand)   │ │
│ │  - yt-dlp (download / captions)         │ │
│ │  - ffmpeg (compress)                    │ │
│ │  - whisper local OR openai API client   │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

**Why Python subprocess:** yt-dlp, ffmpeg, and Whisper are all Python/CLI tools. Bundling them into Node is messy. Spawning Python from Electron main process is the clean pattern.

**Bundled dependencies (shipped with installer):**
- Python runtime (portable, ~50MB)
- yt-dlp binary
- ffmpeg binary
- Whisper (optional — user can install locally if they want the free path; API path has zero Python footprint)

Installer handles all of this. User double-clicks `Transcriber-Setup.exe`, done.

---

## Format Templates ("Skills") — Core Feature

### Template structure
```
{
  "id": "day-by-day-protocol",
  "name": "Day-by-Day Protocol",
  "description": "Good for: diet plans, routines, multi-day challenges",
  "detect_keywords": ["day 1", "day 2", "first day", "phase 1"],
  "prompt": "The following is a transcript of a video describing a multi-day protocol...
             Extract and organize by day. For each day include:
             - Rules / restrictions
             - Time windows (e.g. fasting hours, eating windows)
             - Allowed foods / actions
             - Forbidden foods / actions
             - Key warnings
             Format as markdown with clear day headers..."
}
```

### Default template library (ships with app)
| Template | Use case |
|---|---|
| Auto-detect | Claude picks the best format based on content |
| Day-by-day protocol | Diet plans, fasts, routines, multi-day challenges |
| Tool / feature breakdown | New AI tool announcements, product launches |
| Step-by-step tutorial | How-to videos, walkthroughs |
| Concept breakdown | Educational / explainer videos |
| SOP generator | "Turn this into a standard operating procedure" |
| Checklist | Flat actionable list |
| Raw transcript | No formatting — straight text |
| Meeting notes | Discussion → decisions + action items |

### User-created templates
- Save any output format as a reusable template
- Edit the underlying prompt
- Export template as JSON file to share
- Import templates from file or URL

### Auto-detect logic
When "Auto-detect" is chosen:
1. First 500 words of transcript + all template descriptions sent to Claude
2. Claude picks best-fit template
3. That template's prompt runs on full transcript
4. User sees which template was chosen, can click "Try different template" to re-run

---

## Claude Subscription Integration (Critical)

**Do NOT use the Anthropic API for worksheet generation.** Use Agent SDK with subscription auth.

Pattern (from AutoForge):
- Agent SDK handles OAuth flow on first launch
- User logs into Claude account once, token stored securely via Electron's safeStorage
- All subsequent Claude calls use that token
- Rate-limited by Lober's Max plan (60 hours Sonnet, 5.6 hours Opus daily) — no per-call dollar cost
- Reference: `docs/SUBSCRIPTION_AND_WEBSOCKET_GUIDE.md` and `docs/references/sdk-client-pattern.md`

**Model selection:**
- Default: Sonnet for worksheet generation
- Toggle: Opus (per-job) for deep reasoning tasks (e.g. "turn this into a tool spec")
- Same policy as YT Lab PRD

---

## Integration with YT Lab / AutoForge

Desktop app and YT Lab share the same backend logic. Two modes:

1. **Standalone (v1):** Desktop app is self-contained, saves to local files. No AutoForge dependency. Works even when AutoForge isn't running.
2. **Synced (v2):** "Send to YT Lab" button pushes the finished transcript + worksheet to the AutoForge server (running on localhost). Appears in YT Lab's history.
3. **SaaS (future):** Same desktop app flips a setting from "localhost" to a cloud URL. Works identically.

**The desktop app IS the brain. YT Lab is just the web-viewer brain. Same core engine.**

---

## Data Model

### Job (in-memory + local file log)
```
job {
  id                        // timestamp-based UUID
  source_url | source_file
  source_type               // detected type
  template_id               // which format template used
  whisper_engine            // "local" | "openai-api"
  model                     // "sonnet" | "opus"
  transcript_md_path        // where .md file is saved
  worksheet_md_path
  duration_seconds
  cost_usd                  // 0 if local, tracked if API
  created_at
  status
}
```

Stored in a local SQLite file or plain JSON log (`~/.transcriber/history.json`). SQLite recommended for scale; JSON for simplicity in v1.

### Template
```
template {
  id
  name
  description
  detect_keywords
  prompt
  is_default                // ships with app
  created_at
  updated_at
}
```
Stored in `~/.transcriber/templates.json`.

### Settings
```
{
  anthropic_auth: {...},    // managed by Agent SDK
  openai_api_key: "...",    // encrypted via safeStorage
  default_save_folder: "C:/Users/lober/Transcripts",
  default_template: "auto-detect",
  default_whisper_engine: "local",
  hotkey: "CommandOrControl+Shift+T",
  yt_lab_sync_url: null     // for v2 sync
}
```

---

## Build Segments

### Segment 1 — Core Flow (MVP)
Get URL-in → worksheet-out working with no polish.
- Electron scaffold + tray icon
- Popup window with URL input + progress bar
- Python subprocess integration
- yt-dlp + captions + Whisper local + Whisper API all wired
- Upfront bitrate math (no 25MB retries)
- Claude Agent SDK with subscription auth
- 3 default templates: Auto-detect, Day-by-day, Tool breakdown
- Save .md file on completion
- Manual "copy to clipboard" button

**Acceptance:**
- Paste YouTube URL with captions → get transcript + worksheet in 30 seconds
- Paste YouTube Live URL (no captions, short) → local Whisper transcribes → worksheet
- Paste YouTube Live URL (no captions, long) + API toggle on → Whisper API transcribes → worksheet in ~2 minutes
- Paste Twitter/X URL → works
- Upload mp3 file → works
- Worksheet output is formatted per chosen template

### Segment 2 — Polish
- Global hotkey (Ctrl+Shift+T)
- Settings UI (API keys, folders, defaults)
- Template editor (create / edit / delete)
- Recent transcriptions list in tray menu
- Progress bar with named phases
- Error handling with retry buttons
- Installer (`.exe` for Windows, `.dmg` for Mac)

### Segment 3 — YT Lab Sync (v2)
- "Send to YT Lab" button pushes to localhost AutoForge
- Reuse YT Lab history / batch views
- Auto-sync mode (every transcript also lands in YT Lab)

### Segment 4 — Mobile PWA Viewer (separate, linked PRD needed)
- Read-only worksheet viewer
- Syncs worksheets from desktop via Google Drive folder
- Day-by-day nav for multi-day protocols (defaults to today)
- Big text, spacious layout for repeated reading
- Install to phone home screen via PWA

See **"Mobile Viewer PWA" section** below for scoping.

---

## Mobile Viewer PWA (scoped separately)

**Premise:** Lober wants to reread worksheets (liver cleanse, diet plans, tool guides) on his phone, not edit them. Don't build a native app. Build a PWA that reads from a synced folder.

### Sync mechanism
- Desktop Transcriber app writes worksheets to a local folder
- User pairs that folder with **Google Drive** (free, terabytes, Lober already uses it)
- PWA reads from Google Drive via API (read-only)
- Zero custom backend

### Features (v1)
- List view: all worksheets, newest first, grouped by date
- Tag/folder filter: "Diet," "Tools," "Tutorials," etc. (user tags them manually or templates auto-tag)
- Detail view: big text, sectioned markdown, ideal for reading
- Day-by-day nav: if worksheet has day sections, defaults to today's day based on start date
- "Pin to top" for active references (the liver cleanse while it's running)
- Offline: service worker caches last 20 worksheets

### What it is NOT
- Not an editor (editing stays on desktop / web)
- Not a native app (no app store)
- Not connected to AutoForge directly (syncs via Drive)

### Build effort
- 1 week of focused building after desktop app is stable
- Separate PRD when the time comes

---

## Open Questions for Lober

1. **App name:** "Transcriber" is a placeholder. Suggestions: Scribe, Transcript.me, Grepscribe (matches Greptacular branding), VidToDoc, Paperize. Pick one or propose.
2. **Default hotkey:** `Ctrl+Shift+T` works on Windows but conflicts with "reopen closed tab" in most browsers. Alternatives: `Ctrl+Shift+V` (conflicts with paste-as-plain-text), `Ctrl+Alt+T`, `Win+T`. Pick one.
3. **Windows-only or cross-platform?** You mentioned your live install is Windows. Build Windows first, Mac later? Or both from day one? (Electron makes both easy but adds test surface.)
4. **Template auto-detect — show user which template was picked?** Yes/no/setting.
5. **Save format:** `.md` files (markdown — recommended, universal) or `.docx` (Word)? Or both? Recommendation: `.md` only, with a "copy as Word-compatible" button.
6. **History / recent jobs:** SQLite (robust, scales) or plain JSON (simple, readable). Recommendation: JSON for v1, migrate to SQLite if history grows past 1000 jobs.

---

## Non-Goals / Out of Scope (v1)

- Real-time live transcription (transcribe while the stream airs)
- Speaker diarization ("who said what")
- Video file save/storage (handle via Google Drive manually as needed)
- Multi-user / sharing
- AutoForge integration (Segment 3 — later)
- Mobile PWA (separate PRD, later)
- Translation to other languages (Whisper can do it; expose as v2 checkbox)

---

## Risk / Past Failure Notes

**Why this won't be another extension disaster:**
- Extensions fail because of browser sandbox. Desktop apps have NO sandbox — full system access for yt-dlp, ffmpeg, Whisper, file I/O
- Electron is battle-tested (VSCode, Slack, Discord). Massive training data for AI to produce working code
- The entire flow already works manually (we just did it). This just wraps existing working pieces in a GUI
- Single success criterion: "URL in, .md file out." Clear end state, easy to verify

**Known gotchas:**
- First-launch OAuth flow for Claude subscription needs careful UX (popup, redirect handling) — reference `docs/SUBSCRIPTION_AND_WEBSOCKET_GUIDE.md`
- Bundling Python + ffmpeg into installer adds ~80MB — acceptable
- Electron code-signing for Windows ($) and Mac (Apple dev account $99/yr) needed for clean installs. For personal use, unsigned is fine (user clicks "run anyway")
