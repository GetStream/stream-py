import pytest
import numpy as np

from getstream.video.rtc.audio_track import AudioStreamTrack


@pytest.fixture
def audio_track():
    """Creates an AudioStreamTrack instance for testing."""
    return AudioStreamTrack(framerate=8000, stereo=False, format="s16")


@pytest.mark.asyncio
async def test_audio_track_empty_queue(audio_track):
    """Test that the track returns silence when the queue is empty."""
    # When queue is empty, should return silence
    frame = await audio_track.recv()

    # Check that all planes contain silence (zeros)
    for plane in frame.planes:
        # Convert buffer to numpy array to check values
        buffer_view = memoryview(plane)
        array = np.frombuffer(buffer_view, dtype=np.int16)
        assert np.all(array == 0)


@pytest.mark.asyncio
async def test_audio_track_exact_20ms(audio_track):
    """Test that the track correctly handles exactly 20ms of audio data."""
    # Calculate how many bytes are needed for 20ms of s16 mono audio at 8000Hz
    samples_for_20ms = int(0.02 * 8000)  # 20ms at 8000Hz = 160 samples
    bytes_per_sample = 2  # s16 format = 2 bytes per sample
    required_bytes = samples_for_20ms * bytes_per_sample  # 320 bytes

    # Create test data (all 1s)
    test_data = bytes([1] * required_bytes)

    # Add data to queue
    await audio_track.write(test_data)

    # Get frame from track
    frame = await audio_track.recv()

    # Verify frame has correct number of samples
    assert frame.samples == samples_for_20ms

    # Verify data in frame is our test data
    for plane in frame.planes:
        buffer_view = memoryview(plane)
        # Check that buffer contains our test values (not zeros)
        assert bytes(buffer_view) == test_data


@pytest.mark.asyncio
async def test_audio_track_less_than_20ms(audio_track):
    """Test that the track correctly pads when data is less than 20ms."""
    # Half the amount needed for 20ms
    samples_for_10ms = int(0.01 * 8000)  # 10ms at 8000Hz = 80 samples
    bytes_per_sample = 2  # s16 format = 2 bytes per sample
    data_bytes = samples_for_10ms * bytes_per_sample  # 160 bytes

    # Create test data (all 1s)
    test_data = bytes([1] * data_bytes)

    # Add data to queue
    await audio_track.write(test_data)

    # Get frame from track
    frame = await audio_track.recv()

    # Full 20ms samples expected (padded)
    samples_for_20ms = int(0.02 * 8000)
    assert frame.samples == samples_for_20ms

    # Verify first half of data is our test data and rest is silence
    for plane in frame.planes:
        buffer_view = memoryview(plane)
        buffer_bytes = bytes(buffer_view)

        # First part should match our test data
        assert buffer_bytes[:data_bytes] == test_data

        # Rest should be zeros (silence)
        assert all(b == 0 for b in buffer_bytes[data_bytes:])


@pytest.mark.asyncio
async def test_audio_track_more_than_20ms(audio_track):
    """Test that the track returns all data when more than 20ms is available."""
    # 1.5x the amount needed for 20ms
    samples_for_30ms = int(0.03 * 8000)  # 30ms at 8000Hz = 240 samples
    bytes_per_sample = 2  # s16 format = 2 bytes per sample
    data_bytes = samples_for_30ms * bytes_per_sample  # 480 bytes

    # Create test data (all 1s)
    test_data = bytes([1] * data_bytes)

    # Add data to queue
    await audio_track.write(test_data)

    # Get frame from track
    frame = await audio_track.recv()

    # Should return all samples, not just 20ms worth
    assert frame.samples == samples_for_30ms

    # Verify data in frame is our test data
    for plane in frame.planes:
        buffer_view = memoryview(plane)
        assert bytes(buffer_view) == test_data


@pytest.mark.asyncio
async def test_audio_track_flush_clears_queue_and_pending(audio_track):
    """Test that flush() clears queued data and any pending bytes so next frame is silence."""
    # Prepare 25ms of non-uniform data to force pending bytes after first recv
    samples_for_25ms = int(0.025 * 8000)  # 25ms at 8000Hz = 200 samples
    bytes_per_sample = 2  # s16 mono = 2 bytes/sample
    total_bytes = samples_for_25ms * bytes_per_sample  # 400 bytes

    # Create non-uniform payload (avoid the uniform fast-path in implementation)
    pattern = bytes(list(range(256)) + list(range(total_bytes - 256)))

    # Queue data and perform one recv to leave pending bytes internally
    await audio_track.write(pattern)
    _ = await audio_track.recv()

    # Now flush; this should clear both the queue and any pending bytes
    await audio_track.flush()

    # Next frame should be pure silence of 20ms
    frame = await audio_track.recv()

    samples_for_20ms = int(0.02 * 8000)
    assert frame.samples == samples_for_20ms

    for plane in frame.planes:
        buffer_view = memoryview(plane)
        buffer_bytes = bytes(buffer_view)
        assert all(b == 0 for b in buffer_bytes)


@pytest.mark.asyncio
async def test_audio_track_multiple_chunks(audio_track):
    """Test that the track correctly accumulates multiple chunks to reach 20ms."""
    # Calculate how many bytes for 10ms of audio
    samples_for_10ms = int(0.01 * 8000)  # 10ms at 8000Hz = 80 samples
    bytes_per_sample = 2  # s16 format = 2 bytes per sample
    chunk_bytes = samples_for_10ms * bytes_per_sample  # 160 bytes

    # Create two different test chunks (10ms each)
    chunk1 = bytes([1] * chunk_bytes)
    chunk2 = bytes([2] * chunk_bytes)

    # Add chunks to queue
    await audio_track.write(chunk1)
    await audio_track.write(chunk2)

    # Get frame from track
    frame = await audio_track.recv()

    # Full 20ms samples expected
    samples_for_20ms = int(0.02 * 8000)
    assert frame.samples == samples_for_20ms

    # Verify data in frame contains both chunks in order
    expected_data = chunk1 + chunk2
    for plane in frame.planes:
        buffer_view = memoryview(plane)
        assert bytes(buffer_view) == expected_data


@pytest.mark.asyncio
async def test_audio_track_stereo(monkeypatch):
    """Test that the track correctly handles stereo audio."""
    # Create a stereo track
    stereo_track = AudioStreamTrack(framerate=8000, stereo=True, format="s16")

    # Calculate bytes for 20ms of stereo audio
    samples_for_20ms = int(0.02 * 8000)  # 20ms at 8000Hz = 160 samples
    bytes_per_sample = (
        2 * 2
    )  # s16 stereo format = 4 bytes per sample (2 channels * 2 bytes)
    required_bytes = samples_for_20ms * bytes_per_sample  # 640 bytes

    # Create test data
    test_data = bytes([1] * required_bytes)

    # Add data to queue
    await stereo_track.write(test_data)

    # Get frame from track
    frame = await stereo_track.recv()

    # Verify frame has correct number of samples
    assert frame.samples == samples_for_20ms

    # Verify data in frame is our test data
    for plane in frame.planes:
        buffer_view = memoryview(plane)
        assert bytes(buffer_view) == test_data
