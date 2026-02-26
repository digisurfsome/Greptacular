"""VoxType - Voice to text that types directly into any application.

Usage:
    python main.py              # Start with default settings
    python main.py --model large-v3   # Use large model (needs GPU)
    python main.py --list-devices     # List available microphones
"""

import argparse
import logging
import signal
import sys
import time

from config import VoxConfig
from hotkeys import HotkeyManager
from injector import TextInjector
from transcriber import Transcriber
from tray import TrayIcon

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("voxtype")


class VoxType:
    """Main application controller."""

    def __init__(self, config: VoxConfig):
        self.config = config
        self._listening = False

        # Core components
        self._injector = TextInjector(config)
        self._transcriber = Transcriber(
            config,
            on_partial=self._injector.on_partial,
            on_finalized=self._injector.on_finalized,
            on_recording_start=self._on_speech_start,
            on_recording_stop=self._on_speech_end,
        )
        self._hotkeys = HotkeyManager()
        self._tray = TrayIcon(
            on_toggle=self.toggle,
            on_pause=self.toggle_pause,
            on_quit=self.quit,
        )

    def _on_speech_start(self) -> None:
        logger.debug("Speech detected")

    def _on_speech_end(self) -> None:
        logger.debug("Speech ended (silence)")

    def toggle(self) -> None:
        """Toggle listening on/off."""
        if self._listening:
            self.stop_listening()
        else:
            self.start_listening()

    def start_listening(self) -> None:
        """Start transcribing and injecting text."""
        if self._listening:
            return
        logger.info("Starting VoxType - listening...")
        self._injector.clear()
        self._transcriber.start()
        self._listening = True
        self._tray.update_state("active")
        self._tray.notify("Listening started", "VoxType")

    def stop_listening(self) -> None:
        """Stop transcribing."""
        if not self._listening:
            return
        logger.info("Stopping VoxType")
        self._transcriber.stop()
        self._injector.clear()
        self._listening = False
        self._tray.update_state("inactive")

    def toggle_pause(self) -> None:
        """Pause/resume transcription."""
        if not self._listening:
            return
        if self._transcriber.is_paused:
            self._transcriber.resume()
            self._tray.update_state("active")
            logger.info("Resumed")
        else:
            self._transcriber.pause()
            self._injector.clear()
            self._tray.update_state("paused")
            logger.info("Paused")

    def run(self) -> None:
        """Start the application."""
        logger.info("VoxType starting up...")
        logger.info(f"Model: {self.config.model} | Device: {self.config.device}")
        logger.info(f"Toggle: {self.config.hotkey_toggle} | Pause: {self.config.hotkey_pause}")

        # Register hotkeys
        self._hotkeys.register(self.config.hotkey_toggle, self.toggle, "Toggle listening")
        self._hotkeys.register(self.config.hotkey_pause, self.toggle_pause, "Pause/resume")

        # Start tray icon
        self._tray.start()
        self._tray.update_state("inactive")

        # Auto-start listening
        self.start_listening()

        logger.info("VoxType is running. Press Ctrl+C or use tray icon to quit.")

        # Keep main thread alive
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            self.quit()

    def quit(self) -> None:
        """Clean shutdown."""
        logger.info("Shutting down VoxType...")
        self.stop_listening()
        self._hotkeys.unregister_all()
        self._tray.stop()
        # Give threads a moment to clean up
        time.sleep(0.5)
        sys.exit(0)


def list_audio_devices() -> None:
    """Print available audio input devices."""
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        print("\nAvailable audio input devices:\n")
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                default = " (DEFAULT)" if i == pa.get_default_input_device_info()["index"] else ""
                print(f"  [{i}] {info['name']}{default}")
        pa.terminate()
        print("\nUse --device <number> to select a specific microphone.\n")
    except ImportError:
        print("PyAudio not available. Install it to list devices.")
        print("  pip install pyaudio")


def main() -> None:
    parser = argparse.ArgumentParser(description="VoxType - Voice to text for any application")
    parser.add_argument("--model", default=None, help="Whisper model: tiny, base, small, medium, large-v3")
    parser.add_argument("--device", type=int, default=None, help="Audio input device index (use --list-devices)")
    parser.add_argument("--list-devices", action="store_true", help="List available microphones and exit")
    parser.add_argument("--cpu", action="store_true", help="Force CPU mode (no GPU)")
    parser.add_argument("--pause-threshold", type=float, default=None, help="Seconds of silence before injecting (default: 0.4)")
    parser.add_argument("--no-partial", action="store_true", help="Disable word-by-word injection (inject only on pause)")
    args = parser.parse_args()

    if args.list_devices:
        list_audio_devices()
        return

    # Load or create config
    config = VoxConfig.load()

    # Apply CLI overrides
    if args.model:
        config.model = args.model
    if args.device is not None:
        config.audio_device = args.device
    if args.cpu:
        config.device = "cpu"
    if args.pause_threshold is not None:
        config.pause_threshold = args.pause_threshold
    if args.no_partial:
        config.inject_on_partial = False

    # Save config for next run
    config.save()

    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, lambda *_: None)  # let KeyboardInterrupt propagate naturally

    app = VoxType(config)
    app.run()


if __name__ == "__main__":
    main()
