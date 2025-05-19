import asyncio

import numpy as np
import pyaudio

from getstream import Stream
from getstream.models import UserRequest, CallRequest

from pydub import AudioSegment
import opuslib

from getstream.video.rtc.rtc import RTCCall


async def audio_consumer(queue):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=48000, output=True)

    while True:
        try:
            payload = await queue.get()
            float_array = np.frombuffer(payload, dtype=np.float32)
            stream.write(float_array.tobytes())
        except asyncio.QueueEmpty:
            pass


async def cartesia_tts(call: RTCCall, text: str):
    # wait 5s, we need the SDK to expose a hook for this
    await asyncio.sleep(5)

    while True:
        from cartesia import AsyncCartesia

        client = AsyncCartesia(api_key="c8029f10-b547-4185-9131-4a7d450707e3")
        voice_id = "a0e99841-438c-4a64-b679-ae501e7d6091"
        voice = client.voices.get(id=voice_id)

        # You can check out our models at https://docs.cartesia.ai/getting-started/available-models
        model_id = "sonic-english"

        # You can find the supported `output_format`s at https://docs.cartesia.ai/reference/api-reference/rest/stream-speech-server-sent-events
        output_format = {
            "container": "raw",
            "encoding": "pcm_f32le",
            "sample_rate": 48_000,
        }

        accumulated_bytes = bytes()
        # Generate and stream audio
        async for output in await client.tts.sse(
            model_id=model_id,
            transcript=text,
            voice_embedding=voice["embedding"],
            stream=True,
            output_format=output_format,
        ):
            print(
                f"response contains {len(output["audio"])} samples at 48khz -> {len(output['audio'])/48}ms"
            )
            # accumulated_bytes = accumulated_bytes + output["audio"]
            # await call.send_audio(stream=output["audio"])

        await call.send_audio(stream=accumulated_bytes)
        await client.close()


class OpusStream:
    def __init__(self, mp3_file):
        # Load the MP3 file and convert it to raw audio (PCM)
        self.audio = (
            AudioSegment.from_mp3(mp3_file).set_channels(1).set_frame_rate(48000)
        )  # Opus works best with mono and 48kHz
        self.frame_size = int(48000 * 0.02)  # 20ms frame size for 48kHz audio

        # Initialize the Opus encoder
        self.encoder = opuslib.api.encoder.Encoder(48000, 1, opuslib.APPLICATION_AUDIO)

        # pydub audio is in bytes, so we need to work with its frame data
        self.raw_audio = self.audio.raw_data
        self.position = 0

    def __iter__(self):
        return self

    def __next__(self):
        # Calculate the position of the next frame (20ms chunk)
        start = self.position
        end = start + self.frame_size * 2  # 2 bytes per sample (16-bit PCM)

        if start >= len(self.raw_audio):
            raise StopIteration  # No more audio data

        # Get the next frame of raw audio data
        frame = self.raw_audio[start:end]
        self.position = end

        # Encode the frame into Opus format
        opus_payload = self.encoder.encode(frame, self.frame_size, len(frame))

        return opus_payload


poetry = """
In the quiet hours before the light,
When the stars still cling to the edge of night,
The world, in slumber, softly breathes,
And dreams drift gently on the breeze.
"""


# ffmpeg -re -stream_loop 400 -i ./SampleVideo_1280x720_30mb.mp4 -c:v libx264 -preset veryfast -b:v 3000k -maxrate 3000k -bufsize 6000k -pix_fmt yuv420p -g 50 -c:a aac -b:a 160k -ac 2 -f flv rtmps://ingress.stream-io-video.com:443/hd8szvscpxvd.default.example-ai-recorder/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3MjU2Mzc0MDMsImNhbGxfY2lkcyI6WyJkZWZhdWx0OmFpLXJlY29yZGVyIl0sInVzZXJfaWQiOiIwYzAyYmEwYS1kNjQ5LTQwZWMtOGE0OC1lNDA4MjQwOTE0NGQifQ.uRoqQn5eeEsLMUF6S4li8NDPiFeu3d19QxYKkln2fOA
async def example_recorder():
    client = Stream(
        "hd8szvscpxvd",
        "4dv9yu4hqy7xvqk35vpbnqrafg2b43rzu8u4wt93mgrc3cd2ufb5bndb73g58emq",
    )
    client.upsert_users(
        UserRequest(
            id="ai-recorder",
            name="Python fancy AI",
            image="https://github.com/user-attachments/assets/0c0a7514-6c9c-4587-b2f2-62363f23aedc",
        )
    )
    call = client.video.rtc_call("default", "example-ai-recorder")
    call.get_or_create(data=CallRequest(created_by_id="ai-recorder"))
    call_task = asyncio.create_task(call.join("ai-recorder"))

    results = await asyncio.gather(
        call_task,
        audio_consumer(call.audio_queue),
        cartesia_tts(call, poetry),
    )


if __name__ == "__main__":
    asyncio.run(example_recorder())
