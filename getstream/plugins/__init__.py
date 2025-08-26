# Unified plugin imports - enable access to all plugin classes through getstream.plugins
try:
    # TTS Plugins
    from .cartesia.tts import CartesiaTTS
    from .elevenlabs.tts import ElevenLabsTTS
    from .kokoro.tts import KokoroTTS
except ImportError:
    # Plugins may not be installed
    pass

try:
    # STT Plugins
    from .deepgram.stt import DeepgramSTT
    from .fal.stt import FalWizperSTT
    from .moonshine.stt import MoonshineSTT
except ImportError:
    # Plugins may not be installed
    pass

try:
    # VAD Plugins
    from .silero.vad import SileroVAD
except ImportError:
    # Plugins may not be installed
    pass

try:
    # Live AI Plugins
    from .gemini.live import GeminiLive
except ImportError:
    # Plugins may not be installed
    pass

try:
    # STS Plugins
    from .openai.sts import OpenAIRealtime
except ImportError:
    # Plugins may not be installed
    pass

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
