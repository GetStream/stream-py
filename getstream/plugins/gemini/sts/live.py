"""Gemini Live Speech-to-Speech implementation.

This module provides a wrapper around Google's Gemini Live API that implements the
common STS interface. It is designed to mirror the OpenAI realtime wrapper so it
can be used in a similar way across the plugin ecosystem.

Notes:
- This wrapper exposes a connection object that proxies the underlying GenAI
  live session. It yields responses via ``session.receive()``.
- Session updates are best-effort based on available public API methods.
"""

from __future__ import annotations

import logging
import asyncio
import os
from typing import Optional
import contextlib
from google.genai import Client
from google.genai.types import (
    LiveConnectConfigDict,
    Blob,
    Modality,
    AudioTranscriptionConfigDict,
    RealtimeInputConfigDict,
    TurnCoverage,
    SpeechConfigDict,
    VoiceConfigDict,
    PrebuiltVoiceConfigDict,
)
from google.genai.live import AsyncSession

from getstream.plugins.common import STS
from getstream.audio.utils import resample_audio
from getstream.video.rtc.track_util import PcmData
from getstream.video.rtc.audio_track import AudioStreamTrack

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None  # type: ignore


logger = logging.getLogger(__name__)


class GeminiLive(STS):
    """Speech-to-Speech wrapper for Google Gemini Live API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-live-2.5-flash-preview",
        config: Optional[LiveConnectConfigDict] = LiveConnectConfigDict(
            response_modalities=[Modality.AUDIO],
            input_audio_transcription=AudioTranscriptionConfigDict(),
            output_audio_transcription=AudioTranscriptionConfigDict(),
            speech_config=SpeechConfigDict(
                voice_config=VoiceConfigDict(
                    prebuilt_voice_config=PrebuiltVoiceConfigDict(voice_name="Puck")
                )
            ),
            realtime_input_config=RealtimeInputConfigDict(
                turn_coverage=TurnCoverage.TURN_INCLUDES_ALL_INPUT
            ),
        ),
    ):
        """Create a new Gemini Live wrapper.

        Args:
            api_key: Gemini API key. Falls back to ``GOOGLE_API_KEY`` or ``GEMINI_API_KEY`` env var.
            model: Model ID to use when connecting.
            config: Provider config to pass through unchanged. Prefer passing a
                ``LiveConnectConfigDict`` from ``google.genai.types``.
        """

        super().__init__()

        self.api_key = (
            api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        )
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY or GEMINI_API_KEY not provided and not found in env"
            )

        if Client is None:
            raise ImportError(
                "failed to import google genai SDK, install with: uv add google-genai"
            )

        # Use v1beta for Live APIs as required by current SDK
        self.client = Client(
            api_key=self.api_key, http_options={"api_version": "v1beta"}
        )
        self.model = model
        # Prefer explicit config passed to constructor; can be overridden per-call
        self.config: Optional[LiveConnectConfigDict] = config
        self._session: Optional[AsyncSession] = None
        self._listener_task: Optional[asyncio.Task] = None
        self._connect_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._ready_event = asyncio.Event()

        # Create an outbound audio track for assistant speech
        self.output_track = AudioStreamTrack(
            framerate=24000, stereo=False, format="s16"
        )

        # Kick off background connect if we are in an event loop
        loop = asyncio.get_running_loop()
        self._connect_task = loop.create_task(self._run_connection())

    async def _run_connection(self) -> None:
        """Background task that connects and holds the session open until stopped."""
        if self._is_connected:
            return
        logger.info("Connecting Gemini agent using model %s", self.model)
        connect_cm = self.client.aio.live.connect(model=self.model, config=self.config)
        async with connect_cm as session:
            self._session = session
            self._is_connected = True
            self._ready_event.set()
            self.emit("connected")
            logger.info("Connected Gemini agent using model %s", self.model)
            # Start listener automatically
            await self.start_response_listener()
            # Wait until asked to stop
            await self._stop_event.wait()
        # After context exits
        self._session = None
        self._is_connected = False
        self._ready_event.clear()
        self._listener_task = None

    async def wait_until_ready(self, timeout: Optional[float] = None) -> bool:
        """Wait until the live session is ready. Returns True if ready."""
        if self._ready_event.is_set():
            return True
        try:
            await asyncio.wait_for(self._ready_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def send_text(self, text: str):
        """Send a text message from the human side to the conversation."""
        if not self._is_connected or not self._session:
            await self.wait_until_ready()
            if not self._is_connected or not self._session:
                raise RuntimeError("Not connected")
        await self._session.send_realtime_input(text=text)

    async def send_audio_pcm(self, pcm: PcmData, target_rate: int = 48000):
        """Send a `PcmData` frame, resampling if needed.

        Args:
            pcm: PcmData from RTC pipeline (int16 numpy array or bytes).
            target_rate: Target sample rate for Gemini input.
        """
        if not self._is_connected or not self._session:
            await self.wait_until_ready()
            if not self._is_connected or not self._session:
                raise RuntimeError("Not connected")

        if np is None:
            raise ImportError("numpy not available; required for PCM conversion")

        # Convert to numpy int16 array
        if isinstance(pcm.samples, (bytes, bytearray)):
            # Interpret as int16 little-endian
            audio_array = np.frombuffer(pcm.samples, dtype=np.int16)
        else:
            audio_array = np.asarray(pcm.samples)
            if audio_array.dtype != np.int16:
                audio_array = audio_array.astype(np.int16)

        # Resample if needed
        if pcm.sample_rate != target_rate:
            audio_array = resample_audio(
                audio_array, pcm.sample_rate, target_rate
            ).astype(np.int16)

        # Build blob and send directly
        audio_bytes = audio_array.tobytes()
        mime = f"audio/pcm;rate={target_rate}"
        blob = Blob(data=audio_bytes, mime_type=mime)
        logger.debug(
            "Sending %d bytes audio to Gemini Live (%s)", len(audio_bytes), mime
        )
        await self._session.send_realtime_input(audio=blob)

    async def start_response_listener(
        self,
        emit_events: bool = True,
    ) -> None:
        """Start a background task to read responses and emit/forward audio chunks.

        Args:
            emit_events: If True, emit an "audio" event with chunk bytes.
        """
        if not self._is_connected or not self._session:
            await self.wait_until_ready()
            if not self._is_connected or not self._session:
                raise RuntimeError("Not connected")
        if self._listener_task and not self._listener_task.done():
            return

        # Capture for type-checker
        async def _loop():
            try:
                assert self._session is not None
                # Continuously read turns; receive() yields one complete model turn
                while self._is_connected and self._session is not None:
                    async for resp in self._session.receive():
                        if data := resp.data:
                            if emit_events:
                                self.emit("audio", data)
                            # Write to published output track
                            await self.output_track.write(data)
                        text = getattr(resp, "text", None)
                        if text and emit_events:
                            self.emit("text", text)

                    # Small pause between turns to avoid tight loop
                    await asyncio.sleep(0)
            except asyncio.CancelledError:  # graceful stop
                return
            except Exception as e:
                self.emit("error", e)

        self._listener_task = asyncio.create_task(_loop())
        asyncio.create_task(self._write_to_output_track())
        return None

    async def stop_response_listener(self) -> None:
        """Stop the background response listener, if running."""
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        self._listener_task = None

    async def close(self) -> None:
        """Stop the session and background tasks."""
        self._stop_event.set()
        await self.stop_response_listener()
        if self._connect_task and not self._connect_task.done():
            self._connect_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._connect_task


__all__ = ["GeminiLive"]
