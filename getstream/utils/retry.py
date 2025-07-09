import logging
from typing import Callable, Optional, Any

logger = logging.getLogger("getstream.utils.retry")


class RetryExhausted(Exception):
    """Exception raised when all retry attempts have been exhausted."""

    def __init__(self, original_exception: Exception, attempts: int):
        self.original_exception = original_exception
        self.attempts = attempts
        super().__init__(
            f"All {attempts} retry attempts exhausted. Last error: {original_exception}"
        )


def default_backoff(attempt: int) -> float:
    """Default backoff strategy with exponential backoff.

    Args:
        attempt: The current attempt number (starting from 1)

    Returns:
        The number of seconds to sleep
    """
    raise NotImplementedError("Retry functionality has been removed")


def default_can_retry(exception: Exception) -> bool:
    """Default retry condition that retries all exceptions.

    Args:
        exception: The exception to check

    Returns:
        True if the exception can be retried, False otherwise
    """
    raise NotImplementedError("Retry functionality has been removed")


class Retry:
    """This class has been removed.

    All methods will raise NotImplementedError.
    """

    def __init__(
        self,
        max_retries: int = 3,
        can_retry: Callable[[Exception], bool] = default_can_retry,
        backoff_strategy: Callable[[int], float] = default_backoff,
        logger: Optional[logging.Logger] = None,
        current_attempt: int = 0,
    ):
        """Initialize a new Retry instance."""
        raise NotImplementedError("Retry functionality has been removed")

    def __enter__(self) -> "Retry":
        """Enter the context manager."""
        raise NotImplementedError("Retry functionality has been removed")

    def __exit__(
        self, exc_type: Any, exc_val: Optional[Exception], exc_tb: Any
    ) -> bool:
        """Exit the context manager."""
        raise NotImplementedError("Retry functionality has been removed")

    def __call__(self, func: Callable[[], Any]) -> Any:
        """Execute a function with retries (backwards compatibility)."""
        raise NotImplementedError("Retry functionality has been removed")
