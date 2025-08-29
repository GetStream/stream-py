import abc
import logging
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pyee.asyncio import AsyncIOEventEmitter

from getstream.video.rtc.audio_track import AudioStreamTrack
from getstream.video.rtc.track_util import PcmData

from .event_utils import register_global_event
from .events import (
    ConnectionState,
    LLMConnectionEvent,
    LLMErrorEvent,
    LLMRequestEvent,
    LLMResponseEvent,
    LLMStreamDeltaEvent,
    PluginClosedEvent,
    PluginInitializedEvent,
)
from .llm_types import ImageBytesPart, ImageURLPart, Message, Role

logger = logging.getLogger(__name__)


class LLM(AsyncIOEventEmitter, abc.ABC):
    """Base class for multimodal LLM providers.

    Responsibilities:
    - Normalize requests (messages, tools, options)
    - Emit structured events (request, delta, response, error, usage in response payload)
    - Provide sync and streaming APIs via abstract provider hooks
    """

    def __init__(
        self,
        *,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        client: Optional[Any] = None,
        **_: Any,
    ):
        super().__init__()
        self.session_id = str(uuid.uuid4())
        self.provider_name = provider_name or self.__class__.__name__
        self.model = model
        self.client: Optional[Any] = client

        # Emit initialization event
        init_event = PluginInitializedEvent(
            session_id=self.session_id,
            plugin_name=self.provider_name,
            plugin_type="LLM",
            provider=self.provider_name,
            configuration={"model": self.model} if self.model else None,
        )
        register_global_event(init_event)
        self.emit("initialized", init_event)

    async def generate(
        self,
        messages: List[Message],
        *,
        tools: Optional[List[Dict[str, Any]]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run a non-streaming generation.

        Emits LLM_REQUEST and then either LLM_RESPONSE or LLM_ERROR.
        Returns a normalized response dict (provider-agnostic).

        Expected normalized result shape:
            {
                "message": Message,
                "tool_calls": Optional[List[Dict[str, Any]]],
                "usage": Optional[Dict[str, Any]]
            }
        """
        req_event = LLMRequestEvent(
            session_id=self.session_id,
            plugin_name=self.provider_name,
            model_name=self.model,
            messages=messages,
            tools=tools,
            options=options,
        )
        register_global_event(req_event)
        self.emit("request", req_event)

        try:
            result = await self._generate_impl(
                messages=messages, tools=tools, options=options
            )

            resp_event = LLMResponseEvent(
                session_id=self.session_id,
                plugin_name=self.provider_name,
                message=result.get("message"),
                tool_calls=result.get("tool_calls"),
                usage=result.get("usage"),
                is_complete=True,
            )
            register_global_event(resp_event)
            self.emit("response", resp_event)

            return result
        except Exception as e:
            err_event = LLMErrorEvent(
                session_id=self.session_id,
                plugin_name=self.provider_name,
                error=e,
                context="generate",
            )
            register_global_event(err_event)
            self.emit("error", err_event)
            raise

    async def stream(
        self,
        messages: List[Message],
        *,
        tools: Optional[List[Dict[str, Any]]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Run a streaming generation.

        Emits LLM_REQUEST, then a sequence of LLM_STREAM_DELTA events, and a final LLM_RESPONSE.
        Yields provider-agnostic delta dicts.

        Delta shape (minimum): { "content_delta": str } or provider-specific keys.
        """
        req_event = LLMRequestEvent(
            session_id=self.session_id,
            plugin_name=self.provider_name,
            model_name=self.model,
            messages=messages,
            tools=tools,
            options=options,
        )
        register_global_event(req_event)
        self.emit("request", req_event)

        iterator = await self._stream_impl(
            messages=messages, tools=tools, options=options
        )
        async for delta in iterator:
            delta_event = LLMStreamDeltaEvent(
                session_id=self.session_id,
                plugin_name=self.provider_name,
                delta=delta,
                is_final=bool(delta.get("is_final")),
            )
            register_global_event(delta_event)
            self.emit("delta", delta_event)
            yield delta

    @abc.abstractmethod
    async def _generate_impl(
        self,
        *,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]],
        options: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Provider-specific non-streaming implementation.

        Implementations should return the normalized result shape described in generate().
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def _stream_impl(
        self,
        *,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]],
        options: Optional[Dict[str, Any]],
    ) -> AsyncIterator[Dict[str, Any]]:
        """Provider-specific streaming implementation.

        Implementations should `yield` normalized deltas; a final response event will
        typically be emitted by the provider when the stream ends (if available).
        """
        raise NotImplementedError

    async def close(self):
        """Close the LLM and release any resources."""
        close_event = PluginClosedEvent(
            session_id=self.session_id,
            plugin_name=self.provider_name,
            plugin_type="LLM",
            provider=self.provider_name,
            cleanup_successful=True,
        )
        register_global_event(close_event)
        self.emit("closed", close_event)


class RealtimeLLM(LLM):
    """Base class for realtime-capable LLM providers.

    Adds connection lifecycle and event emission. Concrete classes should
    manage the underlying session and forward provider events into the LLM events.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._is_connected = False
        self._output_track: Optional[AudioStreamTrack] = None

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @abc.abstractmethod
    async def connect(self, *args: Any, **kwargs: Any) -> Any:
        """Establish a realtime session.

        Guidance on state events:
        - Emit ConnectionState.CONNECTING before network activity, then CONNECTED on success
        - Emit RECONNECTING on transient reconnect attempts
        - Emit ERROR on unrecoverable failures (and then DISCONNECTED)
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def _disconnect_impl(self, reason: Optional[str] = None) -> None:
        """Provider-specific disconnect (close sockets, tasks, etc.)."""
        raise NotImplementedError

    async def disconnect(self, reason: Optional[str] = None) -> None:
        """Disconnect the realtime session and emit a DISCONNECTED connection event."""
        await self._disconnect_impl(reason)
        self._emit_connection(
            ConnectionState.DISCONNECTED, {"reason": reason} if reason else None
        )

    def _emit_connection(
        self, state: ConnectionState, details: Optional[Dict[str, Any]] = None
    ) -> None:
        self._is_connected = state == ConnectionState.CONNECTED
        event = LLMConnectionEvent(
            session_id=self.session_id,
            plugin_name=self.provider_name,
            connection_state=state,
            details=details,
        )
        register_global_event(event)
        self.emit("connection", event)

    # Realtime helpers
    def set_output_track(self, track: AudioStreamTrack) -> None:
        """Set an audio output track for providers that return audio in realtime.

        Providers should write audio bytes to `self.output_track.write(...)` when producing audio.
        """
        self._output_track = track

    @property
    def output_track(self) -> Optional[AudioStreamTrack]:
        return self._output_track

    @abc.abstractmethod
    async def send_text(self, text: str) -> None:
        """Send a text input into the realtime session."""
        raise NotImplementedError

    @abc.abstractmethod
    async def send_audio_pcm(self, pcm: PcmData, *, mime_rate: int = 48000) -> None:
        """Send audio PCM into the realtime session (provider should resample if needed)."""
        raise NotImplementedError

    @abc.abstractmethod
    async def send_image(
        self,
        *,
        data: Optional[bytes] = None,
        url: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> None:
        """Send an image (bytes or URL) into the realtime session."""
        raise NotImplementedError

    async def close(self):
        # If connected, disconnect first
        if self._is_connected:
            await self.disconnect("service_closed")
        await super().close()


class Conversation:
    """Lightweight helper to accumulate messages for turn-based interactions.

    This is purely optional and provider-agnostic; it helps build a message list to
    pass into LLM.generate/stream.
    """

    def __init__(self, system: Optional[str] = None):
        self.messages: List[Message] = []
        if system:
            self.add_system(system)

    def add_system(self, text: str) -> None:
        self.messages.append(
            {
                "role": Role.SYSTEM,
                "content": [{"type": "text", "text": text}],
            }
        )

    def add_user_text(self, text: str) -> None:
        self.messages.append(
            {
                "role": Role.USER,
                "content": [{"type": "text", "text": text}],
            }
        )

    def add_user_image(
        self,
        *,
        data: Optional[bytes] = None,
        url: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> None:
        if (data is None) == (url is None):
            raise ValueError("Provide exactly one of data or url for image input")

        image_part: Union[ImageBytesPart, ImageURLPart]
        if data is not None:
            image_part = {"type": "image", "data": data}
        else:
            image_part = {"type": "image", "url": url}  # type: ignore[arg-type]

        if mime_type is not None:
            image_part["mime_type"] = mime_type

        self.messages.append(
            {
                "role": Role.USER,
                "content": [image_part],
            }
        )

    def add_assistant_text(self, text: str) -> None:
        self.messages.append(
            {
                "role": Role.ASSISTANT,
                "content": [{"type": "text", "text": text}],
            }
        )

    def to_messages(self) -> List[Message]:
        return list(self.messages)
