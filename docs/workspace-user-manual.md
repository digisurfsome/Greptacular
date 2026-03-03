# Workspace Page -- Comprehensive User Manual for Automated QA

This document covers every interactive element on the Workspace page (`/#/workspace`). It is derived from the actual source code and is intended as the authoritative reference for AI agents performing end-to-end QA testing.

Source files referenced:
- `ui/src/pages/WorkspacePage.tsx`
- `ui/src/components/workspace/WorkspaceSidebar.tsx`
- `ui/src/components/workspace/WorkspaceChat.tsx`
- `ui/src/components/workspace/WorkspaceChatHeader.tsx`
- `ui/src/components/workspace/WorkspaceLibrary.tsx`
- `ui/src/components/workspace/SwarmPanel.tsx`
- `ui/src/components/workspace/PassoffEditor.tsx`
- `ui/src/components/workspace/CategoryManager.tsx`
- `ui/src/components/workspace/ConversationSearch.tsx`
- `ui/src/components/workspace/ChatForkModal.tsx`
- `ui/src/components/workspace/InjectFromChatModal.tsx`
- `ui/src/components/workspace/LibraryPickerModal.tsx`
- `ui/src/components/workspace/RepoSelector.tsx`
- `ui/src/components/workspace/SaveToLibraryModal.tsx`
- `ui/src/components/workspace/WorkspaceKeyboardHelp.tsx`
- `ui/src/components/workspace/WorkspaceUserGuide.tsx`
- `ui/src/components/workspace/EnhancedContextBudgetBar.tsx`
- `ui/src/components/workspace/AutoSummaryPin.tsx`
- `ui/src/components/workspace/CountdownTimerBar.tsx`
- `ui/src/components/workspace/TokenLogPanel.tsx`
- `ui/src/components/workspace/UsageDashboard.tsx`
- `ui/src/components/workspace/CIStatusWidget.tsx`
- `ui/src/components/GitActivityWidget.tsx`

---

## Section 1: Page Layout

The Workspace page is a full-screen layout with three main zones arranged horizontally. A thin top navigation bar spans the full width.

### Overall Structure (top to bottom, left to right)

1. **Top Navigation Bar** (40px height, full width) -- breadcrumb, view toggles, navigation buttons
2. **Countdown Timer Bar** (conditional) -- session-level timer shown when agent is waiting for input
3. **Main Content Row** (fills remaining height):
   - **Left: Sidebar** (272px wide, collapsible to 0) -- conversations, new chat form, search, categories
   - **Center: Chat Area** (flexible width) -- in Normal Mode: single WorkspaceChat; in Split View: three accordion panels (Research, PRD Builder, Coder)
   - **Swarm Panel** (320px, conditional, between chat and library) -- concurrent agent pipeline
   - **Right: Library Panel** (288px wide, collapsible to 40px) -- file library, repos, walkie-talkie log

### How to Test Layout

1. Navigate to `/#/workspace`
2. **Success**: Page loads with sidebar on left, chat area center, library panel on right
3. **Failure**: Blank screen, infinite spinner, or components overlapping

---

## Section 2: Top Navigation Bar

Location: Fixed 40px bar at the very top of the page.

### 2.1 Back to AutoForge Button (ArrowLeft icon + "AutoForge" text)

- **Location**: Far left of nav bar
- **What it does**: Navigates back to the main AutoForge dashboard by setting `window.location.hash = ''`
- **How to test**: Click the button
- **Success**: Page navigates to the AutoForge main page (the project dashboard)
- **Failure**: Nothing happens, or navigates to wrong page

### 2.2 Breadcrumb "Workspace" Label

- **Location**: After the ChevronRight separator, right of the back button
- **What it does**: Static text label showing current page name. Not interactive.
- **How to test**: Verify text "Workspace" is visible
- **Success**: Label reads "Workspace" in bold
- **Failure**: Missing or wrong text

### 2.3 Git Activity Widget ("G" Button)

- **Location**: Right side of nav bar, first item
- **What it does**: Shows a bold "G" letter that blinks colors based on CI/commit status. Yellow blink = unseen commits, green blink = successful merge, red blink = CI failure. Click expands a dropdown of the last 10 commits with timestamps. Badge count shows unseen commits. Badge and blink reset when dropdown is opened.
- **Prerequisite**: A working directory (repo) must be selected for data to appear
- **How to test**:
  1. Select a repository via the sidebar new chat form's "Attach Repository" toggle
  2. Click the "G" button
- **Success**: Dropdown appears showing recent commit list with hashes, messages, and relative timestamps
- **Failure**: "G" button not visible, dropdown doesn't open, or shows error

### 2.4 CI Status Widget (Pipeline Indicator)

- **Location**: Right side of nav bar, after a vertical divider, next to the Git Activity Widget
- **What it does**: Shows a compact CI pipeline status indicator. States: idle (gray dot), running (cyan spinner), passed (green check, blinking), failed (red X, blinking), fixing (amber wrench, blinking), merging (violet merge icon), merged/deployed (green check, blinking), veto (amber ban), exhausted (red warning, blinking), error (red warning). Click to expand for details. When CI passes, a countdown starts for auto-merge; a veto (X) button appears during the countdown to cancel.
- **Prerequisite**: Working directory must be set and CI monitoring must be initialized
- **How to test**:
  1. Ensure a repository is selected
  2. Look for the CI indicator (will show "idle" if no CI is configured)
  3. Click to expand details if available
- **Success**: Indicator shows correct state; click expands details panel
- **Failure**: Widget not visible, shows wrong state, or crashes on click

### 2.5 Split View Toggle Button (Columns2 icon + "Split" text)

- **Location**: Right side of nav bar, after CI widget divider
- **What it does**: Toggles between Normal Mode (single chat panel) and Split View (three-panel Research/PRD/Coder layout). When active, button has primary background color. When active, additional panel focus buttons (R, P, C, All) and Auto-forward button appear.
- **How to test**: Click the "Split" button
- **Success**:
  - First click: Chat area splits into three vertical panels labeled "RESEARCH", "PRD BUILDER", "CODER"
  - Second click: Returns to single-panel Normal Mode
- **Failure**: Panels don't appear, layout breaks, or state doesn't toggle

### 2.6 Swarm Button (Network icon + "Swarm" text)

- **Location**: Right side of nav bar, after Split button
- **What it does**: Toggles the Swarm Panel (320px side panel) that manages concurrent autonomous agents. When active, button has violet background.
- **How to test**: Click the "Swarm" button
- **Success**: Swarm panel slides in from the right (between chat and library), showing task input area
- **Failure**: Panel doesn't appear, or overlaps existing content

### 2.7 Auto-Forward Button (Zap icon + "Auto" text) -- Split View Only

- **Location**: Right side of nav bar, only visible when Split View is active
- **What it does**: Toggles auto-forwarding. When enabled (amber background), the PRD Builder panel's completed response is automatically injected into the Coder panel.
- **How to test**:
  1. Enable Split View
  2. Click "Auto" button
- **Success**: Button turns amber; when PRD panel finishes a response, the content appears in the Coder panel's input
- **Failure**: Button not visible in split view, or auto-forward doesn't trigger

### 2.8 Panel Focus Buttons (R, P, C, All) -- Split View Only

- **Location**: Right side of nav bar, only visible when Split View is active, after a divider
- **What they do**: Quick-collapse shortcuts for the three panels:
  - **R**: Expands only Research panel, collapses PRD and Coder
  - **P**: Expands only PRD Builder panel, collapses Research and Coder
  - **C**: Expands only Coder panel, collapses Research and PRD
  - **All**: Expands all three panels
- **How to test**: Enable Split View, then click each button
- **Success**: Panels collapse/expand as described. Collapsed panels show as thin vertical bars with rotated labels.
- **Failure**: Panels don't collapse, wrong panels affected, or all buttons disappear

### 2.9 Roles Button (Bot icon + "Roles" text)

- **Location**: Right side of nav bar
- **What it does**: Navigates to the Agent Role Library page at `/#/roles`
- **How to test**: Click the button
- **Success**: Page navigates to `/#/roles`
- **Failure**: Navigation doesn't happen, or wrong page loads

### 2.10 Dashboard Button (LayoutDashboard icon + "Dashboard" text)

- **Location**: Right side of nav bar
- **What it does**: Navigates to the Multi-session Dashboard at `/#/dashboard`
- **How to test**: Click the button
- **Success**: Page navigates to `/#/dashboard`
- **Failure**: Navigation doesn't happen, or wrong page loads

### 2.11 Guide Button (BookOpen icon + "Guide" text)

- **Location**: Right side of nav bar
- **What it does**: Opens/closes the floating User Guide panel. The guide is a draggable, resizable panel with tabbed documentation sections (General, Shortcuts, Sidebar, Chat, etc.) plus a Notes tab with full CRUD for personal notes persisted to localStorage.
- **How to test**: Click the "Guide" button
- **Success**: A floating panel appears with documentation tabs and a notes section
- **Failure**: Panel doesn't appear, or appears but is empty

### 2.12 Keyboard Shortcuts Button (Keyboard icon)

- **Location**: Far right of nav bar
- **What it does**: Opens the keyboard shortcuts help modal
- **How to test**: Click the keyboard icon, or press `?` on the keyboard
- **Success**: Modal appears showing all workspace shortcuts in a list
- **Failure**: Modal doesn't appear

---

## Section 3: Sidebar -- New Chat Form

The sidebar is 272px wide, located on the left side.

### 3.1 Sidebar Header -- "Conversations" Title + Buttons

- **Location**: Top of sidebar, with border below
- **Elements**:
  - "Conversations" text label (not interactive)
  - **Select Mode Button** (CheckSquare icon): Toggles select mode for bulk operations. When active, shows X icon instead.
  - **Collapse/Expand Button** (PanelLeftClose / PanelLeftOpen icon): Collapses sidebar to 0 width or expands it back to 272px.

### 3.1a Select Mode Button

- **How to test**: Click the CheckSquare icon
- **Success**: Checkboxes appear on every conversation row; "Select Mode" bar appears with "All/None" toggle and "Delete (N)" button
- **Failure**: Checkboxes don't appear, or select mode doesn't toggle off when clicking X

### 3.1b Collapse/Expand Sidebar Button

- **How to test**: Click PanelLeftClose icon
- **Success**: Sidebar collapses to 0 width; chat area expands. Click PanelLeftOpen (or use Ctrl/Cmd+B) to bring it back.
- **Failure**: Sidebar doesn't collapse, or doesn't restore properly

### 3.2 "New Chat" Button

- **Location**: Below sidebar header, full width
- **What it does**: Toggles the new chat creation form open/closed. Shows a Plus icon, "New Chat" text, and a ChevronDown that rotates 180 degrees when open.
- **How to test**: Click the button
- **Success**: Form slides in below the button with Name, Folder, Repo Toggle, Model pills, Effort selector, and "Start Chat" button. ChevronDown rotates to point up.
- **Failure**: Form doesn't appear, or appears without proper animation

### 3.3 New Chat Form -- Name Input

- **Location**: First field in the creation form
- **What it does**: Optional text input for naming the conversation. Auto-focused when form opens. Pressing Enter submits the form. Pressing Escape cancels.
- **How to test**:
  1. Open the new chat form
  2. Type a name (e.g. "Test Chat")
  3. Press Enter
- **Success**: Conversation is created with the given name and appears in the sidebar
- **Failure**: Input doesn't focus, or Enter doesn't submit

### 3.4 New Chat Form -- Folder/Category Dropdown

- **Location**: Second field in the creation form, labeled "Folder"
- **What it does**: Select dropdown to assign the new conversation to a category/folder. Options include "No folder" (default) plus all user-created categories.
- **How to test**: Click the dropdown and select a category
- **Success**: Dropdown shows existing categories; selected value persists when chat is created
- **Failure**: Dropdown empty, or category not saved

### 3.5 New Chat Form -- Attach Repository Toggle

- **Location**: Third field in the creation form, labeled "Attach Repository"
- **What it does**: A toggle switch (custom, not native). When ON, reveals the RepoSelector dropdown below it. When a repo is selected, the working directory is set for the new conversation.
- **How to test**:
  1. Click the toggle switch
  2. When RepoSelector appears, click it to see the GitHub repo list
- **Success**: Toggle animates, RepoSelector dropdown appears showing GitHub repos (fetched via `gh` CLI through the backend). Selecting a repo clones it and sets the path.
- **Failure**: Toggle doesn't animate, RepoSelector doesn't appear, or repo list fails to load

### 3.5a RepoSelector Dropdown (appears when Attach Repository is ON)

- **What it does**: Opens a dropdown panel (280px wide) with:
  - Search input to filter repositories
  - List of GitHub repositories showing name, private/public lock icon, and relative update time
  - Clicking a repo triggers clone and sets local path
  - Clear button (X icon) to deselect current repo
- **How to test**:
  1. Toggle on Attach Repository
  2. Click the RepoSelector trigger button
  3. Type in the search field to filter
  4. Click a repo
- **Success**: Repos load (from `gh repo list`), search filters them, clicking clones and sets path, "Cloning..." indicator appears during clone
- **Failure**: "Loading repositories..." never resolves, or error message appears (e.g., "gh CLI not installed")

### 3.6 New Chat Form -- Model Preset Pills

- **Location**: Below the repo toggle, labeled "Model"
- **What it does**: Horizontal pill selector (radio group) for choosing model + context. For Claude provider, default presets are: "Opus 4.6 - 1M", "Sonnet 4.6 - 1M", "Opus 4.6 - 200K". For other providers (Codex, Gemini), shows that provider's models. Active pill is highlighted with provider-specific colors (blue for Opus 1M, violet for Sonnet, zinc for 200K, emerald for Codex, violet for Gemini).
- **How to test**: Click each pill
- **Success**: Selected pill highlights with the correct color; other pills deselect
- **Failure**: Pill doesn't highlight, or selection doesn't persist when chat is created

### 3.7 New Chat Form -- Thinking Effort Selector

- **Location**: Below model pills, labeled "Thinking Effort". Only visible for Claude provider. Grayed out (opacity 35%, pointer-events disabled) unless Opus 1M is selected.
- **What it does**: Three-pill selector for Low / Medium / High thinking effort. Each has a tooltip showing Anthropic's recommended use cases:
  - **Low** (emerald): Quick lookups, classification, routing, sub-agents
  - **Medium** (blue): Agentic coding, tool use, code generation
  - **High** (orange): Complex analysis, nuanced reasoning, quality-critical
- **When it's active**: Only when model preset is Opus + 1M context
- **How to test**:
  1. Select "Opus 4.6 - 1M" model preset
  2. Click each effort level pill
- **Success**: Effort selector becomes interactive (full opacity); each pill highlights with its color; use case description appears below
- **Failure**: Selector stays grayed out on Opus 1M, or doesn't gray out on other models

### 3.8 New Chat Form -- Start Chat Button

- **Location**: Bottom of the creation form
- **What it does**: Creates the conversation via the API with the configured name, category, model, context mode, effort level, and provider. Shows "Creating..." during the mutation. On success, selects the new conversation and closes the form.
- **How to test**: Fill out the form and click "Start Chat"
- **Success**: Button shows "Creating...", then conversation appears in sidebar and chat area loads
- **Failure**: Button stays disabled, or error in console, or conversation not created

### 3.9 New Chat Form -- Cancel (X) Button

- **Location**: Top-right of the form, next to "New Conversation" label
- **What it does**: Closes the form and resets all fields (name, category, attach repo toggle)
- **How to test**: Click the X button
- **Success**: Form closes, fields reset
- **Failure**: Form stays open, or fields retain values on next open

---

## Section 4: Sidebar -- Conversation List

### 4.1 Search Input (ConversationSearch)

- **Location**: Below the New Chat button, full width of sidebar
- **What it does**: Search icon on left, text input, clear (X) button on right when query is non-empty. Behavior depends on query length:
  - < 3 characters: Client-side filter on conversation titles
  - >= 3 characters: Server-side search with 300ms debounce, returns results with matching excerpts
  - Server-side results appear in an overlay dropdown below the input with highlighted text matches
- **How to test**:
  1. Type a short query (1-2 chars) -- sidebar list filters
  2. Type a longer query (3+ chars) -- overlay dropdown appears with search results showing excerpts
  3. Click a result in the dropdown
  4. Click the X to clear
  5. Press Escape to clear and close
- **Success**: Filtering works at both levels; excerpts show highlighted matches; clicking a result selects the conversation
- **Failure**: No filtering, no overlay, or clicking result doesn't navigate

### 4.2 Bulk Action Bar (Select Mode)

- **Location**: Appears below search when select mode is active
- **What it does**: Shows count of selected conversations. Has two buttons:
  - **All/None**: Toggles between selecting all conversations and deselecting all
  - **Delete (N)** (red, destructive): Deletes all selected conversations
- **How to test**:
  1. Enter select mode (Section 3.1a)
  2. Check some conversations
  3. Click "All" to select all
  4. Click "Delete (N)" to bulk delete
- **Success**: Count updates as checkboxes change; "All" toggles to "None" when all selected; delete removes conversations
- **Failure**: Count wrong, All/None doesn't toggle, delete fails silently

### 4.3 Conversation Groups (Category Sections)

- **Location**: Main scrollable area of sidebar
- **What it does**: Conversations are grouped by category with pinned items in a special "Pinned" group at top. Each group has:
  - **Group header**: Clickable button to collapse/expand the group. Shows category color dot (if set), star icon (for Pinned group), category name, and count badge.
  - When collapsed, conversation rows within that group are hidden.
- **How to test**: Click a category group header
- **Success**: Group collapses (rows hidden) on click, expands on second click. Count badge remains visible.
- **Failure**: Group doesn't collapse, or wrong conversations hidden

### 4.4 Conversation Rows

Each conversation appears as a clickable card in its category group.

#### 4.4a Model/Context Badge (top-right corner of each row)

- **What it does**: For Claude conversations: shows model abbreviation and context (e.g., "O-1M", "S-1M", "O-200K"). **Clickable** -- clicking cycles through model/context combinations: Opus 1M -> Sonnet 1M -> Opus 200K -> Opus 1M. Color-coded: blue for Opus+1M, violet for Sonnet+1M, zinc for Opus+200K. For non-Claude conversations (Codex, Gemini): shows the model ID as a static (non-clickable) badge with provider-specific color (emerald for Codex, violet for Gemini).
- **How to test**: Click the badge on a Claude conversation
- **Success**: Badge text and color cycle through the three combinations
- **Failure**: Badge doesn't cycle, or shows wrong model after cycling

#### 4.4b Activity Indicators (left edge of row)

- **Streaming/Running**: Cyan pulsing glow bar on left edge + cyan pulsing dot + shimmer sweep overlay. Appears when the conversation has an active WebSocket stream or a running background session.
- **Waiting Input**: Yellow pulsing glow bar + yellow pulsing dot. Appears when the agent is waiting for user response.
- **Completed**: Small green static dot. Appears when a background session recently completed.
- **Failed**: Small red static dot + red bar on left edge. Appears when a background session failed.
- **How to test**: Start a conversation and send a message to trigger streaming
- **Success**: Cyan glow appears during streaming; disappears when response completes
- **Failure**: No activity indicator despite active streaming

#### 4.4c Clicking a Conversation Row

- **Normal mode**: Selects the conversation, loads it in the chat area
- **Select mode**: Toggles the checkbox for that row (doesn't navigate)
- **How to test**: Click a conversation row
- **Success**: Chat area loads the selected conversation's messages; row highlights with accent background
- **Failure**: Chat area doesn't update, or wrong conversation loads

#### 4.4d Hover Actions (appear on mouse hover, right side of row)

Three icon buttons appear when hovering over a conversation row (not in select mode):

1. **FolderPlus button**: Opens an inline edit popover for assigning folder and repository
   - Popover contains:
     - "Move to Folder" dropdown (same categories as new chat form)
     - "Attach Repository" RepoSelector
     - "Done" button to close the popover
   - Closes when clicking outside the popover
   - **How to test**: Hover a row, click FolderPlus, change folder, click Done
   - **Success**: Popover opens below the row; changing folder updates immediately; Done closes it
   - **Failure**: Popover doesn't open, or changes don't save

2. **Pin button** (Pin icon): Toggles pinning. Pinned conversations appear in the "Pinned" group at the top with a star icon.
   - **How to test**: Hover a row, click Pin
   - **Success**: Conversation moves to "Pinned" group with star; clicking again unpins
   - **Failure**: Conversation doesn't move, or pin state lost on refresh

3. **Delete button** (Trash2 icon, turns red on hover): Deletes the conversation immediately (no confirmation dialog).
   - **How to test**: Hover a row, click Delete
   - **Success**: Conversation disappears from list; if it was the active conversation, chat area clears
   - **Failure**: Conversation remains, or active conversation not cleared

### 4.5 Empty States

- **No conversations**: Shows MessageSquare icon + "No conversations yet"
- **Search with no results**: Shows MessageSquare icon + "No matching conversations"
- **Loading**: Shows "Loading..." text

---

## Section 5: Sidebar -- Category Management

### 5.1 "Manage Categories" Button

- **Location**: Bottom of sidebar, full width, with Settings icon
- **What it does**: Opens the Category Manager modal
- **How to test**: Click the button
- **Success**: Modal overlay appears with category management UI
- **Failure**: Nothing happens, or modal doesn't render

### 5.2 Category Manager Modal

A full modal dialog with:

#### 5.2a Category List

- Shows each category with: color dot, name, up/down arrows, edit (pencil) button, delete (trash) button
- **Move Up/Down Arrows**: Reorder categories. Up arrow disabled on first item, down arrow disabled on last.
- **Edit (Pencil) Button**: Switches the row to edit mode with: editable name input, color swatch palette (10 preset colors), checkmark save button. Press Enter to save.
- **Delete (Trash) Button**: Deletes the category immediately (no confirmation).
- **Empty state**: "No categories yet. Create one below."

#### 5.2b Add Category Form (bottom of modal)

- Text input for new category name + "Add" button (Plus icon)
- Color palette row (10 preset colors as round buttons; selected one has primary border + ring)
- Enter key submits the form
- **How to test**:
  1. Type a category name
  2. Select a color
  3. Click "Add" or press Enter
- **Success**: Category appears in the list with chosen color
- **Failure**: Category not created, or color not saved

#### 5.2c Close Button (X, top-right) and Escape key

- **How to test**: Click X or press Escape
- **Success**: Modal closes
- **Failure**: Modal stays open

---

## Section 6: Chat Header

Location: Top of the chat area, below the nav bar. Rendered by `WorkspaceChatHeader`.

### 6.1 Editable Title

- **Location**: Left side of header
- **What it does**: Click to enter edit mode. Shows current title (or "Untitled Conversation" in italic). A tiny Pencil icon appears on hover. In edit mode: text input appears, blur or Enter saves, Escape cancels.
- **How to test**:
  1. Click the title text
  2. Type a new title
  3. Press Enter (or click away to blur)
- **Success**: Title updates in header and sidebar
- **Failure**: Edit mode doesn't activate, or title not saved

### 6.2 Category Dropdown

- **Location**: Next to the title
- **What it does**: Native `<select>` dropdown showing categories (default: general, debugging, refactoring, feature, exploration, plus any custom categories). Selecting a category immediately updates the conversation's category.
- **How to test**: Change the dropdown value
- **Success**: Category updates; conversation moves to the correct group in sidebar
- **Failure**: Dropdown empty, or category not saved

### 6.3 Tags Section

- **Location**: Next to the category dropdown
- **What it does**: Shows tag chips (colored pills). Each tag has an X button to remove it. A "+" button (Tag + Plus icons) opens a tiny inline input to add a new tag. Tags are comma-separated and stored as a string.
- **How to test**:
  1. Click the "+" button
  2. Type a tag name and press Enter
  3. Verify the tag chip appears
  4. Click the X on a tag to remove it
- **Success**: Tags appear as pills; adding works; removing works; duplicates (case-insensitive) are prevented
- **Failure**: Tag input doesn't appear, or tags not saved

### 6.4 Git Branch Indicator

- **Location**: Next to tags, only visible when a working directory is set and is a git repository
- **What it does**: Shows GitBranch icon + current branch name in monospace font. If the branch is NOT "main" or "master", a Pencil icon appears to rename it. Click Pencil to enter rename mode. In rename mode: input field appears, Enter saves, Escape cancels. A loading spinner appears during rename.
- **How to test**:
  1. Ensure a repo is attached
  2. If not on a protected branch, click the Pencil icon
  3. Type a new branch name
  4. Press Enter
- **Success**: Branch name updates; spinner shows briefly during rename
- **Failure**: Branch not detected, pencil icon missing for non-protected branches, or rename fails

### 6.5 GitHub Repo Link ("Repo" Badge)

- **Location**: Right side of header, only visible when the working directory has a GitHub remote
- **What it does**: Opens the repository on GitHub in a new tab
- **How to test**: Click the "Repo" badge
- **Success**: GitHub repo page opens in new browser tab
- **Failure**: Badge not visible despite GitHub remote, or link broken

### 6.6 PR Link ("View PR" Badge)

- **Location**: Right side of header, only visible when the current branch has an open pull request
- **What it does**: Opens the pull request on GitHub in a new tab
- **How to test**: Check out a branch with an open PR, then click the badge
- **Success**: PR page opens in new browser tab
- **Failure**: Badge not visible despite open PR, or link broken

### 6.7 Walkie-Talkie Settings Gear (Settings icon)

- **Location**: Right side of header
- **What it does**: Toggles the walkie-talkie settings panel (Section 8.7). When active, gear icon has amber background.
- **How to test**: Click the gear icon
- **Success**: Settings panel slides in below the header bar
- **Failure**: Panel doesn't appear

### 6.8 Walkie-Talkie Live/Waiting Indicator

- **Location**: Right side of header, only visible when the walkie-talkie system is active (agent working)
- **What it does**: Shows a pulsing amber dot + text "Live" or "Waiting"
- **How to test**: Send a message to trigger agent work
- **Success**: Indicator appears during agent processing
- **Failure**: Indicator never appears, or shows wrong state

### 6.9 Connection Status Indicator

- **Location**: Far right of header
- **What it does**: Shows WebSocket connection state:
  - **Connected**: Green pulsing dot + Wifi icon
  - **Connecting**: Yellow dot + spinning Loader2 icon
  - **Disconnected/Error**: Red dot + WifiOff icon
- **How to test**: Open a conversation and check the indicator
- **Success**: Green pulsing dot + Wifi when connected
- **Failure**: Always shows disconnected, or wrong state

---

## Section 7: Chat Area -- Header Bar Extensions

The header area also contains elements rendered by WorkspaceChat on the right side of the header bar.

### 7.1 Active Model Badge (Normal Mode only)

- **Location**: Right side of header, before the token log toggle
- **What it does**: Shows a colored pill with the active model preset label (e.g., "Opus 4.6 - 1M"), the confirmed model ID in monospace (e.g., "claude-opus-4-6"), and API cost if available.
- **How to test**: Start a conversation; observe the badge
- **Success**: Badge shows correct model and context; cost appears after first API response
- **Failure**: Badge missing, or shows wrong model

### 7.2 Token Log 3-State Toggle (Auto | On | Off)

- **Location**: Right side of header, pill-shaped radio group with ScrollText icon
- **What it does**: Controls the Token Log side panel visibility:
  - **Auto**: Panel shows automatically when streaming, hides when idle
  - **On**: Panel always visible
  - **Off**: Panel always hidden
- **How to test**: Click each option
- **Success**: Active pill highlights; token log panel behavior changes accordingly
- **Failure**: Toggle doesn't work, or panel state doesn't match selection

### 7.3 Actions Dropdown (MoreHorizontal "..." button)

- **Location**: Far right of header, only visible when a conversation is active
- **What it does**: Opens a dropdown menu with three actions:
  1. **Fork Chat** (GitFork icon): Opens the Fork Modal
  2. **Inject from Chat** (ArrowDownToLine icon): Opens the Inject Modal
  3. **Export as Markdown** (Download icon): Downloads the conversation as a .md file

#### 7.3a Fork Chat

- Opens ChatForkModal showing a scrollable list of all messages with radio buttons
- Select a fork point (message after which to stop copying)
- Click "Fork" to create a new conversation with messages up to that point
- **How to test**: Click "..." > "Fork Chat", select a message, click "Fork"
- **Success**: New conversation appears in sidebar with messages copied up to the selected point
- **Failure**: Modal empty, fork fails, or messages not copied correctly

#### 7.3b Inject from Chat

- Opens InjectFromChatModal with a two-step flow:
  - **Step 1**: Browse/search all other conversations. Click one to select it.
  - **Step 2**: See all messages from the selected conversation with checkboxes. Select/deselect individual messages. "Select All" / "Deselect All" toggle. "Back" button to return to Step 1.
  - Click "Inject (N)" to inject selected messages into the current conversation
- **How to test**: Click "..." > "Inject from Chat", select a source conversation, check some messages, click "Inject"
- **Success**: An injection indicator appears above the input area showing "Injecting N messages from [Source]" with a dismiss (X) button. Messages are prepended to the next send.
- **Failure**: Modal doesn't load conversations, messages don't load, or injection doesn't work

#### 7.3c Export as Markdown

- **How to test**: Click "..." > "Export as Markdown"
- **Success**: Browser downloads a .md file containing the conversation
- **Failure**: No download initiated, or file is empty/malformed

---

## Section 8: Chat Area -- Main Content

### 8.1 Walkie-Talkie Settings Panel (collapsible)

- **Location**: Below the header bar, amber-tinted panel. Toggled by the gear icon (Section 6.7).
- **Contents**:
  1. **Check Frequency** (3 buttons): "Per Feature", "Every Tool Call", "Never"
  2. **Wait Timeout** (4 buttons): "30s", "1m", "2m", "5m"
  3. **Auto-reply on timeout** (Switch toggle)
  4. Info text: "Changes take effect on the next agent session."
  5. Close button (X, top-right)
- **How to test**: Open the panel, change each setting
- **Success**: Buttons highlight when selected; switch toggles; changes persist to server
- **Failure**: Settings don't save, or buttons don't highlight

### 8.2 Disconnection Banner

- **Location**: Below header, red-tinted bar. Only visible when WebSocket connection is lost and a conversation is active.
- **What it does**: Shows WifiOff icon + error message + "Retry" link
- **How to test**: Disconnect the server while in a conversation
- **Success**: Red banner appears with error details and Retry link; clicking Retry reconnects
- **Failure**: No banner despite disconnection, or Retry doesn't work

### 8.3 Split View Panel Labels (split view only)

- **Location**: Below header, colored label bars for each panel
- **What it does**: Shows panel name (e.g., "RESEARCH (Opus - 200K)") with panel-specific color (emerald for Research, violet for PRD, cyan for Coder). Each panel has an Opus/Sonnet toggle (two pills) to switch the model for that specific panel.
- **How to test**: In split view, click the Opus/Sonnet toggle on a panel
- **Success**: Toggle switches; panel label updates to reflect new model
- **Failure**: Toggle doesn't work, or label doesn't update

### 8.4 Compact Control Bar

- **Location**: Below the panel label (or header in normal mode)
- **Contents**:
  1. **Effort Pill Dropdown**: Shows current effort level (Low/Med/High) with colored pill. Click to open dropdown with use case descriptions. Only interactive when Opus 1M is selected.
  2. **Thin Context Budget Bar**: Progress bar showing token usage as a percentage. 200K pricing cliff marker (amber line at 20%) on 1M panels. Streaming shimmer animation when active.
  3. **Usage Text**: "N% - XX.XK/200K" or "N% - XX.XK/1M"
  4. **Message Count**: "N msgs"
- **How to test**: Observe the bar as you send messages; click the effort pill
- **Success**: Bar grows as tokens accumulate; effort dropdown opens with three options; amber cliff marker visible on 1M panels
- **Failure**: Bar doesn't update, effort dropdown doesn't open

### 8.5 Usage Dashboard (expandable)

- **Location**: Below the compact control bar
- **What it does**: Compact expandable panel showing usage across daily, weekly, monthly periods with calibrated limit bars. Shows cost zone breakdown for the active conversation. Includes rate limit event logging. Expands/collapses on click.
- **How to test**: Click to expand; observe usage data
- **Success**: Dashboard expands showing usage bars, cost zones, calibration data
- **Failure**: Dashboard doesn't expand, or shows no data

### 8.6 Auto-Summary Pin

- **Location**: Below usage dashboard, pinned card above messages
- **What it does**: Collapsible card showing the latest AI-generated conversation summary. Shows:
  - ChevronRight/ChevronDown toggle to expand/collapse
  - "Summary (N messages) - updated Xm ago" text
  - Regenerate button (RefreshCw icon, spins during regeneration)
  - Expanded: shows the summary text
- **Only visible when**: A summary exists for the conversation
- **How to test**: Click the summary card to expand, click the refresh icon
- **Success**: Summary text appears when expanded; regenerate triggers a new summary
- **Failure**: Card missing despite messages, regenerate fails

### 8.7 Message Display Area

- **Location**: Main scrollable area of the chat panel
- **What it does**: Displays conversation messages. User messages on one side, assistant messages on the other. Features:
  - Markdown rendering in assistant messages
  - Structured blocks (agent notifications) parsed and displayed as special UI elements above the message
  - Tool call blocks displayed inline
  - Streaming indicator (last assistant message updates in real-time)
  - Image attachments displayed inline
  - "Copy to Passoff" button on assistant messages (split view only)
  - "Save to Library" button on assistant messages
  - Smart auto-scroll: scrolls to bottom when new content arrives, unless user has scrolled up
- **Empty state**: Shows MessageSquare icon + "No conversations yet" or "New Chat -- [Model] ([Context])"
- **Connection failed state**: Shows WifiOff icon + error details + "Retry Connection" and "Back to Conversations" buttons

### 8.8 Loading Indicator

- **Location**: Below messages, above input
- **What it does**: Shows "Thinking..." with spinning Loader2 icon while the agent is processing
- **Only visible when**: Agent is loading AND there are messages AND agent is not in "waiting" state
- **How to test**: Send a message
- **Success**: "Thinking..." appears during processing, disappears when response arrives
- **Failure**: Indicator doesn't appear, or persists after response

### 8.9 Countdown Timer Bar

- **Location**: Below messages, when agent is waiting for user input
- **What it does**: Shows a depleting amber progress bar with Clock icon + "Agent waiting for response..." + countdown (M:SS format) + "Keep Going" button. When auto-reply is enabled, shows "(auto-reply)" badge. When countdown reaches zero: auto-reply sends a continue message; manual mode shows "Time's up".
- **How to test**: Trigger agent waiting state (the agent asks a question)
- **Success**: Timer bar appears with countdown, Keep Going button dismisses it
- **Failure**: Timer doesn't appear, countdown doesn't tick, or Keep Going doesn't work

### 8.10 Agent Waiting Question Display

- **Location**: Below countdown timer, amber-tinted bar
- **What it does**: Shows "Agent asks: [question text]" when the agent is waiting for user input
- **How to test**: Agent asks a question during processing
- **Success**: Question text displayed in amber bar
- **Failure**: Question not shown

### 8.11 Walkie-Talkie Input Bar

- **Location**: Below messages, amber-tinted bar with left amber border
- **Only visible when**: Agent is actively working (loading) AND check frequency is not "never"
- **What it does**: Allows sending messages to the working agent without interrupting it. Shows Radio icon + text input + Send button. After sending, shows a "Sent!" indicator with check icon.
- **How to test**: While agent is working, type a message and click Send (or press Enter)
- **Success**: Message sends; "Sent!" appears briefly; message appears in Walkie-Talkie log (right panel)
- **Failure**: Input not visible during agent work, or message doesn't send

### 8.12 Injection Indicator

- **Location**: Below messages, gray bar
- **Only visible when**: Messages have been injected from another conversation (via "Inject from Chat")
- **What it does**: Shows "Injecting N message(s) from [Source Title]" with dismiss (X) button
- **How to test**: Use "Inject from Chat" (Section 7.3b)
- **Success**: Indicator appears; X button dismisses it and clears the injection
- **Failure**: Indicator doesn't appear after injection

---

## Section 9: Chat Input Area

Location: Bottom of the chat panel, below all bars and indicators.

### 9.1 Drag and Drop Zone

- **What it does**: The entire input area supports drag and drop. When dragging files over it, a dashed border overlay appears with "Drop files or images here" text. Dropping files adds them as image attachments (for images) or text file attachments (for non-images).
- **How to test**: Drag a file from the desktop over the input area
- **Success**: Dashed border overlay appears; dropping adds the file to pending attachments
- **Failure**: No visual feedback, or files not added

### 9.2 Pending Images Preview

- **Location**: Above the input row, only visible when images are attached
- **What it does**: Shows thumbnail previews (64x64) of attached images. Each has an X button (appears on hover) to remove it.
- **How to test**: Paste an image (Ctrl+V) or attach via image button
- **Success**: Thumbnail appears with remove button on hover
- **Failure**: No preview, or X button doesn't remove

### 9.3 Pending Files Preview

- **Location**: Above the input row, only visible when non-image files are attached
- **What it does**: Shows file name with Paperclip icon in a gray chip. X button to remove.
- **How to test**: Click the Paperclip button and select a text file
- **Success**: File chip appears with name; X removes it
- **Failure**: No chip, or file not attached

### 9.4 Attached Library Files Preview

- **Location**: Above the input row, only visible when library files are attached
- **What it does**: Shows file name with BookOpen icon in a primary-colored chip. X button to remove.
- **How to test**: Click the BookOpen button (Section 9.8) and select library files
- **Success**: Library file chips appear; X removes them
- **Failure**: No chips after selection

### 9.5 File Attach Button (Paperclip icon)

- **Location**: Left side of input row
- **What it does**: Opens native file picker (any file type, multiple selection). Selected files are added as text file attachments. Their content is read as text and appended to the message when sent.
- **How to test**: Click the Paperclip button, select one or more files
- **Success**: File picker opens; selected files appear in pending files preview
- **Failure**: File picker doesn't open, or files not added

### 9.6 Image Attach Button (ImagePlus icon)

- **Location**: Left side of input row, next to Paperclip
- **What it does**: Opens native file picker filtered to image types (JPEG, PNG, GIF, WebP, multiple selection). Selected images are converted to base64 attachments with preview thumbnails.
- **How to test**: Click the ImagePlus button, select image files
- **Success**: File picker opens with image filter; selected images appear as thumbnails
- **Failure**: File picker doesn't open, or images not processed

### 9.7 Clipboard Paste (Ctrl+V / Cmd+V)

- **What it does**: Detects pasted images from clipboard and adds them as image attachments. Only works for image content types.
- **How to test**: Copy an image, then paste in the input area
- **Success**: Pasted image appears as thumbnail in pending images
- **Failure**: Image not detected from clipboard

### 9.8 Library Attach Button (BookOpen icon)

- **Location**: Left side of input row, next to ImagePlus
- **What it does**: Opens the Library Picker Modal. When library files are already attached, the icon turns primary color and shows a badge count. Selected files are sent as library file IDs with the next message.
- **How to test**: Click the BookOpen button
- **Success**: Library Picker Modal opens (Section 10.5)
- **Failure**: Modal doesn't open

### 9.9 Text Input (Textarea)

- **Location**: Center of input row, flexible width
- **What it does**: Multi-line text area for typing messages. Features:
  - Auto-expands vertically as you type (min 44px, max 240px)
  - Resizable by dragging the bottom edge
  - Placeholder: "Ask anything... (paste images with Ctrl+V)"
  - Disabled during loading/streaming
  - Drafts persist to localStorage per conversation
  - **Enter**: Sends message
  - **Shift+Enter**: New line
- **How to test**: Type a message, press Enter to send, Shift+Enter for new line
- **Success**: Message sends on Enter; new line on Shift+Enter; textarea expands with content
- **Failure**: Enter doesn't send, or textarea doesn't auto-expand

### 9.10 Send Button

- **Location**: Right side of input row
- **What it does**: Sends the current message (text + images + files + library files). When loading, shows spinning Loader2 icon instead of Send icon. Disabled when: input is empty AND no attachments, OR loading, OR conversation is still loading.
- **Color**: In split view, button color matches the panel (emerald for Research, violet for PRD, cyan for Coder)
- **How to test**: Type a message and click the button
- **Success**: Message sends; input clears; button shows spinner during processing
- **Failure**: Button stays disabled, or message doesn't send

### 9.11 Help Text

- **Location**: Below the input row
- **Text**: "Enter to send, Shift+Enter for new line. Drag & drop or paste images."
- **Not interactive**.

---

## Section 10: Right Panels -- Library, Repos, Walkie-Talkie

Location: 288px wide panel on the right side. Collapsible to a thin 40px strip.

### 10.1 Library Panel Tab Bar

Three tabs + collapse button:
- **Library** (FileText icon): File library with folder browser
- **Repos** (GitBranch icon): Connected repositories with file browser. Shows repo count badge.
- **WT** (Radio icon): Walkie-Talkie message log. Shows message count badge (amber).
- **Collapse button** (">>" text): Collapses the panel to a thin strip

### 10.2 Library Tab

#### 10.2a Upload / Paste Buttons

- **Location**: Top of Library tab, horizontal row
- **Upload** (Upload icon): Opens FileUploadModal in file upload mode
- **Paste** (ClipboardPaste icon): Opens FileUploadModal in text paste mode
- **How to test**: Click each button
- **Success**: Modal opens for file upload or text paste
- **Failure**: Modal doesn't open

#### 10.2b Library Folder Browser (LibraryFolderBrowser)

- **Location**: Below the upload buttons, fills remaining space
- **What it does**: Hierarchical folder browser for the workspace library. Shows folders and files. Click folders to navigate in. Files show type badge, name, size. Click files to preview. Delete files via context action.
- **How to test**: Navigate into folders, click files to preview, delete a file
- **Success**: Folder navigation works; file preview opens; delete removes file
- **Failure**: Folders don't open, or files not visible

### 10.3 Repos Tab

#### 10.3a "Connect Repository" Button

- **Location**: Top of Repos tab
- **What it does**: Opens the RepoConnector modal for connecting a new GitHub repository to the conversation
- **How to test**: Click "Connect Repository"
- **Success**: Modal opens for connecting a repo
- **Failure**: Button doesn't open modal

#### 10.3b Repository List

- **Location**: Below the connect button
- **What it does**: Shows connected repos with expandable file browsers (RepoBrowser). Click files to preview their content in a modal. Empty state shows "No repos connected".
- **How to test**: Connect a repo, then browse its files
- **Success**: Repo appears in list; file tree is browsable; clicking files shows content
- **Failure**: Repo not listed after connection, or files not browsable

### 10.4 Walkie-Talkie (WT) Tab

- **Location**: Third tab in the right panel
- **What it does**: Displays a chronological log of all walkie-talkie messages (both user-sent and agent-received). Messages are color-coded: amber for user, primary color for agent, gray for system. Each shows sender icon (User/Bot/Info), sender label ("You"/"Agent"/"System"), timestamp (HH:MM:SS), and content. Auto-scrolls to bottom when new entries arrive.
- **Empty state**: "No walkie-talkie messages yet" with explanation text
- **How to test**: Send a walkie-talkie message while agent is working (Section 8.11), then check the WT tab
- **Success**: Message appears in the log with correct sender and timestamp
- **Failure**: Messages not logged, or wrong sender attribution

### 10.5 Library Picker Modal (LibraryPickerModal)

- **Triggered by**: BookOpen button in chat input (Section 9.8)
- **What it does**: Modal for browsing the workspace library filesystem and selecting files to attach to a message. Features:
  - Title bar with Paperclip icon + "Attach Files" + selected count badge + close (X)
  - Breadcrumb navigation bar (Home icon + folder names)
  - Folder and file listing: folders are clickable to navigate; files have checkboxes for multi-select
  - Files show: checkbox, type badge (color-coded: blue for doc, green for code, purple for spec, orange for template), name, size
  - Footer: Cancel + "Attach N files" button (disabled when none selected)
- **How to test**: Click BookOpen in input, navigate folders, select files, click Attach
- **Success**: Files attach and appear as library file chips above the input
- **Failure**: Modal doesn't show files, checkboxes don't work, or attach doesn't work

### 10.6 Save to Library Modal (SaveToLibraryModal)

- **Triggered by**: "Save to Library" action on assistant messages in the chat
- **What it does**: Modal for saving an assistant response to the workspace library. Fields:
  - **Filename**: Auto-generated from first line of content (sanitized, max 40 chars, .md extension)
  - **Display Name** (optional): Human-readable label
  - **Folder**: Dropdown with nested folder tree (indented options)
  - **Tags** (optional): Comma-separated text input
  - **Save** / **Cancel** buttons
- **How to test**: Click "Save to Library" on an assistant message, fill form, click Save
- **Success**: File saved to library; appears in the Library tab's folder browser
- **Failure**: Save fails, or file doesn't appear in library

### 10.7 Collapsed Library State

- When collapsed, shows a thin 40px strip with a FileText icon button
- Clicking the icon expands the library panel back to 288px
- **How to test**: Click ">>" to collapse, then click the FileText icon
- **Success**: Panel collapses and expands correctly
- **Failure**: Panel stuck collapsed, or doesn't restore tabs

---

## Section 11: Split View -- Three-Panel Layout

When Split View is activated (Section 2.5), the single chat area is replaced with three resizable, independently collapsible panels.

### 11.1 Research Panel (Left)

- **Label**: "RESEARCH (Opus/Sonnet - 200K)" in emerald color
- **Context mode**: Fixed at 200K (subscription tier)
- **Color theme**: Emerald accents
- **Collapse button**: ChevronsLeft icon (top-right corner). When collapsed, shows a thin vertical bar labeled "RESEARCH" in emerald, click to expand.
- **Features**: Full WorkspaceChat instance with:
  - "Copy to Passoff" button on assistant messages (sends content to the Passoff Editor in the PRD panel)
  - Opus/Sonnet toggle for model selection
  - Send button colored emerald

### 11.2 PRD Builder Panel (Center)

- **Label**: "PRD BUILDER (Opus/Sonnet - 1M)" in violet color
- **Context mode**: 1M for Opus, 200K for Sonnet (API tier)
- **Color theme**: Violet accents
- **Collapse button**: ChevronsLeft icon (top-right). When collapsed, shows "PRD BUILDER" bar.
- **Tab bar** (unique to this panel): Two tabs:
  1. **Chat** (violet underline when active): Standard WorkspaceChat
  2. **Passoff** (amber underline when active): PassoffEditor component with section count badge
- **Features**:
  - Receives injected content from the Passoff Editor's "Send to Execute" button
  - When Auto-Forward is enabled, completed responses are auto-sent to the Coder panel

### 11.3 Coder Panel (Right)

- **Label**: "CODER (Opus/Sonnet - context-dependent)" in cyan color
- **Context mode**: 1M for Opus, 200K for Sonnet
- **Color theme**: Cyan accents
- **Collapse button**: ChevronsRight icon (top-right). When collapsed, shows "CODER" bar.
- **Features**: Full WorkspaceChat instance. Receives auto-forwarded content from PRD Builder.

### 11.4 Collapsed Panel Bars

- **What they are**: Thin vertical strips (40px wide) with rotated text labels
- **How to test**: Collapse a panel using the chevron button, then click the collapsed bar
- **Success**: Panel collapses to a thin bar; clicking the bar restores it
- **Failure**: Panel doesn't collapse, or clicking the bar doesn't restore

---

## Section 12: Passoff Editor (Split View PRD Panel)

Located in the PRD Builder panel's "Passoff" tab.

### 12.1 Header

- Shows "PASSOFF" in amber + section count
- **Add Section Button** (Plus icon): Adds a new empty section at the bottom

### 12.2 Preamble Textarea

- **Location**: Below header
- **What it does**: Free-form text area for introductory context. Placeholder: "Add context here... Explain the big picture..."
- **How to test**: Type text in the preamble
- **Success**: Text persists as you type
- **Failure**: Text not preserved

### 12.3 Section Cards

Each section has:
- **Drag Handle** (GripVertical icon): Drag to reorder sections
- **Title Input**: Inline text input for section title
- **Collapse Toggle** (ChevronUp/ChevronDown): Collapse/expand the section content
- **Delete Button** (Trash2 icon): Remove the section
- **Content Textarea**: Free-form text area for section content

### 12.4 Drag-and-Drop Reorder

- **What it does**: Sections can be dragged and dropped to reorder. Active drag shows ring highlight.
- **How to test**: Drag a section by its grip handle to a new position
- **Success**: Section moves to new position; order persists
- **Failure**: Drag doesn't work, or section snaps back

### 12.5 "Send to Execute" Button

- **Location**: Bottom of Passoff Editor
- **What it does**: Builds a markdown document from preamble + all sections (using ## headings for section titles) and injects it as a message into the PRD Builder Chat panel. Also expands the PRD panel if collapsed.
- **Color**: Violet (bg-violet-600)
- **Disabled when**: No content exists (preamble empty AND no sections)
- **How to test**: Add some sections, then click "Send to Execute"
- **Success**: Content appears in the PRD Chat panel as a user message; passoff overlay closes
- **Failure**: Content not injected, or button stays disabled

---

## Section 13: Swarm Panel

Toggled by the "Swarm" button in the nav bar (Section 2.6). Appears as a 320px panel between the chat area and library.

### 13.1 Header

- Shows "SWARM" with Network icon + status badge (RUNNING/COMPLETED/FAILED/STOPPED)
- Close button (X icon)

### 13.2 Task Input (pre-start)

- **Visible when**: No swarm is running
- **What it does**: Description text explaining the 3-stage pipeline (Research -> PRD Builder -> Coder). Textarea for task description. Warning if no working directory is selected.
- **"Launch Swarm" button** (Zap icon, violet color): Starts the swarm pipeline
- **How to test**: Type a task description and click "Launch Swarm"
- **Success**: Pipeline starts; stage cards appear below
- **Failure**: Button disabled without explanation, or launch fails

### 13.3 Pipeline Stage Cards

- **Visible when**: Swarm is running or completed
- **What it does**: Shows each stage (Research, PRD Builder, Coder) with:
  - Status badge (Pending/Running/Waiting/Done/Failed)
  - Stage label and model/context info
  - Trigger file and output file paths
  - Error message (if failed)
  - "Send walkie-talkie" button (Radio icon) on running stages -- opens injection input
  - Flow arrows between stages (rotated ArrowRight)
- **Controls**:
  - **Stop button** (Square icon): Visible when running. Stops the swarm.
  - **New Swarm button**: Visible when done. Resets to task input state.
- **How to test**: Launch a swarm and observe stage progression
- **Success**: Stages progress from Pending to Running to Done/Failed
- **Failure**: Stages don't update, or stop button doesn't work

### 13.4 Shared Files Section

- **Visible when**: Swarm has produced shared files
- **What it does**: Lists shared workspace files with name, size, and Eye icon. Clicking a file opens a preview modal with syntax-highlighted content.
- **How to test**: After a swarm produces files, click one
- **Success**: Preview modal shows file content
- **Failure**: Files not listed, or preview fails

### 13.5 Walkie-Talkie Injection (per-stage)

- **Triggered by**: "Send walkie-talkie" button on a running stage card
- **What it does**: Shows an amber input bar at the bottom with the target stage name. Type a message and click Send (or Enter) to inject it into that stage's agent.
- **How to test**: Click "Send walkie-talkie" on a running stage, type a message, click Send
- **Success**: Message sends; input clears; injection target closes
- **Failure**: Input doesn't appear, or message doesn't send

---

## Section 14: Token Log Panel

A left-side panel (320px) that sits to the left of the chat area.

### 14.1 Visibility

- Controlled by the 3-state toggle (Section 7.2)
- Auto mode: Shows during streaming, hides when idle
- On mode: Always visible
- Off mode: Never visible

### 14.2 Content

- Shows a running log of token processing events:
  - **assistant_turn** (cyan badge): Model thinking
  - **tool_call** (yellow badge): Tool invocations
  - **tool_result** (orange badge): Tool results
  - **result_summary** (green badge): Turn completion summaries
- Each entry shows: event type badge, token counts (input/output), cost, duration, cumulative cost
- **Header buttons**: Download (export log as JSON), Clear (trash icon), Close (X)
- **Summary section**: Shows total cost, input/output tokens, cache info

### 14.3 How to Test

1. Set token log toggle to "On"
2. Send a message to trigger agent work
3. Observe entries appearing in real-time

- **Success**: Entries appear with correct token counts, costs, and durations
- **Failure**: Panel empty despite streaming, or costs incorrect

---

## Section 15: Keyboard Shortcuts

Press `?` to open the shortcuts modal, or click the Keyboard icon in the nav bar.

| Shortcut | Action | Context |
|----------|--------|---------|
| Ctrl/Cmd+N | New conversation | Always |
| Ctrl/Cmd+L | Toggle library panel | Always |
| Ctrl/Cmd+B | Toggle sidebar | Always |
| Ctrl/Cmd+F | Focus search | Always |
| Ctrl/Cmd+E | Export current chat | With active chat |
| / | Focus chat input | Always |
| 1 | Toggle Research panel | Split view |
| 2 | Toggle PRD Builder panel | Split view |
| 3 | Toggle Coder panel | Split view |
| ? | Show keyboard shortcuts | Always |
| Esc | Close modal | When modal is open |

---

## Section 16: Modals Reference

Summary of all modal dialogs accessible from the Workspace page:

| Modal | Trigger | Component |
|-------|---------|-----------|
| Keyboard Shortcuts Help | `?` key or Keyboard icon | WorkspaceKeyboardHelp |
| User Guide & Notes | "Guide" button in nav bar | WorkspaceUserGuide |
| Category Manager | "Manage Categories" button in sidebar | CategoryManager |
| Fork Chat | "..." menu > "Fork Chat" | ChatForkModal |
| Inject from Chat | "..." menu > "Inject from Chat" | InjectFromChatModal |
| File Upload | "Upload" button in Library tab | FileUploadModal |
| Text Paste | "Paste" button in Library tab | FileUploadModal (text mode) |
| Repo Connector | "Connect Repository" in Repos tab | RepoConnector |
| File Preview | Click a file in Library browser | FilePreview |
| Repo File Preview | Click a file in Repo browser | Inline modal in WorkspaceLibrary |
| Library Picker | BookOpen button in chat input | LibraryPickerModal |
| Save to Library | "Save to Library" on assistant message | SaveToLibraryModal |
| Swarm File Preview | Click a shared file in Swarm panel | Inline modal in SwarmPanel |

---

## Section 17: Error States and Edge Cases

### 17.1 No Working Directory

- Git Activity Widget: Hidden or non-functional
- CI Status Widget: Not initialized
- Git Branch in header: Hidden
- Repo/PR links in header: Hidden
- Swarm panel: Shows warning "Select a working directory first"

### 17.2 WebSocket Connection Failure

- Connection indicator shows red dot + WifiOff
- Disconnection banner appears with error details and Retry link
- Messages area shows "Connection Failed" with error details, Retry Connection button, and Back to Conversations button
- Rate limit errors shown in error details

### 17.3 Empty Library

- Library tab shows folder browser (which may be empty)
- Library Picker Modal shows "This folder is empty"

### 17.4 No Conversations

- Sidebar shows "No conversations yet" with MessageSquare icon
- Chat area shows empty state with "No conversations yet" prompt

### 17.5 Streaming Interruption

- If the page is refreshed during streaming, the conversation is preserved but streaming stops
- Reconnecting to the conversation shows previously received messages

---

## Section 18: Data Persistence

| Data | Storage | Scope |
|------|---------|-------|
| Panel collapse state (Research/PRD/Coder) | localStorage | Per-browser |
| Panel model selection (Research/PRD/Coder) | localStorage | Per-browser |
| Model preset index | localStorage | Per-browser |
| Context mode | localStorage | Per-browser |
| Token log mode (Auto/On/Off) | localStorage | Per-browser |
| Draft messages | localStorage per conversation ID | Per-browser, per-conversation |
| User Guide position & size | localStorage | Per-browser |
| User Guide notes | localStorage | Per-browser |
| Walkie-talkie settings | Server (Settings API) | Global |
| Conversations, messages, categories | Server (SQLite) | Global |
| Library files & folders | Server (SQLite + filesystem) | Global |
