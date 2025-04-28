from typing import Iterator

from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from getstream.agents import stt


class Deepgram(stt.STT):

    def __init__(self, api_key: str, options: LiveOptions):
        super().__init__()
        self.deepgram = DeepgramClient(api_key)
        self.dg_connection = self.deepgram.listen.live.v("1")

        self.dg_connection.on(LiveTranscriptionEvents.Transcript, lambda _: _)
        self.dg_connection.on(LiveTranscriptionEvents.Error, lambda _: _)

        if options is None:
            options = LiveOptions(model="nova-2", language="en-US")

        self.dg_connection.start(options)

    async def send_audio(self, pcm: bytes):
        pass

    def close(self):
        if self.dg_connection is not None:
            self.dg_connection.close()
