# Tool Efficiency Rules

> **MANDATORY.** Every agent must follow these rules. They reduce token usage by 30-50%.
> Read this at the start of every task. No exceptions.

---

## Rule 1: Read the Map Before Exploring

**BEFORE using Glob or Grep to find files, read the CLAUDE.md in the relevant directory:**
- UI task → Read `ui/CLAUDE.md`
- Server task → Read `server/CLAUDE.md`
- Docs task → Read `docs/CLAUDE.md`

These files tell you exactly where every file is. If the map answers your question, **do not search.**

---

## Rule 2: Stay in Your Lane

If your task is about **one specific page**, only touch files related to that page:
- The page file itself (e.g., `ui/src/pages/WorkspacePage.tsx`)
- Its component folder (e.g., `ui/src/components/workspace/`)
- Its hook (e.g., `ui/src/hooks/useWorkspaceChat.ts`)
- Its router (e.g., `server/routers/workspace.py`)
- Its service (e.g., `server/services/workspace_chat_session.py`)

**Do NOT:**
- Read other page files
- Explore directories unrelated to your task
- Read the entire `ui/src/components/` directory
- Read server services for pages you aren't working on

---

## Rule 3: Read Only What You Need

- **Files under 100 lines:** Read the whole thing.
- **Files over 100 lines:** Use `offset` and `limit` to read only the section you need.
- **Never read a 2000-line file fully** when you only need one function. Search for the function name first, then read that section.

---

## Rule 4: Maximum 3 Exploratory Searches

You get **3 exploratory tool calls** (Glob, Grep) to find what you need. If you haven't found it in 3 searches:
1. Re-read the relevant CLAUDE.md file map
2. If still not found, ask the human for the file location
3. Do NOT run 10+ searches hoping to stumble on it

---

## Rule 5: No Unnecessary Verification

- Do NOT `Read` a file after `Edit` just to verify the edit worked — the tool confirms success.
- Do NOT run `Glob` to check if a file exists when you already know the path.
- Do NOT run `Bash` commands to verify things the tools already confirmed.

---

## Rule 6: No Drive-By Improvements

**ONLY modify code directly related to your task.** Do NOT:
- Refactor code you encounter while working
- Add comments or docstrings to files you didn't change
- "Clean up" imports, formatting, or variable names in untouched files
- Fix unrelated bugs you notice

If you see something that needs fixing, note it in your response. Do not fix it.

---

## Rule 7: Batch Your Reads

If you need to read 3 files, read all 3 in a single turn (parallel tool calls). Do NOT:
- Read file 1, process it, read file 2, process it, read file 3
- This creates 3 turns instead of 1, tripling the context overhead

---

## Rule 8: Use the Right Tool

| Need | Use | NOT |
|------|-----|-----|
| Find a file by name | `Glob` | `Bash: find` |
| Find text in files | `Grep` | `Bash: grep` or `Bash: rg` |
| Read a file | `Read` | `Bash: cat` |
| Edit a file | `Edit` | `Bash: sed` |
| Create a file | `Write` | `Bash: echo >` |

The dedicated tools are cheaper (less output tokens) and more reliable.

---

## Rule 9: Token Budget Awareness

For a typical single-page task, your total tool usage should be roughly:
- **2-4 Read calls** (map file + the files you're changing)
- **1-3 Edit/Write calls** (the actual changes)
- **0-2 Glob/Grep calls** (only if the map didn't answer your question)
- **0-1 Bash calls** (only for running tests/builds if asked)

If you're exceeding **15 total tool calls** for a single-page task, you're being inefficient. Stop and reassess.

---

## Quick Decision Tree

```
Need to find a file?
  → Did you read the CLAUDE.md map? 
    → Yes, and it told me the path → Read that file directly
    → Yes, but file not listed → 1 Glob search, then done
    → No → Read the CLAUDE.md map FIRST

Need to understand code?
  → Is it in a file you already read? → Re-read your notes, don't re-read the file
  → Is it a new file? → Read only the relevant section (offset/limit)

About to modify code?
  → Is this file related to my task? → Yes → Edit it
  → No → STOP. Do not touch it.
```
