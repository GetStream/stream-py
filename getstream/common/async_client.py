from getstream.common.async_rest_client import CommonRestClient


class CommonClient(CommonRestClient):
    def __init__(self, api_key: str, base_url, token, timeout):
        super().__init__(
            api_key=api_key, base_url=base_url, token=token, timeout=timeout
        )
