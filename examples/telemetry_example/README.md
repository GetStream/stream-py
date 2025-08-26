# OpenTelemetry Integration Example

This example demonstrates how to use the OpenTelemetry integration for GetStream AI plugins to achieve comprehensive observability.

## Features

- **Tracing**: Automatic span creation for plugin operations
- **Metrics**: Performance and usage metrics collection
- **Logging**: Structured logging with OpenTelemetry context
- **Event Tracking**: Comprehensive event monitoring and analysis
- **Error Handling**: Automatic error recording and metrics

## Prerequisites

- Python 3.10+
- GetStream Python SDK
- GetStream Plugins Common package

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or using uv
uv sync
```

## Usage

### Basic Usage

```python
from getstream.plugins.common import (
    initialize_telemetry,
    get_telemetry,
    TelemetryEventEmitter
)

# Initialize telemetry
telemetry = initialize_telemetry()

# Create event emitter
emitter = TelemetryEventEmitter("my_plugin")

# Emit events with automatic telemetry
emitter.emit(event)
```

### Environment Configuration

Set environment variables to configure OpenTelemetry:

```bash
export OTEL_SERVICE_NAME="my-service"
export OTEL_SERVICE_VERSION="1.0.0"
export OTEL_TRACES_ENABLED="true"
export OTEL_METRICS_ENABLED="true"
export OTEL_LOGS_ENABLED="true"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
```

### Running the Example

```bash
python main.py
```

## Configuration Options

### TelemetryConfig

- `service_name`: Name of the service
- `service_version`: Version of the service
- `enable_tracing`: Enable distributed tracing
- `enable_metrics`: Enable metrics collection
- `enable_logging_instrumentation`: Enable logging instrumentation
- `otlp_endpoint`: OTLP exporter endpoint
- `otlp_protocol`: OTLP protocol (http or grpc)

### Event Emitter

- `emit()`: Emit event with automatic telemetry
- `emit_with_trace()`: Emit event within a trace span
- `operation_context()`: Context manager for operation timing
- `emit_error()`: Emit error events with automatic error recording

### Event Registry

- `register_event()`: Register event with telemetry
- `get_statistics()`: Get comprehensive event statistics
- `get_error_summary()`: Get error summary
- `get_performance_summary()`: Get performance metrics

## Metrics

The integration automatically collects:

- Event counts by type and plugin
- Processing time histograms
- Confidence score distributions
- Error rates and types
- Operation duration metrics
- Registry performance metrics

## Tracing

Automatic tracing includes:

- Plugin operation spans
- Event registration spans
- Error tracking with context
- Performance monitoring
- Cross-service correlation

## Logging

Structured logging with:

- Event context information
- Performance metrics
- Error details
- Trace correlation IDs
- Plugin-specific metadata

## Examples

See `main.py` for comprehensive examples of:

- STT plugin telemetry integration
- TTS plugin telemetry integration
- Batch processing with telemetry
- Error handling and reporting
- Performance monitoring
- Environment-based configuration

## Integration with Existing Plugins

**✅ COMPLETED**: All existing GetStream AI plugins now automatically integrate with OpenTelemetry!

The following plugins have been updated to automatically emit telemetry events:

- **STT Plugins**: Deepgram, AssemblyAI, Moonshine, FAL
- **TTS Plugins**: ElevenLabs, Cartesia, Kokoro  
- **VAD Plugins**: Silero
- **STS Plugins**: OpenAI Realtime, Gemini Live

### How It Works

1. **Automatic Integration**: Plugins automatically create `TelemetryEventEmitter` instances
2. **Event Emission**: All events (transcripts, audio, errors) automatically go through OpenTelemetry
3. **Performance Tracking**: Processing times, confidence scores, and error rates are automatically monitored
4. **No Code Changes Required**: Existing plugin code automatically benefits from telemetry

### What Gets Monitored

- **Plugin Initialization**: When plugins start up
- **Event Processing**: All STT, TTS, VAD, and STS events
- **Performance Metrics**: Processing times, audio durations, confidence scores
- **Error Tracking**: All errors with context and stack traces
- **Resource Usage**: Memory usage, operation counts, session tracking

## Best Practices

- Use operation context managers for automatic timing
- Emit events for all significant operations
- Include relevant metadata in events
- Handle errors gracefully with telemetry recording
- Configure appropriate sampling rates for production
- Use structured logging for better observability
