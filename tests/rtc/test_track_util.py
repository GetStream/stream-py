import asyncio
import pytest
import numpy as np
from unittest.mock import Mock
import logging

from getstream.video.rtc.track_util import AudioTrackHandler, PcmData


logger = logging.getLogger(__name__)


class MockAudioFrame:
    """Mock audio frame that simulates aiortc AudioFrame behavior."""

    def __init__(self, sample_rate=48000, samples=None, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels

        # Create mock layout with channels
        self.layout = Mock()
        self.layout.channels = [Mock() for _ in range(channels)]

        # If no samples provided, create 20ms worth of samples
        if samples is None:
            num_samples = int(sample_rate * 0.02)  # 20ms
            if channels == 1:
                samples = np.random.randint(-1000, 1000, num_samples, dtype=np.int16)
            else:
                samples = np.random.randint(
                    -1000, 1000, (num_samples, channels), dtype=np.int16
                )

        self._samples = samples

    def to_ndarray(self, format="s16"):
        """Mock the to_ndarray method that's causing issues in newer PyAV."""
        if format == "s16":
            return self._samples
        else:
            raise ValueError(f"Unsupported format: {format}")


class MockAudioTrack:
    """Mock audio track that simulates aiortc MediaStreamTrack behavior."""

    def __init__(self, frames=None, should_raise=None):
        self.frames = frames or []
        self.frame_index = 0
        self.should_raise = should_raise
        self.kind = "audio"

    async def recv(self):
        """Mock recv method that returns frames or raises exceptions."""
        if self.should_raise:
            if isinstance(self.should_raise, Exception):
                raise self.should_raise
            elif self.should_raise == "cancelled":
                raise asyncio.CancelledError()

        if self.frame_index >= len(self.frames):
            # Simulate end of stream
            raise Exception("End of stream")

        frame = self.frames[self.frame_index]
        self.frame_index += 1
        return frame


@pytest.mark.asyncio
async def test_audio_track_handler_initialization():
    """Test that AudioTrackHandler can be initialized properly."""
    mock_track = MockAudioTrack()
    callback = Mock()

    handler = AudioTrackHandler(mock_track, callback)

    assert handler.track == mock_track
    assert handler._on_audio_frame == callback
    assert handler._task is None
    assert handler._stopped is False


@pytest.mark.asyncio
async def test_audio_track_handler_start_stop():
    """Test that AudioTrackHandler can start and stop properly."""
    mock_track = MockAudioTrack()
    callback = Mock()

    handler = AudioTrackHandler(mock_track, callback)

    # Start the handler
    await handler.start()
    assert handler._task is not None

    # Stop the handler
    await handler.stop()
    assert handler._stopped is True
    assert handler._task is None


@pytest.mark.asyncio
async def test_run_track_mono_audio():
    """Test _run_track with mono audio frames."""
    # Create mock frames with mono audio
    frames = [
        MockAudioFrame(
            sample_rate=48000,
            samples=np.array([1, 2, 3, 4], dtype=np.int16),
            channels=1,
        ),
        MockAudioFrame(
            sample_rate=48000,
            samples=np.array([5, 6, 7, 8], dtype=np.int16),
            channels=1,
        ),
    ]

    mock_track = MockAudioTrack(frames=frames)
    received_data = []

    def callback(pcm_data: PcmData):
        received_data.append(pcm_data)

    handler = AudioTrackHandler(mock_track, callback)

    # Start processing
    await handler.start()

    # Wait a bit for processing
    await asyncio.sleep(0.1)

    # Stop processing
    await handler.stop()

    # Verify we received the expected data
    assert len(received_data) == 2

    # Check first frame
    assert received_data[0].sample_rate == 48000
    assert received_data[0].format == "s16"
    np.testing.assert_array_equal(
        received_data[0].samples, np.array([1, 2, 3, 4], dtype=np.int16)
    )

    # Check second frame
    assert received_data[1].sample_rate == 48000
    assert received_data[1].format == "s16"
    np.testing.assert_array_equal(
        received_data[1].samples, np.array([5, 6, 7, 8], dtype=np.int16)
    )


@pytest.mark.asyncio
async def test_run_track_stereo_audio():
    """Test _run_track with stereo audio frames (should convert to mono)."""
    # Create mock frames with stereo audio
    stereo_samples = np.array(
        [[1, 2], [3, 4], [5, 6], [7, 8]], dtype=np.int16
    )  # 4 samples, 2 channels
    frames = [
        MockAudioFrame(sample_rate=48000, samples=stereo_samples, channels=2),
    ]

    mock_track = MockAudioTrack(frames=frames)
    received_data = []

    def callback(pcm_data: PcmData):
        received_data.append(pcm_data)

    handler = AudioTrackHandler(mock_track, callback)

    # Start processing
    await handler.start()

    # Wait a bit for processing
    await asyncio.sleep(0.1)

    # Stop processing
    await handler.stop()

    # Verify we received the expected data
    assert len(received_data) == 1

    # Check that stereo was converted to mono (average of channels)
    expected_mono = np.array(
        [1.5, 3.5, 5.5, 7.5], dtype=np.int16
    )  # Average of each stereo pair
    assert received_data[0].sample_rate == 48000
    assert received_data[0].format == "s16"
    np.testing.assert_array_equal(received_data[0].samples, expected_mono)


@pytest.mark.asyncio
async def test_run_track_wrong_sample_rate():
    """Test _run_track raises error for unsupported sample rate."""
    # Create mock frame with wrong sample rate
    frames = [
        MockAudioFrame(
            sample_rate=16000,
            samples=np.array([1, 2, 3, 4], dtype=np.int16),
            channels=1,
        ),
    ]

    mock_track = MockAudioTrack(frames=frames)
    received_data = []

    def callback(pcm_data: PcmData):
        received_data.append(pcm_data)

    handler = AudioTrackHandler(mock_track, callback)

    # Start processing
    await handler.start()

    # Wait a bit for processing
    await asyncio.sleep(0.1)

    # Stop processing - this should raise TypeError due to wrong sample rate
    with pytest.raises(TypeError, match="only 48000 sample rate supported"):
        await handler.stop()


@pytest.mark.asyncio
async def test_run_track_cancelled_error():
    """Test _run_track handles CancelledError gracefully."""
    mock_track = MockAudioTrack(should_raise="cancelled")
    received_data = []

    def callback(pcm_data: PcmData):
        received_data.append(pcm_data)

    handler = AudioTrackHandler(mock_track, callback)

    # Start processing
    await handler.start()

    # Wait a bit for processing
    await asyncio.sleep(0.1)

    # Stop processing
    await handler.stop()

    # Should not have received any data due to cancellation
    assert len(received_data) == 0


@pytest.mark.asyncio
async def test_run_track_general_exception():
    """Test _run_track handles general exceptions gracefully."""
    mock_track = MockAudioTrack(should_raise=Exception("Test error"))
    received_data = []

    def callback(pcm_data: PcmData):
        received_data.append(pcm_data)

    handler = AudioTrackHandler(mock_track, callback)

    # Start processing
    await handler.start()

    # Wait a bit for processing
    await asyncio.sleep(0.1)

    # Stop processing
    await handler.stop()

    # Should not have received any data due to exception
    assert len(received_data) == 0


@pytest.mark.asyncio
async def test_run_track_to_ndarray_error():
    """Test _run_track handles to_ndarray method errors (PyAV compatibility issue)."""

    # Create a mock frame that raises an error when to_ndarray is called
    class BrokenAudioFrame:
        def __init__(self):
            self.sample_rate = 48000
            self.layout = Mock()
            self.layout.channels = [Mock()]  # Single channel

        def to_ndarray(self, format="s16"):
            raise AttributeError("'AudioFrame' object has no attribute 'to_ndarray'")

    frames = [BrokenAudioFrame()]
    mock_track = MockAudioTrack(frames=frames)
    received_data = []

    def callback(pcm_data: PcmData):
        received_data.append(pcm_data)

    handler = AudioTrackHandler(mock_track, callback)

    # Start processing
    await handler.start()

    # Wait a bit for processing
    await asyncio.sleep(0.1)

    # Stop processing
    await handler.stop()

    # Should not have received any data due to to_ndarray error
    assert len(received_data) == 0
