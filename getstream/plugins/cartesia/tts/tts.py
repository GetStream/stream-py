from __future__ import annotations

import os
from typing import Optional

from cartesia import AsyncCartesia
from cartesia.tts import OutputFormat_Raw

from getstream.plugins.common import TTS
from getstream.video.rtc.audio_track import AudioStreamTrack


class CartesiaTTS(TTS):
    """Text-to-Speech plugin backed by the Cartesia Sonic model."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: str = "sonic-2",
        voice_id: str | None = "f9836c6e-a0bd-460e-9d3c-f7299fa60f94",
        sample_rate: int = 16000,
    ) -> None:
        """Create a new Cartesia TTS instance.

        Args:
            api_key: Cartesia API key – falls back to ``CARTESIA_API_KEY`` env var.
            model_id: Which model to use (default ``sonic-2``).
            voice_id: Cartesia voice ID. When ``None`` the model default is used.
            sample_rate: PCM sample-rate you want back (must match output track).
        """

        super().__init__()

        self.api_key = api_key or os.getenv("CARTESIA_API_KEY")
        if not self.api_key:
            raise ValueError("CARTESIA_API_KEY env var or api_key parameter required")

        self.client = AsyncCartesia(api_key=self.api_key)
        self.model_id = model_id
        self.voice_id = voice_id
        self.sample_rate = sample_rate

    def set_output_track(self, track: AudioStreamTrack) -> None:  # noqa: D401
        if track.framerate != self.sample_rate:
            raise TypeError(
                f"Track framerate {track.framerate} ≠ expected {self.sample_rate}"
            )
        super().set_output_track(track)

    async def synthesize(self, text: str, *_, **__) -> bytes:  # noqa: D401
        """Generate speech and yield raw PCM chunks."""

        output_format: OutputFormat_Raw = {
            "container": "raw",
            "encoding": "pcm_s16le",
            "sample_rate": self.sample_rate,
        }  # type: ignore[assignment]

        # ``/tts/bytes`` is the lowest-latency endpoint and returns an *async*
        # iterator when used with ``AsyncCartesia``. Each item yielded is
        # a raw ``bytes`` / ``bytearray`` containing PCM samples (new Cartesia SDK)

        response = self.client.tts.bytes(
            model_id=self.model_id,
            transcript=text,
            voice={"id": self.voice_id} if self.voice_id else {},
            output_format=output_format,
        )

        async def _audio_chunk_stream():  # noqa: D401
            async for chunk in response:
                yield bytes(chunk)

        return _audio_chunk_stream()
