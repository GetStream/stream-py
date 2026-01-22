"""
Central trace buffer for RTC events.
"""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, List, Optional

from google.protobuf.message import Message

TraceRecord = List[Any]  # [tag, id, data, timestamp_ms]


@dataclass
class TraceSlice:
    """A snapshot of trace records with rollback capability."""

    snapshot: List[TraceRecord]
    rollback: Callable[[], None]


def timestamp_ms() -> int:
    """Get current timestamp in milliseconds."""
    return int(time.time() * 1000)


def sanitize_value(value: Any) -> Any:
    """Convert values to JSON-serializable format.

    Handles:
    - datetime objects
    - protobuf messages
    - nested dicts and lists
    - None values
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        # Convert datetime to milliseconds timestamp (matching JS SDK format)
        return int(value.timestamp() * 1000)

    if isinstance(value, Message):
        # Convert protobuf message to dict with camelCase field names
        from google.protobuf.json_format import MessageToDict

        return MessageToDict(value)

    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [sanitize_value(item) for item in value]

    if isinstance(value, bytes):
        # Convert bytes to hex string for JSON serialization
        return value.hex()

    # For primitive types (str, int, float, bool), return as-is
    if isinstance(value, (str, int, float, bool)):
        return value

    # For any other type, try string conversion
    try:
        return str(value)
    except Exception:
        return repr(value)


class Tracer:
    """Central trace buffer for RTC events.

    Collects trace records in the format [tag, pc_id, data, timestamp_ms]
    for later sending to the SFU via SendStats RPC.
    """

    def __init__(self):
        self._buffer: List[TraceRecord] = []
        self._enabled = True

    def trace(self, tag: str, pc_id: Optional[str], data: Any) -> None:
        """Add trace record: [tag, id, data, timestamp_ms]

        Args:
            tag: The trace event tag (e.g., "create", "signalingstatechange")
            pc_id: The peer connection ID (e.g., "0-pub", "0-sub", "0-sfu-hostname")
            data: The trace data (will be sanitized for JSON serialization)
        """
        if not self._enabled:
            return
        self._buffer.append([tag, pc_id, sanitize_value(data), timestamp_ms()])

    def take(self) -> TraceSlice:
        """Return buffer snapshot with rollback capability.

        Returns a TraceSlice containing the current buffer contents
        and a rollback function that can restore the buffer if sending fails.
        """
        snapshot = self._buffer
        self._buffer = []

        def rollback():
            # Prepend the snapshot to any new traces added since take()
            self._buffer = snapshot + self._buffer

        return TraceSlice(snapshot=snapshot, rollback=rollback)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable tracing.

        When disabled, existing traces are cleared.
        """
        if self._enabled == enabled:
            return
        self._enabled = enabled
        self._buffer = []

    def dispose(self) -> None:
        """Clear all trace records."""
        self._buffer = []

    @property
    def enabled(self) -> bool:
        """Check if tracing is enabled."""
        return self._enabled

    def __len__(self) -> int:
        """Return the number of trace records in the buffer."""
        return len(self._buffer)
