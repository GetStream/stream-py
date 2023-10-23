# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.chat.models.image_size import ImageSize


@dataclass_json
@dataclass
class ImageUploadResponse:
    duration: str = field(metadata=config(field_name="duration"))
    file: Optional[str] = field(metadata=config(field_name="file"), default=None)
    thumb_url: Optional[str] = field(
        metadata=config(field_name="thumb_url"), default=None
    )
    upload_sizes: Optional[List[ImageSize]] = field(
        metadata=config(field_name="upload_sizes"), default=None
    )
