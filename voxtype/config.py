"""VoxType configuration."""

import json
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_PATH = Path.home() / ".voxtype" / "config.json"


@dataclass
class VoxConfig:
    # Whisper model - "large-v3" for GPU, "medium" or "small" for CPU-only
    model: str = "medium"
    language: str = "en"
    device: str = "auto"  # "auto", "cuda", "cpu"

    # Pause detection - seconds of silence before finalizing a phrase
    pause_threshold: float = 0.4
    # Minimum audio level to consider as speech
    min_speech_duration: float = 0.1

    # Injection settings
    injection_delay: float = 0.008  # delay between keystrokes (seconds)
    inject_on_partial: bool = True  # word-by-word as you speak
    correction_enabled: bool = True  # backspace+retype when whisper refines words

    # Hotkeys
    hotkey_toggle: str = "ctrl+shift+space"
    hotkey_pause: str = "ctrl+shift+p"

    # Wake words (voice commands) - set to empty string to disable
    wake_word_start: str = ""
    wake_word_stop: str = ""

    # Audio
    sample_rate: int = 16000
    audio_device: int | None = None  # None = default mic

    # Saved text snippets - say the key phrase, inserts the value
    snippets: dict[str, str] = field(default_factory=dict)

    def save(self) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(self.__dict__, indent=2))

    @classmethod
    def load(cls) -> "VoxConfig":
        if CONFIG_PATH.exists():
            try:
                data = json.loads(CONFIG_PATH.read_text())
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except (json.JSONDecodeError, TypeError):
                pass
        return cls()
