from datetime import datetime, timezone

import httpx
import pytest

from getstream.exceptions import StreamRateLimitException, build_api_exception
from getstream.stream_response import StreamResponse


INVALID_HEADERS = [
    ("x-ratelimit-limit", " , , "),
    ("x-ratelimit-remaining", " , , "),
    ("x-ratelimit-reset", " , , "),
    ("x-ratelimit-reset", "inf"),
    ("x-ratelimit-reset", "-inf"),
    ("x-ratelimit-reset", "1e100"),
    ("x-ratelimit-reset", "not-a-timestamp"),
]


class TestInvalidRateLimitHeaders:
    @pytest.mark.parametrize("header,value", INVALID_HEADERS)
    @pytest.mark.parametrize("status", [200, 429])
    def test_invalid_metadata_does_not_hide_response(self, header, value, status):
        headers = {
            "x-ratelimit-limit": "100",
            "x-ratelimit-remaining": "80",
            "x-ratelimit-reset": "1640995200",
            "Retry-After": "5",
            header: value,
        }
        response = httpx.Response(
            status,
            headers=headers,
            json={
                "code": 9,
                "duration": "0ms",
                "message": "too many requests",
                "more_info": "",
                "StatusCode": status,
                "details": [],
                "unrecoverable": False,
            },
        )
        if status == 200:
            result = StreamResponse(response, {"ok": True})
            assert result.status_code() == 200
            assert result.data == {"ok": True}
            assert result.rate_limit() is None
        else:
            error = build_api_exception(response)
            assert isinstance(error, StreamRateLimitException)
            assert error.status_code == 429
            assert error.rate_limit_info is None
            assert error.retry_after.total_seconds() == 5

    @pytest.mark.parametrize("prefix", ["", " , "])
    def test_first_nonempty_value_still_parses(self, prefix):
        response = httpx.Response(
            200,
            headers={
                "x-ratelimit-limit": prefix + "100, 200",
                "x-ratelimit-remaining": prefix + "80, 90",
                "x-ratelimit-reset": prefix + "1640995200, 1640995300",
            },
        )
        result = StreamResponse(response, {})
        info = result.rate_limit()
        assert info.limit == 100
        assert info.remaining == 80
        assert info.reset == datetime(2022, 1, 1, tzinfo=timezone.utc)
