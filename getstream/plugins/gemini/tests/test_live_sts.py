import asyncio
from types import SimpleNamespace
from typing import Any

import pytest
from unittest.mock import AsyncMock, MagicMock


# Module under test
from getstream.plugins.gemini.sts.live import GeminiLive


@pytest.fixture
def mock_call():
    call = MagicMock()
    call.call_type = "default"
    call.id = "test-call"
    return call


def _make_fake_connect_cm(fake_session: Any):
    class FakeConnectCM:
        async def __aenter__(self):
            return fake_session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    return FakeConnectCM()


@pytest.mark.asyncio
async def test_connect_emits_connected_and_yields_session(monkeypatch, mock_call):
    fake_session = AsyncMock()

    class FakeLive:
        def connect(self, *, model, config):  # noqa: ARG002 - signature parity
            return _make_fake_connect_cm(fake_session)

    class FakeAio:
        def __init__(self):
            self.live = FakeLive()

    class FakeClient:
        def __init__(self, api_key=None):  # noqa: ARG002 - signature parity
            self.aio = FakeAio()

    # Patch Client used inside the module
    monkeypatch.setattr(
        "getstream.plugins.gemini.sts.live.Client", FakeClient, raising=True
    )

    events = []
    sts = GeminiLive(api_key="key123")

    @sts.on("connected")  # type: ignore[arg-type]
    async def _on_connected():
        events.append("connected")

    async with sts.connect(mock_call) as session:
        assert session is not None
        assert sts.is_connected is True
        assert "connected" in events


@pytest.mark.asyncio
async def test_session_methods(monkeypatch, mock_call):
    # Prepare a fake session with methods we expect
    async def _recv_gen():
        yield SimpleNamespace(data=b"chunk1")
        yield SimpleNamespace(data=b"chunk2")

    fake_session = SimpleNamespace(
        receive=_recv_gen,
        send_realtime_input=AsyncMock(),
        send_client_content=AsyncMock(),
        send_tool_response=AsyncMock(),
    )

    class FakeLive:
        def connect(self, *, model, config):  # noqa: ARG002 - signature parity
            return _make_fake_connect_cm(fake_session)

    class FakeAio:
        def __init__(self):
            self.live = FakeLive()

    class FakeClient:
        def __init__(self, api_key=None):  # noqa: ARG002 - signature parity
            self.aio = FakeAio()

    monkeypatch.setattr(
        "getstream.plugins.gemini.sts.live.Client", FakeClient, raising=True
    )

    sts = GeminiLive(api_key="key")
    async with sts.connect(mock_call) as conn:
        # receive proxies the session iterator
        chunks = []
        async for msg in conn.receive():
            chunks.append(msg.data)
        assert chunks == [b"chunk1", b"chunk2"]

        # proxy sends
        await conn.send_realtime_input(text="hi")
        fake_session.send_realtime_input.assert_awaited_once()
        kwargs = fake_session.send_realtime_input.await_args.kwargs
        assert list(kwargs.keys()) == ["text"]
        assert kwargs["text"] == "hi"

        await conn.send_client_content(turns={"parts": [{"text": "ok"}]})
        fake_session.send_client_content.assert_awaited()

        await conn.send_tool_response(
            function_responses={"id": "1", "name": "f", "response": {"output": "x"}}
        )
        fake_session.send_tool_response.assert_awaited()


@pytest.mark.asyncio
async def test_send_text_and_audio(monkeypatch, mock_call):
    fake_session = SimpleNamespace(
        receive=lambda: (_ async for _ in ()),  # never used
        send_realtime_input=AsyncMock(),
    )

    class FakeLive:
        def connect(self, *, model, config):  # noqa: ARG002 - signature parity
            return _make_fake_connect_cm(fake_session)

    class FakeAio:
        def __init__(self):
            self.live = FakeLive()

    class FakeClient:
        def __init__(self, api_key=None):  # noqa: ARG002 - signature parity
            self.aio = FakeAio()

    monkeypatch.setattr(
        "getstream.plugins.gemini.sts.live.Client", FakeClient, raising=True
    )

    sts = GeminiLive(api_key="k")
    async with sts.connect(mock_call):
        # send_text -> send_realtime_input(text=...)
        await sts.send_text("hello")
        fake_session.send_realtime_input.assert_awaited()
        kwargs = fake_session.send_realtime_input.await_args.kwargs
        assert list(kwargs.keys()) == ["text"]
        assert kwargs["text"] == "hello"

        # send_audio -> send_realtime_input(audio=Blob)
        fake_session.send_realtime_input.reset_mock()
        await sts.send_audio(b"\x00\x01", sample_rate=16000)
        kwargs = fake_session.send_realtime_input.await_args.kwargs
        assert list(kwargs.keys()) == ["audio"]
        audio_blob = kwargs["audio"]
        assert getattr(audio_blob, "mime_type") == "audio/pcm;rate=16000"
        assert getattr(audio_blob, "data") == b"\x00\x01"


@pytest.mark.asyncio
async def test_send_audio_pcm_resamples(monkeypatch, mock_call):
    np = pytest.importorskip("numpy")

    # Fake session to capture call
    fake_session = SimpleNamespace(send_realtime_input=AsyncMock())

    class FakeLive:
        def connect(self, *, model, config):  # noqa: ARG002 - signature parity
            return _make_fake_connect_cm(fake_session)

    class FakeAio:
        def __init__(self):
            self.live = FakeLive()

    class FakeClient:
        def __init__(self, api_key=None):  # noqa: ARG002 - signature parity
            self.aio = FakeAio()

    monkeypatch.setattr(
        "getstream.plugins.gemini.sts.live.Client", FakeClient, raising=True
    )

    # Patch resample_audio to a predictable transform
    def fake_resample(samples, src_rate, dst_rate):  # noqa: ARG001 - behavior-only
        return samples[::3]  # downsample by factor 3 (48k -> ~16k)

    monkeypatch.setattr(
        "getstream.plugins.gemini.sts.live.resample_audio", fake_resample, raising=True
    )

    sts = GeminiLive(api_key="k")
    async with sts.connect(mock_call):
        # Create PcmData with 48k int16 samples
        from getstream.video.rtc.track_util import PcmData

        arr = np.arange(0, 480, dtype=np.int16)  # 480 samples -> 10ms @ 48k
        pcm = PcmData(format="s16", sample_rate=48000, samples=arr)

        await sts.send_audio_pcm(pcm, target_rate=16000)
        fake_session.send_realtime_input.assert_awaited()
        blob = fake_session.send_realtime_input.await_args.kwargs["audio"]
        # Ensure bytes length matches fake downsampling
        assert isinstance(getattr(blob, "data"), (bytes, bytearray))
        assert len(blob.data) == len(arr[::3].tobytes())


@pytest.mark.asyncio
async def test_update_session_and_tool_response(monkeypatch, mock_call):
    fake_session = SimpleNamespace(
        send_client_content=AsyncMock(),
        send_tool_response=AsyncMock(),
    )

    class FakeLive:
        def connect(self, *, model, config):  # noqa: ARG002 - signature parity
            return _make_fake_connect_cm(fake_session)

    class FakeAio:
        def __init__(self):
            self.live = FakeLive()

    class FakeClient:
        def __init__(self, api_key=None):  # noqa: ARG002 - signature parity
            self.aio = FakeAio()

    monkeypatch.setattr(
        "getstream.plugins.gemini.sts.live.Client", FakeClient, raising=True
    )

    sts = GeminiLive(api_key="k")
    async with sts.connect(mock_call):
        await sts.send_function_call_output("tool-1", '{"ok":true}', "start")
        fake_session.send_tool_response.assert_awaited()
        tool_kwargs = fake_session.send_tool_response.await_args.kwargs
        fr = tool_kwargs.get("function_responses")
        # function_responses is a FunctionResponse instance
        from google.genai.types import FunctionResponse

        assert isinstance(fr, FunctionResponse)
        assert fr.id == "tool-1"
        assert fr.name == "start"


@pytest.mark.asyncio
async def test_start_and_stop_response_listener_emits_audio(monkeypatch, mock_call):
    # Async generator yielding two audio chunks
    async def _recv_gen():
        yield SimpleNamespace(data=b"A")
        yield SimpleNamespace(data=b"B")
        await asyncio.sleep(0)  # allow loop scheduling

    fake_session = SimpleNamespace(receive=_recv_gen)

    class FakeLive:
        def connect(self, *, model, config):  # noqa: ARG002 - signature parity
            return _make_fake_connect_cm(fake_session)

    class FakeAio:
        def __init__(self):
            self.live = FakeLive()

    class FakeClient:
        def __init__(self, api_key=None):  # noqa: ARG002 - signature parity
            self.aio = FakeAio()

    monkeypatch.setattr(
        "getstream.plugins.gemini.sts.live.Client", FakeClient, raising=True
    )

    sts = GeminiLive(api_key="k")
    collected = []

    @sts.on("audio")  # type: ignore[arg-type]
    async def _on_audio(data):
        collected.append(data)

    async with sts.connect(mock_call):
        # Start and allow some iteration
        sts.start_response_listener(emit_events=True)
        await asyncio.sleep(0.05)
        await sts.stop_response_listener()

    assert collected == [b"A", b"B"]


@pytest.mark.asyncio
async def test_methods_raise_if_not_connected():
    sts = GeminiLive(api_key="abc")
    with pytest.raises(RuntimeError):
        await sts.send_text("hi")
    with pytest.raises(RuntimeError):
        await sts.send_audio(b"x")
    with pytest.raises(RuntimeError):
        await sts.send_audio_pcm(MagicMock(), 16000)  # type: ignore[arg-type]
