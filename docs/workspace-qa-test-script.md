# Workspace Page -- QA Test Script

This is an executable test script for AI agents to verify every feature on the Workspace page (`/#/workspace`). Each test has a concrete action, expected result, pass/fail criteria, and investigation guidance on failure.

**Prerequisites for all tests:**
- AutoForge server running at `localhost:8888`
- Browser open to `http://localhost:8888`
- At least one GitHub repository accessible via `gh` CLI (for repo-related tests)
- Console DevTools open (F12) to monitor for errors throughout

**Notation:**
- "Click X" means left-click once on element X
- "Hover X" means move mouse cursor over element X without clicking
- "Type X" means type the text X into the currently focused input
- "Press X" means press keyboard key X
- "Verify X" means visually confirm X is true

---

## Test Group 1: Page Load

### Test 1.1: Navigate to Workspace
- **Setup**: Server running at localhost:8888
- **Action**: Navigate to `http://localhost:8888/#/workspace`
- **Expected**: Workspace page renders with three zones: sidebar (left, ~272px), chat area (center, flexible), library panel (right, ~288px). A 40px top navigation bar spans full width.
- **Pass**: All three zones visible, no overlapping elements, no blank sections
- **Fail**: Blank screen, infinite spinner, missing zones, or components overlapping
- **If Failed**: Check browser console for JavaScript errors. Check `WorkspacePage.tsx` for render crashes. Verify the `/#/workspace` route is registered in `App.tsx`.

### Test 1.2: No Console Errors on Load
- **Setup**: Open browser DevTools Console (F12) before navigating
- **Action**: Navigate to `http://localhost:8888/#/workspace`
- **Expected**: No red error messages in the console. Warnings are acceptable but errors are not.
- **Pass**: Zero red console errors
- **Fail**: One or more red console errors appear
- **If Failed**: Note the exact error text and stack trace. Common issues: missing API endpoints (check server routers), undefined state variables (check hooks), failed WebSocket connections (check server is running).

### Test 1.3: Top Nav Bar Elements Present
- **Setup**: On Workspace page
- **Action**: Visually inspect the top navigation bar (40px height, full width)
- **Expected**: The following elements are visible left-to-right:
  1. Back arrow + "AutoForge" text (far left)
  2. ChevronRight separator + "Workspace" label
  3. Right side: "G" button, CI indicator, "Split" button, "Swarm" button, "Roles" button, "Dashboard" button, "Guide" button, Keyboard icon
- **Pass**: All listed elements are present and visible
- **Fail**: Any element missing or mispositioned
- **If Failed**: Check `WorkspacePage.tsx` nav bar render. Verify imports for `GitActivityWidget`, `CIStatusWidget`, and nav button components.

### Test 1.4: Sidebar Visible with Header
- **Setup**: On Workspace page
- **Action**: Look at the left sidebar
- **Expected**: Sidebar visible (~272px wide) with "Conversations" header text, a select-mode toggle button (CheckSquare icon), and a collapse button (PanelLeftClose icon)
- **Pass**: Sidebar header with all buttons visible
- **Fail**: Sidebar missing, collapsed by default, or header elements missing
- **If Failed**: Check `WorkspaceSidebar.tsx` initial render state. Verify `sidebarCollapsed` default is false.

### Test 1.5: Library Panel Visible
- **Setup**: On Workspace page
- **Action**: Look at the right panel
- **Expected**: Library panel visible (~288px wide) with three tabs: "Library" (FileText icon), "Repos" (GitBranch icon), "WT" (Radio icon), plus a ">>" collapse button
- **Pass**: Panel visible with all three tabs and collapse button
- **Fail**: Panel missing, collapsed by default, or tabs missing
- **If Failed**: Check `WorkspaceLibrary.tsx` render. Verify library panel collapse state default.

### Test 1.6: Empty State Display
- **Setup**: Fresh workspace with no conversations
- **Action**: Observe the sidebar and chat area
- **Expected**: Sidebar shows "No conversations yet" with MessageSquare icon. Chat area shows empty state message.
- **Pass**: Empty state messages visible in both sidebar and chat area
- **Fail**: Blank areas without empty state messaging, or error displayed
- **If Failed**: Check conversation list query in `WorkspaceSidebar.tsx`. Verify the API endpoint `/api/workspace/conversations` returns empty array, not an error.

---

## Test Group 2: New Chat Form

### Test 2.1: Open New Chat Form
- **Setup**: On Workspace page, sidebar visible
- **Action**: Click the "New Chat" button (Plus icon + "New Chat" text + ChevronDown)
- **Expected**: Form slides open below the button showing: Name input, Folder dropdown, Attach Repository toggle, Model pills, and "Start Chat" button. The ChevronDown icon rotates 180 degrees to point up.
- **Pass**: Form visible with all fields, chevron rotated
- **Fail**: Form does not appear, fields missing, no animation
- **If Failed**: Check `WorkspaceSidebar.tsx` `showNewChatForm` state toggle. Verify CSS transition classes.

### Test 2.2: Name Input Auto-Focus
- **Setup**: New Chat form is open (Test 2.1)
- **Action**: Observe cursor position immediately after form opens
- **Expected**: The Name text input is auto-focused (cursor blinking inside it)
- **Pass**: Input has focus, cursor visible
- **Fail**: Input not focused, user must click to focus
- **If Failed**: Check `autoFocus` prop or `useEffect` focus call on the name input in `WorkspaceSidebar.tsx`.

### Test 2.3: Name Input Enter to Submit
- **Setup**: New Chat form open, Name input focused
- **Action**: Type "Test Chat Alpha" then press Enter
- **Expected**: A new conversation is created with the name "Test Chat Alpha". It appears in the sidebar conversation list. The chat area loads the new conversation. The form closes.
- **Pass**: Conversation created with correct name, visible in sidebar, form closed
- **Fail**: Enter does not submit, conversation not created, name incorrect, form stays open
- **If Failed**: Check `onKeyDown` handler on name input for Enter key. Check the create conversation API mutation. Check network tab for POST request to conversation creation endpoint.

### Test 2.4: Name Input Escape to Cancel
- **Setup**: Open the New Chat form, type something in the Name field
- **Action**: Press Escape
- **Expected**: Form closes. Fields reset (name cleared).
- **Pass**: Form closes and fields are empty on next open
- **Fail**: Form stays open, or fields retain values
- **If Failed**: Check `onKeyDown` handler for Escape key. Check form reset logic.

### Test 2.5: Folder/Category Dropdown
- **Setup**: New Chat form open
- **Action**: Click the "Folder" dropdown
- **Expected**: Dropdown opens showing "No folder" (default) plus any user-created categories
- **Pass**: Dropdown displays options, "No folder" is the default
- **Fail**: Dropdown empty, doesn't open, or missing categories
- **If Failed**: Check the categories API query. Verify `CategoryManager` has been used to create categories if expecting them.

### Test 2.6: Folder Selection Persists
- **Setup**: New Chat form open, at least one category exists (create via "Manage Categories" if needed)
- **Action**: Select a category from the Folder dropdown, then click "Start Chat"
- **Expected**: New conversation is created and assigned to the selected category/folder. It appears under that category group in the sidebar.
- **Pass**: Conversation appears under the correct category group in sidebar
- **Fail**: Conversation appears under wrong group or no group
- **If Failed**: Check that the category ID is passed in the create conversation API payload.

### Test 2.7: Attach Repository Toggle -- Off State
- **Setup**: New Chat form open
- **Action**: Observe the "Attach Repository" toggle (should be OFF by default)
- **Expected**: Toggle switch is in OFF position. No RepoSelector dropdown visible below it.
- **Pass**: Toggle off, no repo selector visible
- **Fail**: Toggle on by default, or repo selector visible when toggle is off
- **If Failed**: Check default state of the attach repo toggle in `WorkspaceSidebar.tsx`.

### Test 2.8: Attach Repository Toggle -- On State
- **Setup**: New Chat form open
- **Action**: Click the "Attach Repository" toggle switch
- **Expected**: Toggle animates to ON position. A RepoSelector dropdown appears below it.
- **Pass**: Toggle animates to ON, RepoSelector visible
- **Fail**: Toggle doesn't animate, RepoSelector doesn't appear
- **If Failed**: Check toggle state binding. Check conditional render of `RepoSelector` component.

### Test 2.9: RepoSelector Dropdown
- **Setup**: Attach Repository toggle is ON (Test 2.8)
- **Action**: Click the RepoSelector trigger button
- **Expected**: Dropdown panel opens (~280px wide) with a search input and a list of GitHub repositories. Each repo shows name, lock icon (private/public), and relative update time.
- **Pass**: Dropdown opens with repo list populated
- **Fail**: Dropdown doesn't open, shows "Loading repositories..." indefinitely, or shows error (e.g., "gh CLI not installed")
- **If Failed**: Check backend endpoint that calls `gh repo list`. Verify `gh` CLI is installed and authenticated. Check network tab for the API request and response.

### Test 2.10: RepoSelector Search Filter
- **Setup**: RepoSelector dropdown open with repos listed (Test 2.9)
- **Action**: Type a partial repo name in the search input
- **Expected**: Repo list filters to show only repos matching the search query
- **Pass**: List filters correctly as you type
- **Fail**: No filtering, or all repos disappear
- **If Failed**: Check the filter logic in `RepoSelector.tsx`.

### Test 2.11: Model Preset Pills -- Claude Provider
- **Setup**: New Chat form open (default provider is Claude)
- **Action**: Observe the Model section
- **Expected**: Three horizontal pills visible: "Opus 4.6 - 1M" (blue), "Sonnet 4.6 - 1M" (violet), "Opus 4.6 - 200K" (zinc). One is selected (highlighted).
- **Pass**: All three pills visible with correct labels and colors
- **Fail**: Pills missing, wrong labels, or no selection highlight
- **If Failed**: Check model preset configuration in `WorkspaceSidebar.tsx`. Verify pill rendering logic.

### Test 2.12: Model Preset Pills -- Selection
- **Setup**: New Chat form open, model pills visible
- **Action**: Click each pill one at a time: "Opus 4.6 - 1M", then "Sonnet 4.6 - 1M", then "Opus 4.6 - 200K"
- **Expected**: Each clicked pill highlights with its specific color (blue, violet, zinc respectively). Previously selected pill deselects.
- **Pass**: Single-selection behavior, correct color per pill
- **Fail**: Multiple pills selected, no highlight change, or wrong colors
- **If Failed**: Check radio group logic in the pill selector.

### Test 2.13: Thinking Effort Selector -- Disabled State
- **Setup**: New Chat form open
- **Action**: Select "Sonnet 4.6 - 1M" model preset, then observe the Thinking Effort selector
- **Expected**: Thinking Effort selector is grayed out (opacity ~35%, not clickable) because Sonnet is selected, not Opus 1M
- **Pass**: Selector visually grayed out, clicks have no effect
- **Fail**: Selector is interactive despite Sonnet being selected
- **If Failed**: Check the conditional disable logic for the effort selector. It should only be active when model is Opus AND context is 1M.

### Test 2.14: Thinking Effort Selector -- Enabled State
- **Setup**: New Chat form open
- **Action**: Select "Opus 4.6 - 1M" model preset, then observe the Thinking Effort selector
- **Expected**: Thinking Effort selector becomes interactive (full opacity). Shows three pills: "Low" (emerald), "Medium" (blue), "High" (orange).
- **Pass**: Selector is interactive, all three pills visible and clickable
- **Fail**: Selector remains grayed out on Opus 1M
- **If Failed**: Check the model/context condition that enables the effort selector.

### Test 2.15: Thinking Effort Selector -- Pill Selection
- **Setup**: Effort selector is enabled (Test 2.14)
- **Action**: Click each effort pill: Low, Medium, High
- **Expected**: Each pill highlights with its color (emerald, blue, orange). A use-case description appears below the selected pill. Tooltips show on hover:
  - Low: Quick lookups, classification, routing, sub-agents
  - Medium: Agentic coding, tool use, code generation
  - High: Complex analysis, nuanced reasoning, quality-critical
- **Pass**: Pills toggle correctly, descriptions/tooltips appear
- **Fail**: No visual change, descriptions missing
- **If Failed**: Check tooltip and description rendering in the effort selector component.

### Test 2.16: Start Chat Button
- **Setup**: New Chat form open, name filled in as "QA Test Session"
- **Action**: Click "Start Chat"
- **Expected**: Button text changes to "Creating..." during the API call. On success: conversation appears in sidebar, chat area loads it, form closes.
- **Pass**: Button shows loading state, conversation created, form closes
- **Fail**: Button stays disabled, no loading indicator, conversation not created, console errors
- **If Failed**: Check the create mutation in the API hooks. Check network tab for POST request. Look for validation errors in the response.

### Test 2.17: Cancel (X) Button
- **Setup**: New Chat form open, some fields filled in
- **Action**: Click the X button in the top-right corner of the form
- **Expected**: Form closes. All fields reset to defaults.
- **Pass**: Form closes, fields empty on next open
- **Fail**: Form stays open, or fields retain previous values
- **If Failed**: Check the close handler and field reset logic.

### Test 2.18: Thinking Effort Grays Out on Model Switch
- **Setup**: New Chat form open, "Opus 4.6 - 1M" selected, effort set to "High"
- **Action**: Switch model to "Opus 4.6 - 200K"
- **Expected**: Thinking Effort selector grays out (becomes non-interactive)
- **Pass**: Selector disabled after switching away from Opus 1M
- **Fail**: Selector remains active on 200K model
- **If Failed**: Check that model change resets or disables the effort selector.

---

## Test Group 3: Chat Session

### Test 3.1: Send a Message
- **Setup**: A conversation is active (created in Test Group 2). Model is "Opus 4.6 - 200K" or whichever Claude subscription model is available.
- **Action**: Click the text input at the bottom of the chat area. Type "Hello, please respond with a short greeting." Press Enter.
- **Expected**: Message appears as a user message bubble in the chat area. A "Thinking..." indicator with spinning loader appears. The send button shows a spinner during processing.
- **Pass**: User message displayed, loading indicator visible
- **Fail**: Message not displayed, no loading indicator, or input doesn't clear
- **If Failed**: Check WebSocket connection status (header indicator should be green). Check `WorkspaceChat.tsx` send handler. Check network/console for errors.

### Test 3.2: Response Streams Back
- **Setup**: Message sent (Test 3.1)
- **Action**: Wait for the assistant response to appear
- **Expected**: Assistant message streams in progressively (text appears word-by-word or chunk-by-chunk). The streaming indicator is visible during streaming. When complete, the full response is displayed.
- **Pass**: Response streams visibly, then completes with full text displayed
- **Fail**: No response, response appears all at once (no streaming), or response is cut off
- **If Failed**: Check WebSocket messages in DevTools Network tab (WS frames). Verify the backend chat session handler. Check for rate limit or auth errors in console.

### Test 3.3: Activity Indicator on Sidebar Row During Streaming
- **Setup**: Message sent, response streaming (Test 3.2)
- **Action**: Observe the conversation row in the sidebar during streaming
- **Expected**: Cyan pulsing glow bar on the left edge of the row. Cyan pulsing dot. Shimmer sweep overlay on the row.
- **Pass**: Cyan activity indicators visible during streaming
- **Fail**: No activity indicators on the sidebar row
- **If Failed**: Check the streaming/running status props passed to conversation rows. Verify WebSocket events propagate to sidebar state.

### Test 3.4: Token Counter Updates
- **Setup**: A message has been sent and a response received
- **Action**: Look at the compact control bar below the header (Section 8.4 of manual)
- **Expected**: Context usage bar shows a non-zero percentage. Usage text shows token count (e.g., "2% - 4.2K/200K"). Message count shows "2 msgs" (or appropriate count).
- **Pass**: Token percentage > 0, token count displayed, message count correct
- **Fail**: Token count stuck at 0%, or message count wrong
- **If Failed**: Check token tracking in `WorkspaceChat.tsx`. Verify the WebSocket sends token usage events. Check `EnhancedContextBudgetBar.tsx`.

### Test 3.5: Active Model Badge
- **Setup**: Conversation active with at least one exchange
- **Action**: Look at the right side of the chat header bar
- **Expected**: Colored pill badge showing the active model preset (e.g., "Opus 4.6 - 200K"), the confirmed model ID in monospace (e.g., "claude-opus-4-6"), and API cost if available.
- **Pass**: Badge visible with correct model name, model ID displayed
- **Fail**: Badge missing, wrong model shown, or model ID missing
- **If Failed**: Check `WorkspaceChat.tsx` model badge rendering. Verify the confirmed model comes from the API response metadata.

### Test 3.6: Message Formatting
- **Setup**: Active conversation
- **Action**: Send: "Please respond with a markdown list of 3 items, a code block in Python, and a bold sentence."
- **Expected**: Assistant response renders with: bullet list items, syntax-highlighted code block, and bold text -- all properly formatted in Markdown.
- **Pass**: Markdown renders correctly (lists, code blocks, bold text)
- **Fail**: Raw markdown visible (asterisks, backticks shown as text), or formatting broken
- **If Failed**: Check the markdown renderer used for assistant messages. Verify the markdown library is imported and configured.

### Test 3.7: Loading Indicator Disappears After Response
- **Setup**: Message sent, response completed
- **Action**: Verify the "Thinking..." indicator is gone
- **Expected**: No "Thinking..." indicator. No spinning loader on the send button. Input is re-enabled for the next message.
- **Pass**: Loading indicators gone, input enabled
- **Fail**: "Thinking..." persists, send button still spinning, or input remains disabled
- **If Failed**: Check the loading state management. Verify WebSocket stream-end event properly resets loading state.

### Test 3.8: Send Multiple Messages
- **Setup**: Active conversation with at least one exchange
- **Action**: Send three more messages: "What is 2+2?", wait for response. "Name a color.", wait for response. "Say goodbye.", wait for response.
- **Expected**: Each message and response appears in order. Message count updates after each exchange. Token usage bar grows. Scroll position follows new messages.
- **Pass**: All exchanges appear in order, counters update, auto-scroll works
- **Fail**: Messages out of order, counters stuck, or auto-scroll broken
- **If Failed**: Check message ordering logic. Check auto-scroll behavior in `WorkspaceChat.tsx` (should scroll to bottom on new content unless user has scrolled up).

---

## Test Group 4: Conversation List

### Test 4.1: Conversations Appear in Sidebar
- **Setup**: At least two conversations exist (create a second one via "New Chat" if needed, name it "QA Test Session 2")
- **Action**: Look at the sidebar conversation list
- **Expected**: Both conversations appear as clickable rows in the sidebar. Each shows the conversation title.
- **Pass**: All created conversations visible in sidebar
- **Fail**: Conversations missing, duplicated, or showing wrong titles
- **If Failed**: Check the conversations API query. Verify `useQuery` refetch behavior after creation.

### Test 4.2: Click Conversation Row to Switch
- **Setup**: Two or more conversations exist, one is currently active
- **Action**: Click the other conversation row in the sidebar
- **Expected**: Chat area loads the clicked conversation's messages. The clicked row highlights with accent background. The previously active row loses highlight.
- **Pass**: Chat switches to clicked conversation, highlight updates
- **Fail**: Chat doesn't switch, wrong conversation loads, or both rows highlighted
- **If Failed**: Check the conversation selection handler. Verify the conversation ID is passed correctly to the chat component.

### Test 4.3: Search -- Client-Side Filter (Short Query)
- **Setup**: Multiple conversations exist with distinct names
- **Action**: Click the search input below "New Chat". Type 1-2 characters that match one conversation name (e.g., "Al" for "Test Chat Alpha")
- **Expected**: Sidebar list filters to show only conversations whose titles contain the typed characters. No server request fired (client-side only).
- **Pass**: List filters correctly, matching conversations shown, non-matching hidden
- **Fail**: No filtering occurs, or all conversations disappear
- **If Failed**: Check `ConversationSearch.tsx` filter logic for short queries.

### Test 4.4: Search -- Server-Side Search (Long Query)
- **Setup**: Conversations exist with messages
- **Action**: Type 3+ characters in the search input (e.g., "greeting" if a message contains that word)
- **Expected**: After a brief debounce (~300ms), an overlay dropdown appears below the search input with search results. Results show conversation titles and matching text excerpts with highlighted matches.
- **Pass**: Overlay dropdown appears with search results and highlighted excerpts
- **Fail**: No overlay, no results despite matching content, or no excerpt highlighting
- **If Failed**: Check the server-side search API endpoint. Verify debounce timing. Check `ConversationSearch.tsx` overlay rendering.

### Test 4.5: Search -- Click Result in Overlay
- **Setup**: Server-side search results visible in overlay (Test 4.4)
- **Action**: Click one of the search results
- **Expected**: The clicked conversation is selected and loaded in the chat area. The search overlay closes. The search input may clear.
- **Pass**: Conversation loads, overlay closes
- **Fail**: Overlay stays open, wrong conversation loads, or nothing happens
- **If Failed**: Check the click handler on search result items.

### Test 4.6: Search -- Clear Button
- **Setup**: Text typed in search input
- **Action**: Click the X button on the right side of the search input
- **Expected**: Search text clears. Sidebar list returns to showing all conversations. Overlay dropdown (if open) closes.
- **Pass**: Input cleared, full list restored, overlay closed
- **Fail**: Text remains, list still filtered, or overlay persists
- **If Failed**: Check the clear handler. Verify it resets both the query state and filter state.

### Test 4.7: Search -- Escape to Clear
- **Setup**: Text typed in search input, overlay may be open
- **Action**: Press Escape
- **Expected**: Search text clears. Overlay closes. Full conversation list returns.
- **Pass**: Same result as Test 4.6
- **Fail**: Escape does nothing
- **If Failed**: Check `onKeyDown` handler for Escape key on the search input.

### Test 4.8: Category Group Collapse/Expand
- **Setup**: At least one conversation assigned to a category (or "Pinned" group exists)
- **Action**: Click the category group header (the row with the category name and count badge)
- **Expected**: First click: Group collapses, conversation rows within that group are hidden, but the header remains visible with count badge. Second click: Group expands, rows reappear.
- **Pass**: Toggle collapse/expand works, count badge always visible
- **Fail**: Group doesn't collapse, wrong conversations hidden, or header disappears
- **If Failed**: Check group header click handler in `WorkspaceSidebar.tsx`. Verify collapsed group state tracking.

### Test 4.9: Pinned Group Appears at Top
- **Setup**: At least one conversation is pinned (pin one in Test Group 5 if needed)
- **Action**: Observe the sidebar conversation list
- **Expected**: A "Pinned" group appears at the very top of the conversation list, with a star icon and a count of pinned conversations.
- **Pass**: Pinned group at top with star icon and correct count
- **Fail**: Pinned group missing, or not at top, or count wrong
- **If Failed**: Check pinned group sorting logic. Verify pinned conversations are filtered into the pinned group.

---

## Test Group 5: Conversation Row Actions

### Test 5.1: Hover to Reveal Action Buttons
- **Setup**: Conversations exist in sidebar, not in select mode
- **Action**: Hover the mouse over a conversation row
- **Expected**: Three icon buttons appear on the right side of the row: FolderPlus, Pin, Delete (Trash2)
- **Pass**: All three buttons appear on hover
- **Fail**: Buttons don't appear, wrong buttons, or buttons appear without hovering
- **If Failed**: Check hover CSS/state in conversation row component. Verify `selectMode` is false.

### Test 5.2: Hover Buttons Hidden in Select Mode
- **Setup**: Enter select mode (click CheckSquare button in sidebar header)
- **Action**: Hover over a conversation row
- **Expected**: Hover action buttons (FolderPlus, Pin, Delete) do NOT appear. Instead, a checkbox is visible on the row.
- **Pass**: No hover buttons in select mode, checkbox visible
- **Fail**: Hover buttons still appear in select mode
- **If Failed**: Check the conditional rendering that hides hover actions when `selectMode` is true.

### Test 5.3: FolderPlus Popover -- Open
- **Setup**: Not in select mode, conversations exist
- **Action**: Hover a conversation row, click the FolderPlus button
- **Expected**: An inline popover opens below/near the row with: "Move to Folder" dropdown, "Attach Repository" RepoSelector, and a "Done" button.
- **Pass**: Popover opens with all three elements
- **Fail**: Popover doesn't open, elements missing
- **If Failed**: Check popover state in the conversation row component. Verify `FolderPlus` click handler.

### Test 5.4: FolderPlus Popover -- Move to Folder
- **Setup**: FolderPlus popover open (Test 5.3), at least one category exists
- **Action**: Change the "Move to Folder" dropdown to a different category
- **Expected**: Conversation immediately moves to the selected category group in the sidebar (the conversation row relocates to the new group).
- **Pass**: Conversation moves to new group immediately
- **Fail**: Conversation stays in old group, or move happens only after clicking Done
- **If Failed**: Check the mutation that updates conversation category. Verify optimistic update or refetch after mutation.

### Test 5.5: FolderPlus Popover -- Attach Repository
- **Setup**: FolderPlus popover open (Test 5.3)
- **Action**: Use the RepoSelector in the popover to select a repository
- **Expected**: Repository is attached to the conversation. (This sets the working directory for that conversation.)
- **Pass**: Repo selection saves without error
- **Fail**: RepoSelector doesn't appear, or selection fails
- **If Failed**: Check the RepoSelector integration within the popover.

### Test 5.6: FolderPlus Popover -- Done Button
- **Setup**: FolderPlus popover open
- **Action**: Click "Done"
- **Expected**: Popover closes
- **Pass**: Popover closes
- **Fail**: Popover stays open
- **If Failed**: Check the Done button click handler.

### Test 5.7: FolderPlus Popover -- Click Outside to Close
- **Setup**: FolderPlus popover open
- **Action**: Click anywhere outside the popover
- **Expected**: Popover closes
- **Pass**: Popover closes
- **Fail**: Popover stays open
- **If Failed**: Check the outside-click detection logic on the popover.

### Test 5.8: Pin Button -- Pin a Conversation
- **Setup**: Not in select mode, unpinned conversation exists
- **Action**: Hover a conversation row, click the Pin button
- **Expected**: Conversation moves to the "Pinned" group at the top of the sidebar. A star icon appears on the pinned group or row.
- **Pass**: Conversation in Pinned group at top
- **Fail**: Conversation doesn't move, or Pinned group doesn't appear
- **If Failed**: Check the pin mutation. Verify the sidebar re-sorts conversations when pin state changes.

### Test 5.9: Pin Button -- Unpin a Conversation
- **Setup**: A pinned conversation exists (from Test 5.8)
- **Action**: Hover the pinned conversation row, click the Pin button again
- **Expected**: Conversation moves out of the Pinned group back to its category group (or the default/uncategorized group).
- **Pass**: Conversation removed from Pinned group
- **Fail**: Conversation stays pinned, or disappears entirely
- **If Failed**: Check the unpin mutation. Verify pin state toggle logic.

### Test 5.10: Delete Button -- Delete a Conversation
- **Setup**: At least two conversations exist. One is NOT the currently active conversation.
- **Action**: Hover the non-active conversation row, click the Delete (Trash2) button
- **Expected**: Conversation disappears from the sidebar immediately. No confirmation dialog. The active conversation remains unaffected.
- **Pass**: Conversation removed from list, active chat unaffected
- **Fail**: Conversation remains, confirmation dialog appears (unexpected), or wrong conversation deleted
- **If Failed**: Check the delete mutation. Verify it targets the correct conversation ID.

### Test 5.11: Delete Button -- Delete Active Conversation
- **Setup**: A conversation is active (loaded in chat area)
- **Action**: Hover the active conversation row, click the Delete (Trash2) button
- **Expected**: Conversation disappears from sidebar. Chat area clears to empty state (no conversation selected).
- **Pass**: Conversation removed, chat area shows empty state
- **Fail**: Chat area still shows deleted conversation's messages, or crashes
- **If Failed**: Check that deleting the active conversation also clears the selection state.

---

## Test Group 6: Model Badge Cycling

### Test 6.1: Claude Conversation Badge -- Initial Display
- **Setup**: A Claude conversation exists in the sidebar
- **Action**: Look at the top-right corner of the conversation row
- **Expected**: A small colored badge showing model abbreviation and context (e.g., "O-1M" for Opus 1M, or "S-1M" for Sonnet 1M, or "O-200K"). Color: blue for Opus+1M, violet for Sonnet+1M, zinc for Opus+200K.
- **Pass**: Badge visible with correct abbreviation and color
- **Fail**: Badge missing, or wrong abbreviation/color
- **If Failed**: Check the model badge rendering in conversation row component. Verify model/context data from the API.

### Test 6.2: Claude Badge -- Cycle Through Models
- **Setup**: A Claude conversation exists with badge visible
- **Action**: Click the model badge on the conversation row
- **Expected**: Badge cycles: Opus 1M (blue "O-1M") -> Sonnet 1M (violet "S-1M") -> Opus 200K (zinc "O-200K") -> Opus 1M (blue "O-1M"). Each click advances one step.
- **Pass**: Badge text and color change correctly with each click. Three clicks return to original.
- **Fail**: Badge doesn't change on click, skips a combination, or cycles wrong order
- **If Failed**: Check the badge click handler and the model cycling array.

### Test 6.3: Badge Click Does Not Select Conversation
- **Setup**: One conversation is active, another exists with a badge
- **Action**: Click the badge on the NON-active conversation
- **Expected**: Badge cycles (model changes), but the active conversation does NOT change. The chat area stays on the previously active conversation.
- **Pass**: Badge cycles, active conversation unchanged
- **Fail**: Clicking badge also selects the conversation
- **If Failed**: Check that the badge click handler uses `e.stopPropagation()` to prevent row selection.

### Test 6.4: Non-Claude Badge -- Static Display
- **Setup**: A Codex or Gemini conversation exists (if available)
- **Action**: Look at the badge on a non-Claude conversation row
- **Expected**: Badge shows the model ID as static text (not clickable). Color: emerald for Codex, violet for Gemini.
- **Pass**: Badge is static, not clickable, correct color
- **Fail**: Badge is clickable (it shouldn't be), or wrong color
- **If Failed**: Check conditional rendering for non-Claude provider badges.

---

## Test Group 7: Chat Header

### Test 7.1: Editable Title -- Display
- **Setup**: A conversation is active
- **Action**: Look at the left side of the chat header
- **Expected**: Conversation title displayed (or "Untitled Conversation" in italic if no title set). A tiny Pencil icon appears on hover.
- **Pass**: Title visible, pencil icon on hover
- **Fail**: Title missing, or pencil icon doesn't appear on hover
- **If Failed**: Check `WorkspaceChatHeader.tsx` title rendering and hover state.

### Test 7.2: Editable Title -- Enter Edit Mode
- **Setup**: Active conversation with title visible
- **Action**: Click the title text
- **Expected**: Title text is replaced by a text input containing the current title. Input is focused.
- **Pass**: Input appears with current title, focused
- **Fail**: Nothing happens on click, or input doesn't show current title
- **If Failed**: Check the click handler that toggles edit mode in `WorkspaceChatHeader.tsx`.

### Test 7.3: Editable Title -- Save with Enter
- **Setup**: Title in edit mode (Test 7.2)
- **Action**: Clear the input, type "Renamed Chat Title", press Enter
- **Expected**: Input disappears. Title updates to "Renamed Chat Title" in the header. Sidebar also shows the updated title on the conversation row.
- **Pass**: Title updated in both header and sidebar
- **Fail**: Title reverts, sidebar not updated, or edit mode persists
- **If Failed**: Check the title update mutation. Verify it triggers a refetch or optimistic update for both header and sidebar.

### Test 7.4: Editable Title -- Save on Blur
- **Setup**: Title in edit mode, new title typed
- **Action**: Click somewhere outside the title input (blur it)
- **Expected**: Title saves with the new text, same as pressing Enter
- **Pass**: Title updated on blur
- **Fail**: Title reverts on blur, or edit mode persists
- **If Failed**: Check the `onBlur` handler on the title input.

### Test 7.5: Editable Title -- Cancel with Escape
- **Setup**: Title in edit mode, new title typed
- **Action**: Press Escape
- **Expected**: Input disappears. Title reverts to the original value (before editing).
- **Pass**: Original title restored, edit mode closed
- **Fail**: New title saved despite Escape, or edit mode persists
- **If Failed**: Check the `onKeyDown` handler for Escape key in the title input.

### Test 7.6: Category Dropdown in Header
- **Setup**: Active conversation, categories exist
- **Action**: Click the category dropdown (native select) in the header
- **Expected**: Dropdown shows default categories (general, debugging, refactoring, feature, exploration) plus any custom categories.
- **Pass**: All categories listed
- **Fail**: Dropdown empty or missing categories
- **If Failed**: Check the categories query used by the header component.

### Test 7.7: Category Change via Header Dropdown
- **Setup**: Category dropdown open (Test 7.6)
- **Action**: Select a different category
- **Expected**: Category updates immediately. Conversation moves to the new category group in the sidebar.
- **Pass**: Category changed, sidebar group updated
- **Fail**: Category doesn't change, or sidebar doesn't reflect change
- **If Failed**: Check the category update mutation.

### Test 7.8: Add a Tag
- **Setup**: Active conversation
- **Action**: Click the "+" button (Tag + Plus icons) next to the tags section in the header
- **Expected**: A tiny inline text input appears
- **Pass**: Tag input visible
- **Fail**: Input doesn't appear
- **If Failed**: Check the add-tag button handler in `WorkspaceChatHeader.tsx`.

### Test 7.9: Type and Submit a Tag
- **Setup**: Tag input visible (Test 7.8)
- **Action**: Type "important" and press Enter
- **Expected**: Tag "important" appears as a colored pill chip in the header. The input closes.
- **Pass**: Tag chip visible with text "important"
- **Fail**: Tag not added, or input stays open
- **If Failed**: Check tag submission handler. Verify the tags mutation.

### Test 7.10: Remove a Tag
- **Setup**: At least one tag exists on the active conversation (Test 7.9)
- **Action**: Click the X button on the tag chip
- **Expected**: Tag chip disappears
- **Pass**: Tag removed from header
- **Fail**: Tag persists, or wrong tag removed
- **If Failed**: Check the tag removal handler.

### Test 7.11: Duplicate Tag Prevention
- **Setup**: Tag "important" exists on the conversation
- **Action**: Add tag "+" button, type "important" (same tag, same case), press Enter
- **Expected**: Duplicate tag is prevented (not added). Existing "important" tag remains as the only instance.
- **Pass**: No duplicate tag appears
- **Fail**: Two "important" tags appear
- **If Failed**: Check case-insensitive duplicate detection in the tag handler.

### Test 7.12: Git Branch Display
- **Setup**: Active conversation with a repository attached (working directory set to a git repo)
- **Action**: Observe the header
- **Expected**: GitBranch icon + current branch name displayed in monospace font
- **Pass**: Branch name visible and matches the actual git branch
- **Fail**: No branch displayed despite repo being attached
- **If Failed**: Check the git branch detection logic. Verify the backend provides branch info.

### Test 7.13: Git Branch Rename (Non-Protected Branch)
- **Setup**: Active conversation with a repo on a non-main/non-master branch
- **Action**: Click the Pencil icon next to the branch name
- **Expected**: Input field appears with current branch name. Type a new name, press Enter. Loading spinner appears briefly. Branch name updates.
- **Pass**: Branch renamed successfully
- **Fail**: Pencil icon not visible, rename fails, or spinner persists
- **If Failed**: Check the branch rename API call. Verify the Pencil icon is conditionally shown only for non-protected branches.

### Test 7.14: Connection Status Indicator
- **Setup**: Active conversation
- **Action**: Observe the far right of the chat header
- **Expected**: Green pulsing dot + Wifi icon (indicating WebSocket connected)
- **Pass**: Green indicator with Wifi icon
- **Fail**: Red/yellow indicator, or indicator missing
- **If Failed**: Check WebSocket connection state in `WorkspaceChat.tsx`. Verify the backend WebSocket endpoint.

---

## Test Group 8: Chat Input

### Test 8.1: Image Paste (Ctrl+V)
- **Setup**: Active conversation, copy an image to clipboard (e.g., take a screenshot with PrtScn or copy an image from a web page)
- **Action**: Click the chat input textarea to focus it. Press Ctrl+V.
- **Expected**: A thumbnail preview (~64x64) appears above the input area showing the pasted image. An X button appears on hover of the thumbnail.
- **Pass**: Thumbnail preview visible
- **Fail**: Nothing happens on paste, or image not detected
- **If Failed**: Check the `onPaste` handler in the chat input. Verify it detects image clipboard items.

### Test 8.2: Image Paste -- Remove
- **Setup**: Image pasted (Test 8.1), thumbnail visible
- **Action**: Hover the thumbnail and click the X button
- **Expected**: Thumbnail disappears. Image attachment is removed.
- **Pass**: Thumbnail removed
- **Fail**: Thumbnail persists, or X button not visible
- **If Failed**: Check the remove handler on the pending images preview.

### Test 8.3: File Attach Button (Paperclip)
- **Setup**: Active conversation
- **Action**: Click the Paperclip icon button on the left side of the input row
- **Expected**: Native file picker dialog opens (any file type, multiple selection allowed)
- **Pass**: File picker opens
- **Fail**: Nothing happens on click
- **If Failed**: Check the hidden file input and its click trigger.

### Test 8.4: File Attach -- Select File
- **Setup**: File picker open (Test 8.3)
- **Action**: Select a text file (e.g., a .txt or .json file), click Open
- **Expected**: File chip appears above the input area showing: Paperclip icon + file name in a gray chip. X button to remove.
- **Pass**: File chip visible with correct file name
- **Fail**: No chip appears, or file name wrong
- **If Failed**: Check the file input `onChange` handler.

### Test 8.5: Image Attach Button (ImagePlus)
- **Setup**: Active conversation
- **Action**: Click the ImagePlus icon button (next to Paperclip)
- **Expected**: Native file picker opens, filtered to image types (JPEG, PNG, GIF, WebP). Multiple selection allowed.
- **Pass**: File picker opens with image filter
- **Fail**: File picker doesn't open, or shows all file types
- **If Failed**: Check the `accept` attribute on the hidden image file input.

### Test 8.6: Image Attach -- Select Image
- **Setup**: Image file picker open (Test 8.5)
- **Action**: Select an image file, click Open
- **Expected**: Thumbnail preview appears above the input area (same as clipboard paste)
- **Pass**: Image thumbnail visible
- **Fail**: No thumbnail, or image not processed
- **If Failed**: Check the image file processing in the `onChange` handler.

### Test 8.7: Library Attach Button (BookOpen)
- **Setup**: Active conversation
- **Action**: Click the BookOpen icon button (next to ImagePlus)
- **Expected**: Library Picker Modal opens (see Test Group 9 for modal details)
- **Pass**: Modal opens
- **Fail**: Nothing happens
- **If Failed**: Check the BookOpen button click handler.

### Test 8.8: Library Attach -- Badge Count
- **Setup**: Library files attached (after selecting files in the Library Picker Modal)
- **Action**: Observe the BookOpen button
- **Expected**: BookOpen icon turns primary color. A badge count appears showing the number of attached library files.
- **Pass**: Icon colored, badge count matches number of attached files
- **Fail**: No color change, no badge
- **If Failed**: Check the conditional styling and badge rendering on the BookOpen button.

### Test 8.9: Text Input -- Enter to Send
- **Setup**: Active conversation, text typed in the input
- **Action**: Press Enter
- **Expected**: Message sends. Input clears. User message appears in chat.
- **Pass**: Message sent on Enter
- **Fail**: Enter adds a newline instead of sending
- **If Failed**: Check the `onKeyDown` handler distinguishing Enter from Shift+Enter.

### Test 8.10: Text Input -- Shift+Enter for Newline
- **Setup**: Active conversation, text typed in the input
- **Action**: Press Shift+Enter
- **Expected**: A newline is inserted in the input. Message is NOT sent.
- **Pass**: Newline added, message not sent
- **Fail**: Message sends on Shift+Enter, or no newline added
- **If Failed**: Check the `onKeyDown` handler for Shift modifier detection.

### Test 8.11: Text Input -- Auto-Expand
- **Setup**: Active conversation, input focused
- **Action**: Type multiple lines (use Shift+Enter to add lines) until content exceeds the default height
- **Expected**: Textarea height grows automatically to accommodate content (min 44px, max 240px)
- **Pass**: Textarea height increases with content
- **Fail**: Textarea stays at fixed height, content scrolls within it, or exceeds max
- **If Failed**: Check the auto-resize logic (typically a `useEffect` that adjusts `scrollHeight`).

### Test 8.12: Text Input -- Disabled During Loading
- **Setup**: Active conversation
- **Action**: Send a message and immediately try to type in the input while response is streaming
- **Expected**: Input is disabled (not editable) while the assistant is processing/streaming
- **Pass**: Input not editable during loading
- **Fail**: Input remains editable during loading
- **If Failed**: Check the `disabled` prop on the textarea tied to loading state.

### Test 8.13: Send Button -- Disabled When Empty
- **Setup**: Active conversation, input empty, no attachments
- **Action**: Observe the send button
- **Expected**: Send button is visually disabled (grayed out or not clickable)
- **Pass**: Button disabled when input empty and no attachments
- **Fail**: Button enabled with empty input
- **If Failed**: Check the disabled condition on the send button.

### Test 8.14: Send Button -- Enabled with Attachment Only
- **Setup**: Active conversation, input empty but an image or file is attached
- **Action**: Observe the send button
- **Expected**: Send button is enabled (attachments count as content)
- **Pass**: Button enabled with attachment even if text is empty
- **Fail**: Button disabled despite attachment
- **If Failed**: Check that the disabled condition considers attachments.

### Test 8.15: Drag and Drop
- **Setup**: Active conversation
- **Action**: Drag a file from the desktop/file explorer over the chat input area
- **Expected**: A dashed border overlay appears with "Drop files or images here" text. Dropping the file adds it as an attachment.
- **Pass**: Overlay visible on drag-over, file attached on drop
- **Fail**: No overlay, or file not attached on drop
- **If Failed**: Check drag/drop event handlers (`onDragOver`, `onDrop`) on the input area.

### Test 8.16: Draft Persistence
- **Setup**: Active conversation
- **Action**: Type "This is a draft message" in the input but do NOT send it. Switch to another conversation. Switch back to the original conversation.
- **Expected**: The draft text "This is a draft message" is still in the input (persisted to localStorage)
- **Pass**: Draft text restored on return
- **Fail**: Input is empty after switching back
- **If Failed**: Check localStorage draft save/restore keyed by conversation ID.

---

## Test Group 9: Right Panels

### Test 9.1: Library Tab -- Upload File
- **Setup**: Library panel visible, "Library" tab selected
- **Action**: Click the "Upload" button (Upload icon) at the top of the Library tab
- **Expected**: FileUploadModal opens in file upload mode
- **Pass**: Upload modal opens
- **Fail**: Nothing happens
- **If Failed**: Check the Upload button click handler and `FileUploadModal` component.

### Test 9.2: Library Tab -- Paste Text
- **Setup**: Library panel visible, "Library" tab selected
- **Action**: Click the "Paste" button (ClipboardPaste icon)
- **Expected**: FileUploadModal opens in text paste mode (textarea for pasting text content)
- **Pass**: Paste modal opens with textarea
- **Fail**: Nothing happens or wrong mode
- **If Failed**: Check the Paste button handler and modal mode prop.

### Test 9.3: Library Tab -- Folder Browser
- **Setup**: Library tab active, some files uploaded
- **Action**: Navigate through folders in the library browser (click folders to open, click files to preview)
- **Expected**: Folder navigation works hierarchically. Files show type badge, name, and size. Clicking a file opens a preview.
- **Pass**: Navigation works, file details visible, preview opens
- **Fail**: Folders don't open, files missing, or preview crashes
- **If Failed**: Check `LibraryFolderBrowser` component. Verify the library API endpoints.

### Test 9.4: Repos Tab
- **Setup**: Library panel visible
- **Action**: Click the "Repos" tab (GitBranch icon)
- **Expected**: Tab switches to show the Repos panel. If no repos connected, shows "Connect Repository" button and "No repos connected" text.
- **Pass**: Repos tab displays correctly
- **Fail**: Tab doesn't switch, or content missing
- **If Failed**: Check tab switching logic in `WorkspaceLibrary.tsx`.

### Test 9.5: Repos Tab -- Connect Repository
- **Setup**: Repos tab active
- **Action**: Click "Connect Repository" button
- **Expected**: RepoConnector modal opens for connecting a GitHub repository
- **Pass**: Modal opens
- **Fail**: Nothing happens
- **If Failed**: Check the button handler and `RepoConnector` component.

### Test 9.6: Repos Tab -- Browse Connected Repo
- **Setup**: A repo is connected to the conversation
- **Action**: Expand the repo in the Repos tab, browse its file tree
- **Expected**: File tree is browsable. Clicking a file shows its content in a preview modal.
- **Pass**: File tree navigation works, file content viewable
- **Fail**: Tree doesn't expand, or file preview fails
- **If Failed**: Check `RepoBrowser` component and the file content API.

### Test 9.7: WT (Walkie-Talkie) Tab
- **Setup**: Library panel visible
- **Action**: Click the "WT" tab (Radio icon)
- **Expected**: Tab switches to the Walkie-Talkie log. Shows "No walkie-talkie messages yet" if empty, or a chronological message log if messages exist.
- **Pass**: WT tab displays correctly with appropriate empty/filled state
- **Fail**: Tab doesn't switch, or shows wrong content
- **If Failed**: Check WT tab rendering in `WorkspaceLibrary.tsx`.

### Test 9.8: WT Tab -- Message Display
- **Setup**: Walkie-talkie messages have been sent during an active agent session (Test 8.11 in manual)
- **Action**: View the WT tab
- **Expected**: Messages listed chronologically with: sender icon (User/Bot/Info), sender label ("You"/"Agent"/"System"), timestamp (HH:MM:SS), and content. User messages in amber, agent messages in primary color, system messages in gray.
- **Pass**: Messages displayed with correct sender, timestamp, and color coding
- **Fail**: Messages missing, wrong sender, or no color coding
- **If Failed**: Check WT message list rendering and data source.

### Test 9.9: Collapse Library Panel
- **Setup**: Library panel visible (~288px)
- **Action**: Click the ">>" collapse button
- **Expected**: Library panel collapses to a thin 40px strip with a FileText icon button
- **Pass**: Panel collapses to thin strip
- **Fail**: Panel doesn't collapse, or collapses to 0 (invisible)
- **If Failed**: Check collapse logic in `WorkspaceLibrary.tsx`.

### Test 9.10: Expand Library Panel
- **Setup**: Library panel collapsed (Test 9.9)
- **Action**: Click the FileText icon in the collapsed strip
- **Expected**: Library panel expands back to ~288px with tabs restored
- **Pass**: Panel expands fully with tabs
- **Fail**: Panel stays collapsed, or tabs missing after expand
- **If Failed**: Check the expand handler on the collapsed icon button.

### Test 9.11: Library Picker Modal
- **Setup**: Click BookOpen button in chat input (Test 8.7)
- **Action**: In the modal: navigate folders via breadcrumbs, check file checkboxes, click "Attach N files"
- **Expected**: Modal shows: title bar with count badge, breadcrumb navigation (Home icon + folder path), folders (clickable) and files (with checkboxes). Files show type badge (color-coded), name, size. Footer: Cancel + "Attach N files" button.
- **Pass**: Full navigation and selection works, files attach
- **Fail**: Folders don't open, checkboxes broken, or attach button fails
- **If Failed**: Check `LibraryPickerModal.tsx` component.

### Test 9.12: Save to Library Modal
- **Setup**: Active conversation with at least one assistant message
- **Action**: Find a "Save to Library" button on an assistant message. Click it.
- **Expected**: SaveToLibraryModal opens with fields: Filename (auto-generated), Display Name (optional), Folder (dropdown with nested tree), Tags (optional). Save and Cancel buttons.
- **Pass**: Modal opens with auto-populated filename
- **Fail**: Button not visible, modal doesn't open, or fields empty
- **If Failed**: Check the "Save to Library" button rendering on assistant messages. Check `SaveToLibraryModal.tsx`.

### Test 9.13: Save to Library -- Complete Save
- **Setup**: Save to Library modal open (Test 9.12)
- **Action**: Optionally edit the filename and display name. Select a folder. Click "Save".
- **Expected**: File is saved to the library. It appears in the Library tab's folder browser.
- **Pass**: File appears in library after save
- **Fail**: Save fails, or file doesn't appear in library
- **If Failed**: Check the save mutation and library API endpoint.

---

## Test Group 10: Split View

### Test 10.1: Enable Split View
- **Setup**: On Workspace page in normal (single-panel) mode
- **Action**: Click the "Split" button in the top nav bar
- **Expected**: Chat area splits into three vertical panels labeled "RESEARCH" (emerald), "PRD BUILDER" (violet), and "CODER" (cyan). Each has its own input area. Additional buttons appear in nav bar: R, P, C, All, and Auto.
- **Pass**: Three labeled panels visible, nav buttons appear
- **Fail**: Panels don't appear, layout broken, or nav buttons missing
- **If Failed**: Check split view state toggle in `WorkspacePage.tsx`. Verify the three-panel layout rendering.

### Test 10.2: Disable Split View
- **Setup**: Split view active (Test 10.1)
- **Action**: Click the "Split" button again
- **Expected**: Returns to single-panel normal mode. R, P, C, All, Auto buttons disappear from nav bar.
- **Pass**: Single panel restored, extra nav buttons gone
- **Fail**: Still showing three panels, or nav buttons persist
- **If Failed**: Check the split view toggle state.

### Test 10.3: Panel Labels and Colors
- **Setup**: Split view active
- **Action**: Observe each panel's label bar
- **Expected**:
  - Research panel: "RESEARCH (Opus/Sonnet - 200K)" in emerald with emerald accents
  - PRD Builder panel: "PRD BUILDER (Opus/Sonnet - 1M)" in violet with violet accents
  - Coder panel: "CODER (Opus/Sonnet - context)" in cyan with cyan accents
- **Pass**: Correct labels and colors on all three panels
- **Fail**: Wrong labels, missing labels, or wrong colors
- **If Failed**: Check the panel configuration in the split view rendering.

### Test 10.4: Opus/Sonnet Toggle Per Panel
- **Setup**: Split view active
- **Action**: Click the Opus/Sonnet toggle pill on one panel (e.g., Research panel)
- **Expected**: Toggle switches between Opus and Sonnet for that specific panel. Panel label updates to reflect the new model.
- **Pass**: Model toggles per-panel independently, label updates
- **Fail**: Toggle affects all panels, or label doesn't update
- **If Failed**: Check per-panel model state management.

### Test 10.5: Collapse Research Panel
- **Setup**: Split view active, all three panels expanded
- **Action**: Click the ChevronsLeft button in the top-right corner of the Research panel
- **Expected**: Research panel collapses to a thin vertical bar (~40px) with rotated "RESEARCH" text in emerald. PRD Builder and Coder panels expand to fill the space.
- **Pass**: Panel collapses to thin bar with label, other panels expand
- **Fail**: Panel disappears entirely, or other panels don't expand
- **If Failed**: Check collapse state and CSS flex/grid layout.

### Test 10.6: Expand Collapsed Panel
- **Setup**: Research panel collapsed (Test 10.5)
- **Action**: Click the collapsed "RESEARCH" bar
- **Expected**: Research panel expands back to its normal width
- **Pass**: Panel expands, all three panels visible
- **Fail**: Panel stays collapsed
- **If Failed**: Check the click handler on collapsed panel bars.

### Test 10.7: Panel Focus Buttons -- R
- **Setup**: Split view active, all panels expanded
- **Action**: Click the "R" button in the nav bar
- **Expected**: Only Research panel is expanded. PRD Builder and Coder panels collapse to thin bars.
- **Pass**: Only Research panel visible, others collapsed
- **Fail**: Wrong panel expanded, or none collapsed
- **If Failed**: Check the R button handler's panel state logic.

### Test 10.8: Panel Focus Buttons -- P
- **Setup**: Split view active
- **Action**: Click the "P" button in the nav bar
- **Expected**: Only PRD Builder panel is expanded. Research and Coder panels collapse.
- **Pass**: Only PRD Builder panel visible
- **Fail**: Wrong panel expanded
- **If Failed**: Check the P button handler.

### Test 10.9: Panel Focus Buttons -- C
- **Setup**: Split view active
- **Action**: Click the "C" button in the nav bar
- **Expected**: Only Coder panel is expanded. Research and PRD Builder panels collapse.
- **Pass**: Only Coder panel visible
- **Fail**: Wrong panel expanded
- **If Failed**: Check the C button handler.

### Test 10.10: Panel Focus Buttons -- All
- **Setup**: Split view active, some panels collapsed (from Tests 10.7-10.9)
- **Action**: Click the "All" button in the nav bar
- **Expected**: All three panels expand to visible
- **Pass**: All three panels visible
- **Fail**: Some panels remain collapsed
- **If Failed**: Check the All button handler.

### Test 10.11: Auto-Forward Toggle
- **Setup**: Split view active
- **Action**: Click the "Auto" button in the nav bar
- **Expected**: Auto button turns amber background. (When PRD Builder finishes a response, it auto-injects into the Coder panel.)
- **Pass**: Button turns amber on toggle
- **Fail**: Button doesn't change color, or auto-forward doesn't activate
- **If Failed**: Check the auto-forward state toggle.

### Test 10.12: PRD Builder Tabs (Chat / Passoff)
- **Setup**: Split view active
- **Action**: Look at the PRD Builder panel
- **Expected**: Two tabs visible: "Chat" (violet underline when active) and "Passoff" (amber underline when active, with section count badge).
- **Pass**: Both tabs visible, correct underline colors
- **Fail**: Tabs missing, or wrong colors
- **If Failed**: Check PRD Builder panel tab rendering.

### Test 10.13: Passoff Tab -- Add Section
- **Setup**: Click "Passoff" tab in PRD Builder panel
- **Action**: Click the "+" (Plus icon) button in the Passoff header
- **Expected**: A new empty section card appears at the bottom with: drag handle, title input, collapse toggle, delete button, and content textarea
- **Pass**: Section card appears with all elements
- **Fail**: No section added
- **If Failed**: Check `PassoffEditor.tsx` add section handler.

### Test 10.14: Passoff Tab -- Edit Section
- **Setup**: Passoff tab active, section exists (Test 10.13)
- **Action**: Type a title in the section's title input. Type content in the section's textarea.
- **Expected**: Title and content are editable and persist while the tab is open
- **Pass**: Content saves as typed
- **Fail**: Content disappears or inputs not editable
- **If Failed**: Check section state management in PassoffEditor.

### Test 10.15: Passoff Tab -- Send to Execute
- **Setup**: Passoff tab active, at least one section with content exists
- **Action**: Click the "Send to Execute" button (violet) at the bottom of the Passoff Editor
- **Expected**: Content is built into a markdown document and injected into the PRD Builder Chat panel as a user message. PRD panel expands if collapsed.
- **Pass**: Content appears in PRD Chat as a user message
- **Fail**: Button disabled, or content not injected
- **If Failed**: Check the "Send to Execute" handler. Verify the injection mechanism between Passoff and PRD Chat.

### Test 10.16: Each Panel Has Independent Input
- **Setup**: Split view active, all panels expanded
- **Action**: Type different text in each panel's input area (Research, PRD Chat, Coder)
- **Expected**: Each panel has its own independent input. Typing in one does not affect the others.
- **Pass**: Independent inputs, no cross-contamination
- **Fail**: Typing in one panel affects another
- **If Failed**: Check that each WorkspaceChat instance has its own state.

---

## Test Group 11: Category Management

### Test 11.1: Open Category Manager
- **Setup**: On Workspace page, sidebar visible
- **Action**: Click the "Manage Categories" button at the bottom of the sidebar (Settings icon)
- **Expected**: Category Manager modal opens as an overlay
- **Pass**: Modal opens
- **Fail**: Nothing happens
- **If Failed**: Check the button click handler and `CategoryManager.tsx` component.

### Test 11.2: Empty State
- **Setup**: Category Manager open, no custom categories exist
- **Action**: Observe the modal content
- **Expected**: Text reads "No categories yet. Create one below." with the add category form at the bottom.
- **Pass**: Empty state message visible, add form visible
- **Fail**: Blank modal, or form missing
- **If Failed**: Check empty state rendering in `CategoryManager.tsx`.

### Test 11.3: Create a Category
- **Setup**: Category Manager open
- **Action**: Type "Bug Reports" in the category name input. Select a red color swatch. Click "Add" (or press Enter).
- **Expected**: "Bug Reports" appears in the category list with a red color dot. The input clears.
- **Pass**: Category created with correct name and color
- **Fail**: Category not created, wrong color, or input not cleared
- **If Failed**: Check the add category mutation. Verify the color is sent in the API payload.

### Test 11.4: Create Multiple Categories
- **Setup**: Category Manager open, "Bug Reports" exists
- **Action**: Create two more categories: "Ideas" (blue) and "Archive" (gray)
- **Expected**: All three categories appear in the list in creation order
- **Pass**: All three visible with correct names and colors
- **Fail**: Categories missing or in wrong order
- **If Failed**: Check list rendering and order.

### Test 11.5: Edit Category Name
- **Setup**: Category Manager open, categories exist
- **Action**: Click the Pencil (edit) button on "Bug Reports"
- **Expected**: Row switches to edit mode with: editable name input (prefilled "Bug Reports"), color swatch palette, and checkmark save button.
- **Pass**: Edit mode active with current values
- **Fail**: Edit mode doesn't activate, or input empty
- **If Failed**: Check the edit button handler in `CategoryManager.tsx`.

### Test 11.6: Save Category Edit
- **Setup**: In edit mode (Test 11.5)
- **Action**: Change the name to "Bugs Fixed", select a green color swatch, click the checkmark (or press Enter)
- **Expected**: Category updates to "Bugs Fixed" with green color dot. Edit mode closes.
- **Pass**: Name and color updated, edit mode closed
- **Fail**: Changes not saved, or edit mode persists
- **If Failed**: Check the save/update mutation.

### Test 11.7: Reorder Categories -- Move Up
- **Setup**: Category Manager open, multiple categories exist
- **Action**: Click the up arrow on the second category
- **Expected**: Category moves up one position (swaps with the one above it). Up arrow disabled on the first item.
- **Pass**: Category moves up, first item's up arrow disabled
- **Fail**: No movement, or wrong category moves
- **If Failed**: Check the move-up handler and the reorder API.

### Test 11.8: Reorder Categories -- Move Down
- **Setup**: Category Manager open, multiple categories exist
- **Action**: Click the down arrow on the first category
- **Expected**: Category moves down one position. Down arrow disabled on the last item.
- **Pass**: Category moves down, last item's down arrow disabled
- **Fail**: No movement
- **If Failed**: Check the move-down handler.

### Test 11.9: Delete Category
- **Setup**: Category Manager open, "Archive" category exists
- **Action**: Click the Trash (delete) button on "Archive"
- **Expected**: "Archive" disappears from the list immediately (no confirmation dialog)
- **Pass**: Category removed
- **Fail**: Category persists, or confirmation dialog appears
- **If Failed**: Check the delete mutation.

### Test 11.10: Close Category Manager -- X Button
- **Setup**: Category Manager open
- **Action**: Click the X button in the top-right corner
- **Expected**: Modal closes
- **Pass**: Modal closes
- **Fail**: Modal stays open
- **If Failed**: Check close handler.

### Test 11.11: Close Category Manager -- Escape Key
- **Setup**: Category Manager open
- **Action**: Press Escape
- **Expected**: Modal closes
- **Pass**: Modal closes
- **Fail**: Modal stays open
- **If Failed**: Check Escape key handler on the modal.

### Test 11.12: Categories Appear in Sidebar Groups
- **Setup**: Category Manager closed, custom categories exist
- **Action**: Look at the sidebar conversation list
- **Expected**: Conversations are grouped by category. Category group headers show color dots matching the colors set in the Category Manager.
- **Pass**: Category groups visible with correct colors
- **Fail**: Groups missing, wrong colors, or conversations not grouped
- **If Failed**: Check the sidebar grouping logic. Verify the categories API returns correct data.

---

## Test Group 12: Bulk Operations

### Test 12.1: Enter Select Mode
- **Setup**: Sidebar visible, multiple conversations exist
- **Action**: Click the CheckSquare icon button in the sidebar header
- **Expected**: Checkboxes appear on every conversation row. A "Select Mode" action bar appears below the search input with "All/None" toggle and "Delete (N)" button. The CheckSquare icon changes to an X icon.
- **Pass**: Checkboxes visible, action bar visible, icon changed
- **Fail**: No checkboxes, no action bar, or icon unchanged
- **If Failed**: Check `selectMode` state toggle in `WorkspaceSidebar.tsx`.

### Test 12.2: Select Individual Conversations
- **Setup**: Select mode active (Test 12.1)
- **Action**: Click the checkbox on two conversation rows
- **Expected**: Checkboxes toggle to checked state. The "Delete (N)" button updates count (e.g., "Delete (2)"). Clicking a row does NOT navigate to it (select mode changes click behavior).
- **Pass**: Checkboxes toggle, count updates, no navigation
- **Fail**: Checkbox doesn't toggle, count wrong, or conversation navigates on click
- **If Failed**: Check the checkbox click handler. Verify `selectMode` changes row click behavior.

### Test 12.3: Select All
- **Setup**: Select mode active, some conversations checked
- **Action**: Click "All" in the action bar
- **Expected**: All conversation checkboxes become checked. Button text changes from "All" to "None". Delete count updates to total conversation count.
- **Pass**: All selected, button says "None", count is total
- **Fail**: Not all selected, button text wrong, or count wrong
- **If Failed**: Check the "All" toggle handler.

### Test 12.4: Deselect All (None)
- **Setup**: All conversations selected (Test 12.3), button says "None"
- **Action**: Click "None"
- **Expected**: All checkboxes unchecked. Button text changes back to "All". Delete count goes to 0.
- **Pass**: All deselected, button says "All"
- **Fail**: Some still selected
- **If Failed**: Check the "None" toggle handler.

### Test 12.5: Bulk Delete
- **Setup**: Select mode active, 2 conversations selected (not the one you want to keep)
- **Action**: Click "Delete (2)"
- **Expected**: Both selected conversations are deleted and disappear from the sidebar. If one of them was the active conversation, the chat area clears.
- **Pass**: Selected conversations removed
- **Fail**: Conversations persist, wrong ones deleted, or error
- **If Failed**: Check the bulk delete mutation. Verify it sends the correct list of conversation IDs.

### Test 12.6: Exit Select Mode
- **Setup**: Select mode active
- **Action**: Click the X icon in the sidebar header (where CheckSquare was)
- **Expected**: Select mode deactivates. Checkboxes disappear. Action bar disappears. X icon changes back to CheckSquare.
- **Pass**: Select mode off, checkboxes gone, icon restored
- **Fail**: Select mode persists
- **If Failed**: Check the toggle handler.

---

## Test Group 13: Keyboard Shortcuts

### Test 13.1: ? -- Show Shortcuts Help
- **Setup**: On Workspace page, no modal open, no input focused
- **Action**: Press the `?` key
- **Expected**: Keyboard shortcuts help modal appears showing a list of all shortcuts
- **Pass**: Modal opens with shortcuts list
- **Fail**: Nothing happens, or wrong modal opens
- **If Failed**: Check the global keyboard event listener. Verify it filters out events when an input is focused.

### Test 13.2: Shortcuts Modal Content
- **Setup**: Shortcuts modal open (Test 13.1)
- **Action**: Read the shortcuts list
- **Expected**: The following shortcuts are listed:
  - Ctrl/Cmd+N: New conversation
  - Ctrl/Cmd+L: Toggle library panel
  - Ctrl/Cmd+B: Toggle sidebar
  - Ctrl/Cmd+F: Focus search
  - Ctrl/Cmd+E: Export current chat
  - /: Focus chat input
  - 1, 2, 3: Toggle panels (split view)
  - ?: Show keyboard shortcuts
  - Esc: Close modal
- **Pass**: All shortcuts listed
- **Fail**: Shortcuts missing or wrong descriptions
- **If Failed**: Check `WorkspaceKeyboardHelp.tsx` content.

### Test 13.3: Escape -- Close Modal
- **Setup**: Shortcuts modal open (Test 13.1)
- **Action**: Press Escape
- **Expected**: Modal closes
- **Pass**: Modal closes
- **Fail**: Modal stays open
- **If Failed**: Check Escape key handler on the modal overlay.

### Test 13.4: Ctrl+N -- New Conversation
- **Setup**: On Workspace page, no input focused
- **Action**: Press Ctrl+N (or Cmd+N on Mac)
- **Expected**: New Chat form opens in the sidebar (same as clicking "New Chat")
- **Pass**: New Chat form opens
- **Fail**: Nothing happens, or browser's "new window" overrides
- **If Failed**: Check the global keyboard shortcut handler. Verify `e.preventDefault()` is called.

### Test 13.5: Ctrl+L -- Toggle Library Panel
- **Setup**: Library panel visible
- **Action**: Press Ctrl+L (or Cmd+L on Mac)
- **Expected**: Library panel collapses. Pressing again expands it.
- **Pass**: Library panel toggles collapse/expand
- **Fail**: Nothing happens
- **If Failed**: Check the Ctrl+L handler in the global keyboard listener.

### Test 13.6: Ctrl+B -- Toggle Sidebar
- **Setup**: Sidebar visible
- **Action**: Press Ctrl+B (or Cmd+B on Mac)
- **Expected**: Sidebar collapses to 0 width. Pressing again expands it to 272px.
- **Pass**: Sidebar toggles collapse/expand
- **Fail**: Nothing happens
- **If Failed**: Check the Ctrl+B handler.

### Test 13.7: Ctrl+F -- Focus Search
- **Setup**: Sidebar visible
- **Action**: Press Ctrl+F (or Cmd+F on Mac)
- **Expected**: Search input in the sidebar gains focus (cursor appears in search field)
- **Pass**: Search input focused
- **Fail**: Browser's "Find in page" activates instead, or nothing happens
- **If Failed**: Check the Ctrl+F handler and `e.preventDefault()`.

### Test 13.8: / -- Focus Chat Input
- **Setup**: On Workspace page, no input currently focused, active conversation exists
- **Action**: Press the `/` key
- **Expected**: Chat text input gains focus
- **Pass**: Chat input focused
- **Fail**: "/" character typed in search or other input, or nothing happens
- **If Failed**: Check the `/` handler. Verify it only triggers when no other input is focused.

### Test 13.9: Ctrl+E -- Export Current Chat
- **Setup**: Active conversation with messages
- **Action**: Press Ctrl+E (or Cmd+E on Mac)
- **Expected**: Browser downloads a .md file containing the current conversation
- **Pass**: Markdown file downloads
- **Fail**: Nothing happens, or empty file
- **If Failed**: Check the export handler.

### Test 13.10: 1, 2, 3 -- Panel Toggles (Split View)
- **Setup**: Split view active, all panels expanded
- **Action**: Press `1`
- **Expected**: Toggles the Research panel (collapses if expanded, expands if collapsed)
- **Pass**: Research panel toggles
- **Fail**: Nothing happens, or wrong panel toggles
- **If Failed**: Check the `1` key handler. Verify it only works in split view and when no input is focused.

### Test 13.11: Press `2` (Split View)
- **Setup**: Split view active
- **Action**: Press `2`
- **Expected**: Toggles the PRD Builder panel
- **Pass**: PRD Builder panel toggles
- **Fail**: Nothing happens
- **If Failed**: Check the `2` key handler.

### Test 13.12: Press `3` (Split View)
- **Setup**: Split view active
- **Action**: Press `3`
- **Expected**: Toggles the Coder panel
- **Pass**: Coder panel toggles
- **Fail**: Nothing happens
- **If Failed**: Check the `3` key handler.

### Test 13.13: Shortcuts Don't Fire When Input Focused
- **Setup**: Chat input focused (cursor in textarea)
- **Action**: Press `?`
- **Expected**: The `?` character is typed into the input. Shortcuts modal does NOT open.
- **Pass**: Character typed, no modal
- **Fail**: Shortcuts modal opens while typing
- **If Failed**: Check that the keyboard listener filters events when `document.activeElement` is an input/textarea.

---

## Test Group 14: Error Handling

### Test 14.1: Disconnected Backend -- Connection Indicator
- **Setup**: Active conversation, server running. Note the green connection indicator.
- **Action**: Stop the backend server (kill the Python process or stop `start_ui.bat`)
- **Expected**: Connection indicator in the chat header changes from green pulsing dot + Wifi icon to red dot + WifiOff icon. A yellow "Connecting" state (yellow dot + spinning Loader2) may appear briefly during reconnection attempts.
- **Pass**: Indicator changes to red/disconnected state
- **Fail**: Indicator stays green despite server being down
- **If Failed**: Check WebSocket reconnection logic and status state management.

### Test 14.2: Disconnection Banner
- **Setup**: Backend stopped, active conversation (Test 14.1)
- **Action**: Observe the chat area
- **Expected**: A red-tinted disconnection banner appears below the header with WifiOff icon, error message text, and a "Retry" link.
- **Pass**: Red banner visible with error details and Retry link
- **Fail**: No banner despite disconnection
- **If Failed**: Check the disconnection banner render condition in `WorkspaceChat.tsx`.

### Test 14.3: Retry Connection
- **Setup**: Backend stopped, disconnection banner visible (Test 14.2)
- **Action**: Restart the backend server (re-run `start_ui.bat`). Wait a few seconds for it to be ready. Click the "Retry" link in the disconnection banner.
- **Expected**: Connection re-establishes. Indicator changes back to green. Disconnection banner disappears. Previous messages are still visible.
- **Pass**: Connection restored, banner gone, messages intact
- **Fail**: Retry fails, banner persists, or messages lost
- **If Failed**: Check the retry handler. Verify WebSocket reconnects to the correct URL.

### Test 14.4: Send Message While Disconnected
- **Setup**: Backend stopped, active conversation
- **Action**: Try to type and send a message
- **Expected**: Input may be disabled, or if a send is attempted, an error state is shown (not a silent failure). The message should not be lost.
- **Pass**: Error state visible, user informed of disconnection
- **Fail**: Silent failure (message disappears with no feedback)
- **If Failed**: Check send handler's connection state check.

### Test 14.5: Page Refresh Preserves Conversations
- **Setup**: Backend running, active conversation with messages
- **Action**: Press F5 (or Ctrl+Shift+R for hard refresh)
- **Expected**: Page reloads. Workspace page loads. Previous conversations are still in the sidebar. Selecting a conversation shows its messages.
- **Pass**: Conversations and messages preserved after refresh
- **Fail**: Conversations missing, or messages lost
- **If Failed**: Check server-side persistence. Verify conversations and messages are stored in SQLite, not just in-memory state.

### Test 14.6: Connection Failed State -- Back to Conversations
- **Setup**: WebSocket connection fails for an active conversation
- **Action**: Look for "Back to Conversations" button in the connection failed state
- **Expected**: Clicking "Back to Conversations" deselects the current conversation and returns to the empty/list view
- **Pass**: Returns to conversation list without error
- **Fail**: Button missing, or clicking causes error
- **If Failed**: Check the "Back to Conversations" button handler.

### Test 14.7: Empty Library State
- **Setup**: No files in the workspace library
- **Action**: Open the Library Picker Modal (BookOpen button in chat input)
- **Expected**: Modal opens showing "This folder is empty" text
- **Pass**: Empty state message visible
- **Fail**: Blank modal, error, or modal doesn't open
- **If Failed**: Check empty state in `LibraryPickerModal.tsx`.

---

## Test Group 15: Additional Features

### Test 15.1: Token Log Panel -- Enable
- **Setup**: Active conversation
- **Action**: Click the "On" option in the Token Log 3-state toggle (Auto | On | Off) in the chat header area
- **Expected**: Token Log panel appears on the left side of the chat area (~320px). Shows header with Download, Clear, and Close buttons.
- **Pass**: Token log panel visible with header buttons
- **Fail**: Panel doesn't appear, or appears on wrong side
- **If Failed**: Check the token log toggle state and `TokenLogPanel.tsx` rendering.

### Test 15.2: Token Log Panel -- Entries During Streaming
- **Setup**: Token log set to "On", active conversation
- **Action**: Send a message and watch the token log during streaming
- **Expected**: Entries appear in real-time with colored badges: assistant_turn (cyan), tool_call (yellow), tool_result (orange), result_summary (green). Each shows token counts, cost, and duration.
- **Pass**: Entries appear during streaming with correct badges and data
- **Fail**: Panel empty during streaming, or wrong data
- **If Failed**: Check WebSocket token log events. Verify `TokenLogPanel.tsx` data handling.

### Test 15.3: Token Log Panel -- Auto Mode
- **Setup**: Set token log toggle to "Auto"
- **Action**: Send a message. Observe the panel during and after streaming.
- **Expected**: Panel appears automatically when streaming starts. Panel hides automatically when streaming ends and response is idle.
- **Pass**: Auto show/hide behavior works
- **Fail**: Panel stays visible after streaming, or never appears
- **If Failed**: Check the auto-mode logic tied to streaming state.

### Test 15.4: Token Log Panel -- Off Mode
- **Setup**: Set token log toggle to "Off"
- **Action**: Send a message
- **Expected**: Token log panel never appears, even during streaming
- **Pass**: Panel stays hidden
- **Fail**: Panel appears despite "Off" setting
- **If Failed**: Check the off-mode condition.

### Test 15.5: Token Log Panel -- Download
- **Setup**: Token log panel visible with entries
- **Action**: Click the Download button in the token log header
- **Expected**: Browser downloads a JSON file with the token log data
- **Pass**: JSON file downloads
- **Fail**: Nothing happens, or file is empty
- **If Failed**: Check the download handler.

### Test 15.6: Token Log Panel -- Clear
- **Setup**: Token log panel visible with entries
- **Action**: Click the Clear (trash) button in the token log header
- **Expected**: All entries are removed from the panel
- **Pass**: Panel cleared
- **Fail**: Entries persist
- **If Failed**: Check the clear handler.

### Test 15.7: Actions Menu -- Fork Chat
- **Setup**: Active conversation with at least 4 messages
- **Action**: Click the "..." (MoreHorizontal) button in the chat header. Click "Fork Chat".
- **Expected**: ChatForkModal opens showing a scrollable list of all messages with radio buttons. Each message shows a preview.
- **Pass**: Modal opens with message list and radio buttons
- **Fail**: Modal empty, or radio buttons missing
- **If Failed**: Check `ChatForkModal.tsx`.

### Test 15.8: Fork Chat -- Execute Fork
- **Setup**: Fork modal open (Test 15.7)
- **Action**: Click the radio button on the 2nd message (fork after that message). Click "Fork".
- **Expected**: A new conversation appears in the sidebar containing only the first 2 messages from the original conversation. The new conversation is selected automatically.
- **Pass**: New conversation created with correct subset of messages
- **Fail**: Fork fails, wrong messages copied, or too many/few messages
- **If Failed**: Check the fork mutation. Verify message slicing logic.

### Test 15.9: Actions Menu -- Inject from Chat
- **Setup**: At least two conversations exist, one is active
- **Action**: Click "..." > "Inject from Chat"
- **Expected**: InjectFromChatModal opens with Step 1: a list of all other conversations (excluding the current one). Search/browse functionality available.
- **Pass**: Modal opens showing other conversations
- **Fail**: Modal empty, or shows current conversation
- **If Failed**: Check `InjectFromChatModal.tsx`. Verify conversation filtering excludes current.

### Test 15.10: Inject from Chat -- Select Source and Messages
- **Setup**: Inject modal open at Step 1 (Test 15.9)
- **Action**: Click a source conversation. In Step 2, check some (not all) messages. Click "Inject (N)".
- **Expected**: An injection indicator appears above the chat input: "Injecting N message(s) from [Source Title]" with a dismiss (X) button. Selected messages are queued for the next send.
- **Pass**: Injection indicator visible with correct count and source name
- **Fail**: Indicator missing, wrong count, or injection fails
- **If Failed**: Check the injection state management. Verify the indicator rendering.

### Test 15.11: Inject from Chat -- Dismiss Injection
- **Setup**: Injection indicator visible (Test 15.10)
- **Action**: Click the X button on the injection indicator
- **Expected**: Indicator disappears. Injection is cancelled (messages will not be prepended to next send).
- **Pass**: Indicator removed, injection cleared
- **Fail**: Indicator persists, or injection still happens on next send
- **If Failed**: Check the dismiss handler.

### Test 15.12: Actions Menu -- Export as Markdown
- **Setup**: Active conversation with messages
- **Action**: Click "..." > "Export as Markdown"
- **Expected**: Browser downloads a .md file. The file contains the conversation messages formatted in Markdown.
- **Pass**: File downloads with conversation content
- **Fail**: No download, or file empty/malformed
- **If Failed**: Check the export handler and markdown formatting logic.

### Test 15.13: Usage Dashboard -- Expand/Collapse
- **Setup**: Active conversation with at least one exchange
- **Action**: Click the compact control bar area to expand the Usage Dashboard
- **Expected**: Dashboard expands showing usage bars for daily/weekly/monthly periods, cost zone breakdown, and rate limit event log.
- **Pass**: Dashboard expands with usage data
- **Fail**: Dashboard doesn't expand, or shows no data
- **If Failed**: Check `UsageDashboard.tsx` and the usage data source.

### Test 15.14: Auto-Summary Pin
- **Setup**: Active conversation with several messages (enough for auto-summary to generate)
- **Action**: Look for the Auto-Summary pin card above the messages
- **Expected**: Collapsible card showing "Summary (N messages) - updated Xm ago" with a ChevronRight toggle and RefreshCw button
- **Pass**: Summary card visible (if summary has been generated)
- **Fail**: Card missing despite many messages
- **If Failed**: Check auto-summary generation trigger. Verify `AutoSummaryPin.tsx`.

### Test 15.15: Auto-Summary Pin -- Expand and Regenerate
- **Setup**: Auto-summary pin visible (Test 15.14)
- **Action**: Click the summary card to expand it. Then click the RefreshCw (regenerate) button.
- **Expected**: Expanded: summary text is visible. Regenerate: RefreshCw icon spins during regeneration. Updated summary appears.
- **Pass**: Summary text displays on expand; regeneration produces updated text
- **Fail**: No text on expand, or regeneration fails
- **If Failed**: Check the expand toggle and regenerate API call.

### Test 15.16: Walkie-Talkie Settings Panel
- **Setup**: Active conversation
- **Action**: Click the gear (Settings) icon in the chat header
- **Expected**: Amber-tinted settings panel slides in below the header with:
  1. Check Frequency: "Per Feature", "Every Tool Call", "Never" (3 buttons)
  2. Wait Timeout: "30s", "1m", "2m", "5m" (4 buttons)
  3. Auto-reply on timeout: toggle switch
  4. Info text about changes taking effect on next session
  5. Close button (X)
- **Pass**: Panel visible with all settings controls
- **Fail**: Panel doesn't appear, or settings missing
- **If Failed**: Check the gear button toggle and settings panel rendering.

### Test 15.17: Walkie-Talkie Settings -- Change and Close
- **Setup**: WT settings panel open (Test 15.16)
- **Action**: Click "Every Tool Call" for check frequency. Click "2m" for wait timeout. Toggle the auto-reply switch. Click the X to close.
- **Expected**: Selected buttons highlight. Switch toggles. Panel closes on X click. Settings persist (reopen panel to verify).
- **Pass**: Selections persist after close/reopen
- **Fail**: Settings reset on close, or don't save
- **If Failed**: Check settings save mutation.

### Test 15.18: Guide Button -- User Guide Panel
- **Setup**: On Workspace page
- **Action**: Click the "Guide" button in the nav bar
- **Expected**: A floating panel appears (draggable, resizable) with tabbed documentation sections (General, Shortcuts, Sidebar, Chat, etc.) plus a Notes tab.
- **Pass**: Floating panel visible with tabs
- **Fail**: Panel doesn't appear, or tabs missing
- **If Failed**: Check `WorkspaceUserGuide.tsx`.

### Test 15.19: User Guide -- Notes Tab
- **Setup**: User Guide panel open (Test 15.18)
- **Action**: Click the "Notes" tab. Type a note. Close the panel. Reopen it.
- **Expected**: Note persists (stored in localStorage). CRUD operations work (create, read, update, delete notes).
- **Pass**: Notes persist across close/reopen
- **Fail**: Notes lost on close
- **If Failed**: Check localStorage persistence for notes.

### Test 15.20: Swarm Panel -- Open
- **Setup**: On Workspace page
- **Action**: Click the "Swarm" button in the nav bar
- **Expected**: Swarm panel slides in (~320px) between the chat area and library panel. Shows "SWARM" header with Network icon. If no swarm is running, shows task input area with textarea and "Launch Swarm" button.
- **Pass**: Panel visible with header and task input
- **Fail**: Panel doesn't appear, or overlaps content
- **If Failed**: Check swarm panel toggle state.

### Test 15.21: Swarm Panel -- Close
- **Setup**: Swarm panel open (Test 15.20)
- **Action**: Click the X button in the swarm panel header
- **Expected**: Panel closes, chat area and library panel readjust
- **Pass**: Panel closes cleanly
- **Fail**: Panel stays open, or layout broken after close
- **If Failed**: Check the close handler.

### Test 15.22: Nav Bar Navigation -- Roles Button
- **Setup**: On Workspace page
- **Action**: Click the "Roles" button in the nav bar
- **Expected**: Page navigates to `/#/roles`
- **Pass**: URL changes to `/#/roles`, page loads
- **Fail**: Nothing happens, or wrong page
- **If Failed**: Check the Roles button handler.

### Test 15.23: Nav Bar Navigation -- Dashboard Button
- **Setup**: On Workspace page
- **Action**: Click the "Dashboard" button in the nav bar
- **Expected**: Page navigates to `/#/dashboard`
- **Pass**: URL changes to `/#/dashboard`, page loads
- **Fail**: Nothing happens, or wrong page
- **If Failed**: Check the Dashboard button handler.

### Test 15.24: Nav Bar Navigation -- Back to AutoForge
- **Setup**: On Workspace page
- **Action**: Click the back arrow + "AutoForge" button (far left of nav bar)
- **Expected**: Page navigates to the main AutoForge dashboard (root hash or `/#/`)
- **Pass**: Navigates to main dashboard
- **Fail**: Nothing happens
- **If Failed**: Check the `window.location.hash = ''` logic.

### Test 15.25: Git Activity Widget
- **Setup**: Active conversation with a repo attached
- **Action**: Click the "G" button in the nav bar
- **Expected**: Dropdown appears showing the last 10 commits with: commit hashes, messages, and relative timestamps. Badge count (if any unseen commits) resets on open.
- **Pass**: Dropdown with commit list
- **Fail**: Dropdown empty, "G" button not visible, or error
- **If Failed**: Check `GitActivityWidget.tsx` and the backend git log API.

### Test 15.26: CI Status Widget
- **Setup**: Active conversation with a repo attached
- **Action**: Observe the CI status indicator in the nav bar (near the "G" button)
- **Expected**: Shows a compact indicator. States include: idle (gray dot), running (cyan spinner), passed (green check), failed (red X). Click to expand for details.
- **Pass**: Indicator visible with appropriate state
- **Fail**: Indicator missing or shows wrong state
- **If Failed**: Check `CIStatusWidget.tsx` and CI monitoring initialization.

---

## Summary Checklist

| Group | Tests | Critical? |
|-------|-------|-----------|
| 1. Page Load | 1.1 - 1.6 | YES |
| 2. New Chat Form | 2.1 - 2.18 | YES |
| 3. Chat Session | 3.1 - 3.8 | YES |
| 4. Conversation List | 4.1 - 4.9 | YES |
| 5. Conversation Row Actions | 5.1 - 5.11 | YES |
| 6. Model Badge Cycling | 6.1 - 6.4 | MEDIUM |
| 7. Chat Header | 7.1 - 7.14 | YES |
| 8. Chat Input | 8.1 - 8.16 | YES |
| 9. Right Panels | 9.1 - 9.13 | MEDIUM |
| 10. Split View | 10.1 - 10.16 | MEDIUM |
| 11. Category Management | 11.1 - 11.12 | MEDIUM |
| 12. Bulk Operations | 12.1 - 12.6 | MEDIUM |
| 13. Keyboard Shortcuts | 13.1 - 13.13 | LOW |
| 14. Error Handling | 14.1 - 14.7 | YES |
| 15. Additional Features | 15.1 - 15.26 | MEDIUM |

**Total: 153 tests across 15 groups**

Priority order for testing: Groups 1, 2, 3 (core functionality), then 4, 5, 7, 8, 14 (essential interactions), then remaining groups.
