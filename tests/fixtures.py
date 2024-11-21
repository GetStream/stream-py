import os
import uuid
from typing import Dict
from click.testing import CliRunner
import pytest

from getstream import Stream
from getstream.models import UserRequest, FullUserResponse


def mock_setup(mocker):
    mock_stream = mocker.Mock()
    mock_video_client = mocker.Mock()
    mock_call = mocker.Mock()
    mock_stream.video = mock_video_client
    mock_video_client.call.return_value = mock_call
    mocker.patch("getstream.cli.Stream", return_value=mock_stream)
    return mock_stream, mock_video_client, mock_call


@pytest.fixture
def cli_runner():
    """
    Fixture to create a CliRunner instance.

    Returns:
        CliRunner: An instance of CliRunner for invoking CLI commands in tests.
    """
    return CliRunner()


def _client():
    return Stream(
        api_key=os.environ.get("STREAM_API_KEY"),
        api_secret=os.environ.get("STREAM_API_SECRET"),
        base_url=os.environ.get("STREAM_BASE_URL"),
    )


@pytest.fixture
def client():
    return _client()


@pytest.fixture
def call(client: Stream):
    return client.video.call("default", str(uuid.uuid4()))


@pytest.fixture(scope="class")
def shared_call(request):
    """
    Use this fixture to decorate test classes subclassing base.VideoTestClass

    """
    request.cls.client = _client()
    request.cls.call = request.cls.client.video.call("default", str(uuid.uuid4()))


@pytest.fixture
def get_user(client: Stream):
    def inner(
        name: str = None, image: str = None, custom: Dict[str, object] = None
    ) -> FullUserResponse:
        id = str(uuid.uuid4())
        return client.upsert_users(
            UserRequest(
                id=id,
                name=name,
                image=image,
                custom=custom,
            ),
        ).data.users[id]

    return inner
