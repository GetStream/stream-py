import json
import asyncio
from typing import Dict, List, Optional, Union
from urllib.parse import quote
from datetime import datetime
from datetime import timezone
from urllib.parse import urlparse, urlunparse
import logging
import sys

from .event_emitter import StreamAsyncIOEventEmitter

UTC = timezone.utc


def validate_and_clean_url(url):
    """
    Validates a given URL and removes any trailing slashes.

    Args:
        url (str): The URL to validate and clean.

    Returns:
        str: The validated URL without trailing slashes, or raises an exception if invalid.

    Raises:
        ValueError: If the URL is not valid.
    """

    parsed_url = urlparse(url)
    if parsed_url.scheme not in ("http", "https"):
        raise ValueError("Provided URL is not a valid HTTP URL.")

    path = parsed_url.path.rstrip("/")
    cleaned_url = urlunparse(parsed_url._replace(path=path))
    return cleaned_url


def encode_datetime(date: Optional[datetime]) -> Optional[str]:
    """
    Encodes a datetime object into an ISO 8601 formatted string.

    Args:
    date (Optional[datetime]): The datetime object to encode.

    Returns:
    Optional[str]: The ISO 8601 string representation of the datetime, or None if input is None.
    """
    if date is None:
        return None
    return date.isoformat()


def datetime_from_unix_ns(
    ts: Optional[
        Union[
            int,
            float,
            str,
            Dict[str, Union[int, float, str]],
            List[Union[int, float, str]],
        ]
    ],
) -> Optional[Union[datetime, Dict[str, datetime], List[datetime]]]:
    """
    Converts unix timestamp(s) (nanoseconds since epoch) to datetime object(s).
    Can handle single values, dictionaries, or lists of values.

    Args:
    ts: Nanoseconds since epoch (int, float, or string representation),
        or a dictionary/list of such values.

    Returns:
    Datetime object(s) or None if input is None.
    """
    if ts is None:
        return None

    if isinstance(ts, dict):
        return {k: datetime_from_unix_ns(v) for k, v in ts.items()}

    if isinstance(ts, list):
        return [datetime_from_unix_ns(v) for v in ts]

    if isinstance(ts, str):
        ts = int(ts)

    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts / 1e9, tz=timezone.utc)

    raise TypeError(f"Unsupported type for ts: {type(ts)}")


def build_query_param(**kwargs):
    """
    Constructs a dictionary of query parameters from keyword arguments.

    This function handles various data types:
    - JSON-serializable objects with a `to_json` method will be serialized using that method.
    - Booleans are converted to lowercase strings.
    - Lists are converted to comma-separated strings with URL-encoded values.
    - Other types (strings, integers, dictionaries) are handled appropriately.

    Args:
        **kwargs: Arbitrary keyword arguments representing potential query parameters.

    Returns:
        dict: A dictionary where keys are parameter names and values are URL-ready strings.
    """
    params = {}
    for key, value in kwargs.items():
        if value is None:
            continue
        if hasattr(value, "to_json") and callable(value.to_json):
            params[key] = value.to_json()
        elif isinstance(value, bool):
            params[key] = str(value).lower()
        elif isinstance(value, (str, int)):
            params[key] = str(value)
        elif isinstance(value, list):
            # Process each element, escaping commas in the string representation
            params[key] = ",".join(quote(str(v)) for v in value)
        else:
            # For dictionaries or any other types of objects
            params[key] = json.dumps(value)
    return params


def build_body_dict(**kwargs):
    """
    Constructs a dictionary for the body of a request, handling nested structures.
    If an object has a `to_dict` method, it calls this method to serialize the object.
    It handles nested dictionaries and lists recursively.

    Args:
        **kwargs: Keyword arguments representing keys and values to be included in the body dictionary.

    Returns:
        dict: A dictionary with keys corresponding to kwargs keys and values processed, potentially recursively.
    """

    def handle_value(value):
        if hasattr(value, "to_dict") and callable(value.to_dict):
            return value.to_dict()
        elif isinstance(value, dict):
            return {k: handle_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [handle_value(v) for v in value]
        else:
            return value

    data = {key: handle_value(value) for key, value in kwargs.items()}
    return data


def configure_logging(level=None, handler=None, format=None):
    """
    Configure logging for the Stream library.

    Args:
        level: The logging level to use (default: logging.INFO)
        handler: A custom handler to use (default: StreamHandler)
        format: A custom format string (default: '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    """
    # Get the root logger for the library
    logger = logging.getLogger("getstream")

    # Set the level if provided
    if level is not None:
        logger.setLevel(level)

    # Create a handler if not provided
    if handler is None:
        handler = logging.StreamHandler(sys.stdout)

        # Set the format if provided
        if format is None:
            format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        handler.setFormatter(logging.Formatter(format))

    # Add the handler
    logger.addHandler(handler)

    return logger


async def sync_to_async(func, *args, **kwargs):
    """
    Run a synchronous function asynchronously in a separate thread.

    This helper schedules the blocking function ``func`` to be executed in a
    thread from the default ``ThreadPoolExecutor`` via
    :func:`asyncio.to_thread`.  The returned coroutine is wrapped in
    :func:`asyncio.shield` so that it cannot be cancelled by a caller's
    cancellation of the surrounding coroutine.  This mirrors the behaviour
    of many legacy wrappers that provide an ``async`` interface to a sync
    API.

    Parameters
    ----------
    func : Callable
        The blocking function to execute.
    *args
        Positional arguments to pass to ``func``.
    **kwargs
        Keyword arguments to pass to ``func``.

    Returns
    -------
    Any
        The result returned by ``func``.

    Example
    -------
    >>> import asyncio
    >>> async def main():
    ...     result = await sync_to_async(sum, [1, 2, 3])
    ...     print(result)
    ...
    >>> asyncio.run(main())
    6
    """
    return await asyncio.shield(
        asyncio.create_task(asyncio.to_thread(func, *args, **kwargs))
    )


__all__ = [
    # Event emitter
    "StreamAsyncIOEventEmitter",
    # Utils functions
    "encode_datetime",
    "datetime_from_unix_ns",
    "build_query_param",
    "build_body_dict",
    "validate_and_clean_url",
    "configure_logging",
    "UTC",
    # async
    "sync_to_async",
]
