"""Text injection into any focused application via keystroke simulation.

Two modes of operation:
  1. Word-by-word: as partial transcription updates come in, inject new words
  2. Finalization: when a phrase is complete, correct any words that changed

The key insight: partial transcriptions can revise earlier words. For example:
  partial 1: "I want to"
  partial 2: "I want two"  (Whisper corrected "to" → "two")

We handle this by tracking what's been injected and sending backspaces
to correct changed words when needed.
"""

import threading
import logging
import time
from pynput.keyboard import Controller, Key

from config import VoxConfig

logger = logging.getLogger("voxtype.injector")


class TextInjector:
    def __init__(self, config: VoxConfig):
        self.config = config
        self._keyboard = Controller()
        self._lock = threading.Lock()

        # Track what's currently in the text field from our injection
        self._injected_text = ""
        # Track the last partial we processed
        self._last_partial = ""
        # Flag to know if we're mid-phrase (between start-of-speech and finalization)
        self._in_phrase = False

    def on_partial(self, text: str) -> None:
        """Handle partial transcription update - inject new words as they come.

        Called frequently as the user speaks. `text` is the full partial
        transcription so far (not just the new words).
        """
        if not self.config.inject_on_partial:
            return

        with self._lock:
            self._in_phrase = True

            # Check for snippet triggers
            snippet_result = self._check_snippets(text)
            if snippet_result:
                return

            if text == self._last_partial:
                return  # no change

            if not self._injected_text:
                # First words of a new phrase - just type them
                self._type_text(text)
                self._injected_text = text
                self._last_partial = text
                return

            # Find what changed
            old_words = self._injected_text.split()
            new_words = text.split()

            if not new_words:
                return

            # Find divergence point
            common_count = 0
            for i in range(min(len(old_words), len(new_words))):
                if old_words[i] == new_words[i]:
                    common_count = i + 1
                else:
                    break

            if common_count == len(old_words) and len(new_words) > len(old_words):
                # Simple case: new words appended, nothing changed
                new_part = " ".join(new_words[common_count:])
                self._type_text(" " + new_part)
                self._injected_text = text
            elif self.config.correction_enabled and common_count < len(old_words):
                # Words changed - need to correct via backspace
                # Delete from divergence point to end
                chars_to_delete = len(self._injected_text) - len(" ".join(old_words[:common_count]))
                if common_count > 0:
                    chars_to_delete -= 1  # account for space before divergent words

                self._backspace(chars_to_delete)

                # Type corrected text
                corrected_part = " ".join(new_words[common_count:])
                prefix = " " if common_count > 0 else ""
                self._type_text(prefix + corrected_part)
                self._injected_text = text
            else:
                # Correction disabled or only appending - just track it
                if len(new_words) > len(old_words):
                    new_part = " ".join(new_words[len(old_words):])
                    self._type_text(" " + new_part)
                    self._injected_text = text

            self._last_partial = text

    def on_finalized(self, text: str) -> None:
        """Handle finalized transcription - correct and finalize the phrase.

        Called when a pause is detected. `text` is the final, most accurate
        version of what was said.
        """
        with self._lock:
            # Check for snippet triggers first
            snippet_result = self._check_snippets(text)
            if snippet_result:
                self._reset_phrase()
                return

            if self.config.inject_on_partial and self._injected_text:
                # We've been injecting word-by-word. Now correct if needed.
                if text != self._injected_text:
                    # Final version differs - correct it
                    self._select_and_replace(self._injected_text, text)
            else:
                # Not doing word-by-word, inject the full finalized text
                self._type_text(text)

            # Add a space after the finalized phrase so the next phrase
            # starts cleanly
            self._type_text(" ")
            self._reset_phrase()

    def _reset_phrase(self) -> None:
        """Reset state for the next phrase."""
        self._injected_text = ""
        self._last_partial = ""
        self._in_phrase = False

    def _check_snippets(self, text: str) -> bool:
        """Check if text matches a snippet trigger. Returns True if matched."""
        text_lower = text.strip().lower()
        for trigger, replacement in self.config.snippets.items():
            if text_lower == trigger.lower():
                # Clear any partial text we've injected
                if self._injected_text:
                    self._backspace(len(self._injected_text))
                self._type_text(replacement)
                self._reset_phrase()
                return True
        return False

    def _select_and_replace(self, old_text: str, new_text: str) -> None:
        """Replace old_text with new_text using minimal edits."""
        # Find common prefix
        common_len = 0
        for i in range(min(len(old_text), len(new_text))):
            if old_text[i] == new_text[i]:
                common_len = i + 1
            else:
                break

        # Backspace to remove divergent suffix
        chars_to_delete = len(old_text) - common_len
        if chars_to_delete > 0:
            self._backspace(chars_to_delete)

        # Type the new suffix
        new_suffix = new_text[common_len:]
        if new_suffix:
            self._type_text(new_suffix)

    def _type_text(self, text: str) -> None:
        """Simulate typing text into the focused application."""
        if not text:
            return
        for char in text:
            try:
                self._keyboard.type(char)
            except Exception:
                # Some special chars might fail - try press/release
                try:
                    self._keyboard.press(char)
                    self._keyboard.release(char)
                except Exception:
                    logger.warning(f"Could not type character: {repr(char)}")
            if self.config.injection_delay > 0:
                time.sleep(self.config.injection_delay)

    def _backspace(self, count: int) -> None:
        """Send backspace keystrokes."""
        for _ in range(count):
            self._keyboard.press(Key.backspace)
            self._keyboard.release(Key.backspace)
            if self.config.injection_delay > 0:
                time.sleep(self.config.injection_delay)

    def clear(self) -> None:
        """Reset injection state (call when user manually edits text)."""
        with self._lock:
            self._reset_phrase()
