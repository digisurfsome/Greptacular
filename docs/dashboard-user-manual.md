# Dashboard Page -- Comprehensive User Manual for Automated QA

This document covers every interactive element on the Dashboard page (`/#/dashboard`). It is derived from the actual source code and is intended as the authoritative reference for AI agents performing end-to-end QA testing.

Source files referenced:
- `ui/src/pages/DashboardPage.tsx`
- `ui/src/components/workspace/WorkspaceSidebar.tsx`
- `ui/src/components/workspace/WorkspaceChat.tsx`
- `ui/src/components/workspace/WorkspaceChatHeader.tsx`
- `ui/src/components/workspace/RepoSelector.tsx`
- `ui/src/components/workspace/ConversationSearch.tsx`
- `ui/src/components/workspace/CategoryManager.tsx`
- `ui/src/components/workspace/TokenLogPanel.tsx`
- `ui/src/components/workspace/EnhancedContextBudgetBar.tsx`

---

## Section 1: Page Layout

The Dashboard page is a full-screen layout for running 1, 2, or 3 independent AI sessions side-by-side. It shares the sidebar and chat components with the Workspace page but adds multi-pane management and per-pane provider selection.

### Overall Structure (top to bottom, left to right)

1. **Top Navigation Bar** (~40px height, full width, wraps on narrow screens) -- breadcrumb, repo selector, layout mode buttons, workspace link
2. **Main Content Row** (fills remaining height):
   - **Left: Sidebar** (272px wide, collapsible to 0) -- conversations, new chat form, search, categories (shared `WorkspaceSidebar` component)
   - **Right: Pane Area** (flexible width) -- 1, 2, or 3 side-by-side chat panes, each with its own provider selector and WorkspaceChat instance

### Layout Modes

- **Single** (1 pane): One full-width pane. Default provider: Claude.
- **Dual** (2 panes): Two side-by-side panes separated by a border. Default providers: Claude + Codex.
- **Triple** (3 panes): Three side-by-side panes. Default providers: Claude + Codex + Gemini.

The default layout mode is **dual**. Layout mode is persisted to `localStorage` under the key `dashboard-layout`.

### How to Test Layout

1. Navigate to `/#/dashboard`
2. **Success**: Page loads with sidebar on left, pane area on right with the correct number of panes for the active layout mode
3. **Failure**: Blank screen, infinite spinner, or components overlapping

---

## Section 2: Top Navigation Bar

Location: Fixed bar at the very top of the page. Uses `flex-wrap` so items wrap on narrow screens.

### 2.1 Mobile Sidebar Toggle (Menu icon)

- **Location**: Far left of nav bar, only visible below the `md` breakpoint (~768px)
- **What it does**: Toggles the sidebar overlay drawer on mobile. When open, a dark backdrop (black/40 opacity) covers the pane area and clicking the backdrop closes the sidebar.
- **How to test**: Resize browser to below 768px width, click the Menu icon
- **Success**: Sidebar slides in as a fixed overlay (272px wide, z-50) with shadow. Backdrop darkens the pane area. Clicking backdrop or selecting a conversation closes the drawer.
- **Failure**: Sidebar doesn't appear, no backdrop, or clicking backdrop doesn't close

### 2.2 Back to AutoForge Button (ArrowLeft icon + "AutoForge" text)

- **Location**: Left side of nav bar, after the mobile menu button
- **What it does**: Navigates back to the main AutoForge page by setting `window.location.hash = ''`
- **Note**: The "AutoForge" text label is hidden on screens narrower than the `sm` breakpoint (~640px) via `hidden sm:inline`.
- **How to test**: Click the button
- **Success**: Page navigates to the AutoForge main page (project dashboard)
- **Failure**: Nothing happens, or navigates to wrong page

### 2.3 Breadcrumb "Dashboard" Label

- **Location**: After the ChevronRight separator, right of the back button
- **What it does**: Static text label showing current page name. Not interactive.
- **How to test**: Verify text "Dashboard" is visible
- **Success**: Label reads "Dashboard" in bold semibold font at `text-xs` size
- **Failure**: Missing or wrong text

### 2.4 RepoSelector (Select Repo Dropdown)

- **Location**: After a second ChevronRight separator, right of the "Dashboard" label. Hidden on mobile (below `sm` breakpoint).
- **What it does**: Opens a dropdown for selecting a GitHub repository. Shows FolderGit2 icon + selected repo name (or "Select Repo" if none selected) + ChevronDown icon. When a repo is selected, an X (clear) button replaces the ChevronDown.
- **Prerequisite**: `gh` CLI must be installed and authenticated for repo list to populate.
- **How to test**:
  1. Click the "Select Repo" button
  2. Dropdown opens with search input and repository list
  3. Type to filter, click a repo
- **Success**: Dropdown opens (~320px wide). Repos load with name, lock icon (private), and relative update time. Selecting a repo shows "Cloning..." then displays the repo name. The selected path is persisted to `localStorage` under the key `dashboard-working-dir` and shared across all panes.
- **Failure**: Dropdown doesn't open, "Loading repositories..." persists, or error message (e.g., "gh CLI not installed")

#### 2.4a RepoSelector -- Search Filter

- **How to test**: With dropdown open, type a partial repo name
- **Success**: Repo list filters by name, nameWithOwner, or description (case-insensitive)
- **Failure**: No filtering, or all repos disappear

#### 2.4b RepoSelector -- Clear Selection

- **How to test**: With a repo selected, click the X button
- **Success**: Selection clears, button returns to "Select Repo" with ChevronDown icon
- **Failure**: Selection not cleared

#### 2.4c RepoSelector -- Close on Outside Click / Escape

- **How to test**: Open the dropdown, then click outside it (or press Escape)
- **Success**: Dropdown closes, filter text resets
- **Failure**: Dropdown stays open

### 2.5 Layout Mode Buttons (1 / 2 / 3)

- **Location**: Right side of nav bar. Hidden on mobile (below `md` breakpoint) since panes stack automatically on mobile.
- **What they do**: Switch between single, dual, and triple pane layouts. Each button shows an icon and a number label:
  - **1** (Square icon): Single pane layout
  - **2** (Columns2 icon): Dual pane layout
  - **3** (Columns3 icon): Triple pane layout
- **Active state**: The active layout button has `bg-primary text-primary-foreground` styling; inactive buttons have `text-muted-foreground`.
- **How to test**: Click each layout button
- **Success**:
  - Clicking "1" shows a single full-width pane
  - Clicking "2" shows two side-by-side panes
  - Clicking "3" shows three side-by-side panes
  - Active button highlights with primary color
  - Pane count adjusts: adding panes picks unused providers (Claude, Codex, Gemini); shrinking keeps the first N panes
- **Failure**: Pane count doesn't change, wrong button highlights, or layout breaks

### 2.6 Workspace Link ("Workspace" text)

- **Location**: Far right of nav bar, after a vertical divider
- **What it does**: Navigates to the Workspace page at `/#/workspace`
- **How to test**: Click the button
- **Success**: Page navigates to `/#/workspace`
- **Failure**: Navigation doesn't happen

---

## Section 3: Sidebar

The Dashboard uses the shared `WorkspaceSidebar` component. It behaves identically to the Workspace page sidebar with one key difference: the sidebar's `activeProvider` prop is driven by the first pane's provider, which changes which model presets appear in the New Chat form.

### 3.1 Sidebar Header -- "Conversations" Title + Buttons

- **Location**: Top of sidebar, with border below
- **Elements**:
  - "Conversations" text label (not interactive)
  - **Select Mode Button** (CheckSquare icon): Toggles select mode for bulk operations. When active, shows X icon instead.
  - **Collapse/Expand Button** (PanelLeftClose / PanelLeftOpen icon): Collapses sidebar to 0 width or expands it back to 272px.

### 3.1a Select Mode Button

- **How to test**: Click the CheckSquare icon
- **Success**: Checkboxes appear on every conversation row; bulk action bar appears with "All/None" toggle and "Delete (N)" button
- **Failure**: Checkboxes don't appear, or select mode doesn't toggle off when clicking X

### 3.1b Collapse/Expand Sidebar Button

- **How to test**: Click PanelLeftClose icon
- **Success**: Sidebar collapses to 0 width; pane area expands to fill the space. Click PanelLeftOpen to restore.
- **Failure**: Sidebar doesn't collapse, or doesn't restore properly

### 3.2 "New Chat" Button

- **Location**: Below sidebar header, full width
- **What it does**: Toggles the new chat creation form open/closed. Shows a Plus icon, "New Chat" text, and a ChevronDown that rotates 180 degrees when open.
- **How to test**: Click the button
- **Success**: Form slides in below the button with Name, Folder, Repo Toggle, Model pills, optional Thinking Effort, and "Start Chat" button. ChevronDown rotates to point up.
- **Failure**: Form doesn't appear, or appears without animation

### 3.3 New Chat Form -- Name Input

- **Location**: First field in the creation form
- **What it does**: Optional text input for naming the conversation. Auto-focused when form opens. Pressing Enter submits the form. Pressing Escape cancels.
- **How to test**:
  1. Open the new chat form
  2. Type a name (e.g. "Test Chat")
  3. Press Enter
- **Success**: Conversation is created with the given name and appears in the sidebar; the conversation is loaded into the first pane
- **Failure**: Input doesn't focus, or Enter doesn't submit

### 3.4 New Chat Form -- Folder/Category Dropdown

- **Location**: Second field in the creation form, labeled "Folder"
- **What it does**: Select dropdown to assign the new conversation to a category/folder. Options include "No folder" (default) plus all user-created categories.
- **How to test**: Click the dropdown and select a category
- **Success**: Dropdown shows existing categories; selected value persists when chat is created
- **Failure**: Dropdown empty, or category not saved

### 3.5 New Chat Form -- Attach Repository Toggle

- **Location**: Third field in the creation form, labeled "Attach Repository"
- **What it does**: A custom toggle switch. When ON, reveals the RepoSelector dropdown below it. When a repo is selected, the working directory is set for the new conversation.
- **How to test**:
  1. Click the toggle switch
  2. When RepoSelector appears, click it to see the GitHub repo list
- **Success**: Toggle animates, RepoSelector dropdown appears
- **Failure**: Toggle doesn't animate, RepoSelector doesn't appear

### 3.6 New Chat Form -- Model Preset Pills (Provider-Aware)

- **Location**: Below the repo toggle, labeled "Model"
- **What it does**: Horizontal pill selector (radio group) for choosing model + context. The pills displayed depend on the first pane's active provider:
  - **Claude**: "Opus 4.6 . 1M", "Sonnet 4.6 . 1M", "Opus 4.6 . 200K". Active colors: blue for Opus 1M, violet for Sonnet, zinc for 200K.
  - **Codex**: "GPT-5.4", "GPT-5.4 Pro", "GPT-5.3", "o3", "o4-mini" (fetched from backend). Active color: emerald.
  - **Gemini**: "Gemini 3.1 Pro", "Gemini 3.1 Flash", "Gemini 3.1 Flash Lite" (fetched from backend). Active color: violet.
- **Important**: Changing the first pane's provider automatically changes which model pills are shown in the sidebar.
- **How to test**: Click each pill; switch the first pane's provider and observe the pills change
- **Success**: Selected pill highlights with the correct provider color; pills update when provider changes
- **Failure**: Pill doesn't highlight, wrong pills shown, or pills don't update on provider switch

### 3.7 New Chat Form -- Thinking Effort Selector (Claude Only)

- **Location**: Below model pills, labeled "Thinking Effort". Only visible when the first pane's provider is Claude. Grayed out (opacity 35%, pointer-events disabled) unless the Opus 1M preset is selected.
- **What it does**: Three-pill selector for Low / Medium / High thinking effort. Each has a tooltip showing Anthropic's recommended use cases:
  - **Low** (emerald): Quick lookups, classification, routing, sub-agents
  - **Medium** (blue): Agentic coding, tool use, code generation
  - **High** (orange): Complex analysis, nuanced reasoning, quality-critical
- **When it's active**: Only when model preset is Opus + 1M context AND provider is Claude
- **How to test**:
  1. Ensure first pane provider is Claude
  2. Select "Opus 4.6 . 1M" model preset
  3. Click each effort level pill
- **Success**: Effort selector becomes interactive (full opacity); each pill highlights with its color; use case description appears below
- **Failure**: Selector stays grayed out on Opus 1M, or appears for non-Claude providers

### 3.8 New Chat Form -- Start Chat Button

- **Location**: Bottom of the creation form
- **What it does**: Creates the conversation via the API with the configured name, category, model, context mode, effort level, and provider (matching the first pane's active provider). Shows "Creating..." during the mutation. On success, selects the new conversation in the first pane and closes the form.
- **How to test**: Fill out the form and click "Start Chat"
- **Success**: Button shows "Creating...", then conversation appears in sidebar and first pane loads it
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
  2. Type a longer query (3+ chars) -- overlay dropdown appears with search results
  3. Click a result in the dropdown
  4. Click the X to clear
  5. Press Escape to clear and close
- **Success**: Filtering works at both levels; clicking a result selects the conversation and loads it into the first available pane
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
- **Success**: Count updates as checkboxes change; delete removes conversations; any pane showing a deleted conversation clears to empty state
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

- **What it does**: Badge appearance and behavior depends on the conversation's provider:
  - **Claude conversations**: Clickable badge that cycles through model/context combinations. Shows abbreviation using middle-dot separator: "O.1M" (Opus 1M, blue), "S.1M" (Sonnet 1M, violet), "O.200K" (Opus 200K, zinc). Cycle order: Opus 1M -> Sonnet 1M -> Opus 200K -> Opus 1M. Clicking uses `e.stopPropagation()` so it does not select the conversation.
  - **Codex conversations**: Static (non-clickable) emerald badge. Model abbreviations: `5.4` (GPT-5.4), `5.4P` (GPT-5.4 Pro), `5.3` (GPT-5.3), `o3`, `o4m` (o4-mini), `5C` (GPT-5-Codex).
  - **Gemini conversations**: Static (non-clickable) violet badge. Model abbreviations: `3.1P` (Gemini 3.1 Pro), `3.1F` (Gemini 3.1 Flash), `3.1L` (Gemini 3.1 Flash Lite), `Pro`, `Flsh` (Flash), `Lite` (Flash Lite).
- **How to test**: Click the badge on a Claude conversation; observe badges on Codex/Gemini conversations
- **Success**: Claude badges cycle correctly; Codex/Gemini badges are static with correct abbreviations and colors
- **Failure**: Badge doesn't cycle, wrong abbreviation, or non-Claude badges are clickable

#### 4.4b Activity Indicators (left edge of row)

- **Streaming/Running**: Cyan pulsing glow bar on left edge + cyan pulsing dot + shimmer sweep overlay. Appears when the conversation has an active WebSocket stream or a running background session.
- **Waiting Input**: Yellow pulsing glow bar + yellow pulsing dot. Appears when the agent is waiting for user response.
- **Completed**: Small green static dot. Appears when a background session recently completed.
- **Failed**: Small red static dot + red bar on left edge. Appears when a background session failed.
- **How to test**: Start a conversation and send a message to trigger streaming
- **Success**: Cyan glow appears during streaming; disappears when response completes
- **Failure**: No activity indicator despite active streaming

#### 4.4c Clicking a Conversation Row

- **Normal mode**: Selects the conversation and loads it into the first available pane. If the conversation has a stored provider, the pane's provider updates to match. On mobile, the sidebar drawer auto-closes.
- **Select mode**: Toggles the checkbox for that row (doesn't navigate)
- **How to test**: Click a conversation row
- **Success**: Conversation loads in a pane; sidebar row highlights with accent background
- **Failure**: Chat doesn't load, or loads in wrong pane

#### 4.4d Hover Actions (appear on mouse hover, right side of row)

Three icon buttons appear when hovering over a conversation row (not in select mode):

1. **FolderPlus button**: Opens an inline edit popover for assigning folder and repository
   - Popover contains: "Move to Folder" dropdown, "Attach Repository" RepoSelector, "Done" button
   - Closes when clicking outside the popover
2. **Pin button** (Pin icon): Toggles pinning. Pinned conversations appear in the "Pinned" group at the top with a star icon.
3. **Delete button** (Trash2 icon, turns red on hover): Deletes the conversation immediately (no confirmation dialog). If the deleted conversation was loaded in a pane, that pane clears to empty state.

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
- **Edit (Pencil) Button**: Switches the row to edit mode with: editable name input, color swatch palette, checkmark save button. Press Enter to save.
- **Delete (Trash) Button**: Deletes the category immediately (no confirmation).
- **Empty state**: "No categories yet. Create one below."

#### 5.2b Add Category Form (bottom of modal)

- Text input for new category name + "Add" button (Plus icon)
- Color palette row (preset colors as round buttons)
- Enter key submits the form

#### 5.2c Close Button (X, top-right) and Escape key

- **How to test**: Click X or press Escape
- **Success**: Modal closes
- **Failure**: Modal stays open

---

## Section 6: Pane Headers

Each pane in the Dashboard has a thin header bar with provider selection and pane controls.

### 6.1 Provider Selector (Pill Strip)

- **Location**: Left side of each pane's header bar
- **What it does**: A rounded-full pill strip with three buttons in a radio group: **Claude** (blue), **Codex** (emerald), **Gemini** (violet). The active provider's button is filled with its color; inactive buttons use card background.
- **Important behavior**: Switching a pane's provider resets that pane's `conversationId` to null (clears the current conversation) because conversations are provider-specific. It also resets the model preset index in the sidebar to 0.
- **How to test**: Click each provider pill in a pane's header
- **Success**:
  - Active pill fills with provider color (blue/emerald/violet)
  - Pane's chat area clears to empty state (conversation reset)
  - If it's the first pane, sidebar model pills update to match the new provider
  - Pane label text updates to the provider name (e.g., "CLAUDE", "CODEX", "GEMINI")
- **Failure**: Provider doesn't switch, conversation not cleared, or sidebar pills don't update

### 6.2 Pane Label

- **Location**: Center of pane header, right of the provider selector
- **What it does**: Shows the provider name in uppercase with tracking-wider styling (e.g., "CLAUDE"). If a conversation is loaded, shows the conversation ID suffix (e.g., "CLAUDE #42") in muted color.
- **How to test**: Load a conversation in a pane, observe the label
- **Success**: Label shows provider name + conversation ID
- **Failure**: Label missing or incorrect

### 6.3 Clear Pane Button (X icon)

- **Location**: Right side of pane header, only visible when a conversation is loaded in that pane
- **What it does**: Clears the pane's conversation (sets `conversationId` to null), returning it to the empty state. Does NOT delete the conversation.
- **How to test**: Load a conversation in a pane, click the X
- **Success**: Pane returns to empty state; conversation still exists in the sidebar
- **Failure**: Button not visible, or conversation deleted from sidebar

### 6.4 Collapse Pane Button (ChevronsLeft / ChevronsRight icon)

- **Location**: Right side of pane header, only visible when there are multiple panes (dual or triple layout). Hidden on mobile. The last pane shows ChevronsRight; all others show ChevronsLeft.
- **What it does**: Collapses the pane to a thin vertical bar (~40px wide, `w-10`) showing the provider label in rotated text. The remaining panes expand to fill the freed space.
- **How to test**: In dual or triple layout, click the collapse button on a pane
- **Success**: Pane collapses to a thin bar with rotated uppercase label. Bar has provider-tinted background (blue-500/5 for Claude, emerald-500/5 for Codex, violet-500/5 for Gemini).
- **Failure**: Pane disappears entirely, or remaining panes don't expand

### 6.5 Collapsed Pane Bar (Expand on Click)

- **Location**: Where a collapsed pane was -- a 40px-wide vertical strip
- **What it does**: Shows the pane label in vertical text (10px bold, tracking-widest, rotated 180 degrees). Clicking the bar expands the pane back to its normal width.
- **How to test**: Collapse a pane (Section 6.4), then click the collapsed bar
- **Success**: Pane expands to normal width; collapsed bar disappears
- **Failure**: Pane stays collapsed, or expands to wrong size

---

## Section 7: Pane Chat Area

Each pane contains a full `WorkspaceChat` instance. The chat component handles message display, user input, WebSocket communication, and session management.

### 7.1 Empty State (No Conversation Selected)

- **Location**: Center of the pane when no conversation is loaded
- **What it does**: Shows an empty state message with the panel label (e.g., "CLAUDE SESSION") and a prompt to start a new conversation from the sidebar.
- **How to test**: Clear a pane's conversation or switch to an unused pane
- **Success**: Empty state message visible with correct panel label
- **Failure**: Blank pane with no messaging, or stale conversation visible

### 7.2 Chat Header (WorkspaceChatHeader)

When a conversation is loaded, each pane shows a full chat header with:
- **Editable title**: Click to rename. Pencil icon on hover. Enter saves, Escape cancels, blur saves.
- **Category dropdown**: Native select to change the conversation's category
- **Tags section**: Add/remove tag chips
- **Git branch indicator**: Shows branch name when working directory is a git repo
- **Connection status indicator**: Green (connected), yellow (connecting), red (disconnected)
- **Active model badge**: Colored pill showing the active model preset and confirmed model ID

### 7.3 Message Display Area

- Displays conversation messages with Markdown rendering
- User messages and assistant messages styled distinctly
- Streaming indicator during active responses
- Smart auto-scroll: follows new content unless user has scrolled up

### 7.4 Chat Input Area

- Text input with Enter to send, Shift+Enter for newline
- File attachment (Paperclip icon), Image attachment (ImagePlus icon), Library attachment (BookOpen icon)
- Image paste (Ctrl+V) with thumbnail preview
- Draft persistence to localStorage per conversation ID
- Disabled during streaming/loading

### 7.5 Token Log Panel

- Three-state toggle in chat header: Auto / On / Off
- Side panel showing token-by-token streaming data
- "Auto" shows panel during streaming, hides when idle

### 7.6 Context Budget Bar

- Thin progress bar showing token usage as a percentage
- Usage text: "N% - XX.XK/200K" or "N% - XX.XK/1M"
- Message count display
- 200K pricing cliff marker on 1M context panels

---

## Section 8: Multi-Pane Interactions

### 8.1 Conversation Assignment from Sidebar

- **What it does**: Clicking a conversation in the sidebar assigns it to a pane. Assignment logic:
  1. If the conversation has a stored provider, prefer an empty pane matching that provider
  2. If no matching empty pane, use any empty pane
  3. If no empty panes, use the first pane (pane 0)
- If the conversation's provider differs from the target pane's provider, the pane's provider updates to match.
- **How to test**: Create conversations for different providers, click each in the sidebar
- **Success**: Conversations load in appropriate panes; provider syncs correctly
- **Failure**: Conversation loads in wrong pane, or provider doesn't sync

### 8.2 Cross-Pane Streaming Indicators

- **What it does**: The Dashboard tracks streaming state for all panes. Each pane reports its streaming status to the parent. The sidebar receives a `Set<number>` of all streaming conversation IDs, so activity indicators appear for any conversation with an active stream in any pane.
- **How to test**: Load conversations in two panes, send messages in both
- **Success**: Sidebar shows streaming indicators for both conversations simultaneously
- **Failure**: Only one indicator shows, or indicators don't appear

### 8.3 Shared Working Directory

- **What it does**: The `workingDirectory` selected via the nav bar RepoSelector is shared across ALL panes. Each pane's `WorkspaceChat` receives the same `workingDirectory` prop.
- **How to test**: Select a repo in the nav bar, observe all panes
- **Success**: All panes use the same working directory for git features and agent sessions
- **Failure**: Some panes don't reflect the selected repo

### 8.4 Pending Model/Context for New Chats

- **What it does**: Only the first pane (index 0) receives `pendingModel`, `pendingContextMode`, `pendingEffort`, and `newChatKey` props. This means new conversations created from the sidebar always target the first pane.
- **How to test**: Create a new conversation from the sidebar
- **Success**: New conversation appears in the first pane only
- **Failure**: Conversation appears in wrong pane, or not at all

### 8.5 Pane Deletion Cascade

- **What it does**: When a conversation is deleted (from sidebar hover actions or bulk delete), all panes with that conversation clear to empty state. The streaming state is also cleaned up.
- **How to test**: Load a conversation in a pane, delete it from the sidebar
- **Success**: Pane clears to empty state; no console errors
- **Failure**: Pane still shows deleted conversation, or crashes

---

## Section 9: Session Persistence (localStorage)

The Dashboard persists its state across page reloads using the following localStorage keys:

### 9.1 Layout Mode

- **Key**: `dashboard-layout`
- **Values**: `single`, `dual`, or `triple`
- **Default**: `dual` (if key doesn't exist or value is invalid)
- **How to test**: Set layout to triple, reload the page
- **Success**: Page loads in triple layout
- **Failure**: Page resets to dual

### 9.2 Pane State

- **Key**: `dashboard-panes`
- **Values**: JSON array of `PaneState` objects, each containing: `id`, `conversationId`, `provider`, `label`, `collapsed`, `attachedSessionId`
- **How to test**: Load conversations in panes, collapse a pane, reload the page
- **Success**: Panes restore with same providers, conversation IDs, and collapse states
- **Failure**: Panes reset to defaults, or conversation IDs lost

### 9.3 Working Directory

- **Key**: `dashboard-working-dir`
- **Values**: String path of the selected repository, or absent if none selected
- **How to test**: Select a repo, reload the page
- **Success**: Repo selector shows the previously selected repo
- **Failure**: Repo selector resets to "Select Repo"

---

## Section 10: Mobile Responsive Behavior

### 10.1 Sidebar as Overlay Drawer

- **Trigger**: Screen width below `md` breakpoint (~768px)
- **What it does**: Sidebar becomes a fixed overlay panel (z-50, full height, 272px wide) that opens over the pane area. A dark backdrop (black/40) appears behind it. Tapping the backdrop or selecting a conversation closes the drawer.
- **How to test**: Resize browser below 768px, tap the Menu icon
- **Success**: Sidebar slides in as overlay; backdrop visible; closes on backdrop tap
- **Failure**: Sidebar pushes content instead of overlaying, or no backdrop

### 10.2 Single Pane on Mobile

- **What it does**: On mobile (below `md` breakpoint), only the first non-collapsed pane is visible. Additional panes are hidden with `hidden md:flex`. This prevents unusable tiny pane widths.
- **How to test**: Set triple layout, resize below 768px
- **Success**: Only one pane visible; layout mode buttons hidden
- **Failure**: All three tiny panes visible, or no pane visible

### 10.3 Layout Buttons Hidden on Mobile

- **What it does**: The layout mode buttons (1/2/3) are wrapped in `hidden md:flex` so they don't appear on mobile, since the mobile layout always shows a single pane.
- **How to test**: Resize below 768px
- **Success**: Layout buttons not visible
- **Failure**: Layout buttons still visible on mobile

### 10.4 Collapsed Pane Bars Hidden on Mobile

- **What it does**: Collapsed pane bars (thin vertical strips) are wrapped in `hidden md:flex` since they don't work well on mobile. Collapsed panes are simply hidden on mobile.
- **How to test**: Collapse a pane, resize below 768px
- **Success**: No thin vertical bar visible on mobile
- **Failure**: Thin bar visible on mobile

### 10.5 RepoSelector Hidden on Mobile

- **What it does**: The breadcrumb RepoSelector is hidden below `sm` breakpoint (`hidden sm:block`). On mobile, repos can still be attached via the sidebar New Chat form's "Attach Repository" toggle.
- **How to test**: Resize below 640px
- **Success**: RepoSelector not visible in nav bar; available in sidebar form instead
- **Failure**: RepoSelector visible but too cramped, or not accessible at all

### 10.6 AutoForge Text Hidden on Mobile

- **What it does**: The "AutoForge" text next to the back arrow is hidden below `sm` breakpoint (`hidden sm:inline`). The ArrowLeft icon remains visible for navigation.
- **How to test**: Resize below 640px
- **Success**: Only arrow icon visible, "AutoForge" text hidden
- **Failure**: Text still visible and causing layout issues
