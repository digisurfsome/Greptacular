"""
Screen Command Agent — press Ctrl+Shift+X, it reads your screen, understands
what needs to happen, and keeps running commands until the task is done.

It's not a dumb command extractor — it reads the conversation context,
figures out the goal, runs commands, checks output, fixes errors, and
loops until the job is complete.

Usage:
    python screen_agent.py          # Start listening
    pythonw screen_agent.py         # Start hidden (no console window)

Hotkeys:
    Ctrl+Shift+X  — Go! Read screen and do the thing.
    Ctrl+Shift+S  — Stop current task
    Ctrl+Shift+Q  — Quit agent

Requires: pip install anthropic Pillow pynput
Requires: ANTHROPIC_API_KEY env var (~$0.02-0.05 per task)
"""

import base64
import io
import json
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
from pathlib import Path

try:
    from PIL import ImageGrab
except ImportError:
    print("ERROR: Run: pip install Pillow")
    sys.exit(1)

try:
    from pynput import keyboard
except ImportError:
    print("ERROR: Run: pip install pynput")
    sys.exit(1)

try:
    import anthropic
except ImportError:
    print("ERROR: Run: pip install anthropic")
    sys.exit(1)

# === CONFIG ===
MAX_LOOPS = 15  # Safety cap — won't run more than 15 rounds
COMMAND_TIMEOUT = 300  # 5 min per command
LOG_DIR = Path.home() / ".autoforge"
LOG_FILE = LOG_DIR / "screen_agent.log"

current_keys = set()
client = None
stop_flag = threading.Event()
busy = threading.Event()

SYSTEM_PROMPT = """\
You are an autonomous command execution agent on the user's Windows machine.
You are smart, resourceful, and you SOLVE PROBLEMS — you don't just run commands blindly.

The user pressed a hotkey and you're seeing their screen. Your job:
1. Read the screen — it shows a Claude Code conversation, terminal, or instructions
2. Understand the GOAL (deploy, install, build, fix error, git operations, etc.)
3. Figure out what commands to run to accomplish that goal
4. When things go wrong, FIGURE OUT THE FIX — don't give up

YOU ARE A PROBLEM SOLVER. Common situations you handle:
- Vim/editor pops up during git merge → use --no-edit flag, or echo | to pipe empty input
- Wrong path / "system cannot find the path" → try alternative paths, use dir to explore
- Merge conflicts → try git merge --abort then retry with strategy, or resolve
- Permission denied → try running as admin, or find alternative approach
- "not recognized" command → find the right tool, install if needed
- npm errors → try npm ci, delete node_modules, clear cache
- Port in use → find and kill the process using it
- Git "divergent branches" → use --no-edit --no-rebase or set pull strategy
- Process won't die → taskkill /f /t /pid
- Build fails → read the error, fix the issue, retry

ENVIRONMENT:
- Windows 10, Command Prompt (cmd.exe) — NOT PowerShell
- Use && to chain commands, use cd /d for drive changes
- The user's dev repo: "C:\\Users\\lober\\GitHub\\Greptacular - AutoForge Build\\Greptacular"
- The user's live install: C:\\Users\\lober\\Greptacular
- ALWAYS use --no-edit on git merge/pull to avoid Vim
- ALWAYS use cd /d for absolute paths

DEPLOY CHAIN (when you see deploy/update instructions):
1. cd /d "C:\\Users\\lober\\GitHub\\Greptacular - AutoForge Build\\Greptacular"
2. git fetch origin <branch> && git merge origin/<branch> --no-edit
3. cd ui && npm run build && cd ..
4. git push origin main
5. cd /d C:\\Users\\lober\\Greptacular && git pull origin main --no-edit
6. start "" "C:\\Users\\lober\\Greptacular\\start_ui.bat"

RESPOND WITH JSON ONLY:
{
  "goal": "short description of what you're trying to accomplish",
  "status": "running" or "done" or "error",
  "message": "what you're doing now (shown to user)",
  "commands": ["command1", "command2"],
  "done_reason": "only if status is done — explain what was accomplished"
}

If nothing to do: {"goal": "...", "status": "done", "commands": [], "done_reason": "..."}
"""

FOLLOWUP_PROMPT = """\
Command results:

{results}

Goal: {goal}

You are a problem-solving agent. Analyze the output carefully:

1. Did the commands succeed? Check exit codes and error messages.
2. If there were errors — FIGURE OUT THE WORKAROUND. Don't give up.
   - Path not found? → Try alternative paths, use dir/where to search
   - Merge conflict? → git merge --abort, try different strategy
   - Vim/editor opened? → Kill it, redo with --no-edit
   - Build error? → Read the error message, fix the specific issue
   - Permission denied? → Try alternative approach
   - "not recognized"? → Find the right command or install the tool
3. If everything succeeded, is the FULL goal done or are there more steps?

Think step by step about what went wrong and how to fix it.

RESPOND WITH JSON ONLY:
{{
  "goal": "{goal}",
  "status": "running" or "done" or "error",
  "message": "what's happening / what you're fixing",
  "commands": ["next commands"],
  "done_reason": "only if fully done"
}}
"""


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def take_screenshot() -> str:
    """Screenshot → base64 PNG (resized to save tokens)."""
    img = ImageGrab.grab()
    max_width = 1280
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


def ask_claude_with_screenshot(screenshot_b64: str) -> dict:
    """Send screenshot to Claude, get back action plan."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": screenshot_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Read my screen. What commands do I need to run? Do it for me.",
                    },
                ],
            }
        ],
    )
    text = response.content[0].text.strip()
    # Parse JSON (handle markdown code blocks)
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)


def ask_claude_followup(goal: str, results: str, include_screenshot: bool = False) -> dict:
    """Send command results to Claude, ask what's next. Optionally include fresh screenshot."""
    content = []

    if include_screenshot:
        # Take a fresh screenshot so Claude can see if Vim/editor/error dialog popped up
        try:
            fresh_shot = take_screenshot()
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": fresh_shot,
                },
            })
            content.append({
                "type": "text",
                "text": "Here's what the screen looks like now after running the commands.\n\n"
                        + FOLLOWUP_PROMPT.format(goal=goal, results=results),
            })
        except Exception:
            content.append({
                "type": "text",
                "text": FOLLOWUP_PROMPT.format(goal=goal, results=results),
            })
    else:
        content.append({
            "type": "text",
            "text": FOLLOWUP_PROMPT.format(goal=goal, results=results),
        })

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)


def run_command(cmd: str) -> str:
    """Run a single command and return output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += result.stderr
        if result.returncode != 0:
            output += f"\n[exit code {result.returncode}]"
        return output.strip() or "[no output]"
    except subprocess.TimeoutExpired:
        return "[TIMED OUT after 5 min]"
    except Exception as e:
        return f"[ERROR: {e}]"


class AgentWindow:
    """Floating status window that shows what the agent is doing."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Screen Agent")
        self.root.attributes("-topmost", True)
        self.root.geometry("750x550")
        self.root.configure(bg="#1a1a2e")
        self.root.protocol("WM_DELETE_WINDOW", self.on_stop)

        # Header
        self.header = tk.Label(
            self.root,
            text="Screen Agent — Working...",
            font=("Consolas", 13, "bold"),
            fg="#00ff88",
            bg="#1a1a2e",
        )
        self.header.pack(pady=(10, 0))

        # Goal
        self.goal_label = tk.Label(
            self.root,
            text="",
            font=("Consolas", 10),
            fg="#88aaff",
            bg="#1a1a2e",
            wraplength=700,
        )
        self.goal_label.pack(pady=(2, 5))

        # Output
        self.output = scrolledtext.ScrolledText(
            self.root,
            font=("Consolas", 10),
            bg="#0d0d1a",
            fg="#cccccc",
            insertbackground="#ffffff",
        )
        self.output.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.output.tag_configure("cmd", foreground="#00ff88", font=("Consolas", 10, "bold"))
        self.output.tag_configure("info", foreground="#88aaff")
        self.output.tag_configure("error", foreground="#ff4444")
        self.output.tag_configure("done", foreground="#00ff88", font=("Consolas", 11, "bold"))
        self.output.tag_configure("step", foreground="#ffaa00")

        # Stop button
        self.stop_btn = tk.Button(
            self.root,
            text="  Stop  ",
            font=("Consolas", 12, "bold"),
            bg="#cc3333",
            fg="#ffffff",
            command=self.on_stop,
        )
        self.stop_btn.pack(pady=10)

    def on_stop(self):
        stop_flag.set()
        self.header.config(text="Stopping...", fg="#ff8888")

    def append(self, text: str, tag: str = None):
        self.output.insert(tk.END, text + "\n", tag)
        self.output.see(tk.END)
        self.root.update()

    def set_goal(self, goal: str):
        self.goal_label.config(text=f"Goal: {goal}")
        self.root.update()

    def set_header(self, text: str, color: str = "#00ff88"):
        self.header.config(text=text, fg=color)
        self.root.update()

    def finish(self, message: str):
        self.set_header("Done!", "#00ff88")
        self.append(f"\n{'='*50}", "done")
        self.append(message, "done")
        self.append("='*50", "done")
        self.stop_btn.config(text="  Close  ", bg="#00cc66", command=self.root.destroy)


def agent_loop():
    """Main agent loop: screenshot → plan → execute → check → repeat."""
    stop_flag.clear()
    busy.set()

    win = AgentWindow()
    win.append("Taking screenshot...", "info")
    win.root.update()

    try:
        # Step 1: Screenshot and initial plan
        screenshot_b64 = take_screenshot()
        win.append("Analyzing screen with Claude...", "info")
        win.root.update()

        plan = ask_claude_with_screenshot(screenshot_b64)
        goal = plan.get("goal", "Unknown task")
        win.set_goal(goal)
        log(f"Goal: {goal}")

        if plan.get("status") == "done":
            win.finish(plan.get("done_reason", "Nothing to do."))
            win.root.mainloop()
            busy.clear()
            return

        # Agent loop
        loop_count = 0
        while loop_count < MAX_LOOPS and not stop_flag.is_set():
            loop_count += 1
            commands = plan.get("commands", [])
            message = plan.get("message", "")

            if message:
                win.append(f"\n[Step {loop_count}] {message}", "step")

            if not commands:
                if plan.get("status") == "done":
                    break
                win.append("No commands to run. Done.", "info")
                break

            # Run commands and collect output
            all_results = []
            for cmd in commands:
                if stop_flag.is_set():
                    break
                win.append(f"> {cmd}", "cmd")
                win.root.update()
                output = run_command(cmd)
                win.append(output)
                win.root.update()
                all_results.append(f"> {cmd}\n{output}")

            if stop_flag.is_set():
                win.append("\nStopped by user.", "error")
                break

            # Check if done
            if plan.get("status") == "done":
                break

            # Ask Claude: what next?
            # Include screenshot if any command failed (might be Vim, dialog, etc.)
            any_errors = any("[exit code" in r or "[ERROR" in r or "[TIMED OUT" in r for r in all_results)
            win.append("\nChecking results..." + (" (+ screenshot)" if any_errors else ""), "info")
            win.root.update()
            results_text = "\n\n".join(all_results)
            plan = ask_claude_followup(goal, results_text, include_screenshot=any_errors)

            if plan.get("status") == "done":
                break
            if plan.get("status") == "error":
                win.append(f"\nError: {plan.get('message', 'Unknown error')}", "error")
                break

        # Done
        done_reason = plan.get("done_reason", plan.get("message", "Task complete."))
        log(f"Finished: {done_reason}")
        win.finish(done_reason)

    except json.JSONDecodeError as e:
        win.append(f"\nClaude returned invalid JSON: {e}", "error")
        log(f"JSON error: {e}")
    except anthropic.AuthenticationError:
        win.append("\nBad API key! Set ANTHROPIC_API_KEY.", "error")
    except Exception as e:
        win.append(f"\nUnexpected error: {e}", "error")
        log(f"Error: {e}")

    try:
        win.root.mainloop()
    except Exception:
        pass
    busy.clear()


# === HOTKEY HANDLING ===

class KeyChar:
    def __init__(self, char):
        self.char = char

    def __eq__(self, other):
        if isinstance(other, KeyChar):
            return self.char == other.char
        if hasattr(other, "char"):
            return self.char == (other.char or "").lower()
        return False

    def __hash__(self):
        return hash(self.char)


keyboard.KeyChar = KeyChar
HOTKEY_RUN = {keyboard.Key.ctrl_l, keyboard.Key.shift, KeyChar("x")}
HOTKEY_STOP = {keyboard.Key.ctrl_l, keyboard.Key.shift, KeyChar("s")}
HOTKEY_QUIT = {keyboard.Key.ctrl_l, keyboard.Key.shift, KeyChar("q")}


def normalize_key(key):
    if isinstance(key, keyboard.Key):
        return key
    if hasattr(key, "char") and key.char:
        return KeyChar(key.char.lower())
    return key


def on_press(key):
    normalized = normalize_key(key)
    current_keys.add(normalized)

    if all(k in current_keys for k in HOTKEY_RUN):
        current_keys.clear()
        if busy.is_set():
            log("Already running a task. Press Ctrl+Shift+S to stop it first.")
            return
        log("Hotkey: Ctrl+Shift+X — Go!")
        threading.Thread(target=agent_loop, daemon=True).start()

    if all(k in current_keys for k in HOTKEY_STOP):
        current_keys.clear()
        log("Hotkey: Ctrl+Shift+S — Stopping...")
        stop_flag.set()

    if all(k in current_keys for k in HOTKEY_QUIT):
        log("Hotkey: Ctrl+Shift+Q — Quitting.")
        os._exit(0)


def on_release(key):
    normalized = normalize_key(key)
    current_keys.discard(normalized)
    current_keys.discard(key)


def main():
    global client

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("=" * 55)
        print("  Screen Agent needs an Anthropic API key.")
        print()
        print("  Set it:  set ANTHROPIC_API_KEY=sk-ant-...")
        print("  Get one: console.anthropic.com")
        print()
        print("  Cost: ~$0.02-0.05 per task (uses Sonnet)")
        print("=" * 55)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("=" * 55)
    print("  Screen Command Agent is running!")
    print()
    print("  Ctrl+Shift+X  →  Read screen & do the thing")
    print("  Ctrl+Shift+S  →  Stop current task")
    print("  Ctrl+Shift+Q  →  Quit")
    print()
    print("  It reads your screen, understands the goal,")
    print("  runs commands, and keeps going until done.")
    print("=" * 55)

    log("Screen Agent started.")

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


if __name__ == "__main__":
    main()
