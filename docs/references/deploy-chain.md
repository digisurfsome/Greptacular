# Deploy Chain

After every server or UI code change in the dev repo, run this sequence:

1. `cd ui && npm run build` (in dev repo)
2. `git push origin main`
3. `cd C:\Users\lober\Greptacular && git pull origin main --no-edit`
4. Kill running python processes, restart `start_ui.bat`
5. Ctrl+Shift+R in the browser to bust the cache

## Paths

- **Dev repo:** `c:\Users\lober\GitHub\Greptacular - AutoForge Build\Greptacular`
- **Live install:** `C:\Users\lober\Greptacular` (serves on port 8888)

## Rules

- Commit directly to `main`. No branches.
- `ui/dist/` is gitignored. `start_ui.bat` auto-rebuilds from source — source changes alone fix the UI.
- The user pulls from `main`. Never leave changes on a feature branch.
