import json
from typing import Dict, List, Optional, Union
from urllib.parse import quote
from datetime import datetime
from datetime import timezone
from urllib.parse import urlparse, urlunparse

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
