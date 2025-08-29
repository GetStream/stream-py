# OpenTelemetry Integration for Stream AI Plugins

This document describes the comprehensive OpenTelemetry integration for Stream AI plugins, providing observability through tracing, metrics, and logging.


## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Plugin Code  │───▶│ TelemetryEvent   │───▶│ OpenTelemetry   │
│                 │    │    Emitter       │    │     SDK        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ TelemetryEvent   │    │   Exporters    │
                       │    Registry      │    │ (OTLP, Console)│
                       └──────────────────┘    └─────────────────┘
```

## Core Components

### 1. PluginTelemetry

The main telemetry class that initializes and manages OpenTelemetry SDK.

```python
from getstream.plugins.common import PluginTelemetry, TelemetryConfig

# Initialize with custom configuration
config = TelemetryConfig(
    service_name="my-plugin",
    enable_tracing=True,
    enable_metrics=True,
    otlp_endpoint="http://localhost:4317"
)

telemetry = PluginTelemetry(config)
```

### 2. TelemetryEventEmitter

Enhanced event emitter with automatic telemetry integration.

```python
from getstream.plugins.common import TelemetryEventEmitter

emitter = TelemetryEventEmitter("stt_plugin")

# Basic event emission with telemetry
emitter.emit(event)

# Event emission within trace span
emitter.emit_with_trace(event, "transcribe_audio", {"audio_size": len(audio)})

# Operation timing with context manager
with emitter.operation_context("batch_process", {"file_count": 10}):
    # Process files
    pass
```

### 3. TelemetryEventRegistry

Enhanced event registry with telemetry capabilities.

```python
from getstream.plugins.common import TelemetryEventRegistry

registry = TelemetryEventRegistry(
    max_events=10000,
    enable_metrics=True,
    enable_tracing=True
)

# Register events with automatic telemetry
registry.register_event(event)

# Get comprehensive statistics
stats = registry.get_statistics()
error_summary = registry.get_error_summary()
performance_summary = registry.get_performance_summary()
```

## Configuration

### Environment Variables

The integration can be configured through environment variables:

```bash
# Service information
export OTEL_SERVICE_NAME="getstream-plugins"
export OTEL_SERVICE_VERSION="0.2.0"
export OTEL_SERVICE_NAMESPACE="getstream"

# Feature flags
export OTEL_TRACES_ENABLED="true"
export OTEL_METRICS_ENABLED="true"
export OTEL_LOGS_ENABLED="true"

# Exporters
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
export OTEL_EXPORTER_OTLP_PROTOCOL="http"
export OTEL_EXPORTER_OTLP_HEADERS="authorization=Bearer token"

# Plugin-specific settings
export OTEL_PLUGIN_METRICS="true"
export OTEL_EVENT_TRACING="true"
export OTEL_PERFORMANCE_METRICS="true"
```

### Programmatic Configuration

```python
from getstream.plugins.common import TelemetryConfig

config = TelemetryConfig(
    service_name="custom-service",
    service_version="1.0.0",
    enable_tracing=True,
    enable_metrics=True,
    otlp_endpoint="https://collector.example.com:4317",
    otlp_protocol="grpc",
    otlp_headers={"authorization": "Bearer token"},
    enable_console_export=True,
    enable_plugin_metrics=True,
    enable_event_tracing=True,
    enable_performance_metrics=True
)
```

## Usage Patterns

### 1. Basic Plugin Integration

```python
class MySTTPlugin:
    def __init__(self):
        self.telemetry = get_telemetry()
        self.event_emitter = TelemetryEventEmitter("my_stt_plugin")
    
    async def transcribe(self, audio_data: bytes) -> str:
        with self.event_emitter.operation_context("transcribe"):
            # Process audio
            result = await self._process_audio(audio_data)
            
            # Create and emit event
            event = create_event(EventType.STT_TRANSCRIPT, text=result)
            self.event_emitter.emit(event)
            
            return result
```

### 2. Advanced Tracing

```python
class MyTTSPlugin:
    def __init__(self):
        self.telemetry = get_telemetry()
        self.event_emitter = TelemetryEventEmitter("my_tts_plugin")
    
    async def synthesize(self, text: str) -> bytes:
        # Start operation with custom attributes
        self.event_emitter.start_operation("synthesize", {
            "text_length": len(text),
            "language": "en-US"
        })
        
        try:
            # Process synthesis
            audio_data = await self._synthesize_text(text)
            
            # Emit completion event
            completion_event = create_event(
                EventType.TTS_SYNTHESIS_COMPLETE,
                text=text,
                audio_data=audio_data
            )
            
            self.event_emitter.end_operation(
                "synthesize",
                success=True,
                event=completion_event
            )
            
            return audio_data
            
        except Exception as e:
            self.event_emitter.end_operation("synthesize", success=False)
            self.event_emitter.emit_error(e, EventType.TTS_ERROR)
            raise
```

### 3. Batch Processing

```python
async def process_batch(self, items: List[Any]):
    with self.event_emitter.operation_context("batch_process", {
        "item_count": len(items),
        "batch_id": str(uuid.uuid4())
    }):
        results = []
        
        for i, item in enumerate(items):
            try:
                result = await self._process_item(item)
                results.append(result)
                
                # Emit progress event
                progress_event = create_event(
                    EventType.PLUGIN_PROGRESS,
                    progress_percentage=(i + 1) / len(items) * 100
                )
                self.event_emitter.emit(progress_event)
                
            except Exception as e:
                self.telemetry.record_error(e, {
                    "item_index": i,
                    "item_type": type(item).__name__
                })
        
        return results
```

### 4. Error Handling

```python
async def safe_operation(self):
    try:
        return await self._perform_operation()
    except Exception as e:
        # Record error with context
        self.telemetry.record_error(e, {
            "operation": "perform_operation",
            "plugin": self.plugin_name,
            "session_id": self.session_id
        })
        
        # Emit error event
        self.event_emitter.emit_error(
            e,
            EventType.PLUGIN_ERROR,
            {"operation": "perform_operation"}
        )
        
        raise
```

## Metrics

### Automatic Metrics

The integration automatically collects:

- **Event Counts**: Total events by type, plugin, and session
- **Processing Times**: Histograms of operation durations
- **Confidence Scores**: Distribution of confidence values
- **Error Rates**: Error counts and types
- **Registry Performance**: Query times and operation metrics

### Custom Metrics

```python
# Create custom metrics
meter = self.telemetry.get_meter("custom.metrics")

# Counter
request_counter = meter.create_counter(
    name="requests.total",
    description="Total number of requests",
    unit="1"
)

# Histogram
latency_histogram = meter.create_histogram(
    name="request.latency",
    description="Request latency",
    unit="ms"
)

# Gauge
active_connections = meter.create_up_down_counter(
    name="connections.active",
    description="Active connections",
    unit="1"
)

# Record metrics
request_counter.add(1, {"endpoint": "/api/transcribe"})
latency_histogram.record(150.5, {"endpoint": "/api/transcribe"})
active_connections.add(1)
```

## Tracing

### Automatic Spans

The integration creates spans for:

- Plugin operations
- Event registration
- Error handling
- Performance monitoring

### Custom Spans

```python
# Create custom spans
with self.telemetry.trace_span(
    "custom.operation",
    attributes={
        "plugin.name": self.plugin_name,
        "operation.type": "custom"
    }
) as span:
    # Add span events
    span.add_event("operation.started")
    
    # Perform operation
    result = await self._perform_operation()
    
    # Add span attributes
    span.set_attribute("result.size", len(result))
    
    # Add span events
    span.add_event("operation.completed")
    
    return result
```

### Span Attributes

Common span attributes include:

- `plugin.name`: Name of the plugin
- `operation.name`: Name of the operation
- `session.id`: Session identifier
- `event.type`: Type of event being processed
- `processing_time_ms`: Processing time in milliseconds
- `confidence`: Confidence score (for applicable events)
- `audio_duration_ms`: Audio duration (for audio events)

## Logging

### Structured Logging

The integration provides structured logging with:

- Trace correlation IDs
- Event context information
- Performance metrics
- Error details
- Plugin metadata

### Log Format

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "getstream.plugins.stt_plugin",
  "message": "Event: stt_transcript",
  "event_type": "stt_transcript",
  "event_id": "uuid-123",
  "session_id": "session-456",
  "plugin_name": "stt_plugin",
  "text_length": 25,
  "confidence": 0.95,
  "processing_time_ms": 150.5
}
```

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.getLogger("getstream.plugins.telemetry").setLevel(logging.DEBUG)
```

### Health Checks

Monitor telemetry health:

```python
# Check telemetry status
telemetry = get_telemetry()
if telemetry._initialized:
    print("Telemetry is healthy")
else:
    print("Telemetry initialization failed")

# Check registry health
registry = get_global_telemetry_registry()
stats = registry.get_statistics()
print(f"Registry health: {stats}")
```