import abc
import logging
import time
from typing import Optional, Dict, Any, Tuple, List
import asyncio
from asyncio import AbstractEventLoop
from pyee.asyncio import AsyncIOEventEmitter
from getstream.video.rtc.track_util import PcmData

logger = logging.getLogger(__name__)


class STT(AsyncIOEventEmitter, abc.ABC):
    """
    Abstract base class for Speech-to-Text implementations.

    This class provides a standardized interface for STT implementations with consistent
    event emission patterns and error handling.

    Events:
        - transcript: Emitted when a complete transcript is available.
            Args: text (str), user_metadata (dict), metadata (dict)
        - partial_transcript: Emitted when a partial transcript is available.
            Args: text (str), user_metadata (dict), metadata (dict)
        - error: Emitted when an error occurs during transcription.
            Args: error (Exception)

    Standard Error Handling:
        - All implementations should catch exceptions in _process_audio_impl and emit error events
        - Use _emit_error_event() helper for consistent error emission
        - Log errors with appropriate context using the logger

    Standard Event Emission:
        - Use _emit_transcript_event() and _emit_partial_transcript_event() helpers
        - Include processing time and audio duration in metadata when available
        - Maintain consistent metadata structure across implementations
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        language: str = "en-US",
        *,
        loop: Optional[AbstractEventLoop] = None,
    ):
        """
        Initialize the STT service.

        Args:
            sample_rate: The sample rate of the audio to process, in Hz.
            language: The language code to use for transcription.
            loop: The asyncio event loop that should be used by the underlying
                  ``AsyncIOEventEmitter`` when scheduling coroutine callbacks.

        Providing an explicit event loop is critical when callbacks may be
        emitted from background threads (for example, SDK-managed listening
        threads).  When the loop is not specified, ``pyee.AsyncIOEventEmitter``
        falls back to ``asyncio.ensure_future`` without an explicit loop which
        relies on ``asyncio.get_event_loop``.  In non-main threads this raises
        ``RuntimeError: There is no current event loop``.  Capturing the running
        loop at instantiation guarantees the callbacks are always scheduled on
        the correct loop regardless of the calling thread.
        """

        if loop is None:
            try:
                # Prefer the currently running loop if in async context
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # We are likely being instantiated in a sync test before any loop
                # exists.  Create a dedicated loop to schedule callbacks.
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

        _loop = loop

        # Pass the resolved loop to the ``AsyncIOEventEmitter`` base class so
        # that all callbacks are scheduled on this loop even when ``emit`` is
        # invoked from worker threads.
        super().__init__(loop=_loop)
        self._track = None
        self.sample_rate = sample_rate
        self.language = language
        self._is_closed = False

        logger.debug(
            "Initialized STT base class",
            extra={
                "sample_rate": sample_rate,
                "language": language,
                "loop": str(_loop),
            },
        )

    def _validate_pcm_data(self, pcm_data: PcmData) -> bool:
        """
        Validate PCM data input for processing.

        Args:
            pcm_data: The PCM audio data to validate.

        Returns:
            True if the data is valid, False otherwise.
        """

        if not hasattr(pcm_data, "samples") or pcm_data.samples is None:
            logger.warning("PCM data has no samples")
            return False

        if not hasattr(pcm_data, "sample_rate") or pcm_data.sample_rate <= 0:
            logger.warning("PCM data has invalid sample rate")
            return False

        # Check if samples are empty
        if hasattr(pcm_data.samples, "__len__") and len(pcm_data.samples) == 0:
            logger.debug("Received empty audio samples")
            return False

        return True

    def _emit_transcript_event(
        self,
        text: str,
        user_metadata: Optional[Dict[str, Any]],
        metadata: Dict[str, Any],
    ):
        """
        Emit a final transcript event with consistent logging.

        Args:
            text: The transcribed text.
            user_metadata: User-specific metadata.
            metadata: Transcription metadata (processing time, confidence, etc.).
        """
        logger.info(
            "Emitting final transcript",
            extra={
                "text_length": len(text),
                "has_user_metadata": user_metadata is not None,
                "processing_time_ms": metadata.get("processing_time_ms"),
                "confidence": metadata.get("confidence"),
            },
        )
        self.emit("transcript", text, user_metadata, metadata)

    def _emit_partial_transcript_event(
        self,
        text: str,
        user_metadata: Optional[Dict[str, Any]],
        metadata: Dict[str, Any],
    ):
        """
        Emit a partial transcript event with consistent logging.

        Args:
            text: The partial transcribed text.
            user_metadata: User-specific metadata.
            metadata: Transcription metadata (processing time, confidence, etc.).
        """
        logger.debug(
            "Emitting partial transcript",
            extra={
                "text_length": len(text),
                "has_user_metadata": user_metadata is not None,
                "confidence": metadata.get("confidence"),
            },
        )
        self.emit("partial_transcript", text, user_metadata, metadata)

    def _emit_error_event(self, error: Exception, context: str = ""):
        """
        Emit an error event with consistent logging.

        Args:
            error: The exception that occurred.
            context: Additional context about where the error occurred.
        """
        logger.error(
            f"STT error{' in ' + context if context else ''}",
            exc_info=error,
        )
        self.emit("error", error)

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

        # Validate input data
        if not self._validate_pcm_data(pcm_data):
            logger.warning("Invalid PCM data received, skipping processing")
            return

        try:
            # Process the audio data using the implementation-specific method
            audio_duration_ms = (
                pcm_data.duration * 1000 if hasattr(pcm_data, "duration") else None
            )
            logger.debug(
                "Processing audio chunk",
                extra={
                    "duration_ms": audio_duration_ms,
                    "has_user_metadata": user_metadata is not None,
                },
            )

            start_time = time.time()
            results = await self._process_audio_impl(pcm_data, user_metadata)
            processing_time = time.time() - start_time

            # If no results were returned, just return
            if not results:
                logger.debug(
                    "No speech detected in audio",
                    extra={
                        "processing_time_ms": processing_time * 1000,
                        "audio_duration_ms": audio_duration_ms,
                    },
                )
                return

            # Process each result and emit the appropriate event
            for is_final, text, metadata in results:
                # Ensure metadata includes processing time if not already present
                if "processing_time_ms" not in metadata:
                    metadata["processing_time_ms"] = processing_time * 1000

                if is_final:
                    self._emit_transcript_event(text, user_metadata, metadata)
                else:
                    self._emit_partial_transcript_event(text, user_metadata, metadata)

        except Exception as e:
            # Emit any errors that occur during processing
            self._emit_error_event(e, "audio processing")

    @abc.abstractmethod
    async def _process_audio_impl(
        self, pcm_data: PcmData, user_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Tuple[bool, str, Dict[str, Any]]]]:
        """
        Implementation-specific method to process audio data.

        This method must be implemented by all STT providers and should handle the core
        transcription logic. The base class handles event emission and error handling.

        Args:
            pcm_data: The PCM audio data to process. Guaranteed to be valid by base class.
            user_metadata: Additional metadata about the user or session.

        Returns:
            optional list[tuple[bool, str, dict]] | None
                • synchronous providers: a list of results.
                • asynchronous providers: None (they emit events themselves).

        Notes:
            Implementations must not both emit events and return non-empty results,
            or duplicate events will be produced.
            Exceptions should bubble up; process_audio() will catch them
            and emit a single "error" event.
        """
        pass

    @abc.abstractmethod
    async def close(self):
        """
        Close the STT service and release any resources.

        Implementations should:
        - Set self._is_closed = True
        - Clean up any background tasks or connections
        - Release any allocated resources
        - Log the closure appropriately
        """
        pass
