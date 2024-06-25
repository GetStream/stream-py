from click.testing import CliRunner
import inspect
from getstream import cli as stream_cli
import pytest
from typing import Optional, List, Dict, Union
from getstream.models import CallRequest, CallSettingsRequest
from getstream.cli.utils import get_type_name, parse_complex_type, add_option_from_arg
import click

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




# Tests for get_type_name
def test_get_type_name():
    assert get_type_name(str) == 'str'
    assert get_type_name(int) == 'int'
    assert get_type_name(bool) == 'bool'
    # assert get_type_name(List[str]) == 'list[str]'
    # assert get_type_name(Dict[str, int]) == 'dict[str, int]'
    # assert get_type_name(Optional[str]) == 'str'
    # assert get_type_name(Union[str, int]) == 'Union[str, int]'
    assert get_type_name(CallRequest) == 'CallRequest'

# Tests for parse_complex_type
def test_parse_complex_type():
    # Test parsing a simple dict
    assert parse_complex_type('{"key": "value"}', dict) == {"key": "value"}

    # Test parsing a CallRequest
    call_request_json = '{"created_by_id": "user123", "custom": {"key": "value"}}'
    parsed_call_request = parse_complex_type(call_request_json, CallRequest)
    # assert isinstance(parsed_call_request, CallRequest)
    # assert parsed_call_request.created_by_id == "user123"
    # assert parsed_call_request.custom == {"key": "value"}

    # # Test parsing a CallSettingsRequest
    # settings_json = '{"audio": {"access_request_enabled": true}, "video": {"enabled": true}}'
    # parsed_settings = parse_complex_type(settings_json, CallSettingsRequest)
    # assert isinstance(parsed_settings, CallSettingsRequest)
    # assert parsed_settings.audio.access_request_enabled == True
    # assert parsed_settings.video.enabled == True

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
    # cmd = add_option_from_arg(dummy_cmd, 'list_param', inspect.Parameter('list_param', inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=List[str]))
    # assert any(option.name == 'list_param' for option in cmd.params)
    # assert cmd.params[-1].multiple

    # Test adding a complex option
    cmd = add_option_from_arg(dummy_cmd, 'complex_param', inspect.Parameter('complex_param', inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=CallRequest))
    assert any(option.name == 'complex_param' for option in cmd.params)
    # Check if it's using json_option (this might need to be adjusted based on how you've implemented json_option)
    assert cmd.params[-1].type == click.STRING  # Assuming json_option uses STRING type
