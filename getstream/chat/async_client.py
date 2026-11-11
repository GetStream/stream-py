from typing import List, Optional

from getstream.chat.async_channel import Channel
from getstream.chat.async_rest_client import ChatRestClient
from getstream.models import (
    ImageSize,
    OnlyUserID,
    UploadChannelResponse,
)
from getstream.stream_response import StreamResponse


class ChatClient(ChatRestClient):
    def __init__(self, api_key: str, base_url, token, timeout, stream, user_agent=None):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            token=token,
            timeout=timeout,
            user_agent=user_agent,
        )
        self.stream = stream

    def channel(self, call_type: str, id: str) -> Channel:
        return Channel(self, call_type, id)

    # Keeps the `channel_type` name this method has always taken; the generated one takes `type`.
    async def upload_channel_image(
        self,
        channel_type: Optional[str] = None,
        id: Optional[str] = None,
        file: Optional[str] = None,
        upload_sizes: Optional[List[ImageSize]] = None,
        user: Optional[OnlyUserID] = None,
        **kwargs,
    ) -> StreamResponse[UploadChannelResponse]:
        if channel_type is None:
            channel_type = kwargs.pop("type", None)
        if kwargs:
            raise TypeError(f"Unexpected keyword arguments: {', '.join(kwargs.keys())}")
        if channel_type is None:
            raise TypeError(
                "upload_channel_image() missing required argument: 'channel_type'"
            )
        if id is None:
            raise TypeError("upload_channel_image() missing required argument: 'id'")
        if file is None:
            raise TypeError("upload_channel_image() missing required argument: 'file'")
        return await super().upload_channel_image(
            channel_type, id, file=file, upload_sizes=upload_sizes, user=user
        )
