import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Conditional imports with error handling
try:
    import assemblyai as aai
    from assemblyai.streaming.v3 import (
        StreamingClient,
        StreamingClientOptions,
        StreamingEvents,
        StreamingParameters,
    )
    _assemblyai_available = True
except ImportError:
    aai = None  # type: ignore
    StreamingClient = None  # type: ignore
    StreamingClientOptions = None  # type: ignore
    StreamingEvents = None  # type: ignore
    StreamingParameters = None  # type: ignore
    _assemblyai_available = False

from getstream.plugins.common import STT
from getstream.video.rtc.track_util import PcmData

logger = logging.getLogger(__name__)


class AssemblyAISTT(STT):
    """
    AssemblyAI-based Speech-to-Text implementation.

    This implementation operates in asynchronous mode - it receives streaming transcripts
    from AssemblyAI's WebSocket connection and emits events immediately as they arrive,
    providing real-time responsiveness for live transcription scenarios.

    Events:
        - transcript: Emitted when a complete transcript is available.
            Args: text (str), user_metadata (dict), metadata (dict)
        - partial_transcript: Emitted when a partial transcript is available.
            Args: text (str), user_metadata (dict), metadata (dict)
        - error: Emitted when an error occurs during transcription.
            Args: error (Exception)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        sample_rate: int = 48000,
        language: str = "en",
        interim_results: bool = True,
        enable_partials: bool = True,
        enable_automatic_punctuation: bool = True,
        enable_utterance_end_detection: bool = True,
    ):
        """
        Initialize the AssemblyAI STT service.

        Args:
            api_key: AssemblyAI API key. If not provided, the ASSEMBLYAI_API_KEY
                    environment variable will be used automatically.
            sample_rate: Sample rate of the audio in Hz (default: 48000)
            language: Language code for transcription (default: "en")
            interim_results: Whether to emit interim results (partial transcripts)
            enable_partials: Whether to enable partial results
            enable_automatic_punctuation: Whether to enable automatic punctuation
            enable_utterance_end_detection: Whether to enable utterance end detection
        """
        super().__init__(sample_rate=sample_rate, provider_name="assemblyai")

        # Check if assemblyai is available
        if not _assemblyai_available:
            raise ImportError("assemblyai package not installed.")

        # If no API key was provided, check for ASSEMBLYAI_API_KEY in environment
        if api_key is None:
            api_key = os.environ.get("ASSEMBLYAI_API_KEY")
            if not api_key:
                logger.warning(
                    "No API key provided and ASSEMBLYAI_API_KEY environment variable not found."
                )

        # Set the API key globally for AssemblyAI
        aai.settings.api_key = api_key

        # Initialize streaming client
        logger.info("Initializing AssemblyAI streaming client")
        self.streaming_client = None
        self._running = False
        self._setup_attempted = False
        self._is_closed = False

        # Configuration options
        self.language = language
        self.interim_results = interim_results
        self.enable_partials = enable_partials
        self.enable_automatic_punctuation = enable_automatic_punctuation
        self.enable_utterance_end_detection = enable_utterance_end_detection

        # Track current user context for associating transcripts with users
        self._current_user = None

        # Audio buffering for AssemblyAI requirements (50-1000ms chunks)
        self._audio_buffer = bytearray()
        self._buffer_start_time = None
        self._min_chunk_duration_ms = 100  # Minimum 100ms chunks
        self._max_chunk_duration_ms = 500   # Maximum 500ms chunks

        self._setup_connection()

    def _setup_connection(self):
        """Set up the AssemblyAI streaming connection with event handlers."""
        if self._is_closed:
            logger.warning("Cannot setup connection - AssemblyAI instance is closed")
            return

        if self.streaming_client is not None:
            logger.debug("Connection already set up, skipping initialization")
            return

        try:
            # Create the streaming client
            logger.debug("Setting up AssemblyAI streaming connection")
            self.streaming_client = StreamingClient(
                StreamingClientOptions(
                    api_key=aai.settings.api_key,
                )
            )

            # Register event handlers with proper method references
            self.streaming_client.on(StreamingEvents.Begin, self._on_begin)
            self.streaming_client.on(StreamingEvents.Turn, self._on_turn)
            self.streaming_client.on(StreamingEvents.Termination, self._on_terminated)
            self.streaming_client.on(StreamingEvents.Error, self._on_error)

            # Start the connection
            logger.info("Starting AssemblyAI connection")
            self.streaming_client.connect(
                StreamingParameters(
                    sample_rate=self.sample_rate,
                    language=self.language,
                    enable_partials=self.enable_partials,
                    enable_automatic_punctuation=self.enable_automatic_punctuation,
                    enable_utterance_end_detection=self.enable_utterance_end_detection,
                )
            )

            # Mark as running
            self._running = True

        except Exception as e:
            # Log the error and set connection to None
            logger.error("Error setting up AssemblyAI connection", exc_info=e)
            self.streaming_client = None
            # Emit error immediately
            self._emit_error_event(e, "AssemblyAI connection setup")

    def _on_begin(self, client, event):
        """Handler for session begin event."""
        logger.info(f"AssemblyAI session started: {event.id}")

    def _on_turn(self, client, event):
        """Handler for transcript results."""
        try:
            # Get the transcript text from the response
            transcript_text = event.transcript
            if not transcript_text:
                return

            # Check what attributes are available on the event
            logger.debug(f"TurnEvent attributes: {dir(event)}")
            
            # AssemblyAI TurnEvent doesn't have is_final, it's always final
            # Partial results come through different events
            is_final = True

            # Create metadata with useful information
            metadata = {
                "confidence": getattr(event, "confidence", 0),
                "is_final": is_final,
                "session_id": getattr(event, "session_id", ""),
                "audio_start": getattr(event, "audio_start", 0),
                "audio_end": getattr(event, "audio_end", 0),
            }

            # Handle the result (both collect and emit)
            self._handle_transcript_result(is_final, transcript_text, metadata)

            logger.debug(
                "Received transcript",
                extra={
                    "is_final": is_final,
                    "text_length": len(transcript_text),
                    "confidence": metadata["confidence"],
                },
            )
        except Exception as e:
            logger.error("Error processing transcript", exc_info=e)
            # Emit error immediately
            self._emit_error_event(e, "AssemblyAI transcript processing")

    def _on_terminated(self, client, event):
        """Handler for session termination event."""
        logger.info(
            f"AssemblyAI session terminated: {event.audio_duration_seconds} seconds of audio processed"
        )

    def _on_error(self, client, error):
        """Handler for error events."""
        error_text = str(error) if error is not None else "Unknown error"
        logger.error(f"AssemblyAI error received: {error_text}")

        # Emit error immediately
        error_obj = Exception(f"AssemblyAI error: {error_text}")
        self._emit_error_event(error_obj, "AssemblyAI connection")

    def _handle_transcript_result(
        self, is_final: bool, text: str, metadata: Dict[str, Any]
    ):
        """
        Handle a transcript result by emitting it immediately.
        """
        # Emit immediately for real-time responsiveness
        if is_final:
            self._emit_transcript_event(text, self._current_user, metadata)
        else:
            self._emit_partial_transcript_event(text, self._current_user, metadata)

        logger.debug(
            "Handled transcript result",
            extra={
                "is_final": is_final,
                "text_length": len(text),
            },
        )

    async def _process_audio_impl(
        self, pcm_data: PcmData, user_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Tuple[bool, str, Dict[str, Any]]]]:
        """
        Process audio data through AssemblyAI for transcription.

        Args:
            pcm_data: The PCM audio data to process.
            user_metadata: Additional metadata about the user or session.

        Returns:
            None - AssemblyAI operates in asynchronous mode and emits events directly
            when transcripts arrive from the streaming service.
        """
        if self._is_closed:
            logger.warning("AssemblyAI connection is closed, ignoring audio")
            return None

        # Store the current user context for transcript events
        self._current_user = user_metadata

        # Check if the input sample rate matches the expected sample rate
        if pcm_data.sample_rate != self.sample_rate:
            logger.warning(
                "Input audio sample rate (%s Hz) does not match the expected sample rate (%s Hz). "
                "This may result in incorrect transcriptions. Consider resampling the audio.",
                pcm_data.sample_rate,
                self.sample_rate,
            )

        # Ensure connection is set up
        if not self.streaming_client and not self._setup_attempted:
            logger.warning("AssemblyAI connection not initialized, attempting setup")
            self._setup_connection()
            self._setup_attempted = True

        if not self.streaming_client:
            if not self._setup_attempted:
                logger.info("No AssemblyAI connection available, retrying setup")
                self._setup_connection()
                self._setup_attempted = True
            else:
                logger.error("No AssemblyAI connection available after retry")
                # Return an error result instead of emitting directly
                raise Exception("No AssemblyAI connection available")

        # Mark that we've attempted setup
        self._setup_attempted = True

        # Convert PCM data to bytes if needed
        audio_data = pcm_data.samples
        if not isinstance(audio_data, bytes):
            # Convert numpy array to bytes
            audio_data = audio_data.astype(np.int16).tobytes()

        # Initialize buffer start time if not set
        if self._buffer_start_time is None:
            self._buffer_start_time = time.time()

        # Add audio data to buffer
        self._audio_buffer.extend(audio_data)

        # Calculate current buffer duration
        buffer_duration_ms = (len(self._audio_buffer) / (self.sample_rate * 2)) * 1000  # 2 bytes per sample for int16

        # Send buffer if it meets minimum duration requirement
        if buffer_duration_ms >= self._min_chunk_duration_ms:
            try:
                logger.debug(
                    "Sending buffered audio to AssemblyAI",
                    extra={
                        "audio_bytes": len(self._audio_buffer),
                        "duration_ms": buffer_duration_ms,
                    },
                )
                
                # Send the buffered audio data
                self.streaming_client.stream(bytes(self._audio_buffer))
                
                # Clear buffer and reset timer
                self._audio_buffer.clear()
                self._buffer_start_time = time.time()
                
            except Exception as e:
                logger.error("Error sending audio to AssemblyAI", exc_info=e)
                # Clear buffer on error to prevent accumulation
                self._audio_buffer.clear()
                self._buffer_start_time = time.time()
                raise Exception(f"AssemblyAI audio transmission error: {e}")

        # Return None for asynchronous mode - events are emitted when they arrive
        return None

    async def close(self):
        """Close the AssemblyAI connection and clean up resources."""
        if self._is_closed:
            logger.debug("AssemblyAI STT service already closed")
            return

        logger.info("Closing AssemblyAI STT service")
        self._is_closed = True
        self._running = False

        # Flush any remaining audio in buffer
        if self._audio_buffer and self.streaming_client:
            try:
                logger.debug("Flushing remaining audio buffer")
                self.streaming_client.stream(bytes(self._audio_buffer))
                self._audio_buffer.clear()
            except Exception as e:
                logger.warning("Error flushing audio buffer", exc_info=e)

        # Close the AssemblyAI connection if it exists
        if self.streaming_client:
            logger.debug("Closing AssemblyAI connection")
            try:
                self.streaming_client.disconnect()
                self.streaming_client = None
            except Exception as e:
                logger.error("Error closing AssemblyAI connection", exc_info=e)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def flush_buffer(self):
        """Flush the current audio buffer immediately (for testing purposes)."""
        if self.streaming_client and self._audio_buffer:
            try:
                self.streaming_client.stream(bytes(self._audio_buffer))
                self._audio_buffer.clear()
                self._buffer_start_time = None
            except Exception as e:
                logger.error("Error flushing audio buffer", exc_info=e)
                raise Exception(f"AssemblyAI buffer flush error: {e}")
