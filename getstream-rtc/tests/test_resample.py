import getstream_rtc
import numpy as np
import pytest


@pytest.fixture
def loud_end_16k() -> np.ndarray:
    """20 ms of silence at 16 kHz whose last 2 ms carry a loud 1 kHz tone."""
    samples = np.zeros(320, dtype=np.int16)
    time = np.arange(32) / 16000
    samples[-32:] = (20000 * np.sin(2 * np.pi * 1000 * time)).astype(np.int16)
    return samples


def peak(frame: getstream_rtc.PcmFrame) -> int:
    return int(np.abs(frame.samples.astype(np.int32)).max(initial=0))


class TestStreamResampler:
    def test_push_resamples_to_the_output_rate(self) -> None:
        resampler = getstream_rtc.StreamResampler(48000, 1)

        frame = resampler.push(np.zeros(1600, dtype=np.int16), 16000, 1)

        assert (frame.sample_rate, frame.channels) == (48000, 1)
        assert len(frame.samples) == pytest.approx(4800, abs=10)

    def test_flush_returns_the_audio_that_the_filter_holds(
        self, loud_end_16k: np.ndarray
    ) -> None:
        resampler = getstream_rtc.StreamResampler(48000, 1)

        pushed = resampler.push(loud_end_16k, 16000, 1)
        flushed = resampler.flush()

        assert peak(pushed) < 1000
        assert peak(flushed) > 15000

    def test_audio_at_the_output_rate_is_copied(self) -> None:
        resampler = getstream_rtc.StreamResampler(48000, 2)
        samples = np.array([100, -200, 300, -400], dtype=np.int16)

        frame = resampler.push(samples, 48000, 2)

        assert np.array_equal(frame.samples, samples)
        assert len(resampler.flush().samples) == 0

    def test_another_rate_than_the_first_frame_raises(self) -> None:
        resampler = getstream_rtc.StreamResampler(48000, 1)
        resampler.push(np.zeros(320, dtype=np.int16), 16000, 1)

        with pytest.raises(getstream_rtc.PcmRateMismatchError) as exc_info:
            resampler.push(np.zeros(480, dtype=np.int16), 24000, 1)

        assert (exc_info.value.expected, exc_info.value.actual) == (16000, 24000)

    def test_another_channel_count_raises(self) -> None:
        resampler = getstream_rtc.StreamResampler(48000, 1)

        with pytest.raises(getstream_rtc.IllegalStateError):
            resampler.push(np.zeros(640, dtype=np.int16), 16000, 2)

    def test_misaligned_samples_raise(self) -> None:
        resampler = getstream_rtc.StreamResampler(48000, 1)
        samples = np.frombuffer(memoryview(bytearray(641))[1:], dtype=np.int16)

        with pytest.raises(ValueError):
            resampler.push(samples, 16000, 1)
