from getstream.moderation.rest_client import ModerationRestClient


class ModerationClient(ModerationRestClient):
    def __init__(self, api_key: str, base_url, token, timeout, stream, user_agent=None):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            token=token,
            timeout=timeout,
            user_agent=user_agent,
        )
        self.stream = stream
