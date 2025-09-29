"""
Exception classes for WebSocket coordinator operations.

This module defines the exception hierarchy for WebSocket-related errors
in the Stream Video Coordinator client.
"""

import logging

logger = logging.getLogger(__name__)


class StreamWSException(Exception):
    """
    Base exception class for all WebSocket coordinator-related errors.

    This is the root exception from which all other WebSocket coordinator
    exceptions inherit.
    """

    pass


class StreamWSAuthError(StreamWSException):
    """
    Exception raised when authentication with the WebSocket server fails.

    This error is raised when the first frame received from the server
    has type == "error", indicating authentication failure. This error
    does not trigger retry logic.
    """

    pass


class StreamWSConnectionError(StreamWSException):
    """
    Exception raised when there are transient connection issues.

    This error is raised for network-related failures, socket errors,
    and other transient connection problems that may be resolved by retrying.
    """

    pass


class StreamWSMaxRetriesExceeded(StreamWSException):
    """
    Exception raised when the maximum number of retry attempts is exceeded.

    This error is raised when all retry attempts have been exhausted and
    the connection still cannot be established.
    """

    pass
