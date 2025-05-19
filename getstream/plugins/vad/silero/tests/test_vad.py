import os
import pytest
import asyncio
import logging
import numpy as np
import soundfile as sf
import tempfile

import torchaudio

from getstream.plugins.vad.silero import Silero
from getstream.video.rtc.track_util import PcmData
from getstream.plugins.test_utils import get_audio_asset, get_json_metadata

# Setup logging for the test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def mia_mp3_path():
    """Return the path to the mia.mp3 test file."""
    return get_audio_asset("mia.mp3")


@pytest.fixture
def mia_json_path():
    """Return the path to the mia.json metadata file."""
    return get_audio_asset("mia.json")


@pytest.fixture
def mia_metadata():
    """Load the mia.json metadata."""
    return get_json_metadata("mia.json")


@pytest.fixture
def mia_wav_path(mia_mp3_path):
    """Convert the mp3 to wav for testing."""
    # Create a temporary wav file
    fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)

    # Convert mp3 to wav using torchaudio
    waveform, sample_rate = torchaudio.load(mia_mp3_path)
    torchaudio.save(wav_path, waveform, sample_rate)

    yield wav_path

    # Clean up temporary file
    if os.path.exists(wav_path):
        os.remove(wav_path)


@pytest.fixture
def audio_data(mia_wav_path):
    """Load and prepare the audio data for testing."""
    # Load audio file
    data, sample_rate = sf.read(mia_wav_path)

    # Convert to mono if stereo
    if len(data.shape) > 1 and data.shape[1] > 1:
        data = np.mean(data, axis=1)

    return data, sample_rate


@pytest.fixture
def vad_setup():
    """Create a Silero VAD instance with standard test configuration."""
    vad = Silero(
        sample_rate=16000,  # Use the model's native sample rate
        speech_pad_ms=400,  # Increase padding to connect nearby speech segments
        min_speech_ms=100,  # Keep minimum low to catch shorter segments
        silence_threshold=0.2,  # Lower threshold for more sensitivity
    )

    # Storage for detected segments
    detected_segments = []

    return vad, detected_segments


async def process_audio_file(vad, data, original_sample_rate, detected_segments):
    """Process audio data with VAD and collect detected speech segments."""

    # Register event handler to collect speech segments
    @vad.on("audio")
    async def on_audio(pcm_data: PcmData, user):
        # Use the duration property instead of calling it as a method
        duration = pcm_data.duration
        detected_segments.append({"duration": duration, "bytes": len(pcm_data.samples)})
        logger.info(
            f"Detected speech segment: {duration:.2f} seconds ({len(pcm_data.samples)} bytes)"
        )

    # Resample if needed
    if original_sample_rate != vad.sample_rate:
        import scipy.signal

        num_samples = int(len(data) * vad.sample_rate / original_sample_rate)
        data = scipy.signal.resample(data, num_samples)

    # Convert to int16 PCM
    pcm_samples = (data * 32768.0).astype(np.int16)

    # Process the audio data
    await vad.process_audio(
        PcmData(samples=pcm_samples, sample_rate=vad.sample_rate, format="s16")
    )

    # Ensure we flush any remaining speech
    await vad._flush_speech_buffer()

    # Add a small delay to allow all events to be processed
    await asyncio.sleep(0.1)


async def process_audio_in_chunks(
    vad, data, original_sample_rate, detected_segments, chunk_size_ms=20
):
    """Process audio data in small chunks to simulate streaming."""

    # Register event handler to collect speech segments
    @vad.on("audio")
    async def on_audio(pcm_data: PcmData, user):
        # Use the duration property instead of calling it as a method
        duration = pcm_data.duration
        detected_segments.append({"duration": duration, "bytes": len(pcm_data.samples)})
        logger.info(
            f"Detected speech segment: {duration:.2f} seconds ({len(pcm_data.samples)} bytes)"
        )

    # Resample if needed
    if original_sample_rate != vad.sample_rate:
        import scipy.signal

        num_samples = int(len(data) * vad.sample_rate / original_sample_rate)
        data = scipy.signal.resample(data, num_samples)

    # Calculate chunk size in samples for the target sample rate
    chunk_samples = int(vad.sample_rate * chunk_size_ms / 1000)
    logger.info(
        f"Processing audio in {chunk_size_ms}ms chunks ({chunk_samples} samples per chunk)"
    )

    # Process audio in chunks
    for i in range(0, len(data), chunk_samples):
        # Extract chunk
        chunk = data[i : i + chunk_samples]

        # Pad last chunk if needed
        if len(chunk) < chunk_samples:
            padded_chunk = np.zeros(chunk_samples)
            padded_chunk[: len(chunk)] = chunk
            chunk = padded_chunk

        # Convert to int16 PCM
        chunk_pcm = (chunk * 32768.0).astype(np.int16)

        # Process the chunk
        await vad.process_audio(
            PcmData(samples=chunk_pcm, sample_rate=vad.sample_rate, format="s16")
        )

        # Add a small delay to simulate real-time processing
        await asyncio.sleep(0.001)

    # Ensure we flush any remaining speech
    await vad._flush_speech_buffer()

    # Add a small delay to allow all events to be processed
    await asyncio.sleep(0.1)


def verify_detected_speech(detected_segments, expected_duration, tolerance=0.55):
    """Verify that the detected speech matches expectations."""
    # Verify that speech was detected
    assert len(detected_segments) > 0, "No speech segments were detected"

    # Calculate total detected duration
    total_detected_duration = sum(segment["duration"] for segment in detected_segments)

    # Calculate expected range
    min_expected = expected_duration * (1 - tolerance)
    max_expected = expected_duration * (1 + tolerance)

    logger.info(f"Expected speech duration: {expected_duration:.2f} seconds")
    logger.info(f"Detected speech duration: {total_detected_duration:.2f} seconds")

    if len(detected_segments) > 0:
        logger.info(f"Number of detected segments: {len(detected_segments)}")
        # Log the speech segments for inspection
        for i, segment in enumerate(detected_segments):
            logger.info(f"Speech segment {i+1}: {segment['duration']:.2f}s")

    # Verify that the duration is within expected range
    assert (
        min_expected <= total_detected_duration <= max_expected
    ), f"Expected speech duration {expected_duration}s, got {total_detected_duration}s"


@pytest.mark.asyncio
async def test_silero_vad_initialization():
    """Test that the Silero VAD can be initialized with default parameters."""
    vad = Silero()
    assert vad is not None
    assert vad.model is not None


@pytest.mark.asyncio
async def test_silero_vad_speech_detection(audio_data, mia_metadata, vad_setup):
    """Test that the Silero VAD can detect speech in an audio file."""
    vad, detected_segments = vad_setup
    data, sample_rate = audio_data

    # Process the entire audio file
    await process_audio_file(vad, data, sample_rate, detected_segments)

    # Verify speech detection
    expected_duration = mia_metadata["duration"]
    verify_detected_speech(detected_segments, expected_duration)


@pytest.mark.asyncio
async def test_vad_with_connection_manager_format(audio_data, vad_setup):
    """Test VAD with PCM data in bytes format."""
    vad, detected_segments = vad_setup
    data, sample_rate = audio_data

    # Resample if needed
    if sample_rate != vad.sample_rate:
        import scipy.signal

        num_samples = int(len(data) * vad.sample_rate / sample_rate)
        data = scipy.signal.resample(data, num_samples)

    # Convert to int16 PCM bytes
    pcm_bytes = (data * 32768.0).astype(np.int16).tobytes()

    @vad.on("audio")
    async def on_audio(pcm_data, user):
        # Use the duration property instead of calling it as a method
        duration = pcm_data.duration
        detected_segments.append({"duration": duration, "bytes": len(pcm_data.samples)})
        logger.info(
            f"Detected speech segment: {duration:.2f} seconds ({len(pcm_data.samples)} bytes)"
        )

    # Process the audio data as bytes
    await vad.process_audio(
        PcmData(samples=pcm_bytes, sample_rate=vad.sample_rate, format="s16")
    )

    # Ensure we flush any remaining speech
    await vad._flush_speech_buffer()

    # Add a small delay to allow all events to be processed
    await asyncio.sleep(0.1)

    # Verify that speech was detected
    assert len(detected_segments) > 0, "No speech segments were detected"
    logger.info(f"Detected {len(detected_segments)} speech segments")


@pytest.mark.asyncio
async def test_silero_vad_with_short_chunks(audio_data, mia_metadata):
    """Test that the Silero VAD works correctly with small audio chunks."""
    # Create a new VAD for this test
    vad = Silero(
        sample_rate=16000,  # Use the model's native sample rate
        speech_pad_ms=400,  # Increase padding to connect nearby speech segments
        min_speech_ms=100,  # Keep minimum low to catch shorter segments
        silence_threshold=0.2,  # Lower threshold for more sensitivity
    )
    detected_segments = []
    data, sample_rate = audio_data

    # Process the audio in small chunks to simulate streaming
    await process_audio_in_chunks(
        vad, data, sample_rate, detected_segments, chunk_size_ms=20
    )

    # Verify that speech was detected and is close to expected duration
    # We allow more tolerance when processing in chunks
    expected_duration = mia_metadata["duration"]
    verify_detected_speech(detected_segments, expected_duration, tolerance=0.6)
