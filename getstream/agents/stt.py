import abc
import asyncio
import logging
from typing import Optional, Dict, Any, Tuple

from pyee.asyncio import AsyncIOEventEmitter
from getstream.video.rtc.track_util import PcmData

logger = logging.getLogger(__name__)


class STT(AsyncIOEventEmitter, abc.ABC):
    """
    Abstract base class for Speech-to-Text implementations.

    Events:
        - transcript: Emitted when a complete transcript is available.
            Args: text (str), metadata (dict)
        - partial_transcript: Emitted when a partial transcript is available.
            Args: text (str), metadata (dict)
        - error: Emitted when an error occurs during transcription.
            Args: error (Exception)
    """

    def __init__(self, sample_rate: int = 16000, language: str = "en-US"):
        """
        Initialize the STT service.

        Args:
            sample_rate: The sample rate of the audio to process, in Hz.
            language: The language code to use for transcription.
        """
        super().__init__()
        self._track = None
        self.sample_rate = sample_rate
        self.language = language
        self._is_closed = False
        self._buffer = []
        self._buffer_lock = asyncio.Lock()

        logger.debug(
            "Initialized STT base class",
            extra={"sample_rate": sample_rate, "language": language},
        )

    async def process_audio(
        self, pcm_data: PcmData, user_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Process audio data for transcription and emit appropriate events.

        Args:
            pcm_data: The PCM audio data to process.
            user_metadata: Additional metadata about the user or session.
        """
        if self._is_closed:
            logger.debug("Ignoring audio processing request - STT is closed")
            return

        try:
            # Process the audio data using the implementation-specific method
            logger.debug(
                "Processing audio chunk",
                extra={
                    "duration_ms": pcm_data.duration * 1000
                    if pcm_data.duration
                    else None,
                    "has_user_metadata": user_metadata is not None,
                },
            )

            results = await self._process_audio_impl(pcm_data, user_metadata)

            # If no results were returned, just return
            if not results:
                return

            # Process each result and emit the appropriate event
            for is_final, text, metadata in results:
                event_type = "transcript" if is_final else "partial_transcript"
                logger.debug(
                    f"Emitting {event_type} event",
                    extra={
                        "is_final": is_final,
                        "text_length": len(text),
                        "has_metadata": bool(metadata),
                    },
                )

                if is_final:
                    self.emit("transcript", text, metadata)
                else:
                    self.emit("partial_transcript", text, metadata)

        except Exception as e:
            # Emit any errors that occur during processing
            logger.error("Error processing audio", exc_info=e)
            self.emit("error", e)

    @abc.abstractmethod
    async def _process_audio_impl(
        self, pcm_data: PcmData, user_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[list[Tuple[bool, str, Dict[str, Any]]]]:
        """
        Implementation-specific method to process audio data.

        Args:
            pcm_data: The PCM audio data to process.
            user_metadata: Additional metadata about the user or session.

        Returns:
            A list of tuples (is_final, text, metadata) representing transcription results,
            or None if no results are available.
        """
        pass

    @abc.abstractmethod
    async def close(self):
        """
        Close the STT service and release any resources.
        """
        pass
