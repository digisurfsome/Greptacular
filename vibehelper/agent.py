"""
VibeHelper Agent — the core brain that reads screens, understands goals,
runs commands, fixes problems, and learns.

This is the engine. vibehelper/cli.py is the entry point.
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

from PIL import ImageGrab
import anthropic

# === CONFIG ===
MAX_LOOPS = 15
COMMAND_TIMEOUT = 300
DATA_DIR = Path.home() / ".vibehelper"
LOG_FILE = DATA_DIR / "vibehelper.log"
BRAIN_FILE = DATA_DIR / "my_brain.md"
CONFIG_FILE = DATA_DIR / "config.json"

client = None
stop_flag = threading.Event()
busy = threading.Event()


SYSTEM_PROMPT_TEMPLATE = """\
You are VibeHelper — a friendly AI sidekick for people learning to code with AI.
You run on the user's machine, watch their screen, and jump in to help when they're stuck.

Think of yourself as their tech-savvy friend sitting next to them. They pressed a hotkey
because they're stuck. Read their screen, figure out what's wrong, and fix it.

## WHAT YOU KNOW ABOUT THIS USER

{brain}

## YOUR PERSONALITY

- You're patient — they're learning
- You're fast — don't overthink, just fix it
- You're resourceful — when something fails, try a different way
- You explain ONLY if they need to do something manually (like refresh browser)
- You never judge — everyone was a beginner once

## HOW YOU WORK

1. Read the screen — probably shows Claude Code, a terminal, VS Code, or a browser
2. Understand what they're TRYING to do (not just the last error)
3. Run commands to fix it / continue the task
4. If a command fails — figure out why and try a workaround
5. Keep going until the task is done
6. If you learn a new trick, report it so I remember next time

## PROBLEM-SOLVING PLAYBOOK

You NEVER give up on the first error. Common fixes:

**Path issues:** Search for the right path, try quotes, use cd /d (Windows)
**Git hell:** Always --no-edit, abort and retry on conflicts, fetch before merge
**Vim trap:** Kill it (taskkill/kill), redo with --no-edit
**npm broken:** Delete node_modules, npm ci, try --legacy-peer-deps
**Python missing:** Try py/python3, check venv is activated
**Build fails:** Read the ACTUAL error line, not the wall of text
**Port in use:** Find PID, kill it
**Permission denied:** Try different approach, or find who has the file open
**"not recognized":** Tool not installed or not in PATH — install it or find it

## PLATFORM DETECTION

Detect the OS from the screenshot (Windows CMD, Mac Terminal, Linux, VS Code terminal).
Use the right commands for that platform:
- Windows: cmd.exe syntax, backslashes, cd /d, taskkill, rmdir /s /q
- Mac/Linux: bash/zsh, forward slashes, kill, rm -rf

## RESPONSE FORMAT

RESPOND WITH JSON ONLY:
{{
  "goal": "what you're trying to accomplish",
  "status": "running" or "done" or "error",
  "message": "friendly status update for the user",
  "commands": ["command1", "command2"],
  "done_reason": "only when fully done — what was accomplished",
  "learned": "only if you solved a new problem — describe it so I remember",
  "user_action": "only if user needs to do something manually (like refresh browser)"
}}
"""

FOLLOWUP_PROMPT = """\
Here's what happened when I ran the commands:

{results}

Goal: {goal}

Did it work? What's next?
- If errors: figure out the fix, don't give up
- If success: is the whole goal done, or more steps?
- If stuck: take a different approach

JSON ONLY:
{{
  "goal": "{goal}",
  "status": "running" or "done" or "error",
  "message": "what's happening",
  "commands": ["next commands if needed"],
  "done_reason": "only if fully done",
  "learned": "only if new problem solved",
  "user_action": "only if user needs to do something"
}}
"""


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_brain() -> str:
    if BRAIN_FILE.exists():
        return BRAIN_FILE.read_text(encoding="utf-8")
    return "(No brain file found. Run `vibehelper --setup` to create one.)"


def save_learned(problem: str, solution: str):
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n### [{ts}] {problem}\n{solution}\n"
        with open(BRAIN_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
        log(f"Learned: {problem}")
    except Exception as e:
        log(f"Failed to save: {e}")


def get_api_key() -> str:
    # Check env first
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    # Check config file
    if CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return config.get("api_key", "")
        except Exception:
            pass
    return ""


def take_screenshot() -> str:
    img = ImageGrab.grab()
    max_width = 1280
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


def ask_claude_screenshot(screenshot_b64: str) -> dict:
    system = SYSTEM_PROMPT_TEMPLATE.format(brain=load_brain())
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=system,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b64}},
                {"type": "text", "text": "I'm stuck. Read my screen and help me out."},
            ],
        }],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)


def ask_claude_followup(goal: str, results: str, include_screenshot: bool = False) -> dict:
    system = SYSTEM_PROMPT_TEMPLATE.format(brain=load_brain())
    content = []

    if include_screenshot:
        try:
            shot = take_screenshot()
            content.append({"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": shot}})
            content.append({"type": "text", "text": "Screen after commands:\n\n" + FOLLOWUP_PROMPT.format(goal=goal, results=results)})
        except Exception:
            content.append({"type": "text", "text": FOLLOWUP_PROMPT.format(goal=goal, results=results)})
    else:
        content.append({"type": "text", "text": FOLLOWUP_PROMPT.format(goal=goal, results=results)})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": content}],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)


def run_command(cmd: str) -> str:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=COMMAND_TIMEOUT)
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += result.stderr
        if result.returncode != 0:
            output += f"\n[exit code {result.returncode}]"
        return output.strip() or "[no output]"
    except subprocess.TimeoutExpired:
        return "[TIMED OUT]"
    except Exception as e:
        return f"[ERROR: {e}]"


class HelpWindow:
    """Friendly floating window showing what VibeHelper is doing."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VibeHelper")
        self.root.attributes("-topmost", True)
        self.root.geometry("720x520")
        self.root.configure(bg="#0f172a")

        # Header with emoji
        self.header = tk.Label(
            self.root, text="VibeHelper — On it!",
            font=("Segoe UI", 14, "bold"), fg="#38bdf8", bg="#0f172a",
        )
        self.header.pack(pady=(12, 0))

        # Status / goal
        self.status = tk.Label(
            self.root, text="Reading your screen...",
            font=("Segoe UI", 10), fg="#94a3b8", bg="#0f172a", wraplength=680,
        )
        self.status.pack(pady=(2, 8))

        # Output log
        self.output = scrolledtext.ScrolledText(
            self.root, font=("Consolas", 10), bg="#1e293b", fg="#e2e8f0",
            insertbackground="#e2e8f0", relief="flat", borderwidth=0,
        )
        self.output.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))
        self.output.tag_configure("cmd", foreground="#4ade80", font=("Consolas", 10, "bold"))
        self.output.tag_configure("info", foreground="#38bdf8")
        self.output.tag_configure("error", foreground="#f87171")
        self.output.tag_configure("done", foreground="#4ade80", font=("Segoe UI", 11, "bold"))
        self.output.tag_configure("step", foreground="#fbbf24")
        self.output.tag_configure("action", foreground="#c084fc", font=("Segoe UI", 10, "bold"))

        # Bottom bar
        bottom = tk.Frame(self.root, bg="#0f172a")
        bottom.pack(fill=tk.X, padx=12, pady=(0, 12))

        self.stop_btn = tk.Button(
            bottom, text="Stop", font=("Segoe UI", 11, "bold"),
            bg="#ef4444", fg="#ffffff", relief="flat", padx=20, pady=4,
            command=self.on_stop,
        )
        self.stop_btn.pack(side=tk.RIGHT)

        self.cost_label = tk.Label(
            bottom, text="", font=("Segoe UI", 9), fg="#64748b", bg="#0f172a",
        )
        self.cost_label.pack(side=tk.LEFT)

    def on_stop(self):
        stop_flag.set()
        self.header.config(text="Stopping...", fg="#f87171")

    def append(self, text: str, tag: str = None):
        self.output.insert(tk.END, text + "\n", tag)
        self.output.see(tk.END)
        self.root.update()

    def set_status(self, text: str):
        self.status.config(text=text)
        self.root.update()

    def set_header(self, text: str, color: str = "#38bdf8"):
        self.header.config(text=text, fg=color)
        self.root.update()

    def finish(self, message: str, user_action: str = None):
        self.set_header("Done!", "#4ade80")
        self.append(f"\n{'='*50}", "done")
        self.append(message, "done")
        if user_action:
            self.append(f"\nYou need to: {user_action}", "action")
        self.append("=" * 50, "done")
        self.stop_btn.config(text="Close", bg="#22c55e", command=self.root.destroy)


def help_loop():
    """Main agent loop."""
    stop_flag.clear()
    busy.set()

    win = HelpWindow()
    win.root.update()

    try:
        screenshot_b64 = take_screenshot()
        win.append("Analyzing your screen...", "info")
        win.root.update()

        plan = ask_claude_screenshot(screenshot_b64)
        goal = plan.get("goal", "Help with task")
        win.set_status(f"Goal: {goal}")
        log(f"Goal: {goal}")

        if plan.get("status") == "done":
            win.finish(
                plan.get("done_reason", "Nothing to do!"),
                plan.get("user_action"),
            )
            win.root.mainloop()
            busy.clear()
            return

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
                win.append("Nothing more to run.", "info")
                break

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
                win.append("\nStopped.", "error")
                break

            # Save learnings
            learned = plan.get("learned")
            if learned:
                save_learned(goal, learned)
                win.append(f"Remembered for next time: {learned}", "info")

            if plan.get("status") == "done":
                break

            # Check results with Claude
            any_errors = any("[exit code" in r or "[ERROR" in r or "[TIMED OUT" in r for r in all_results)
            win.append("\nChecking..." + (" (taking screenshot)" if any_errors else ""), "info")
            win.root.update()

            results_text = "\n\n".join(all_results)
            plan = ask_claude_followup(goal, results_text, include_screenshot=any_errors)

            learned = plan.get("learned")
            if learned:
                save_learned(goal, learned)

            if plan.get("status") in ("done", "error"):
                break

        # Finish
        done_reason = plan.get("done_reason", plan.get("message", "Task complete."))
        user_action = plan.get("user_action")
        log(f"Done: {done_reason}")
        win.finish(done_reason, user_action)

    except json.JSONDecodeError as e:
        win.append(f"\nBad response from Claude: {e}", "error")
    except anthropic.AuthenticationError:
        win.append("\nBad API key! Run: vibehelper --setup", "error")
    except Exception as e:
        win.append(f"\nError: {e}", "error")
        log(f"Error: {e}")

    try:
        win.root.mainloop()
    except Exception:
        pass
    busy.clear()


def init_client():
    """Initialize the API client."""
    global client
    api_key = get_api_key()
    if not api_key:
        return False
    client = anthropic.Anthropic(api_key=api_key)
    return True
