"""
OpenTelemetry integration for GetStream AI plugins.

This module provides comprehensive observability for all plugin operations
including tracing, metrics, and logging with OpenTelemetry.
"""

import os
import time
import logging
from contextlib import contextmanager
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass

# OpenTelemetry imports
from opentelemetry import trace, metrics, context
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    BatchSpanProcessor,
    SimpleSpanProcessor
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GRPCOTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter as GRPCOTLPMetricExporter

from .events import BaseEvent, EventType


@dataclass
class TelemetryConfig:
    """Configuration for OpenTelemetry integration."""
    
    # Service information
    service_name: str = "getstream-plugins"
    service_version: str = "0.2.0"
    service_namespace: str = "getstream"
    
    # Tracing configuration
    enable_tracing: bool = True
    trace_sampler: str = "always_on"  # "always_on", "always_off", "traceidratio"
    trace_sampling_ratio: float = 1.0
    
    # Metrics configuration
    enable_metrics: bool = True
    metrics_export_interval_ms: int = 5000
    
    # Logging configuration
    enable_logging_instrumentation: bool = True
    log_level: str = "INFO"
    
    # Exporters configuration
    otlp_endpoint: Optional[str] = None
    otlp_protocol: str = "http"  # "http" or "grpc"
    otlp_headers: Optional[Dict[str, str]] = None
    enable_console_export: bool = True
    
    # Plugin-specific configuration
    enable_plugin_metrics: bool = True
    enable_event_tracing: bool = True
    enable_performance_metrics: bool = True
    
    @classmethod
    def from_env(cls) -> "TelemetryConfig":
        """Create configuration from environment variables."""
        return cls(
            service_name=os.getenv("OTEL_SERVICE_NAME", "getstream-plugins"),
            service_version=os.getenv("OTEL_SERVICE_VERSION", "0.2.0"),
            service_namespace=os.getenv("OTEL_SERVICE_NAMESPACE", "getstream"),
            enable_tracing=os.getenv("OTEL_TRACES_ENABLED", "true").lower() == "true",
            trace_sampler=os.getenv("OTEL_TRACES_SAMPLER", "always_on"),
            trace_sampling_ratio=float(os.getenv("OTEL_TRACES_SAMPLER_ARG", "1.0")),
            enable_metrics=os.getenv("OTEL_METRICS_ENABLED", "true").lower() == "true",
            metrics_export_interval_ms=int(os.getenv("OTEL_METRICS_EXPORT_INTERVAL_MS", "5000")),
            enable_logging_instrumentation=os.getenv("OTEL_LOGS_ENABLED", "true").lower() == "true",
            log_level=os.getenv("OTEL_LOG_LEVEL", "INFO"),
            otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
            otlp_protocol=os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "http"),
            otlp_headers=cls._parse_otlp_headers(),
            enable_console_export=os.getenv("OTEL_CONSOLE_EXPORT", "true").lower() == "true",
            enable_plugin_metrics=os.getenv("OTEL_PLUGIN_METRICS", "true").lower() == "true",
            enable_event_tracing=os.getenv("OTEL_EVENT_TRACING", "true").lower() == "true",
            enable_performance_metrics=os.getenv("OTEL_PERFORMANCE_METRICS", "true").lower() == "true",
        )
    
    @staticmethod
    def _parse_otlp_headers() -> Optional[Dict[str, str]]:
        """Parse OTLP headers from environment variable."""
        headers_str = os.getenv("OTEL_EXPORTER_OTLP_HEADERS")
        if not headers_str:
            return None
        
        headers = {}
        for header in headers_str.split(","):
            if "=" in header:
                key, value = header.split("=", 1)
                headers[key.strip()] = value.strip()
        return headers


class PluginTelemetry:
    """OpenTelemetry integration for GetStream plugins."""
    
    def __init__(self, config: Optional[TelemetryConfig] = None):
        """Initialize OpenTelemetry integration."""
        self.config = config or TelemetryConfig.from_env()
        self._initialized = False
        self._tracer_provider: Optional[TracerProvider] = None
        self._meter_provider: Optional[MeterProvider] = None
        
        # Initialize OpenTelemetry if enabled
        if self.config.enable_tracing or self.config.enable_metrics:
            self._initialize_opentelemetry()
    
    def _initialize_opentelemetry(self):
        """Initialize OpenTelemetry SDK."""
        try:
            # Create resource with service information
            resource = Resource.create({
                "service.name": self.config.service_name,
                "service.version": self.config.service_version,
                "service.namespace": self.config.service_namespace,
            })
            
            # Initialize tracing if enabled
            if self.config.enable_tracing:
                self._initialize_tracing(resource)
            
            # Initialize metrics if enabled
            if self.config.enable_metrics:
                self._initialize_metrics(resource)
            
            # Initialize logging instrumentation if enabled
            if self.config.enable_logging_instrumentation:
                self._initialize_logging()
            
            self._initialized = True
            logging.info("OpenTelemetry initialized successfully")
            
        except Exception as e:
            logging.warning(f"Failed to initialize OpenTelemetry: {e}")
            self._initialized = False
    
    def _initialize_tracing(self, resource: Resource):
        """Initialize tracing with OpenTelemetry."""
        self._tracer_provider = TracerProvider(resource=resource)
        
        # Add span processors
        if self.config.enable_console_export:
            self._tracer_provider.add_span_processor(
                SimpleSpanProcessor(ConsoleSpanExporter())
            )
        
        if self.config.otlp_endpoint:
            if self.config.otlp_protocol == "grpc":
                otlp_exporter = GRPCOTLPSpanExporter(
                    endpoint=self.config.otlp_endpoint,
                    headers=self.config.otlp_headers
                )
            else:
                otlp_exporter = OTLPSpanExporter(
                    endpoint=self.config.otlp_endpoint,
                    headers=self.config.otlp_headers
                )
            
            self._tracer_provider.add_span_processor(
                BatchSpanProcessor(otlp_exporter)
            )
        
        # Set as global tracer provider
        trace.set_tracer_provider(self._tracer_provider)
    
    def _initialize_metrics(self, resource: Resource):
        """Initialize metrics with OpenTelemetry."""
        self._meter_provider = MeterProvider(resource=resource)
        
        # Add metric readers
        if self.config.enable_console_export:
            self._meter_provider.add_metric_reader(
                PeriodicExportingMetricReader(
                    ConsoleMetricExporter(),
                    export_interval_millis=self.config.metrics_export_interval_ms
                )
            )
        
        if self.config.otlp_endpoint:
            if self.config.otlp_protocol == "grpc":
                otlp_exporter = GRPCOTLPMetricExporter(
                    endpoint=self.config.otlp_endpoint,
                    headers=self.config.otlp_headers
                )
            else:
                otlp_exporter = OTLPMetricExporter(
                    endpoint=self.config.otlp_endpoint,
                    headers=self.config.otlp_headers
                )
            
            self._meter_provider.add_metric_reader(
                PeriodicExportingMetricReader(
                    otlp_exporter,
                    export_interval_millis=self.config.metrics_export_interval_ms
                )
            )
        
        # Set as global meter provider
        metrics.set_meter_provider(self._meter_provider)
    
    def _initialize_logging(self):
        """Initialize logging instrumentation."""
        try:
            LoggingInstrumentor().instrument(
                set_logging_format=True,
                log_level=getattr(logging, self.config.log_level.upper(), logging.INFO)
            )
        except Exception as e:
            logging.warning(f"Failed to initialize logging instrumentation: {e}")
    
    def get_tracer(self, name: str) -> trace.Tracer:
        """Get a tracer instance."""
        if not self._initialized or not self.config.enable_tracing:
            return trace.NoOpTracer()
        return trace.get_tracer(name)
    
    def get_meter(self, name: str) -> metrics.Meter:
        """Get a meter instance."""
        if not self._initialized or not self.config.enable_metrics:
            return metrics.NoOpMeter()
        return metrics.get_meter(name)
    
    @contextmanager
    def trace_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Context manager for tracing spans."""
        if not self._initialized or not self.config.enable_tracing:
            yield
            return
        
        tracer = self.get_tracer("getstream.plugins")
        with tracer.start_as_current_span(name, attributes=attributes or {}) as span:
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
    
    def record_event(self, event: BaseEvent, span: Optional[trace.Span] = None):
        """Record an event in OpenTelemetry."""
        if not self._initialized:
            return
        
        # Add event as span event if tracing is enabled
        if self.config.enable_event_tracing and span:
            span.add_event(
                f"plugin.{event.event_type.value}",
                attributes={
                    "event.id": event.event_id,
                    "event.type": event.event_type.value,
                    "plugin.name": event.plugin_name or "unknown",
                    "session.id": event.session_id or "unknown",
                    "timestamp": event.timestamp.isoformat(),
                }
            )
        
        # Record metrics if enabled
        if self.config.enable_plugin_metrics:
            self._record_event_metrics(event)
    
    def _record_event_metrics(self, event: BaseEvent):
        """Record metrics for an event."""
        try:
            meter = self.get_meter("getstream.plugins.events")
            
            # Event counter
            event_counter = meter.create_counter(
                name="plugin.events.total",
                description="Total number of plugin events",
                unit="1"
            )
            
            event_counter.add(
                1,
                attributes={
                    "event.type": event.event_type.value,
                    "plugin.name": event.plugin_name or "unknown",
                    "session.id": event.session_id or "unknown",
                }
            )
            
            # Performance metrics for applicable events
            if self.config.enable_performance_metrics:
                self._record_performance_metrics(event, meter)
                
        except Exception as e:
            logging.debug(f"Failed to record event metrics: {e}")
    
    def _record_performance_metrics(self, event: BaseEvent, meter: metrics.Meter):
        """Record performance-related metrics for an event."""
        try:
            # Processing time metrics
            if hasattr(event, 'processing_time_ms') and event.processing_time_ms is not None:
                processing_time_histogram = meter.create_histogram(
                    name="plugin.processing.time",
                    description="Event processing time",
                    unit="ms"
                )
                
                processing_time_histogram.record(
                    event.processing_time_ms,
                    attributes={
                        "event.type": event.event_type.value,
                        "plugin.name": event.plugin_name or "unknown",
                    }
                )
            
            # Confidence metrics for applicable events
            if hasattr(event, 'confidence') and event.confidence is not None:
                confidence_histogram = meter.create_histogram(
                    name="plugin.confidence",
                    description="Event confidence scores",
                    unit="1"
                )
                
                confidence_histogram.record(
                    event.confidence,
                    attributes={
                        "event.type": event.event_type.value,
                        "plugin.name": event.plugin_name or "unknown",
                    }
                )
            
            # Audio duration metrics for applicable events
            if hasattr(event, 'audio_duration_ms') and event.audio_duration_ms is not None:
                audio_duration_histogram = meter.create_histogram(
                    name="plugin.audio.duration",
                    description="Audio duration for events",
                    unit="ms"
                )
                
                audio_duration_histogram.record(
                    event.audio_duration_ms,
                    attributes={
                        "event.type": event.event_type.value,
                        "plugin.name": event.plugin_name or "unknown",
                    }
                )
                
        except Exception as e:
            logging.debug(f"Failed to record performance metrics: {e}")
    
    def record_error(self, error: Exception, context_info: Optional[Dict[str, Any]] = None):
        """Record an error in OpenTelemetry."""
        if not self._initialized:
            return
        
        try:
            # Record error in current span if available
            current_span = trace.get_current_span()
            if current_span and current_span.is_recording():
                current_span.record_exception(error)
                current_span.set_status(trace.Status(trace.StatusCode.ERROR, str(error)))
                
                if context_info:
                    for key, value in context_info.items():
                        current_span.set_attribute(key, str(value))
            
            # Record error metrics
            if self.config.enable_plugin_metrics:
                meter = self.get_meter("getstream.plugins.errors")
                error_counter = meter.create_counter(
                    name="plugin.errors.total",
                    description="Total number of plugin errors",
                    unit="1"
                )
                
                # Prepare attributes with error info
                error_attributes = {
                    "error.type": type(error).__name__,
                    "error.message": str(error),
                }
                if context_info:
                    error_attributes.update(context_info)
                
                error_counter.add(1, attributes=error_attributes)
                
        except Exception as e:
            logging.debug(f"Failed to record error: {e}")
    
    def record_plugin_operation(
        self,
        operation_name: str,
        plugin_name: str,
        duration_ms: float,
        success: bool = True,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Record metrics for plugin operations."""
        if not self._initialized or not self.config.enable_plugin_metrics:
            return
        
        try:
            meter = self.get_meter("getstream.plugins.operations")
            
            # Operation duration histogram
            duration_histogram = meter.create_histogram(
                name="plugin.operation.duration",
                description="Plugin operation duration",
                unit="ms"
            )
            
            # Prepare histogram attributes
            histogram_attributes = {
                "operation.name": operation_name,
                "plugin.name": plugin_name,
                "success": success,
            }
            if attributes:
                histogram_attributes.update(attributes)
            
            duration_histogram.record(duration_ms, attributes=histogram_attributes)
            
            # Operation counter
            operation_counter = meter.create_counter(
                name="plugin.operations.total",
                description="Total number of plugin operations",
                unit="1"
            )
            
            # Prepare counter attributes
            counter_attributes = {
                "operation.name": operation_name,
                "plugin.name": plugin_name,
                "success": success,
            }
            if attributes:
                counter_attributes.update(attributes)
            
            operation_counter.add(1, attributes=counter_attributes)
            
        except Exception as e:
            logging.debug(f"Failed to record operation metrics: {e}")
    
    def shutdown(self):
        """Shutdown OpenTelemetry gracefully."""
        if not self._initialized:
            return
        
        try:
            if self._tracer_provider:
                self._tracer_provider.shutdown()
            
            if self._meter_provider:
                self._meter_provider.shutdown()
                
            self._initialized = False
            logging.info("OpenTelemetry shutdown successfully")
            
        except Exception as e:
            logging.warning(f"Error during OpenTelemetry shutdown: {e}")


# Global telemetry instance
_global_telemetry: Optional[PluginTelemetry] = None


def initialize_telemetry(config: Optional[TelemetryConfig] = None) -> PluginTelemetry:
    """Initialize global telemetry instance."""
    global _global_telemetry
    if _global_telemetry is None:
        _global_telemetry = PluginTelemetry(config)
    return _global_telemetry


def get_telemetry() -> PluginTelemetry:
    """Get the global telemetry instance."""
    global _global_telemetry
    if _global_telemetry is None:
        _global_telemetry = PluginTelemetry()
    return _global_telemetry


def shutdown_telemetry():
    """Shutdown global telemetry."""
    global _global_telemetry
    if _global_telemetry:
        _global_telemetry.shutdown()
        _global_telemetry = None


# Convenience functions for common operations
def trace_plugin_operation(operation_name: str, plugin_name: str):
    """Decorator for tracing plugin operations."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            telemetry = get_telemetry()
            start_time = time.time()
            
            try:
                with telemetry.trace_span(
                    f"{plugin_name}.{operation_name}",
                    attributes={
                        "plugin.name": plugin_name,
                        "operation.name": operation_name,
                    }
                ) as span:
                    result = func(*args, **kwargs)
                    
                    # Record success metrics
                    duration_ms = (time.time() - start_time) * 1000
                    telemetry.record_plugin_operation(
                        operation_name, plugin_name, duration_ms, success=True
                    )
                    
                    return result
                    
            except Exception as e:
                # Record error metrics
                duration_ms = (time.time() - start_time) * 1000
                telemetry.record_plugin_operation(
                    operation_name, plugin_name, duration_ms, success=False
                )
                
                telemetry.record_error(e, {
                    "operation.name": operation_name,
                    "plugin.name": plugin_name,
                })
                
                raise
        
        return wrapper
    return decorator


__all__ = [
    "TelemetryConfig",
    "PluginTelemetry",
    "initialize_telemetry",
    "get_telemetry",
    "shutdown_telemetry",
    "trace_plugin_operation",
]
