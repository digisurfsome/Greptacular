# Chat Finder Skill — Install Instructions

The chat-finder skill you created earlier pointed Claude at the wrong place
(`.claude\projects` jsonl files — those are Claude Code's own session logs).
AutoForge workspace chats actually live in a SQLite database at
`C:\Users\lober\.autoforge\workspace.db`. This corrected skill points at the
right place and uses the new search script.

## How to install (one copy-paste)

1. Open File Explorer, paste this in the address bar:
   `C:\Users\lober\.claude\skills\chat-finder`
2. Open `SKILL.md` in Notepad (it already exists from last time).
3. Select everything (Ctrl+A), delete it, and paste in the block below
   (everything between the START and END markers — do NOT include the
   markers themselves).
4. Save and close.

---- START — copy from the next line ----

---
name: chat-finder
description: Find an old AutoForge workspace chat from a vague description. Use when the user says "chat finder", "find that chat/conversation", or describes a past conversation they want to locate (keywords, topic, rough timeframe).
---

# Chat Finder

AutoForge workspace chats are stored in SQLite at
`C:\Users\lober\.autoforge\workspace.db`. Search and read them with:

`python "C:\Users\lober\Greptacular\server\scripts\chat_finder.py" <command>`

(If that path doesn't exist, try the dev repo:
`C:\Users\lober\GitHub\Greptacular - AutoForge Build\Greptacular\server\scripts\chat_finder.py`)

The script is read-only — it can never modify chats.

## Commands

- `search "keywords"` — searches every chat title AND every message. Shows
  chat id, title, folder, how long ago, and matching snippets.
- `read <id>` — prints the full conversation so you can read through it.
- `list --days 14` — recent chats, useful when the user only remembers
  "sometime last week".

## Workflow (do this every time)

1. From the user's description, pick 3–5 keyword variations — including
   synonyms (e.g. "deploy", "deployment", "push live", "pipeline").
2. Run `search` for each variation. Collect the hits (typically 3–7 chats).
3. `read` each promising hit and judge whether it matches what the user
   described (topic + rough timeframe).
4. Report back in plain language:
   - Chat title and folder
   - How many days ago it was active
   - A short quote of the relevant part proving it's the right chat
5. If nothing matches, say so and suggest 2–3 different keywords to try —
   don't silently give up.

The user is not a coder. Never show raw SQL or stack traces; translate
everything into plain language.

---- END — stop copying at the previous line ----
