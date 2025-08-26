"""
Telemetry-enhanced event registry for GetStream AI plugins.

This module provides an event registry that automatically integrates with OpenTelemetry
for comprehensive observability of all plugin events and operations.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Callable, Set
from collections import defaultdict, deque
from dataclasses import dataclass

from .events import BaseEvent, EventType
from .telemetry import get_telemetry, PluginTelemetry


@dataclass
class RegistryMetrics:
    """Metrics for the event registry."""
    total_events: int = 0
    events_by_type: Dict[str, int] = None
    events_by_plugin: Dict[str, int] = None
    events_by_session: Dict[str, int] = None
    error_count: int = 0
    active_listeners: int = 0
    
    def __post_init__(self):
        if self.events_by_type is None:
            self.events_by_type = defaultdict(int)
        if self.events_by_plugin is None:
            self.events_by_plugin = defaultdict(int)
        if self.events_by_session is None:
            self.events_by_session = defaultdict(int)


class TelemetryEventRegistry:
    """
    Enhanced event registry with OpenTelemetry integration.
    
    This class extends the basic event registry functionality with automatic
    tracing, metrics, and performance monitoring through OpenTelemetry.
    """
    
    def __init__(
        self,
        max_events: int = 10000,
        telemetry: Optional[PluginTelemetry] = None,
        enable_metrics: bool = True,
        enable_tracing: bool = True
    ):
        """
        Initialize the telemetry event registry.
        
        Args:
            max_events: Maximum number of events to keep in memory
            telemetry: Optional telemetry instance, will use global if not provided
            enable_metrics: Whether to enable metrics collection
            enable_tracing: Whether to enable tracing
        """
        self.max_events = max_events
        self.telemetry = telemetry or get_telemetry()
        self.enable_metrics = enable_metrics
        self.enable_tracing = enable_tracing
        
        # Event storage
        self.events: deque = deque(maxlen=max_events)
        self.event_counts: Dict[EventType, int] = defaultdict(int)
        self.session_events: Dict[str, List[BaseEvent]] = defaultdict(list)
        self.plugin_events: Dict[str, List[BaseEvent]] = defaultdict(list)
        
        # Error tracking
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.error_details: List[Dict[str, Any]] = []
        
        # Event listeners
        self.listeners: Dict[EventType, List[Callable]] = defaultdict(list)
        self.global_listeners: List[Callable] = []
        
        # Performance tracking
        self.operation_timings: Dict[str, List[float]] = defaultdict(list)
        self.registry_metrics = RegistryMetrics()
        
        # Initialize telemetry if enabled
        if self.enable_metrics or self.enable_tracing:
            self._initialize_telemetry()
    
    def _initialize_telemetry(self):
        """Initialize telemetry components for the registry."""
        try:
            # Create registry-specific meters
            if self.enable_metrics:
                self._registry_meter = self.telemetry.get_meter("getstream.plugins.registry")
                self._create_registry_metrics()
            
            # Create registry-specific tracer
            if self.enable_tracing:
                self._registry_tracer = self.telemetry.get_tracer("getstream.plugins.registry")
            
            logging.info("Telemetry initialized for event registry")
            
        except Exception as e:
            logging.warning(f"Failed to initialize telemetry for registry: {e}")
            self.enable_metrics = False
            self.enable_tracing = False
    
    def _create_registry_metrics(self):
        """Create metrics for the registry."""
        try:
            # Event counter
            self._event_counter = self._registry_meter.create_counter(
                name="registry.events.total",
                description="Total number of events registered",
                unit="1"
            )
            
            # Event type counter
            self._event_type_counter = self._registry_meter.create_counter(
                name="registry.events.by_type",
                description="Events by type",
                unit="1"
            )
            
            # Plugin counter
            self._plugin_counter = self._registry_meter.create_counter(
                name="registry.events.by_plugin",
                description="Events by plugin",
                unit="1"
            )
            
            # Session counter
            self._session_counter = self._registry_meter.create_counter(
                name="registry.events.by_session",
                description="Events by session",
                unit="1"
            )
            
            # Error counter
            self._error_counter = self._registry_meter.create_counter(
                name="registry.errors.total",
                description="Total number of registry errors",
                unit="1"
            )
            
            # Registry size gauge
            self._registry_size_gauge = self._registry_meter.create_up_down_counter(
                name="registry.size",
                description="Current size of the registry",
                unit="1"
            )
            
            # Listener count gauge
            self._listener_count_gauge = self._registry_meter.create_up_down_counter(
                name="registry.listeners",
                description="Number of active listeners",
                unit="1"
            )
            
        except Exception as e:
            logging.warning(f"Failed to create registry metrics: {e}")
    
    def register_event(self, event: BaseEvent):
        """Register a new event with telemetry integration."""
        start_time = time.time()
        
        try:
            # Add event to storage
            self.events.append(event)
            self.event_counts[event.event_type] += 1
            
            # Track by session
            if event.session_id:
                self.session_events[event.session_id].append(event)
            
            # Track by plugin
            if event.plugin_name:
                self.plugin_events[event.plugin_name].append(event)
            
            # Track errors separately
            if "ERROR" in event.event_type.value.upper():
                error_key = f"{event.plugin_name}_{event.event_type.value}"
                self.error_counts[error_key] += 1
                
                # Store error details
                error_detail = {
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type.value,
                    "plugin_name": event.plugin_name,
                    "session_id": event.session_id,
                    "error_message": getattr(event, 'error_message', str(getattr(event, 'error', 'Unknown error'))),
                }
                self.error_details.append(error_detail)
                
                # Keep only last 100 error details
                if len(self.error_details) > 100:
                    self.error_details = self.error_details[-100:]
            
            # Update metrics
            self._update_registry_metrics(event)
            
            # Record telemetry
            if self.enable_metrics:
                self._record_event_metrics(event)
            
            if self.enable_tracing:
                self._record_event_trace(event)
            
            # Notify listeners
            self._notify_listeners(event)
            
            # Record operation timing
            duration_ms = (time.time() - start_time) * 1000
            self.operation_timings["event_registration"].append(duration_ms)
            
            # Keep only last 1000 timings
            if len(self.operation_timings["event_registration"]) > 1000:
                self.operation_timings["event_registration"] = self.operation_timings["event_registration"][-1000:]
            
        except Exception as e:
            logging.error(f"Error registering event: {e}")
            if self.enable_metrics:
                self._record_error_metrics(e, "event_registration")
            raise
    
    def _update_registry_metrics(self, event: BaseEvent):
        """Update internal registry metrics."""
        self.registry_metrics.total_events += 1
        self.registry_metrics.events_by_type[event.event_type.value] += 1
        
        if event.plugin_name:
            self.registry_metrics.events_by_plugin[event.plugin_name] += 1
        
        if event.session_id:
            self.registry_metrics.events_by_session[event.session_id] += 1
        
        if "ERROR" in event.event_type.value.upper():
            self.registry_metrics.error_count += 1
    
    def _record_event_metrics(self, event: BaseEvent):
        """Record metrics for an event."""
        try:
            # Increment event counter
            self._event_counter.add(1)
            
            # Increment event type counter
            self._event_type_counter.add(
                1,
                attributes={"event.type": event.event_type.value}
            )
            
            # Increment plugin counter
            if event.plugin_name:
                self._plugin_counter.add(
                    1,
                    attributes={"plugin.name": event.plugin_name}
                )
            
            # Increment session counter
            if event.session_id:
                self._session_counter.add(
                    1,
                    attributes={"session.id": event.session_id}
                )
            
            # Update registry size
            self._registry_size_gauge.add(
                1,
                attributes={"metric.type": "total_events"}
            )
            
        except Exception as e:
            logging.debug(f"Failed to record event metrics: {e}")
    
    def _record_event_trace(self, event: BaseEvent):
        """Record trace information for an event."""
        try:
            with self._registry_tracer.start_as_current_span(
                "registry.event_registered",
                attributes={
                    "event.type": event.event_type.value,
                    "event.id": event.event_id,
                    "plugin.name": event.plugin_name or "unknown",
                    "session.id": event.session_id or "unknown",
                    "timestamp": event.timestamp.isoformat(),
                }
            ) as span:
                # Add event-specific attributes
                if hasattr(event, 'text') and event.text:
                    span.set_attribute("event.text_length", len(event.text))
                
                if hasattr(event, 'confidence') and event.confidence is not None:
                    span.set_attribute("event.confidence", event.confidence)
                
                if hasattr(event, 'processing_time_ms') and event.processing_time_ms is not None:
                    span.set_attribute("event.processing_time_ms", event.processing_time_ms)
                
                # Add event as span event
                span.add_event(
                    "event.registered",
                    attributes={
                        "event.type": event.event_type.value,
                        "plugin.name": event.plugin_name or "unknown",
                    }
                )
                
        except Exception as e:
            logging.debug(f"Failed to record event trace: {e}")
    
    def _record_error_metrics(self, error: Exception, context: str):
        """Record error metrics."""
        try:
            self._error_counter.add(
                1,
                attributes={
                    "error.type": type(error).__name__,
                    "error.message": str(error),
                    "context": context,
                }
            )
        except Exception as e:
            logging.debug(f"Failed to record error metrics: {e}")
    
    def add_listener(self, event_type: EventType, listener: Callable[[BaseEvent], None]):
        """Add a listener for a specific event type."""
        self.listeners[event_type].append(listener)
        self._update_listener_metrics()
    
    def add_global_listener(self, listener: Callable[[BaseEvent], None]):
        """Add a global listener for all events."""
        self.global_listeners.append(listener)
        self._update_listener_metrics()
    
    def remove_listener(self, event_type: EventType, listener: Callable):
        """Remove a listener for a specific event type."""
        if listener in self.listeners[event_type]:
            self.listeners[event_type].remove(listener)
            self._update_listener_metrics()
    
    def remove_global_listener(self, listener: Callable):
        """Remove a global listener."""
        if listener in self.global_listeners:
            self.global_listeners.remove(listener)
            self._update_listener_metrics()
    
    def _update_listener_metrics(self):
        """Update listener count metrics."""
        if not self.enable_metrics:
            return
        
        try:
            total_listeners = sum(len(listeners) for listeners in self.listeners.values())
            total_listeners += len(self.global_listeners)
            
            # Reset to 0 first, then add current count
            self._listener_count_gauge.add(-self.registry_metrics.active_listeners)
            self._listener_count_gauge.add(total_listeners)
            
            self.registry_metrics.active_listeners = total_listeners
            
        except Exception as e:
            logging.debug(f"Failed to update listener metrics: {e}")
    
    def _notify_listeners(self, event: BaseEvent):
        """Notify all relevant listeners."""
        # Notify type-specific listeners
        type_listeners = self.listeners.get(event.event_type, [])
        for listener in type_listeners:
            try:
                listener(event)
            except Exception as e:
                logging.error(f"Error in event listener: {e}")
                if self.enable_metrics:
                    self._record_error_metrics(e, "listener_execution")
        
        # Notify global listeners
        for listener in self.global_listeners:
            try:
                listener(event)
            except Exception as e:
                logging.error(f"Error in global listener: {e}")
                if self.enable_metrics:
                    self._record_error_metrics(e, "global_listener_execution")
    
    def get_events(
        self,
        filter_criteria: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[BaseEvent]:
        """Get events matching the filter criteria."""
        start_time = time.time()
        
        try:
            events = list(self.events)
            
            if filter_criteria:
                events = self._apply_filter(events, filter_criteria)
            
            if limit:
                events = events[-limit:]
            
            # Record query metrics
            if self.enable_metrics:
                duration_ms = (time.time() - start_time) * 1000
                self._record_query_metrics(len(events), duration_ms, filter_criteria)
            
            return events
            
        except Exception as e:
            logging.error(f"Error getting events: {e}")
            if self.enable_metrics:
                self._record_error_metrics(e, "event_query")
            raise
    
    def _apply_filter(self, events: List[BaseEvent], criteria: Dict[str, Any]) -> List[BaseEvent]:
        """Apply filter criteria to events."""
        filtered_events = []
        
        for event in events:
            if self._matches_criteria(event, criteria):
                filtered_events.append(event)
        
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
    
    def _record_query_metrics(self, result_count: int, duration_ms: float, criteria: Optional[Dict[str, Any]]):
        """Record metrics for event queries."""
        try:
            # Query duration histogram
            query_duration_histogram = self._registry_meter.create_histogram(
                name="registry.query.duration",
                description="Event query duration",
                unit="ms"
            )
            
            query_duration_histogram.record(
                duration_ms,
                attributes={
                    "result.count": str(result_count),
                    "has_filter": str(criteria is not None),
                }
            )
            
        except Exception as e:
            logging.debug(f"Failed to record query metrics: {e}")
    
    def get_session_events(self, session_id: str) -> List[BaseEvent]:
        """Get all events for a specific session."""
        return self.session_events.get(session_id, [])
    
    def get_plugin_events(self, plugin_name: str) -> List[BaseEvent]:
        """Get all events for a specific plugin."""
        return self.plugin_events.get(plugin_name, [])
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors across all plugins."""
        total_events = len(self.events)
        total_errors = sum(self.error_counts.values())
        
        summary = {
            "total_events": total_events,
            "total_errors": total_errors,
            "error_rate": total_errors / total_events if total_events > 0 else 0,
            "error_breakdown": dict(self.error_counts),
            "most_common_errors": sorted(
                self.error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "recent_errors": self.error_details[-10:] if self.error_details else []
        }
        
        return summary
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for the registry."""
        summary = {}
        
        for operation, timings in self.operation_timings.items():
            if timings:
                summary[operation] = {
                    "count": len(timings),
                    "avg_duration_ms": sum(timings) / len(timings),
                    "min_duration_ms": min(timings),
                    "max_duration_ms": max(timings),
                    "p95_duration_ms": sorted(timings)[int(len(timings) * 0.95)] if len(timings) > 0 else 0,
                }
        
        return summary
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about events."""
        total_events = len(self.events)
        
        # Calculate event type distribution
        event_distribution = {
            event_type.value: count
            for event_type, count in self.event_counts.items()
        }
        
        # Calculate session statistics
        session_count = len(self.session_events)
        avg_events_per_session = (
            total_events / session_count if session_count > 0 else 0
        )
        
        # Calculate plugin statistics
        plugin_count = len(self.plugin_events)
        avg_events_per_plugin = (
            total_events / plugin_count if plugin_count > 0 else 0
        )
        
        # Calculate time-based statistics
        if self.events:
            oldest_event = min(self.events, key=lambda e: e.timestamp)
            newest_event = max(self.events, key=lambda e: e.timestamp)
            time_span_ms = (newest_event.timestamp - oldest_event.timestamp).total_seconds() * 1000
            events_per_second = total_events / (time_span_ms / 1000) if time_span_ms > 0 else 0
        else:
            time_span_ms = 0
            events_per_second = 0
        
        return {
            "total_events": total_events,
            "event_distribution": event_distribution,
            "session_count": session_count,
            "avg_events_per_session": avg_events_per_session,
            "plugin_count": plugin_count,
            "avg_events_per_plugin": avg_events_per_plugin,
            "time_span_ms": time_span_ms,
            "events_per_second": events_per_second,
            "error_summary": self.get_error_summary(),
            "performance_summary": self.get_performance_summary(),
            "registry_metrics": self.registry_metrics,
        }
    
    def clear(self):
        """Clear all events from the registry."""
        self.events.clear()
        self.event_counts.clear()
        self.session_events.clear()
        self.plugin_events.clear()
        self.error_counts.clear()
        self.error_details.clear()
        self.operation_timings.clear()
        self.registry_metrics = RegistryMetrics()
        
        # Update metrics
        if self.enable_metrics:
            try:
                self._registry_size_gauge.add(-self.registry_metrics.total_events)
            except Exception as e:
                logging.debug(f"Failed to update size metrics: {e}")
    
    def shutdown(self):
        """Shutdown the registry gracefully."""
        try:
            # Clear all data
            self.clear()
            
            # Clear listeners
            self.listeners.clear()
            self.global_listeners.clear()
            
            logging.info("Telemetry event registry shutdown successfully")
            
        except Exception as e:
            logging.warning(f"Error during registry shutdown: {e}")


# Global telemetry registry instance
_global_telemetry_registry: Optional[TelemetryEventRegistry] = None


def get_global_telemetry_registry() -> TelemetryEventRegistry:
    """Get the global telemetry event registry."""
    global _global_telemetry_registry
    if _global_telemetry_registry is None:
        _global_telemetry_registry = TelemetryEventRegistry()
    return _global_telemetry_registry


def shutdown_global_telemetry_registry():
    """Shutdown the global telemetry event registry."""
    global _global_telemetry_registry
    if _global_telemetry_registry:
        _global_telemetry_registry.shutdown()
        _global_telemetry_registry = None


__all__ = [
    "RegistryMetrics",
    "TelemetryEventRegistry",
    "get_global_telemetry_registry",
    "shutdown_global_telemetry_registry",
]
