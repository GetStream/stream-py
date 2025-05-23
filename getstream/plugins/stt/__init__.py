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
                logger.info(
                    "No speech detected in audio",
                    extra={
                        "processing_time_ms": processing_time * 1000,
                        "audio_duration_ms": audio_duration_ms,
                    },
                )
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
                    logger.info(
                        "Processed speech to text",
                        extra={
                            "processing_time_ms": processing_time * 1000,
                            "audio_duration_ms": audio_duration_ms,
                            "text_length": len(text),
                            "real_time_factor": (processing_time * 1000)
                            / audio_duration_ms
                            if audio_duration_ms
                            else None,
                        },
                    )
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
