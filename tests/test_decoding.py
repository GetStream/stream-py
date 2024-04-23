from dataclasses import dataclass, field
from datetime import datetime

from getstream.models import OwnCapability
from getstream.utils import encode_query_param, datetime_from_unix_ns, request_to_dict
from dataclasses_json import DataClassJsonMixin, config

def test_primitive_string():
    assert encode_query_param("hello") == "hello"


def test_primitive_int():
    assert encode_query_param(123) == "123"


def test_primitive_bool():
    assert encode_query_param(True) == "True"
    assert encode_query_param(False) == "False"


def test_none_type():
    assert encode_query_param(None) == "None"


def test_list_of_ints():
    assert encode_query_param([1, 2, 3]) == "1,2,3"


def test_list_with_strings():
    assert encode_query_param(["apple", "banana", "cherry, tart"]) == "apple,banana,cherry%2C%20tart"


def test_list_with_mixed_types():
    assert encode_query_param([1, "hello, world", True]) == "1,hello%2C%20world,True"


def test_dictionary():
    assert encode_query_param({"a": 1, "b": "yes, no"}) == '{"a": 1, "b": "yes, no"}'


def test_datetime_from_valid_unix_ns():
    # Example timestamp: January 1, 2020, 00:00:00 UTC in nanoseconds
    timestamp_ns = 1577836800000000000
    expected_datetime = datetime(2020, 1, 1, 0, 0)
    assert datetime_from_unix_ns(timestamp_ns) == expected_datetime


def test_datetime_from_none():
    assert datetime_from_unix_ns(None) is None


def test_datetime_precision():
    # Timestamp with more precision: January 1, 2020, 00:00:00.123456789 UTC
    timestamp_ns = 1577836800123456789
    expected_datetime = datetime(2020, 1, 1, 0, 0, 0, 123457)
    result_datetime = datetime_from_unix_ns(timestamp_ns)
    # Testing up to microseconds precision because Python's datetime only supports microseconds
    assert result_datetime == expected_datetime


def test_negative_timestamp():
    # Negative timestamp: Before January 1, 1970, e.g., December 31, 1969, 23:59:59 UTC
    timestamp_ns = -1000000000
    expected_datetime = datetime(1969, 12, 31, 23, 59, 59)
    assert datetime_from_unix_ns(timestamp_ns) == expected_datetime


def test_future_timestamp():
    # Future timestamp: January 1, 2100, 00:00:00 UTC
    timestamp_ns = 4102444800000000000
    expected_datetime = datetime(2100, 1, 1, 0, 0)
    assert datetime_from_unix_ns(timestamp_ns) == expected_datetime


# Helper class to test the conversion of objects with to_dict method
class MockObjectWithToDict:
    def to_dict(self):
        return {'key': 'value'}


# Tests using pytest
def test_request_to_dict_with_none():
    assert request_to_dict(None) == {}


def test_request_to_dict_with_dict():
    input_dict = {'a': 1, 'b': 2}
    assert request_to_dict(input_dict) == input_dict


def test_request_to_dict_with_object_having_to_dict():
    obj = MockObjectWithToDict()
    assert request_to_dict(obj) == {'key': 'value'}


def test_request_to_dict_with_primitive_type():
    assert request_to_dict(123) == 123
    assert request_to_dict("test string") == "test string"


def test_request_to_dict_with_list():
    input_list = [1, 2, 3]
    assert request_to_dict(input_list) == input_list


@dataclass
class TestRequest(DataClassJsonMixin):
    own_capabilities: 'List[OwnCapability]' = field(metadata=config(field_name="own_capabilities"))
def test_encode_own_capability():
    obj = TestRequest(own_capabilities=[OwnCapability.BLOCK_USERS, "custom-value"])
    assert request_to_dict(obj) == {'own_capabilities': ['block-users', "custom-value"]}
