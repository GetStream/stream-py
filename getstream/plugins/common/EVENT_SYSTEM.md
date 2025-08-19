# GetStream AI Plugins Event System

## Overview

The GetStream AI Plugins Event System provides a structured, type-safe approach to event handling across all plugin types (STT, TTS, STS, VAD). This system replaces the previous loose dictionary-based events with strongly-typed data classes that provide better debugging, logging, and integration capabilities.

## Key Features

- **Type Safety**: All events are defined as dataclasses with proper typing
- **Consistent Structure**: Standardized event format across all plugin types
- **Automatic Metadata**: Events include timestamps, unique IDs, and session tracking
- **Global Registry**: Central event tracking and analysis capabilities
- **Backward Compatibility**: Legacy event formats are still supported during transition
- **Rich Debugging**: Enhanced logging and tracing capabilities

## Event Architecture

### Base Event Structure

All events inherit from `BaseEvent` which provides:

```python
@dataclass
class BaseEvent:
    event_type: EventType
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    user_metadata: Optional[Dict[str, Any]] = None
    plugin_name: Optional[str] = None
    plugin_version: Optional[str] = None
```

### Event Types

Events are categorized by type using the `EventType` enum:

- **STT Events**: `STT_TRANSCRIPT`, `STT_PARTIAL_TRANSCRIPT`, `STT_ERROR`, `STT_CONNECTION`
- **TTS Events**: `TTS_AUDIO`, `TTS_SYNTHESIS_START`, `TTS_SYNTHESIS_COMPLETE`, `TTS_ERROR`
- **STS Events**: `STS_CONNECTED`, `STS_DISCONNECTED`, `STS_TRANSCRIPT`, `STS_RESPONSE`, etc.
- **VAD Events**: `VAD_SPEECH_START`, `VAD_SPEECH_END`, `VAD_AUDIO`, `VAD_PARTIAL`, `VAD_ERROR`
- **Generic Events**: `PLUGIN_INITIALIZED`, `PLUGIN_CLOSED`, `PLUGIN_ERROR`

## Plugin-Specific Events

### STT (Speech-to-Text) Events

#### STTTranscriptEvent
Emitted when a complete transcript is available.

```python
@dataclass
class STTTranscriptEvent(BaseEvent):
    text: str = ""
    confidence: float = 1.0
    language: Optional[str] = None
    processing_time_ms: Optional[float] = None
    audio_duration_ms: Optional[float] = None
    model_name: Optional[str] = None
    words: Optional[List[Dict[str, Any]]] = None
    is_final: bool = True
```

#### STTPartialTranscriptEvent
Emitted when a partial transcript is available.

```python
@dataclass
class STTPartialTranscriptEvent(BaseEvent):
    text: str = ""
    confidence: float = 1.0
    # ... similar fields to STTTranscriptEvent
    is_final: bool = False
```

### TTS (Text-to-Speech) Events

#### TTSAudioEvent
Emitted when TTS audio data is available.

```python
@dataclass
class TTSAudioEvent(BaseEvent):
    audio_data: bytes
    audio_format: AudioFormat = AudioFormat.PCM_S16
    sample_rate: int = 16000
    channels: int = 1
    chunk_index: int = 0
    is_final_chunk: bool = True
    text_source: Optional[str] = None
    synthesis_id: Optional[str] = None
```

#### TTSSynthesisStartEvent / TTSSynthesisCompleteEvent
Track synthesis lifecycle with timing and performance metrics.

### VAD (Voice Activity Detection) Events

#### VADSpeechStartEvent / VADSpeechEndEvent
Mark the beginning and end of speech segments.

#### VADAudioEvent
Emitted when VAD detects a complete speech segment.

```python
@dataclass
class VADAudioEvent(BaseEvent):
    audio_data: bytes  # PCM audio data
    sample_rate: int
    audio_format: AudioFormat = AudioFormat.PCM_S16
    channels: int = 1
    duration_ms: float
    speech_probability: float
    frame_count: int
```

### STS (Speech-to-Speech) Events

STS events cover the complete conversation flow including connection management, audio I/O, transcripts, and responses.

## Usage Examples

### Basic Event Handling

```python
from getstream.plugins.common import STT, STTTranscriptEvent

# Create STT plugin
stt = MySTTPlugin(provider_name="my_provider")

# Handle structured events
@stt.on("transcript")
async def on_transcript(event: STTTranscriptEvent):
    print(f"Final transcript: {event.text}")
    print(f"Confidence: {event.confidence}")
    print(f"Processing time: {event.processing_time_ms}ms")
    print(f"Event ID: {event.event_id}")

# Handle legacy events (for backward compatibility)
@stt.on("transcript_legacy")
async def on_transcript_legacy(text: str, user_metadata: dict, metadata: dict):
    print(f"Legacy transcript: {text}")
```

### Event Filtering and Analysis

```python
from getstream.plugins.common import EventFilter, get_global_registry

# Create event filter
filter_criteria = EventFilter(
    event_types=[EventType.STT_TRANSCRIPT, EventType.STT_PARTIAL_TRANSCRIPT],
    time_window_ms=60000,  # Last minute
    min_confidence=0.8
)

# Get filtered events
registry = get_global_registry()
recent_transcripts = registry.get_events(filter_criteria, limit=10)

# Analyze events
for event in recent_transcripts:
    print(f"Event: {event.event_type.value}")
    print(f"Text: {event.text}")
    print(f"Confidence: {event.confidence}")
```

### Performance Metrics

```python
from getstream.plugins.common import EventMetrics, EventType

# Get all STT events
stt_events = registry.get_events(
    EventFilter(event_types=[
        EventType.STT_TRANSCRIPT, 
        EventType.STT_PARTIAL_TRANSCRIPT
    ])
)

# Calculate performance metrics
metrics = EventMetrics.calculate_stt_metrics(stt_events)
print(f"Average processing time: {metrics['avg_processing_time_ms']}ms")
print(f"Average confidence: {metrics['avg_confidence']}")
print(f"Total transcripts: {metrics['total_transcripts']}")
```

### Event Serialization

```python
from getstream.plugins.common import EventSerializer

# Serialize events for storage
events_json = EventSerializer.serialize_events(recent_transcripts)

# Save to file
with open("transcript_events.json", "w") as f:
    f.write(events_json)

# Deserialize events
with open("transcript_events.json", "r") as f:
    events_data = json.load(f)

restored_events = [
    EventSerializer.deserialize_event(event_data) 
    for event_data in events_data
]
```

## Migration Guide

### From Legacy Events to Structured Events

**Before (Legacy):**
```python
@stt.on("transcript")
async def on_transcript(text: str, user_metadata: dict, metadata: dict):
    confidence = metadata.get("confidence", 1.0)
    processing_time = metadata.get("processing_time_ms")
    print(f"Transcript: {text} (confidence: {confidence})")
```

**After (Structured):**
```python
@stt.on("transcript")
async def on_transcript(event: STTTranscriptEvent):
    print(f"Transcript: {event.text} (confidence: {event.confidence})")
    print(f"Event ID: {event.event_id}")
    print(f"Session: {event.session_id}")
    print(f"Processing time: {event.processing_time_ms}ms")
```

### Gradual Migration Strategy

1. **Phase 1**: Update event handlers to use structured events
2. **Phase 2**: Start using event registry and analysis tools
3. **Phase 3**: Remove legacy event handlers
4. **Phase 4**: Full adoption of structured event system

## Plugin Implementation Guidelines

### For Plugin Authors

When creating new plugins, follow these patterns:

```python
class MySTTPlugin(STT):
    def __init__(self, **kwargs):
        super().__init__(provider_name="my_provider", **kwargs)
    
    async def _process_audio_impl(self, pcm_data, user_metadata=None):
        # Process audio...
        
        # For synchronous plugins, return results
        metadata = {
            "confidence": 0.95,
            "processing_time_ms": 150.0,
            "model_name": "my_model_v1"
        }
        return [(True, "transcribed text", metadata)]
    
    async def close(self):
        # Cleanup resources
        await super().close()  # This emits the closure event
```

### For Asynchronous Plugins

```python
class MyAsyncSTTPlugin(STT):
    async def _process_audio_impl(self, pcm_data, user_metadata=None):
        # Send audio to streaming service
        # Events will be emitted when responses arrive
        self.send_audio_to_service(pcm_data)
        
        # Return None for asynchronous mode
        return None
    
    def on_service_response(self, response):
        # Emit structured events directly
        metadata = {
            "confidence": response.confidence,
            "processing_time_ms": response.processing_time,
        }
        self._emit_transcript_event(response.text, self._current_user, metadata)
```

## Event Registry and Analytics

### Global Event Registry

The global event registry automatically tracks all events across all plugins:

```python
from getstream.plugins.common import get_global_registry

registry = get_global_registry()

# Get statistics
stats = registry.get_statistics()
print(f"Total events: {stats['total_events']}")
print(f"Error rate: {stats['error_summary']['error_rate']:.2%}")

# Get session-specific events
session_events = registry.get_session_events("session_123")
```

### Custom Event Listeners

Register global event listeners:

```python
from getstream.plugins.common import EventType, get_global_registry

registry = get_global_registry()

def on_any_error(event):
    print(f"Error in {event.plugin_name}: {event.error_message}")

# Listen to all error events globally
registry.add_listener(EventType.STT_ERROR, on_any_error)
registry.add_listener(EventType.TTS_ERROR, on_any_error)
registry.add_listener(EventType.VAD_ERROR, on_any_error)
```

## Best Practices

### 1. Always Use Structured Events
- Prefer structured events over legacy events for new code
- Include rich metadata in events
- Use appropriate event types for different scenarios

### 2. Session Management
- Use consistent session IDs across related plugins
- Track user context through session metadata

### 3. Error Handling
- Emit detailed error events with context
- Include recovery suggestions when possible
- Log errors with structured data

### 4. Performance Monitoring
- Include timing information in events
- Monitor real-time factors for TTS
- Track confidence scores for STT

### 5. Event Filtering
- Use event filters for efficient event processing
- Implement time-based filtering for recent events
- Filter by confidence thresholds for quality control

## Troubleshooting

### Common Issues

1. **Missing Events**: Ensure plugins call `super().__init__()` and `super().close()`
2. **Duplicate Events**: Check that plugins don't both return results AND emit events
3. **Performance Issues**: Use event filtering to limit event processing scope
4. **Memory Usage**: Configure appropriate max_events limits for registries

### Debugging Tips

```python
# Enable detailed event logging
import logging
logging.getLogger("getstream.plugins.events").setLevel(logging.DEBUG)

# Monitor event flow
from getstream.plugins.common import get_global_logger

logger = get_global_logger()
registry = logger.get_registry()

# Print recent events
recent_events = registry.get_events(limit=10)
for event in recent_events:
    print(f"{event.timestamp}: {event.event_type.value} - {event.plugin_name}")
```

## Future Enhancements

- **Event Streaming**: Real-time event streaming to external systems
- **Event Persistence**: Long-term storage of events in databases
- **Advanced Analytics**: ML-based event pattern analysis
- **Distributed Events**: Event synchronization across multiple instances
- **Custom Event Types**: Plugin-specific event type registration

## API Reference

See the individual module documentation for complete API details:

- `getstream.plugins.common.events` - Event class definitions
- `getstream.plugins.common.event_utils` - Event utilities and registry
- `getstream.plugins.common.stt` - STT base class with events
- `getstream.plugins.common.tts` - TTS base class with events
- `getstream.plugins.common.vad` - VAD base class with events
- `getstream.plugins.common.sts` - STS base class with events
