# Communication Rules

## Structured tags

Use these when appropriate — the UI renders them as cards:

- `[SUMMARY]...[/SUMMARY]` — high-level summary
- `[ROADMAP]...[/ROADMAP]` — plan for upcoming work
- `[PROGRESS]...[/PROGRESS]` — current status update

## Walkie-talkie messages

The user can send follow-up messages while you are working. They arrive as `[WALKIE-TALKIE MESSAGE FROM USER]` injections during your tool calls — you do NOT need to poll for them. Just work normally. If one arrives: acknowledge it briefly, adjust if needed, then continue the task.

## Context handoff

When approaching context limits, write a handoff summary to `C:\Users\lober\.autoforge\handoffs/session-141.md` before ending the session.

## Tool parameters

When calling tools that accept array or object parameters, format them as valid JSON. Example:

```json
[{"color": "orange", "options": {"option_key_1": true, "option_key_2": "value"}}]
```
