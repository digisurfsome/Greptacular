# My Brain — Personal Knowledge File

This file is your Screen Agent's memory. It knows everything in here instantly
when you press Ctrl+Shift+X. Edit it anytime. The agent also adds new knowledge
automatically when it solves a problem for you.

---

## Who I Am

- Name: (your name)
- Machine: Windows 10
- Shell: Command Prompt (cmd.exe), NOT PowerShell
- I'm not a coder — explain things simply, just fix it

## My Setup

### AutoForge / Greptacular
- Dev repo: `C:\Users\lober\GitHub\Greptacular - AutoForge Build\Greptacular`
- Live install: `C:\Users\lober\Greptacular`
- UI runs on: http://localhost:8888
- Start server: `start_ui.bat` (in live install dir)
- Refresh UI: Ctrl+Shift+R in browser

### Deploy Chain (do this after code changes)
1. `cd /d "C:\Users\lober\GitHub\Greptacular - AutoForge Build\Greptacular"`
2. `git fetch origin <branch>`
3. `git merge origin/<branch> --no-edit`
4. `cd ui && npm run build && cd ..`
5. `git push origin main`
6. `cd /d C:\Users\lober\Greptacular`
7. `git pull origin main --no-edit`
8. Kill old server, restart `start_ui.bat`
9. Ctrl+Shift+R in browser

### Common Paths
- Home: `C:\Users\lober`
- GitHub repos: `C:\Users\lober\GitHub`
- AutoForge config: `C:\Users\lober\.autoforge`
- Node/npm: Should be in PATH
- Python: Should be in PATH
- Git: Should be in PATH

## Problems I Hit All the Time

### Vim opens during git merge
- ALWAYS use `--no-edit` flag
- If stuck in Vim: the agent should kill the process and retry with --no-edit
- Prevention: `git config --global core.editor "true"` (makes git use a no-op editor)

### "System cannot find the path specified"
- Usually means I cd'd to wrong directory
- Dev repo has spaces in path — MUST use quotes: `cd /d "C:\Users\lober\GitHub\Greptacular - AutoForge Build\Greptacular"`
- Use `cd /d` for absolute paths (handles drive changes)

### Git "couldn't find remote ref"
- Branch probably hasn't been pushed yet
- Or branch name is wrong — check with `git branch -r`

### npm run build fails
- Try `npm ci` first to clean install deps
- If node_modules is corrupt: `rmdir /s /q node_modules && npm ci`
- Check Node version: `node --version` (need 20+)

### Port 8888 already in use
- Find it: `netstat -ano | findstr :8888`
- Kill it: `taskkill /f /pid <PID>`

### Git merge conflicts
- Don't panic
- `git merge --abort` to undo
- Try `git checkout --theirs .` then `git add .` for simple cases
- Or just `git stash && git pull origin main --no-edit`

### Python "not recognized"
- Try `py` instead of `python`
- Or use full path: `C:\Users\lober\AppData\Local\Programs\Python\Python311\python.exe`

## My Preferences

- Don't explain — just do it
- If something breaks, fix it and move on
- Commit directly to main for speed
- I check timestamps in the UI to confirm changes worked
- I like things simple and fast

## Tools I Use

- Claude Code (AI coding agent)
- AutoForge (my AI coding platform)
- Git + GitHub
- Node.js + npm
- Python 3.11+
- VS Code (sometimes)
- Chrome browser

---

## Learned Solutions

<!-- The agent adds new solutions here automatically -->

