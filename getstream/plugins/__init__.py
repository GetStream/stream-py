# Unified plugin imports - enable access to all plugin classes through getstream.plugins

# TTS Plugins
try:
    from .cartesia.tts import CartesiaTTS
except ImportError:
    CartesiaTTS = None

try:
    from .elevenlabs.tts import ElevenLabsTTS
except ImportError:
    ElevenLabsTTS = None

try:
    from .kokoro.tts import KokoroTTS
except ImportError:
    KokoroTTS = None

# STT Plugins
try:
    from .deepgram.stt import DeepgramSTT
except ImportError:
    DeepgramSTT = None

try:
    from .fal.stt import FalWizperSTT
except ImportError:
    FalWizperSTT = None

try:
    from .moonshine.stt import MoonshineSTT
except ImportError:
    MoonshineSTT = None

# VAD Plugins
try:
    from .silero.vad import SileroVAD
except ImportError:
    SileroVAD = None

# Live AI Plugins
try:
    from .gemini.live import GeminiLive
except ImportError:
    GeminiLive = None

# STS Plugins
try:
    from .openai.sts import OpenAIRealtime
except ImportError:
    OpenAIRealtime = None

# Common plugin base classes and utilities
from .common import (
    STT,
    TTS,
    VAD,
    STS,
    EventType,
    ConnectionState,
    AudioFormat,
    BaseEvent,
    STTTranscriptEvent,
    STTPartialTranscriptEvent,
    STTErrorEvent,
    STTConnectionEvent,
    TTSAudioEvent,
    TTSSynthesisStartEvent,
    TTSSynthesisCompleteEvent,
    TTSErrorEvent,
    TTSConnectionEvent,
    STSConnectedEvent,
    STSDisconnectedEvent,
    STSAudioInputEvent,
    STSAudioOutputEvent,
    STSTranscriptEvent,
    STSResponseEvent,
    STSConversationItemEvent,
    STSErrorEvent,
    VADSpeechStartEvent,
    VADSpeechEndEvent,
    VADAudioEvent,
    VADPartialEvent,
    VADErrorEvent,
    PluginInitializedEvent,
    PluginClosedEvent,
    PluginErrorEvent,
    EventFilter,
    EventRegistry,
    EventLogger,
    register_global_event,
    get_global_registry,
    get_global_logger,
    serialize_event,
    serialize_events,
    deserialize_event,
    calculate_stt_metrics,
    calculate_tts_metrics,
    calculate_vad_metrics,
    create_event,
)

def is_plugin_available(plugin_class):
    """Check if a specific plugin is available.
    
    Args:
        plugin_class: The plugin class to check (e.g., CartesiaTTS)
        
    Returns:
        bool: True if the plugin is available, False otherwise
    """
    return plugin_class is not None

def get_available_plugins():
    """Get a list of all available plugin classes.
    
    Returns:
        dict: Dictionary mapping plugin names to their classes if available
    """
    return {
        'CartesiaTTS': CartesiaTTS,
        'ElevenLabsTTS': ElevenLabsTTS,
        'KokoroTTS': KokoroTTS,
        'DeepgramSTT': DeepgramSTT,
        'FalWizperSTT': FalWizperSTT,
        'MoonshineSTT': MoonshineSTT,
        'SileroVAD': SileroVAD,
        'GeminiLive': GeminiLive,
        'OpenAIRealtime': OpenAIRealtime,
    }

# Only export successfully imported plugins
__all__ = [
    # Plugin classes (only include if successfully imported)
    'CartesiaTTS' if CartesiaTTS is not None else None,
    'ElevenLabsTTS' if ElevenLabsTTS is not None else None,
    'KokoroTTS' if KokoroTTS is not None else None,
    'DeepgramSTT' if DeepgramSTT is not None else None,
    'FalWizperSTT' if FalWizperSTT is not None else None,
    'MoonshineSTT' if MoonshineSTT is not None else None,
    'SileroVAD' if SileroVAD is not None else None,
    'GeminiLive' if GeminiLive is not None else None,
    'OpenAIRealtime' if OpenAIRealtime is not None else None,
    # Helper functions
    'is_plugin_available',
    'get_available_plugins',
    # Common classes and utilities
    'STT', 'TTS', 'VAD', 'STS',
    'EventType', 'ConnectionState', 'AudioFormat', 'BaseEvent',
    'STTTranscriptEvent', 'STTPartialTranscriptEvent', 'STTErrorEvent', 'STTConnectionEvent',
    'TTSAudioEvent', 'TTSSynthesisStartEvent', 'TTSSynthesisCompleteEvent', 'TTSErrorEvent', 'TTSConnectionEvent',
    'STSConnectedEvent', 'STSDisconnectedEvent', 'STSAudioInputEvent', 'STSAudioOutputEvent',
    'STSTranscriptEvent', 'STSResponseEvent', 'STSConversationItemEvent', 'STSErrorEvent',
    'VADSpeechStartEvent', 'VADSpeechEndEvent', 'VADAudioEvent', 'VADPartialEvent', 'VADErrorEvent',
    'PluginInitializedEvent', 'PluginClosedEvent', 'PluginErrorEvent',
    'EventFilter', 'EventRegistry', 'EventLogger',
    'register_global_event', 'get_global_registry', 'get_global_logger',
    'serialize_event', 'serialize_events', 'deserialize_event',
    'calculate_stt_metrics', 'calculate_tts_metrics', 'calculate_vad_metrics',
    'create_event',
]

# Filter out None values from __all__
__all__ = [item for item in __all__ if item is not None]
