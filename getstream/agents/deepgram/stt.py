import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import os
import time

from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from getstream.agents import stt
from getstream.video.rtc.track_util import PcmData

logger = logging.getLogger(__name__)


class Deepgram(stt.STT):
    """
    Deepgram-based Speech-to-Text implementation.

    Events:
        - transcript: Emitted when a complete transcript is available.
            Args: text (str), metadata (dict)
        - partial: Emitted when a partial transcript is available.
            Args: text (str), metadata (dict)
        - error: Emitted when an error occurs during transcription.
            Args: error (Exception)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        options: Optional[LiveOptions] = None,
        sample_rate: int = 16000,
        language: str = "en-US",
        keep_alive_interval: float = 5.0,
    ):
        """
        Initialize the Deepgram STT service.

        Args:
            api_key: Deepgram API key. If not provided, the DEEPGRAM_API_KEY
                    environment variable will be used automatically.
            options: Deepgram live transcription options
            sample_rate: Sample rate of the audio in Hz
            language: Language code for transcription
            keep_alive_interval: Interval in seconds to send keep-alive messages.
                                Default is 5.0 seconds (recommended value by Deepgram)
        """
        super().__init__(sample_rate=sample_rate, language=language)

        # If no API key was provided, check for DEEPGRAM_API_KEY in environment
        if api_key is None:
            api_key = os.environ.get("DEEPGRAM_API_KEY")
            if not api_key:
                logger.warning(
                    "No API key provided and DEEPGRAM_API_KEY environment variable not found."
                )

        # Initialize DeepgramClient with the API key
        logger.info("Initializing Deepgram client")
        self.deepgram = DeepgramClient(api_key)
        self.dg_connection = None
        self.options = options or LiveOptions(
            model="nova-2",
            language=language,
            encoding="linear16",
            sample_rate=sample_rate,
            channels=1,
        )
        self._results_queue = asyncio.Queue()

        # Keep-alive mechanism
        self.keep_alive_interval = keep_alive_interval
        self.last_activity_time = time.time()
        self.keep_alive_task = None
        self._running = False

        self._setup_connection()

    def _setup_connection(self):
        """Set up the Deepgram connection with event handlers."""
        try:
            # Use the newer websocket interface instead of deprecated live
            logger.debug("Setting up Deepgram WebSocket connection")
            self.dg_connection = self.deepgram.listen.websocket.v("1")

            # Handler for transcript results
            # Updates to handle LiveResultResponse objects from the Deepgram SDK
            def handle_transcript(conn, result=None):
                try:
                    # Update the last activity time
                    self.last_activity_time = time.time()

                    # Check if result is already a dict (from LiveResultResponse)
                    if hasattr(result, "to_dict"):
                        transcript = result.to_dict()
                    elif hasattr(result, "to_json"):
                        transcript = json.loads(result.to_json())
                    elif isinstance(result, (str, bytes, bytearray)):
                        transcript = json.loads(result)
                    else:
                        logger.warning(
                            "Unrecognized transcript format: %s", type(result)
                        )
                        return

                    # Get the transcript text from the response
                    alternatives = transcript.get("channel", {}).get("alternatives", [])
                    if not alternatives:
                        return

                    transcript_text = alternatives[0].get("transcript", "")
                    if not transcript_text:
                        return

                    # Check if this is a final result
                    is_final = transcript.get("is_final", False)

                    # Create metadata with useful information
                    metadata = {
                        "confidence": alternatives[0].get("confidence", 0),
                        "words": alternatives[0].get("words", []),
                        "is_final": is_final,
                        "channel_index": transcript.get("channel_index", 0),
                    }

                    # Add the result to the queue
                    self._results_queue.put_nowait(
                        (is_final, transcript_text, metadata)
                    )
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
                    # Handle errors during transcript processing
                    error_obj = Exception(f"Transcript processing error: {e}")
                    self._results_queue.put_nowait((None, None, error_obj))

            # Handler for errors - updated to accept the connection object
            def handle_error(conn, error=None):
                # Update the last activity time
                self.last_activity_time = time.time()

                error_text = str(error) if error is not None else "Unknown error"
                logger.error("Deepgram error received: %s", error_text)
                error_obj = Exception(f"Deepgram error: {error_text}")
                # We can't use self.emit directly here since it's in a callback
                # Instead, we'll put the error in the queue for the process_audio method to handle
                self._results_queue.put_nowait((None, None, error_obj))

            # Register event handlers directly
            self.dg_connection.on(LiveTranscriptionEvents.Transcript, handle_transcript)
            self.dg_connection.on(LiveTranscriptionEvents.Error, handle_error)

            # Start the connection
            logger.info("Starting Deepgram connection with options %s", self.options)
            self.dg_connection.start(self.options)

            # Start the keep-alive task
            self._running = True
            self._start_keep_alive_task()

        except Exception as e:
            # Log the error and set connection to None
            logger.error("Error setting up Deepgram connection", exc_info=e)
            self.dg_connection = None
            # Put the error in the queue so it can be processed by _process_audio_impl
            self._results_queue.put_nowait((None, None, e))

    def _start_keep_alive_task(self):
        """Start the background task that sends keep-alive messages."""
        if self.keep_alive_task is None and self._running:
            logger.debug(
                "Starting keep-alive task with interval %ss", self.keep_alive_interval
            )
            self.keep_alive_task = asyncio.create_task(self._keep_alive_loop())

    async def _keep_alive_loop(self):
        """Background task that sends keep-alive messages to prevent connection timeout."""
        while self._running and self.dg_connection:
            try:
                # Check if we need to send a keep-alive message
                # Deepgram closes connection after 10s of inactivity, so we send
                # keep-alive messages if no activity for keep_alive_interval seconds
                time_since_last_activity = time.time() - self.last_activity_time

                if time_since_last_activity >= self.keep_alive_interval:
                    # Send a keep-alive message
                    logger.debug(
                        "Sending keep-alive message",
                        extra={"time_since_activity": time_since_last_activity},
                    )
                    await self.send_keep_alive()
                    # Update the last activity time
                    self.last_activity_time = time.time()

                # Sleep for a short period before checking again
                # We check more frequently than the interval to ensure timely keep-alive messages
                await asyncio.sleep(min(1.0, self.keep_alive_interval / 2))
            except asyncio.CancelledError:
                # Task was cancelled, exit the loop
                logger.info("Keep-alive task cancelled")
                break
            except Exception as e:
                logger.error("Error in keep-alive loop", exc_info=e)
                # Sleep briefly to avoid tight loop in case of persistent errors
                await asyncio.sleep(1.0)

    async def send_keep_alive(self):
        """Send a keep-alive message to maintain the connection."""
        if not self.dg_connection:
            logger.warning("Cannot send keep-alive: no connection available")
            return False

        try:
            # Create the keep-alive message according to Deepgram docs
            keep_alive_msg = json.dumps({"type": "KeepAlive"})

            # Send as a text message (not binary)
            # The Deepgram SDK doesn't have a send_text method, but the connection
            # does have a method to send non-binary data which we should use
            if hasattr(self.dg_connection, "send_text"):
                self.dg_connection.send_text(keep_alive_msg)
            elif hasattr(self.dg_connection, "keep_alive"):
                # Many SDKs have a dedicated keep_alive method
                self.dg_connection.keep_alive()
            else:
                # Fallback: try sending json as non-binary data
                self.dg_connection.send(keep_alive_msg)

            logger.debug("Sent keep-alive message to Deepgram")
            return True
        except Exception as e:
            logger.error("Error sending keep-alive message", exc_info=e)
            return False

    async def _process_audio_impl(
        self, pcm_data: PcmData, user_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Tuple[bool, str, Dict[str, Any]]]]:
        """
        Process audio data through Deepgram for transcription.

        Args:
            pcm_data: The PCM audio data to process
            user_metadata: Additional user metadata (ignored by Deepgram)

        Returns:
            A list of tuples (is_final, text, metadata) representing transcription results,
            or None if no results are available.
        """
        # Ensure we have a valid connection
        if not self.dg_connection:
            try:
                self._setup_connection()
                if not self.dg_connection:
                    raise ValueError(
                        "Failed to create Deepgram connection. Check your API key."
                    )
            except Exception as e:
                raise ValueError(f"Failed to create Deepgram connection: {e}") from e

        # Handle different audio formats
        if pcm_data.format == "s16":
            # Deepgram expects s16 linear PCM, which is what we have
            audio_data = pcm_data.samples

            # If we need to resample, handle that here
            if pcm_data.sample_rate != self.sample_rate:
                # Simple resampling for demonstration purposes
                # In production, use a proper resampling library
                import scipy.signal

                num_samples = int(
                    len(audio_data) * self.sample_rate / pcm_data.sample_rate
                )
                audio_data = scipy.signal.resample(audio_data, num_samples).astype(
                    np.int16
                )

            # Send audio data to Deepgram
            try:
                # Convert ndarray to bytes
                audio_bytes = audio_data.tobytes()
                self.dg_connection.send(audio_bytes)
                logger.debug(f"Sent {len(audio_bytes)} bytes to Deepgram")

                # Update the last activity time since we sent audio
                self.last_activity_time = time.time()

                # Wait for results with a longer timeout
                results = []
                try:
                    # Try to get results with longer timeout (1 second)
                    while True:
                        try:
                            # Use a longer timeout to capture results from the API
                            result = await asyncio.wait_for(
                                self._results_queue.get(), timeout=1.0
                            )

                            # Check if this is an error
                            if result[0] is None and isinstance(result[2], Exception):
                                raise result[2]

                            results.append(result)
                        except asyncio.TimeoutError:
                            # No more results available right now
                            break
                except Exception as e:
                    # Re-raise any exceptions from the results queue
                    raise e

                return results if results else None

            except Exception as e:
                # Propagate the error up
                raise e
        else:
            # If we get another format, raise an error
            raise ValueError(f"Unsupported audio format: {pcm_data.format}")

    async def close(self):
        """Close the Deepgram connection and clean up resources."""
        if not self._is_closed:
            self._is_closed = True
            self._running = False

            # Cancel the keep-alive task
            if self.keep_alive_task:
                self.keep_alive_task.cancel()
                try:
                    await self.keep_alive_task
                except asyncio.CancelledError:
                    pass
                self.keep_alive_task = None

            if self.dg_connection:
                try:
                    # Send a clean close message
                    try:
                        # Try different methods to close the connection cleanly
                        close_msg = json.dumps({"type": "CloseStream"})

                        if hasattr(self.dg_connection, "send_text"):
                            self.dg_connection.send_text(close_msg)
                        else:
                            # Fallback to regular send for text data
                            self.dg_connection.send(close_msg)
                    except Exception as e:
                        logger.error("Error sending close message", exc_info=e)

                    # Finish the connection
                    self.dg_connection.finish()
                    self.dg_connection = None
                except Exception as e:
                    # Just log errors during shutdown
                    logger.error("Error closing Deepgram connection", exc_info=e)
