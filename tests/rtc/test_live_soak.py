"""Repeated join/leave RSS growth bound. Mirrors Rust tests/rtc_soak.rs."""

import asyncio
import gc
import os

import pytest

from getstream.video.rtc.connection_utils import ConnectionState
from tests.conftest import skip_on_rate_limit
from tests.rtc.live_support import live_call, process_rss_bytes, rtc, wait_for_state


pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.timeout(180)]

DEFAULT_ITERATIONS = 10
MAX_RSS_GROWTH_BYTES = 64 * 1024 * 1024


def _iterations() -> int:
    raw = os.environ.get("STREAM_SOAK_ITERATIONS")
    if not raw:
        return DEFAULT_ITERATIONS
    try:
        return max(1, min(int(raw), 100))
    except ValueError:
        return DEFAULT_ITERATIONS


class TestLiveSoak:
    @skip_on_rate_limit
    async def test_repeated_join_leave_has_bounded_rss_growth(self, live_call):
        call, users = live_call
        user_id = users[0]
        iterations = _iterations()

        async with await rtc.join(call, user_id) as connection:
            await wait_for_state(connection, ConnectionState.JOINED)
        await asyncio_sleep_gc()

        start_rss = process_rss_bytes()
        for iteration in range(1, iterations + 1):
            async with await rtc.join(call, user_id) as connection:
                await wait_for_state(connection, ConnectionState.JOINED)
            print(f"SOAK iteration {iteration}/{iterations} complete")

        await asyncio_sleep_gc()
        end_rss = process_rss_bytes()
        growth = max(0, end_rss - start_rss)
        print(
            f"SOAK_RESULT iterations={iterations} start_rss_bytes={start_rss} "
            f"end_rss_bytes={end_rss} growth_bytes={growth}"
        )
        assert growth <= MAX_RSS_GROWTH_BYTES, (
            f"RSS grew by {growth} bytes across {iterations} join/leave cycles"
        )


async def asyncio_sleep_gc() -> None:
    gc.collect()
    await asyncio.sleep(0.5)
    gc.collect()
