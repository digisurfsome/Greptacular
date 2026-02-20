# Walkie-Talkie System: Test Script & User Manual

---

## Part 1: Quick Test Script

Covers every walkie-talkie feature in a single pass. ~5 minutes, minimal token cost.

**Prerequisites:**
- Server running (`autoforge` or `./start_ui.sh`)
- Workspace open in browser
- Working directory set (any folder works)

---

### A. Verify Settings UI

- [ ] **Click the gear icon** in the chat header bar (top-right area, small gear icon next to the connection status dots)
  - **Expected:** An amber-tinted settings panel drops down below the header with "Walkie-Talkie Settings" title
- [ ] **Verify three controls are visible:**
  - Check Frequency (3 buttons: Per Feature / Every Tool Call / Never)
  - Wait Timeout (4 buttons: 30s / 1m / 2m / 5m)
  - Auto-reply on timeout (toggle switch)
- [ ] **Set Check Frequency to "Every Tool Call"** — Most responsive for testing
- [ ] **Set Wait Timeout to "30s"** — Short timeout makes countdown easy to test
- [ ] **Confirm Auto-Reply is ON** — Toggle should be active
- [ ] **Close the panel** by clicking the X in the top-right of the settings panel, or click the gear icon again

---

### B. Verify Hidden When Idle

- [ ] **Look at chat panel with no agent running** (empty state or finished conversation)
  - **Expected:** No amber walkie-talkie bar visible. It only appears while agent is working.

---

### C. Start Agent & Test Live Messaging

- [ ] **Start a new conversation.** Send:
  ```
  Create a Python file called hello.py that prints "Hello World" 10 times.
  Then create goodbye.py that prints "Goodbye World".
  After creating both files, read them back and confirm they look correct.
  ```
- [ ] **Watch for amber walkie-talkie bar** to appear once agent starts tool calls
  - **Expected:** Amber bar with radio icon, input field ("Send message to working agent..."), Send button
- [ ] **Check header status indicator**
  - **Expected:** Pulsing amber dot with "Live" label in the top-right of chat header
- [ ] **Send a walkie-talkie message.** Type in amber bar:
  ```
  Add a comment at the top of each file with today's date
  ```
  Press Enter.
  - **Expected:**
    1. Input clears
    2. Brief "Sent!" confirmation with checkmark (~1.5s)
    3. Agent acknowledges your message in its response
    4. Agent adjusts work to include date comments

---

### D. Test Waiting State & Countdown Timer

- [ ] **Start a new conversation.** Send:
  ```
  I want you to create a config file. Before you do, ask me what format I prefer
  using the [WAITING] tag. Output exactly:
  [WAITING]What format would you like? JSON, YAML, or TOML?[/WAITING]
  ```
- [ ] **Watch for countdown timer bar**
  - **Expected:** Amber bar at top of chat with clock icon, "Agent waiting for response...", countdown from 0:30, "auto-reply" badge, "Keep Going" button, depleting progress bar
- [ ] **Check header changes**
  - **Expected:** Amber dot now says "Waiting" instead of "Live"
- [ ] **Check question display**
  - **Expected:** Amber strip shows "Agent asks: What format would you like? JSON, YAML, or TOML?"
- [ ] **Reply via walkie-talkie.** Type `YAML` and press Enter.
  - **Expected:** Countdown disappears, header reverts to "Live", agent proceeds with YAML

---

### E. Test Auto-Reply on Timeout

- [ ] **Start a new conversation.** Send:
  ```
  Ask me a question using [WAITING]Should I continue?[/WAITING] then wait for my response.
  ```
- [ ] **Do NOT reply.** Watch countdown from 0:30 to 0:00.
  - **Expected:** At 0:00 — bar shows "Time's up", system auto-sends "Continue with your best judgment", agent continues, countdown bar disappears

---

### F. Test "Keep Going" Button

- [ ] **Start a new conversation.** Same waiting-trigger as Step E.
- [ ] **Click "Keep Going" before timer expires**
  - **Expected:** System sends "Keep going, proceed with your best judgment", countdown clears, agent continues

---

### G. Test Disabling Walkie-Talkie

- [ ] **Click the gear icon** in the header → Set Check Frequency to **"Never"** → Close panel
- [ ] **Start a new conversation** with any task (e.g., "Create test.txt with 'hello'")
  - **Expected:** No amber bar appears, no "Live" indicator in header
- [ ] **Click the gear icon** again → Restore Check Frequency to "Every Tool Call" or "Per Feature"

---

### Checklist Summary

| Feature | Step |
|---------|------|
| Settings UI (3 controls) | A |
| Hidden when idle | B |
| Amber bar appears during work | C |
| Header "Live" indicator | C |
| Send message to working agent | C |
| "Sent!" confirmation | C |
| Agent acknowledges message | C |
| Countdown timer bar | D |
| Header "Waiting" indicator | D |
| Agent question display | D |
| Reply clears countdown | D |
| Auto-reply on timeout | E |
| "Keep Going" button | F |
| Disable via "Never" setting | G |

---

## Part 2: User Manual

### What is Walkie-Talkie?

Walkie-Talkie is a bidirectional communication channel between you and the workspace agent **while it is actively working**. Normally, once you send a message and the agent starts working, you have to wait for it to finish. Walkie-Talkie changes that.

With Walkie-Talkie enabled, you can:
1. **Send messages to the agent mid-task** — steer direction, add requirements, correct course
2. **Receive questions from the agent** — the agent can pause and ask you something, then wait for your response

Think of it like a walkie-talkie radio: either side can transmit at any time, but the agent keeps working between exchanges.

---

### How It Works

The system uses an in-memory message queue on the server:

1. You send a walkie-talkie message → it enters the queue
2. Before every tool call the agent makes, a `PreToolUse` hook checks the queue
3. If a message is waiting, the hook **blocks** the tool call and injects your message
4. The agent reads your message, acknowledges it, then re-attempts the tool call
5. Work continues

For agent-to-user questions, the agent outputs `[WAITING]...[/WAITING]` in its response. The UI shows a countdown timer. You respond (or auto-reply fires), and the agent continues.

---

### How to Enable or Disable

Click the **gear icon** (⚙) in the chat header bar (top-right area, next to the connection status indicator). A settings panel drops down:

| Setting | Options | Default | What it does |
|---------|---------|---------|-------------|
| **Check Frequency** | Per Feature / Every Tool Call / Never | Per Feature | How often agent checks for your messages |
| **Wait Timeout** | 30s / 1m / 2m / 5m | 2m | How long agent waits when it asks you a question |
| **Auto-Reply** | ON / OFF | ON | Auto-send "Continue with your best judgment" on timeout |

**"Never"** completely disables walkie-talkie — no amber bar, no checking, no overhead.

---

### Sending a Message While the Agent Works

When the agent is working, an amber bar appears above the main input:

```
[📻] | Send message to working agent... | [Send]
```

1. Type your message in the amber field
2. Press Enter or click Send
3. See brief "Sent!" confirmation
4. Agent reads it on the next tool call, acknowledges, and adjusts

You can send multiple messages — they batch together if the agent hasn't checked yet.

---

### When the Agent Asks You a Question

Sometimes the agent needs input. When this happens:

1. **Countdown timer** appears at top — shows remaining time, "auto-reply" badge, "Keep Going" button
2. **Question display** — amber strip: "Agent asks: [question]"
3. **Header** changes from "Live" to "Waiting"

**To respond:** Type answer in walkie-talkie bar, press Enter. Countdown clears.

**To skip:** Click "Keep Going" — sends "proceed with your best judgment."

**If you do nothing:** Timer expires. Auto-reply sends generic continue message (if enabled).

---

### Status Indicators

| Header Indicator | Meaning |
|-----------------|---------|
| No amber dot | Agent idle or walkie-talkie disabled |
| Pulsing amber dot + **"Live"** | Agent working, walkie-talkie available |
| Pulsing amber dot + **"Waiting"** | Agent asked a question, waiting for you |

---

### Tips & Gotchas

1. **Messages deliver on the next tool call**, not instantly. If the agent is thinking (no tool calls), your message waits in the queue — usually seconds, not minutes.

2. **The intercepted tool call is NOT executed.** The agent must re-attempt it after reading your message. This causes a brief but normal interruption.

3. **Multiple queued messages are batched** into a single delivery: "Message 1: ..., Message 2: ..."

4. **Walkie-talkie only works during active agent work.** The amber bar disappears when the agent finishes. Use the main input for normal conversation.

5. **Settings changes apply to the next session.** Change mid-conversation → start a new conversation for it to take effect.

6. **"Per Feature" vs "Every Tool Call"** — In workspace context these behave similarly since there's no feature concept. "Never" is the meaningful toggle.

7. **The amber bar ≠ the main input.** Main textarea = new conversation turns. Amber bar = inject into in-progress turn.

8. **Auto-reply sends a generic message** ("Continue with your best judgment"). If the agent asked something specific, it will make its own choice.

9. **"Keep Going" vs auto-reply** send slightly different text but achieve the same result.

10. **The `[WAITING]` tag is part of the system prompt.** The agent decides when to use it based on context. To test reliably, explicitly instruct the agent to use the tag.
