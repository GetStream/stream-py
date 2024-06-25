import pytest
from click.testing import CliRunner
from getstream import Stream
from getstream.cli import cli

@pytest.fixture
def mock_stream(mocker):
    mock = mocker.Mock(spec=Stream)
    mocker.patch('cli.Stream', return_value=mock)
    return mock

def test_create_token(mock_stream):
    runner = CliRunner()
    result = runner.invoke(cli, ['create-token', '--user-id', 'test_user'])
    assert result.exit_code == 0
    mock_stream.create_call_token.assert_called_once_with(user_id='test_user')

def test_video_get_call(mock_stream):
    runner = CliRunner()
    result = runner.invoke(cli, ['video', 'get-call', '--call-id', 'test_call'])
    assert result.exit_code == 0
    mock_stream.video.call.assert_called_once_with('test_call')
    mock_stream.video.call().get.assert_called_once()

def test_rtmp_in_setup(mock_stream):
    runner = CliRunner()
    result = runner.invoke(cli, ['video', 'rtmp-in-setup'])
    assert result.exit_code == 0
    mock_stream.video.call.assert_called_once()
    mock_stream.video.call().get_or_create.assert_called_once()

def test_json_input(mock_stream):
    runner = CliRunner()
    result = runner.invoke(cli, ['video', 'get-or-create-call',
                                 '--call-type', 'default',
                                 '--call-id', 'test_call',
                                 '--data', '{"created_by_id": "test_user", "custom": {"color": "red"}}'])
    assert result.exit_code == 0
    mock_stream.video.call.assert_called_once_with('default', 'test_call')
    mock_stream.video.call().get_or_create.assert_called_once()
