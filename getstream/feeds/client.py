from getstream.feeds.rest_client import FeedsRestClient
from getstream.feeds.feeds import Feed
from typing import Optional, Dict


class FeedsClient(FeedsRestClient):
    def __init__(self, api_key: str, base_url, token, timeout, stream):
        super().__init__(
            api_key=api_key, base_url=base_url, token=token, timeout=timeout
        )
        self.stream = stream

    def feed(
        self, feed_type: str, feed_id: str, custom_data: Optional[Dict] = None
    ) -> Feed:
        """
        Create a Feed instance for the given feed type and ID.

        :param feed_type: The type of feed (e.g., 'user', 'timeline')
        :param feed_id: The unique identifier for the feed
        :param custom_data: Optional custom data for the feed
        :return: Feed instance
        """
        return Feed(self, feed_type, feed_id, custom_data)
