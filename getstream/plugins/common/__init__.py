"""Common abstract base classes and utilities shared by all Stream AI plugins.

Moving forward, provider wheels (`stream-plugins-deepgram`, …) should depend on
this package for the canonical definitions of STT, TTS, VAD, …
"""

from .event_metrics import (
    calculate_stt_metrics,
    calculate_tts_metrics,
    calculate_vad_metrics,
)
from .event_serialization import deserialize_event, serialize_event, serialize_events
from .event_utils import (
    EventFilter,
    EventLogger,
    EventRegistry,
    get_global_logger,
    get_global_registry,
    register_global_event,
)
from .events import (
    AudioFormat,
    BaseEvent,
    ConnectionState,
    EventType,
    LLMConnectionEvent,
    LLMErrorEvent,
    # LLM Events
    LLMRequestEvent,
    LLMResponseEvent,
    LLMStreamDeltaEvent,
    PluginClosedEvent,
    PluginErrorEvent,
    # Generic Events
    PluginInitializedEvent,
    STSAudioInputEvent,
    STSAudioOutputEvent,
    # STS Events
    STSConnectedEvent,
    STSConversationItemEvent,
    STSDisconnectedEvent,
    STSErrorEvent,
    STSResponseEvent,
    STSTranscriptEvent,
    STTConnectionEvent,
    STTErrorEvent,
    STTPartialTranscriptEvent,
    # STT Events
    STTTranscriptEvent,
    # TTS Events
    TTSAudioEvent,
    TTSConnectionEvent,
    TTSErrorEvent,
    TTSSynthesisCompleteEvent,
    TTSSynthesisStartEvent,
    VADAudioEvent,
    VADErrorEvent,
    VADPartialEvent,
    VADSpeechEndEvent,
    # VAD Events
    VADSpeechStartEvent,
    create_event,
)
from .llm import LLM, RealtimeLLM
from .sts import STS
from .stt import STT
from .tts import TTS
from .vad import VAD

__all__ = [
    # Base classes
    "STT",
    "TTS",
    "VAD",
    "STS",
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
    # LLM Events
    "LLMRequestEvent",
    "LLMStreamDeltaEvent",
    "LLMResponseEvent",
    "LLMErrorEvent",
    "LLMConnectionEvent",
    # Generic Events
    "PluginInitializedEvent",
    "PluginClosedEvent",
    "PluginErrorEvent",
    # LLM base classes
    "LLM",
    "RealtimeLLM",
    # Event utilities
    "EventFilter",
    "EventRegistry",
    "EventLogger",
    "register_global_event",
    "get_global_registry",
    "get_global_logger",
    "create_event",
    # Event serialization
    "serialize_event",
    "serialize_events",
    "deserialize_event",
    # Event metrics
    "calculate_stt_metrics",
    "calculate_tts_metrics",
    "calculate_vad_metrics",
]
