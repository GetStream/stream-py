import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence

import pytest

from getstream.plugins.common.event_utils import get_global_registry
from getstream.plugins.common.events import ConnectionState, EventType
from getstream.plugins.common.llm import LLM, RealtimeLLM
from getstream.plugins.common.llm_types import (
    Message,
    NormalizedOutputItem,
    NormalizedResponse,
    Role,
)


class FakeLLM(
    LLM[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]
):
    """Deterministic fake LLM for unit testing the base class behavior."""

    async def _create_response_impl(
        self,
        *,
        messages: Sequence[Dict[str, Any]],
        tools: Optional[Sequence[Dict[str, Any]]],
        options: Optional[Dict[str, Any]],
        response_format: Optional[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return {
            "ok": True,
            "id": "sync-1",
            "text": "hello world",
            "model": self.model or "fake-model",
            "echo_messages": list(messages),
            "echo_tools": list(tools) if tools else None,
            "echo_options": dict(options) if options else None,
            "echo_response_format": dict(response_format) if response_format else None,
            "echo_metadata": dict(metadata) if metadata else None,
        }

    async def _create_response_stream_impl(
        self,
        *,
        messages: Sequence[Dict[str, Any]],
        tools: Optional[Sequence[Dict[str, Any]]],
        options: Optional[Dict[str, Any]],
        response_format: Optional[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]],
    ) -> AsyncIterator[Dict[str, Any]]:
        # Yield a text delta, then an audio delta, then a final marker
        yield {"kind": "text", "delta": "hi", "is_final": False}
        yield {
            "kind": "audio",
            "data": b"\x01\x02",
            "mime_type": "audio/wav",
            "sample_rate": 16000,
            "channels": 1,
        }
        yield {"kind": "done", "is_final": True}

    def _normalize_sync_result_payload(
        self, result: Dict[str, Any]
    ) -> Optional[NormalizedResponse]:
        return {
            "id": result["id"],
            "model": result["model"],
            "status": "completed",
            "output": [
                {"type": "text", "text": result["text"]},
            ],
            "output_text": result["text"],
            "raw": dict(result),
        }

    def _normalize_stream_item_payload(
        self, item: Dict[str, Any]
    ) -> Optional[NormalizedOutputItem]:
        if item.get("kind") == "text":
            return {"type": "text", "text": item.get("delta", "")}
        if item.get("kind") == "audio":
            return {
                "type": "audio",
                "data": item.get("data", b""),
                "mime_type": item.get("mime_type", "audio/unknown"),
                "sample_rate": item.get("sample_rate", 0),
                "channels": item.get("channels", 0),
            }
        return None

    def _extract_text_delta(self, item: Dict[str, Any]) -> Optional[str]:
        if item.get("kind") == "text":
            return item.get("delta", "")
        return None

    def _extract_audio_delta(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if item.get("kind") == "audio":
            return {
                "data": item.get("data", b""),
                "mime_type": item.get("mime_type", "audio/unknown"),
                "sample_rate": item.get("sample_rate", 0),
                "channels": item.get("channels", 0),
            }
        return None


class ErrorLLM(FakeLLM):
    async def _create_response_impl(
        self,
        *,
        messages: Sequence[Dict[str, Any]],
        tools: Optional[Sequence[Dict[str, Any]]],
        options: Optional[Dict[str, Any]],
        response_format: Optional[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        raise ValueError("boom")


class FakeRealtime(
    RealtimeLLM[
        Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]
    ]
):
    async def _create_response_impl(
        self,
        *,
        messages: Sequence[Dict[str, Any]],
        tools: Optional[Sequence[Dict[str, Any]]],
        options: Optional[Dict[str, Any]],
        response_format: Optional[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return {"ok": True}

    async def _create_response_stream_impl(
        self,
        *,
        messages: Sequence[Dict[str, Any]],
        tools: Optional[Sequence[Dict[str, Any]]],
        options: Optional[Dict[str, Any]],
        response_format: Optional[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]],
    ) -> AsyncIterator[Dict[str, Any]]:
        if False:
            yield {}
        return

    async def connect(self, *args: Any, **kwargs: Any) -> Any:
        self._emit_connection(ConnectionState.CONNECTING)
        await asyncio.sleep(0)
        self._emit_connection(ConnectionState.CONNECTED)
        return True

    async def _disconnect_impl(self, reason: Optional[str] = None) -> None:
        await asyncio.sleep(0)

    async def send_text(self, text: str) -> None:
        return None

    async def send_audio_pcm(self, pcm, *, mime_rate: int = 48000) -> None:  # type: ignore[override]
        return None

    async def send_image(
        self,
        *,
        data: Optional[bytes] = None,
        url: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> None:
        return None

    async def send_video_frame(
        self,
        *,
        data: bytes,
        mime_type: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> None:
        return None


@pytest.mark.asyncio
async def test_llm_create_response_emits_events_and_normalized_response():
    reg = get_global_registry()
    reg.clear()

    llm = FakeLLM(provider_name="Fake", model="m1")

    # Provider-agnostic messages payload, carried through events
    messages: List[Message] = [
        {"role": Role.USER, "content": [{"type": "text", "text": "hi"}]},
    ]
    tools: List[Dict[str, Any]] = [{"name": "tool1"}]
    options: Dict[str, Any] = {"temperature": 0.1}
    response_format: Dict[str, Any] = {
        "json_schema": {"type": "object"},
        "strict": True,
    }
    metadata: Dict[str, Any] = {"trace_id": "abc"}

    result = await llm.create_response(
        messages,
        tools=tools,
        options=options,
        response_format=response_format,
        metadata=metadata,
    )

    assert result["ok"] is True

    session_events = reg.get_session_events(llm.session_id)
    # Should include initialization, request, response (at least)
    event_types = [e.event_type for e in session_events]
    assert EventType.LLM_REQUEST in event_types
    assert EventType.LLM_RESPONSE in event_types

    # Validate request payload echoed in event
    req_events = [e for e in session_events if e.event_type == EventType.LLM_REQUEST]
    assert len(req_events) == 1
    req = req_events[0]
    assert req.messages == messages
    assert req.tools == tools
    assert req.options == options
    assert req.response_format == response_format
    assert req.metadata == metadata

    # Validate normalized response present with text
    resp_events = [e for e in session_events if e.event_type == EventType.LLM_RESPONSE]
    assert len(resp_events) == 1
    norm = resp_events[0].normalized_response
    assert norm is not None
    assert norm.get("output_text") == "hello world"


@pytest.mark.asyncio
async def test_llm_create_response_error_emits_error_and_raises():
    reg = get_global_registry()
    reg.clear()

    llm = ErrorLLM(provider_name="Fake", model="m1")

    # Register a no-op error handler to satisfy pyee's 'error' semantics
    @llm.on("error")
    async def _ignore_error(_):  # type: ignore[unused-ignore]
        return None

    with pytest.raises(ValueError):
        await llm.create_response([])

    session_events = reg.get_session_events(llm.session_id)
    err_events = [e for e in session_events if e.event_type == EventType.LLM_ERROR]
    assert len(err_events) == 1
    assert err_events[0].context == "create_response"


@pytest.mark.asyncio
async def test_llm_stream_emits_normalized_and_convenience_delta_events():
    reg = get_global_registry()
    reg.clear()

    llm = FakeLLM(provider_name="Fake", model="m1")

    collected: List[Dict[str, Any]] = []
    async for item in llm.create_response_stream([]):
        collected.append(item)

    assert len(collected) == 3
    assert collected[0]["kind"] == "text"
    assert collected[1]["kind"] == "audio"
    assert collected[2]["kind"] == "done"

    session_events = reg.get_session_events(llm.session_id)
    delta_events = [
        e for e in session_events if e.event_type == EventType.LLM_STREAM_DELTA
    ]
    # Expect normalized text + convenience text, normalized audio + convenience audio, and a final delta from 'done'
    assert len(delta_events) >= 5

    text_named = [e for e in delta_events if e.event_name == "text.delta"]
    audio_named = [e for e in delta_events if e.event_name == "audio.delta"]
    assert len(text_named) >= 2  # normalized + convenience
    assert len(audio_named) >= 2  # normalized + convenience

    finals = [e for e in delta_events if getattr(e, "is_final", False)]
    assert any(f.is_final for f in finals)


def test_map_turn_input_variants():
    reg = get_global_registry()
    reg.clear()

    llm = FakeLLM(provider_name="Fake", model="m1")

    # Only text
    msgs = llm._map_turn_input(text="hello", inputs=None, state=None)
    assert msgs[0]["role"] == Role.USER
    assert msgs[0]["content"][0] == {"type": "text", "text": "hello"}

    # Text + inputs + state
    parts = [
        {"type": "image", "url": "http://example.com/image.jpg"},
        {"type": "audio", "data": b"\x00", "mime_type": "audio/wav"},
    ]
    msgs2 = llm._map_turn_input(text="t", inputs=parts, state={"k": 1})
    kinds = [p["type"] for p in msgs2[0]["content"]]
    assert kinds == ["text", "image", "audio", "json"]

    # Error when nothing provided
    with pytest.raises(ValueError):
        llm._map_turn_input(text=None, inputs=None, state=None)


def test_conversation_helpers_and_validation():
    from getstream.plugins.common.llm import Conversation

    convo = Conversation(system="sys")
    convo.add_user_text("hi")
    convo.add_assistant_text("yo")

    # valid image by data
    convo.add_user_image(data=b"abc", mime_type="image/png")

    msgs = convo.to_messages()
    roles = [m["role"] for m in msgs]
    assert roles == [Role.SYSTEM, Role.USER, Role.ASSISTANT, Role.USER]

    # invalid cases for image: both or neither
    with pytest.raises(ValueError):
        convo.add_user_image(data=b"x", url="http://example.com/x.png")
    with pytest.raises(ValueError):
        convo.add_user_image()


@pytest.mark.asyncio
async def test_realtime_llm_connection_output_track_transcript_and_close():
    reg = get_global_registry()
    reg.clear()

    r = FakeRealtime(provider_name="RT", model="m2")

    # Connect should emit CONNECTING then CONNECTED and set flag
    await r.connect()
    assert r.is_connected is True

    session_events = reg.get_session_events(r.session_id)
    conn_states = [
        e.connection_state
        for e in session_events
        if e.event_type == EventType.LLM_CONNECTION
    ]
    assert ConnectionState.CONNECTING in conn_states
    assert ConnectionState.CONNECTED in conn_states

    # Output track helpers
    track = r.create_output_track(framerate=24000, stereo=False, format="s16")
    assert r.output_track is track

    # Transcript convenience event
    r.emit_transcript("partial text", is_final=True)
    deltas = [
        e
        for e in reg.get_session_events(r.session_id)
        if e.event_type == EventType.LLM_STREAM_DELTA
    ]
    assert any(e.event_name == "transcript.delta" and e.is_final for e in deltas)

    # Close should disconnect (emit DISCONNECTED) and emit PLUGIN_CLOSED
    await r.close()

    session_events = reg.get_session_events(r.session_id)
    conn_states = [
        e.connection_state
        for e in session_events
        if e.event_type == EventType.LLM_CONNECTION
    ]
    assert ConnectionState.DISCONNECTED in conn_states
    assert any(e.event_type == EventType.PLUGIN_CLOSED for e in session_events)
