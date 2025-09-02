"""
Tests for getstream.audio.pcm_utils module.

This module tests all PCM audio utility functions including conversion,
validation, and logging functionality.
"""

import logging

import numpy as np
import pytest

from getstream.audio.pcm_utils import (
    log_audio_processing_info,
    numpy_array_to_bytes,
    pcm_to_numpy_array,
    validate_sample_rate_compatibility,
)
from getstream.video.rtc.track_util import PcmData

from .utils import get_audio_asset


class TestPcmToNumpyArray:
    """Test the pcm_to_numpy_array function."""

    def test_with_bytes_input(self):
        """Test converting PcmData with bytes samples to numpy array."""
        # Create test audio data as bytes (int16 format)
        test_samples = np.array([100, -200, 300, -400, 500], dtype=np.int16)
        test_bytes = test_samples.tobytes()

        pcm_data = PcmData(format="s16", sample_rate=16000, samples=test_bytes)

        result = pcm_to_numpy_array(pcm_data)

        # Should return numpy array with correct values
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.int16
        np.testing.assert_array_equal(result, test_samples)

    def test_with_numpy_array_input(self):
        """Test converting PcmData with numpy array samples."""
        # Create test audio data as numpy array
        test_samples = np.array([100, -200, 300, -400, 500], dtype=np.int16)

        pcm_data = PcmData(format="s16", sample_rate=16000, samples=test_samples)

        result = pcm_to_numpy_array(pcm_data)

        # Should return numpy array with correct values
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.int16
        np.testing.assert_array_equal(result, test_samples)

    def test_with_float_numpy_array(self):
        """Test converting PcmData with float numpy array to int16."""
        # Create test audio data as float32 array
        test_samples = np.array([100.5, -200.3, 300.7, -400.1, 500.9], dtype=np.float32)

        pcm_data = PcmData(format="s16", sample_rate=16000, samples=test_samples)

        result = pcm_to_numpy_array(pcm_data)

        # Should return int16 array with converted values
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.int16
        expected = test_samples.astype(np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_with_unsupported_input_type(self):
        """Test that unsupported input types raise ValueError."""
        pcm_data = PcmData(
            format="s16",
            sample_rate=16000,
            samples="invalid_string_type",  # Unsupported type
        )

        with pytest.raises(ValueError) as exc_info:
            pcm_to_numpy_array(pcm_data)

        assert "Unsupported samples type" in str(exc_info.value)
        assert "Expected bytes or numpy.ndarray" in str(exc_info.value)


class TestNumpyArrayToBytes:
    """Test the numpy_array_to_bytes function."""

    def test_int16_array_conversion(self):
        """Test converting int16 numpy array to bytes."""
        test_array = np.array([100, -200, 300, -400, 500], dtype=np.int16)

        result = numpy_array_to_bytes(test_array)

        # Should return bytes that can be converted back to the same array
        assert isinstance(result, bytes)
        reconstructed = np.frombuffer(result, dtype=np.int16)
        np.testing.assert_array_equal(reconstructed, test_array)

    def test_float_array_conversion(self):
        """Test converting float array to bytes (should convert to int16 first)."""
        test_array = np.array([100.5, -200.3, 300.7, -400.1, 500.9], dtype=np.float32)

        result = numpy_array_to_bytes(test_array)

        # Should return bytes representing int16 conversion
        assert isinstance(result, bytes)
        reconstructed = np.frombuffer(result, dtype=np.int16)
        expected = test_array.astype(np.int16)
        np.testing.assert_array_equal(reconstructed, expected)

    def test_empty_array(self):
        """Test converting empty array to bytes."""
        test_array = np.array([], dtype=np.int16)

        result = numpy_array_to_bytes(test_array)

        # Should return empty bytes
        assert isinstance(result, bytes)
        assert len(result) == 0

    def test_large_array(self):
        """Test converting larger array to ensure performance."""
        # Create 1 second of audio at 16kHz
        test_array = np.random.randint(-32768, 32767, 16000, dtype=np.int16)

        result = numpy_array_to_bytes(test_array)

        # Should return correct number of bytes (2 bytes per int16 sample)
        assert isinstance(result, bytes)
        assert len(result) == len(test_array) * 2

        # Verify round-trip conversion
        reconstructed = np.frombuffer(result, dtype=np.int16)
        np.testing.assert_array_equal(reconstructed, test_array)


class TestValidateSampleRateCompatibility:
    """Test the validate_sample_rate_compatibility function."""

    def test_matching_sample_rates(self, caplog):
        """Test validation with matching sample rates."""
        with caplog.at_level(logging.DEBUG):
            validate_sample_rate_compatibility(16000, 16000, "test_plugin")

        # Should log that no resampling is needed
        assert "No resampling needed - sample rates match" in caplog.text

    def test_webrtc_to_plugin_conversion(self, caplog):
        """Test validation for expected WebRTC to plugin conversion."""
        with caplog.at_level(logging.DEBUG):
            validate_sample_rate_compatibility(48000, 16000, "test_plugin")

        # Should log the expected conversion
        assert (
            "Converting WebRTC audio (48kHz) to test_plugin format (16kHz)"
            in caplog.text
        )

    def test_unexpected_conversion(self, caplog):
        """Test validation for unexpected sample rate conversion."""
        with caplog.at_level(logging.WARNING):
            validate_sample_rate_compatibility(22050, 8000, "test_plugin")

        # Should log a warning about unexpected conversion
        assert (
            "Unexpected sample rate conversion in test_plugin: 22050Hz -> 8000Hz"
            in caplog.text
        )

    def test_invalid_input_rate(self):
        """Test validation with invalid input sample rate."""
        with pytest.raises(ValueError) as exc_info:
            validate_sample_rate_compatibility(0, 16000, "test_plugin")

        assert "Invalid input sample rate: 0Hz" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            validate_sample_rate_compatibility(-1000, 16000, "test_plugin")

        assert "Invalid input sample rate: -1000Hz" in str(exc_info.value)

    def test_invalid_target_rate(self):
        """Test validation with invalid target sample rate."""
        with pytest.raises(ValueError) as exc_info:
            validate_sample_rate_compatibility(16000, 0, "test_plugin")

        assert "Invalid target sample rate: 0Hz" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            validate_sample_rate_compatibility(16000, -8000, "test_plugin")

        assert "Invalid target sample rate: -8000Hz" in str(exc_info.value)


class TestLogAudioProcessingInfo:
    """Test the log_audio_processing_info function."""

    def test_log_with_bytes_samples(self, caplog):
        """Test logging with PcmData containing bytes samples."""
        # Create test audio data as bytes
        test_samples = np.array([100, -200, 300, -400], dtype=np.int16)
        test_bytes = test_samples.tobytes()

        pcm_data = PcmData(format="s16", sample_rate=16000, samples=test_bytes)

        with caplog.at_level(logging.DEBUG):
            log_audio_processing_info(pcm_data, 16000, "test_plugin")

        # Should log processing information
        assert "Processing audio chunk in test_plugin" in caplog.text

        # Check that log record contains expected extra fields
        records = [
            record for record in caplog.records if record.levelno == logging.DEBUG
        ]
        assert len(records) > 0

        record = records[0]
        assert hasattr(record, "plugin")
        assert record.plugin == "test_plugin"
        assert hasattr(record, "input_sample_rate")
        assert record.input_sample_rate == 16000
        assert hasattr(record, "target_sample_rate")
        assert record.target_sample_rate == 16000
        assert hasattr(record, "samples_type")
        assert record.samples_type == "bytes"
        assert hasattr(record, "duration_ms")
        assert record.duration_ms > 0  # Should calculate some duration

    def test_log_with_numpy_samples(self, caplog):
        """Test logging with PcmData containing numpy array samples."""
        # Create test audio data as numpy array
        test_samples = np.array([100, -200, 300, -400], dtype=np.int16)

        pcm_data = PcmData(format="s16", sample_rate=16000, samples=test_samples)

        with caplog.at_level(logging.DEBUG):
            log_audio_processing_info(pcm_data, 8000, "numpy_plugin")

        # Should log processing information
        assert "Processing audio chunk in numpy_plugin" in caplog.text

        # Check that log record contains expected extra fields
        records = [
            record for record in caplog.records if record.levelno == logging.DEBUG
        ]
        assert len(records) > 0

        record = records[0]
        assert record.plugin == "numpy_plugin"
        assert record.input_sample_rate == 16000
        assert record.target_sample_rate == 8000
        assert record.samples_type == "ndarray"
        assert record.duration_ms > 0

    def test_log_with_zero_sample_rate(self, caplog):
        """Test logging with zero sample rate (edge case)."""
        test_samples = np.array([100, -200, 300, -400], dtype=np.int16)

        pcm_data = PcmData(
            format="s16",
            sample_rate=0,  # Invalid sample rate
            samples=test_samples,
        )

        with caplog.at_level(logging.DEBUG):
            log_audio_processing_info(pcm_data, 16000, "edge_case_plugin")

        # Should still log but with 0 duration
        assert "Processing audio chunk in edge_case_plugin" in caplog.text

        records = [
            record for record in caplog.records if record.levelno == logging.DEBUG
        ]
        assert len(records) > 0

        record = records[0]
        assert record.duration_ms == 0.0  # Should handle gracefully

    def test_log_duration_calculation_accuracy(self, caplog):
        """Test that duration calculation is accurate."""
        # Create 1 second of audio at 16kHz (16000 samples)
        sample_rate = 16000
        test_samples = np.zeros(sample_rate, dtype=np.int16)  # 1 second worth

        pcm_data = PcmData(format="s16", sample_rate=sample_rate, samples=test_samples)

        with caplog.at_level(logging.DEBUG):
            log_audio_processing_info(pcm_data, 16000, "duration_test_plugin")

        records = [
            record for record in caplog.records if record.levelno == logging.DEBUG
        ]
        assert len(records) > 0

        record = records[0]
        # Should be approximately 1000ms (1 second)
        assert abs(record.duration_ms - 1000.0) < 1.0  # Allow small tolerance


class TestIntegrationWithRealAudio:
    """Integration tests using real audio assets."""

    def test_round_trip_conversion_with_real_audio(self):
        """Test complete round-trip conversion using real audio data."""
        import soundfile as sf

        # Load real audio asset
        audio_path = get_audio_asset("formant_speech_16k.wav")
        audio_data, sample_rate = sf.read(audio_path, dtype="int16")

        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1).astype(np.int16)

        # Create PcmData with numpy array
        pcm_data = PcmData(format="s16", sample_rate=sample_rate, samples=audio_data)

        # Convert to numpy array (should be unchanged)
        numpy_result = pcm_to_numpy_array(pcm_data)
        np.testing.assert_array_equal(numpy_result, audio_data)

        # Convert to bytes
        bytes_result = numpy_array_to_bytes(numpy_result)

        # Create PcmData with bytes
        pcm_data_bytes = PcmData(
            format="s16", sample_rate=sample_rate, samples=bytes_result
        )

        # Convert back to numpy array
        final_numpy = pcm_to_numpy_array(pcm_data_bytes)

        # Should match original data
        np.testing.assert_array_equal(final_numpy, audio_data)

    def test_validate_common_sample_rates(self):
        """Test validation with common audio sample rates."""
        common_rates = [8000, 16000, 22050, 44100, 48000]

        for input_rate in common_rates:
            for target_rate in common_rates:
                # Should not raise any exceptions
                validate_sample_rate_compatibility(
                    input_rate, target_rate, "test_plugin"
                )

    def test_processing_info_with_real_audio(self, caplog):
        """Test logging processing info with real audio data."""
        import soundfile as sf

        # Load real audio asset
        audio_path = get_audio_asset("formant_speech_16k.wav")
        audio_data, sample_rate = sf.read(audio_path, dtype="int16")

        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1).astype(np.int16)

        pcm_data = PcmData(format="s16", sample_rate=sample_rate, samples=audio_data)

        with caplog.at_level(logging.DEBUG):
            log_audio_processing_info(pcm_data, 16000, "real_audio_plugin")

        # Should log processing information with realistic duration
        assert "Processing audio chunk in real_audio_plugin" in caplog.text

        records = [
            record for record in caplog.records if record.levelno == logging.DEBUG
        ]
        assert len(records) > 0

        record = records[0]
        assert record.duration_ms > 0
        assert record.samples_length == len(audio_data)
