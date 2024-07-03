from click.testing import CliRunner
import inspect
from getstream import cli as stream_cli
import pytest
from typing import Optional, List, Dict, Union
from getstream.models import CallRequest, CallSettingsRequest
from getstream.cli.utils import get_type_name, parse_complex_type, add_option_from_arg
import click
import json


def test_create_token(mocker):
    # Mock the Stream client
    mock_stream = mocker.Mock()
    mock_stream.create_call_token.return_value = "mocked_token"

    # Mock the Stream class to return our mocked client
    mocker.patch('getstream.cli.Stream', return_value=mock_stream)

    runner = CliRunner()
    result = runner.invoke(stream_cli.cli, ["create-token", "--user-id", "your_user_id"])

    # Print debug information
    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.output}")
    print(f"Exception: {result.exception}")

    # Assertions
    assert result.exit_code == 0
    assert "mocked_token" in result.output
    mock_stream.create_call_token.assert_called_once_with(user_id='your_user_id')

def test_get_type_name():
    assert get_type_name(str) == 'str'
    assert get_type_name(int) == 'int'
    assert get_type_name(bool) == 'bool'
    assert get_type_name(List[str]) == 'list[str]'
    assert get_type_name(Dict[str, int]) == 'dict[str, int]'
    assert get_type_name(Optional[str]) == 'union[str, NoneType]'
    assert get_type_name(Union[str, int]) == 'union[str, int]'

def test_parse_complex_type():
    # Test parsing a simple dict
    assert parse_complex_type('{"key": "value"}', dict) == {"key": "value"}

    class MockComplex:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    complex_json = '{"created_by_id": "user123", "custom": {"key": "value"}}'
    parsed_complex = parse_complex_type(complex_json, MockComplex)
    assert isinstance(parsed_complex, MockComplex)
    assert parsed_complex.created_by_id == "user123"
    assert parsed_complex.custom == {"key": "value"}

    # Test invalid JSON
    with pytest.raises(click.BadParameter):
        parse_complex_type('invalid json', dict)

# Tests for add_option
def test_add_option():
    # Create a dummy command
    @click.command()
    def dummy_cmd():
        pass

    # Test adding a string option
    cmd = add_option_from_arg(dummy_cmd, 'string_param', inspect.Parameter('string_param', inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=str))
    assert any(option.name == 'string_param' for option in cmd.params)
    assert cmd.params[-1].type == click.STRING

    # Test adding an int option
    cmd = add_option_from_arg(dummy_cmd, 'int_param', inspect.Parameter('int_param', inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=int))
    assert any(option.name == 'int_param' for option in cmd.params)
    assert cmd.params[-1].type == click.INT

    # Test adding a bool option
    cmd = add_option_from_arg(dummy_cmd, 'bool_param', inspect.Parameter('bool_param', inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=bool))
    assert any(option.name == 'bool_param' for option in cmd.params)
    assert cmd.params[-1].is_flag

    # Test adding a list option
    cmd = add_option_from_arg(dummy_cmd, 'list_param', inspect.Parameter('list_param', inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=List[str]))
    assert any(option.name == 'list_param' for option in cmd.params)
    assert cmd.params[-1].multiple

    # Test adding a complex option
    cmd = add_option_from_arg(dummy_cmd, 'complex_param', inspect.Parameter('complex_param', inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=CallRequest))
    assert any(option.name == 'complex_param' for option in cmd.params)
    # Check if it's using json_option (this might need to be adjusted based on how you've implemented json_option)
    assert cmd.params[-1].type == click.STRING  # Assuming json_option uses STRING type


def test_video_call_get_or_create(mocker):
    # Mock the Stream client
    mock_stream = mocker.Mock()
    mock_video_client = mocker.Mock()
    mock_call = mocker.Mock()
    mock_stream.video = mock_video_client
    mock_video_client.call.return_value = mock_call

    # Mock the get-or-create method
    mock_response = mocker.Mock()
    mock_response.data.to_dict.return_value = {
        "call": {
            "cid": "default:18632",
            "created_at": "2023-07-03T12:00:00Z",
            "updated_at": "2023-07-03T12:00:00Z",
            "members_limit": 10,
            # Add other expected fields here
        }
    }
    mock_call.get_or_create.return_value = mock_response

    # Mock the json.dumps function to return a predictable string
    mocker.patch('json.dumps', return_value='{"cid": "default:18632", "members_limit": 10, "mocked": "json"}')

    # Mock the Stream class to return our mocked client
    mocker.patch('getstream.cli.Stream', return_value=mock_stream)

    # Prepare test data
    json_data = '{"created_by_id": "user123", "custom": {"key": "value"}}'

    runner = CliRunner()
    result = runner.invoke(stream_cli.cli, [
        "video", "call", "get-or-create",
        "--call-type", "default",
        "--call-id", "18632",
        "--members_limit", "10",
        "--data", json_data
    ])

    # Print debug information
    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.output}")
    print(f"Exception: {result.exception}")

    # Assertions
    assert result.exit_code == 0
    assert '"cid": "default:18632"' in result.output
    assert '"members_limit": 10' in result.output
    assert '"mocked": "json"' in result.output

    # Verify the mocked method was called with correct arguments
    mock_video_client.call.assert_called_once_with("default", "18632")
    mock_call.get_or_create.assert_called_once()
    call_args = mock_call.get_or_create.call_args[1]
    assert call_args["members_limit"] == 10
    assert isinstance(call_args["data"], dict)
    assert call_args["data"]["created_by_id"] == "user123"
    assert call_args["data"]["custom"] == {"key": "value"}
