import asyncio
import time
import pytest
import numpy as np

from getstream.video.rtc.audio_track import AudioStreamTrack
from getstream.video.rtc.track_util import PcmData, AudioFormat
import aiortc


class TestAudioStreamTrack:
    """Test suite for AudioStreamTrack class."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test that AudioStreamTrack initializes with correct parameters."""
        # Default initialization
        track = AudioStreamTrack()
        assert track.sample_rate == 48000
        assert track.channels == 1
        assert track.format == "s16"
        assert track.audio_buffer_size_ms == 30000
        assert track.kind == "audio"
        assert track.readyState == "live"

        # Custom initialization
        track = AudioStreamTrack(
            sample_rate=16000,
            channels=2,
            format="f32",
            audio_buffer_size_ms=10000,
        )
        assert track.sample_rate == 16000
        assert track.channels == 2
        assert track.format == "f32"
        assert track.audio_buffer_size_ms == 10000

    @pytest.mark.asyncio
    async def test_write_and_recv_basic(self):
        """Test basic write and receive functionality."""
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        # Create 40ms of audio data (should be enough for 2 frames)
        samples_40ms = int(0.04 * 48000)  # 1920 samples
        audio_data = np.zeros(samples_40ms, dtype=np.int16)
        pcm = PcmData(
            samples=audio_data,
            sample_rate=48000,
            format=AudioFormat.S16,
            channels=1,
        )

        # Write data to track
        await track.write(pcm)

        # Receive first 20ms frame
        frame1 = await track.recv()
        assert frame1.sample_rate == 48000
        assert frame1.samples == 960  # 20ms at 48kHz
        assert frame1.format.name == "s16"
        assert len(frame1.layout.channels) == 1

        # Receive second 20ms frame
        frame2 = await track.recv()
        assert frame2.sample_rate == 48000
        assert frame2.samples == 960

    @pytest.mark.asyncio
    async def test_format_conversion(self):
        """Test that write converts formats correctly."""
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="f32")

        # Write s16 data to f32 track
        samples = np.array([100, 200, 300], dtype=np.int16)
        pcm = PcmData(
            samples=samples,
            sample_rate=48000,
            format=AudioFormat.S16,
            channels=1,
        )

        await track.write(pcm)

        # Check that buffer contains f32 data
        assert track._bytes_per_sample == 4  # f32 = 4 bytes

    @pytest.mark.asyncio
    async def test_sample_rate_conversion(self):
        """Test that write resamples audio correctly."""
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        # Write 16kHz data to 48kHz track
        samples_16k = np.zeros(320, dtype=np.int16)  # 20ms at 16kHz
        pcm = PcmData(
            samples=samples_16k,
            sample_rate=16000,
            format=AudioFormat.S16,
            channels=1,
        )

        await track.write(pcm)

        # After resampling, we should have 3x more samples (960 samples)
        expected_bytes = 960 * 2  # 960 samples * 2 bytes per s16 sample
        assert len(track._buffer) == expected_bytes

    @pytest.mark.asyncio
    async def test_channel_conversion(self):
        """Test mono to stereo and stereo to mono conversion."""
        # Test mono to stereo
        track_stereo = AudioStreamTrack(sample_rate=48000, channels=2, format="s16")

        samples_mono = np.zeros(960, dtype=np.int16)  # 20ms mono
        pcm_mono = PcmData(
            samples=samples_mono,
            sample_rate=48000,
            format=AudioFormat.S16,
            channels=1,
        )

        await track_stereo.write(pcm_mono)

        # Should have doubled the data for stereo
        expected_bytes = 960 * 2 * 2  # samples * bytes_per_sample * channels
        assert len(track_stereo._buffer) == expected_bytes

        # Test stereo to mono
        track_mono = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        samples_stereo = np.zeros((2, 960), dtype=np.int16)  # 20ms stereo
        pcm_stereo = PcmData(
            samples=samples_stereo,
            sample_rate=48000,
            format=AudioFormat.S16,
            channels=2,
        )

        await track_mono.write(pcm_stereo)

        # Should have halved the data for mono
        expected_bytes = 960 * 2  # samples * bytes_per_sample
        assert len(track_mono._buffer) == expected_bytes

    @pytest.mark.asyncio
    async def test_buffer_overflow(self):
        """Test that buffer drops old data when it exceeds max size."""
        # Set small buffer size for testing (100ms)
        track = AudioStreamTrack(
            sample_rate=48000, channels=1, format="s16", audio_buffer_size_ms=100
        )

        # Try to write 200ms of data
        samples_200ms = int(0.2 * 48000)  # 9600 samples
        audio_data = np.zeros(samples_200ms, dtype=np.int16)
        pcm = PcmData(
            samples=audio_data,
            sample_rate=48000,
            format=AudioFormat.S16,
            channels=1,
        )

        await track.write(pcm)

        # Buffer should only contain 100ms worth of data
        max_samples = int(0.1 * 48000)  # 4800 samples
        max_bytes = max_samples * 2  # * 2 bytes per s16 sample
        assert len(track._buffer) == max_bytes

    @pytest.mark.asyncio
    async def test_silence_emission(self):
        """Test that recv emits silence when buffer is empty."""
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        # Receive frame without writing any data
        frame = await track.recv()
        assert frame.samples == 960  # 20ms at 48kHz

        # Extract audio data and verify it's silence (all zeros)
        audio_data = frame.to_ndarray()
        assert np.all(audio_data == 0)

    @pytest.mark.asyncio
    async def test_partial_frame_padding(self):
        """Test that partial frames are padded with silence."""
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        # Write only 10ms of data (480 samples)
        samples_10ms = int(0.01 * 48000)
        audio_data = np.ones(samples_10ms, dtype=np.int16) * 100  # Non-zero data
        pcm = PcmData(
            samples=audio_data,
            sample_rate=48000,
            format=AudioFormat.S16,
            channels=1,
        )

        await track.write(pcm)

        # Receive 20ms frame
        frame = await track.recv()
        assert frame.samples == 960  # Full 20ms frame

        # Check that first half has data and second half is silence
        audio_array = frame.to_ndarray()
        assert np.any(audio_array[:480] != 0)  # First 10ms has data
        assert np.all(audio_array[480:] == 0)  # Last 10ms is silence

    @pytest.mark.asyncio
    async def test_flush(self):
        """Test that flush clears the buffer."""
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        # Write some data
        samples = np.zeros(960, dtype=np.int16)
        pcm = PcmData(
            samples=samples,
            sample_rate=48000,
            format=AudioFormat.S16,
            channels=1,
        )
        await track.write(pcm)

        # Verify data is in buffer
        assert len(track._buffer) > 0

        # Flush
        await track.flush()

        # Verify buffer is empty
        assert len(track._buffer) == 0

    @pytest.mark.asyncio
    async def test_frame_timing(self, monkeypatch):
        """Test that frames are emitted at 20ms intervals."""
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        # Write enough data for multiple frames
        samples = np.zeros(4800, dtype=np.int16)  # 100ms of audio
        pcm = PcmData(
            samples=samples,
            sample_rate=48000,
            format=AudioFormat.S16,
            channels=1,
        )
        await track.write(pcm)

        # Record timing
        frame_times = []

        # Receive 3 frames and measure timing
        for _ in range(3):
            await track.recv()
            frame_times.append(time.time())

        # Check intervals between frames (should be ~20ms)
        for i in range(1, len(frame_times)):
            interval_ms = (frame_times[i] - frame_times[i - 1]) * 1000
            # Allow reasonable tolerance for asyncio.sleep() accuracy
            assert 15.0 <= interval_ms <= 25.0

    @pytest.mark.asyncio
    async def test_timing_warning(self, caplog):
        """Test that timing warnings are logged correctly."""
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        # Write data
        samples = np.zeros(960, dtype=np.int16)
        pcm = PcmData(
            samples=samples,
            sample_rate=48000,
            format=AudioFormat.S16,
            channels=1,
        )
        await track.write(pcm)

        # Get first frame to initialize timing
        await track.recv()

        # Simulate delay before getting second frame
        await asyncio.sleep(0.05)  # 50ms delay

        # Get second frame - should trigger warning
        with caplog.at_level("WARNING"):
            await track.recv()

        # Check that warning was logged
        assert any(
            "Frame timing issue detected" in record.message for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_continuous_streaming(self):
        """Test continuous audio streaming scenario."""
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        # Simulate continuous writing and reading
        write_task = asyncio.create_task(self._continuous_writer(track))
        read_task = asyncio.create_task(self._continuous_reader(track))

        # Run for 100ms
        await asyncio.sleep(0.1)

        # Cancel tasks
        write_task.cancel()
        read_task.cancel()

        try:
            await write_task
            await read_task
        except asyncio.CancelledError:
            pass

    async def _continuous_writer(self, track):
        """Helper to continuously write audio data."""
        while True:
            # Write 20ms chunks
            samples = np.zeros(960, dtype=np.int16)
            pcm = PcmData(
                samples=samples,
                sample_rate=48000,
                format=AudioFormat.S16,
                channels=1,
            )
            await track.write(pcm)
            await asyncio.sleep(0.02)  # 20ms

    async def _continuous_reader(self, track):
        """Helper to continuously read audio frames."""
        frames_received = 0
        while True:
            frame = await track.recv()
            frames_received += 1
            assert frame.samples == 960

    @pytest.mark.asyncio
    async def test_media_stream_error(self):
        """Test that MediaStreamError is raised when track is not live."""
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        # Stop the track
        track.stop()

        # Try to receive - should raise error
        with pytest.raises(aiortc.mediastreams.MediaStreamError):
            await track.recv()
