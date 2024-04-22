import json
from urllib.parse import quote
from datetime import datetime


def datetime_from_unix_ns(ts):
    """
    Converts a unix timestamp to a datetime object
    :param ts: nanoseconds since epoch
    :return: datetime object
    """
    if ts is None:
        return None
    return datetime.utcfromtimestamp(ts / 1e9)

def encode_query_param(value):
    """
    Encodes a value into a string suitable for use as a URL query parameter.

    Args:
        value: The value to encode, which can be a primitive, list, or dictionary.

    Returns:
        A string representation of the value, encoded according to its type:
        - primitive types are directly converted to strings,
        - lists of ints and strings are encoded as comma-separated values,
          with commas within strings being URI-escaped,
        - dictionaries and other objects are encoded using JSON.
    """
    if hasattr(value, 'to_json') and callable(value.to_json):
        return value.to_json()
    if isinstance(value, (str, int, bool, type(None))):
        return str(value)
    elif isinstance(value, list):
        # Process each element, escaping commas in the string representation
        return ','.join(quote(str(v)) for v in value)
    else:
        # For dictionaries or any other types of objects
        return json.dumps(value)


def request_to_dict(value):
    """
    Converts a request value to a dictionary.
    Args:
    value: The input value which could be None, a dictionary, or an object with a to_dict() method.

    Returns:
    A dictionary representation of the input, or the input itself if it does not meet conversion criteria.
    """
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, 'to_dict') and callable(value.to_dict):
        return value.to_dict()
    return value
