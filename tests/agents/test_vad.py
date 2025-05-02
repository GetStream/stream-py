import os
import json
import pytest
import asyncio
import logging
import numpy as np
import soundfile as sf
import tempfile
from typing import Dict, Any, List

import torchaudio

from getstream.agents.silero.vad import Silero
from getstream.video.rtc.track_util import PcmData

# Setup logging for the test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def mia_mp3_path():
    """Return the path to the mia.mp3 test file."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "mia.mp3")

@pytest.fixture
def mia_json_path():
    """Return the path to the mia.json metadata file."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "mia.json")

@pytest.fixture
def mia_metadata(mia_json_path):
    """Load the mia.json metadata."""
    with open(mia_json_path, 'r') as f:
        return json.load(f)

@pytest.fixture
def mia_wav_path(mia_mp3_path):
    """Convert the mp3 to wav for testing."""
    # Create a temporary wav file
    fd, wav_path = tempfile.mkstemp(suffix='.wav')
    os.close(fd)
    
    # Convert mp3 to wav using torchaudio
    waveform, sample_rate = torchaudio.load(mia_mp3_path)
    torchaudio.save(wav_path, waveform, sample_rate)
    
    yield wav_path
    
    # Clean up temporary file
    if os.path.exists(wav_path):
        os.remove(wav_path)

@pytest.mark.asyncio
async def test_silero_vad_initialization():
    """Test that the Silero VAD initializes correctly."""
    vad = Silero()
    assert vad is not None
    await vad.close()

@pytest.mark.asyncio
async def test_silero_vad_speech_detection(mia_wav_path, mia_metadata):
    """Test that the Silero VAD correctly detects speech in the mia.mp3 file."""
    # Create VAD with parameters tuned for the test
    vad = Silero(
        sample_rate=44100,
        speech_pad_ms=100,  # Shorter padding for testing
        min_speech_ms=100,  # Lower minimum to catch shorter segments
    )
    
    # Create a list to store detected speech segments
    detected_segments = []
    
    # Create an event handler to collect speech segments
    @vad.on("audio")
    async def on_audio(pcm_data, user):
        # Calculate duration in seconds
        num_samples = len(pcm_data) // 2  # 2 bytes per sample in int16
        duration = num_samples / vad.sample_rate
        
        # Store segment info
        detected_segments.append({
            "duration": duration,
            "bytes": len(pcm_data)
        })
        logger.info(f"Detected speech segment: {duration:.2f} seconds ({len(pcm_data)} bytes)")
    
    try:
        # Load audio file
        data, sample_rate = sf.read(mia_wav_path)
        
        # Convert to mono if stereo
        if len(data.shape) > 1 and data.shape[1] > 1:
            data = np.mean(data, axis=1)
        
        # Resample if needed
        if sample_rate != vad.sample_rate:
            # Simple resampling for testing purposes
            # In production, use a proper resampling library
            import scipy.signal
            num_samples = int(len(data) * vad.sample_rate / sample_rate)
            data = scipy.signal.resample(data, num_samples)
        
        # Convert to int16 PCM
        pcm_data = (data * 32768.0).astype(np.int16).tobytes()
        
        # Process the audio data
        await vad.process_audio(PcmData(samples=pcm_data, sample_rate=sample_rate, format="s16"))
        
        # Ensure we flush any remaining speech
        await vad._flush_speech_buffer()
        
        # Add a small delay to allow all events to be processed
        await asyncio.sleep(0.1)
        
        # Verify that speech was detected
        assert len(detected_segments) > 0, "No speech segments were detected"
        
        # Calculate total speech duration
        total_detected_duration = sum(segment["duration"] for segment in detected_segments)
        
        # Get expected segments from metadata
        expected_segments = mia_metadata["segments"]
        expected_duration = sum(seg["end_time"] - seg["start_time"] for seg in expected_segments)
        
        # Allow for some tolerance in duration comparison
        # VAD might detect slightly different segments than the reference
        tolerance = 0.3  # 30% tolerance
        min_expected = expected_duration * (1 - tolerance)
        max_expected = expected_duration * (1 + tolerance)
        
        logger.info(f"Expected speech duration: {expected_duration:.2f} seconds")
        logger.info(f"Detected speech duration: {total_detected_duration:.2f} seconds")
        
        # Assert that the detected duration is within tolerance
        assert min_expected <= total_detected_duration <= max_expected, \
            f"Detected duration {total_detected_duration:.2f}s not within expected range " \
            f"({min_expected:.2f}s - {max_expected:.2f}s)"
            
        # Log the speech segments for inspection
        for i, segment in enumerate(detected_segments):
            logger.info(f"Speech segment {i+1}: {segment['duration']:.2f}s")
    
    finally:
        # Clean up
        await vad.close()

@pytest.mark.asyncio
async def test_vad_with_connection_manager_format(mia_wav_path):
    """Test that the VAD works with the connection_manager's audio event format."""
    # Create VAD with default parameters
    vad = Silero()
    
    # Flag to indicate audio was received
    audio_received = asyncio.Event()
    received_audio_data = []
    
    # Create event handler similar to connection_manager
    @vad.on("audio")
    async def on_audio(pcm_data, user):
        received_audio_data.append(pcm_data)
        audio_received.set()
    
    try:
        # Load audio file
        data, sample_rate = sf.read(mia_wav_path)
        
        # Convert to mono if stereo
        if len(data.shape) > 1 and data.shape[1] > 1:
            data = np.mean(data, axis=1)
        
        # Resample if needed
        if sample_rate != vad.sample_rate:
            import scipy.signal
            num_samples = int(len(data) * vad.sample_rate / sample_rate)
            data = scipy.signal.resample(data, num_samples)
        
        # Convert to int16 PCM
        pcm_data = (data * 32768.0).astype(np.int16).tobytes()
        
        # Create user metadata similar to what connection_manager would provide
        user_metadata = {
            "user_id": "test-user",
            "session_id": "test-session"
        }
        
        # Process the audio data with user metadata
        await vad.process_audio(pcm_data, user_metadata)
        
        # Wait for audio event or timeout
        try:
            await asyncio.wait_for(audio_received.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            assert False, "No audio event was emitted within timeout"
        
        # Verify that audio was received with correct metadata
        assert len(received_audio_data) > 0, "No audio data was received"
        
    finally:
        # Clean up
        await vad.close()

@pytest.mark.asyncio
async def test_silero_vad_with_short_chunks(mia_wav_path, mia_metadata):
    """Test the Silero VAD with audio streamed in small 20ms chunks like in WebRTC."""
    # Create VAD with parameters tuned for the test
    vad = Silero(
        sample_rate=48000,  # WebRTC commonly uses 48kHz
        frame_size=512,
        silence_threshold=0.5,
        speech_pad_ms=300,
        min_speech_ms=250,
    )
    
    # Create a list to store detected speech segments
    detected_segments = []
    
    # Create an event handler to collect speech segments
    @vad.on("audio")
    async def on_audio(pcm_data: PcmData, user):
        # Calculate duration in seconds
        num_samples = len(pcm_data.samples) // 2  # 2 bytes per sample in int16
        duration = num_samples / vad.sample_rate
        
        # Store segment info
        detected_segments.append({
            "duration": duration,
            "bytes": len(pcm_data)
        })
        logger.info(f"Detected speech segment: {duration:.2f} seconds ({len(pcm_data.samples)} bytes)")
    
    try:
        # Load audio file
        data, sample_rate = sf.read(mia_wav_path)
        
        # Convert to mono if stereo
        if len(data.shape) > 1 and data.shape[1] > 1:
            data = np.mean(data, axis=1)
        
        # Resample to 48kHz if needed
        if sample_rate != vad.sample_rate:
            import scipy.signal
            num_samples = int(len(data) * vad.sample_rate / sample_rate)
            data = scipy.signal.resample(data, num_samples)
        
        # Calculate number of samples in 20ms chunk at 48kHz
        chunk_size_ms = 20
        chunk_samples = int(vad.sample_rate * chunk_size_ms / 1000)
        
        # Process audio in 20ms chunks
        logger.info(f"Processing audio in {chunk_size_ms}ms chunks ({chunk_samples} samples per chunk)")
        
        for i in range(0, len(data), chunk_samples):
            # Extract chunk
            chunk = data[i:i + chunk_samples]
            
            # Pad last chunk if needed
            if len(chunk) < chunk_samples:
                padded_chunk = np.zeros(chunk_samples)
                padded_chunk[:len(chunk)] = chunk
                chunk = padded_chunk
            
            # Convert to int16 PCM
            chunk_pcm = (chunk * 32768.0).astype(np.int16).tobytes()
            
            # Process the chunk
            await vad.process_audio(chunk_pcm)
            
            # Add a small delay to simulate real-time processing
            await asyncio.sleep(0.001)
        
        # Ensure we flush any remaining speech
        await vad._flush_speech_buffer()
        
        # Add a small delay to allow all events to be processed
        await asyncio.sleep(0.1)
        
        # Verify that speech was detected
        assert len(detected_segments) > 0, "No speech segments were detected"
        
        # Calculate total speech duration
        total_detected_duration = sum(segment["duration"] for segment in detected_segments)
        
        # Get expected segments from metadata
        expected_segments = mia_metadata["segments"]
        expected_duration = sum(seg["end_time"] - seg["start_time"] for seg in expected_segments)
        
        # Allow for some tolerance in duration comparison
        # VAD might detect slightly different segments than the reference
        tolerance = 0.5  # 50% tolerance (increased for chunked processing)
        min_expected = expected_duration * (1 - tolerance)
        max_expected = expected_duration * (1 + tolerance)
        
        logger.info(f"Expected speech duration: {expected_duration:.2f} seconds")
        logger.info(f"Detected speech duration: {total_detected_duration:.2f} seconds")
        logger.info(f"Number of detected segments: {len(detected_segments)}")
        
        # Assert that the detected duration is within tolerance
        assert min_expected <= total_detected_duration <= max_expected, \
            f"Detected duration {total_detected_duration:.2f}s not within expected range " \
            f"({min_expected:.2f}s - {max_expected:.2f}s)"
            
        # Log the speech segments for inspection
        for i, segment in enumerate(detected_segments):
            logger.info(f"Speech segment {i+1}: {segment['duration']:.2f}s")
    
    finally:
        # Clean up
        await vad.close() 