"""Tests for WebSocket coordinator exception hierarchy."""

import pytest

from getstream.video.rtc.coordinator.errors import (
    StreamWSAuthError,
    StreamWSConnectionError,
    StreamWSException,
    StreamWSMaxRetriesExceeded,
)


def test_base_exception_inheritance():
    """Test that StreamWSException inherits from Exception."""
    assert issubclass(StreamWSException, Exception)


def test_auth_error_inheritance():
    """Test that StreamWSAuthError inherits from StreamWSException."""
    assert issubclass(StreamWSAuthError, StreamWSException)
    assert issubclass(StreamWSAuthError, Exception)


def test_connection_error_inheritance():
    """Test that StreamWSConnectionError inherits from StreamWSException."""
    assert issubclass(StreamWSConnectionError, StreamWSException)
    assert issubclass(StreamWSConnectionError, Exception)


def test_max_retries_error_inheritance():
    """Test that StreamWSMaxRetriesExceeded inherits from StreamWSException."""
    assert issubclass(StreamWSMaxRetriesExceeded, StreamWSException)
    assert issubclass(StreamWSMaxRetriesExceeded, Exception)


def test_exception_instantiation():
    """Test that all exception classes can be instantiated."""
    # Test base exception
    base_exc = StreamWSException("Base error")
    assert str(base_exc) == "Base error"
    assert isinstance(base_exc, Exception)

    # Test auth error
    auth_exc = StreamWSAuthError("Authentication failed")
    assert str(auth_exc) == "Authentication failed"
    assert isinstance(auth_exc, StreamWSException)
    assert isinstance(auth_exc, Exception)

    # Test connection error
    conn_exc = StreamWSConnectionError("Connection failed")
    assert str(conn_exc) == "Connection failed"
    assert isinstance(conn_exc, StreamWSException)
    assert isinstance(conn_exc, Exception)

    # Test max retries error
    retries_exc = StreamWSMaxRetriesExceeded("Max retries exceeded")
    assert str(retries_exc) == "Max retries exceeded"
    assert isinstance(retries_exc, StreamWSException)
    assert isinstance(retries_exc, Exception)


def test_exception_raising_and_catching():
    """Test that exceptions can be raised and caught properly."""
    # Test raising and catching specific exceptions
    with pytest.raises(StreamWSAuthError):
        raise StreamWSAuthError("Auth failed")

    with pytest.raises(StreamWSConnectionError):
        raise StreamWSConnectionError("Connection failed")

    with pytest.raises(StreamWSMaxRetriesExceeded):
        raise StreamWSMaxRetriesExceeded("Max retries exceeded")

    # Test catching with base exception
    with pytest.raises(StreamWSException):
        raise StreamWSAuthError("Should be caught by base exception")

    with pytest.raises(StreamWSException):
        raise StreamWSConnectionError("Should be caught by base exception")

    with pytest.raises(StreamWSException):
        raise StreamWSMaxRetriesExceeded("Should be caught by base exception")


def test_exception_hierarchy_distinctness():
    """Test that specific exception classes are distinct from each other."""
    # Auth error should not be instance of connection error
    auth_exc = StreamWSAuthError("Auth error")
    assert not isinstance(auth_exc, StreamWSConnectionError)
    assert not isinstance(auth_exc, StreamWSMaxRetriesExceeded)

    # Connection error should not be instance of auth error
    conn_exc = StreamWSConnectionError("Connection error")
    assert not isinstance(conn_exc, StreamWSAuthError)
    assert not isinstance(conn_exc, StreamWSMaxRetriesExceeded)

    # Max retries error should not be instance of other specific errors
    retries_exc = StreamWSMaxRetriesExceeded("Retries error")
    assert not isinstance(retries_exc, StreamWSAuthError)
    assert not isinstance(retries_exc, StreamWSConnectionError)

    # But all should be instances of the base exception
    assert isinstance(auth_exc, StreamWSException)
    assert isinstance(conn_exc, StreamWSException)
    assert isinstance(retries_exc, StreamWSException)
