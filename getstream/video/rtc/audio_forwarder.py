import asyncio
import logging

import aiortc

from getstream import _rust
from getstream.video.rtc.audio_track import AudioStreamTrack

logger = logging.getLogger(__name__)


class AudioForwarder:
    """Copies the frames of an aiortc audio track to an SDK `LocalAudioTrack`.

    The SDK paces the frames, so the source need not be paced. A `flush()` of
    an `AudioStreamTrack` source also clears the SDK queue.
    """

    def __init__(
        self, source: aiortc.MediaStreamTrack, target: _rust.LocalAudioTrack
    ) -> None:
        self.source = source
        self.target = target

    async def run(self) -> None:
        """Copy frames until the source ends or the SDK stops the target."""
        flushes = (
            asyncio.create_task(self._forward_flushes(self.source))
            if isinstance(self.source, AudioStreamTrack)
            else None
        )
        try:
            await self._forward_frames()
        finally:
            if flushes:
                flushes.cancel()

    async def _forward_frames(self) -> None:
        while True:
            try:
                frame = await self.source.recv()
            except aiortc.mediastreams.MediaStreamError:
                return
            try:
                await self.target.write_pcm(
                    frame.to_ndarray().reshape(-1),
                    frame.sample_rate,
                    len(frame.layout.channels),
                )
            except _rust.PcmQueueOverflowError as error:
                # The SDK dropped the oldest audio and kept the newest.
                logger.debug(
                    f"Audio buffer overflow: dropped {error.dropped_samples} samples"
                )
            except _rust.IllegalStateError:
                # The only cause is a stopped track: it was unpublished, or the
                # call was left or ended.
                return

    async def _forward_flushes(self, source: AudioStreamTrack) -> None:
        while True:
            await source.wait_for_flush()
            self.target.flush()
