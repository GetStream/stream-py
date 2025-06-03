import abc
import logging

from pyee.asyncio import AsyncIOEventEmitter


logger = logging.getLogger(__name__)


class STS(AsyncIOEventEmitter, abc.ABC):
    """Speech-to-Speech (full duplex) base class.

    Implementations are expected to:
    • establish an audio session (usually via Stream Video `Call.connect_openai`)
    • emit high-level events coming from the AI agent (for example
      ``conversation.updated`` or ``error``)
    • optionally expose helper methods like ``update_session`` or
      ``send_user_message``.

    Events emitted by *all* STS implementations:
        - *connected*: fired once the underlying websocket is ready
        - *disconnected*: fired when the websocket is closed (graceful or error)
        - *error*: emitted for any exception that bubbles up
        - *<any other event type coming from the provider>*: forwarded verbatim
    """

    def __init__(self):
        super().__init__()
        self._is_connected = False

    # ---------------------------------------------------------------------
    # Lifecycle helpers
    # ---------------------------------------------------------------------
    @abc.abstractmethod
    async def connect(self, *args, **kwargs):  # pragma: no cover
        """Establish the realtime connection (provider-specific)."""

    @abc.abstractmethod
    async def close(self):  # pragma: no cover
        """Close the connection and release all resources."""

    # Derived classes should set ``self._is_connected`` accordingly so that
    # embedders can introspect the state.
    # ---------------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        """Return True if the realtime session is currently active."""
        return self._is_connected

# Public re-export
__all__ = ["STS"]
