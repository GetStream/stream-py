"""Record audio: joins a call and writes the audio of each participant to a
WAV file, one file for each participant session.

It uses the public `getstream.video.rtc` API: `rtc.join` and the `audio`
event, whose `PcmData` has the participant and 48 kHz mono samples.

Run it with the credentials in the environment (STREAM_API_KEY and
STREAM_API_SECRET), for example from a `.env` file:

    uv run --env-file .env python examples/rtc/record_audio.py

It opens the Stream demo app in the browser for a new call. Allow the
microphone and speak, then stop it with Ctrl+C. The files are written to the
current directory as `<user_id>_<session_id>.wav`.

Two limits:
- No audio arrives while a participant is muted, so a file is shorter than
  the call. The `pts` of each `PcmData` tells where to put silence.
- The microphone and the screen-share audio of one participant go into the
  same file.
"""

import asyncio
import logging
import uuid
import wave

from getstream import AsyncStream
from getstream.models import CallRequest, UserRequest
from getstream.video import rtc
from getstream.video.rtc import PcmData
from getstream.video.rtc.utils import open_browser

RECORDER_ID = "audio-recorder"
SPEAKER_ID = "audio-speaker"

logger = logging.getLogger("record_audio")


class Recorder:
    """Writes the audio of each participant session to its own WAV file."""

    def __init__(self) -> None:
        self._files: dict[str, wave.Wave_write] = {}

    def write(self, pcm: PcmData) -> None:
        participant = pcm.participant
        file = self._files.get(participant.session_id)
        if file is None:
            path = f"{participant.user_id}_{participant.session_id}.wav"
            file = wave.open(path, "wb")
            file.setnchannels(pcm.channels)
            file.setsampwidth(2)  # 16-bit samples
            file.setframerate(pcm.sample_rate)
            self._files[participant.session_id] = file
            logger.info("Recording %s", path)
        file.writeframes(pcm.samples.tobytes())

    def close(self) -> None:
        for file in self._files.values():
            file.close()


async def main() -> None:
    recorder = Recorder()
    async with AsyncStream() as client:
        await client.upsert_users(
            UserRequest(id=RECORDER_ID), UserRequest(id=SPEAKER_ID)
        )
        call_id = str(uuid.uuid4())
        call = client.video.call("default", call_id)
        await call.get_or_create(data=CallRequest(created_by_id=RECORDER_ID))

        # Remote audio arrives without a subscription config.
        connection = await rtc.join(call, RECORDER_ID)
        connection.on("audio", recorder.write)
        try:
            async with connection:
                open_browser(client.api_key, client.create_token(SPEAKER_ID), call_id)
                # Returns when the call ends; Ctrl+C leaves the call.
                await connection.wait()
        finally:
            # The WAV header gets its length only when the file is closed.
            recorder.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
