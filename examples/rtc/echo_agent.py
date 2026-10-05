"""Echo agent: joins a call, plays back what the person in the browser says,
and shows their camera mirrored in its own video tile.

It uses only the public `getstream.video.rtc` API: `rtc.join` with a
subscription config, the `audio` and `track_added` events,
`RemoteTrack.video_frames()`, `add_tracks` and `wait`.

Run it with the credentials in the environment (STREAM_API_KEY and
STREAM_API_SECRET), for example from a `.env` file:

    uv run --env-file .env python examples/rtc/echo_agent.py

It opens the Stream demo app in the browser for a new call. Allow the
microphone and the camera, then speak: the agent plays back your audio and
shows your camera mirrored. Stop it with Ctrl+C. Use one person in the
browser: the audio of several people is played back one after another, not
mixed.
"""

import asyncio
import logging
import uuid
from fractions import Fraction
from typing import Optional

import aiortc
import av
import numpy as np

from getstream import AsyncStream
from getstream.models import CallRequest, UserRequest
from getstream.video import rtc
from getstream.video.rtc import (
    AudioStreamTrack,
    PcmData,
    RemoteTrack,
    TrackType,
    VideoFrame,
    VideoFrameStream,
)
from getstream.video.rtc.pb.stream.video.sfu.models.models_pb2 import (
    TRACK_TYPE_AUDIO,
    TRACK_TYPE_VIDEO,
)
from getstream.video.rtc.tracks import SubscriptionConfig, TrackSubscriptionConfig
from getstream.video.rtc.utils import open_browser

AGENT_ID = "echo-agent"
HUMAN_ID = "echo-human"
# The RTP clock of WebRTC video.
VIDEO_TIME_BASE = Fraction(1, 90000)

logger = logging.getLogger("echo_agent")


def mirrored(frame: VideoFrame) -> av.VideoFrame:
    """The frame flipped left to right, as a PyAV frame."""
    width, height = frame.width, frame.height
    # Packed I420: the Y plane, then the U and V planes at half size, rounded up.
    chroma = ((height + 1) // 2, (width + 1) // 2)
    image = av.VideoFrame(width, height, "yuv420p")
    offset = 0
    for plane, (rows, columns) in zip(image.planes, [(height, width), chroma, chroma]):
        pixels = frame.data[offset : offset + rows * columns].reshape(rows, columns)
        offset += rows * columns
        # A PyAV plane can have padding at the end of each row.
        padded = np.zeros((rows, plane.line_size), dtype=np.uint8)
        padded[:, :columns] = pixels[:, ::-1]
        plane.update(padded)
    image.pts = frame.rtp_timestamp
    image.time_base = VIDEO_TIME_BASE
    return image


class MirrorTrack(aiortc.MediaStreamTrack):
    """A video track with the mirrored frames of the latest remote camera."""

    kind = "video"

    def __init__(self) -> None:
        super().__init__()
        self._frames: Optional[VideoFrameStream] = None
        self._camera = asyncio.Event()

    def show(self, frames: VideoFrameStream) -> None:
        self._frames = frames
        self._camera.set()

    async def recv(self) -> av.VideoFrame:
        while True:
            await self._camera.wait()
            frames = self._frames
            assert frames is not None
            try:
                return mirrored(await anext(frames))
            except StopAsyncIteration:
                # The camera track ended; wait for the next one.
                if self._frames is frames:
                    self._camera.clear()


async def main() -> None:
    async with AsyncStream() as client:
        await client.upsert_users(UserRequest(id=AGENT_ID), UserRequest(id=HUMAN_ID))
        call_id = str(uuid.uuid4())
        call = client.video.call("default", call_id)
        await call.get_or_create(data=CallRequest(created_by_id=AGENT_ID))

        connection = await rtc.join(
            call,
            AGENT_ID,
            subscription_config=SubscriptionConfig(
                default=TrackSubscriptionConfig(
                    track_types=[TRACK_TYPE_AUDIO, TRACK_TYPE_VIDEO]
                )
            ),
        )
        audio = AudioStreamTrack()
        mirror = MirrorTrack()

        @connection.on("audio")
        async def echo(pcm: PcmData) -> None:
            await audio.write(pcm)

        @connection.on("track_added")
        def show_camera(track: RemoteTrack) -> None:
            if track.track_type == TrackType.VIDEO:
                # The stream keeps the track subscribed.
                mirror.show(track.video_frames())

        for event_name in (
            "participant_joined",
            "participant_left",
            "track_published",
            "track_unpublished",
        ):
            connection.on(event_name, lambda event: logger.info("%r", event))
        connection.on(
            "connection.state_changed",
            lambda change: logger.info("state %s -> %s", change["old"], change["new"]),
        )

        async with connection:
            await connection.add_tracks(audio=audio, video=mirror)
            open_browser(client.api_key, client.create_token(HUMAN_ID), call_id)
            # Returns when the call ends; Ctrl+C leaves the call.
            await connection.wait()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
