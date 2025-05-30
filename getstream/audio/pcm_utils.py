"""
Common PCM audio processing utilities for plugins.

This module provides shared utilities for audio format conversion and validation
to eliminate code duplication between STT, TTS, and VAD plugins.
"""

import logging

import numpy as np

from getstream.video.rtc.track_util import PcmData

logger = logging.getLogger(__name__)


def pcm_to_numpy_array(pcm_data: PcmData) -> np.ndarray:
    """
    Convert PcmData samples to numpy array.

    Handles both bytes and numpy array inputs, ensuring consistent int16 output.

    Args:
        pcm_data: The PCM audio data to convert

    Returns:
        numpy array of int16 audio samples

    Raises:
        ValueError: If the input format is not supported
    """
    if isinstance(pcm_data.samples, bytes):
        # Convert bytes to numpy array
        return np.frombuffer(pcm_data.samples, dtype=np.int16)
    elif isinstance(pcm_data.samples, np.ndarray):
        # Ensure it's int16 format
        return pcm_data.samples.astype(np.int16)
    else:
        raise ValueError(
            f"Unsupported samples type: {type(pcm_data.samples)}. "
            "Expected bytes or numpy.ndarray"
        )


def numpy_array_to_bytes(audio_array: np.ndarray) -> bytes:
    """
    Convert numpy audio array to bytes.

    Args:
        audio_array: numpy array of audio samples

    Returns:
        bytes representation of the audio data
    """
    # Ensure int16 format before converting to bytes
    if audio_array.dtype != np.int16:
        audio_array = audio_array.astype(np.int16)

    return audio_array.tobytes()


def validate_sample_rate_compatibility(
    input_rate: int, target_rate: int, plugin_name: str
) -> None:
    """
    Validate sample rate compatibility and log appropriate messages.

    Args:
        input_rate: Input sample rate in Hz
        target_rate: Target sample rate in Hz
        plugin_name: Name of the plugin for logging context

    Raises:
        ValueError: If sample rates are invalid (zero or negative)
    """
    if input_rate <= 0:
        raise ValueError(f"Invalid input sample rate: {input_rate}Hz")

    if target_rate <= 0:
        raise ValueError(f"Invalid target sample rate: {target_rate}Hz")

    if input_rate != target_rate:
        if input_rate == 48000 and target_rate == 16000:
            # This is the expected WebRTC -> plugin conversion
            logger.debug(
                f"Converting WebRTC audio (48kHz) to {plugin_name} format (16kHz)"
            )
        else:
            logger.warning(
                f"Unexpected sample rate conversion in {plugin_name}: "
                f"{input_rate}Hz -> {target_rate}Hz"
            )
    else:
        logger.debug("No resampling needed - sample rates match")


def log_audio_processing_info(
    pcm_data: PcmData, target_rate: int, plugin_name: str
) -> None:
    """
    Log detailed audio processing information for debugging.

    Args:
        pcm_data: The PCM audio data being processed
        target_rate: Target sample rate for the plugin
        plugin_name: Name of the plugin for logging context
    """
    # Calculate duration safely
    duration_ms = 0.0
    if pcm_data.sample_rate > 0:
        if isinstance(pcm_data.samples, bytes):
            # For bytes, calculate based on int16 format (2 bytes per sample)
            num_samples = len(pcm_data.samples) // 2
        else:
            num_samples = len(pcm_data.samples)
        duration_ms = (num_samples / pcm_data.sample_rate) * 1000

    logger.debug(
        f"Processing audio chunk in {plugin_name}",
        extra={
            "plugin": plugin_name,
            "input_sample_rate": pcm_data.sample_rate,
            "target_sample_rate": target_rate,
            "input_format": pcm_data.format,
            "samples_type": type(pcm_data.samples).__name__,
            "samples_length": len(pcm_data.samples),
            "duration_ms": duration_ms,
        },
    )
