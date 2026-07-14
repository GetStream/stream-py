import asyncio
import time

import aiortc
import numpy as np
import pytest

from getstream.video.rtc.audio_track import AudioStreamTrack
from getstream.video.rtc.track_util import AudioFormat, PcmData

SINE_FREQ = 1000.0


def _sine_chunks(
    freq: float,
    sample_rate: int,
    total_ms: int,
    chunk_ms: int = 20,
    amplitude: int = 10000,
) -> list[PcmData]:
    n_total = int(sample_rate * total_ms / 1000)
    t = np.arange(n_total) / sample_rate
    wave = (amplitude * np.sin(2 * np.pi * freq * t)).astype(np.int16)
    chunk = int(sample_rate * chunk_ms / 1000)
    return [
        PcmData(
            samples=wave[i : i + chunk],
            sample_rate=sample_rate,
            format="s16",
            channels=1,
        )
        for i in range(0, n_total, chunk)
        if len(wave[i : i + chunk]) == chunk
    ]


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
            format="s16",
            audio_buffer_size_ms=10000,
        )
        assert track.sample_rate == 16000
        assert track.channels == 2
        assert track.format == "s16"
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

    def test_rejects_f32_output(self):
        """Output format must be s16; f32 is rejected at construction."""
        with pytest.raises(ValueError):
            AudioStreamTrack(format="f32")

    @pytest.mark.asyncio
    async def test_format_conversion(self):
        """Test that write converts input to the track's s16 output format."""
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        # Write a full 20ms of f32 input at half scale.
        pcm = PcmData(
            samples=np.full(960, 0.5, dtype=np.float32),
            sample_rate=48000,
            format=AudioFormat.F32,
            channels=1,
        )

        await track.write(pcm)

        # The emitted frame is s16 with the f32 value scaled into the int16 range.
        frame = await track.recv()
        assert frame.format.name == "s16"
        assert 15000 < int(np.max(frame.to_ndarray())) < 17000  # ~0.5 * 32767

    @pytest.mark.asyncio
    async def test_sample_rate_conversion(self):
        """Test that write resamples audio to the track's output rate."""
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        # 20ms at 16kHz = 320 samples; upsampled to 48kHz that is one 960-sample frame.
        samples_16k = np.zeros(320, dtype=np.int16)
        pcm = PcmData(
            samples=samples_16k,
            sample_rate=16000,
            format=AudioFormat.S16,
            channels=1,
        )

        await track.write(pcm)

        frame = await track.recv()
        assert frame.sample_rate == 48000
        assert frame.samples == 960  # 320 samples @16kHz -> 960 @48kHz

    @pytest.mark.asyncio
    async def test_channel_conversion(self):
        """Test mono to stereo and stereo to mono conversion."""
        # Mono input to a stereo track -> stereo output frame.
        track_stereo = AudioStreamTrack(sample_rate=48000, channels=2, format="s16")

        samples_mono = np.zeros(960, dtype=np.int16)  # 20ms mono
        pcm_mono = PcmData(
            samples=samples_mono,
            sample_rate=48000,
            format=AudioFormat.S16,
            channels=1,
        )

        await track_stereo.write(pcm_mono)

        frame = await track_stereo.recv()
        assert len(frame.layout.channels) == 2
        assert frame.samples == 960

        # Stereo input to a mono track -> mono output frame.
        track_mono = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        samples_stereo = np.zeros((2, 960), dtype=np.int16)  # 20ms stereo
        pcm_stereo = PcmData(
            samples=samples_stereo,
            sample_rate=48000,
            format=AudioFormat.S16,
            channels=2,
        )

        await track_mono.write(pcm_stereo)

        frame = await track_mono.recv()
        assert len(frame.layout.channels) == 1
        assert frame.samples == 960

    @pytest.mark.asyncio
    async def test_buffer_overflow(self):
        """Test that the buffer drops old data when it exceeds max size."""
        # 100ms cap holds at most five 20ms frames.
        track = AudioStreamTrack(
            sample_rate=48000, channels=1, format="s16", audio_buffer_size_ms=100
        )

        # Write 200ms (ten 20ms frames) of non-zero audio; the cap must drop the oldest.
        samples_200ms = int(0.2 * 48000)  # 9600 samples
        audio_data = np.full(samples_200ms, 100, dtype=np.int16)
        pcm = PcmData(
            samples=audio_data,
            sample_rate=48000,
            format=AudioFormat.S16,
            channels=1,
        )

        await track.write(pcm)

        # Only the last 100ms survives: five frames carry data, the rest are silence.
        data_frames = 0
        for _ in range(8):
            frame = await track.recv()
            if np.any(frame.to_ndarray() != 0):
                data_frames += 1
        assert data_frames == 5

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
    async def test_partial_frame_buffered_until_flush(self):
        """Sub-frame writes are held; a final flush emits them, padded by recv to a full frame."""
        # Without a final flush, a sub-frame write (10ms) emits nothing.
        held = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")
        await held.write(
            PcmData(
                samples=np.full(480, 100, dtype=np.int16),
                sample_rate=48000,
                format=AudioFormat.S16,
                channels=1,
            )
        )
        starved = await held.recv()
        assert np.all(
            starved.to_ndarray() == 0
        )  # partial held -> recv starves to silence

        # With final=True the buffered partial is flushed; recv pads it to a full 20ms
        # frame: the first 10ms carries the data, the last 10ms is silence.
        flushed = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")
        await flushed.write(
            PcmData(
                samples=np.full(480, 100, dtype=np.int16),
                sample_rate=48000,
                format=AudioFormat.S16,
                channels=1,
            ),
            final=True,
        )
        frame = await flushed.recv()
        assert frame.samples == 960
        audio = frame.to_ndarray().flatten()
        assert np.all(audio[:480] != 0)  # flushed data
        assert np.all(audio[480:] == 0)  # silence padding

    @pytest.mark.asyncio
    async def test_flush(self):
        """Test that flush drops pending audio so recv falls back to silence."""
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        # Buffer 40ms of non-zero audio (two frames).
        samples = np.full(1920, 100, dtype=np.int16)
        pcm = PcmData(
            samples=samples,
            sample_rate=48000,
            format=AudioFormat.S16,
            channels=1,
        )
        await track.write(pcm)

        # Flush drops the buffered frames; the next recv is synthesized silence.
        await track.flush()
        frame = await track.recv()
        assert np.all(frame.to_ndarray() == 0)

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
    async def test_first_frame_is_immediate_and_pts_zero(self):
        """The first recv anchors the clock: it returns without waiting, pts=0."""
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        start = time.time()
        frame = await track.recv()
        elapsed_ms = (time.time() - start) * 1000

        assert frame.pts == 0
        assert elapsed_ms < 10  # no pacing wait on the first frame

    @pytest.mark.asyncio
    async def test_pts_advances_by_one_frame_per_recv(self):
        """Successive frames carry pts stepping by samples_per_frame (960 @48kHz)."""
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        pts = [(await track.recv()).pts for _ in range(4)]

        assert pts == [0, 960, 1920, 2880]

    @pytest.mark.asyncio
    async def test_slow_consumer_does_not_accumulate_drift(self):
        """A consumer that falls behind gets overdue frames immediately, not delayed.

        Pacing anchors each pts to the start time, not the previous frame, so a stalled
        consumer catches up rather than stretching the timeline.
        """
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        await track.recv()  # anchor the clock at pts=0
        await asyncio.sleep(0.1)  # fall ~5 frames behind

        start = time.time()
        frame = await track.recv()
        elapsed_ms = (time.time() - start) * 1000

        assert frame.pts == 960
        assert elapsed_ms < 10  # overdue frame is due already -> no wait

    @pytest.mark.asyncio
    async def test_pacing_is_independent_of_buffer_content(self):
        """Pacing advances even while starved: silence frames still step pts by a frame."""
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        # No write(): every recv starves to silence, but the clock keeps ticking.
        frames = [await track.recv() for _ in range(3)]

        assert [f.pts for f in frames] == [0, 960, 1920]
        assert all(np.all(f.to_ndarray() == 0) for f in frames)

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
    async def test_recv_consumes_frames_in_order(self):
        """recv hands out buffered frames one at a time, in FIFO order, then starves."""
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        # Two distinguishable 20ms frames: first all 100, then all 200.
        samples = np.concatenate(
            [np.full(960, 100, dtype=np.int16), np.full(960, 200, dtype=np.int16)]
        )
        pcm = PcmData(
            samples=samples,
            sample_rate=48000,
            format=AudioFormat.S16,
            channels=1,
        )
        await track.write(pcm)

        first = await track.recv()
        second = await track.recv()
        third = await track.recv()

        assert np.all(first.to_ndarray() == 100)
        assert np.all(second.to_ndarray() == 200)
        assert np.all(third.to_ndarray() == 0)  # buffer drained -> silence

    @pytest.mark.asyncio
    async def test_buffer_overflow_drops_oldest_across_writes(self):
        """Overflow across multiple writes drops the oldest frames, keeping the newest."""
        track = AudioStreamTrack(
            sample_rate=48000, channels=1, format="s16", audio_buffer_size_ms=100
        )

        # First 40ms (value 100), then 200ms (value 200); total far exceeds the 100ms cap.
        await track.write(
            PcmData(
                samples=np.full(1920, 100, dtype=np.int16),
                sample_rate=48000,
                format=AudioFormat.S16,
                channels=1,
            )
        )
        await track.write(
            PcmData(
                samples=np.full(9600, 200, dtype=np.int16),
                sample_rate=48000,
                format=AudioFormat.S16,
                channels=1,
            )
        )

        # Only the newest five frames survive: all value 200, the older 100s were dropped.
        values = []
        for _ in range(6):
            frame = await track.recv()
            arr = frame.to_ndarray()
            values.append(0 if np.all(arr == 0) else int(arr.flatten()[0]))
        assert values == [200, 200, 200, 200, 200, 0]

    @pytest.mark.asyncio
    async def test_media_stream_error(self):
        """Test that MediaStreamError is raised when track is not live."""
        track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")

        # Stop the track
        track.stop()

        # Try to receive - should raise error
        with pytest.raises(aiortc.mediastreams.MediaStreamError):
            await track.recv()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("src_rate, dst_rate", [(24000, 48000), (48000, 24000)])
    async def test_resampling_is_high_quality(self, src_rate, dst_rate):
        # A clean tone resampled up or down must stay clean: the fundamental should
        # dominate, i.e. high SINAD. Linear interpolation lands around ~28 dB here.
        track = AudioStreamTrack(sample_rate=dst_rate, channels=1)
        for chunk in _sine_chunks(SINE_FREQ, src_rate, total_ms=500):
            await track.write(chunk)
        drained = np.concatenate(
            [(await track.recv()).to_ndarray().reshape(-1) for _ in range(28)]
        ).astype(np.float64)
        drained = drained[: np.nonzero(np.abs(drained) > 1)[0][-1] + 1]

        spectrum = np.abs(np.fft.rfft(drained * np.hanning(len(drained)))) ** 2
        freqs = np.fft.rfftfreq(len(drained), 1 / dst_rate)
        df = freqs[1] - freqs[0]
        fundamental = spectrum[np.abs(freqs - SINE_FREQ) <= 4 * df].sum()
        noise = spectrum.sum() - fundamental - spectrum[freqs < 30].sum()

        assert 10 * np.log10(fundamental / noise) > 60
