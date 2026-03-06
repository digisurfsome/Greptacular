# Operational Plan: Multi-App Architecture with Skills, MD Segmentation & CLI Dashboard

## Current State

### 5 Apps (hash-routed in one React codebase)

| App | Route | Page File | Purpose |
|-----|-------|-----------|---------|
| AutoForge | `/#/` | `App.tsx` | Factory for making apps (core) |
| DunkStack | `/#/dunkstack` | `DunkStackPage.tsx` | Context tracking, token budgeting |
| IdeaForge Workspace | `/#/workspace` | `WorkspacePage.tsx` | Multi-conversation coding workspace |
| Multi-Session Dashboard | `/#/dashboard` | `DashboardPage.tsx` | 1-3 AI sessions side-by-side |
| YT Strategy Lab | `/#/yt-lab` | `YTStrategyLabPage.tsx` | YouTube strategy extraction |

### Current Skills (`.claude/skills/`)

18 skills available: algorithmic-art, brand-guidelines, canvas-design, doc-coauthoring, docx, frontend-design, gsd-to-autoforge-spec, internal-comms, mcp-builder, pdf, pptx, skill-creator, slack-gif-creator, theme-factory, web-artifacts-builder, webapp-testing, xlsx

### Current Agents (`.claude/agents/`)

3 agents: coder (orange), code-review (red), deep-dive (purple)

### Current Commands (`.claude/commands/`)

6 slash commands: /create-spec, /expand-project, /review-pr, /check-code, /checkpoint, /gsd-to-autoforge-spec

---

## PART 1: Per-App MD Files

### Problem
One CLAUDE.md covers AutoForge only. Agents working on DunkStack/Dashboard/Workspace/YT Lab lack focused context.

### Solution
Each app gets a lightweight MD file (~100-200 lines) alongside its page file:

```
ui/src/pages/
├── DUNKSTACK.md
├── DunkStackPage.tsx
├── WORKSPACE.md
├── WorkspacePage.tsx
├── DASHBOARD.md
├── DashboardPage.tsx
├── YTLAB.md
└── YTStrategyLabPage.tsx
```

### MD File Template

Each file contains:
1. **Identity** — What this app IS (2-3 sentences)
2. **Components** — Files/components belonging to this app
3. **Patterns** — State management, data storage, hooks
4. **Skill Recommendations** — Relevant skills with estimated context cost
5. **Anti-Patterns** — What NOT to touch from this context
6. **Voice/Personality** — Agent communication style for this domain

---

## PART 2: Skills "Tool Shed"

### Skill Manifest (embedded in each per-app MD)

```markdown
## Skill Shed

### Always Available (low cost)
- check-code — lint/typecheck (tiny footprint)
- checkpoint — commit workflow

### Recommended For This App
- frontend-design — UI work (~8% context)
- webapp-testing — testing interactions (~5% context)

### Context Budget Guide
- 1-2 skills: Ideal
- 3-4 skills: Workable
- 5+: NOT recommended
```

### Suggestion Flow
1. User describes task
2. Agent reads per-app MD, sees relevant skills
3. Agent suggests 1-2 skills with context cost estimate
4. User approves/declines
5. Agent proceeds

---

## PART 3: CLI-to-Dashboard Mapping

### A. Agent Configuration
| CLI | Dashboard Control |
|-----|-------------------|
| Model selection (`--model`) | Model dropdown |
| Agent roles (`.claude/agents/`) | Agent role picker cards |
| Max turns | Turn limit slider |
| System prompt override | Prompt editor with templates |

### B. Session Controls
| CLI | Dashboard Control |
|-----|-------------------|
| Planning mode (`/plan`) | Toggle switch |
| YOLO mode (`--yolo`) | Lightning bolt button |
| Auto-continue | Toggle with delay slider |
| `/compact` | Compact button in toolbar |
| `/clear` | Clear button with confirmation |

### C. Skills & Commands
| CLI | Dashboard Control |
|-----|-------------------|
| `/check-code` | One-click lint/typecheck button |
| `/checkpoint` | Commit button → message editor |
| `/review-pr` | PR review button → PR selector |
| Skill loading | Skill shelf panel with toggles |

### D. Hooks & Automation
| CLI | Dashboard Control |
|-----|-------------------|
| Pre/post-tool hooks | Hook editor with enable/disable |
| Notification hooks | Toggle per event type |
| Custom bash hooks | Script editor with test button |

### E. MCP Servers
| CLI | Dashboard Control |
|-----|-------------------|
| MCP server config | Server list: add/remove/configure |
| Server status | Green/red dots per server |
| Tool permissions | Checkbox matrix per server |

### F. Context Management
| CLI | Dashboard Control |
|-----|-------------------|
| CLAUDE.md editing | In-app MD editor per app |
| `.claudeignore` | Pattern editor with file browser |
| Context window usage | Context gauge (DunkStack has this) |
| Extra read paths | Path list editor with folder browser |

### G. Templates & Presets
| CLI | Dashboard Control |
|-----|-------------------|
| Prompt templates | Template library grid |
| Workflow presets | One-click preset dropdown |
| Save config as preset | Save Preset button |
| Import/export | JSON file import/export buttons |

---

## PART 4: Template & Preset System

### Individual Settings (granular)
- Model: `[Opus ▾]`
- Agent Role: `[Coder ▾]`
- Skills: `[frontend-design ✓] [theme-factory ✓]`
- Planning Mode: `[ON/OFF]`
- YOLO Mode: `[ON/OFF]`

### Workflow Presets (one-click)
- **Frontend Build** → Opus + Coder + frontend-design + theme-factory + planning ON
- **Bug Hunt** → Opus + Deep Dive + webapp-testing + check-code + planning OFF
- **Quick Prototype** → Sonnet + Coder + YOLO ON + no skills
- **Code Review** → Opus + Code Review + check-code + review-pr
- **Documentation** → Sonnet + doc-coauthoring + planning ON

### Storage
JSON in localStorage (or SQLite for server-side persistence):
```json
{
  "name": "Frontend Build",
  "model": "opus",
  "agent": "coder",
  "skills": ["frontend-design", "theme-factory"],
  "planningMode": true,
  "yolo": false
}
```

---

## PART 5: Planning Mode & Voice-Friendly UX

### Planning Mode Toggle
- Toggle in chat header: `[Plan Mode: ON/OFF]`
- ON: Agent asks clarifying questions before coding
- OFF: Agent goes straight to implementation

### Multi-Question UI (voice-friendly)
```
┌──────────────────────────────────┐
│ Q1: What framework? [React  ▾]  │
│                       [Next ►]  │
├──────────────────────────────────┤
│ Q2: Auth method?   [________]   │  ← focus here
│                       [Next ►]  │
├──────────────────────────────────┤
│ Q3: Database?      [________]   │
│                       [Next ►]  │
├──────────────────────────────────┤
│           [Submit All Answers]   │
└──────────────────────────────────┘
```

### Voice Shortcut Words (configurable)
- "next" → advance to next question
- "send" → submit answer(s)
- "skip" → skip current question
- "plan" → toggle planning mode
- "commit" → trigger checkpoint

---

## PART 6: Execution Tasks (in order)

### Phase 1 — Foundation

**Task 1: Create Per-App MD Files**
Create segmented CLAUDE.md override files for each of the 4 non-AutoForge apps (DunkStack, Workspace, Dashboard, YT Lab). Each MD file goes alongside the page file. Each MD should contain: (1) App identity and purpose in 2-3 sentences, (2) List of all components/files belonging to this app, (3) State management patterns and data storage approach, (4) Recommended skills from .claude/skills/ with estimated context cost, (5) Anti-patterns — what code/areas to NOT touch from this context, (6) Agent personality and communication style for this app's domain. Keep each file under 200 lines.

**Task 2: Build the Settings/Config Panel Template**
Create a reusable settings panel component embeddable in any of the 4 dashboard apps. Tabs/sections for: Model Selection, Agent Role, Skills (toggle list with context cost badges), Session Settings (Planning/YOLO/Auto-Continue/turn limit), Hooks (enable/disable toggles). Use existing SettingsModal.tsx as styling reference. Collapsible, neobrutalism design. Store settings in localStorage keyed by app name.

### Phase 2 — Core Features

**Task 3: Build the Template/Preset System**
Add preset system to settings panel: "Save as Preset" button, "Presets" dropdown, 5 built-in defaults (Frontend Build, Bug Hunt, Quick Prototype, Code Review, Documentation), Import/Export as JSON, Delete/rename for user presets. Store in localStorage.

**Task 4: Build Planning Mode Toggle & Multi-Question UI**
Planning Mode toggle in chat header. When ON and AI responds with multiple questions: render as individual cards with text inputs and "Next" buttons, "Submit All" at bottom, Tab advances, Ctrl+Enter submits. When OFF, questions render inline.

**Task 5: Voice Shortcut System**
Configurable voice shortcut system for chat. Watches input for trigger words, executes mapped actions, clears field. Settings sub-panel for editing trigger words. Visual indicator showing voice shortcuts active.

### Phase 3 — Full Integration

**Task 6: Skill Shelf Panel**
"Skill Shelf" sidebar panel listing all skills from .claude/skills/. Cards with name, description, context cost estimate. Grouped by app relevance (from per-app MD). Running "Context Budget" bar at top (yellow at 15%, red at 25%). Warning when over 25%. "Suggest Skills" button.

**Task 7: CLI Capability Dashboard**
Full "CLI Controls" panel with sections: Session, Skills & Commands, Hooks, MCP Servers, Context, Security. This is the master template reused across all apps.

**Task 8: Replicate Across All Apps**
Integrate CLI Controls into all 4 non-AutoForge apps as an openable side panel (gear icon or keyboard shortcut). Per-app scoped settings. Styling adapts per app theme.
