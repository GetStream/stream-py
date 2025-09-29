from getstream.video.async_rest_client import VideoRestClient
from getstream.video.async_call import Call


class VideoClient(VideoRestClient):
    def __init__(self, api_key: str, base_url, token, timeout, stream):
        """
        Initializes VideoClient with BaseClient instance
        :param api_key: A string representing the client's API key
        :param base_url: A string representing the base uniform resource locator
        :param token: A string instance representing the client's token
        :param timeout: A number representing the time limit for a request
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            token=token,
            timeout=timeout,
        )
        self.stream = stream

    def call(self, call_type: str, id: str) -> Call:
        return Call(self, call_type, id)
