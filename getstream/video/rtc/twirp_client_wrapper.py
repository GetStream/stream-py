# -*- coding: utf-8 -*-
import asyncio  # Import asyncio if not already present
import functools
import logging
from typing import TYPE_CHECKING, Callable, Optional

import structlog
from structlog.stdlib import LoggerFactory, add_log_level
from structlog.types import BindableLogger
from twirp.context import Context as TwirpContext

from getstream.common import telemetry
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2
from getstream.video.rtc.pb.stream.video.sfu.signal_rpc.signal_twirp import (
    AsyncSignalServerClient,
)

if TYPE_CHECKING:
    from getstream.video.rtc.tracer import Tracer

logger = logging.getLogger(__name__)

# RPC methods to exclude from tracing (to avoid circular tracing)
RPC_TRACE_EXCLUSIONS = {"SendStats"}

# RPC methods that should include response data in traces
RPC_RESPONSE_INCLUSIONS = {"SetPublisher"}


def _get_twirp_default_logger() -> BindableLogger:
    """Re-generate the default structlog config used inside `twirp` without overriding
     the root logger level.
    A trimmed down copy of `twirp.logging.configure`"""

    structlog.configure(
        logger_factory=LoggerFactory(),
        processors=[
            add_log_level,
            # Add timestamp
            structlog.processors.TimeStamper("iso"),
            # Add stack information
            structlog.processors.StackInfoRenderer(),
            # Set exception field using exec info
            structlog.processors.format_exc_info,
            # Render event_dict as JSON
            structlog.processors.JSONRenderer(),
        ],
    )
    return structlog.get_logger()


_TWIRP_DEFAULT_LOGGER = _get_twirp_default_logger()


class Context(TwirpContext):
    """A wrapper around `twirp.context.Context` to fix the logging issue.
    Use it as a replacement.
    """

    def __init__(self, *args, headers=None):
        # Passing our own logger here because twirp configures the root logger
        # under the hood, making every other library noisy.
        super().__init__(*args, logger=_TWIRP_DEFAULT_LOGGER, headers=headers)


# Define a custom exception for SFU RPC errors
class SfuRpcError(Exception):
    """Exception raised when an SFU RPC call returns an error."""

    def __init__(self, code, message, method_name):
        self.code = code
        self.message = message
        self.method_name = method_name
        super().__init__(
            f"SFU RPC Error in {method_name} - Code: {code}, Message: {message}"
        )


# Helper function to check response error
def _check_response_for_error(response, method_name, span=None):
    """Checks the response for an error and annotates the span.

    - If an error is present, adds error code/message to the span and raises.
    - Otherwise, marks the call as ok on the span.
    """
    try:
        if span is not None:
            # Always record which RPC method we hit
            try:
                span.set_attribute("twirp.method", method_name)
            except Exception:
                pass

        if hasattr(response, "HasField") and response.HasField("error"):
            code = getattr(response.error, "code", models_pb2.ERROR_CODE_UNSPECIFIED)
            message = getattr(response.error, "message", "")
            if code != models_pb2.ERROR_CODE_UNSPECIFIED:
                # Annotate span with error details
                if span is not None:
                    try:
                        span.set_attribute("twirp.error", True)
                        span.set_attribute("twirp.error_code", int(code))
                        if message:
                            span.set_attribute("twirp.error_message", message)
                        # Set error status when available
                        if hasattr(telemetry, "Status") and hasattr(
                            telemetry, "StatusCode"
                        ):
                            span.set_status(
                                telemetry.Status(
                                    telemetry.StatusCode.ERROR, str(message)
                                )
                            )
                    except Exception:
                        pass
                # Raise structured error
                raise SfuRpcError(code=code, message=message, method_name=method_name)

        # No error present
        if span is not None:
            try:
                span.set_attribute("twirp.error", False)
            except Exception:
                pass
        return response
    except Exception:
        # Ensure we re-raise for caller handling
        raise


# Inherit but use __getattribute__ for dynamic wrapping
class SignalClient(AsyncSignalServerClient):
    """An async TwirpClient wrapper that inherits from AsyncSignalServerClient
    (for IDE support) but uses __getattribute__ to dynamically wrap public
    methods with error checking, avoiding manual synchronization.

    Also supports optional tracing of RPC calls for debugging.
    """

    def __init__(
        self,
        address: str,
        tracer: Optional["Tracer"] = None,
        sfu_id_fn: Optional[Callable[[], Optional[str]]] = None,
    ):
        """Initialize the SignalClient.

        Args:
            address: The address of the signaling server
            tracer: Optional tracer for RPC tracing
            sfu_id_fn: Optional function that returns the current SFU ID for tracing
        """
        super().__init__(address)
        self._tracer = tracer
        self._sfu_id_fn = sfu_id_fn

    def __getattribute__(self, name: str):
        """Intercepts attribute access to dynamically wrap public async methods."""
        # Get the original attribute using the default mechanism (respects MRO)
        # Use super() to avoid recursion within this method if accessing SignalClient's own attributes
        original_attr = super().__getattribute__(name)

        # Wrap public, callable async methods (heuristic: callable, not starting with '_')
        # Important: Check if it's an async function using asyncio.iscoroutinefunction
        if (
            callable(original_attr)
            and not name.startswith("_")
            and asyncio.iscoroutinefunction(original_attr)
        ):
            # Get tracer and sfu_id_fn from instance (use object.__getattribute__ to avoid recursion)
            tracer = object.__getattribute__(self, "_tracer")
            sfu_id_fn = object.__getattribute__(self, "_sfu_id_fn")

            @functools.wraps(original_attr)
            async def wrapped_method(*args, **kwargs):
                # Trace RPC request (if not excluded)
                should_trace = tracer and name not in RPC_TRACE_EXCLUSIONS
                sfu_id = sfu_id_fn() if sfu_id_fn else None

                # Extract request data for tracing
                request_data = None
                if should_trace:
                    request = kwargs.get("request")
                    if request:
                        try:
                            from google.protobuf.json_format import MessageToDict

                            # Use default camelCase field names (no preserving_proto_field_name)
                            request_data = MessageToDict(request)
                        except Exception:
                            request_data = str(request)
                    tracer.trace(name, sfu_id, request_data)

                with telemetry.start_as_current_span(f"signaling.twirp.{name}") as span:
                    try:
                        # Call the original async method retrieved earlier
                        response = await original_attr(*args, **kwargs)

                        # Trace response for certain methods
                        if should_trace and name in RPC_RESPONSE_INCLUSIONS:
                            try:
                                from google.protobuf.json_format import MessageToDict

                                # Use default camelCase field names
                                response_data = MessageToDict(response)
                                tracer.trace(f"{name}Response", sfu_id, response_data)
                            except Exception:
                                pass

                        # Check response and annotate span
                        return _check_response_for_error(response, name, span=span)
                    except Exception as e:
                        # Trace failure
                        if should_trace:
                            tracer.trace(
                                f"{name}OnFailure", sfu_id, [str(e), request_data]
                            )
                        raise

            # Return the dynamic wrapper
            return wrapped_method
        elif callable(original_attr) and not name.startswith("_"):

            @functools.wraps(original_attr)
            async def wrapped_method(*args, **kwargs):
                with telemetry.start_as_current_span(f"signaling.twirp.{name}") as span:
                    response = original_attr(*args, **kwargs)
                    return _check_response_for_error(response, name, span=span)

            # Return the dynamic wrapper
            return wrapped_method
        else:
            # For non-callable attributes, or non-async methods, or private methods,
            # return the original attribute directly.
            return original_attr

    # No need to explicitly override each method like SetPublisher, SendAnswer etc.
    # __getattribute__ handles them dynamically.


# Export necessary symbols
__all__ = [
    "SfuRpcError",
    "SignalClient",
    "Context",
]
