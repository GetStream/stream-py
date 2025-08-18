from unittest.mock import patch

import numpy as np
import pytest

from getstream.plugins.kokoro.tts import KokoroTTS
from getstream.video.rtc.audio_track import AudioStreamTrack


############################
# Test utilities & fixtures
############################


class MockAudioTrack(AudioStreamTrack):
    def __init__(self, framerate: int = 24_000):
        self.framerate = framerate
        self.written_data = []

    async def write(self, data: bytes):
        self.written_data.append(data)
        return True


class _MockKPipeline:  # noqa: D401
    """Very small stub that mimics ``kokoro.KPipeline`` callable behaviour."""

    def __init__(self, *_, **__):
        pass

    def __call__(self, text, *, voice, speed, split_pattern):  # noqa: D401
        # Produce two mini 20 ms chunks of silence at 24 kHz
        blank = np.zeros(480, dtype=np.float32)  # 480 samples @ 24 kHz = 20 ms
        for _ in range(2):
            yield text, voice, blank


############################
# Unit-tests
############################


@pytest.mark.asyncio
@patch("getstream.plugins.kokoro.tts.tts.KPipeline", _MockKPipeline)
async def test_kokoro_tts_initialization():
    tts = KokoroTTS()
    assert tts is not None


@pytest.mark.asyncio
@patch("getstream.plugins.kokoro.tts.tts.KPipeline", _MockKPipeline)
async def test_kokoro_synthesize_returns_iterator():
    tts = KokoroTTS()
    stream = await tts.synthesize("Hello")

    # Should be iterable (list of bytes)
    chunks = list(stream)
    assert len(chunks) == 2
    assert all(isinstance(c, (bytes, bytearray)) for c in chunks)


@pytest.mark.asyncio
@patch("getstream.plugins.kokoro.tts.tts.KPipeline", _MockKPipeline)
async def test_kokoro_send_writes_and_emits():
    tts = KokoroTTS()
    track = MockAudioTrack()
    tts.set_output_track(track)

    received = []

    @tts.on("audio")
    def _on_audio(chunk, _user):
        received.append(chunk)

    await tts.send("Hello world")

    assert len(track.written_data) == 2
    assert track.written_data == received


@pytest.mark.asyncio
@patch("getstream.plugins.kokoro.tts.tts.KPipeline", _MockKPipeline)
async def test_kokoro_invalid_framerate():
    tts = KokoroTTS()
    bad_track = MockAudioTrack(framerate=16_000)

    with pytest.raises(TypeError):
        tts.set_output_track(bad_track)


@pytest.mark.asyncio
@patch("getstream.plugins.kokoro.tts.tts.KPipeline", _MockKPipeline)
async def test_kokoro_send_without_track():
    tts = KokoroTTS()
    with pytest.raises(ValueError):
        await tts.send("Hi")
