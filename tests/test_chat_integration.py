import os

import pytest
from getstream.models.user_request import UserRequest
from getstream.sync.stream import Stream
from getstream.version import VERSION


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


def test_update_users(client: Stream):
    users = {}
    users["user1"] = UserRequest(
        id="user1", role="admin", custom={"premium": True}, name="user1"
    )

    client.users.update_users(users=users)
