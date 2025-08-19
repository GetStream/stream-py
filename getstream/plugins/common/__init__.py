"""Common abstract base classes and utilities shared by all Stream AI plugins.

Moving forward, provider wheels (`stream-plugins-deepgram`, …) should depend on
this package for the canonical definitions of STT, TTS, VAD, …
"""

from .stt import STT  # noqa: F401
from .tts import TTS  # noqa: F401
from .sts import STS  # noqa: F401
from .vad import VAD  # noqa: F401

# Event system exports
from .events import *  # noqa: F401, F403
from .event_utils import (  # noqa: F401
    EventFilter, EventRegistry, EventSerializer, EventLogger, EventMetrics,
    global_event_registry, global_event_logger, register_global_event,
    get_global_registry, get_global_logger
)

__all__ = [
    # Base plugin classes
    "STT",
    "TTS", 
    "STS",
    "VAD",
    
    # Event system
    "EventType",
    "ConnectionState",
    "AudioFormat",
    "BaseEvent",
    
    # STT Events
    "STTTranscriptEvent",
    "STTPartialTranscriptEvent",
    "STTErrorEvent", 
    "STTConnectionEvent",
    
    # TTS Events
    "TTSAudioEvent",
    "TTSSynthesisStartEvent",
    "TTSSynthesisCompleteEvent",
    "TTSErrorEvent",
    "TTSConnectionEvent",
    
    # STS Events
    "STSConnectedEvent",
    "STSDisconnectedEvent",
    "STSAudioInputEvent",
    "STSAudioOutputEvent",
    "STSTranscriptEvent",
    "STSResponseEvent",
    "STSConversationItemEvent",
    "STSErrorEvent",
    
    # VAD Events
    "VADSpeechStartEvent",
    "VADSpeechEndEvent", 
    "VADAudioEvent",
    "VADPartialEvent",
    "VADErrorEvent",
    
    # Generic Events
    "PluginInitializedEvent",
    "PluginClosedEvent",
    "PluginErrorEvent",
    
    # Event utilities
    "EventFilter",
    "EventRegistry",
    "EventSerializer", 
    "EventLogger",
    "EventMetrics",
    "global_event_registry",
    "global_event_logger",
    "register_global_event",
    "get_global_registry",
    "get_global_logger",
    "create_event",
]
