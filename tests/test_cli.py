import inspect
from getstream import cli as stream_cli
import pytest
from typing import Optional, List, Dict, Union
from getstream.models import CallRequest, CallSettingsRequest
from getstream.cli.utils import get_type_name, parse_complex_type, add_option_from_arg
import click
import json
from tests.fixtures import mock_setup, cli_runner


def test_create_token(mocker,cli_runner):
    # Mock the Stream client
    mock_stream = mocker.Mock()
    mock_stream.create_call_token.return_value = "mocked_token"

    # Mock the Stream class to return our mocked client
    mocker.patch('getstream.cli.Stream', return_value=mock_stream)

    result = cli_runner.invoke(stream_cli.cli, ["create-token", "--user-id", "your_user_id"])

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

    # Test parsing a string
    assert parse_complex_type('simple string', str) == 'simple string'

    # Test parsing an integer
    assert parse_complex_type('42', int) == 42

    class MockComplex:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    # Test parsing a complex object
    complex_json = '{"created_by_id": "user123", "custom": {"key": "value"}}'
    parsed_complex = parse_complex_type(complex_json, MockComplex)
    assert isinstance(parsed_complex, MockComplex)
    assert parsed_complex.created_by_id == "user123"
    assert parsed_complex.custom == {"key": "value"}

    # Test invalid JSON for dict annotation
    with pytest.raises(click.BadParameter):
        parse_complex_type('invalid json', dict)

    # Test invalid JSON for list annotation
    with pytest.raises(click.BadParameter):
        parse_complex_type('invalid json', list)

    # Test invalid JSON for string annotation (should not raise an error)
    assert parse_complex_type('invalid json', str) == 'invalid json'

    # Test None value
    assert parse_complex_type(None, dict) is None

    # Test non-string, non-None value
    assert parse_complex_type(42, int) == 42

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

def test_video_call_get_or_create(mocker, cli_runner):
    mock_stream, mock_video_client, mock_call = mock_setup(mocker)

    # Mock the get_or_create method
    mock_response = mocker.Mock()
    mock_response.data.to_dict.return_value = {
        "call": {
            "cid": "default:123456",
            "created_at": "2023-07-03T12:00:00Z",
            "updated_at": "2023-07-03T12:00:00Z",
            "members_limit": 10,
        }
    }
    mock_call.get_or_create.return_value = mock_response

    # Mock the json.dumps function to return a predictable string
    mocker.patch('json.dumps', return_value='{"cid": "default:123456", "members_limit": 10, "mocked": "json"}')

    result = cli_runner.invoke(stream_cli.cli, [
        "video", "call", "get-or-create",
        "--call-type", "default",
        "--call-id", "123456",
        "--data", '{"created_by_id": "user-id", "members_limit": 10}'
    ])

    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.output}")
    print(f"Exception: {result.exception}")

    assert result.exit_code == 0
    assert '"cid": "default:123456"' in result.output
    assert '"members_limit": 10' in result.output
    assert '"mocked": "json"' in result.output

    mock_video_client.call.assert_called_once_with("default", "123456")
    mock_call.get_or_create.assert_called_once()
    call_args = mock_call.get_or_create.call_args[1]
    assert 'data' in call_args
    assert call_args['data']['created_by_id'] == "user-id"
    assert call_args['data']['members_limit'] == 10


def test_cli_create_call_with_members(mocker, cli_runner):
    mock_stream, mock_video_client, mock_call = mock_setup(mocker)

    result = cli_runner.invoke(stream_cli.cli, [
        "video", "call", "get-or-create",
        "--call-type", "default",
        "--call-id", "123456",
        "--data", '{"created_by_id": "tommaso-id", "members": [{"user_id": "thierry-id"}, {"user_id": "tommaso-id"}]}'
    ])

    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.output}")
    print(f"Exception: {result.exception}")

    assert result.exit_code == 0
    mock_video_client.call.assert_called_once_with("default", "123456")
    mock_call.get_or_create.assert_called_once()
    call_args = mock_call.get_or_create.call_args[1]
    assert 'data' in call_args
    assert call_args['data']['created_by_id'] == "tommaso-id"
    assert len(call_args['data']['members']) == 2
    assert call_args['data']['members'][0]['user_id'] == "thierry-id"
    assert call_args['data']['members'][1]['user_id'] == "tommaso-id"

def test_cli_mute_all(mocker, cli_runner):
    mock_stream, mock_video_client, mock_call = mock_setup(mocker)

    result = cli_runner.invoke(stream_cli.cli, [
        "video", "call", "mute-users",
        "--call-type", "default",
        "--call-id", "123456",
        "--muted_by_id", "user-id",
        "--mute_all_users", "true",
        "--audio", "true",
    ])

    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.output}")
    print(f"Exception: {result.exception}")

    assert result.exit_code == 0
    mock_video_client.call.assert_called_once_with("default", "123456")
    mock_call.mute_users.assert_called_once_with(
        muted_by_id="user-id",
        mute_all_users=True,
        audio=True,
        screenshare=None,
        screenshare_audio=None,
        video=None,
        user_ids=None,
        muted_by=None
    )

def test_cli_block_user_from_call(mocker,cli_runner):
    """
    poetry run python -m getstream.cli video call block-user --call-type default --call-id 123456 --user_id bad-user-id
    """
    mock_setup(mocker)
    result = cli_runner.invoke(stream_cli.cli, [
        "video", "call", "block-user",
        "--call-type", "default",
        "--call-id", "123456",
        "--user_id", "bad-user-id"
    ])
    assert result.exit_code == 0

def test_cli_unblock_user_from_call(mocker,cli_runner):
    """
    poetry run python -m getstream.cli video call unblock-user --call-type default --call-id 123456 --user_id bad-user-id
    """
    mock_setup(mocker)
    result = cli_runner.invoke(stream_cli.cli, [
        "video", "call", "unblock-user",
        "--call-type", "default",
        "--call-id", "123456",
        "--user_id", "bad-user-id"
    ])
    assert result.exit_code == 0

def test_cli_send_custom_event(mocker,cli_runner):
    """
    poetry run python -m getstream.cli video call send-event --call-type default --call-id 123456 --user_id user-id --custom '{"bananas": "good"}'
    """
    mock_setup(mocker)
    result = cli_runner.invoke(stream_cli.cli, [
        "video", "call", "send-event",
        "--call-type", "default",
        "--call-id", "123456",
        "--user_id", "user-id",
        "--custom", '{"bananas": "good"}'
    ])
    assert result.exit_code == 0

def test_cli_update_settings(mocker,cli_runner):
    """
    poetry run python -m getstream.cli video call update --call-type default --call-id 123456 --settings_override '{"screensharing": {"enabled": true, "access_request_enabled": true}}'
    """
    mock_setup(mocker)
    result = cli_runner.invoke(stream_cli.cli, [
        "video", "call", "update",
        "--call-type", "default",
        "--call-id", "123456",
        "--settings_override", '{"screensharing": {"enabled": true, "access_request_enabled": true}}'
    ])
    assert result.exit_code == 0