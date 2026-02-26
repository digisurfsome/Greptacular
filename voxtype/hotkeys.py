"""Global hotkey registration for VoxType.

Registers system-wide keyboard shortcuts that work regardless
of which application is focused.
"""

import logging
from collections.abc import Callable

import keyboard

logger = logging.getLogger("voxtype.hotkeys")


class HotkeyManager:
    def __init__(self):
        self._registered: list[str] = []

    def register(self, hotkey: str, callback: Callable[[], None], description: str = "") -> None:
        """Register a global hotkey.

        Args:
            hotkey: Key combination string, e.g. "ctrl+shift+space"
            callback: Function to call when hotkey is pressed
            description: Human-readable description for logging
        """
        if not hotkey:
            return

        try:
            keyboard.add_hotkey(hotkey, callback, suppress=False)
            self._registered.append(hotkey)
            logger.info(f"Registered hotkey: {hotkey} ({description})")
        except Exception:
            logger.exception(f"Failed to register hotkey: {hotkey}")

    def unregister_all(self) -> None:
        """Unregister all hotkeys."""
        for hotkey in self._registered:
            try:
                keyboard.remove_hotkey(hotkey)
            except (KeyError, ValueError):
                pass
        self._registered.clear()
        logger.info("All hotkeys unregistered")
