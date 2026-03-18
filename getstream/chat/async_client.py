import json
from typing import List, Optional

from getstream.chat.async_channel import Channel
from getstream.chat.async_rest_client import ChatRestClient
from getstream.common import telemetry
from getstream.models import (
    ImageSize,
    OnlyUserID,
    UploadChannelFileResponse,
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

    @telemetry.operation_name("getstream.api.chat.upload_channel_file")
    async def upload_channel_file(
        self,
        type: str,
        id: str,
        file: Optional[str] = None,
        user: Optional[OnlyUserID] = None,
    ) -> StreamResponse[UploadChannelFileResponse]:
        form_fields = []
        if user is not None:
            form_fields.append(("user", json.dumps(user.to_dict())))
        return await self._upload_multipart(
            "/api/v2/chat/channels/{type}/{id}/file",
            UploadChannelFileResponse,
            file,
            path_params={"type": type, "id": id},
            form_fields=form_fields,
        )

    @telemetry.operation_name("getstream.api.chat.upload_channel_image")
    async def upload_channel_image(
        self,
        type: str,
        id: str,
        file: Optional[str] = None,
        upload_sizes: Optional[List[ImageSize]] = None,
        user: Optional[OnlyUserID] = None,
    ) -> StreamResponse[UploadChannelResponse]:
        form_fields = []
        if user is not None:
            form_fields.append(("user", json.dumps(user.to_dict())))
        if upload_sizes is not None:
            form_fields.append(
                ("upload_sizes", json.dumps([s.to_dict() for s in upload_sizes]))
            )
        return await self._upload_multipart(
            "/api/v2/chat/channels/{type}/{id}/image",
            UploadChannelResponse,
            file,
            path_params={"type": type, "id": id},
            form_fields=form_fields,
        )
