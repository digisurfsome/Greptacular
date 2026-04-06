# Emergency: UI Broken? Run This

If the UI is showing weird panels, stuck spinners, or anything that shouldn't be there:

```cmd
cd C:\Users\lober\Greptacular
git stash
git checkout main
git pull origin main
rmdir /s /q ui\dist
start_ui.bat
```

Then **Ctrl+Shift+R** in browser.
