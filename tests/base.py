import functools
import time
from abc import ABC

import httpx

from getstream import Stream
from getstream.base import StreamAPIException
from getstream.video.call import Call


class VideoTestClass(ABC):
    """
    Abstract base class for video tests that need to share the same call and client objects using pytest fixture
    """

    client: Stream
    call: Call


def wait_for_task(client, task_id, timeout_ms=10000, poll_interval_ms=1000):
    """
    Wait until the task is completed or timeout is reached.

    Args:
        client: The client used to make the API call.
        task_id: The ID of the task to wait for.
        timeout_ms: The maximum amount of time to wait (in ms).
        poll_interval_ms: The interval between poll attempts (in ms).

    Returns:
        The final response from the API.

    Raises:
        RuntimeError: If the task failed.
        TimeoutError: If the task is not completed within the timeout period.
    """
    start_time = time.time() * 1000  # Convert to milliseconds
    while True:
        response = client.get_task(id=task_id)
        if response.data.status == "completed":
            return response
        if response.data.status == "failed":
            raise RuntimeError(f"Task {task_id} failed")
        if (time.time() * 1000) - start_time > timeout_ms:
            raise TimeoutError(f"Task {task_id} did not complete within {timeout_ms}ms")
        time.sleep(poll_interval_ms / 1000.0)


def _is_transient_error(exc: Exception) -> bool:
    """Check if an exception is a transient infrastructure error worth retrying."""
    if isinstance(exc, (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError)):
        return True
    if isinstance(exc, StreamAPIException):
        body = ""
        try:
            body = exc.http_response.text or ""
        except Exception:
            pass
        if "upstream connect error" in body or "disconnect" in body:
            return True
        if exc.status_code in (502, 503, 504):
            return True
    return False


def retry_on_transient_error(max_retries=3, backoff=1.0):
    """Decorator that retries a test on transient infrastructure errors."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    if attempt < max_retries and _is_transient_error(exc):
                        last_exc = exc
                        time.sleep(backoff * (attempt + 1))
                        continue
                    raise
            raise last_exc

        return wrapper

    return decorator
