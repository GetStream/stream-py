
import os
import pytest
from getstream import Stream

VIDEO_API_KEY = os.environ.get("VIDEO_API_KEY")
BASE_URL = "https://video.stream-io-api.com/video"
VIDEO_API_SECRET = os.environ.get("VIDEO_API_SECRET")
TIMEOUT = 6

@pytest.fixture(scope="module")
def client():
    return Stream(
    api_key=VIDEO_API_KEY,
    api_secret=VIDEO_API_SECRET,
    timeout=TIMEOUT,
    video_base_url=BASE_URL,
    )

def test_video_client_initialization(client):
    assert client.api_key == VIDEO_API_KEY
    assert client.video_base_url == BASE_URL
    assert client.timeout == TIMEOUT