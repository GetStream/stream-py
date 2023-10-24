# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.chat.models.image_size_request import ImageSizeRequest
from getstream.chat.models.only_user_id_request import OnlyUserIdrequest


@dataclass_json
@dataclass
class ImageUploadRequest:
    file: Optional[str] = field(metadata=config(field_name="file"), default=None)
    upload_sizes: Optional[List[ImageSizeRequest]] = field(
        metadata=config(field_name="upload_sizes"), default=None
    )
    user: Optional[OnlyUserIdrequest] = field(
        metadata=config(field_name="user"), default=None
    )
