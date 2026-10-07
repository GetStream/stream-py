import uuid
from typing import AsyncIterator

import getstream_rtc
import pytest

from getstream import Stream
from getstream.models import FullUserResponse


@pytest.fixture
async def joined_call(
    client: Stream, call_users: list[FullUserResponse]
) -> AsyncIterator[getstream_rtc.Call]:
    """A new call that the first call user has joined through the bindings."""
    call = getstream_rtc.Client(client.api_key, client.api_secret).call(
        "default", str(uuid.uuid4())
    )
    await call.join(call_users[0].id)
    yield call
    await call.leave()
