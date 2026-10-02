import asyncio
import logging

import numpy as np
import pytest

from getstream import _rust
from getstream.video.rtc import AudioStreamTrack, PcmData
from getstream.video.rtc.audio_forwarder import AudioForwarder

SAMPLE_RATE = 48000


@pytest.fixture
def one_second() -> PcmData:
    return PcmData(
        samples=np.zeros(SAMPLE_RATE, dtype=np.int16),
        sample_rate=SAMPLE_RATE,
        format="s16",
        channels=1,
    )


class TestAudioForwarder:
    async def test_run_returns_when_the_source_stops(self):
        source = AudioStreamTrack()
        run = asyncio.create_task(AudioForwarder(source, _rust.LocalAudioTrack()).run())
        await asyncio.sleep(0.01)

        source.stop()

        await asyncio.wait_for(run, timeout=1)

    async def test_overflow_is_logged_and_the_copy_continues(
        self, caplog: pytest.LogCaptureFixture, one_second: PcmData
    ):
        source = AudioStreamTrack()
        # Not published, so nothing drains the 100 ms queue.
        target = _rust.LocalAudioTrack(pcm_queue_capacity=0.1)
        run = asyncio.create_task(AudioForwarder(source, target).run())

        logger = "getstream.video.rtc.audio_forwarder"
        with caplog.at_level(logging.DEBUG, logger=logger):
            await source.write(one_second)
            await asyncio.sleep(0.2)

        assert any(
            record.getMessage().startswith("Audio buffer overflow")
            for record in caplog.records
        )
        assert not run.done()
        source.stop()
        await asyncio.wait_for(run, timeout=1)
