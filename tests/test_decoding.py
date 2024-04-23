from dataclasses import dataclass, field
from datetime import datetime, timezone, UTC

from getstream.models import OwnCapability
from getstream.utils import (
    datetime_from_unix_ns,
    encode_datetime,
    build_query_param,
    build_body_dict,
)
from dataclasses_json import DataClassJsonMixin, config


class MockJsonSerializable:
    def to_json(self):
        return '{"type": "Mock"}'


def test_build_query_param_with_various_types():
    mock_obj = MockJsonSerializable()
    params = build_query_param(
        num=123,
        text="hello",
        flag=True,
        none_value=None,
        list_val=[1, 2, "three, maybe"],
        obj=mock_obj,
        dict_val={"a": 1, "b": "two"},
    )
    assert params == {
        "num": "123",
        "text": "hello",
        "flag": "true",
        "list_val": "1,2,three%2C%20maybe",
        "obj": '{"type": "Mock"}',
        "dict_val": '{"a": 1, "b": "two"}',
    }


def test_build_query_param_with_none():
    assert build_query_param(value=None) == {}


def test_build_query_param_with_empty():
    assert build_query_param() == {}


def test_build_query_param_with_booleans():
    params = build_query_param(true_val=True, false_val=False)
    assert params["true_val"] == "true"
    assert params["false_val"] == "false"


def test_datetime_from_valid_unix_ns():
    # Example timestamp: January 1, 2020, 00:00:00 UTC in nanoseconds
    timestamp_ns = 1577836800000000000
    expected_datetime = datetime(2020, 1, 1, 0, 0, tzinfo=UTC)
    assert datetime_from_unix_ns(timestamp_ns) == expected_datetime


def test_datetime_from_none():
    assert datetime_from_unix_ns(None) is None


def test_datetime_precision():
    # Timestamp with more precision: January 1, 2020, 00:00:00.123456789 UTC
    timestamp_ns = 1577836800123456789
    expected_datetime = datetime(2020, 1, 1, 0, 0, 0, 123457, tzinfo=UTC)
    result_datetime = datetime_from_unix_ns(timestamp_ns)
    # Testing up to microseconds precision because Python's datetime only supports microseconds
    assert result_datetime == expected_datetime


def test_negative_timestamp():
    # Negative timestamp: Before January 1, 1970, e.g., December 31, 1969, 23:59:59 UTC
    timestamp_ns = -1000000000
    expected_datetime = datetime(1969, 12, 31, 23, 59, 59, tzinfo=UTC)
    assert datetime_from_unix_ns(timestamp_ns) == expected_datetime


def test_future_timestamp():
    # Future timestamp: January 1, 2100, 00:00:00 UTC
    timestamp_ns = 4102444800000000000
    expected_datetime = datetime(2100, 1, 1, 0, 0, tzinfo=UTC)
    assert datetime_from_unix_ns(timestamp_ns) == expected_datetime


class MockObjectWithToDict:
    def to_dict(self):
        return {"type": "Mock", "valid": True}


def test_with_to_dict_method():
    obj = MockObjectWithToDict()
    result = build_body_dict(obj=obj)
    expected = {"obj": {"type": "Mock", "valid": True}}
    assert result == expected, "Failed to serialize object with to_dict method"


def test_with_nested_dictionaries():
    result = build_body_dict(
        info={"name": "John", "address": {"street": "123 Elm St", "city": "Somewhere"}}
    )
    expected = {
        "info": {
            "name": "John",
            "address": {"street": "123 Elm St", "city": "Somewhere"},
        }
    }
    assert result == expected, "Failed to handle nested dictionaries"


def test_with_lists_and_dicts():
    result = build_body_dict(data=[1, 2, {"num": 3}, [4, 5]])
    expected = {"data": [1, 2, {"num": 3}, [4, 5]]}
    assert (
        result == expected
    ), "Failed to handle lists containing dictionaries and other lists"


def test_empty_input():
    result = build_body_dict()
    assert result == {}, "Failed to handle empty input correctly"


# Additional test for complex nested structures
def test_complex_nested_structures():
    result = build_body_dict(
        user={
            "id": 1,
            "profile": MockObjectWithToDict(),
            "history": [2010, 2012, {"year": 2014}],
        }
    )
    expected = {
        "user": {
            "id": 1,
            "profile": {"type": "Mock", "valid": True},
            "history": [2010, 2012, {"year": 2014}],
        }
    }
    assert result == expected, "Failed to handle complex nested structures"


def test_encode_datetime_with_none():
    assert encode_datetime(None) is None, "Should return None when input is None"


def test_encode_datetime_with_valid_datetime():
    date = datetime(2022, 1, 1, 15, 30, 45)
    expected = "2022-01-01T15:30:45"
    assert (
        encode_datetime(date) == expected
    ), f"Expected {expected}, got {encode_datetime(date)}"


def test_encode_datetime_with_timezone_aware_datetime():
    date = datetime(2022, 1, 1, 15, 30, 45, tzinfo=timezone.utc)
    expected = "2022-01-01T15:30:45+00:00"
    assert (
        encode_datetime(date) == expected
    ), f"Expected {expected}, got {encode_datetime(date)}"


@dataclass
class MockRequest(DataClassJsonMixin):
    own_capabilities: "List[OwnCapability]" = field(
        metadata=config(field_name="own_capabilities")
    )


def test_encode_own_capability():
    obj = MockRequest(own_capabilities=[OwnCapability.BLOCK_USERS, "custom-value"])
    assert build_body_dict(obj=obj) == {
        "obj": {"own_capabilities": ["block-users", "custom-value"]}
    }
