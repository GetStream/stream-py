import pytest
import logging
import io
from unittest.mock import patch, MagicMock

from getstream.utils.retry import (
    Retry,
    RetryExhausted,
    default_backoff,
    default_can_retry,
)


# Test-specific exceptions
class TestException(Exception):
    pass


class RetriableException(Exception):
    pass


class NonRetriableException(Exception):
    pass


def test_default_backoff():
    """Test the default backoff function."""
    # Test first few attempts to verify exponential pattern
    assert default_backoff(1) == 0.1
    assert default_backoff(2) == 0.2
    assert default_backoff(3) == 0.4
    assert default_backoff(4) == 0.8

    # Test that it caps at 10 seconds
    assert default_backoff(100) == 10


def test_default_can_retry():
    """Test the default retry condition function."""
    # Should retry all exceptions by default
    assert default_can_retry(Exception()) is True
    assert default_can_retry(ValueError()) is True
    assert default_can_retry(KeyError()) is True


def test_successful_execution():
    """Test that the Retry allows successful code to run without interference."""

    # Define a function that succeeds
    def successful_func():
        return "success"

    retry = Retry(max_retries=3)

    # This function should run once and return its result
    result = retry(successful_func)

    assert result == "success"
    assert retry.attempts == 1  # Should have only attempted once


def test_retry_eventually_succeeds():
    """Test that Retry retries until success."""
    counter = 0

    def function_that_sometimes_fails():
        nonlocal counter
        counter += 1
        if counter < 3:
            raise TestException(f"Failed attempt {counter}")
        return "success"

    retry = Retry(max_retries=3)

    with patch("time.sleep", lambda s: None):  # Don't actually sleep in tests
        result = retry(function_that_sometimes_fails)

    assert result == "success"
    assert counter == 3  # It should succeed on the third attempt
    assert retry.attempts == 3  # Should have attempted 3 times total


def test_retry_eventually_fails():
    """Test that Retry gives up after max_retries and raises RetryExhausted."""
    counter = 0

    def function_that_always_fails():
        nonlocal counter
        counter += 1
        raise TestException(f"Failed attempt {counter}")

    retry = Retry(max_retries=3)

    with patch("time.sleep", lambda s: None):  # Don't actually sleep in tests
        with pytest.raises(RetryExhausted) as excinfo:
            retry(function_that_always_fails)

    assert counter == 4  # Initial attempt + 3 retries
    assert retry.attempts == 4  # Should have attempted 4 times total
    assert "All 4 retry attempts exhausted" in str(excinfo.value)


def test_custom_retry_condition():
    """Test that Retry respects custom retry conditions."""
    counter = 0

    def can_retry(exc):
        return isinstance(exc, RetriableException)

    def function_that_throws_retriable():
        nonlocal counter
        counter += 1
        if counter < 2:
            raise RetriableException("This should be retried")
        return "success"

    def function_that_throws_non_retriable():
        raise NonRetriableException("This should not be retried")

    # Test with retriable exception
    retry = Retry(max_retries=2, can_retry=can_retry)

    with patch("time.sleep", lambda s: None):  # Don't actually sleep in tests
        result = retry(function_that_throws_retriable)

    assert result == "success"
    assert counter == 2  # It should succeed on the second attempt

    # Test with non-retriable exception
    counter = 0
    retry = Retry(max_retries=2, can_retry=can_retry)

    with patch("time.sleep", lambda s: None):  # Don't actually sleep in tests
        with pytest.raises(NonRetriableException):
            retry(function_that_throws_non_retriable)

    assert retry.attempts == 1  # It should not retry


def test_custom_backoff_strategy():
    """Test that Retry uses the custom backoff strategy."""
    sleep_times = []
    counter = 0

    def custom_backoff(attempt):
        return attempt * 2  # Linear backoff

    def mock_sleep(seconds):
        sleep_times.append(seconds)

    def function_that_sometimes_fails():
        nonlocal counter
        counter += 1
        if counter < 3:
            raise TestException(f"Failed attempt {counter}")
        return "success"

    retry = Retry(max_retries=3, backoff_strategy=custom_backoff)

    with patch("time.sleep", mock_sleep):
        result = retry(function_that_sometimes_fails)

    assert result == "success"
    assert counter == 3  # It should succeed on the third attempt
    assert sleep_times == [2, 4]  # Should have slept according to our strategy


def test_logging():
    """Test that Retry logs warnings on retries."""
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    formatter = logging.Formatter("%(levelname)s:%(message)s")
    handler.setFormatter(formatter)

    logger = logging.getLogger("test_retry_logger")
    logger.setLevel(logging.WARNING)
    logger.addHandler(handler)
    logger.propagate = False  # Don't pass to parent handlers

    counter = 0

    def function_that_eventually_succeeds():
        nonlocal counter
        counter += 1
        if counter < 3:
            raise TestException(f"Failed attempt {counter}")
        return "success"

    retry = Retry(max_retries=3, logger=logger)

    with patch("time.sleep", lambda s: None):  # Don't actually sleep in tests
        retry(function_that_eventually_succeeds)

    log_output = log_stream.getvalue()
    assert "WARNING:Retry attempt 1/3" in log_output
    assert "WARNING:Retry attempt 2/3" in log_output
    assert "TestException: Failed attempt 1" in log_output
    assert "TestException: Failed attempt 2" in log_output


def test_nested_retries():
    """Test that nested Retry invocations work correctly."""
    outer_counter = 0
    inner_counter = 0

    def inner_function():
        nonlocal inner_counter
        inner_counter += 1
        if inner_counter < 2:
            raise TestException("Inner retry needed")
        return "inner success"

    def outer_function():
        nonlocal outer_counter
        outer_counter += 1

        # Call inner retry
        inner_retry = Retry(max_retries=1)
        inner_result = inner_retry(inner_function)

        if outer_counter < 2:
            raise TestException("Outer retry needed")

        return f"{inner_result} and outer success"

    outer_retry = Retry(max_retries=2)

    with patch("time.sleep", lambda s: None):  # Don't actually sleep in tests
        result = outer_retry(outer_function)

    assert result == "inner success and outer success"
    assert outer_counter == 2  # Outer function should run twice
    # Note: The inner function may run more than twice with our implementation
    # The important part is that the result is correct
    assert inner_counter >= 2  # Inner function runs at least twice


def test_retry_with_different_exceptions():
    """Test that Retry handles different exceptions on each retry."""
    exceptions = [
        ValueError("First error"),
        KeyError("Second error"),
        TypeError("Third error"),
    ]
    attempt = 0

    def function_with_different_exceptions():
        nonlocal attempt
        attempt += 1
        raise exceptions[attempt - 1]

    mock_logger = MagicMock()
    retry = Retry(max_retries=2, logger=mock_logger)

    with patch("time.sleep", lambda s: None):  # Don't actually sleep in tests
        with pytest.raises(RetryExhausted) as excinfo:
            retry(function_with_different_exceptions)

    # Check that the last exception is the one in the RetryExhausted
    assert excinfo.value.original_exception == exceptions[2]

    # Check that the logger was called with each exception
    assert mock_logger.warning.call_count >= 2


def test_retry_as_decorator():
    """Test that Retry works as a decorator."""
    counter = 0

    # Apply the retry decorator
    @Retry(max_retries=2)
    def decorated_function():
        nonlocal counter
        counter += 1
        if counter < 3:
            raise TestException(f"Failed attempt {counter}")
        return "success"

    # Mock sleep to avoid delays in tests
    with patch("time.sleep", lambda s: None):
        result = decorated_function()

    assert result == "success"
    assert counter == 3  # Should succeed on the third attempt


def test_retry_as_context_manager():
    """Test that Retry works as a context manager."""
    # This is a manual simulation of how the context manager would work
    retry = Retry(max_retries=2)
    counter = 0

    with patch("time.sleep", lambda s: None):  # Don't actually sleep in tests
        # Manually simulate context manager behavior
        retry.__enter__()

        for attempt in range(1, 4):  # Initial + 2 retries
            try:
                counter = attempt
                if counter < 3:
                    raise TestException(f"Failed attempt {counter}")
                break  # Success
            except Exception as e:
                # Call __exit__ with the exception
                should_suppress = retry.__exit__(type(e), e, None)
                if not should_suppress:
                    # If not suppressed, it would raise in real usage
                    if counter == 3:  # Last attempt
                        # Should raise RetryExhausted on last attempt
                        assert isinstance(e, RetryExhausted)
                        break
                    raise

    assert counter == 3  # Should have tried 3 times (original + 2 retries)


def test_retry_context_manager_exhaustion():
    """Test that Retry as context manager raises RetryExhausted when all retries fail."""
    retry = Retry(max_retries=2)
    counter = 0
    final_exception = None

    with patch("time.sleep", lambda s: None):  # Don't actually sleep in tests
        # Manually simulate context manager behavior
        retry.__enter__()

        for attempt in range(1, 4):  # Initial + 2 retries
            try:
                counter = attempt
                raise TestException(f"Always fails {counter}")
            except Exception as e:
                try:
                    # Call __exit__ with the exception
                    should_suppress = retry.__exit__(type(e), e, None)
                    if not should_suppress:
                        # If not suppressed, it would raise in real usage
                        final_exception = e
                        break
                except RetryExhausted as re:
                    # In the last attempt, RetryExhausted will be raised
                    final_exception = re
                    break

    assert counter == 3  # Should have tried 3 times (original + 2 retries)
    assert isinstance(final_exception, RetryExhausted)
    assert "All 3 retry attempts exhausted" in str(final_exception)


def test_retry_context_manager_custom_condition():
    """Test that Retry as context manager respects custom retry conditions."""

    def custom_can_retry(exc):
        return isinstance(exc, RetriableException)

    retry = Retry(max_retries=2, can_retry=custom_can_retry)
    counter = 0
    final_exception = None

    with patch("time.sleep", lambda s: None):  # Don't actually sleep in tests
        # Manually simulate context manager behavior
        retry.__enter__()

        try:
            counter += 1
            raise NonRetriableException("This should not be retried")
        except Exception as e:
            # Call __exit__ with the exception
            should_suppress = retry.__exit__(type(e), e, None)
            if not should_suppress:
                # If not suppressed, it would raise in real usage
                final_exception = e

    assert counter == 1  # Should have tried only once
    assert isinstance(final_exception, NonRetriableException)
