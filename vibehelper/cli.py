"""
VibeHelper CLI — entry point.

Usage:
    vibehelper              # Start the helper (runs in background)
    vibehelper --setup      # Run setup wizard
    vibehelper --brain      # Open your brain file in editor
    vibehelper --version    # Show version
"""

import os
import sys
import threading
from pathlib import Path

from pynput import keyboard

from vibehelper import __version__
from vibehelper.agent import (
    init_client, help_loop, busy, stop_flag, log, DATA_DIR, BRAIN_FILE
)
from vibehelper.setup_wizard import run_setup


# === HOTKEY HANDLING ===

current_keys = set()


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


HOTKEY_HELP = {keyboard.Key.ctrl_l, keyboard.Key.shift, KeyChar("x")}
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

    if all(k in current_keys for k in HOTKEY_HELP):
        current_keys.clear()
        if busy.is_set():
            log("Already helping! Press Ctrl+Shift+S to stop first.")
            return
        log("Help requested! (Ctrl+Shift+X)")
        threading.Thread(target=help_loop, daemon=True).start()

    if all(k in current_keys for k in HOTKEY_STOP):
        current_keys.clear()
        log("Stopping... (Ctrl+Shift+S)")
        stop_flag.set()

    if all(k in current_keys for k in HOTKEY_QUIT):
        log("Quitting. (Ctrl+Shift+Q)")
        os._exit(0)


def on_release(key):
    normalized = normalize_key(key)
    current_keys.discard(normalized)
    current_keys.discard(key)


def main():
    args = sys.argv[1:]

    if "--version" in args:
        print(f"VibeHelper v{__version__}")
        return

    if "--setup" in args:
        run_setup()
        return

    if "--brain" in args:
        if BRAIN_FILE.exists():
            if sys.platform == "win32":
                os.startfile(str(BRAIN_FILE))
            elif sys.platform == "darwin":
                os.system(f"open '{BRAIN_FILE}'")
            else:
                os.system(f"xdg-open '{BRAIN_FILE}'")
        else:
            print("No brain file yet. Run: vibehelper --setup")
        return

    # First run?
    if not DATA_DIR.exists() or not BRAIN_FILE.exists():
        print("First time? Let's get you set up!")
        print()
        run_setup()

    # Init API client
    if not init_client():
        print()
        print("No API key found!")
        print("  Option 1: set ANTHROPIC_API_KEY=sk-ant-your-key")
        print("  Option 2: vibehelper --setup")
        print()
        print("Get a key at: https://console.anthropic.com")
        sys.exit(1)

    # Start listening
    print()
    print("=" * 55)
    print()
    print("  VibeHelper is running!")
    print()
    print("  Ctrl+Shift+X  →  HELP! (read screen & fix it)")
    print("  Ctrl+Shift+S  →  Stop current task")
    print("  Ctrl+Shift+Q  →  Quit VibeHelper")
    print()
    print("  Just press Ctrl+Shift+X whenever you're stuck.")
    print("  I'll read your screen and handle it.")
    print()
    print("=" * 55)
    print()

    log("VibeHelper started. Waiting for Ctrl+Shift+X...")

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


if __name__ == "__main__":
    main()
