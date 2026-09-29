import numpy as np
import pytest

from getstream import _rust

SAMPLE_RATE = 48000
VIDEO_FPS = 15


class TestLocalTracks:
    async def test_audio_queue_overflow_raises(self):
        track = _rust.LocalAudioTrack()
        samples = np.zeros(SAMPLE_RATE * 61, dtype=np.int16)

        with pytest.raises(_rust.RtcError, match="pcm queue overflow"):
            await track.write_pcm(samples, SAMPLE_RATE, 1)

    async def test_misaligned_samples_raise(self):
        track = _rust.LocalAudioTrack()
        samples = np.frombuffer(memoryview(bytearray(1921))[1:], dtype=np.int16)

        with pytest.raises(ValueError, match="aligned"):
            await track.write_pcm(samples, SAMPLE_RATE, 1)

    async def test_odd_video_dimensions_raise(self):
        track = _rust.LocalVideoTrack.vp9()
        frame = np.zeros(321 * 240 * 3 // 2, dtype=np.uint8)

        with pytest.raises(_rust.RtcError, match="must be non-zero and even"):
            await track.write_i420(frame, 321, 240, 1 / VIDEO_FPS)
