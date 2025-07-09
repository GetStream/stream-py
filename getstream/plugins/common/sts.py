import abc
import logging

from pyee.asyncio import AsyncIOEventEmitter


logger = logging.getLogger(__name__)


class STS(AsyncIOEventEmitter, abc.ABC):
    """Base class for Speech-to-Speech (STS) implementations.

    This abstract base class provides the foundation for implementing real-time
    speech-to-speech communication with AI agents. It handles event emission
    and connection state management.

    Key Features:
    - Event-driven architecture using AsyncIOEventEmitter
    - Connection state tracking
    - Standardized event interface

    Implementations should:
    1. Establish and manage the audio session
    2. Handle provider-specific authentication and setup
    3. Emit appropriate events for state changes and interactions
    4. Implement any provider-specific helper methods
    """

    def __init__(self):
        super().__init__()
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """Return True if the realtime session is currently active."""
        return self._is_connected


# Public re-export
__all__ = ["STS"]
