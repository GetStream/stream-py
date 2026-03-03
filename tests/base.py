import time
from abc import ABC

from getstream import Stream
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
