import logging
import os
from typing import Iterator

import getstream_rtc
import pytest


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
