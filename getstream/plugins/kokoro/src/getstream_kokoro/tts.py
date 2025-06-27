from __future__ import annotations

import asyncio
import numpy as np
from typing import AsyncIterator, List, Optional

from getstream_common.tts import TTS
from getstream.video.rtc.audio_track import AudioStreamTrack

# Kokoro is an optional, heavy dependency – we import lazily so that
# unit-tests can mock it before class construction.
try:
    from kokoro import KPipeline  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – mocked during CI
    KPipeline = None  # type: ignore  # noqa: N816


class KokoroTTS(TTS):
    """Text-to-Speech plugin backed by the Kokoro-82M model."""

    def __init__(
        self,
        lang_code: str = "a", # American English
        voice: str = "af_heart",
        speed: float = 1.0,
        sample_rate: int = 24_000,
        device: Optional[str] = None,
    ) -> None:
        """Create a new Kokoro TTS instance.

        Args:
            lang_code: Language group identifier (see Kokoro docs).
            voice: Kokoro voice id.
            speed: Playback speed multiplier.
            sample_rate: Output PCM sample-rate. Kokoro is trained at 24 kHz.
            device: "cpu", "cuda", … – passed straight to `KPipeline`.
        """

        super().__init__()

        if KPipeline is None:
            raise ImportError(
                "The 'kokoro' package is not installed. ``pip install kokoro`` first."
            )

        # Build a reusable pipeline – this keeps the model in memory between calls
        if device is None:
            self._pipeline = KPipeline(lang_code=lang_code)
        else:
            self._pipeline = KPipeline(lang_code=lang_code, device=device)

        self.voice = voice
        self.speed = speed
        self.sample_rate = sample_rate

    # ---------------------------------------------------------------------
    # TTS base-class API
    # ---------------------------------------------------------------------

    def set_output_track(self, track: AudioStreamTrack) -> None:  # noqa: D401
        if track.framerate != self.sample_rate:
            raise TypeError(
                f"Invalid framerate {track.framerate}, Kokoro requires {self.sample_rate} Hz"
            )
        super().set_output_track(track)

    async def synthesize(self, text: str, *_, **__) -> AsyncIterator[bytes]:  # noqa: D401
        """Generate speech and yield PCM chunks as *bytes*.

        Kokoro returns NumPy float32 arrays in the range [-1, 1]. We scale
        those to 16-bit signed little-endian samples so they can be written
        straight into :class:`~getstream.video.rtc.audio_track.AudioStreamTrack`.
        """

        loop = asyncio.get_event_loop()

        # Run blocking inference in a thread-pool to avoid stalling the event-loop
        chunks: List[bytes] = await loop.run_in_executor(
            None, lambda: list(self._generate_chunks(text))
        )
        return chunks  # List is iterable – the base-class will iterate over it

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _generate_chunks(self, text: str):
        """Blocking helper that returns an iterator of *bytes* chunks."""
        # Kokoro supports simple regex splitting – this yields multiple shorter
        # audio arrays which we forward as separate PCM chunks.
        for _gs, _ps, audio in self._pipeline(
            text,
            voice=self.voice,
            speed=self.speed,
            split_pattern=r"\n+",
        ):
            # Ensure we have a NumPy array
            if not isinstance(audio, np.ndarray):
                audio = np.asarray(audio)

            # Clamp/scale and convert to int16 little-endian PCM
            pcm16 = (np.clip(audio, -1.0, 1.0) * 32767.0).astype("<i2")
            yield pcm16.tobytes() 