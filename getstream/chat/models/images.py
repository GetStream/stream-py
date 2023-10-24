# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.chat.models.image_data import ImageData


@dataclass_json
@dataclass
class Images:
    original: ImageData = field(metadata=config(field_name="original"))
    fixed_height: ImageData = field(metadata=config(field_name="fixed_height"))
    fixed_height_downsampled: ImageData = field(
        metadata=config(field_name="fixed_height_downsampled")
    )
    fixed_height_still: ImageData = field(
        metadata=config(field_name="fixed_height_still")
    )
    fixed_width: ImageData = field(metadata=config(field_name="fixed_width"))
    fixed_width_downsampled: ImageData = field(
        metadata=config(field_name="fixed_width_downsampled")
    )
    fixed_width_still: ImageData = field(
        metadata=config(field_name="fixed_width_still")
    )
