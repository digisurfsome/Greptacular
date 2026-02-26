"""Speech-to-text transcription engine using RealtimeSTT + faster-whisper.

Provides two callback streams:
  1. on_partial(text) - fires frequently with partial words as you speak
  2. on_finalized(text) - fires when a pause is detected, text is final/accurate

The partial stream drives word-by-word injection.
The finalized stream drives correction passes.
"""

import logging
import threading
from collections.abc import Callable

from config import VoxConfig
from RealtimeSTT import AudioToTextRecorder

logger = logging.getLogger("voxtype.transcriber")


class Transcriber:
    def __init__(
        self,
        config: VoxConfig,
        on_partial: Callable[[str], None] | None = None,
        on_finalized: Callable[[str], None] | None = None,
        on_recording_start: Callable[[], None] | None = None,
        on_recording_stop: Callable[[], None] | None = None,
    ):
        self.config = config
        self._on_partial = on_partial
        self._on_finalized = on_finalized
        self._on_recording_start = on_recording_start
        self._on_recording_stop = on_recording_stop

        self._recorder: AudioToTextRecorder | None = None
        self._running = False
        self._paused = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

        # Audio buffer for crash recovery - keep last N seconds
        self._audio_buffer: list[bytes] = []
        self._max_buffer_chunks = 200  # ~12 seconds at 16kHz

    def _resolve_device(self) -> str:
        """Determine compute device."""
        if self.config.device != "auto":
            return self.config.device
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def _build_recorder(self) -> AudioToTextRecorder:
        device = self._resolve_device()
        compute_type = "float16" if device == "cuda" else "int8"

        logger.info(f"Initializing Whisper model={self.config.model} device={device} compute={compute_type}")

        recorder = AudioToTextRecorder(
            model=self.config.model,
            language=self.config.language,
            device=device,
            compute_type=compute_type,
            # Real-time partial transcription
            enable_realtime_transcription=True,
            realtime_model_type="tiny",  # fast small model for partials
            realtime_processing_pause=0.05,  # 50ms between partial updates
            on_realtime_transcription_update=self._handle_partial,
            on_realtime_transcription_stabilized=self._handle_partial_stabilized,
            # Pause/silence detection
            silero_sensitivity=0.4,
            post_speech_silence_duration=self.config.pause_threshold,
            min_length_of_recording=self.config.min_speech_duration,
            # Recording callbacks
            on_recording_start=self._handle_recording_start,
            on_recording_stop=self._handle_recording_stop,
            # Audio settings
            sample_rate=self.config.sample_rate,
            spinner=False,
            level=logging.WARNING,
        )

        # Set input device if specified
        if self.config.audio_device is not None:
            recorder.input_device_index = self.config.audio_device

        return recorder

    def _handle_partial(self, text: str) -> None:
        """Called frequently with partial transcription as user speaks."""
        if self._paused or not text.strip():
            return
        if self._on_partial:
            try:
                self._on_partial(text.strip())
            except Exception:
                logger.exception("Error in on_partial callback")

    def _handle_partial_stabilized(self, text: str) -> None:
        """Called with stabilized partial text (less likely to change)."""
        # We use this as an additional partial signal for more stable word-by-word
        if self._paused or not text.strip():
            return
        if self._on_partial:
            try:
                self._on_partial(text.strip())
            except Exception:
                logger.exception("Error in on_partial_stabilized callback")

    def _handle_finalized(self, text: str) -> None:
        """Called when a complete phrase/sentence is finalized after pause."""
        if self._paused or not text.strip():
            return
        if self._on_finalized:
            try:
                self._on_finalized(text.strip())
            except Exception:
                logger.exception("Error in on_finalized callback")

    def _handle_recording_start(self) -> None:
        if self._on_recording_start:
            try:
                self._on_recording_start()
            except Exception:
                logger.exception("Error in on_recording_start callback")

    def _handle_recording_stop(self) -> None:
        if self._on_recording_stop:
            try:
                self._on_recording_stop()
            except Exception:
                logger.exception("Error in on_recording_stop callback")

    def _run_loop(self) -> None:
        """Main transcription loop - runs on background thread."""
        try:
            self._recorder = self._build_recorder()
            logger.info("Transcriber started")

            while self._running:
                try:
                    # text() blocks until a complete phrase is detected (pause)
                    # then returns the finalized transcription
                    self._recorder.text(self._handle_finalized)
                    # text() returns the finalized text, but we already handle
                    # it via the callback. This just keeps the loop running.
                except Exception:
                    if self._running:
                        logger.exception("Error in transcription loop, restarting...")
                        # Crash recovery: rebuild recorder and continue
                        try:
                            if self._recorder:
                                self._recorder.stop()
                                self._recorder.shutdown()
                        except Exception:
                            pass
                        self._recorder = self._build_recorder()

        except Exception:
            logger.exception("Fatal error initializing transcriber")
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        if self._recorder:
            try:
                self._recorder.stop()
                self._recorder.shutdown()
            except Exception:
                pass
            self._recorder = None

    def start(self) -> None:
        """Start transcription on a background thread."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._paused = False
            self._thread = threading.Thread(target=self._run_loop, daemon=True, name="voxtype-transcriber")
            self._thread.start()

    def stop(self) -> None:
        """Stop transcription and clean up."""
        with self._lock:
            self._running = False
            if self._recorder:
                try:
                    self._recorder.abort()
                except Exception:
                    pass
            if self._thread:
                self._thread.join(timeout=5)
                self._thread = None

    def pause(self) -> None:
        """Pause transcription (mic stays open but output is suppressed)."""
        self._paused = True
        logger.info("Transcriber paused")

    def resume(self) -> None:
        """Resume transcription after pause."""
        self._paused = False
        logger.info("Transcriber resumed")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_paused(self) -> bool:
        return self._paused
