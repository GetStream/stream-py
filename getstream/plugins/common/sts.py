import abc
import logging
from typing import Any, Dict, List, Optional

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

    def __init__(
        self,
        *,
        model: Optional[str] = None,
        instructions: Optional[str] = None,
        temperature: Optional[float] = None,
        voice: Optional[str] = None,
        provider_config: Optional[Any] = None,
        response_modalities: Optional[List[str]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **_: Any,
    ):
        """Initialize base STS with common, provider-agnostic preferences.

        These fields are optional hints that concrete providers may choose to map
        to their own session/config structures. They are not enforced here.

        Args:
            model: Model ID to use when connecting.
            instructions: Optional system instructions passed to the session.
            temperature: Optional temperature passed to the session.
            voice: Optional voice selection passed to the session.
            provider_config: Provider-specific configuration (e.g., Gemini Live config, OpenAI session prefs).
            response_modalities: Optional response modalities passed to the session.
            tools: Optional tools passed to the session.
        """
        super().__init__()
        self._is_connected = False

        # Common, optional preferences (not all providers will use all of these)
        self.model = model
        self.instructions = instructions
        self.temperature = temperature
        self.voice = voice
        # Provider-specific configuration (e.g., Gemini Live config, OpenAI session prefs)
        self.provider_config = provider_config
        self.response_modalities = response_modalities
        self.tools = tools

    @property
    def is_connected(self) -> bool:
        """Return True if the realtime session is currently active."""
        return self._is_connected


# Public re-export
__all__ = ["STS"]
