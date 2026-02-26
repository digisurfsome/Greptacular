"""System tray icon for VoxType.

Provides:
  - Left-click: toggle listening on/off
  - Right-click menu: pause, settings, quit
  - Icon color indicates state: green=listening, yellow=paused, gray=off
"""

import logging
import threading
from collections.abc import Callable

from PIL import Image, ImageDraw

logger = logging.getLogger("voxtype.tray")

# Icon size
ICON_SIZE = 64


def _create_icon(color: str, has_dot: bool = False) -> Image.Image:
    """Create a simple microphone-style tray icon."""
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Mic body (rounded rectangle approximated with ellipse + rect)
    mic_color = color
    cx, cy = ICON_SIZE // 2, ICON_SIZE // 2 - 6

    # Mic head (circle)
    r = 14
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=mic_color)

    # Mic body (rectangle below head)
    body_h = 12
    draw.rectangle([cx - r, cy, cx + r, cy + body_h], fill=mic_color)

    # Mic base (arc)
    base_y = cy + body_h + 2
    draw.arc([cx - r - 4, cy - 2, cx + r + 4, base_y + 10], start=0, end=180, fill=mic_color, width=3)

    # Stand
    stand_top = base_y + 8
    draw.line([cx, stand_top, cx, stand_top + 8], fill=mic_color, width=3)
    draw.line([cx - 8, stand_top + 8, cx + 8, stand_top + 8], fill=mic_color, width=3)

    # Recording dot
    if has_dot:
        dot_r = 6
        draw.ellipse(
            [ICON_SIZE - dot_r * 2 - 2, 2, ICON_SIZE - 2, dot_r * 2 + 2],
            fill="#FF3333",
        )

    return img


# Pre-generate icons for each state
ICON_ACTIVE = _create_icon("#22C55E", has_dot=True)   # green + red recording dot
ICON_PAUSED = _create_icon("#EAB308", has_dot=False)   # yellow
ICON_INACTIVE = _create_icon("#6B7280", has_dot=False)  # gray


class TrayIcon:
    def __init__(
        self,
        on_toggle: Callable[[], None],
        on_pause: Callable[[], None],
        on_quit: Callable[[], None],
    ):
        self._on_toggle = on_toggle
        self._on_pause = on_pause
        self._on_quit = on_quit
        self._icon = None
        self._thread: threading.Thread | None = None
        self._state = "inactive"  # "active", "paused", "inactive"

    def _build_menu(self):
        import pystray
        toggle_label = "Stop Listening" if self._state == "active" else "Start Listening"
        pause_label = "Resume" if self._state == "paused" else "Pause"

        return pystray.Menu(
            pystray.MenuItem(toggle_label, lambda: self._on_toggle()),
            pystray.MenuItem(pause_label, lambda: self._on_pause()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit VoxType", lambda: self._on_quit()),
        )

    def _get_icon_image(self) -> Image.Image:
        if self._state == "active":
            return ICON_ACTIVE
        elif self._state == "paused":
            return ICON_PAUSED
        return ICON_INACTIVE

    def _on_click(self, icon, item):
        """Handle left-click on tray icon."""
        self._on_toggle()

    def start(self) -> None:
        """Start the tray icon on a background thread."""
        import pystray

        self._icon = pystray.Icon(
            name="VoxType",
            icon=self._get_icon_image(),
            title="VoxType - Voice to Text",
            menu=self._build_menu(),
        )

        # Left-click toggles
        self._icon.on_activate = self._on_click

        self._thread = threading.Thread(target=self._icon.run, daemon=True, name="voxtype-tray")
        self._thread.start()
        logger.info("Tray icon started")

    def update_state(self, state: str) -> None:
        """Update tray icon appearance. state: 'active', 'paused', 'inactive'."""
        self._state = state
        if self._icon:
            self._icon.icon = self._get_icon_image()
            self._icon.menu = self._build_menu()
            title_suffix = {"active": "Listening", "paused": "Paused", "inactive": "Off"}
            self._icon.title = f"VoxType - {title_suffix.get(state, state)}"

    def stop(self) -> None:
        """Stop the tray icon."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
        logger.info("Tray icon stopped")

    def notify(self, message: str, title: str = "VoxType") -> None:
        """Show a system notification."""
        if self._icon:
            try:
                self._icon.notify(message, title)
            except Exception:
                logger.warning(f"Could not show notification: {message}")
