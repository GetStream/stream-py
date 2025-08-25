import asyncio
import importlib
import sys
import types
from typing import Any, cast
from unittest.mock import AsyncMock

import numpy as np
import pytest


# --- Provide mocked google.genai SDK so the module under test can import ---
class _DummyBlob:
    def __init__(self, data=None, mime_type=None):
        self.data = data
        self.mime_type = mime_type


class _DummyDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__()


class _DummyModality:
    AUDIO = "audio"


class _DummyTurnCoverage:
    TURN_INCLUDES_ONLY_ACTIVITY = "turn_only"


_types_mod: Any = types.ModuleType("google.genai.types")
_types_mod.LiveConnectConfigDict = _DummyDict
_types_mod.Blob = _DummyBlob
_types_mod.Modality = _DummyModality
_types_mod.AudioTranscriptionConfigDict = _DummyDict
_types_mod.RealtimeInputConfigDict = _DummyDict
_types_mod.TurnCoverage = _DummyTurnCoverage
_types_mod.SpeechConfigDict = _DummyDict
_types_mod.VoiceConfigDict = _DummyDict
_types_mod.PrebuiltVoiceConfigDict = _DummyDict
_types_mod.ContextWindowCompressionConfigDict = _DummyDict
_types_mod.SlidingWindowDict = _DummyDict

_live_mod: Any = types.ModuleType("google.genai.live")
_live_mod.AsyncSession = object


# A controllable dummy session/context for tests
class _DummySession:
    def __init__(self, responses=None):
        # list of (data_bytes, text_str) tuples
        self._responses = responses or []
        self._receive_calls = 0
        self.sent = []

    async def send_realtime_input(self, text=None, audio=None):
        self.sent.append({"text": text, "audio": audio})

    def receive(self):
        async def _gen():
            # yield responses only on first call to receive(); then be empty
            if self._receive_calls == 0:
                for data, text in self._responses:
                    obj = types.SimpleNamespace()
                    obj.data = data
                    obj.text = text
                    yield obj
            self._receive_calls += 1

        return _gen()


class _DummyConnectCM:
    def __init__(self, responses=None):
        self._responses = responses or []
        self.session = None

    async def __aenter__(self):
        self.session = _DummySession(self._responses)
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _DummyLive:
    def __init__(self, responses=None):
        self._responses = responses or []

    def connect(self, model=None, config=None):
        return _DummyConnectCM(self._responses)


class _DummyClient:
    def __init__(self, *args, **kwargs):
        # tests will mutate this instance's live.responses via monkeypatch
        self.aio = types.SimpleNamespace(live=_DummyLive([]))


_genai_mod: Any = types.ModuleType("google.genai")
_genai_mod.Client = _DummyClient

# Ensure root google package exists for environments that lack it
try:
    importlib.import_module("google")
except ImportError:  # pragma: no cover - environment should have google from protobuf
    pkg: Any = types.ModuleType("google")
    pkg.__path__ = []  # mark as package
    sys.modules["google"] = pkg


from getstream.plugins.gemini.live import live as gemini_live  # noqa: E402
from getstream.plugins.gemini.live.live import GeminiLive  # noqa: E402
from getstream.video.rtc.track_util import PcmData  # noqa: E402


@pytest.mark.asyncio
async def test_connect_emits_events_and_forwards_audio_and_text(monkeypatch):
    # Arrange streamed responses
    responses = [(b"abc", "hello"), (b"def", None)]
    # Ensure our dummy client will yield these from the connect context
    client = _DummyClient()
    client.aio.live = _DummyLive(responses)
    monkeypatch.setattr(gemini_live, "Client", lambda *a, **k: client)

    events = {"connected": False, "audio": [], "text": []}

    sts = GeminiLive(api_key="key", model="model", provider_config=None)

    @sts.on("connected")  # type: ignore[arg-type]
    async def _on_connected():
        events["connected"] = True

    @sts.on("audio")  # type: ignore[arg-type]
    async def _on_audio(data: bytes):
        events["audio"].append(data)

    @sts.on("text")  # type: ignore[arg-type]
    async def _on_text(text: str):
        events["text"].append(text)

    # Spy on track writes
    write_spy = AsyncMock()
    monkeypatch.setattr(sts.output_track, "write", write_spy)

    # Act
    ready = await sts.wait_until_ready(timeout=1.0)
    assert ready is True

    # Give the background receiver loop time to process
    await asyncio.sleep(0.05)

    # Assert
    assert events["connected"] is True
    assert events["audio"] == [b"abc", b"def"]
    assert events["text"] == ["hello"]
    # Track writes should mirror audio chunks while playback is enabled
    write_spy.assert_any_await(b"abc")
    write_spy.assert_any_await(b"def")

    await sts.close()


@pytest.mark.asyncio
async def test_send_text_calls_underlying_session(monkeypatch):
    client = _DummyClient()
    client.aio.live = _DummyLive([])
    monkeypatch.setattr(gemini_live, "Client", lambda *a, **k: client)

    sts = GeminiLive(api_key="key", model="model", provider_config=None)
    await sts.wait_until_ready(timeout=1.0)

    # Access dummy session to inspect sent calls
    session = cast(Any, sts._session)
    assert session is not None

    await sts.send_text("hi there")

    assert any(call.get("text") == "hi there" for call in session.sent)


@pytest.mark.asyncio
async def test_send_audio_pcm_resample_barge_in_and_silence_timeout(monkeypatch):
    # No incoming responses needed for this test
    client = _DummyClient()
    client.aio.live = _DummyLive([])
    monkeypatch.setattr(gemini_live, "Client", lambda *a, **k: client)

    # Use our dummy Blob in assertions
    monkeypatch.setattr(gemini_live, "Blob", _DummyBlob)

    # Avoid doing real resampling; return the provided array unchanged
    monkeypatch.setattr(gemini_live, "resample_audio", lambda arr, src, dst: arr)

    sts = GeminiLive(
        api_key="key",
        model="model",
        provider_config=None,
        activity_threshold=10,
        silence_timeout_ms=20,
        barge_in=True,
    )
    await sts.wait_until_ready(timeout=1.0)

    # Threshold and timeout configured via constructor

    # Spy on flush
    flush_spy = AsyncMock()
    monkeypatch.setattr(sts.output_track, "flush", flush_spy)

    # Build loud mono PCM ndarray at 16k to trigger resample path
    samples = np.ones(480, dtype=np.int16) * 1000  # 30ms at 16k
    pcm = PcmData(format="s16", sample_rate=16000, samples=samples)

    # Act
    await sts.send_audio_pcm(pcm, target_rate=48000)

    # Barge-in should have interrupted playback and flushed
    assert sts._playback_enabled is False
    flush_spy.assert_awaited()

    # Underlying session should have received a blob with correct mime
    session = cast(Any, sts._session)
    assert session is not None and session.sent
    sent_audio = next(call["audio"] for call in session.sent if call.get("audio"))
    assert isinstance(sent_audio, _DummyBlob)
    assert sent_audio.mime_type == "audio/pcm;rate=48000"
    assert isinstance(sent_audio.data, (bytes, bytearray))

    # Wait for silence timeout to re-enable playback
    await asyncio.sleep(0.05)
    assert sts._user_speaking is False
    assert sts._playback_enabled is True

    await sts.close()


@pytest.mark.asyncio
async def test_interrupt_and_resume_playback(monkeypatch):
    client = _DummyClient()
    client.aio.live = _DummyLive([])
    monkeypatch.setattr(gemini_live, "Client", lambda *a, **k: client)

    sts = GeminiLive(api_key="key", model="model", provider_config=None)
    await sts.wait_until_ready(timeout=1.0)

    flush_spy = AsyncMock()
    monkeypatch.setattr(sts.output_track, "flush", flush_spy)

    await sts.interrupt_playback()
    assert sts._playback_enabled is False
    flush_spy.assert_awaited()

    sts.resume_playback()
    assert sts._playback_enabled is True

    await sts.close()


@pytest.mark.asyncio
async def test_stop_response_listener_cancels_task(monkeypatch):
    # Start with one response so the listener spins up
    responses = [(b"x", None)]
    client = _DummyClient()
    client.aio.live = _DummyLive(responses)
    monkeypatch.setattr(gemini_live, "Client", lambda *a, **k: client)

    sts = GeminiLive(api_key="key", model="model", provider_config=None)
    await sts.wait_until_ready(timeout=1.0)

    # Ensure listener task exists
    await asyncio.sleep(0.02)
    assert sts._audio_receiver_task is not None

    await sts.stop_response_listener()
    assert sts._audio_receiver_task is None

    await sts.close()
