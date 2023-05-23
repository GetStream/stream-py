
import os
import pytest

from getstream.video.sync.client import VideoClient


VIDEO_API_KEY = os.environ.get("VIDEO_API_KEY")
BASE_URL = "https://video.stream-io-api.com/video"
VIDEO_API_SECRET = os.environ.get("VIDEO_API_SECRET")
TIMEOUT = 6
USER_AGENT = "getstream-python-client"

@pytest.fixture(scope="module")
def client():
    return VideoClient(VIDEO_API_KEY, BASE_URL, TIMEOUT, USER_AGENT)

def test_video_client_initialization(client):
    assert client.api_key == VIDEO_API_KEY
    assert client.base_url == BASE_URL
    assert client.timeout == TIMEOUT
    assert client.user_agent == USER_AGENT