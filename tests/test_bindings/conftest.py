import logging
import os
import uuid
from typing import Iterator

import pytest

from getstream import Stream, _rust
from getstream.models import FullUserResponse, UserRequest


@pytest.fixture
def rust_client() -> _rust.Client:
    return _rust.Client(os.environ["STREAM_API_KEY"], os.environ["STREAM_API_SECRET"])


@pytest.fixture(scope="session")
def call_users() -> Iterator[list[FullUserResponse]]:
    client = Stream(timeout=10.0)
    user_ids = [str(uuid.uuid4()) for _ in range(2)]
    response = client.update_users(
        users={user_id: UserRequest(id=user_id, name=user_id) for user_id in user_ids}
    )
    yield [response.data.users[user_id] for user_id in user_ids]
    client.delete_users(
        user_ids=user_ids, user="hard", conversations="hard", messages="hard"
    )


@pytest.fixture
def sdk_logs(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    caplog.set_level(logging.DEBUG, logger="getstream")
    logger = logging.getLogger("getstream")
    _rust.configure_logging(logger, logger.getEffectiveLevel())
    yield caplog
    _rust.configure_logging(None, logging.NOTSET)
