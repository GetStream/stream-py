import os
import asyncio
import logging
import tempfile
import time
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import soundfile as sf

from getstream.plugins.stt import STT
from getstream.video.rtc.track_util import PcmData
from getstream.audio.utils import resample_audio
import moonshine_onnx as moonshine

logger = logging.getLogger(__name__)

# Supported Moonshine models with canonical mapping
_SUPPORTED_MODELS = {
    "tiny": "moonshine/tiny",
    "moonshine/tiny": "moonshine/tiny",
    "base": "moonshine/base",
    "moonshine/base": "moonshine/base",
}


class Moonshine(STT):
    """
    Moonshine-based Speech-to-Text implementation.

    Moonshine is a family of speech-to-text models optimized for fast and accurate
    automatic speech recognition (ASR) on resource-constrained devices.

    Events:
        - transcript: Emitted when a complete transcript is available.
            Args: text (str), user (any), metadata (dict)
        - partial_transcript: Emitted when a partial transcript is available.
            Args: text (str), user (any), metadata (dict)
        - error: Emitted when an error occurs during transcription.
            Args: error (Exception)
    """

    def __init__(
        self,
        model_name: str = "moonshine/base",
        sample_rate: int = 16000,
        language: str = "en-US",
        chunk_duration_ms: int = 1000,
        min_audio_length_ms: int = 500,
        target_dbfs: float = -26.0,
    ):
        """
        Initialize the Moonshine STT service.

        Args:
            model_name: Moonshine model to use ("moonshine/tiny" or "moonshine/base")
            sample_rate: Sample rate of the audio in Hz (default: 16000, Moonshine's native rate)
            language: Language code for transcription (currently only "en-US" supported)
            chunk_duration_ms: Duration of audio chunks to process in milliseconds
            min_audio_length_ms: Minimum audio length required for transcription
            target_dbfs: Target RMS level in dBFS for audio normalization (default: -26.0, Moonshine's optimal level)
        """
        super().__init__(sample_rate=sample_rate, language=language)

        # Validate and normalize model name
        if model_name not in _SUPPORTED_MODELS:
            raise ValueError(
                f"Unknown Moonshine model '{model_name}'. "
                f"Allowed values: {', '.join(_SUPPORTED_MODELS.keys())}"
            )
        self.model_name = _SUPPORTED_MODELS[model_name]  # Use canonical value
        self.chunk_duration_ms = chunk_duration_ms
        self.min_audio_length_ms = min_audio_length_ms
        self.target_dbfs = target_dbfs

        # ONNX runtime will handle device selection automatically

        # Audio buffer for accumulating samples
        self._audio_buffer = np.array([], dtype=np.int16)
        self._buffer_lock = asyncio.Lock()

        # Track current user context
        self._current_user = None

        logger.info(
            "Initialized Moonshine STT",
            extra={
                "model_name": model_name,
                "canonical_model": self.model_name,
                "sample_rate": sample_rate,
                "chunk_duration_ms": chunk_duration_ms,
                "min_audio_length_ms": min_audio_length_ms,
                "target_dbfs": target_dbfs,
            },
        )

        # Log the exact checkpoint that will be loaded
        logger.info("Moonshine model selected", extra={"checkpoint": self.model_name})

    def _normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Normalize audio data to float32 in range [-1, 1].

        Args:
            audio_data: Input audio data as int16

        Returns:
            Normalized audio data as float32
        """
        # Convert int16 to float32 and normalize to [-1, 1]
        return audio_data.astype(np.float32) / 32768.0

    def _rms_normalise(self, audio: np.ndarray) -> np.ndarray:
        """
        Boost or attenuate audio to match target RMS in dBFS.

        Args:
            audio: Input audio data as int16

        Returns:
            RMS-normalized audio data as int16
        """
        # Calculate current RMS in dB
        rms = np.sqrt(np.mean(audio.astype(np.float32) ** 2))
        if rms == 0:
            logger.debug("Silent audio detected, skipping RMS normalization")
            return audio  # silence

        current_dbfs = 20 * np.log10(rms / 32768.0)
        gain_db = self.target_dbfs - current_dbfs
        gain = 10 ** (gain_db / 20)

        logger.debug(
            "RMS normalization applied",
            extra={
                "current_dbfs": current_dbfs,
                "target_dbfs": self.target_dbfs,
                "gain_db": gain_db,
                "gain_linear": gain,
            },
        )

        # Apply gain and clip to prevent overflow
        boosted = np.clip(audio.astype(np.float32) * gain, -32768, 32767)
        return boosted.astype(np.int16)

    def _should_process_buffer(self) -> bool:
        """
        Check if the current buffer should be processed.

        Returns:
            True if buffer should be processed, False otherwise
        """
        buffer_duration_ms = (len(self._audio_buffer) / self.sample_rate) * 1000
        return buffer_duration_ms >= self.chunk_duration_ms

    async def _transcribe_audio(
        self, audio_data: np.ndarray
    ) -> Optional[Tuple[str, float]]:
        """
        Transcribe audio data using Moonshine.

        Args:
            audio_data: Audio data as float32 array

        Returns:
            Transcribed text or None if transcription failed
        """
        try:
            # Check minimum audio length
            audio_duration_ms = (len(audio_data) / self.sample_rate) * 1000
            if audio_duration_ms < self.min_audio_length_ms:
                logger.debug(
                    "Audio too short for transcription",
                    extra={
                        "duration_ms": audio_duration_ms,
                        "min_duration_ms": self.min_audio_length_ms,
                    },
                )
                return None

            # Create a temporary file for Moonshine
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name

            try:
                # Save audio to temporary file as 16-bit PCM WAV
                # Moonshine was trained on 16-bit PCM, not float32 WAV

                # Ensure we're saving at the correct sample rate for Moonshine
                if self.sample_rate != 16000:
                    logger.warning(
                        f"Moonshine expects 16kHz audio, but saving at {self.sample_rate}Hz"
                    )

                # Convert float32 audio back to int16 for proper WAV format
                # audio_data is already float32 in range [-1, 1]
                audio_int16 = (audio_data * 32768.0).astype(np.int16)

                # Apply RMS normalization to boost audio to optimal level for Moonshine
                audio_int16 = self._rms_normalise(audio_int16)

                logger.debug(
                    "Saving audio for Moonshine transcription",
                    extra={
                        "sample_rate": self.sample_rate,
                        "audio_shape": audio_int16.shape,
                        "audio_duration_ms": audio_duration_ms,
                        "temp_file": temp_path,
                        "format": "16-bit PCM WAV",
                        "rms_normalized": True,
                        "target_dbfs": self.target_dbfs,
                    },
                )

                # Use soundfile to guarantee 16-bit PCM format
                sf.write(
                    temp_path,
                    audio_int16,
                    self.sample_rate,
                    subtype="PCM_16",  # Forces 16-bit signed little-endian
                )

                # Transcribe using Moonshine ONNX
                start_time = time.time()
                result = moonshine.transcribe(temp_path, self.model_name)
                processing_time = time.time() - start_time

                # Moonshine returns a list of strings
                if result and len(result) > 0:
                    text = " ".join(result).strip()
                    if text:
                        logger.debug(
                            "Transcription completed",
                            extra={
                                "text_length": len(text),
                                "processing_time_ms": processing_time * 1000,
                                "audio_duration_ms": audio_duration_ms,
                                "real_time_factor": (processing_time * 1000)
                                / audio_duration_ms,
                            },
                        )
                        return text, processing_time * 1000
                    else:
                        logger.debug("Empty transcription result")
                        return None
                else:
                    logger.debug("No transcription result")
                    return None

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

        except Exception as e:
            logger.error("Error during transcription", exc_info=e)
            return None

    async def _process_audio_impl(
        self, pcm_data: PcmData, user_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Tuple[bool, str, Dict[str, Any]]]]:
        """
        Process audio data through Moonshine for transcription.

        Args:
            pcm_data: The PCM audio data to process.
            user_metadata: Additional metadata about the user or session.

        Returns:
            List of tuples (is_final, text, metadata) representing transcription results,
            or None if no results are available.
        """
        if self._is_closed:
            logger.warning("Moonshine STT is closed, ignoring audio")
            return None

        # Store the current user context
        self._current_user = user_metadata

        async with self._buffer_lock:
            try:
                # Log incoming audio details for debugging
                logger.debug(
                    "Processing audio chunk",
                    extra={
                        "input_sample_rate": pcm_data.sample_rate,
                        "target_sample_rate": self.sample_rate,
                        "input_format": pcm_data.format,
                        "samples_type": type(pcm_data.samples).__name__,
                        "samples_length": len(pcm_data.samples),
                        "duration_ms": (len(pcm_data.samples) / pcm_data.sample_rate)
                        * 1000
                        if pcm_data.sample_rate > 0
                        else 0,
                    },
                )

                # Convert PCM data to numpy array
                if isinstance(pcm_data.samples, bytes):
                    # Convert bytes to numpy array
                    audio_array = np.frombuffer(pcm_data.samples, dtype=np.int16)
                else:
                    # Assume it's already a numpy array
                    audio_array = pcm_data.samples.astype(np.int16)

                # Validate and resample if needed
                if pcm_data.sample_rate != self.sample_rate:
                    if pcm_data.sample_rate == 48000 and self.sample_rate == 16000:
                        # This is the expected WebRTC -> Moonshine conversion
                        logger.debug(
                            "Converting WebRTC audio (48kHz) to Moonshine format (16kHz)"
                        )
                    else:
                        logger.warning(
                            f"Unexpected sample rate conversion: {pcm_data.sample_rate}Hz -> {self.sample_rate}Hz"
                        )

                    audio_array = resample_audio(
                        audio_array, pcm_data.sample_rate, self.sample_rate
                    ).astype(np.int16)
                else:
                    logger.debug("No resampling needed - sample rates match")

                # Add to buffer
                self._audio_buffer = np.concatenate([self._audio_buffer, audio_array])

                # Check if we should process the buffer
                if not self._should_process_buffer():
                    return None

                # Process the current buffer
                buffer_to_process = self._audio_buffer.copy()

                # Keep some overlap for better transcription continuity
                overlap_samples = int(self.sample_rate * 0.1)  # 100ms overlap
                if len(self._audio_buffer) > overlap_samples:
                    self._audio_buffer = self._audio_buffer[-overlap_samples:]
                else:
                    self._audio_buffer = np.array([], dtype=np.int16)

                # Normalize audio for Moonshine
                normalized_audio = self._normalize_audio(buffer_to_process)

                # Transcribe the audio
                result = await self._transcribe_audio(normalized_audio)

                if result:
                    # Handle both tuple (text, processing_time) and string returns for backward compatibility
                    if isinstance(result, tuple):
                        text, processing_time_ms = result
                    else:
                        text = result
                        processing_time_ms = 0.0  # Default for mocked tests

                    # Create metadata
                    metadata = {
                        "model_name": self.model_name,
                        "audio_duration_ms": (len(buffer_to_process) / self.sample_rate)
                        * 1000,
                        "processing_time_ms": processing_time_ms,
                        "confidence": 1.0,  # Moonshine doesn't provide confidence scores
                        "original_sample_rate": pcm_data.sample_rate,
                        "target_sample_rate": self.sample_rate,
                        "resampled": pcm_data.sample_rate != self.sample_rate,
                    }

                    # Return as final transcript (Moonshine doesn't support streaming)
                    return [(True, text, metadata)]

                return None

            except Exception as e:
                logger.error("Error processing audio", exc_info=e)
                # Emit error event
                self.emit("error", e)
                return None

    async def flush(self):
        """
        Flush any remaining audio in the buffer and process it.
        """
        if self._is_closed:
            return

        async with self._buffer_lock:
            if len(self._audio_buffer) > 0:
                logger.debug(
                    "Flushing remaining audio buffer",
                    extra={"buffer_samples": len(self._audio_buffer)},
                )

                # Process remaining buffer
                buffer_to_process = self._audio_buffer.copy()
                self._audio_buffer = np.array([], dtype=np.int16)

                # Normalize audio for Moonshine
                normalized_audio = self._normalize_audio(buffer_to_process)

                # Transcribe the audio
                result = await self._transcribe_audio(normalized_audio)

                if result:
                    # Handle both tuple (text, processing_time) and string returns for backward compatibility
                    if isinstance(result, tuple):
                        text, processing_time_ms = result
                    else:
                        text = result
                        processing_time_ms = 0.0  # Default for mocked tests

                    # Create metadata
                    metadata = {
                        "model_name": self.model_name,
                        "audio_duration_ms": (len(buffer_to_process) / self.sample_rate)
                        * 1000,
                        "processing_time_ms": processing_time_ms,
                        "confidence": 1.0,
                        "from_flush": True,
                    }

                    # Emit final transcript
                    self.emit("transcript", text, self._current_user, metadata)

    async def close(self):
        """Close the Moonshine STT service and clean up resources."""
        if self._is_closed:
            logger.debug("Moonshine STT service already closed")
            return

        logger.info("Closing Moonshine STT service")
        self._is_closed = True

        # Flush any remaining audio
        await self.flush()

        # Clear the buffer
        async with self._buffer_lock:
            self._audio_buffer = np.array([], dtype=np.int16)

        logger.debug("Moonshine STT service closed successfully")
