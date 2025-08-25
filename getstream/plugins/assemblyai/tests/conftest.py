import os

import numpy as np
import pytest

from getstream.video.rtc.track_util import PcmData


@pytest.fixture(scope="session")
def assemblyai_api_key():
    """Get the AssemblyAI API key from environment variables."""
    api_key = os.environ.get("ASSEMBLYAI_API_KEY")
    if not api_key:
        pytest.skip(
            "ASSEMBLYAI_API_KEY environment variable not set. Add it to your .env file."
        )
    return api_key


@pytest.fixture
def mock_assemblyai_api_key():
    """Provide a mock API key for unit tests that don't need real API access."""
    return "test_api_key_12345"


@pytest.fixture(scope="session")
def assemblyai_language():
    """Get the AssemblyAI language from environment variables."""
    return os.environ.get("ASSEMBLYAI_LANGUAGE", "en")


@pytest.fixture(scope="session")
def assemblyai_sample_rate():
    """Get the AssemblyAI sample rate from environment variables."""
    return int(os.environ.get("ASSEMBLYAI_SAMPLE_RATE", "48000"))


@pytest.fixture
def sample_audio_data():
    """Create realistic sample audio data for testing."""
    # Generate 1 second of audio at 48kHz (sine wave)
    sample_rate = 48000
    duration = 1.0  # seconds
    frequency = 440  # Hz (A note)
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    samples = (np.sin(2 * np.pi * frequency * t) * 16384).astype(np.int16)
    
    return PcmData(format="s16", samples=samples, sample_rate=sample_rate)


@pytest.fixture
def sample_audio_data_16k():
    """Create realistic sample audio data at 16kHz for testing."""
    # Generate 1 second of audio at 16kHz (sine wave)
    sample_rate = 16000
    duration = 1.0  # seconds
    frequency = 440  # Hz (A note)
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    samples = (np.sin(2 * np.pi * frequency * t) * 16384).astype(np.int16)
    
    return PcmData(format="s16", samples=samples, sample_rate=sample_rate)


@pytest.fixture
def mock_transcription_response():
    """Mock transcription response data."""
    return {
        "text": "Hello world, this is a test transcription.",
        "confidence": 0.95,
        "words": [
            {"text": "Hello", "start": 0, "end": 0.5, "confidence": 0.98},
            {"text": "world", "start": 0.5, "end": 1.0, "confidence": 0.96},
            {"text": "this", "start": 1.0, "end": 1.3, "confidence": 0.94},
            {"text": "is", "start": 1.3, "end": 1.5, "confidence": 0.97},
            {"text": "a", "start": 1.5, "end": 1.6, "confidence": 0.99},
            {"text": "test", "start": 1.6, "end": 2.0, "confidence": 0.93},
            {"text": "transcription", "start": 2.0, "end": 2.8, "confidence": 0.92}
        ],
        "audio_start": 0,
        "audio_end": 2.8
    }


@pytest.fixture
def mock_partial_transcription():
    """Mock partial transcription response data."""
    return {
        "text": "Hello world, this is",
        "confidence": 0.94,
        "words": [
            {"text": "Hello", "start": 0, "end": 0.5, "confidence": 0.98},
            {"text": "world", "start": 0.5, "end": 1.0, "confidence": 0.96},
            {"text": "this", "start": 1.0, "end": 1.3, "confidence": 0.94},
            {"text": "is", "start": 1.3, "end": 1.5, "confidence": 0.97}
        ],
        "audio_start": 0,
        "audio_end": 1.5
    }


@pytest.fixture
def mock_error_response():
    """Mock error response data."""
    return {
        "error": "Invalid audio format",
        "code": "INVALID_AUDIO_FORMAT",
        "details": "The provided audio data is not in a supported format."
    }
