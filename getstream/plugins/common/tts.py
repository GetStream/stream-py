import abc
import logging
import inspect
import time
from typing import Optional, Dict, Any, Union, Iterator, AsyncIterator

from pyee.asyncio import AsyncIOEventEmitter
from getstream.video.rtc.audio_track import AudioStreamTrack

logger = logging.getLogger(__name__)


class TTS(AsyncIOEventEmitter, abc.ABC):
    """
    Text-to-Speech base class.

    This abstract class provides the interface for text-to-speech implementations.
    It handles:
    - Converting text to speech
    - Sending audio data to an output track
    - Emitting audio events

    Events:
        - audio: Emitted when an audio chunk is available.
            Args: audio_data (bytes), user_metadata (dict)
        - error: Emitted when an error occurs during speech synthesis.
            Args: error (Exception)

    Implementations should inherit from this class and implement the synthesize method.
    """

    def __init__(self):
        """
        Initialize the TTS base class.

        All implementation-specific parameters should be handled by subclasses.
        """
        super().__init__()
        self._track: Optional[AudioStreamTrack] = None

    def set_output_track(self, track: AudioStreamTrack) -> None:
        """
        Set the audio track to output speech to.

        Args:
            track: The audio track object that will receive speech audio
        """
        self._track = track

    @property
    def track(self):
        """Get the current output track."""
        return self._track

    @abc.abstractmethod
    async def synthesize(
        self, text: str, *args, **kwargs
    ) -> Union[bytes, Iterator[bytes], AsyncIterator[bytes]]:
        """
        Convert text to speech audio data.

        This method must be implemented by subclasses.

        Args:
            text: The text to convert to speech
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Audio data as bytes, an iterator of audio chunks, or an async iterator of audio chunks
        """
        pass

    async def send(
        self, text: str, user: Optional[Dict[str, Any]] = None, *args, **kwargs
    ):
        """
        Convert text to speech, send to the output track, and emit an audio event.

        Args:
            text: The text to convert to speech
            user: Optional user metadata to include with the audio event
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Raises:
            ValueError: If no output track has been set
        """
        if self._track is None:
            raise ValueError("No output track set. Call set_output_track() first.")

        try:
            # Log start of synthesis
            start_time = time.time()
            logger.debug(
                "Starting text-to-speech synthesis", extra={"text_length": len(text)}
            )

            # Synthesize audio
            audio_data = await self.synthesize(text, *args, **kwargs)

            # Calculate synthesis time
            synthesis_time = time.time() - start_time

            # Track total audio duration and bytes
            total_audio_bytes = 0
            audio_chunks = 0

            if isinstance(audio_data, bytes):
                total_audio_bytes = len(audio_data)
                audio_chunks = 1
                await self._track.write(audio_data)
                self.emit("audio", audio_data, user)
            elif inspect.isasyncgen(audio_data):
                async for chunk in audio_data:
                    if isinstance(chunk, bytes):
                        total_audio_bytes += len(chunk)
                        audio_chunks += 1
                        await self._track.write(chunk)
                        self.emit("audio", chunk, user)
                    else:  # assume it's a Cartesia TTS chunk object
                        total_audio_bytes += len(chunk.data)
                        audio_chunks += 1
                        await self._track.write(chunk.data)
                        self.emit("audio", chunk.data, user)
            elif hasattr(audio_data, "__iter__") and not isinstance(
                audio_data, (str, bytes, bytearray)
            ):
                for chunk in audio_data:
                    total_audio_bytes += len(chunk)
                    audio_chunks += 1
                    await self._track.write(chunk)
                    self.emit("audio", chunk, user)
            else:
                raise TypeError(
                    f"Unsupported return type from synthesize: {type(audio_data)}"
                )

            # Log completion with timing information
            end_time = time.time()
            total_time = end_time - start_time

            # Estimate audio duration - this is approximate without knowing format details
            # Use track framerate if available, otherwise assume 16kHz
            sample_rate = self._track.framerate if self._track else 16000
            # For s16 format (16-bit samples), each byte is half a sample
            estimated_audio_duration_ms = (total_audio_bytes / 2) / (sample_rate / 1000)

            logger.info(
                "Text-to-speech synthesis completed",
                extra={
                    "text_length": len(text),
                    "synthesis_time_ms": synthesis_time * 1000,
                    "total_time_ms": total_time * 1000,
                    "audio_bytes": total_audio_bytes,
                    "audio_chunks": audio_chunks,
                    "estimated_audio_duration_ms": estimated_audio_duration_ms,
                    "real_time_factor": (synthesis_time * 1000)
                    / estimated_audio_duration_ms
                    if estimated_audio_duration_ms > 0
                    else None,
                    "sample_rate": sample_rate,
                },
            )

        except Exception as e:
            # Emit any errors that occur during processing
            self.emit("error", e)
            # Re-raise to allow the caller to handle the error
            raise
