import os

import pytest
from getstream import Stream

STREAM_BASE_URL = os.environ.get("STREAM_BASE_URL")
STREAM_API_KEY = os.environ.get("STREAM_API_KEY")
STREAM_API_SECRET = os.environ.get("STREAM_API_SECRET")
TIMEOUT = 6


@pytest.fixture
def client():
    return Stream(
        api_key=STREAM_API_KEY,
        api_secret=STREAM_API_SECRET,
        timeout=TIMEOUT,
        base_url=STREAM_BASE_URL,
    )
