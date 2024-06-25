import pytest
from click.testing import CliRunner
from getstream import cli as stream_cli

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
