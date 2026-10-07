import getstream_rtc
import numpy as np
import pytest

SAMPLE_RATE = 48000
VIDEO_FPS = 15


class TestLocalTracks:
    async def test_audio_queue_overflow_raises(self):
        track = getstream_rtc.LocalAudioTrack()
        samples = np.zeros(SAMPLE_RATE * 61, dtype=np.int16)

        with pytest.raises(getstream_rtc.PcmQueueOverflowError) as exc_info:
            await track.write_pcm(samples, SAMPLE_RATE, 1)

        assert exc_info.value.capacity_samples == SAMPLE_RATE * 60
        assert exc_info.value.dropped_samples == SAMPLE_RATE

    async def test_pcm_queue_capacity_limits_the_queue(self):
        track = getstream_rtc.LocalAudioTrack(pcm_queue_capacity=0.1)
        samples = np.zeros(SAMPLE_RATE, dtype=np.int16)

        with pytest.raises(getstream_rtc.PcmQueueOverflowError) as exc_info:
            await track.write_pcm(samples, SAMPLE_RATE, 1)

        assert exc_info.value.capacity_samples == SAMPLE_RATE // 10
        assert exc_info.value.dropped_samples == SAMPLE_RATE - SAMPLE_RATE // 10

    async def test_misaligned_samples_raise(self):
        track = getstream_rtc.LocalAudioTrack()
        samples = np.frombuffer(memoryview(bytearray(1921))[1:], dtype=np.int16)

        with pytest.raises(ValueError):
            await track.write_pcm(samples, SAMPLE_RATE, 1)

    async def test_odd_video_dimensions_raise(self):
        track = getstream_rtc.LocalVideoTrack.vp9()
        frame = np.zeros(321 * 240 * 3 // 2, dtype=np.uint8)

        with pytest.raises(getstream_rtc.MediaError):
            await track.write_i420(frame, 321, 240, 1 / VIDEO_FPS)
