from typing import Any, Optional, Generic
import typing

import httpx

from getstream.rate_limit import RateLimitInfo, extract_rate_limit
from getstream.generic import T


class StreamResponse(Generic[T]):
    """
    A custom dictionary where you can access the response data the same way
    as a normal dictionary. Additionally, we expose some methods to access other metadata.
    """

    def __init__(self, response: httpx.Response, data: T) -> None:
        self.__headers = response.headers
        self.__status_code = response.status_code
        self.__rate_limit = extract_rate_limit(response)

        self.__data: T = data
        super(StreamResponse, self).__init__()

    def data(self) -> T:
        """Returns the encapsulated data of provided type."""
        return self.__data

    def rate_limit(self) -> Optional[RateLimitInfo]:
        """Returns the ratelimit info of your API operation."""
        return self.__rate_limit

    def headers(self) -> typing.Dict[str, Any]:
        """Returns the headers of the response."""
        return self.__headers

    def status_code(self) -> int:
        """Returns the HTTP status code of the response."""
        return self.__status_code
