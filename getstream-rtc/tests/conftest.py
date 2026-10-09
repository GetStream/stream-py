import logging
import os
import uuid
from typing import Iterator

import getstream_rtc
import pytest
from dotenv import load_dotenv

from getstream import Stream
from getstream.models import FullUserResponse, UserRequest


@pytest.fixture(scope="session", autouse=True)
def load_env() -> None:
    load_dotenv()


@pytest.fixture
def client() -> Stream:
    return Stream(timeout=10.0)


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


@pytest.fixture(autouse=True)
def forward_sdk_logs() -> Iterator[None]:
    logger = logging.getLogger("getstream")
    getstream_rtc.configure_logging(logger, logger.getEffectiveLevel())
    yield
    getstream_rtc.configure_logging(None, logging.NOTSET)


@pytest.fixture
def rust_client() -> getstream_rtc.Client:
    return getstream_rtc.Client(
        os.environ["STREAM_API_KEY"], os.environ["STREAM_API_SECRET"]
    )


@pytest.fixture
def sdk_logs(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    caplog.set_level(logging.DEBUG, logger="getstream")
    logger = logging.getLogger("getstream")
    getstream_rtc.configure_logging(logger, logger.getEffectiveLevel())
    yield caplog
    getstream_rtc.configure_logging(None, logging.NOTSET)
