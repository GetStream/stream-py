import logging
import os
from typing import Iterator

import pytest

from getstream import _rust


@pytest.fixture
def rust_client() -> _rust.Client:
    return _rust.Client(os.environ["STREAM_API_KEY"], os.environ["STREAM_API_SECRET"])


@pytest.fixture
def sdk_logs(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    caplog.set_level(logging.DEBUG, logger="getstream")
    logger = logging.getLogger("getstream")
    _rust.configure_logging(logger, logger.getEffectiveLevel())
    yield caplog
    _rust.configure_logging(None, logging.NOTSET)
