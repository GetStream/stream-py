import asyncio
import pytest
import numpy as np
from unittest.mock import Mock
import logging

from getstream.video.rtc.track_util import (
    AudioTrackHandler,
    PcmData,
    AudioRingBuffer,
    AudioSegmentCollector,
    AudioFormat,
)
import getstream.video.rtc.track_util as track_util


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

    def to_ndarray(self, format=AudioFormat.S16):
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


@pytest.fixture
def _monkeypatch_audio_frame(monkeypatch):
    """Monkey-patch `track_util.av.AudioFrame` so `isinstance(..., av.AudioFrame)`
    succeeds for the real PyAV class *and* any duck-typed test double that
    exposes the minimal interface we rely on (``sample_rate``, ``layout``,
    and ``to_ndarray``).  This covers both ``MockAudioFrame`` and ad-hoc
    classes like ``BrokenAudioFrame`` defined inside individual tests.

    Note: This fixture is NOT auto-used because some tests (like resampling tests)
    need the real PyAV AudioFrame.from_ndarray method.
    """

    real_audio_frame_cls = track_util.av.AudioFrame

    class _AudioFrameMeta(type):
        def __instancecheck__(cls, instance):  # type: ignore[override]
            # Real PyAV frames pass straight through.
            if isinstance(instance, real_audio_frame_cls):
                return True

            # Duck-typed fallback used by tests.
            return (
                hasattr(instance, "sample_rate")
                and hasattr(instance, "layout")
                and callable(getattr(instance, "to_ndarray", None))
            )

    class _AudioFrame(metaclass=_AudioFrameMeta):
        pass

    monkeypatch.setattr(track_util.av, "AudioFrame", _AudioFrame, raising=True)


@pytest.mark.asyncio
async def test_audio_track_handler_initialization(_monkeypatch_audio_frame):
    """Test that AudioTrackHandler can be initialized properly."""
    mock_track = MockAudioTrack()
    callback = Mock()

    handler = AudioTrackHandler(mock_track, callback)

    assert handler.track == mock_track
    assert handler._on_audio_frame == callback
    assert handler._task is None
    assert handler._stopped is False


@pytest.mark.asyncio
async def test_audio_track_handler_start_stop(_monkeypatch_audio_frame):
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
async def test_run_track_mono_audio(_monkeypatch_audio_frame):
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
async def test_run_track_stereo_audio(_monkeypatch_audio_frame):
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
async def test_run_track_wrong_sample_rate(_monkeypatch_audio_frame):
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
async def test_run_track_cancelled_error(_monkeypatch_audio_frame):
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
async def test_run_track_general_exception(_monkeypatch_audio_frame):
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
async def test_run_track_to_ndarray_error(_monkeypatch_audio_frame):
    """Test _run_track handles to_ndarray method errors (PyAV compatibility issue)."""

    # Create a mock frame that raises an error when to_ndarray is called
    class BrokenAudioFrame:
        def __init__(self):
            self.sample_rate = 48000
            self.layout = Mock()
            self.layout.channels = [Mock()]  # Single channel

        def to_ndarray(self, format=AudioFormat.S16):
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


class TestPcmDataChunking:
    """Test PcmData chunking and sliding window methods."""

    def test_chunks_basic(self):
        """Test basic chunking functionality."""
        # Create test audio with 10 samples
        samples = np.arange(10, dtype=np.int16)
        pcm = PcmData(
            samples=samples, sample_rate=16000, format=AudioFormat.S16, channels=1
        )

        # Get chunks of size 4
        chunks = list(pcm.chunks(4))

        # Should have 3 chunks: [0:4], [4:8], [8:10]
        assert len(chunks) == 3

        # Check first chunk
        np.testing.assert_array_equal(
            chunks[0].samples, np.array([0, 1, 2, 3], dtype=np.int16)
        )
        assert chunks[0].sample_rate == 16000
        assert chunks[0].format == "s16"

        # Check second chunk
        np.testing.assert_array_equal(
            chunks[1].samples, np.array([4, 5, 6, 7], dtype=np.int16)
        )

        # Check third chunk (partial)
        np.testing.assert_array_equal(
            chunks[2].samples, np.array([8, 9], dtype=np.int16)
        )

    def test_chunks_with_overlap(self):
        """Test chunking with overlap."""
        samples = np.arange(10, dtype=np.int16)
        pcm = PcmData(
            samples=samples, sample_rate=16000, format=AudioFormat.S16, channels=1
        )

        # Get chunks of size 4 with overlap of 2
        chunks = list(pcm.chunks(4, overlap=2))

        # Should have chunks: [0:4], [2:6], [4:8], [6:10], [8:10]
        assert len(chunks) == 5

        np.testing.assert_array_equal(
            chunks[0].samples, np.array([0, 1, 2, 3], dtype=np.int16)
        )
        np.testing.assert_array_equal(
            chunks[1].samples, np.array([2, 3, 4, 5], dtype=np.int16)
        )
        np.testing.assert_array_equal(
            chunks[2].samples, np.array([4, 5, 6, 7], dtype=np.int16)
        )
        np.testing.assert_array_equal(
            chunks[3].samples, np.array([6, 7, 8, 9], dtype=np.int16)
        )
        np.testing.assert_array_equal(
            chunks[4].samples, np.array([8, 9], dtype=np.int16)
        )  # Final partial chunk

    def test_chunks_with_padding(self):
        """Test chunking with padding for the last chunk."""
        samples = np.arange(10, dtype=np.int16)
        pcm = PcmData(
            samples=samples, sample_rate=16000, format=AudioFormat.S16, channels=1
        )

        # Get chunks of size 4 with padding
        chunks = list(pcm.chunks(4, pad_last=True))

        # Should have 3 chunks, last one padded
        assert len(chunks) == 3

        # Last chunk should be padded with zeros
        np.testing.assert_array_equal(
            chunks[2].samples, np.array([8, 9, 0, 0], dtype=np.int16)
        )

    def test_chunks_stereo(self):
        """Test chunking with stereo audio."""
        # Create stereo samples (2 channels, 8 samples each)
        left_channel = np.arange(8, dtype=np.int16)
        right_channel = np.arange(8, 16, dtype=np.int16)
        samples = np.array([left_channel, right_channel])  # Shape: (2, 8)

        pcm = PcmData(
            samples=samples, sample_rate=16000, format=AudioFormat.S16, channels=2
        )

        # Get chunks of size 3
        chunks = list(pcm.chunks(3))

        # Should have 3 chunks: samples 0-2, 3-5, 6-7
        assert len(chunks) == 3

        # Check first chunk maintains stereo
        assert chunks[0].channels == 2
        assert chunks[0].samples.shape == (2, 3)
        np.testing.assert_array_equal(
            chunks[0].samples[0], np.array([0, 1, 2], dtype=np.int16)
        )
        np.testing.assert_array_equal(
            chunks[0].samples[1], np.array([8, 9, 10], dtype=np.int16)
        )

    def test_sliding_window(self):
        """Test sliding window functionality."""
        # Create 800 samples (50ms at 16kHz)
        samples = np.arange(800, dtype=np.int16)
        pcm = PcmData(
            samples=samples, sample_rate=16000, format=AudioFormat.S16, channels=1
        )

        # 25ms window = 400 samples, 10ms hop = 160 samples
        windows = list(pcm.sliding_window(25.0, 10.0))

        # Calculate expected number of windows
        # With 800 samples, 400-sample windows, 160-sample hop:
        # Windows start at: 0, 160, 320, 480, 640
        # Last full window starts at 400 (ends at 800)
        assert len(windows) >= 3

        # Check first window
        assert len(windows[0].samples) == 400
        assert windows[0].samples[0] == 0

        # Check second window (should start at 160)
        assert len(windows[1].samples) == 400
        assert windows[1].samples[0] == 160

    def test_sliding_window_with_padding(self):
        """Test sliding window with padding."""
        samples = np.arange(500, dtype=np.int16)
        pcm = PcmData(
            samples=samples, sample_rate=16000, format=AudioFormat.S16, channels=1
        )

        # 25ms window = 400 samples, 15ms hop = 240 samples
        windows = list(pcm.sliding_window(25.0, 15.0, pad_last=True))

        # Windows start at: 0, 240, 480
        # Last window needs padding
        assert len(windows) == 3

        # Last window should be padded
        assert len(windows[-1].samples) == 400
        # Check that padding with zeros occurred
        assert windows[-1].samples[-1] == 0  # Last value should be 0 (padded)


class TestAudioRingBuffer:
    """Test AudioRingBuffer functionality."""

    def test_basic(self):
        """Test basic ring buffer functionality."""
        # Create buffer for 100ms at 16kHz = 1600 samples
        buffer = AudioRingBuffer(
            max_duration_ms=100, sample_rate=16000, format=AudioFormat.F32
        )

        # Add some samples
        pcm1 = PcmData(
            samples=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            sample_rate=16000,
            format=AudioFormat.F32,
            channels=1,
        )
        buffer.append(pcm1)

        # Check buffer contents
        result = buffer.to_pcm()
        np.testing.assert_array_equal(
            result.samples, np.array([1.0, 2.0, 3.0], dtype=np.float32)
        )
        assert result.sample_rate == 16000
        assert result.format == "f32"

    def test_overflow(self):
        """Test ring buffer overflow behavior."""
        # Create small buffer for 10ms at 1000Hz = 10 samples
        buffer = AudioRingBuffer(
            max_duration_ms=10, sample_rate=1000, format=AudioFormat.F32
        )

        # Add more samples than buffer can hold
        pcm = PcmData(
            samples=np.arange(15, dtype=np.float32),
            sample_rate=1000,
            format=AudioFormat.F32,
            channels=1,
        )
        buffer.append(pcm)

        # Buffer should only contain last 10 samples (5-14)
        result = buffer.to_pcm()
        assert len(result.samples) == 10
        np.testing.assert_array_equal(
            result.samples, np.arange(5, 15, dtype=np.float32)
        )

    def test_resampling(self):
        """Test ring buffer with automatic resampling."""
        # Create buffer at 16kHz
        buffer = AudioRingBuffer(
            max_duration_ms=100, sample_rate=16000, format=AudioFormat.F32
        )

        # Add audio at different sample rate (48kHz)
        # Using simple values that survive resampling
        pcm_48k = PcmData(
            samples=np.ones(480, dtype=np.float32),
            sample_rate=48000,
            format=AudioFormat.F32,
            channels=1,
        )
        buffer.append(pcm_48k)

        # Result should be at 16kHz
        result = buffer.to_pcm()
        assert result.sample_rate == 16000
        # After resampling 480 samples at 48kHz -> ~160 samples at 16kHz
        # Allowing wider range due to resampler implementation details
        assert 140 <= len(result.samples) <= 170

    def test_format_conversion(self):
        """Test ring buffer with format conversion."""
        # Create f32 buffer
        buffer = AudioRingBuffer(
            max_duration_ms=100, sample_rate=16000, format=AudioFormat.F32
        )

        # Add s16 audio
        pcm_s16 = PcmData(
            samples=np.array([16384, -16384], dtype=np.int16),
            sample_rate=16000,
            format=AudioFormat.S16,
            channels=1,
        )
        buffer.append(pcm_s16)

        # Result should be f32 with scaled values
        result = buffer.to_pcm()
        assert result.format == "f32"
        # 16384 / 32768 = 0.5, -16384 / 32768 = -0.5
        np.testing.assert_allclose(
            result.samples, np.array([0.5, -0.5], dtype=np.float32), rtol=1e-4
        )

    def test_clear(self):
        """Test clearing the ring buffer."""
        buffer = AudioRingBuffer(
            max_duration_ms=100, sample_rate=16000, format=AudioFormat.F32
        )

        # Add samples
        pcm = PcmData(
            samples=np.array([1, 2, 3], dtype=np.float32),
            sample_rate=16000,
            format=AudioFormat.F32,
            channels=1,
        )
        buffer.append(pcm)

        # Clear buffer
        buffer.clear()

        # Buffer should be empty
        result = buffer.to_pcm()
        assert len(result.samples) == 0

    def test_duration(self):
        """Test duration calculation."""
        buffer = AudioRingBuffer(
            max_duration_ms=100, sample_rate=1000, format=AudioFormat.F32
        )

        # Add 50 samples at 1000Hz = 50ms
        pcm = PcmData(
            samples=np.ones(50, dtype=np.float32),
            sample_rate=1000,
            format=AudioFormat.F32,
            channels=1,
        )
        buffer.append(pcm)

        assert buffer.duration_ms == 50.0


class TestAudioSegmentCollector:
    """Test AudioSegmentCollector functionality."""

    def test_basic(self):
        """Test basic segment collection."""
        collector = AudioSegmentCollector(
            pre_speech_ms=20,  # Small values for testing
            post_speech_ms=30,
            sample_rate=1000,  # 1kHz for simple calculations
            format=AudioFormat.F32,
        )

        # Create test chunks
        silence_chunk = PcmData(
            samples=np.zeros(10, dtype=np.float32),
            sample_rate=1000,
            format=AudioFormat.F32,
            channels=1,
        )
        speech_chunk = PcmData(
            samples=np.ones(10, dtype=np.float32),
            sample_rate=1000,
            format=AudioFormat.F32,
            channels=1,
        )

        # Add pre-speech silence
        result = collector.add_chunk(silence_chunk, is_speech=False)
        assert result is None

        # Start speech - should not return segment yet
        result = collector.add_chunk(speech_chunk, is_speech=True)
        assert result is None
        assert collector.is_collecting is True

        # Add more speech
        result = collector.add_chunk(speech_chunk, is_speech=True)
        assert result is None

        # Add silence (not enough to trigger end)
        result = collector.add_chunk(silence_chunk, is_speech=False)
        assert result is None

        # Add more silence to trigger segment end (30ms = 30 samples at 1kHz)
        for _ in range(3):  # 30 samples total
            result = collector.add_chunk(silence_chunk, is_speech=False)
            if result is not None:
                break

        # Should have returned a segment
        assert result is not None
        assert isinstance(result, PcmData)
        # Segment should include pre-buffer, speech, and trailing silence
        assert len(result.samples) > 20  # At least pre-buffer + speech

    def test_max_duration(self):
        """Test max duration limit."""
        collector = AudioSegmentCollector(
            pre_speech_ms=10,
            post_speech_ms=1000,  # Long post-speech so it doesn't trigger
            max_duration_s=0.1,  # 100ms max
            sample_rate=1000,
            format=AudioFormat.F32,
        )

        speech_chunk = PcmData(
            samples=np.ones(20, dtype=np.float32),
            sample_rate=1000,
            format=AudioFormat.F32,
            channels=1,
        )

        # Start collecting
        collector.add_chunk(speech_chunk, is_speech=True)

        # Add chunks until max duration is reached
        result = None
        for _ in range(10):  # Add up to 200ms of audio
            result = collector.add_chunk(speech_chunk, is_speech=True)
            if result is not None:
                break

        # Should have hit max duration
        assert result is not None
        # Max 100 samples + 10 pre-buffer samples = 110 samples
        assert len(result.samples) <= 110

    def test_pre_buffer(self):
        """Test that pre-buffer is included in segment."""
        collector = AudioSegmentCollector(
            pre_speech_ms=20,
            post_speech_ms=20,
            sample_rate=1000,
            format=AudioFormat.F32,
        )

        # Add identifiable pre-speech samples
        pre_speech = PcmData(
            samples=np.full(20, -1.0, dtype=np.float32),
            sample_rate=1000,
            format=AudioFormat.F32,
            channels=1,
        )
        collector.add_chunk(pre_speech, is_speech=False)

        # Add speech
        speech = PcmData(
            samples=np.ones(10, dtype=np.float32),
            sample_rate=1000,
            format=AudioFormat.F32,
            channels=1,
        )
        collector.add_chunk(speech, is_speech=True)

        # Add enough silence to end
        silence = PcmData(
            samples=np.zeros(20, dtype=np.float32),
            sample_rate=1000,
            format=AudioFormat.F32,
            channels=1,
        )
        result = collector.add_chunk(silence, is_speech=False)

        assert result is not None
        # Check that pre-buffer values are at the start
        assert result.samples[0] == -1.0  # Pre-buffer value

    def test_reset(self):
        """Test resetting the collector."""
        collector = AudioSegmentCollector(sample_rate=1000, format=AudioFormat.F32)

        # Start collecting
        speech = PcmData(
            samples=np.ones(10, dtype=np.float32),
            sample_rate=1000,
            format=AudioFormat.F32,
            channels=1,
        )
        collector.add_chunk(speech, is_speech=True)
        assert collector.is_collecting is True

        # Reset
        collector.reset()

        # Should be back to initial state
        assert collector.is_collecting is False
        assert len(collector.segment_buffer) == 0
        assert collector.silence_samples == 0

    def test_force_finish(self):
        """Test force finishing a segment."""
        collector = AudioSegmentCollector(
            sample_rate=1000, format=AudioFormat.F32, pre_speech_ms=0
        )

        # Start collecting
        speech = PcmData(
            samples=np.ones(10, dtype=np.float32),
            sample_rate=1000,
            format=AudioFormat.F32,
            channels=1,
        )
        collector.add_chunk(speech, is_speech=True)

        # Force finish
        result = collector.force_finish()

        assert result is not None
        assert len(result.samples) == 10
        assert collector.is_collecting is False

        # Force finish when not collecting should return None
        result = collector.force_finish()
        assert result is None

    def test_format_conversion(self):
        """Test segment collector with format conversion."""
        collector = AudioSegmentCollector(sample_rate=16000, format=AudioFormat.F32)

        # Add s16 audio
        s16_chunk = PcmData(
            samples=np.array([16384], dtype=np.int16),
            sample_rate=16000,
            format=AudioFormat.S16,
            channels=1,
        )

        collector.add_chunk(s16_chunk, is_speech=True)
        result = collector.force_finish()

        assert result is not None
        assert result.format == "f32"
        # Check conversion: 16384 / 32768 = 0.5
        np.testing.assert_allclose(result.samples[0], 0.5, rtol=1e-4)

    def test_resampling(self):
        """Test segment collector with resampling."""
        # Use pre_speech_ms=0 to avoid pre-buffer complications in test
        collector = AudioSegmentCollector(
            sample_rate=16000, format=AudioFormat.F32, pre_speech_ms=0
        )

        # Add 48kHz audio
        chunk_48k = PcmData(
            samples=np.ones(480, dtype=np.float32),
            sample_rate=48000,
            format=AudioFormat.F32,
            channels=1,
        )

        collector.add_chunk(chunk_48k, is_speech=True)
        result = collector.force_finish()

        assert result is not None
        assert result.sample_rate == 16000
        # 480 samples at 48kHz -> ~160 samples at 16kHz
        # Allowing wider range due to resampler implementation details
        assert 140 <= len(result.samples) <= 170


class TestPcmDataNoOpOptimizations:
    """Test that PcmData methods avoid unnecessary work when data is already in target format."""

    def test_resample_no_op_same_rate(self):
        """Test that resample() returns self when already at target sample rate."""
        pcm = PcmData(
            samples=np.array([1, 2, 3], dtype=np.int16),
            sample_rate=16000,
            format=AudioFormat.S16,
            channels=1,
        )

        # Resample to same rate should return the same object (not a copy)
        resampled = pcm.resample(16000)
        assert resampled is pcm, (
            "resample() should return self when already at target rate"
        )

    def test_resample_no_op_same_rate_and_channels(self):
        """Test that resample() returns self when rate and channels match."""
        pcm = PcmData(
            samples=np.array([[1, 2], [3, 4]], dtype=np.int16),
            sample_rate=16000,
            format=AudioFormat.S16,
            channels=2,
        )

        # Resample to same rate and channels should return the same object
        resampled = pcm.resample(16000, target_channels=2)
        assert resampled is pcm, (
            "resample() should return self when rate and channels match"
        )

    def test_resample_does_work_different_rate(self):
        """Test that resample() creates new object when rate differs."""
        # Use more realistic audio length (10ms at 16kHz = 160 samples)
        pcm = PcmData(
            samples=np.ones(160, dtype=np.int16),
            sample_rate=16000,
            format=AudioFormat.S16,
            channels=1,
        )

        # Resample to different rate should create new object
        resampled = pcm.resample(48000)
        assert resampled is not pcm, (
            "resample() should create new object for different rate"
        )
        assert resampled.sample_rate == 48000
        # 160 samples at 16kHz -> 480 samples at 48kHz
        assert len(resampled.samples) > len(pcm.samples)

    def test_resample_does_work_different_channels(self):
        """Test that resample() creates new object when channels differ."""
        pcm = PcmData(
            samples=np.array([1, 2, 3], dtype=np.int16),
            sample_rate=16000,
            format=AudioFormat.S16,
            channels=1,
        )

        # Resample to different channels should create new object
        resampled = pcm.resample(16000, target_channels=2)
        assert resampled is not pcm, (
            "resample() should create new object for different channels"
        )
        assert resampled.channels == 2

    def test_to_float32_no_op_already_f32(self):
        """Test that to_float32() returns self when already in f32 format."""
        pcm = PcmData(
            samples=np.array([0.5, -0.5], dtype=np.float32),
            sample_rate=16000,
            format=AudioFormat.F32,
            channels=1,
        )

        # Should return the same object
        converted = pcm.to_float32()
        assert converted is pcm, "to_float32() should return self when already f32"

    def test_to_float32_does_work_s16_format(self):
        """Test that to_float32() converts when format is s16."""
        pcm = PcmData(
            samples=np.array([16384, -16384], dtype=np.int16),
            sample_rate=16000,
            format=AudioFormat.S16,
            channels=1,
        )

        # Should create new object with f32 format
        converted = pcm.to_float32()
        assert converted is not pcm, "to_float32() should create new object for s16"
        assert converted.format == AudioFormat.F32
        assert converted.samples.dtype == np.float32
        # Check conversion: 16384 / 32768 = 0.5
        np.testing.assert_allclose(converted.samples, [0.5, -0.5], rtol=1e-4)

    def test_chained_operations_avoid_unnecessary_work(self):
        """Test that chaining resample().to_float32() avoids work when already correct."""
        # Create f32 audio at 16kHz
        pcm = PcmData(
            samples=np.array([0.5, -0.5, 0.25], dtype=np.float32),
            sample_rate=16000,
            format=AudioFormat.F32,
            channels=1,
        )

        # Chain operations that are already satisfied
        result = pcm.resample(16000).to_float32()

        # Both operations should be no-ops, so we get back the original object
        assert result is pcm, "Chained no-op operations should return original object"

    def test_chained_operations_do_necessary_work(self):
        """Test that chaining resample().to_float32() does work when needed."""
        # Create s16 audio at 48kHz
        pcm = PcmData(
            samples=np.ones(480, dtype=np.int16) * 16384,
            sample_rate=48000,
            format=AudioFormat.S16,
            channels=1,
        )

        # Chain operations that need work
        result = pcm.resample(16000).to_float32()

        # Should have done both conversions
        assert result is not pcm, "Should create new object when work is needed"
        assert result.sample_rate == 16000, "Should have resampled to 16kHz"
        assert result.format == AudioFormat.F32, "Should have converted to f32"
        assert result.samples.dtype == np.float32, "Samples should be float32"
        # 480 samples at 48kHz -> ~160 samples at 16kHz
        assert 140 <= len(result.samples) <= 170
