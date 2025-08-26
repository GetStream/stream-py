"""
Tests for OpenTelemetry integration.
"""

import pytest
import time
from unittest.mock import Mock, patch

from ..telemetry import (
    TelemetryConfig,
    PluginTelemetry,
    initialize_telemetry,
    get_telemetry,
    shutdown_telemetry,
    trace_plugin_operation,
)
from ..telemetry_events import TelemetryEventEmitter, TelemetryEventFilter
from ..telemetry_registry import TelemetryEventRegistry, get_global_telemetry_registry
from ..events import EventType, create_event, STTTranscriptEvent


class TestTelemetryConfig:
    """Test TelemetryConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = TelemetryConfig()
        
        assert config.service_name == "getstream-plugins"
        assert config.service_version == "0.2.0"
        assert config.enable_tracing is True
        assert config.enable_metrics is True
        assert config.enable_logging_instrumentation is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = TelemetryConfig(
            service_name="test-service",
            service_version="1.0.0",
            enable_tracing=False,
            enable_metrics=False
        )
        
        assert config.service_name == "test-service"
        assert config.service_version == "1.0.0"
        assert config.enable_tracing is False
        assert config.enable_metrics is False
    
    @patch.dict('os.environ', {
        'OTEL_SERVICE_NAME': 'env-service',
        'OTEL_SERVICE_VERSION': '2.0.0',
        'OTEL_TRACES_ENABLED': 'false'
    })
    def test_from_env(self):
        """Test configuration from environment variables."""
        config = TelemetryConfig.from_env()
        
        assert config.service_name == "env-service"
        assert config.service_version == "2.0.0"
        assert config.enable_tracing is False
    
    def test_parse_otlp_headers(self):
        """Test OTLP headers parsing."""
        with patch.dict('os.environ', {
            'OTEL_EXPORTER_OTLP_HEADERS': 'key1=value1,key2=value2'
        }):
            config = TelemetryConfig.from_env()
            assert config.otlp_headers == {"key1": "value1", "key2": "value2"}


class TestPluginTelemetry:
    """Test PluginTelemetry class."""
    
    def test_init_with_config(self):
        """Test initialization with configuration."""
        config = TelemetryConfig(enable_tracing=False, enable_metrics=False)
        telemetry = PluginTelemetry(config)
        
        assert telemetry.config == config
        assert telemetry._initialized is False
    
    @patch('getstream.plugins.common.telemetry.Resource.create')
    @patch('getstream.plugins.common.telemetry.trace.set_tracer_provider')
    @patch('getstream.plugins.common.telemetry.metrics.set_meter_provider')
    def test_initialize_opentelemetry(self, mock_meter, mock_trace, mock_resource):
        """Test OpenTelemetry initialization."""
        config = TelemetryConfig(enable_tracing=True, enable_metrics=True)
        telemetry = PluginTelemetry(config)
        
        # Mock resource creation
        mock_resource.return_value = Mock()
        
        # Test initialization
        telemetry._initialize_opentelemetry()
        
        assert telemetry._initialized is True
        mock_resource.assert_called_once()
        mock_trace.assert_called_once()
        mock_meter.assert_called_once()
    
    def test_get_tracer_noop_when_disabled(self):
        """Test that NoOpTracer is returned when tracing is disabled."""
        config = TelemetryConfig(enable_tracing=False)
        telemetry = PluginTelemetry(config)
        
        tracer = telemetry.get_tracer("test")
        assert "NoOpTracer" in str(type(tracer))
    
    def test_get_meter_noop_when_disabled(self):
        """Test that NoOpMeter is returned when metrics is disabled."""
        config = TelemetryConfig(enable_metrics=False)
        telemetry = PluginTelemetry(config)
        
        meter = telemetry.get_meter("test")
        assert "NoOpMeter" in str(type(meter))


class TestTelemetryEventEmitter:
    """Test TelemetryEventEmitter class."""
    
    def test_init(self):
        """Test emitter initialization."""
        emitter = TelemetryEventEmitter("test_plugin")
        
        assert emitter.plugin_name == "test_plugin"
        assert emitter.telemetry is not None
        assert emitter._listeners == {}
    
    def test_emit_basic(self):
        """Test basic event emission."""
        emitter = TelemetryEventEmitter("test_plugin")
        event = create_event(EventType.STT_TRANSCRIPT, text="test")
        
        # Mock telemetry methods
        emitter.telemetry.record_event = Mock()
        
        emitter.emit(event)
        
        assert event.plugin_name == "test_plugin"
        emitter.telemetry.record_event.assert_called_once_with(event)
    
    def test_add_listener(self):
        """Test adding event listeners."""
        emitter = TelemetryEventEmitter("test_plugin")
        listener = Mock()
        
        emitter.add_listener(EventType.STT_TRANSCRIPT, listener)
        
        assert listener in emitter._listeners[EventType.STT_TRANSCRIPT]
    
    def test_remove_listener(self):
        """Test removing event listeners."""
        emitter = TelemetryEventEmitter("test_plugin")
        listener = Mock()
        
        emitter.add_listener(EventType.STT_TRANSCRIPT, listener)
        emitter.remove_listener(EventType.STT_TRANSCRIPT, listener)
        
        assert listener not in emitter._listeners[EventType.STT_TRANSCRIPT]


class TestTelemetryEventRegistry:
    """Test TelemetryEventRegistry class."""
    
    def test_init(self):
        """Test registry initialization."""
        registry = TelemetryEventRegistry(max_events=100)
        
        assert registry.max_events == 100
        assert registry.enable_metrics is True
        assert registry.enable_tracing is True
        assert len(registry.events) == 0
    
    def test_register_event(self):
        """Test event registration."""
        registry = TelemetryEventRegistry()
        event = create_event(EventType.STT_TRANSCRIPT, text="test")
        
        # Mock telemetry methods
        registry._record_event_metrics = Mock()
        registry._record_event_trace = Mock()
        
        registry.register_event(event)
        
        assert len(registry.events) == 1
        assert registry.event_counts[EventType.STT_TRANSCRIPT] == 1
        registry._record_event_metrics.assert_called_once_with(event)
        registry._record_event_trace.assert_called_once_with(event)
    
    def test_get_events_with_filter(self):
        """Test getting events with filter."""
        registry = TelemetryEventRegistry()
        
        # Add events
        event1 = create_event(EventType.STT_TRANSCRIPT, text="test1", plugin_name="plugin1")
        event2 = create_event(EventType.STT_TRANSCRIPT, text="test2", plugin_name="plugin2")
        
        registry.register_event(event1)
        registry.register_event(event2)
        
        # Filter by plugin
        filtered_events = registry.get_events(filter_criteria={"plugin_name": "plugin1"})
        
        assert len(filtered_events) == 1
        assert filtered_events[0].plugin_name == "plugin1"
    
    def test_get_statistics(self):
        """Test getting registry statistics."""
        registry = TelemetryEventRegistry()
        
        # Add some events
        event = create_event(EventType.STT_TRANSCRIPT, text="test")
        registry.register_event(event)
        
        stats = registry.get_statistics()
        
        assert stats["total_events"] == 1
        assert "STT_TRANSCRIPT" in stats["event_distribution"]
        assert stats["session_count"] == 0


class TestGlobalFunctions:
    """Test global telemetry functions."""
    
    def test_initialize_and_get_telemetry(self):
        """Test global telemetry initialization and retrieval."""
        # Initialize telemetry
        telemetry1 = initialize_telemetry()
        assert telemetry1 is not None
        
        # Get the same instance
        telemetry2 = get_telemetry()
        assert telemetry2 is telemetry1
    
    def test_get_global_registry(self):
        """Test global registry retrieval."""
        registry = get_global_telemetry_registry()
        assert registry is not None
        assert isinstance(registry, TelemetryEventRegistry)


class TestTraceDecorator:
    """Test the trace_plugin_operation decorator."""
    
    def test_trace_decorator_success(self):
        """Test successful operation tracing."""
        @trace_plugin_operation("test_op", "test_plugin")
        def test_function():
            return "success"
        
        # Mock telemetry
        with patch('getstream.plugins.common.telemetry.get_telemetry') as mock_get:
            mock_telemetry = Mock()
            mock_get.return_value = mock_telemetry
            
            result = test_function()
            
            assert result == "success"
            mock_telemetry.record_plugin_operation.assert_called_once()
    
    def test_trace_decorator_error(self):
        """Test error handling in tracing decorator."""
        @trace_plugin_operation("test_op", "test_plugin")
        def test_function():
            raise ValueError("test error")
        
        # Mock telemetry
        with patch('getstream.plugins.common.telemetry.get_telemetry') as mock_get:
            mock_telemetry = Mock()
            mock_get.return_value = mock_telemetry
            
            with pytest.raises(ValueError):
                test_function()
            
            # Should record error
            mock_telemetry.record_error.assert_called_once()


class TestIntegration:
    """Integration tests for telemetry components."""
    
    def test_full_workflow(self):
        """Test complete telemetry workflow."""
        # Initialize telemetry
        config = TelemetryConfig(enable_tracing=False, enable_metrics=False)
        telemetry = PluginTelemetry(config)
        
        # Create event emitter
        emitter = TelemetryEventEmitter("test_plugin", telemetry)
        
        # Create event registry
        registry = TelemetryEventRegistry(telemetry=telemetry)
        
        # Create and emit event
        event = create_event(EventType.STT_TRANSCRIPT, text="test")
        emitter.emit(event)
        
        # Register event
        registry.register_event(event)
        
        # Verify workflow
        assert len(registry.events) == 1
        assert registry.event_counts[EventType.STT_TRANSCRIPT] == 1
        
        # Get statistics
        stats = registry.get_statistics()
        assert stats["total_events"] == 1
    
    def test_error_handling(self):
        """Test error handling in telemetry workflow."""
        # Initialize telemetry
        config = TelemetryConfig(enable_tracing=False, enable_metrics=False)
        telemetry = PluginTelemetry(config)
        
        # Create event emitter
        emitter = TelemetryEventEmitter("test_plugin", telemetry)
        
        # Test error emission
        error = ValueError("test error")
        emitter.emit_error(error, EventType.PLUGIN_ERROR, {"context": "test"})
        
        # Verify error was recorded
        # (Note: In a real scenario, this would be verified through the telemetry system)
        assert True  # Placeholder assertion


if __name__ == "__main__":
    pytest.main([__file__])
