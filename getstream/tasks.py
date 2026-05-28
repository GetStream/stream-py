"""Task-waiting helpers (CHA-2958 §8).

Sync and async polling helpers that wait for an async task to reach a
terminal state. On ``status='failed'`` they raise ``StreamTaskException``
populated from the task's ``ErrorResult``; on timeout they raise
``StreamTransportException`` with ``error_type='timeout'``.

The public surface for SDK users is the ``wait_for_task`` method on
``Stream``/``AsyncStream`` (see ``getstream.stream``); the functions here
are reused by both.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

from getstream.exceptions import (
    StreamTaskException,
    StreamTransportException,
    TRANSPORT_ERROR_TIMEOUT,
)

if TYPE_CHECKING:
    from getstream.models import GetTaskResponse
    from getstream.stream_response import StreamResponse


DEFAULT_POLL_INTERVAL = 1.0
DEFAULT_TIMEOUT = 60.0


def _build_task_exception(task_id: str, response_data: Any) -> StreamTaskException:
    """Construct a ``StreamTaskException`` from a ``GetTaskResponse.data``.

    Missing ``error`` (shouldn't happen when status == 'failed' but defend
    anyway) collapses to ``error_type='unknown'`` with an empty description.
    """
    err = getattr(response_data, "error", None)
    return StreamTaskException(
        task_id=task_id,
        error_type=err.type if err is not None else "unknown",
        description=err.description if err is not None else "",
        stack_trace=err.stacktrace if err is not None else None,
        version=err.version if err is not None else None,
    )


def _timeout_exception(task_id: str, timeout: float) -> StreamTransportException:
    return StreamTransportException(
        error_type=TRANSPORT_ERROR_TIMEOUT,
        message=(
            f"wait_for_task timed out after {timeout}s waiting for task {task_id}"
        ),
    )


def wait_for_task_sync(
    client: Any,
    task_id: str,
    *,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    timeout: float = DEFAULT_TIMEOUT,
) -> "StreamResponse[GetTaskResponse]":
    """Poll ``client.get_task(id=task_id)`` (sync) until terminal state.

    Returns the ``StreamResponse`` on ``completed``. Raises
    ``StreamTaskException`` on ``failed``, ``StreamTransportException`` with
    ``error_type='timeout'`` if ``timeout`` elapses first.
    """
    deadline = time.monotonic() + timeout
    while True:
        response = client.get_task(id=task_id)
        status = response.data.status
        if status == "completed":
            return response
        if status == "failed":
            raise _build_task_exception(task_id, response.data)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise _timeout_exception(task_id, timeout)
        time.sleep(min(poll_interval, remaining))


async def wait_for_task_async(
    client: Any,
    task_id: str,
    *,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    timeout: float = DEFAULT_TIMEOUT,
) -> "StreamResponse[GetTaskResponse]":
    """Async variant of :func:`wait_for_task_sync`.

    Uses ``asyncio.get_running_loop().time()`` for the deadline so callers
    don't pay for instantiating a default loop when none exists.
    """
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while True:
        response = await client.get_task(id=task_id)
        status = response.data.status
        if status == "completed":
            return response
        if status == "failed":
            raise _build_task_exception(task_id, response.data)
        remaining = deadline - loop.time()
        if remaining <= 0:
            raise _timeout_exception(task_id, timeout)
        await asyncio.sleep(min(poll_interval, remaining))


__all__ = [
    "DEFAULT_POLL_INTERVAL",
    "DEFAULT_TIMEOUT",
    "wait_for_task_sync",
    "wait_for_task_async",
]
