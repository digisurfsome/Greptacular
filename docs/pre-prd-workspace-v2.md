# Pre-PRD: Workspace V2 — One Agent Per Page

## What This Document Is

This is the discovery/design document for rebuilding the AutoForge Workspace page. It captures every decision made, explains the architecture in plain language, and serves as the foundation for the specs-level PRD that follows.

**Date:** March 10, 2026
**Status:** Pre-PRD (design decisions captured, ready for specs)

---

## The Problem

The current workspace page tries to run 3+ simultaneous WebSocket connections on one page (split-view with Research/PRD/Coder panels plus a Swarm panel for 5+ concurrent agents). This causes:
- WebSocket instability and connection failures
- Complexity that makes bugs hard to fix
- Every edit creates new problems because everything is intertwined
- The page is unreliable as a daily driver

## The Solution (One Sentence)

Each chat is its own page with its own single WebSocket connection, and a shared sidebar provides navigation between all pages — identical to how Claude Code web works, but built on separate routes for maximum simplicity.

---

## Core Architecture Decision

### Why Separate Pages, Not Tabs on One Page

| Approach | How it works | Risk |
|----------|-------------|------|
| Tabs (rejected) | One page, swap which chat is visible. Disconnect/reconnect WebSocket on tab switch. | Tab switching logic, cleanup bugs, shared state leaks |
| **Separate pages (chosen)** | Each chat is its own URL route. Navigate between them like regular web pages. | None. Each page is independent. Zero shared state. |

The separate pages approach means:
- Each page loads fresh with its own WebSocket lifecycle
- No disconnect/reconnect juggling
- No shared state between pages
- If one page has a bug, other pages are unaffected
- The sidebar is just a navigation component — links, not state management

### The Illusion

It looks like one app with a sidebar (just like Claude Code web). In reality, each chat is a completely independent page. The consistent sidebar framing creates the illusion of a single-page app while keeping the backend dead simple.

---

## Page Structure

### Three Route Types

```
/#/workspace              → Redirects to most recently used chat page
/#/workspace/all          → Organizational page (browse all, search, sort)
/#/workspace/:chatId      → Individual chat page (one agent, one socket)
/#/workspace-legacy       → Old workspace page (preserved for reference)
```

### The Chat Page (`/#/workspace/:chatId`)

The main workhorse. Each chat page has:

**Left sidebar (shared across all pages):**
- "New Page" button at top
- Sort dropdown
- List of all chat pages as navigation buttons
- "All Pages" link at bottom
- Each button shows: name, date/time, model info, context usage

**Main area:**
- Single WorkspaceChat component (already built, no modifications needed)
- One WebSocket connection
- One agent
- One conversation

**Setup flow (first time only):**
- When a new page is created, user MUST name it (no auto-naming)
- User picks model (Opus/Sonnet) and context mode (200K/1M)
- User picks repo/working directory
- User picks provider (Claude/Codex/Gemini)
- Once first message is sent, these settings lock permanently for this page

### The Home Route (`/#/workspace`)

Not a page itself — just a redirect. Checks localStorage for the last visited chat page ID and navigates there immediately. If no previous page exists, creates a new one and goes there.

### The Organizational Page (`/#/workspace/all`)

A browse/search page for when you have many chat pages and need to find something:
- All chat pages displayed as cards
- Search bar that searches across page names
- Sort/filter controls
- Click a card → navigates to that chat page
- This is NOT the default landing — it's accessed from the sidebar link

### The Legacy Page (`/#/workspace-legacy`)

The original WorkspacePage.tsx preserved at its own route. No modifications — it's a living reference of all the components that were built (split-view, swarm, factory, passoff, library). Can be visited anytime to jog memory about existing work and pull ideas for future features.

---

## Sidebar Navigation Buttons — Detailed Design

Each chat page appears in the sidebar as a button/card with this information:

### Layout Per Button

```
┌─────────────────────────────┐
│  My Opus Build              │  ← User-given name
│  MON 3/10/26  2:58 PM       │  ← Day (3-4 letter abbrev) + date + time (12hr)
│  Opus 4.6 · 1M · 43K ████░ │  ← Model · context mode · live usage + bar
└─────────────────────────────┘
```

**Name:** User-typed name (required at creation). Can be renamed later.

**Date/Time format:**
- Day: MON, TUE, WED, THU, FRI, SAT, SUN
- Date: M/DD/YY (e.g., 3/10/26)
- Time: H:MM PM/AM (e.g., 2:58 PM)
- Shows creation date OR last used date (based on current sort mode)

**Model info line:**
- Model name abbreviated: "Opus 4.6" or "SON 4.6" for Sonnet
- Context mode: "200K" or "1M"
- Current context usage: "43K" (live for active page, last-known for inactive)
- Optional: small visual bar showing context fill percentage

**Provider indicator:**
- Color-coded or icon-coded: Claude (default), Codex, Gemini
- Subtle — doesn't dominate the button, but scannable at a glance

**Active page indicator:**
- The currently viewed page is highlighted (different background or border)

### Context Window Number — How It Works

This is the killer feature. At a glance, you see how "full" each conversation is.

- **Active page:** Live number from WebSocket `token_usage` events (updates in real-time as tokens flow)
- **Inactive pages:** Last-known number saved to localStorage when you navigated away
- **Display:** Just the number in thousands (e.g., "43K", "87K", "112K")
- **Visual bar (optional):** Small progress bar showing fill relative to context mode (43K out of 1M = barely filled, 87K out of 200K = almost full)

This lets the user instantly decide: "My current chat is at 87K on a 200K model — I'll start a new page for this big idea instead of cramming it in here."

---

## Sorting System

### Default Sort: Last Used

The most recently interacted-with page goes to the top. When you send a message in a page, its "last used" timestamp updates and it floats to the top of the sidebar.

### Available Sort Options

| Sort Option | What it does | When you'd use it |
|-------------|-------------|-------------------|
| **Last Used** (default) | Most recently messaged page first | Daily driving — "where was I?" |
| **Date Created** | Newest created page first | "What did I start recently?" |
| **By Provider** | Group by Claude → Codex → Gemini | "Show me all my Codex chats" |
| **By Model** | Group by Opus → Sonnet → other | "Where are my Opus conversations?" |
| **By Context Usage** | Highest context first | "Which chats are almost full?" |

### Sort UI

Simple dropdown at the top of the sidebar: `Sort: [Last Used ▼]`

Click to change sort. Selection persists to localStorage.

---

## Page Creation Flow

### Step-by-Step

1. User clicks "+ New Page" (sidebar or organizational page)
2. Modal pops up with setup form:
   - **Name** (required text field — user MUST type something)
   - **Provider** dropdown: Claude / Codex / Gemini
   - **Model** dropdown: changes based on provider (Claude → Opus 4.6 / Sonnet 4.6, etc.)
   - **Context Mode**: 200K / 1M
   - **Repo/Working Directory**: folder browser or text input for path
3. User fills out form, clicks "Create"
4. New page is created and navigated to
5. Settings are locked for this page — shown in sidebar button but not editable

### Why Force Naming

Auto-naming (like Claude Code web does) creates names like "Help me build a React component for..." that are impossible to scan. The user hates this. Forcing a manual name means:
- "IdeaVault Build" not "Help me create an app that stores my ideas..."
- Scannable at a glance in the sidebar
- User can use whatever shorthand makes sense to them
- Can rename later if needed

### Settings Lock

Once the first message is sent (or immediately after creation), the provider/model/repo settings lock. This prevents:
- Accidentally changing models mid-conversation
- Confusion about which model a conversation is using
- The complexity of model-switching logic

The locked settings are displayed in the sidebar button (model + context mode) but cannot be changed.

---

## Technical Architecture

### What Gets Built (New)

| Component | What It Is | Estimated Size |
|-----------|-----------|---------------|
| `WorkspacePage.tsx` | New simplified page with sidebar + routing | ~250 lines |
| `WorkspaceSidebarV2.tsx` | New sidebar with nav buttons, sort, context display | ~200 lines |
| `WorkspaceAllPages.tsx` | Organizational/search page | ~150 lines |
| `PageSetupModal.tsx` | Creation modal (name + model + repo) | ~100 lines |
| Route config updates | Add new routes in App.tsx | ~20 lines |

**Total new code: ~720 lines**

### What Gets Reused (No Modifications)

| Component | Why It Stays Untouched |
|-----------|----------------------|
| `WorkspaceChat.tsx` (~1000 lines) | Already works perfectly for single conversations |
| `useWorkspaceChat.ts` (~400 lines) | Already manages one WebSocket connection correctly |
| `server/routers/workspace.py` | Backend WebSocket endpoint — already handles single sessions |
| `server/services/background_session_manager.py` | Session lifecycle — already works |
| All other backend files | Zero backend changes needed |

### What Gets Preserved (Legacy)

| Component | Action |
|-----------|--------|
| `WorkspacePage.tsx` (current) | Renamed to `WorkspacePageLegacy.tsx`, routed to `/#/workspace-legacy` |
| `WorkspaceSidebar.tsx` (current) | Kept in place — legacy page still imports it |
| `SwarmPanel.tsx` | Kept in place — legacy page still imports it |
| `FactoryPanel.tsx` | Kept in place — legacy page still imports it |
| `PassoffEditor.tsx` | Kept in place — legacy page still imports it |
| `WorkspaceLibrary.tsx` | Kept in place — legacy page still imports it |

Nothing gets deleted. The old page and all its components stay in the codebase, accessible at the legacy route.

### Data Storage (Phase 1: localStorage)

All page metadata stored in localStorage:

```json
{
  "workspace_pages": [
    {
      "id": "chat-1710000000",
      "name": "IdeaVault Build",
      "conversationId": 42,
      "provider": "claude",
      "model": "claude-opus-4-6",
      "contextMode": "1m",
      "workingDirectory": "C:/Projects/ideavault",
      "createdAt": "2026-03-10T14:58:00Z",
      "lastUsedAt": "2026-03-10T15:43:00Z",
      "lastKnownTokens": 43000,
      "lastKnownBudget": 1000000
    }
  ],
  "workspace_last_page": "chat-1710000000",
  "workspace_sort": "lastUsed"
}
```

**Future upgrade (Phase 2):** Move to SQLite database for persistence, search across message content, unlimited pages with archival. But that's a separate build — localStorage is fine for now.

---

## WebSocket Architecture (How It Connects)

### One Page = One Socket

Each chat page creates exactly ONE WebSocket connection to `ws://localhost:8888/api/workspace/ws`.

```
Chat Page "IdeaVault Build" (/#/workspace/chat-1)
  └→ useWorkspaceChat hook
      └→ WebSocket: ws://localhost:8888/api/workspace/ws
          └→ BackgroundSession (server-side)
              └→ WorkspaceChatSession
                  └→ Claude CLI subprocess (subscription auth)
```

When you navigate to a different chat page, the current page unmounts (WebSocket disconnects naturally via React cleanup). The new page mounts and creates its own WebSocket.

No juggling. No manual disconnect. React's component lifecycle handles it.

### Auth Flow for Claude (Subscription — No API Cost)

```
Page mounts → useWorkspaceChat opens WebSocket
  → Sends "start" message with provider: "claude"
  → Backend creates BackgroundSession
  → BackgroundSession creates WorkspaceChatSession
  → WorkspaceChatSession calls get_effective_sdk_env(force_subscription=True)
  → SDK env clears API key, uses ~/.claude/.credentials.json (OAuth)
  → Claude CLI starts with subscription auth
  → Zero API cost
```

### Auth Flow for Codex/Gemini

```
Page mounts → useWorkspaceChat opens WebSocket
  → Sends "start" message with provider: "codex" (or "gemini")
  → Backend creates BackgroundSession with provider-specific config
  → Uses provider's auth mechanism (API key from settings)
```

### WebSocket Message Protocol

**Starting a new conversation:**
```
CLIENT → { type: "start", conversation_id: null, working_directory: "...",
           context_mode: "1m", model: "claude-opus-4-6", provider: "claude" }
SERVER → { type: "session_created", session_id: "abc", conversation_id: 42 }
```

**Sending a message:**
```
CLIENT → { type: "message", content: "Build me a todo app" }
SERVER → { type: "text", content: "..." }           // streamed chunks
SERVER → { type: "tool_call", tool: "Write", ... }  // tool use
SERVER → { type: "token_usage", total: 15000, budget: 1000000 }
SERVER → { type: "session_completed" }
```

**Resuming an existing conversation (navigating back to a page):**
```
CLIENT → { type: "attach", session_id: "abc", since_seq: 0 }
SERVER → { type: "attached", session_id: "abc", state: "running" }
SERVER → { type: "replay", events: [...] }
SERVER → { type: "replay_done", current_seq: 47 }
```

**Token usage events (for context window display):**
```
SERVER → { type: "token_usage", total: 43000, budget: 1000000, model: "claude-opus-4-6" }
```

The frontend reads `total` and `budget` from these events to display the context window number in the sidebar.

---

## Provider Support

### Supported Providers (Phase 1)

| Provider | Models Available | Auth Method | Context Modes |
|----------|-----------------|-------------|---------------|
| Claude | Opus 4.6, Sonnet 4.6 | Subscription (no API cost) | 200K, 1M |
| Codex | (configured in settings) | API key | Varies |
| Gemini | (configured in settings) | API key | Varies |

### How Provider Affects the Page

When creating a page, the provider selection determines:
- Which models appear in the model dropdown
- Which auth method the backend uses
- The sidebar icon/color for that page

Provider is locked after page creation. If you want a different provider, create a new page.

---

## What the Legacy Page Preserves

The old `WorkspacePageLegacy.tsx` at `/#/workspace-legacy` keeps ALL of these accessible:

- **Split-view 3-panel layout** (Research + PRD + Coder)
- **PassoffEditor** (document passing between panels)
- **SwarmPanel** (multi-agent orchestration)
- **FactoryPanel** (phased agent pipeline)
- **WorkspaceLibrary** (file library + walkie-talkie log)
- **Auto-forward** (chain outputs between panels)
- **CountdownTimerBar** (walkie-talkie timeout)
- **Per-panel model selection** (3 independent model configs)
- **Keyboard shortcuts** for all the above

All these components remain in the codebase, importable, and visually inspectable. When the time comes to rebuild any of them in simpler formats, the legacy page serves as the living reference.

---

## Future Upgrades (Not in This Build)

These are recognized needs but explicitly out of scope for V2:

| Future Feature | What It Is | When |
|---------------|-----------|------|
| SQLite database | Replace localStorage with persistent DB for unlimited pages, message search | Phase 2 (next week) |
| Page archival | Close/archive pages that hit context limit, reopen later | Phase 2 |
| Page limit | Max active pages (prevent hundreds of open pages) | Phase 2 |
| Cross-page search | Search across all conversation message content | Phase 2 (requires DB) |
| Phase runner | Auto-loop through PRD phases (the app factory mechanism) | Separate build |
| Walkie-talkie | Inject messages into running agent | Keep from existing WorkspaceChat (already built in) |

---

## Build Approach

### Step 1: Preserve
- Copy `WorkspacePage.tsx` → `WorkspacePageLegacy.tsx`
- Add route for `/#/workspace-legacy`
- Verify legacy page still loads and works

### Step 2: Build New Page Shell
- New `WorkspacePage.tsx` with sidebar + main area layout
- Route handling for `/#/workspace`, `/#/workspace/all`, `/#/workspace/:chatId`
- Redirect logic (workspace root → most recent page)

### Step 3: Page Creation
- "New Page" button in sidebar
- Setup modal (name, provider, model, context mode, repo)
- Save to localStorage
- Navigate to new page

### Step 4: Wire Chat
- Render single WorkspaceChat component per page
- Pass page settings (model, context mode, repo, conversationId) as props
- On conversation created, save conversationId back to localStorage

### Step 5: Sidebar Navigation
- Display all pages as nav buttons with name, date, model, context
- Active page highlighted
- Click navigates to that page's route
- Sort dropdown with localStorage persistence

### Step 6: Context Window Display
- Read token_usage events from active page's WebSocket
- Display live number in sidebar for active page
- Save last-known number to localStorage on page unmount
- Display last-known number for inactive pages

### Step 7: Organizational Page
- Card grid of all pages
- Search bar (filters by name)
- Sort controls
- Click card → navigate to page

### Verification
1. `cd ui && npm run build` — must compile with zero errors
2. Open workspace — redirects to new page creation (first time)
3. Create page with name + model + repo → chat works
4. Create second page → both appear in sidebar
5. Navigate between pages — each has own conversation
6. Context numbers show in sidebar
7. Sort dropdown works
8. Refresh page → pages persist, redirects to last used
9. Visit /#/workspace-legacy → old page still works
10. Visit /#/workspace/all → organizational page shows all pages
