import os
import uuid

import pytest
from getstream import Stream

CALL_TYPE = "default"
CALL_ID = str(uuid.uuid4())


@pytest.fixture
def client():
    return Stream(
        api_key=os.environ.get("STREAM_API_KEY"),
        api_secret=os.environ.get("STREAM_API_SECRET"),
        base_url=os.environ.get("STREAM_BASE_URL"),
    )


@pytest.fixture
def call(client: Stream):
    return client.video.call(CALL_TYPE, CALL_ID)
