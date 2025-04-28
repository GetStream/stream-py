from getstream.agents import tts
from getstream.video.rtc.audio_track import AudioStreamTrack
from typing import Iterator

class ElevenLabs(tts.TTS):

    def __init__(self, api_key: str, voice_id: str, model_id="eleven_multilingual_v2"):
        super().__init__()
        from elevenlabs.client import ElevenLabs

        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id
        self.model_id = model_id
        self.output_format = "pcm_16000"

    def set_output_track(self, track: AudioStreamTrack) -> None:
        if track.framerate != 16000:
            raise TypeError("Invalid framerate, audio track only supports 16000")
        super().set_output_track(track)

    async def synthesize(self, text: str, *args, **kwargs) -> Iterator[bytes]:
        """
        Convert text to speech using ElevenLabs API.
        
        Args:
            text: The text to convert to speech
            
        Returns:
            An iterator of audio chunks as bytes
        """
        audio_stream = self.client.text_to_speech.convert_as_stream(
            text=text,
            voice_id=self.voice_id,
            output_format=self.output_format,
            model_id=self.model_id
        )
        
        return audio_stream
