import json
from typing import List, Optional

from getstream.common import telemetry
from getstream.common.async_rest_client import CommonRestClient
from getstream.models import (
    FileUploadResponse,
    ImageSize,
    ImageUploadResponse,
    OnlyUserID,
)
from getstream.stream_response import StreamResponse


class CommonClient(CommonRestClient):
    def __init__(self, api_key: str, base_url, token, timeout, user_agent=None):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            token=token,
            timeout=timeout,
            user_agent=user_agent,
        )

    @telemetry.operation_name("getstream.api.common.upload_file")
    async def upload_file(
        self, file: str, user: Optional[OnlyUserID] = None
    ) -> StreamResponse[FileUploadResponse]:
        form_fields = []
        if user is not None:
            form_fields.append(("user", json.dumps(user.to_dict())))
        return await self._upload_multipart(
            "/api/v2/uploads/file",
            FileUploadResponse,
            file,
            form_fields=form_fields,
        )

    @telemetry.operation_name("getstream.api.common.upload_image")
    async def upload_image(
        self,
        file: str,
        upload_sizes: Optional[List[ImageSize]] = None,
        user: Optional[OnlyUserID] = None,
    ) -> StreamResponse[ImageUploadResponse]:
        form_fields = []
        if user is not None:
            form_fields.append(("user", json.dumps(user.to_dict())))
        if upload_sizes is not None:
            form_fields.append(
                ("upload_sizes", json.dumps([s.to_dict() for s in upload_sizes]))
            )
        return await self._upload_multipart(
            "/api/v2/uploads/image",
            ImageUploadResponse,
            file,
            form_fields=form_fields,
        )
