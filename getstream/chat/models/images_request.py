# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.image_data_request import ImageDataRequest


@dataclass_json
@dataclass
class ImagesRequest:
    fixed_width_downsampled: Optional[ImageDataRequest] = field(
        metadata=config(field_name="fixed_width_downsampled"), default=None
    )
    fixed_width_still: Optional[ImageDataRequest] = field(
        metadata=config(field_name="fixed_width_still"), default=None
    )
    original: Optional[ImageDataRequest] = field(
        metadata=config(field_name="original"), default=None
    )
    fixed_height: Optional[ImageDataRequest] = field(
        metadata=config(field_name="fixed_height"), default=None
    )
    fixed_height_downsampled: Optional[ImageDataRequest] = field(
        metadata=config(field_name="fixed_height_downsampled"), default=None
    )
    fixed_height_still: Optional[ImageDataRequest] = field(
        metadata=config(field_name="fixed_height_still"), default=None
    )
    fixed_width: Optional[ImageDataRequest] = field(
        metadata=config(field_name="fixed_width"), default=None
    )
