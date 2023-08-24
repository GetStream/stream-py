from ast import Dict
from datetime import datetime, timezone
from typing import Any, Optional, TypeVar, Generic

import httpx

from getstream.rate_limit import RateLimitInfo

T = TypeVar("T")


class StreamResponse(Generic[T]):
    """
    A custom dictionary where you can access the response data the same way
    as a normal dictionary. Additionally, we expose some methods to access other metadata.
    """

    def __init__(self, response: httpx.Response, data: T) -> None:
        self.__headers = response.headers
        self.__status_code = response.status_code
        self.__rate_limit: Optional[RateLimitInfo] = None
        limit, remaining, reset = (
            response.headers.get("x-ratelimit-limit"),
            response.headers.get("x-ratelimit-remaining"),
            response.headers.get("x-ratelimit-reset"),
        )

        if limit and remaining and reset:
            self.__rate_limit = RateLimitInfo(
                limit=int(self._clean_header(limit)),
                remaining=int(self._clean_header(remaining)),
                reset=datetime.fromtimestamp(
                    float(self._clean_header(reset)), timezone.utc
                ),
            )

        self.__data: T = data
        super(StreamResponse, self).__init__(response)

    def data(self) -> T:
        """Returns the encapsulated data of provided type."""
        return self.__data

    def _clean_header(self, header: str) -> int:
        try:
            values = (v.strip() for v in header.split(","))
            return int(next(v for v in values if v))
        except ValueError:
            return 0

    def rate_limit(self) -> Optional[RateLimitInfo]:
        """Returns the ratelimit info of your API operation."""
        return self.__rate_limit

    def headers(self) -> Dict[str, Any]:
        """Returns the headers of the response."""
        return self.__headers

    def status_code(self) -> int:
        """Returns the HTTP status code of the response."""
        return self.__status_code
