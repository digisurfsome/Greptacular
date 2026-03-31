# FIX: Typing Lag in WorkspaceChat (5-13 Second Freezes)

## Problem

When the user types in the input textarea while the agent is streaming responses or making tool calls, the UI freezes for 5-13 seconds between keystrokes. This happens because:

1. `WorkspaceChat.tsx` is a **2000-line single component**
2. Every WebSocket message (`text`, `tool_call`, `token_log`, `status`) calls `setMessages()` or `setTokenLog()`
3. Each state change triggers a **full re-render of the entire 2000-line component**
4. The input textarea is part of that component, so it re-renders too
5. The user's keystrokes get queued behind these re-renders → typing freezes

During active streaming, WebSocket messages arrive **dozens of times per second**. Each one triggers a re-render. The input textarea is trapped in this render cycle.

## Fix: Extract Input into React.memo Component

**Difficulty: 3/10 | Confidence: 95% | Risk: Very Low**

This is a pure refactor — no logic changes, just moving code into a separate component.

### Step 1: Create the Input Component

Create a new file: `ui/src/components/workspace/WorkspaceChatInput.tsx`

Extract the input area from `WorkspaceChat.tsx` (approximately lines 1840-1960) into this new component.

The component should:
- Accept these props (and ONLY these — minimizing re-render triggers):
  ```typescript
  interface WorkspaceChatInputProps {
    inputValue: string
    setInputValue: (value: string) => void
    onSend: () => void
    onKeyDown: (e: React.KeyboardEvent) => void
    onPaste: (e: React.ClipboardEvent) => void
    placeholder: string
    disabled: boolean
    isWalkieTalkieMode: boolean  // controls green styling
    isLoading: boolean
    firstMessageSent: boolean
    onEndSession: () => void
    onFileSelect: () => void
    onImageSelect: () => void
    onLibrarySelect: () => void
    hasAttachments: boolean  // show attachment preview area
    attachmentPreview?: React.ReactNode  // render attachment chips
    inputRef: React.RefObject<HTMLTextAreaElement>
  }
  ```
- Wrap with `React.memo()`:
  ```typescript
  export const WorkspaceChatInput = React.memo(function WorkspaceChatInput(props: WorkspaceChatInputProps) {
    // ... textarea, buttons, attachment preview
  })
  ```

### Step 2: Add Green Styling for Walkie-Talkie Mode

In the new component, make the textarea border/background change when `isWalkieTalkieMode` is true:

```typescript
className={`flex-1 resize-y min-h-[44px] max-h-[240px] rounded-md border px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:ring-1 disabled:cursor-not-allowed disabled:opacity-50 ${
  isWalkieTalkieMode
    ? 'border-emerald-500 ring-emerald-500/30 bg-emerald-500/5 placeholder:text-emerald-400/60'
    : 'border-border bg-input ring-ring'
}`}
```

Also make the send button green (not amber) in walkie-talkie mode:
```typescript
className={`... ${isWalkieTalkieMode ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-primary hover:bg-primary/90'}`}
```

### Step 3: Replace in WorkspaceChat.tsx

In `WorkspaceChat.tsx`, replace the inline textarea/buttons section (lines ~1840-1960) with:

```tsx
<WorkspaceChatInput
  inputValue={inputValue}
  setInputValue={setInputValue}
  onSend={handleSend}
  onKeyDown={handleKeyDown}
  onPaste={handlePaste}
  placeholder={isLoading && firstMessageSent ? "Type to send via walkie-talkie..." : "Ask anything... (paste images with Ctrl+V)"}
  disabled={isLoadingConversation || (isLoading && !firstMessageSent)}
  isWalkieTalkieMode={isLoading && firstMessageSent}
  isLoading={isLoading}
  firstMessageSent={firstMessageSent}
  onEndSession={handleEndSession}
  onFileSelect={() => fileInputRef.current?.click()}
  onImageSelect={() => imageInputRef.current?.click()}
  onLibrarySelect={() => setShowLibraryPicker(true)}
  hasAttachments={pendingAttachments.length > 0 || pendingImages.length > 0 || pendingLibraryFiles.length > 0}
  attachmentPreview={/* move the attachment chips JSX here */}
  inputRef={inputRef as React.RefObject<HTMLTextAreaElement>}
/>
```

### Step 4: Keep file inputs in parent

The `<input type="file">` elements (lines 1845-1867) should STAY in `WorkspaceChat.tsx` since they're hidden and only triggered by ref. Just the visible textarea and buttons move to the new component.

### Why This Works

`React.memo()` prevents re-rendering when props haven't changed. When a WebSocket `text` message arrives and calls `setMessages()`:
- `WorkspaceChat` re-renders (messages changed)
- `WorkspaceChatInput` does NOT re-render (none of its props changed — `inputValue`, `isLoading`, etc. are all the same)
- User's typing is unaffected

The input only re-renders when you actually type (changing `inputValue`) or when `isLoading` changes. That's it.

## BONUS FIX: Images/Files Dropped in Walkie-Talkie Mode

**Priority: HIGH — user reported this during live testing.**

When the user is in walkie-talkie mode (mid-conversation, agent is running), images pasted via Ctrl+V, files attached via the file button, and library files are ALL silently dropped. Only the text content is sent through the walkie-talkie path.

### What's Happening

In `WorkspaceChat.tsx`, the walkie-talkie send path (inside `handleSend`) only sends the text string via `sendWalkieTalkie(content)`. It completely bypasses the attachment processing logic (pending images, pending files, pending library files).

### How to Fix

When attachments are present in walkie-talkie mode, convert images to base64 data URLs and append them to the text content as markdown: `![image](data:image/png;base64,...)`. This way they travel through the existing text-only walkie-talkie channel. For files, append their content as code blocks. For library files, append the path reference.

In `WorkspaceChat.tsx`, in the walkie-talkie send path:

1. Before calling `sendWalkieTalkie(content)`, check for pending images/files
2. If images exist, convert each to base64 and append as markdown image tags
3. If files exist, append their content as code blocks
4. Send the combined text+attachments string via `sendWalkieTalkie()`
5. Clear the pending attachments after sending (same as normal path)

**IMPORTANT:** Look at how `pendingImages`, `pendingAttachments`, and `pendingLibraryFiles` are structured in the existing code. Match the actual data structures.

## Checklist

- [ ] Create `ui/src/components/workspace/WorkspaceChatInput.tsx`
- [ ] Extract textarea + send button + attachment buttons + end session button
- [ ] Wrap in `React.memo()`
- [ ] Add green border/background for walkie-talkie mode (`isWalkieTalkieMode` prop)
- [ ] Replace inline JSX in `WorkspaceChat.tsx` with `<WorkspaceChatInput />`
- [ ] Move attachment preview chips to the new component (or pass as `attachmentPreview` prop)
- [ ] Keep hidden `<input type="file">` elements in parent
- [ ] Fix walkie-talkie mode to include images/files/library attachments in the message
- [ ] Clear pending attachments after walkie-talkie send
- [ ] Test: type while agent is streaming — no lag
- [ ] Test: green styling appears when in walkie-talkie mode
- [ ] Test: all buttons still work (send, file, image, library, end session)
- [ ] Test: paste an image while in walkie-talkie mode — it should be sent with the message
- [ ] Run `npm run build` in `ui/` to verify no TypeScript errors
