from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import httpx


@dataclass(frozen=True)
class RateLimitInfo:
    limit: int
    remaining: int
    reset: datetime


def extract_rate_limit(response: httpx.Response) -> Optional[RateLimitInfo]:
    limit, remaining, reset = (
        response.headers.get("x-ratelimit-limit"),
        response.headers.get("x-ratelimit-remaining"),
        response.headers.get("x-ratelimit-reset"),
    )

    if limit and remaining and reset:
        try:
            values = (v.strip() for v in httpx.Headers.split(","))
            return RateLimitInfo(
                limit=int(next(v for v in values if v)),
                remaining=int(next(v for v in values if v)),
                reset=datetime.fromtimestamp(
                    float(next(v for v in values if v)), timezone.utc
                ),
            )
        except ValueError:
            return None
    return None
