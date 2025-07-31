"""
Fal Wizper STT Plugin for Stream

Provides real-time audio transcription and translation using fal-ai/wizper (Whisper v3).
This plugin integrates with Stream's audio processing pipeline to provide high-quality
speech-to-text capabilities.

Example usage:
    from fal_wizper_stt import FalWizperSTT

    # For transcription
    stt = FalWizperSTT(task="transcribe")

    # For translation to Portuguese
    stt = FalWizperSTT(task="translate", target_language="pt")

    @stt.on("transcript")
    async def on_transcript(text: str, user: Any, metadata: dict):
        print(f"Transcript: {text}")

    @stt.on("error")
    async def on_error(error: str):
        print(f"Error: {error}")
"""

import asyncio
import io
import os
import tempfile
import wave
import time
import logging
import numpy as np
from typing import Any, Dict, Optional, List, Tuple

import fal_client
from getstream.video.rtc.track_util import PcmData
from getstream.plugins.common import STT

logger = logging.getLogger(__name__)


class FalWizperSTT(STT):
    """
    Audio transcription and translation using fal-ai/wizper (Whisper v3).

    This plugin provides real-time speech-to-text capabilities using the fal-ai/wizper
    service, which is based on OpenAI's Whisper v3 model. It supports both transcription
    and translation tasks.

    Attributes:
        task: The task type - either "transcribe" or "translate"
        target_language: Target language code for translation (e.g., "pt" for Portuguese)
    """

    def __init__(
        self,
        task: str = "translate",
        target_language: str = "pt",
        sample_rate: int = 48000,
    ):
        """
        Initialize FalWizperSTT.

        Args:
            task: "transcribe" or "translate"
            target_language: Target language code (e.g., "pt" for Portuguese)
            sample_rate: Sample rate of the audio in Hz.
        """
        language = target_language if task == "translate" else "en-US"
        super().__init__(sample_rate=sample_rate, language=language)
        self.task = task
        self.target_language = target_language
        self.last_activity_time = time.time()
        self._is_closed = False

    def on(self, event: str):
        """Register an event callback.

        This is a thin wrapper around the :pyclass:`~pyee.asyncio.AsyncIOEventEmitter` ``on`` method so that
        callers can continue to use the decorator-style registration while relying on the
        implementation provided by the ``STT`` base class.
        """
        return super().on(event)

    # The custom _emit helper is no longer necessary as the STT base class
    # provides standard helpers for emitting transcript, partial_transcript, and
    # error events.  It is intentionally left as a no-op for backward
    # compatibility should any external code still reference it.
    def _emit(self, *args, **kwargs):
        pass

    def _pcm_to_wav_bytes(self, pcm_data: PcmData) -> bytes:
        """
        Convert PCM data to WAV format bytes.

        Args:
            pcm_data: PCM audio data from Stream's audio pipeline

        Returns:
            WAV format audio data as bytes

        Raises:
            AttributeError: If PCM data format is not recognized
        """

        # Try common attribute names
        audio_data = None
        for attr in ["data", "samples", "bytes", "raw_data", "audio_data", "pcm_data"]:
            if hasattr(pcm_data, attr):
                audio_data = getattr(pcm_data, attr)
                break

        if audio_data is None:
            raise AttributeError(
                "Could not find audio data attribute in PcmData object"
            )

        wav_buffer = io.BytesIO()

        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data)

        wav_buffer.seek(0)
        return wav_buffer.read()

    def _numpy_to_wav_bytes(self, audio_array: np.ndarray) -> bytes:
        """
        Convert numpy array to WAV format bytes.

        Args:
            audio_array: Audio data as numpy array

        Returns:
            WAV format audio data as bytes
        """

        # Ensure audio is int16
        if audio_array.dtype != np.int16:
            if audio_array.dtype == np.float32 or audio_array.dtype == np.float64:
                # Convert from float [-1, 1] to int16
                audio_array = (audio_array * 32767).astype(np.int16)
            else:
                audio_array = audio_array.astype(np.int16)

        wav_buffer = io.BytesIO()

        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_array.tobytes())

        wav_buffer.seek(0)
        return wav_buffer.read()

    async def _process_audio_impl(
        self, pcm_data: PcmData, user_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Tuple[bool, str, Dict[str, Any]]]]:
        """
        Process audio data through fal-ai/wizper for transcription.

        Args:
            pcm_data: The PCM audio data to process.
            user_metadata: Additional metadata about the user or session.

        Returns:
            None - fal-ai/wizper operates in asynchronous mode and emits events directly
            when transcripts arrive from the streaming service.
        """
        if self._is_closed:
            logger.warning("fal-ai/wizper connection is closed, ignoring audio")
            return None

        # Check if the input sample rate matches the expected sample rate
        if (
            hasattr(pcm_data, "sample_rate")
            and pcm_data.sample_rate != self.sample_rate
        ):
            logger.warning(
                "Input audio sample rate (%s Hz) does not match the expected sample rate (%s Hz). "
                "This may result in incorrect transcriptions. Consider resampling the audio.",
                pcm_data.sample_rate,
                self.sample_rate,
            )

        # Update the last activity time
        self.last_activity_time = time.time()

        try:
            # Convert PCM to WAV format
            wav_data = self._pcm_to_wav_bytes(pcm_data)

            # Create temporary file for upload
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(wav_data)
                temp_file.flush()
                temp_file_path = temp_file.name

            try:
                # Upload file and get URL
                audio_url = fal_client.upload_file(temp_file_path)

                # Prepare request parameters
                input_params = {
                    "audio_url": audio_url,
                    "task": self.task,
                    "chunk_level": "segment",
                    "version": "3",
                    "language": self.target_language,
                }

                logger.debug(
                    "Sending audio data to fal-ai/wizper",
                    extra={"audio_bytes": len(wav_data)},
                )

                # Submit to fal-ai/wizper
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: fal_client.subscribe("fal-ai/wizper", input_params)
                )

                # Extract text from result
                if "text" in result:
                    text = result["text"].strip()
                    if text:
                        self._emit_transcript_event(
                            text, user_metadata, {"chunks": result.get("chunks", [])}
                        )
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass

        except Exception as e:
            logger.error(f"fal-ai/wizper audio transmission error: {e}")
            self._emit_error_event(e, "fal-ai/wizper audio transmission")
            raise

        # Return None for asynchronous mode - events are emitted when they arrive
        return None

    async def process_speech_audio(self, speech_audio: np.ndarray, user: Any) -> None:
        """
        Process accumulated speech audio through fal-ai/wizper.

        This method is typically called by VAD (Voice Activity Detection) systems
        when speech segments are detected.

        Args:
            speech_audio: Accumulated speech audio as numpy array
            user: User metadata from the Stream call
        """
        if self._is_closed:
            return

        if len(speech_audio) == 0:
            return

        try:
            # Convert numpy array to WAV format
            wav_data = self._numpy_to_wav_bytes(speech_audio)

            # Create temporary file for upload
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(wav_data)
                temp_file.flush()
                temp_file_path = temp_file.name

            try:
                # Upload file and get URL
                audio_url = fal_client.upload_file(temp_file_path)

                # Prepare request parameters
                input_params = {
                    "audio_url": audio_url,
                    "task": self.task,
                    "chunk_level": "segment",
                    "version": "3",
                }

                # Add language for translation
                if self.task == "translate":
                    input_params["language"] = self.target_language

                logger.debug(
                    "Sending speech audio to fal-ai/wizper",
                    extra={"audio_bytes": len(wav_data)},
                )

                # Submit to fal-ai/wizper
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: fal_client.subscribe("fal-ai/wizper", input_params)
                )

                # Extract text from result
                if "text" in result:
                    text = result["text"].strip()
                    if text:
                        self._emit_transcript_event(
                            text, user, {"chunks": result.get("chunks", [])}
                        )
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass

        except Exception as e:
            logger.error(f"FalWizper processing error: {str(e)}")
            self._emit_error_event(e, "FalWizper processing")

    async def close(self):
        """Close the STT service and release any resources."""
        if self._is_closed:
            return
        self._is_closed = True
        logger.info("FalWizperSTT closed")
