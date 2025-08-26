"""
Telemetry-enhanced event emitter for GetStream AI plugins.

This module provides an event emitter that automatically integrates with OpenTelemetry
for tracing, metrics, and logging of all plugin events.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Callable, Union
from contextlib import contextmanager

from .events import BaseEvent, EventType
from .telemetry import get_telemetry, PluginTelemetry
from opentelemetry import context


class TelemetryEventEmitter:
    """
    Event emitter with automatic OpenTelemetry integration.
    
    This class extends the basic event emission functionality with automatic
    tracing, metrics, and logging through OpenTelemetry.
    """
    
    def __init__(self, plugin_name: str, telemetry: Optional[PluginTelemetry] = None):
        """
        Initialize the telemetry event emitter.
        
        Args:
            plugin_name: Name of the plugin using this emitter
            telemetry: Optional telemetry instance, will use global if not provided
        """
        self.plugin_name = plugin_name
        self.telemetry = telemetry or get_telemetry()
        self.logger = logging.getLogger(f"getstream.plugins.{plugin_name}")
        
        # Event listeners
        self._listeners: Dict[EventType, List[Callable[[BaseEvent], None]]] = {}
        
        # Performance tracking
        self._operation_start_times: Dict[str, float] = {}
    
    def emit(self, event: BaseEvent, trace_context: Optional[Dict[str, Any]] = None):
        """
        Emit an event with automatic telemetry integration.
        
        Args:
            event: The event to emit
            trace_context: Optional context for tracing
        """
        # Ensure event has plugin information
        if not event.plugin_name:
            event.plugin_name = self.plugin_name
        
        # Record event in OpenTelemetry
        self.telemetry.record_event(event)
        
        # Log event
        self._log_event(event)
        
        # Notify listeners
        self._notify_listeners(event)
        
        # Add trace context if provided
        if trace_context:
            self._add_trace_context(event, trace_context)
    
    def emit_with_trace(
        self,
        event: BaseEvent,
        operation_name: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Emit an event within a trace span.
        
        Args:
            event: The event to emit
            operation_name: Name of the operation being traced
            attributes: Additional attributes for the trace span
        """
        span_attributes = {
            "plugin.name": self.plugin_name,
            "operation.name": operation_name,
        }
        if attributes:
            span_attributes.update(attributes)
        
        with self.telemetry.trace_span(
            f"{self.plugin_name}.{operation_name}",
            attributes=span_attributes
        ) as span:
            # Add event to span
            self.telemetry.record_event(event, span)
            
            # Emit event normally
            self.emit(event)
            
            # Add span attributes from event
            if hasattr(event, 'text') and event.text:
                span.set_attribute("event.text_length", len(event.text))
            
            if hasattr(event, 'confidence') and event.confidence is not None:
                span.set_attribute("event.confidence", event.confidence)
            
            if hasattr(event, 'processing_time_ms') and event.processing_time_ms is not None:
                span.set_attribute("event.processing_time_ms", event.processing_time_ms)
    
    def start_operation(self, operation_name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Start timing an operation.
        
        Args:
            operation_name: Name of the operation
            attributes: Additional attributes for the operation
        """
        operation_id = f"{self.plugin_name}.{operation_name}"
        self._operation_start_times[operation_id] = time.time()
        
        # Start trace span if tracing is enabled
        if self.telemetry.config.enable_tracing:
            span_attrs = {
                "plugin.name": self.plugin_name,
                "operation.name": operation_name,
            }
            if attributes:
                span_attrs.update(attributes)
            
            # Store span in context for later use
            context.attach(context.set_value("operation_span_attrs", span_attrs))
    
    def end_operation(
        self,
        operation_name: str,
        success: bool = True,
        attributes: Optional[Dict[str, Any]] = None,
        event: Optional[BaseEvent] = None
    ):
        """
        End timing an operation and record metrics.
        
        Args:
            operation_name: Name of the operation
            success: Whether the operation was successful
            attributes: Additional attributes for the operation
            event: Optional event to emit with the operation completion
        """
        operation_id = f"{self.plugin_name}.{operation_name}"
        start_time = self._operation_start_times.pop(operation_id, None)
        
        if start_time is None:
            self.logger.warning(f"Operation {operation_id} was not started")
            return
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Record operation metrics
        self.telemetry.record_plugin_operation(
            operation_name,
            self.plugin_name,
            duration_ms,
            success,
            attributes
        )
        
        # Emit event if provided
        if event:
            self.emit(event)
        
        # Log operation completion
        self.logger.debug(
            f"Operation {operation_name} completed in {duration_ms:.2f}ms (success: {success})"
        )
    
    @contextmanager
    def operation_context(
        self,
        operation_name: str,
        attributes: Optional[Dict[str, Any]] = None,
        emit_event: Optional[BaseEvent] = None
    ):
        """
        Context manager for automatic operation timing and tracing.
        
        Args:
            operation_name: Name of the operation
            attributes: Additional attributes for the operation
            emit_event: Optional event to emit when operation completes
        """
        try:
            self.start_operation(operation_name, attributes)
            yield
            self.end_operation(operation_name, success=True, attributes=attributes, event=emit_event)
        except Exception as e:
            self.end_operation(operation_name, success=False, attributes=attributes)
            self.telemetry.record_error(e, {
                "operation.name": operation_name,
                "plugin.name": self.plugin_name,
            })
            raise
    
    def add_listener(self, event_type: EventType, listener: Callable[[BaseEvent], None]):
        """Add a listener for a specific event type."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)
    
    def remove_listener(self, event_type: EventType, listener: Callable[[BaseEvent], None]):
        """Remove a listener for a specific event type."""
        if event_type in self._listeners and listener in self._listeners[event_type]:
            self._listeners[event_type].remove(listener)
    
    def _notify_listeners(self, event: BaseEvent):
        """Notify all listeners for the event type."""
        listeners = self._listeners.get(event.event_type, [])
        for listener in listeners:
            try:
                listener(event)
            except Exception as e:
                self.logger.error(f"Error in event listener: {e}")
                self.telemetry.record_error(e, {
                    "event.type": event.event_type.value,
                    "plugin.name": self.plugin_name,
                })
    
    def _log_event(self, event: BaseEvent):
        """Log an event with structured information."""
        log_data = {
            "event_type": event.event_type.value,
            "event_id": event.event_id,
            "session_id": event.session_id,
            "plugin_name": event.plugin_name,
            "timestamp": event.timestamp.isoformat(),
        }
        
        # Add event-specific information
        if hasattr(event, 'text') and event.text:
            log_data["text_length"] = len(event.text)
            log_data["text_preview"] = event.text[:100]
        
        if hasattr(event, 'confidence') and event.confidence is not None:
            log_data["confidence"] = event.confidence
        
        if hasattr(event, 'processing_time_ms') and event.processing_time_ms is not None:
            log_data["processing_time_ms"] = event.processing_time_ms
        
        if hasattr(event, 'error') and event.error:
            log_data["error_message"] = str(event.error)
            log_data["error_type"] = type(event.error).__name__
        
        # Log with appropriate level
        if "ERROR" in event.event_type.value.upper():
            self.logger.error(f"Event: {event.event_type.value}", extra=log_data)
        else:
            self.logger.info(f"Event: {event.event_type.value}", extra=log_data)
    
    def _add_trace_context(self, event: BaseEvent, trace_context: Dict[str, Any]):
        """Add trace context to an event."""
        # This could be extended to add trace IDs, span IDs, etc.
        if hasattr(event, 'user_metadata'):
            if event.user_metadata is None:
                event.user_metadata = {}
            event.user_metadata.update(trace_context)
    
    def emit_error(
        self,
        error: Exception,
        event_type: EventType,
        context_info: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ):
        """
        Emit an error event with automatic error recording.
        
        Args:
            error: The exception that occurred
            event_type: Type of error event to emit
            context_info: Additional context information
            session_id: Optional session ID for the error
        """
        from .events import create_event
        
        # Create error event
        error_event = create_event(
            event_type,
            error=error,
            plugin_name=self.plugin_name,
            session_id=session_id,
            user_metadata=context_info
        )
        
        # Record error in OpenTelemetry
        error_context = {
            "event.type": event_type.value,
            "plugin.name": self.plugin_name,
            "session.id": session_id,
        }
        if context_info:
            error_context.update(context_info)
        
        self.telemetry.record_error(error, error_context)
        
        # Emit the error event
        self.emit(error_event)
    
    def emit_performance_event(
        self,
        event_type: EventType,
        duration_ms: float,
        success: bool = True,
        additional_attrs: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ):
        """
        Emit a performance-related event.
        
        Args:
            event_type: Type of event to emit
            duration_ms: Duration of the operation in milliseconds
            success: Whether the operation was successful
            additional_attrs: Additional attributes for the event
            session_id: Optional session ID
        """
        from .events import create_event
        
        # Create performance event
        user_metadata = {
            "duration_ms": duration_ms,
            "success": success,
        }
        if additional_attrs:
            user_metadata.update(additional_attrs)
        
        event = create_event(
            event_type,
            plugin_name=self.plugin_name,
            session_id=session_id,
            user_metadata=user_metadata
        )
        
        # Record performance metrics
        if hasattr(event, 'processing_time_ms'):
            event.processing_time_ms = duration_ms
        
        # Emit the event
        self.emit(event)
    
    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Get a summary of telemetry data for this emitter."""
        return {
            "plugin_name": self.plugin_name,
            "active_operations": len(self._operation_start_times),
            "listener_counts": {
                event_type.value: len(listeners)
                for event_type, listeners in self._listeners.items()
            }
        }


class TelemetryEventFilter:
    """
    Event filter with telemetry integration.
    
    This class provides filtering capabilities while maintaining
    telemetry context for filtered events.
    """
    
    def __init__(self, telemetry: Optional[PluginTelemetry] = None):
        """Initialize the telemetry event filter."""
        self.telemetry = telemetry or get_telemetry()
    
    def filter_events(
        self,
        events: List[BaseEvent],
        filter_criteria: Dict[str, Any]
    ) -> List[BaseEvent]:
        """
        Filter events based on criteria while maintaining telemetry.
        
        Args:
            events: List of events to filter
            filter_criteria: Criteria for filtering
            
        Returns:
            Filtered list of events
        """
        filtered_events = []
        
        for event in events:
            if self._matches_criteria(event, filter_criteria):
                filtered_events.append(event)
            else:
                # Record filtered event for telemetry
                self.telemetry.record_event(event)
        
        # Record filtering metrics
        if self.telemetry.config.enable_plugin_metrics:
            meter = self.telemetry.get_meter("getstream.plugins.filtering")
            filter_counter = meter.create_counter(
                name="plugin.events.filtered",
                description="Number of events filtered",
                unit="1"
            )
            
            filter_counter.add(
                len(events) - len(filtered_events),
                attributes={"filter.criteria": str(filter_criteria)}
            )
        
        return filtered_events
    
    def _matches_criteria(self, event: BaseEvent, criteria: Dict[str, Any]) -> bool:
        """Check if an event matches the filter criteria."""
        for key, value in criteria.items():
            if not hasattr(event, key):
                return False
            
            event_value = getattr(event, key)
            if event_value != value:
                return False
        
        return True


__all__ = [
    "TelemetryEventEmitter",
    "TelemetryEventFilter",
]
