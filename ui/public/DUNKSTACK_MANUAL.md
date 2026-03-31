# DunkStack User Manual

**Version 2.0 — March 2026**

DunkStack is your AI coding agent command center inside AutoForge. Think of it as a mission control dashboard where you talk to an AI agent, watch it work, control how autonomous it is, and manage its memory between sessions.

This manual is written for someone who isn't a coder. No jargon, no API references — just how to use the thing.

---

## Table of Contents

1. [What Is DunkStack?](#1-what-is-dunkstack)
2. [Getting Started](#2-getting-started)
3. [The Dashboard Layout](#3-the-dashboard-layout)
4. [Choosing Your AI Model](#4-choosing-your-ai-model)
5. [The Walkie-Talkie Chat](#5-the-walkie-talkie-chat)
6. [Starting and Stopping the Agent](#6-starting-and-stopping-the-agent)
7. [Control Modes — How Autonomous Is the Agent?](#7-control-modes--how-autonomous-is-the-agent)
8. [The Context Gauge — Tracking Token Usage](#8-the-context-gauge--tracking-token-usage)
9. [Safety System — The Three-Tier Shield](#9-safety-system--the-three-tier-shield)
10. [Session Bridging — Agent Memory Between Sessions](#10-session-bridging--agent-memory-between-sessions)
11. [The Right Panel — Files, Safety, Preview](#11-the-right-panel--files-safety-preview)
12. [Agent OS Integration](#12-agent-os-integration)
13. [The Orchestrator](#13-the-orchestrator)
14. [Dark Mode and Themes](#14-dark-mode-and-themes)
15. [Tips and Best Practices](#15-tips-and-best-practices)
16. [Troubleshooting](#16-troubleshooting)

---

## 1. What Is DunkStack?

DunkStack is a **file-based context management system**. In plain English:

- You talk to an AI coding agent through a chat interface
- The agent reads and writes files in a special `.agent/` folder inside your project
- You can control how much freedom the agent has (idle, continue, or full autopilot)
- You can track how much of the AI's "memory" (context window) has been used
- When a session ends, you can save a "bridge" file so the next session picks up where the last one left off

It's designed so you can run an AI agent on your project, communicate with it in real-time, and never lose context between sessions.

---

## 2. Getting Started

### Step 1: Start AutoForge

Double-click `start_ui.bat` (Windows) or run `./start_ui.sh` (Mac/Linux) from your Greptacular install folder. The server starts on `http://localhost:8888`.

### Step 2: Open DunkStack

In your browser, go to: **`http://localhost:8888/#/dunkstack`**

### Step 3: Create or Select a Project

**Left sidebar** shows all your projects. Click one to select it.

**To create a new project:**
1. Click the **+ New Project** button at the top of the sidebar
2. Type a name (it auto-formats to lowercase with hyphens)
3. Optionally attach an existing code repository by toggling "Attach existing repo" and browsing to the folder
4. Pick a model preset (more on this below)
5. Click **Create**

Your project is now ready. The system automatically creates the `.agent/` folder structure inside it.

### Step 4: Pick a Model and Start Chatting

Choose a model from the pills at the top of the page (see [Section 4](#4-choosing-your-ai-model)), then type a message in the chat area to start talking to the agent.

---

## 3. The Dashboard Layout

The DunkStack page has three main areas:

```
┌──────────┬─────────────────────────────┬──────────────┐
│          │                             │              │
│  Left    │       Center Area           │   Right      │
│  Sidebar │   (Chat / Agent OS view)    │   Panel      │
│          │                             │              │
│ Projects │                             │  Safety /    │
│  list    │    Walkie-Talkie Chat       │  Files /     │
│          │    or Agent OS workflow     │  Preview     │
│          │                             │              │
└──────────┴─────────────────────────────┴──────────────┘
```

### Top Bar (left to right)

| Element | What It Does |
|---------|-------------|
| **← Back arrow** | Returns to the main AutoForge dashboard |
| **Model preset pills** | Switch between AI models (Opus, Sonnet, Haiku) |
| **Context Gauge** | Shows how much of the AI's memory is used (color-coded bar) |
| **Reset Tokens** button | Clears the token counter back to zero |
| **Guide book icon** | Opens the built-in guide panel with tips |
| **Shield icon** | Opens the safety panel (3-tier protection system) |
| **File icon** | Opens the file viewer panel |
| **Globe icon** | Opens the live preview panel |
| **Agent OS icon** | Opens the Agent OS integration panel |
| **Sun/Moon icon** | Toggle dark mode |
| **Theme selector** | Choose a visual theme |

### Left Sidebar

- List of all your AutoForge projects
- Click a project to select it — all DunkStack features scope to that project
- **+ New Project** button to create projects inline
- Collapsible (click the chevron arrow)

### Center Area

This is where the main action happens. Two views:

1. **Chat view** (default) — The walkie-talkie conversation with the agent
2. **Agent OS view** — The structured product/spec workflow (intake, standards, features, specs)

Switch between them using the tabs at the top of the center area.

### Right Panel

Toggle between three panels using the icons in the top bar:

- **Safety** (shield) — Safety thresholds, control mode, agent status
- **Files** (file icon) — Browse files in the `.agent/` directory
- **Preview** (globe) — Live preview of your app (if it has a dev server)

---

## 4. Choosing Your AI Model

At the top of the page you'll see colored pills — these are your model presets:

| Preset | Color | Best For |
|--------|-------|----------|
| **Opus 4.6 · 200K** | Dark gray | Fast work on smaller codebases. Smartest model, smaller memory. |
| **Sonnet 4.6 · 200K** | Purple | Good balance of speed and smarts. Smaller memory. |
| **Haiku 3.5 · 200K** | Green | Quick, cheap tasks. Fastest model, good for simple edits. |
| **Opus 4.6 · 1M** | Blue | Large codebases that need the full context window. Smartest + most memory. |
| **Sonnet 4.6 · 1M** | Deep purple | Large codebases, cost-effective. Good balance + most memory. |

**What's the difference between 200K and 1M?**

The number is how much "memory" (context) the AI can hold at once. 200K is enough for most projects. 1M is for huge codebases where the agent needs to see a lot of files at once. 1M uses more of your hourly quota per request.

**How to switch:** Just click the pill. It updates immediately — both the UI gauge and the backend settings.

**All models run on your Claude subscription.** No API keys needed. No extra charges beyond your subscription.

---

## 5. The Walkie-Talkie Chat

The center panel is a **walkie-talkie style chat**. Here's how it works:

### Sending Messages

1. Type your message in the input box at the bottom
2. Press **Enter** or click the send button
3. Your message gets written to a file (`.agent/comms/from_human.md`) that the agent reads

### How It's Different from Regular Chat

This isn't a back-and-forth conversation like ChatGPT. It's more like a **walkie-talkie**:

- You send a message → it goes into a file
- The agent checks that file periodically (every ~30 seconds while running)
- The agent writes its responses to a different file (`.agent/comms/to_human.md`)
- The UI polls for new messages and displays them

This means there can be a short delay between when you send a message and when the agent sees it. That's normal.

### Message Types

Messages in the chat are color-coded:

| Color/Icon | Meaning |
|-----------|---------|
| **Your messages** | What you typed — sent to the agent |
| **Agent messages** | What the agent wrote back |
| **System messages** | Status updates (agent started, bridge saved, etc.) |

### Tips for Messaging

- **Be specific:** "Build the login page with email and password fields" works better than "build the login"
- **One task at a time:** The agent works best when focused on one thing
- **Check in:** If the agent seems stuck, send "status?" or "what are you working on?"
- **Course correct:** Send "stop what you're doing and focus on X" to redirect

---

## 6. Starting and Stopping the Agent

### Starting the Agent

1. Select a project from the left sidebar
2. Choose your model preset
3. Click the **▶ Start** button (green play icon in the control bar)
4. The agent boots up, reads the project files, and starts working

The button shows a spinning loader while the agent is starting up.

### Stopping the Agent

Click the **■ Stop** button (red square icon). The agent will:
1. Finish its current thought
2. Save its state
3. Shut down cleanly

### Agent Status Indicators

The control bar shows the current agent status:

| Status | Meaning |
|--------|---------|
| **Idle** | Agent is not running |
| **Starting** | Agent is booting up |
| **Running** | Agent is actively working |
| **Stopped** | Agent was stopped |
| **Error** | Something went wrong (check the chat for details) |

---

## 7. Control Modes — How Autonomous Is the Agent?

The control mode determines how much freedom the agent has. Set it in the Safety panel (shield icon):

| Mode | What It Does | When to Use |
|------|-------------|-------------|
| **Idle** | Agent waits for your instructions after each task. It does one thing, then stops and waits for you to say what's next. | When you want full control. Good for learning or sensitive work. |
| **Continue** | Agent automatically picks up the next feature after finishing one. Still pauses for your input on big decisions. | Normal day-to-day work. The agent stays productive but you stay in the loop. |
| **Autopilot** | Full autonomous mode. Agent works through the entire feature backlog without stopping. | When you trust the agent and want maximum speed. Walk away and come back to finished features. |

**To change modes:** Open the Safety panel (shield icon in the top bar) → click the mode you want.

**You can change modes while the agent is running.** Switch from Autopilot to Idle if you want it to pause after the current task.

---

## 8. The Context Gauge — Tracking Token Usage

The colored bar at the top of the page shows how much of the AI's "context window" (memory) has been used in the current session.

### The Color Zones

| Zone | Color | Meaning |
|------|-------|---------|
| **0-40%** | 🟢 Green | All good. Plenty of room. |
| **40-70%** | 🟡 Yellow | Getting up there. Agent should start being more concise. |
| **70-85%** | 🟠 Orange | Warning zone. Agent should wrap up current work and save state. |
| **85-100%** | 🔴 Red | Critical. Agent must stop and do a handoff immediately. |

### What Happens at Each Threshold

The safety system automatically responds based on the gauge:

- **40% (Warning)** — The agent gets a gentle nudge to be more efficient with context
- **45% (Handoff)** — The agent starts writing a bridge file to preserve its knowledge
- **50% (Hard Stop)** — The agent must stop coding, commit everything, and save a complete handoff

### Reset Tokens

Click the **"Reset"** button next to the gauge to zero out the counter. Use this when:
- Starting a fresh session on the same project
- The counter seems wrong after a restart
- You loaded a bridge from a previous session and want clean tracking

---

## 9. Safety System — The Three-Tier Shield

The safety panel (click the shield icon in the top bar) shows the current safety status and lets you adjust settings.

### Three Safety Tiers

| Tier | Trigger | What Happens |
|------|---------|-------------|
| **Warning** | Context hits 40% | Agent is notified, starts being more concise |
| **Handoff** | Context hits 45% | Agent begins saving state to bridge file |
| **Hard Stop** | Context hits 50% | Agent stops all work, saves everything, exits |

### Safety Panel Shows

- **Current safety tier** — Which zone you're in (green/yellow/orange/red)
- **Control mode** — Current mode (idle/continue/autopilot) with buttons to change
- **Agent status** — Whether the agent is running, stopped, or errored
- **Token usage** — Numeric breakdown of tokens used vs. limit

### Why These Thresholds Exist

AI models have a fixed context window. If the agent uses it all up without saving state, all its knowledge about your project is lost. The safety system ensures the agent always saves before running out of room.

---

## 10. Session Bridging — Agent Memory Between Sessions

When an AI session ends (either by hitting context limits or being stopped), the agent loses its memory. **Bridge files** solve this.

### What's a Bridge File?

A bridge file (`.agent/bridge.md`) is a summary the agent writes before ending a session. It contains:
- What the agent was working on
- What's done and what's still pending
- Key decisions made
- Known issues or blockers
- Where to pick up next time

### Saving a Bridge

The agent saves bridges automatically when:
- The context gauge hits the handoff threshold (45%)
- You stop the agent cleanly

You can also manually trigger a bridge save from the UI controls.

### Loading a Previous Bridge

When starting a new session, you can load a bridge from a previous session:

1. Before clicking Start, look for the **bridge selector** dropdown (appears when bridges exist)
2. Click it to see a list of saved bridges with timestamps
3. Select the one you want — the agent will read it on startup
4. Click Start — the new session continues where the old one left off

### Bridge History

Every bridge save creates a timestamped copy (`bridge-<timestamp>.md`) so you never lose previous saves. The list shows all available bridges ordered by date.

---

## 11. The Right Panel — Files, Safety, Preview

Toggle between three panels using the icons in the top bar:

### Files Panel (📄 icon)

Browse the `.agent/` directory for your project. See what files the agent has created or modified:

- `comms/` — Communication files (to_human.md, from_human.md, control.md)
- `progress/` — Build log
- `knowledge/` — Context primer and research
- `product/` — Vision, users, use cases, roadmap (if using Agent OS)
- `specs/` — Feature specifications
- `settings/` — Configuration

### Safety Panel (🛡 icon)

See [Section 9](#9-safety-system--the-three-tier-shield) above.

### Preview Panel (🌐 icon)

If your project has a dev server running, this panel shows a live preview of your app embedded in an iframe. Useful for watching the agent's changes appear in real-time.

---

## 12. Agent OS Integration

DunkStack includes an integrated **Agent OS** workflow for structured product development. Access it by clicking the Agent OS icon (✨ sparkles) in the top bar.

### What Agent OS Does

Agent OS takes you through a structured process to go from "I have an idea" to "here's a full spec the coding agent can build":

1. **Intake** — Upload or describe your project idea
2. **Standards** — Define tech stack, coding style, quality bars
3. **Product Discovery** — Vision, target users, use cases, roadmap
4. **Gap Analysis** — Find holes in the spec before building
5. **Feature Specs** — Detailed specifications for each feature
6. **Handoff** — Package everything for the coding agent

### How to Use It

1. Click the Agent OS icon in the top bar
2. The center view switches to the Agent OS workflow
3. Follow the guided steps from intake through handoff
4. When done, switch back to Chat view — the agent now has full specs to work from

---

## 13. The Orchestrator

For larger projects, DunkStack includes an **orchestrator** that manages multi-agent workflows. Access it through the dedicated tabs when a project is selected.

### Orchestrator Tabs

| Tab | What It Shows |
|-----|-------------|
| **Action Log** | Real-time feed of what the agent is doing (thinking, writing, testing) |
| **Checkpoints** | Timeline of saved checkpoints (commit snapshots) |
| **Verifications** | History of test runs and verification results |
| **Commits** | Git commits made by the agent |
| **Approvals** | Pending approval requests from the agent (when it needs your OK) |

### Approval Banner

When the agent needs your permission to do something (like make a breaking change), an approval banner appears at the top. Click **Approve** or **Reject** to respond.

---

## 14. Dark Mode and Themes

### Dark Mode

Click the **Sun/Moon icon** in the top bar to toggle between light and dark mode. Your preference is saved.

### Themes

Click the **theme selector** (palette icon) to choose from available visual themes. Themes change the color scheme and visual style of the entire dashboard.

---

## 15. Tips and Best Practices

### For Best Results

1. **Start with a spec.** Use Agent OS to create a proper spec before asking the agent to build. Agents with specs build better code.

2. **Use Opus for complex work, Sonnet for routine work, Haiku for quick fixes.** Don't burn Opus quota on simple tasks.

3. **Save bridges often.** If you're doing a long session, manually save a bridge before you walk away. The auto-save at 45% is your safety net, not your strategy.

4. **Start in Idle mode, graduate to Continue.** Learn how the agent works before giving it full autonomy. Once you trust it on your project, switch to Continue for productivity.

5. **One project at a time.** DunkStack scopes everything to the selected project. If you need to switch projects, select the new one from the sidebar — all state updates accordingly.

6. **Check the gauge.** If you're approaching 40%, consider whether to push through or start a new session with a bridge. Agents get less effective as context fills up.

### Common Mistakes to Avoid

- **Don't give vague instructions.** "Make it better" doesn't help. "Add error handling to the login form" does.
- **Don't ignore the context gauge.** Running out of context mid-task means lost work.
- **Don't switch models mid-session.** Finish the current task, save a bridge, then start fresh with the new model.
- **Don't run multiple DunkStack tabs.** One browser tab per project. Multiple tabs create conflicting WebSocket connections.

---

## 16. Troubleshooting

### The chat isn't showing any messages

1. Check that you've selected a project in the left sidebar
2. Check that the server is running (`start_ui.bat`)
3. Try a hard refresh: **Ctrl+Shift+R**

### The agent won't start

1. Make sure no other agent is running on the same project (check the agent status indicator)
2. Try stopping any running agent first, then start fresh
3. Check the server console for error messages

### The context gauge seems stuck or wrong

Click **Reset Tokens** to zero it out. The gauge reads from the backend — if the server restarted, the count might be stale.

### Messages aren't reaching the agent

The walkie-talkie system has a natural delay (up to ~30 seconds). If messages still aren't getting through after a minute:
1. Check the `.agent/comms/from_human.md` file in the Files panel — your messages should appear there
2. If they're not there, the write is failing — try refreshing the page

### The bridge selector is empty

Bridges are only created when the agent saves one. If you've never run the agent or it was hard-stopped before saving, there won't be any bridges yet.

### "Hard stop" notification appeared

This means the agent hit the 50% context threshold and was forced to stop. Your work is safe — the agent commits and saves a bridge before stopping. Start a new session and load the bridge to continue.

### Server crashed or computer restarted

1. Run `start_ui.bat` from your Greptacular install folder
2. Open `http://localhost:8888/#/dunkstack`
3. **Ctrl+Shift+R** to force-refresh the browser
4. Select your project — the `.agent/` files are still there, nothing is lost

---

## Quick Reference Card

| Action | How |
|--------|-----|
| Open DunkStack | `http://localhost:8888/#/dunkstack` |
| Create a project | + New Project button in sidebar |
| Switch models | Click a model pill in the top bar |
| Send a message | Type in chat box, press Enter |
| Start the agent | Click ▶ (play button) |
| Stop the agent | Click ■ (stop button) |
| Change control mode | Shield icon → pick Idle/Continue/Autopilot |
| Save a bridge | Automatic at 45%, or manual via UI |
| Load a bridge | Bridge selector dropdown → pick one → Start |
| Toggle dark mode | Sun/Moon icon in top bar |
| Reset token counter | "Reset" button next to context gauge |
| View agent files | File icon in top bar |
| Live preview | Globe icon in top bar |
| Open safety panel | Shield icon in top bar |
| Open guide | Book icon in top bar |

---

*This manual covers DunkStack as of March 2026. Features may be added or changed in future updates.*
