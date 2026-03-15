# My Brain — VibeHelper Personal Knowledge File

This is your AI assistant's memory. It knows everything in here.
Edit it anytime to teach it about YOUR machine and YOUR projects.
It also learns automatically — when it solves a new problem, it writes the fix here.

---

## About Me

- OS: (auto-detected on first run)
- Shell: (auto-detected)
- I'm learning to code with AI — keep it simple, just fix things

## My Projects

<!-- VibeHelper auto-fills this on first run -->
<!-- Add your projects manually too: -->
<!-- - Project name: C:\path\to\project -->

## Common Problems & Fixes

### Git

**Vim opens and I'm stuck**
- Prevention: Run `git config --global core.editor "true"` once
- Escape: Press Esc, type `:q!`, press Enter
- Better: Always use `--no-edit` flag on merge/pull
- Fix command: `taskkill /f /im vim.exe 2>nul & git merge --abort`

**"fatal: not a git repository"**
- You're in the wrong directory — cd to your project folder first
- Check: `dir .git` should show the git folder

**"couldn't find remote ref"**
- Branch name is wrong or hasn't been pushed
- Check available branches: `git branch -r`
- Maybe try: `git fetch --all`

**"divergent branches" / "need to specify how to reconcile"**
- Run: `git config --global pull.rebase false`
- Then retry your pull with `--no-edit`

**Merge conflicts**
- Simple fix: `git merge --abort` then `git pull origin main --no-edit`
- Nuclear option: `git stash && git checkout main && git pull origin main --no-edit`

**"Permission denied (publickey)"**
- SSH key not set up — use HTTPS instead
- Change remote: `git remote set-url origin https://github.com/USER/REPO.git`

### npm / Node.js

**"npm is not recognized"**
- Node.js isn't installed or not in PATH
- Download from: https://nodejs.org (get LTS version)
- After install, close and reopen terminal

**"EACCES permission denied"**
- On Mac/Linux: Don't use sudo! Fix npm permissions instead
- Run: `mkdir ~/.npm-global && npm config set prefix '~/.npm-global'`

**"npm ERR! code ERESOLVE" (dependency conflicts)**
- Try: `npm install --legacy-peer-deps`
- Or: `npm install --force`

**"Module not found" after npm install**
- Delete and reinstall: `rmdir /s /q node_modules && npm install` (Windows)
- Or: `rm -rf node_modules && npm install` (Mac/Linux)

**"ENOENT: no such file or directory, open 'package.json'"**
- You're in the wrong directory — cd to where package.json is
- Check: `dir package.json` (Windows) or `ls package.json` (Mac/Linux)

**Build fails with TypeScript errors**
- Often just type warnings — try `npm run build -- --skipLibCheck`
- Or check the specific error and fix the file mentioned

### Python

**"python is not recognized"**
- Windows: Try `py` instead of `python`
- Or `python3` on Mac/Linux
- Install from: https://python.org (check "Add to PATH" during install!)

**"pip is not recognized"**
- Try: `python -m pip install ...` instead of `pip install ...`
- Or: `py -m pip install ...` (Windows)

**"No module named ..."**
- Install it: `pip install module-name`
- If in a venv: make sure it's activated first

**Virtual environment confusion**
- Create: `python -m venv venv`
- Activate Windows: `venv\Scripts\activate`
- Activate Mac/Linux: `source venv/bin/activate`
- You'll see `(venv)` in your prompt when it's active

### Terminal / Command Line

**"The system cannot find the path specified"**
- Path doesn't exist or has typo
- Paths with spaces MUST use quotes: `cd "My Folder Name"`
- Use `cd /d` on Windows for absolute paths (handles drive changes)

**"Access is denied"**
- Another program has the file open
- Or you need admin — right-click terminal → Run as administrator

**Port already in use**
- Windows: `netstat -ano | findstr :PORT` then `taskkill /f /pid PID`
- Mac/Linux: `lsof -i :PORT` then `kill -9 PID`

**Process won't stop / terminal frozen**
- Windows: `taskkill /f /im process.exe`
- Mac/Linux: `kill -9 PID`
- Or just close the terminal and open a new one

### VS Code

**Terminal says wrong directory**
- Open terminal in VS Code: Ctrl+` (backtick)
- It opens in the workspace root — cd to where you need to be

**Extensions not working**
- Reload window: Ctrl+Shift+P → "Reload Window"

### Claude Code Specific

**Claude says to run commands but I don't know where**
- Open a terminal (Command Prompt on Windows, Terminal on Mac)
- cd to your project directory first
- Then paste the commands one at a time

**"claude: command not found"**
- Install: `npm install -g @anthropic-ai/claude-code`
- May need to restart terminal after installing

**Claude made changes but nothing happened**
- Might need to: restart the dev server, rebuild, or refresh browser
- Check if there's a build step: `npm run build` or `npm run dev`

## My Preferences

- Don't explain things I didn't ask about — just fix it
- If something breaks, try the fix before asking me
- Keep commands simple — one thing at a time for beginners

---

## Learned Solutions

<!-- VibeHelper adds new solutions here automatically as it helps you -->

