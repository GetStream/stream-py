import abc
import asyncio
import logging
import time
from typing import Optional, Dict, Any, Tuple, Callable, TypeVar, Generic

from pyee.asyncio import AsyncIOEventEmitter
from getstream.video.rtc.track_util import PcmData

logger = logging.getLogger(__name__)

# Type variable for the result queue items
T = TypeVar("T")


class BackgroundDispatcher(Generic[T]):
    """
    A helper class for background dispatch of items from a queue.
    This can be used by different STT providers to process transcription results asynchronously.
    """

    def __init__(self, process_item: Callable[[T], None], name: str = "dispatcher"):
        """
        Initialize the background dispatcher.

        Args:
            process_item: Function that processes each item from the queue.
            name: Name of the dispatcher for logging purposes.
        """
        self.queue = asyncio.Queue()
        self.task = None
        self.process_item = process_item
        self.running = False
        self.name = name
        self._loop = None
        logger.debug(f"Initialized background {name}")

    def start(self):
        """Start the background dispatcher task if not already running."""
        if self.task is None and not self.running:
            logger.info(f"Starting {self.name} task")
            self.running = True
            self._loop = asyncio.get_running_loop()
            self.task = asyncio.create_task(self._dispatch_loop())

    async def _dispatch_loop(self):
        """Background task that processes items from the queue."""
        logger.info(f"{self.name} loop started")
        while self.running:
            try:
                # Wait for an item from the queue
                item = await self.queue.get()

                # Process the item
                try:
                    self.process_item(item)
                except Exception as e:
                    logger.error(f"Error processing item in {self.name}", exc_info=e)

                # Mark the task as done
                self.queue.task_done()

            except asyncio.CancelledError:
                # Task was cancelled, exit the loop
                logger.info(f"{self.name} task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in {self.name} loop", exc_info=e)
                # Sleep briefly to avoid tight loop in case of persistent errors
                await asyncio.sleep(1.0)

        logger.info(f"{self.name} loop stopped")

    def add_item(self, item: T, threadsafe: bool = False):
        """
        Add an item to the queue.

        Args:
            item: The item to add to the queue.
            threadsafe: Whether to use call_soon_threadsafe for adding the item.
        """
        if not self.running:
            logger.warning(f"Tried to add item to stopped {self.name}")
            return

        if threadsafe:
            try:
                # Use call_soon_threadsafe to safely add to the queue from a different thread
                if self._loop and self._loop.is_running():
                    self._loop.call_soon_threadsafe(self.queue.put_nowait, item)
                else:
                    # If we don't have a valid loop reference, try to get the event loop
                    # This might raise a RuntimeError in a non-main thread
                    try:
                        asyncio.get_event_loop().call_soon_threadsafe(
                            self.queue.put_nowait, item
                        )
                    except RuntimeError:
                        # We're in a different thread and there's no event loop
                        logger.warning(
                            f"Cannot add item to {self.name} from non-event loop thread"
                        )
                        # Create a new thread-local event loop for this thread
                        # This is a fallback when the item must be added but we're in a different thread
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        # Now we can add the item
                        new_loop.call_soon_threadsafe(self.queue.put_nowait, item)
                        # Clean up the loop
                        new_loop.close()
            except Exception as e:
                logger.error(f"Error adding item to {self.name} queue", exc_info=e)
        else:
            try:
                # Add directly to the queue
                self.queue.put_nowait(item)
            except Exception as e:
                logger.error(
                    f"Error adding item directly to {self.name} queue", exc_info=e
                )

    async def stop(self):
        """Stop the background dispatcher task."""
        if not self.running:
            return

        self.running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

        # Clear the queue
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except asyncio.QueueEmpty:
                break


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

        logger.debug(
            "Initialized STT base class",
            extra={"sample_rate": sample_rate, "language": language},
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
    ) -> Optional[list[Tuple[bool, str, Dict[str, Any]]]]:
        """
        Implementation-specific method to process audio data.

        This method must be implemented by all STT providers and should handle the core
        transcription logic. The base class handles event emission and error handling.

        Args:
            pcm_data: The PCM audio data to process. Guaranteed to be valid by base class.
            user_metadata: Additional metadata about the user or session.

        Returns:
            A list of tuples (is_final, text, metadata) representing transcription results,
            or None if no results are available.

            Each tuple contains:
            - is_final (bool): True for final transcripts, False for partial/interim results
            - text (str): The transcribed text
            - metadata (dict): Implementation-specific metadata including:
                - confidence (float, optional): Confidence score if available
                - processing_time_ms (float, optional): Processing time in milliseconds
                - Any other provider-specific metadata

        Raises:
            Exception: Implementations should let exceptions bubble up to be handled
                      by the base class, which will emit appropriate error events.
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
