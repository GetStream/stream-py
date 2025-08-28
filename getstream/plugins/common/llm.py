import abc
import logging
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional

from pyee.asyncio import AsyncIOEventEmitter

from .event_utils import register_global_event
from .events import (
    LLMConnectionEvent,
    LLMErrorEvent,
    LLMRequestEvent,
    LLMResponseEvent,
    LLMStreamDeltaEvent,
    PluginClosedEvent,
    PluginInitializedEvent,
)

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
        **_: Any,
    ):
        super().__init__()
        self.session_id = str(uuid.uuid4())
        self.provider_name = provider_name or self.__class__.__name__
        self.model = model

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
        messages: List[Dict[str, Any]],
        *,
        tools: Optional[List[Dict[str, Any]]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run a non-streaming generation.

        Emits LLM_REQUEST and then either LLM_RESPONSE or LLM_ERROR.
        Returns a normalized response dict (provider-agnostic).
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
        messages: List[Dict[str, Any]],
        *,
        tools: Optional[List[Dict[str, Any]]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Run a streaming generation.

        Emits LLM_REQUEST, then a sequence of LLM_STREAM_DELTA events, and a final LLM_RESPONSE.
        Yields provider-agnostic delta dicts.
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

        async for delta in self._stream_impl(
            messages=messages, tools=tools, options=options
        ):
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
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        options: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Provider-specific non-streaming implementation."""
        raise NotImplementedError

    @abc.abstractmethod
    async def _stream_impl(
        self,
        *,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        options: Optional[Dict[str, Any]],
    ) -> AsyncIterator[Dict[str, Any]]:
        """Provider-specific streaming implementation."""
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

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    async def connect(self, *args: Any, **kwargs: Any) -> Any:
        """Establish a realtime session. Subclasses should override and call _emit_connection()."""
        raise NotImplementedError

    async def disconnect(self, reason: Optional[str] = None) -> None:
        if self._is_connected:
            self._is_connected = False
            event = LLMConnectionEvent(
                session_id=self.session_id,
                plugin_name=self.provider_name,
                connection_state=None,
                details={"reason": reason} if reason else None,
            )
            register_global_event(event)
            self.emit("connection", event)

    def _emit_connection(
        self, state: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        self._is_connected = state == "connected"
        event = LLMConnectionEvent(
            session_id=self.session_id,
            plugin_name=self.provider_name,
            details=details,
        )
        register_global_event(event)
        self.emit("connection", event)
