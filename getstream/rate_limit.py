from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
import httpx


@dataclass(frozen=True)
class RateLimitInfo:
    limit: int
    remaining: int
    reset: datetime


def extract_rate_limit(response: httpx.Response) -> Optional[RateLimitInfo]:
    def get_first_nonempty_value(header: str) -> Any:
        return next(v.strip() for v in header.split(",") if v.strip())

    limit, remaining, reset = (
        response.headers.get("x-ratelimit-limit"),
        response.headers.get("x-ratelimit-remaining"),
        response.headers.get("x-ratelimit-reset"),
    )

    if limit and remaining and reset:
        try:
            limit_value = int(get_first_nonempty_value(limit))
            remaining_value = int(get_first_nonempty_value(remaining))
            reset_value = datetime.fromtimestamp(
                float(get_first_nonempty_value(reset)), timezone.utc
            )
            return RateLimitInfo(
                limit=limit_value,
                remaining=remaining_value,
                reset=reset_value,
            )
        except ValueError:
            return None
    return None
