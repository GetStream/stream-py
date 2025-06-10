# -*- coding: utf-8 -*-
import logging
import functools
import asyncio  # Import asyncio if not already present
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2
from getstream.video.rtc.pb.stream.video.sfu.signal_rpc.signal_twirp import (
    AsyncSignalServerClient,
    _async_available,
)

logger = logging.getLogger(__name__)


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
def _check_response_for_error(response, method_name):
    """Checks the response for a populated error field and raises SfuRpcError if found."""
    # Check HasField first before accessing attributes of response.error
    if hasattr(response, "HasField") and response.HasField("error"):
        if response.error.code != models_pb2.ERROR_CODE_UNSPECIFIED:
            raise SfuRpcError(
                code=response.error.code,
                message=response.error.message,
                method_name=method_name,
            )
    return response


# Check if async capabilities are available
if not _async_available:
    raise ImportError("AsyncSignalServerClient requires 'aiohttp'. Please install it.")


# Inherit but use __getattribute__ for dynamic wrapping
class SignalClient(AsyncSignalServerClient):
    """An async TwirpClient wrapper that inherits from AsyncSignalServerClient
    (for IDE support) but uses __getattribute__ to dynamically wrap public
    methods with error checking, avoiding manual synchronization.
    """

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

            @functools.wraps(original_attr)
            async def wrapped_method(*args, **kwargs):
                # Call the original async method retrieved earlier
                response = await original_attr(*args, **kwargs)
                # Check response using the globally defined helper
                # Pass the original method name for clearer error messages
                return _check_response_for_error(response, name)

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
]
