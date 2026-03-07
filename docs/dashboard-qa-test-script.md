# Dashboard Page -- QA Test Script

This is an executable test script for AI agents to verify every feature on the Dashboard page (`/#/dashboard`). Each test has a concrete action, expected result, pass/fail criteria, and investigation guidance on failure.

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

### Test 1.1: Navigate to Dashboard
- **Setup**: Server running at localhost:8888
- **Action**: Navigate to `http://localhost:8888/#/dashboard`
- **Expected**: Dashboard page renders with two zones: sidebar (left, ~272px) and pane area (right, flexible). A top navigation bar spans full width. Default layout is dual (two panes).
- **Pass**: Sidebar visible on left, two panes visible side-by-side, no overlapping elements, no blank sections
- **Fail**: Blank screen, infinite spinner, missing zones, or components overlapping
- **If Failed**: Check browser console for JavaScript errors. Check `DashboardPage.tsx` for render crashes. Verify the `/#/dashboard` route is registered in `App.tsx`.

### Test 1.2: No Console Errors on Load
- **Setup**: Open browser DevTools Console (F12) before navigating
- **Action**: Navigate to `http://localhost:8888/#/dashboard`
- **Expected**: No red error messages in the console. Warnings are acceptable but errors are not.
- **Pass**: Zero red console errors
- **Fail**: One or more red console errors appear
- **If Failed**: Note the exact error text and stack trace. Common issues: missing API endpoints (check server routers), undefined state variables (check hooks), failed WebSocket connections (check server is running).

### Test 1.3: Top Nav Bar Elements Present
- **Setup**: On Dashboard page, browser wider than 768px
- **Action**: Visually inspect the top navigation bar
- **Expected**: The following elements are visible left-to-right:
  1. Back arrow + "AutoForge" text (left side)
  2. ChevronRight separator + "Dashboard" label
  3. ChevronRight separator + RepoSelector button ("Select Repo" or selected repo name)
  4. Right side: Layout mode buttons (1, 2, 3) with vertical divider, "Workspace" link
- **Pass**: All listed elements are present and visible
- **Fail**: Any element missing or mispositioned
- **If Failed**: Check `DashboardPage.tsx` nav bar render. Verify imports for layout icons and `RepoSelector`.

### Test 1.4: Sidebar Visible with Header
- **Setup**: On Dashboard page
- **Action**: Look at the left sidebar
- **Expected**: Sidebar visible (~272px wide) with "Conversations" header text, a select-mode toggle button (CheckSquare icon), and a collapse button (PanelLeftClose icon)
- **Pass**: Sidebar header with all buttons visible
- **Fail**: Sidebar missing, collapsed by default, or header elements missing
- **If Failed**: Check `WorkspaceSidebar.tsx` initial render state. Verify `sidebarCollapsed` initializes to false in `DashboardPage.tsx`.

### Test 1.5: Dual Panes Visible by Default
- **Setup**: Fresh page load (no localStorage state), browser wider than 768px
- **Action**: Look at the pane area to the right of the sidebar
- **Expected**: Two panes visible side-by-side. First pane defaults to Claude provider, second pane defaults to Codex. Each pane has a header bar with provider selector pills and a label.
- **Pass**: Two panes with distinct provider headers (Claude blue active, Codex emerald active)
- **Fail**: Only one pane, three panes, or panes without headers
- **If Failed**: Check localStorage for `dashboard-layout` and `dashboard-panes` keys that may override defaults. Clear them and reload. Check `DashboardPage.tsx` initial state.

### Test 1.6: Provider Selector Visible in Each Pane
- **Setup**: On Dashboard page with dual layout
- **Action**: Look at each pane's header bar
- **Expected**: Each pane has a rounded-full pill strip with three buttons: Claude, Codex, Gemini. One is filled with its provider color (active); the other two are neutral.
- **Pass**: Both panes show provider pill strips with correct active states
- **Fail**: Provider selectors missing, or both panes show same active provider
- **If Failed**: Check `ProviderSelector` component render in `DashboardPage.tsx`. Verify the `PROVIDERS` array.

### Test 1.7: Empty State in Panes
- **Setup**: On Dashboard page with no conversations loaded
- **Action**: Observe the chat area within each pane
- **Expected**: Each pane shows an empty state with its panel label (e.g., "CLAUDE SESSION", "CODEX SESSION")
- **Pass**: Empty state messages visible in both panes
- **Fail**: Blank panes without messaging, or error displayed
- **If Failed**: Check `WorkspaceChat.tsx` empty state rendering. Verify `panelLabel` prop is passed correctly.

### Test 1.8: Empty State in Sidebar
- **Setup**: Fresh workspace with no conversations
- **Action**: Observe the sidebar conversation list
- **Expected**: Sidebar shows MessageSquare icon + "No conversations yet"
- **Pass**: Empty state message visible
- **Fail**: Blank area or error
- **If Failed**: Check conversation list query in `WorkspaceSidebar.tsx`.

---

## Test Group 2: Layout Mode Switching

### Test 2.1: Switch to Single Pane
- **Setup**: On Dashboard page in dual layout (default)
- **Action**: Click the "1" layout button (Square icon)
- **Expected**: Pane area shows one full-width pane. The "1" button highlights with primary color. The "2" button becomes neutral.
- **Pass**: Single pane visible, button highlights correctly
- **Fail**: Still shows two panes, or layout button doesn't highlight
- **If Failed**: Check `setLayoutMode` handler. Verify the `useEffect` that syncs pane count with layout mode.

### Test 2.2: Switch to Triple Pane
- **Setup**: On Dashboard page in single layout (Test 2.1)
- **Action**: Click the "3" layout button (Columns3 icon)
- **Expected**: Three panes visible side-by-side. The third pane gets the remaining unused provider (Gemini if Claude and Codex are used). The "3" button highlights.
- **Pass**: Three panes visible with three distinct providers (Claude, Codex, Gemini)
- **Fail**: Wrong number of panes, or duplicate providers
- **If Failed**: Check the pane-adding logic in the `useEffect` that handles `layoutMode` changes. Verify `available` provider selection.

### Test 2.3: Switch Back to Dual
- **Setup**: Triple layout active (Test 2.2)
- **Action**: Click the "2" layout button (Columns2 icon)
- **Expected**: Third pane removed. First two panes remain with their providers and any loaded conversations. The "2" button highlights.
- **Pass**: Two panes visible, third pane gone, first two panes retain their state
- **Fail**: Wrong panes removed (e.g., second pane removed instead of third), or state lost
- **If Failed**: Check `prev.slice(0, targetCount)` logic in the layout sync effect.

### Test 2.4: Layout Mode Persists on Reload
- **Setup**: Set layout to triple (click "3")
- **Action**: Reload the page (F5)
- **Expected**: Page loads in triple layout. The "3" button is highlighted.
- **Pass**: Triple layout restored from localStorage
- **Fail**: Reverts to dual (default)
- **If Failed**: Check that localStorage key `dashboard-layout` is written on layout change. Check the `useState` initializer that reads from localStorage.

### Test 2.5: New Panes Get Unused Providers
- **Setup**: Start in single pane (Claude)
- **Action**: Click "2" to add a second pane
- **Expected**: Second pane appears with Codex provider (first unused provider after Claude)
- **Pass**: Second pane shows Codex as active provider
- **Fail**: Second pane shows Claude (duplicate) or no provider
- **If Failed**: Check the `usedProviders` / `available` logic when adding panes.

### Test 2.6: Shrinking Layout Keeps First N Panes
- **Setup**: Triple layout with Claude (pane 1), Codex (pane 2), Gemini (pane 3). Load a conversation in pane 2.
- **Action**: Click "2" to switch to dual layout
- **Expected**: Panes 1 and 2 remain (Claude and Codex). Pane 3 (Gemini) is removed. The conversation in pane 2 is still loaded.
- **Pass**: First two panes preserved with state; third pane gone
- **Fail**: Conversation in pane 2 lost, or wrong pane removed
- **If Failed**: Check that `prev.slice(0, targetCount)` preserves pane order and state.

---

## Test Group 3: Provider Selection

### Test 3.1: Switch Pane Provider to Codex
- **Setup**: Dual layout, first pane is Claude
- **Action**: In the first pane's header, click the "Codex" pill
- **Expected**: "Codex" pill fills with emerald color. Pane label changes from "CLAUDE" to "CODEX". Pane's conversation clears to empty state (because conversations are provider-specific).
- **Pass**: Provider switches, conversation clears, label updates
- **Fail**: Provider doesn't switch, conversation persists, or label unchanged
- **If Failed**: Check `handlePaneProviderChange`. Verify it sets `conversationId: null` and updates `label`.

### Test 3.2: Switch Pane Provider to Gemini
- **Setup**: Any pane with a non-Gemini provider
- **Action**: Click the "Gemini" pill
- **Expected**: "Gemini" pill fills with violet color. Pane label updates. Conversation clears.
- **Pass**: Gemini active, label reads "GEMINI", conversation cleared
- **Fail**: Same as Test 3.1 failure modes
- **If Failed**: Same investigation as Test 3.1.

### Test 3.3: Provider Switch Resets Conversation
- **Setup**: Load a Claude conversation in a pane
- **Action**: Switch the pane's provider from Claude to Codex
- **Expected**: The conversation is cleared from the pane (returns to empty state). The conversation still exists in the sidebar.
- **Pass**: Pane empty, conversation still in sidebar
- **Fail**: Conversation still displayed in pane, or conversation deleted from sidebar
- **If Failed**: Check that `handlePaneProviderChange` sets `conversationId: null`.

### Test 3.4: Sidebar Model Pills Sync with First Pane Provider
- **Setup**: Dual layout, first pane is Claude, sidebar visible with New Chat form open
- **Action**: Switch the first pane's provider to Codex
- **Expected**: Sidebar model pills change from Claude presets ("Opus 4.6 . 1M", "Sonnet 4.6 . 1M", "Opus 4.6 . 200K") to Codex presets ("GPT-5.4", "GPT-5.4 Pro", "GPT-5.3", "o3", "o4-mini").
- **Pass**: Model pills update to Codex models with emerald active color
- **Fail**: Model pills still show Claude presets
- **If Failed**: Check that `activeProvider` prop passed to `WorkspaceSidebar` reflects `panes[0].provider`. Check `buildPresetsForProvider` in the sidebar.

### Test 3.5: Sidebar Model Pills Show Gemini Presets
- **Setup**: First pane switched to Gemini, sidebar New Chat form open
- **Action**: Observe the model pills
- **Expected**: Pills show Gemini presets: "Gemini 3.1 Pro", "Gemini 3.1 Flash", "Gemini 3.1 Flash Lite" with violet active color
- **Pass**: Gemini model pills visible with correct labels
- **Fail**: Wrong model pills, or Claude pills still shown
- **If Failed**: Check `useWorkspaceProviders` hook. Verify backend returns Gemini provider definition.

### Test 3.6: Thinking Effort Hidden for Non-Claude Providers
- **Setup**: First pane provider is Codex (or Gemini), sidebar New Chat form open
- **Action**: Observe the area below model pills
- **Expected**: Thinking Effort selector is NOT visible. It only appears when the first pane's provider is Claude.
- **Pass**: No Thinking Effort section visible
- **Fail**: Thinking Effort selector still visible for Codex/Gemini
- **If Failed**: Check the `isClaudeProvider` conditional in `WorkspaceSidebar.tsx`.

### Test 3.7: Model Preset Index Resets on Provider Switch
- **Setup**: First pane is Claude, model preset index is 2 (Opus 200K selected)
- **Action**: Switch first pane to Codex
- **Expected**: Model preset index resets to 0 (first Codex model selected)
- **Pass**: First Codex model pill is highlighted
- **Fail**: Index out of bounds, or third pill highlighted despite fewer Codex models
- **If Failed**: Check `setModelPresetIndex(0)` call in `handlePaneProviderChange`.

### Test 3.8: Provider Pill Radio Group Accessibility
- **Setup**: Any pane with provider selector
- **Action**: Inspect the provider selector with accessibility tools
- **Expected**: Container has `role="radiogroup"` with `aria-label="Provider selection"`. Each button has `role="radio"` and `aria-checked` matching its active state.
- **Pass**: ARIA attributes present and correct
- **Fail**: Missing roles or wrong aria-checked values
- **If Failed**: Check `ProviderSelector` component in `DashboardPage.tsx`.

---

## Test Group 4: New Chat Form (Provider-Aware)

### Test 4.1: Open New Chat Form
- **Setup**: On Dashboard page, sidebar visible
- **Action**: Click the "New Chat" button (Plus icon + "New Chat" text + ChevronDown)
- **Expected**: Form slides open showing: Name input, Folder dropdown, Attach Repository toggle, Model pills (matching first pane's provider), and "Start Chat" button. ChevronDown rotates 180 degrees.
- **Pass**: Form visible with all fields, chevron rotated
- **Fail**: Form does not appear, fields missing, no animation
- **If Failed**: Check `showNewChatForm` state toggle in `WorkspaceSidebar.tsx`.

### Test 4.2: Name Input Auto-Focus
- **Setup**: New Chat form is open (Test 4.1)
- **Action**: Observe cursor position immediately after form opens
- **Expected**: The Name text input is auto-focused (cursor blinking inside it)
- **Pass**: Input has focus, cursor visible
- **Fail**: Input not focused
- **If Failed**: Check the `useEffect` with `namingInputRef.current?.focus()` and the 50ms delay timer.

### Test 4.3: Name Input Enter to Submit
- **Setup**: New Chat form open, Name input focused
- **Action**: Type "Dashboard Test Alpha" then press Enter
- **Expected**: A new conversation is created with the name "Dashboard Test Alpha" and the first pane's active provider. It appears in the sidebar and loads in the first pane. The form closes.
- **Pass**: Conversation created with correct name and provider, visible in sidebar, form closed
- **Fail**: Enter does not submit, conversation not created, or name incorrect
- **If Failed**: Check `onKeyDown` handler for Enter key. Check the create conversation API mutation. Verify the `provider: activeProvider` field is included in the payload.

### Test 4.4: Name Input Escape to Cancel
- **Setup**: Open the New Chat form, type something in the Name field
- **Action**: Press Escape
- **Expected**: Form closes. Fields reset (name cleared).
- **Pass**: Form closes and fields are empty on next open
- **Fail**: Form stays open, or fields retain values
- **If Failed**: Check `handleCancelNaming` function.

### Test 4.5: Claude Model Pills
- **Setup**: First pane is Claude, New Chat form open
- **Action**: Observe the Model pills
- **Expected**: Three pills visible: "Opus 4.6 . 1M" (blue active), "Sonnet 4.6 . 1M" (violet when active), "Opus 4.6 . 200K" (zinc when active). One is selected (highlighted).
- **Pass**: All three pills visible with correct labels and colors
- **Fail**: Pills missing, wrong labels, or no selection highlight
- **If Failed**: Check `CLAUDE_MODEL_PRESETS` and `buildPresetsForProvider` in `WorkspaceSidebar.tsx`.

### Test 4.6: Claude Model Pill Selection
- **Setup**: First pane is Claude, New Chat form open, model pills visible
- **Action**: Click each pill one at a time
- **Expected**: Each clicked pill highlights with its color (blue for Opus 1M, violet for Sonnet, zinc for 200K). Previously selected pill deselects.
- **Pass**: Single-selection behavior, correct color per pill
- **Fail**: Multiple pills selected, no highlight change, or wrong colors
- **If Failed**: Check `modelPresetIndex` state and `onModelPresetChange` callback.

### Test 4.7: Codex Model Pills
- **Setup**: Switch first pane to Codex, open New Chat form
- **Action**: Observe the Model pills
- **Expected**: Codex model pills appear with emerald active color. Labels come from the backend provider definition (e.g., "GPT-5.4", "GPT-5.4 Pro", "GPT-5.3", "o3", "o4-mini").
- **Pass**: Codex-specific model pills visible with emerald highlight
- **Fail**: Claude pills still showing, or empty pill strip
- **If Failed**: Check `useWorkspaceProviders` hook data. Verify backend endpoint `/api/workspace/providers` returns Codex provider definition.

### Test 4.8: Gemini Model Pills
- **Setup**: Switch first pane to Gemini, open New Chat form
- **Action**: Observe the Model pills
- **Expected**: Gemini model pills appear with violet active color. Labels from backend (e.g., "Gemini 3.1 Pro", "Gemini 3.1 Flash", "Gemini 3.1 Flash Lite").
- **Pass**: Gemini-specific model pills visible with violet highlight
- **Fail**: Wrong pills showing, or empty
- **If Failed**: Same investigation as Test 4.7, but for Gemini provider.

### Test 4.9: Thinking Effort -- Visible for Claude
- **Setup**: First pane is Claude, New Chat form open
- **Action**: Look below model pills
- **Expected**: "Thinking Effort" section visible with three pills: Low (emerald), Medium (blue), High (orange). Grayed out unless Opus 1M is selected.
- **Pass**: Thinking Effort section present
- **Fail**: Section missing
- **If Failed**: Check `isClaudeProvider` conditional rendering.

### Test 4.10: Thinking Effort -- Hidden for Codex
- **Setup**: First pane is Codex, New Chat form open
- **Action**: Look below model pills
- **Expected**: No "Thinking Effort" section visible
- **Pass**: Section absent
- **Fail**: Section visible for Codex
- **If Failed**: Check `isClaudeProvider` is false when `activeProvider === 'codex'`.

### Test 4.11: Thinking Effort -- Disabled for Sonnet
- **Setup**: First pane is Claude, select "Sonnet 4.6 . 1M" model preset
- **Action**: Observe the Thinking Effort section
- **Expected**: Section visible but grayed out (opacity ~35%, not clickable). Text shows "(Opus 1M only)".
- **Pass**: Selector grayed out and non-interactive
- **Fail**: Selector active for Sonnet
- **If Failed**: Check `isOpus1M` condition: `selectedPreset?.context === '1m' && selectedPreset?.model === 'opus'`.

### Test 4.12: Thinking Effort -- Enabled for Opus 1M
- **Setup**: First pane is Claude, select "Opus 4.6 . 1M" model preset
- **Action**: Click each effort pill: Low, Medium, High
- **Expected**: Each pill highlights with its color. A use-case description appears below when Opus 1M is active. Tooltips show on hover.
- **Pass**: Pills toggle correctly, descriptions appear
- **Fail**: Selector stays grayed out on Opus 1M
- **If Failed**: Check the `isOpus1M` computed value.

### Test 4.13: Folder Dropdown
- **Setup**: New Chat form open
- **Action**: Click the "Folder" dropdown
- **Expected**: Dropdown shows "No folder" (default) plus any user-created categories
- **Pass**: Dropdown displays options
- **Fail**: Dropdown empty or doesn't open
- **If Failed**: Check categories API query.

### Test 4.14: Attach Repository Toggle
- **Setup**: New Chat form open
- **Action**: Click the "Attach Repository" toggle switch
- **Expected**: Toggle animates to ON. RepoSelector dropdown appears below it.
- **Pass**: Toggle ON, RepoSelector visible
- **Fail**: Toggle doesn't animate, or RepoSelector missing
- **If Failed**: Check `attachRepo` state and conditional render.

### Test 4.15: Start Chat -- Claude Conversation
- **Setup**: First pane is Claude, New Chat form open, name filled as "Claude QA Test"
- **Action**: Click "Start Chat"
- **Expected**: Button shows "Creating...". Conversation created with provider=claude. Appears in sidebar. Loads in first pane. Form closes.
- **Pass**: Conversation created with correct provider, loaded in pane
- **Fail**: Wrong provider, not loaded, or error
- **If Failed**: Check create mutation payload includes `provider: 'claude'`. Check network tab for POST request.

### Test 4.16: Start Chat -- Codex Conversation
- **Setup**: First pane switched to Codex, New Chat form open, name filled as "Codex QA Test", Codex model selected
- **Action**: Click "Start Chat"
- **Expected**: Conversation created with provider=codex. Badge in sidebar shows abbreviated Codex model ID (e.g., "5.4") in emerald.
- **Pass**: Conversation has codex provider; sidebar badge is emerald with correct abbreviation
- **Fail**: Provider is claude, or badge color wrong
- **If Failed**: Check `activeProvider` value passed to `handleCreateNamedChat`. Verify sidebar badge rendering for non-Claude providers.

### Test 4.17: Start Chat -- Gemini Conversation
- **Setup**: First pane switched to Gemini, New Chat form open, name filled as "Gemini QA Test", Gemini model selected
- **Action**: Click "Start Chat"
- **Expected**: Conversation created with provider=gemini. Badge in sidebar shows abbreviated Gemini model ID (e.g., "3.1P") in violet.
- **Pass**: Conversation has gemini provider; sidebar badge is violet
- **Fail**: Wrong provider or badge color
- **If Failed**: Same investigation as Test 4.16 for Gemini.

### Test 4.18: Cancel Form Resets Fields
- **Setup**: New Chat form open, name typed, folder selected, repo toggle on
- **Action**: Click the X button
- **Expected**: Form closes. On next open: name empty, folder "No folder", attach repo OFF.
- **Pass**: All fields reset
- **Fail**: Fields retain values
- **If Failed**: Check `handleCancelNaming` resets: `setNewChatName('')`, `setNewChatCategory('')`, `setAttachRepo(false)`.

---

## Test Group 5: Conversation List

### Test 5.1: Conversations Appear in Sidebar
- **Setup**: At least two conversations exist (create from Tests 4.15-4.17)
- **Action**: Look at the sidebar conversation list
- **Expected**: All created conversations visible as clickable rows with titles and relative timestamps
- **Pass**: All conversations visible in sidebar
- **Fail**: Conversations missing, duplicated, or wrong titles
- **If Failed**: Check the conversations API query. Verify `useQuery` refetch after creation.

### Test 5.2: Click Conversation Loads in First Pane
- **Setup**: Dual layout, both panes empty, Claude conversation exists
- **Action**: Click the Claude conversation row
- **Expected**: Conversation loads in the first pane (index 0). First pane's provider updates to Claude (if not already). Sidebar row highlights.
- **Pass**: Chat loads in first pane, row highlights
- **Fail**: Chat doesn't load, loads in wrong pane, or no highlight
- **If Failed**: Check `handleSelectConversation` logic. Verify it finds an empty pane or defaults to pane 0.

### Test 5.3: Click Conversation Assigns to Provider-Matching Pane
- **Setup**: Dual layout. First pane is Claude, second pane is Codex (both empty). A Codex conversation exists.
- **Action**: Click the Codex conversation row
- **Expected**: Conversation loads in the second pane (which matches the Codex provider) rather than the first pane.
- **Pass**: Conversation in second pane (Codex)
- **Fail**: Conversation in first pane
- **If Failed**: Check the `matchIdx` logic in `handleSelectConversation` that prefers matching provider.

### Test 5.4: Click Conversation Syncs Pane Provider
- **Setup**: Dual layout. First pane is Claude (empty), second pane is Codex (loaded). A Gemini conversation exists.
- **Action**: Click the Gemini conversation row
- **Expected**: First pane (empty) loads the Gemini conversation. First pane's provider updates from Claude to Gemini (provider sync).
- **Pass**: First pane shows Gemini conversation with Gemini provider active
- **Fail**: Provider mismatch, or conversation loads but provider doesn't update
- **If Failed**: Check the `if (provider && provider !== p.provider)` branch in `handleSelectConversation`.

### Test 5.5: Search -- Client-Side Filter
- **Setup**: Multiple conversations with distinct names exist
- **Action**: Type 1-2 characters in the search input that match one conversation name
- **Expected**: Sidebar list filters to show only matching conversations
- **Pass**: List filters correctly
- **Fail**: No filtering
- **If Failed**: Check client-side filter logic in `WorkspaceSidebar.tsx`.

### Test 5.6: Search -- Server-Side Search
- **Setup**: Conversations with messages exist
- **Action**: Type 3+ characters matching a message
- **Expected**: Overlay dropdown with search results and highlighted excerpts
- **Pass**: Results with excerpts appear
- **Fail**: No overlay or results
- **If Failed**: Check search API endpoint and debounce logic.

### Test 5.7: Search -- Click Result Loads in Pane
- **Setup**: Server-side search results visible (Test 5.6)
- **Action**: Click a search result
- **Expected**: Conversation is selected, loads in a pane, search overlay closes
- **Pass**: Conversation loads, overlay closes
- **Fail**: Nothing happens or overlay stays open
- **If Failed**: Check click handler on search result items and the `onSelectConversation` callback.

### Test 5.8: Search -- Clear and Escape
- **Setup**: Text in search input
- **Action**: Click X to clear, or press Escape
- **Expected**: Search clears, full conversation list restores
- **Pass**: Input cleared, full list shown
- **Fail**: Text remains or list still filtered
- **If Failed**: Check clear handler and `onKeyDown` Escape handler.

---

## Test Group 6: Conversation Row Actions

### Test 6.1: Hover to Reveal Action Buttons
- **Setup**: Conversations exist, not in select mode
- **Action**: Hover over a conversation row
- **Expected**: Three icon buttons appear: FolderPlus, Pin, Delete (Trash2)
- **Pass**: All three buttons visible on hover
- **Fail**: Buttons don't appear
- **If Failed**: Check hover state and conditional rendering in conversation row.

### Test 6.2: Pin a Conversation
- **Setup**: Unpinned conversation exists
- **Action**: Hover the row, click Pin button
- **Expected**: Conversation moves to "Pinned" group at top of sidebar with star icon
- **Pass**: Conversation in Pinned group
- **Fail**: Conversation doesn't move
- **If Failed**: Check pin mutation and group sorting logic.

### Test 6.3: Unpin a Conversation
- **Setup**: Pinned conversation exists (Test 6.2)
- **Action**: Hover the pinned row, click Pin button again
- **Expected**: Conversation moves back to its category group
- **Pass**: Removed from Pinned group
- **Fail**: Still pinned
- **If Failed**: Check unpin toggle logic.

### Test 6.4: Delete Non-Active Conversation
- **Setup**: Two+ conversations, one is NOT loaded in any pane
- **Action**: Hover the unloaded conversation, click Delete (Trash2)
- **Expected**: Conversation removed from sidebar. No panes affected.
- **Pass**: Conversation gone, panes unchanged
- **Fail**: Conversation remains, or wrong conversation deleted
- **If Failed**: Check delete mutation targets correct ID.

### Test 6.5: Delete Active Conversation -- Pane Clears
- **Setup**: A conversation is loaded in a pane
- **Action**: Hover that conversation's sidebar row, click Delete
- **Expected**: Conversation removed from sidebar. The pane that was showing it clears to empty state.
- **Pass**: Sidebar row gone, pane shows empty state
- **Fail**: Pane still shows deleted conversation
- **If Failed**: Check `handleDeleteConversation` in `DashboardPage.tsx`. Verify it matches pane `conversationId` and sets it to null.

### Test 6.6: FolderPlus Popover
- **Setup**: Conversation exists, not in select mode
- **Action**: Hover row, click FolderPlus button
- **Expected**: Inline popover opens with "Move to Folder" dropdown, "Attach Repository" selector, and "Done" button
- **Pass**: Popover opens with all elements
- **Fail**: Popover doesn't open or elements missing
- **If Failed**: Check popover state and `editingConvId` in sidebar.

### Test 6.7: FolderPlus -- Change Folder
- **Setup**: FolderPlus popover open, categories exist
- **Action**: Select a different category from the dropdown
- **Expected**: Conversation moves to the selected category group immediately
- **Pass**: Conversation relocated in sidebar
- **Fail**: Conversation stays in old group
- **If Failed**: Check `updateConversationMut.mutate` call with category.

### Test 6.8: FolderPlus -- Close on Done or Outside Click
- **Setup**: FolderPlus popover open
- **Action**: Click "Done" button, or click outside the popover
- **Expected**: Popover closes
- **Pass**: Popover closes
- **Fail**: Popover stays open
- **If Failed**: Check Done handler and `handleClickOutside` logic for `editPopoverRef`.

### Test 6.9: Select Mode Bulk Delete
- **Setup**: Multiple conversations exist
- **Action**: Enter select mode (CheckSquare), check several conversations, click "Delete (N)"
- **Expected**: All selected conversations are deleted. Any pane showing a deleted conversation clears.
- **Pass**: Selected conversations gone; affected panes cleared
- **Fail**: Some conversations remain, or panes not cleared
- **If Failed**: Check `handleBulkDelete`. Verify it calls `onDeleteConversation` for each deleted ID.

---

## Test Group 7: Conversation Badges

### Test 7.1: Claude Badge -- Display
- **Setup**: Claude conversation exists in sidebar
- **Action**: Look at the top-right corner of the row
- **Expected**: Small colored badge: "O.1M" (blue) for Opus 1M, "S.1M" (violet) for Sonnet 1M, or "O.200K" (zinc) for Opus 200K
- **Pass**: Badge visible with correct abbreviation (middle-dot separator) and color
- **Fail**: Badge missing or wrong format
- **If Failed**: Check badge rendering in conversation row.

### Test 7.2: Claude Badge -- Click to Cycle
- **Setup**: Claude conversation with badge visible
- **Action**: Click the badge three times
- **Expected**: Badge cycles: O.1M (blue) -> S.1M (violet) -> O.200K (zinc) -> O.1M (blue)
- **Pass**: Three clicks return to original; colors match each state
- **Fail**: Badge doesn't change, or wrong cycle order
- **If Failed**: Check `cycleNext` function and `cycleModelBadgeMut` mutation.

### Test 7.3: Claude Badge Click Does Not Select Conversation
- **Setup**: One conversation active in pane, another Claude conversation with badge
- **Action**: Click the badge on the non-active conversation
- **Expected**: Badge cycles, but active pane's conversation does NOT change
- **Pass**: Badge cycles, pane unchanged
- **Fail**: Clicking badge also selects the conversation
- **If Failed**: Check `e.stopPropagation()` on badge click handler.

### Test 7.4: Codex Badge -- Static Display
- **Setup**: Codex conversation exists (created in Test 4.16)
- **Action**: Observe the badge on the Codex conversation row
- **Expected**: Static emerald badge showing abbreviated model (e.g., "5.4", "5.4P", "o3"). Not clickable.
- **Pass**: Badge is static, emerald color, correct abbreviation
- **Fail**: Badge is clickable, or wrong color
- **If Failed**: Check `convProvider !== 'claude'` conditional in badge rendering.

### Test 7.5: Gemini Badge -- Static Display
- **Setup**: Gemini conversation exists (created in Test 4.17)
- **Action**: Observe the badge on the Gemini conversation row
- **Expected**: Static violet badge showing abbreviated model (e.g., "3.1P", "3.1F", "Lite"). Not clickable.
- **Pass**: Badge is static, violet color, correct abbreviation
- **Fail**: Badge is clickable, or wrong color
- **If Failed**: Same investigation as Test 7.4 for Gemini.

### Test 7.6: Badge Abbreviation Accuracy
- **Setup**: Multiple Codex and Gemini conversations with different models
- **Action**: Compare badge text against expected abbreviations
- **Expected**: The following model-to-badge mappings are correct:
  - Codex: `gpt-5.4` -> `5.4`, `gpt-5.4-pro` -> `5.4P`, `gpt-5.3` -> `5.3`, `o3` -> `o3`, `o4-mini` -> `o4m`, `gpt-5-codex` -> `5C`
  - Gemini: `gemini-3.1-pro` -> `3.1P`, `gemini-3.1-flash` -> `3.1F`, `gemini-3.1-flash-lite` -> `3.1L`, `pro` -> `Pro`, `flash` -> `Flsh`, `flash-lite` -> `Lite`
- **Pass**: All abbreviations match the `SHORT_MODEL` lookup table
- **Fail**: Any abbreviation mismatches
- **If Failed**: Check the `SHORT_MODEL` record in `WorkspaceSidebar.tsx`.

---

## Test Group 8: Pane Operations

### Test 8.1: Collapse a Pane
- **Setup**: Dual or triple layout, browser wider than 768px
- **Action**: Click the collapse button (ChevronsLeft or ChevronsRight) on a pane
- **Expected**: Pane collapses to a thin vertical bar (~40px, `w-10`). Bar shows the provider name in rotated uppercase text. Remaining pane(s) expand to fill the space. Bar has provider-tinted background.
- **Pass**: Pane collapses to labeled bar, other panes expand
- **Fail**: Pane disappears entirely, bar not visible, or other panes don't expand
- **If Failed**: Check `collapsed` state update via `updatePane`. Verify `CollapsedPaneBar` render.

### Test 8.2: Expand a Collapsed Pane
- **Setup**: A pane is collapsed (Test 8.1)
- **Action**: Click the collapsed pane bar
- **Expected**: Pane expands to normal width. Collapsed bar disappears.
- **Pass**: Pane restored to full width with chat content
- **Fail**: Pane stays collapsed
- **If Failed**: Check the `onClick` handler on `CollapsedPaneBar` that sets `collapsed: false`.

### Test 8.3: Collapsed Pane Bar Background Colors
- **Setup**: Collapse each provider's pane one at a time
- **Action**: Observe the collapsed bar's background color
- **Expected**:
  - Claude: `bg-blue-500/5` (very faint blue tint)
  - Codex: `bg-emerald-500/5` (very faint emerald tint)
  - Gemini: `bg-violet-500/5` (very faint violet tint)
- **Pass**: Correct tint per provider
- **Fail**: Wrong color or no tint
- **If Failed**: Check the `bg` variable in `CollapsedPaneBar` component.

### Test 8.4: Collapse Button Hidden in Single Layout
- **Setup**: Single pane layout
- **Action**: Look at the pane header
- **Expected**: No collapse button visible (because `panes.length === 1` and the collapse button renders only when `panes.length > 1`)
- **Pass**: No collapse button
- **Fail**: Collapse button visible in single layout
- **If Failed**: Check the `{panes.length > 1 && ...}` conditional.

### Test 8.5: Clear Pane Button
- **Setup**: A conversation is loaded in a pane
- **Action**: Click the X button in the pane header (next to the label)
- **Expected**: Pane clears to empty state. Conversation still exists in sidebar. The X button disappears (only shows when `conversationId` is not null).
- **Pass**: Pane clears, conversation in sidebar, X hidden
- **Fail**: Conversation deleted, or X still visible
- **If Failed**: Check `updatePane(pane.id, { conversationId: null })` handler.

### Test 8.6: Clear Pane Button Hidden When Empty
- **Setup**: Pane has no conversation (empty state)
- **Action**: Observe the pane header
- **Expected**: No X button visible
- **Pass**: X button absent
- **Fail**: X button visible on empty pane
- **If Failed**: Check `{pane.conversationId && ...}` conditional rendering.

### Test 8.7: Collapse Button Direction
- **Setup**: Triple layout, all panes expanded
- **Action**: Observe collapse buttons on each pane
- **Expected**: First pane: ChevronsLeft icon. Second pane: ChevronsLeft icon. Third (last) pane: ChevronsRight icon.
- **Pass**: Directional icons correct per position
- **Fail**: Wrong icon direction
- **If Failed**: Check `idx === panes.length - 1 ? <ChevronsRight> : <ChevronsLeft>` conditional.

### Test 8.8: Multiple Panes Collapsed
- **Setup**: Triple layout
- **Action**: Collapse pane 1, then collapse pane 2
- **Expected**: Two collapsed bars visible. Remaining pane 3 fills full width.
- **Pass**: Two bars + one full pane
- **Fail**: Bars overlap, or remaining pane doesn't expand
- **If Failed**: Check CSS flex layout handles multiple collapsed panes.

---

## Test Group 9: Chat Session in Pane

### Test 9.1: Send a Message
- **Setup**: A conversation loaded in a pane with a Claude/Codex/Gemini subscription
- **Action**: Click the text input at the bottom of the pane. Type "Hello from dashboard." Press Enter.
- **Expected**: User message appears in the pane. A "Thinking..." indicator shows. Send button shows spinner.
- **Pass**: User message displayed, loading indicator visible
- **Fail**: Message not displayed, no loading indicator
- **If Failed**: Check WebSocket connection in `WorkspaceChat`. Verify `panelLabel` and `provider` props are correct.

### Test 9.2: Response Streams Back
- **Setup**: Message sent (Test 9.1)
- **Action**: Wait for the assistant response
- **Expected**: Assistant message streams in progressively. When complete, full response displayed.
- **Pass**: Response streams and completes
- **Fail**: No response, or response appears all at once
- **If Failed**: Check WebSocket frames in DevTools. Verify backend chat session handler.

### Test 9.3: Streaming Indicator in Sidebar
- **Setup**: Message sent, response streaming
- **Action**: Observe the conversation's sidebar row
- **Expected**: Cyan pulsing glow bar + pulsing dot + shimmer sweep on the row
- **Pass**: Streaming indicators visible
- **Fail**: No indicators
- **If Failed**: Check `handlePaneStreamingChange` callback. Verify `streamingIds` prop reaches the sidebar.

### Test 9.4: Streaming in Multiple Panes Simultaneously
- **Setup**: Dual layout, conversations loaded in both panes
- **Action**: Send a message in pane 1. While streaming, quickly send a message in pane 2.
- **Expected**: Both panes stream independently. Sidebar shows streaming indicators for both conversation rows.
- **Pass**: Both panes stream, both sidebar rows have cyan indicators
- **Fail**: One pane blocks the other, or only one indicator shows
- **If Failed**: Check that `streamingIds` is a Set of all streaming IDs across panes.

### Test 9.5: Token Counter Updates
- **Setup**: A message sent and response received
- **Action**: Look at the compact control bar in the pane
- **Expected**: Context usage bar shows non-zero percentage. Message count reflects exchanges.
- **Pass**: Token percentage > 0, message count correct
- **Fail**: Stuck at 0%
- **If Failed**: Check token tracking in `WorkspaceChat.tsx`.

### Test 9.6: Text Input Disabled During Streaming
- **Setup**: Message sent, response streaming
- **Action**: Try to type in the input
- **Expected**: Input is disabled during streaming
- **Pass**: Input not editable
- **Fail**: Input remains editable
- **If Failed**: Check `disabled` prop tied to loading state.

### Test 9.7: Draft Persistence
- **Setup**: Conversation loaded in pane
- **Action**: Type "draft text" but do NOT send. Click a different conversation in the sidebar to load it in the pane. Click the original conversation to reload it.
- **Expected**: Draft text "draft text" is restored in the input
- **Pass**: Draft restored
- **Fail**: Input empty
- **If Failed**: Check localStorage draft save/restore keyed by conversation ID.

---

## Test Group 10: Category Management

### Test 10.1: Open Category Manager
- **Setup**: Sidebar visible
- **Action**: Click "Manage Categories" button at bottom of sidebar
- **Expected**: Category Manager modal opens
- **Pass**: Modal visible
- **Fail**: Nothing happens
- **If Failed**: Check `setShowCategoryManager(true)` handler.

### Test 10.2: Create Category
- **Setup**: Category Manager modal open
- **Action**: Type "Dashboard Testing" in the input, select a color, click "Add" (or press Enter)
- **Expected**: Category appears in the modal list with chosen color
- **Pass**: Category created with name and color
- **Fail**: Category not created
- **If Failed**: Check create category mutation.

### Test 10.3: Category Appears in Sidebar
- **Setup**: Category created (Test 10.2)
- **Action**: Close modal, observe sidebar
- **Expected**: Category appears as a group header when conversations are assigned to it
- **Pass**: Category group visible with correct name and color dot
- **Fail**: Category not showing
- **If Failed**: Check `categoryOrder` computed value and group rendering.

### Test 10.4: Delete Category
- **Setup**: Category Manager modal open, category exists
- **Action**: Click the trash icon on the category
- **Expected**: Category removed immediately (no confirmation)
- **Pass**: Category gone from list and sidebar
- **Fail**: Category remains
- **If Failed**: Check delete category mutation.

### Test 10.5: Close Category Manager
- **Setup**: Modal open
- **Action**: Click X or press Escape
- **Expected**: Modal closes
- **Pass**: Modal closed
- **Fail**: Modal stays open
- **If Failed**: Check close handler.

---

## Test Group 11: Session Persistence (localStorage)

### Test 11.1: Layout Mode Persists
- **Setup**: Set layout to triple
- **Action**: Reload page
- **Expected**: Triple layout restored
- **Pass**: Three panes on reload
- **Fail**: Reverts to dual
- **If Failed**: Check `localStorage.getItem('dashboard-layout')` in state initializer.

### Test 11.2: Pane Provider Persists
- **Setup**: Change second pane to Gemini
- **Action**: Reload page
- **Expected**: Second pane shows Gemini provider
- **Pass**: Gemini active in second pane
- **Fail**: Reverts to Codex
- **If Failed**: Check `localStorage.setItem('dashboard-panes', ...)` in the `useEffect`.

### Test 11.3: Pane Conversation ID Persists
- **Setup**: Load a conversation in a pane
- **Action**: Reload page
- **Expected**: Same conversation loaded in the same pane
- **Pass**: Conversation restored
- **Fail**: Pane is empty
- **If Failed**: Check that `conversationId` is included in the serialized pane state.

### Test 11.4: Pane Collapse State Persists
- **Setup**: Collapse a pane
- **Action**: Reload page
- **Expected**: Pane remains collapsed
- **Pass**: Collapsed bar visible after reload
- **Fail**: Pane expands on reload
- **If Failed**: Check that `collapsed` field is serialized in pane state.

### Test 11.5: Working Directory Persists
- **Setup**: Select a repo via RepoSelector
- **Action**: Reload page
- **Expected**: RepoSelector shows previously selected repo
- **Pass**: Repo name displayed
- **Fail**: "Select Repo" shown
- **If Failed**: Check `localStorage.getItem('dashboard-working-dir')`.

### Test 11.6: Clear localStorage Resets to Defaults
- **Setup**: Custom layout, providers, and conversations set
- **Action**: Clear localStorage (DevTools > Application > Storage > Clear), reload page
- **Expected**: Dashboard loads with defaults: dual layout, Claude + Codex panes, no conversations, no repo
- **Pass**: All defaults restored
- **Fail**: Errors or unexpected state
- **If Failed**: Check `try/catch` blocks in state initializers handle missing localStorage gracefully.

---

## Test Group 12: Mobile Responsive

### Test 12.1: Mobile Sidebar Overlay
- **Setup**: Resize browser to below 768px width
- **Action**: Click the Menu icon (hamburger) in the nav bar
- **Expected**: Sidebar appears as a fixed overlay (272px, z-50) with dark backdrop (black/40). Clicking backdrop closes sidebar.
- **Pass**: Overlay sidebar with backdrop; closes on backdrop click
- **Fail**: Sidebar doesn't appear, no backdrop, or doesn't close
- **If Failed**: Check `mobileSidebarOpen` state and the overlay/backdrop rendering.

### Test 12.2: Mobile -- Single Pane Visible
- **Setup**: Triple layout, browser below 768px
- **Action**: Observe the pane area
- **Expected**: Only the first non-collapsed pane is visible. Other panes hidden via `hidden md:flex`.
- **Pass**: Single pane visible
- **Fail**: Multiple tiny panes visible
- **If Failed**: Check the `idx > 0 ? 'hidden md:flex' : ''` class on pane containers.

### Test 12.3: Layout Buttons Hidden on Mobile
- **Setup**: Browser below 768px
- **Action**: Observe the nav bar
- **Expected**: Layout mode buttons (1/2/3) are not visible
- **Pass**: Buttons hidden
- **Fail**: Buttons visible on mobile
- **If Failed**: Check `hidden md:flex` class on the layout buttons container.

### Test 12.4: RepoSelector Hidden on Small Mobile
- **Setup**: Browser below 640px
- **Action**: Observe the nav bar
- **Expected**: RepoSelector is not visible (hidden below `sm` breakpoint)
- **Pass**: RepoSelector hidden
- **Fail**: Still visible
- **If Failed**: Check `hidden sm:block` class on the RepoSelector container.

### Test 12.5: AutoForge Text Hidden on Small Mobile
- **Setup**: Browser below 640px
- **Action**: Observe the back button area
- **Expected**: Only the ArrowLeft icon is visible; "AutoForge" text is hidden
- **Pass**: Arrow only, no text
- **Fail**: Text still visible
- **If Failed**: Check `hidden sm:inline` on the "AutoForge" span.

### Test 12.6: Sidebar Closes on Conversation Select (Mobile)
- **Setup**: Mobile sidebar overlay open (Test 12.1), conversations exist
- **Action**: Click a conversation row
- **Expected**: Sidebar drawer closes automatically. Conversation loads in the visible pane.
- **Pass**: Drawer closes, conversation loads
- **Fail**: Drawer stays open
- **If Failed**: Check `setMobileSidebarOpen(false)` in `handleSelectConversation`.

### Test 12.7: Collapsed Pane Bars Hidden on Mobile
- **Setup**: A pane is collapsed, browser below 768px
- **Action**: Observe the pane area
- **Expected**: No thin vertical collapsed bar visible (hidden via `hidden md:flex` on `CollapsedPaneBar` wrapper)
- **Pass**: No collapsed bar on mobile
- **Fail**: Bar visible on mobile
- **If Failed**: Check `className="hidden md:flex"` on the collapsed bar container.

### Test 12.8: Nav Bar Wraps on Narrow Screens
- **Setup**: Browser at ~600px width
- **Action**: Observe the nav bar
- **Expected**: Nav bar uses `flex-wrap` so items wrap to a second line if needed, rather than overflowing
- **Pass**: Items wrap gracefully, no horizontal overflow
- **Fail**: Items overflow or overlap
- **If Failed**: Check `flex flex-wrap` and `gap-y-1` classes on the nav bar.

---

## Test Group 13: Cross-Pane Interactions

### Test 13.1: Working Directory Shared Across Panes
- **Setup**: Dual layout, select a repo via nav bar RepoSelector
- **Action**: Load conversations in both panes, check if both have access to the repo
- **Expected**: Both panes receive the same `workingDirectory` prop. Git features (branch display, etc.) work in both.
- **Pass**: Both panes show same repo context
- **Fail**: Only one pane has repo access
- **If Failed**: Check that `workingDirectory` is passed to all pane `WorkspaceChat` instances.

### Test 13.2: New Chat Always Targets First Pane
- **Setup**: Dual layout, both panes have conversations loaded
- **Action**: Create a new conversation from the sidebar
- **Expected**: First pane's conversation is cleared and replaced with the new one. Second pane unchanged.
- **Pass**: New chat in first pane, second pane preserved
- **Fail**: New chat in second pane, or both panes affected
- **If Failed**: Check `handleNewChat` which targets `updated[0]`. Verify `pendingModel`/`newChatKey` only passed to pane index 0.

### Test 13.3: New Chat Updates First Pane Provider If Needed
- **Setup**: First pane is Claude. Switch sidebar to Gemini (by switching first pane provider). Create a new Gemini conversation.
- **Action**: Observe first pane
- **Expected**: First pane shows the new Gemini conversation with Gemini provider active
- **Pass**: Correct provider and conversation in first pane
- **Fail**: Provider mismatch
- **If Failed**: Check `handleNewChat` provider-sync logic.

### Test 13.4: Deleting a Conversation Clears All Panes Showing It
- **Setup**: Dual layout. Load the SAME conversation in both panes (by selecting it, then clearing pane 2, then selecting it again in pane 2 -- or loading it in pane 1 while pane 2 has a different one, then loading it in pane 2).
- **Action**: Delete the conversation from the sidebar
- **Expected**: Both panes clear to empty state
- **Pass**: Both panes show empty state
- **Fail**: One pane still shows the deleted conversation
- **If Failed**: Check `handleDeleteConversation` maps over ALL panes, not just the first.

### Test 13.5: Streaming State Isolated Per Pane
- **Setup**: Dual layout, different conversations in each pane
- **Action**: Send a message in pane 1 (triggers streaming). Observe pane 2.
- **Expected**: Pane 2 is unaffected. Only pane 1's conversation row shows streaming indicators.
- **Pass**: Only pane 1 streaming; pane 2 idle
- **Fail**: Both panes show as streaming, or pane 2's indicators appear
- **If Failed**: Check `handlePaneStreamingChange` uses pane-specific `conversationId`.

---

## Test Group 14: Navigation

### Test 14.1: Back to AutoForge
- **Setup**: On Dashboard page
- **Action**: Click the ArrowLeft + "AutoForge" button
- **Expected**: Navigates to the main AutoForge page (hash becomes empty)
- **Pass**: Main page loads
- **Fail**: Nothing happens or wrong page
- **If Failed**: Check `window.location.hash = ''` handler.

### Test 14.2: Navigate to Workspace
- **Setup**: On Dashboard page
- **Action**: Click the "Workspace" link on the right side of the nav bar
- **Expected**: Navigates to `/#/workspace`
- **Pass**: Workspace page loads
- **Fail**: Navigation doesn't happen
- **If Failed**: Check `window.location.hash = '#/workspace'` handler.

### Test 14.3: Direct URL Navigation
- **Setup**: On any page
- **Action**: Type `http://localhost:8888/#/dashboard` in the address bar and press Enter
- **Expected**: Dashboard page loads correctly
- **Pass**: Dashboard renders with all elements
- **Fail**: 404, blank page, or wrong page
- **If Failed**: Check route registration in `App.tsx`.

---

## Test Group 15: Error Handling

### Test 15.1: Conversation Creation Failure
- **Setup**: New Chat form open
- **Action**: Simulate a network error (disconnect server, or trigger API error) and click "Start Chat"
- **Expected**: Button shows "Creating...", then error is logged to console. Form closes and resets (per the `onError` handler in `handleCreateNamedChat`).
- **Pass**: No crash; form resets; error in console
- **Fail**: App crashes, infinite loading, or form stays open with "Creating..." forever
- **If Failed**: Check the `onError` callback in `createConversationMut.mutate`.

### Test 15.2: Invalid localStorage Graceful Fallback
- **Setup**: Set `dashboard-layout` to "invalid_value" in localStorage. Set `dashboard-panes` to "not-json".
- **Action**: Reload the page
- **Expected**: Page loads with defaults (dual layout, two panes) without errors
- **Pass**: Defaults restored, no console errors from state init
- **Fail**: Page crashes or shows unexpected layout
- **If Failed**: Check `try/catch` blocks in `useState` initializers.

### Test 15.3: RepoSelector Error States
- **Setup**: Dashboard page loaded, `gh` CLI not installed or not authenticated
- **Action**: Click the RepoSelector dropdown
- **Expected**: Error message appears in the dropdown (e.g., "gh CLI not installed" or "Failed to load repos")
- **Pass**: Error message displayed, no crash
- **Fail**: Infinite "Loading repositories..." or app crashes
- **If Failed**: Check error handling in `RepoSelector.tsx` for `fetchError` and `ghError`.

### Test 15.4: Provider Definition Fetch Failure
- **Setup**: Backend `/api/workspace/providers` endpoint returns error
- **Action**: Open New Chat form in sidebar
- **Expected**: Falls back to Claude model presets (hardcoded `CLAUDE_MODEL_PRESETS`). No crash.
- **Pass**: Claude presets shown as fallback
- **Fail**: Empty model pills or crash
- **If Failed**: Check fallback logic in `SIDEBAR_MODEL_PRESETS` useMemo: `if (!providers || !providers[activeProvider]) return CLAUDE_MODEL_PRESETS`.

### Test 15.5: WebSocket Disconnection in Pane
- **Setup**: Conversation loaded and connected in a pane
- **Action**: Stop the server while a conversation is active
- **Expected**: Disconnection banner appears in the pane with error message and "Retry" link. Connection indicator turns red.
- **Pass**: Banner visible with retry option
- **Fail**: No indication of disconnection
- **If Failed**: Check disconnection handling in `WorkspaceChat.tsx`.

---

## Test Group 16: Accessibility

### Test 16.1: Provider Selector ARIA Roles
- **Setup**: Any pane with provider selector
- **Action**: Inspect with accessibility tools or browser DevTools
- **Expected**: Container: `role="radiogroup"`, `aria-label="Provider selection"`. Each button: `role="radio"`, `aria-checked` matching active state.
- **Pass**: All ARIA attributes present and correct
- **Fail**: Missing or incorrect roles
- **If Failed**: Check `ProviderSelector` component JSX.

### Test 16.2: Model Preset ARIA Roles
- **Setup**: Sidebar New Chat form open
- **Action**: Inspect model pill strip
- **Expected**: Container: `role="radiogroup"`, `aria-label="Model selection"`. Each pill: `role="radio"`, `aria-checked`.
- **Pass**: ARIA attributes correct
- **Fail**: Missing roles
- **If Failed**: Check sidebar model pill rendering.

### Test 16.3: Effort Level ARIA Roles
- **Setup**: Claude provider, Opus 1M selected, effort selector active
- **Action**: Inspect effort pills
- **Expected**: Container: `role="radiogroup"`, `aria-label="Thinking effort level"`. Each pill: `role="radio"`, `aria-checked`, `disabled` when not Opus 1M.
- **Pass**: ARIA attributes correct
- **Fail**: Missing roles or wrong disabled state
- **If Failed**: Check effort selector JSX.

### Test 16.4: Conversation Row Keyboard Navigation
- **Setup**: Conversations exist in sidebar
- **Action**: Tab to a conversation row and press Enter or Space
- **Expected**: Conversation is selected (same as clicking)
- **Pass**: Keyboard activates row
- **Fail**: Nothing happens on Enter/Space
- **If Failed**: Check `onKeyDown` handler and `tabIndex={0}` on conversation rows.

### Test 16.5: Collapsed Pane Bar Title Attribute
- **Setup**: A pane is collapsed
- **Action**: Hover the collapsed bar
- **Expected**: Tooltip shows "Expand {label}" (e.g., "Expand Claude")
- **Pass**: Tooltip visible
- **Fail**: No tooltip
- **If Failed**: Check `title` prop on `CollapsedPaneBar` button.
