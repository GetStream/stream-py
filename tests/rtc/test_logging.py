import logging
import pytest
import io
from unittest.mock import patch, MagicMock

from getstream.utils import configure_logging
from getstream.video.rtc import join, logger as rtc_logger


def test_logging_configuration():
    """Test that configuring logging affects module loggers."""
    # Capture log output
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))

    # Configure logging with our handler
    configure_logging(level=logging.DEBUG, handler=handler)

    # Log a message with the module logger
    rtc_logger.debug("This is a debug message")
    rtc_logger.info("This is an info message")

    # Check the captured output
    log_output = log_capture.getvalue()
    assert "DEBUG:getstream.video.rtc:This is a debug message" in log_output
    assert "INFO:getstream.video.rtc:This is an info message" in log_output


@pytest.mark.asyncio
async def test_join_logging():
    """Test that ConnectionManager logs messages using the configured logger."""
    # Create a mock logger
    mock_logger = MagicMock()

    # Patch the ConnectionManager to use our mock logger
    with patch("getstream.video.rtc.connection_manager.logger", mock_logger):
        # Create mock call
        mock_call = MagicMock()

        # Call join, which creates and returns a ConnectionManager
        cm = await join(mock_call)
        # Enter the ConnectionManager context
        async with cm:
            pass  # We only care about the logging during __aenter__

    # Verify that logger.info was called with the expected messages
    mock_logger.info.assert_any_call("Discovering location")
    mock_logger.info.assert_any_call("Performing join call request on coordinator API")
