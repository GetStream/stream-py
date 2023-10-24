# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class ImageSizeRequest:
    width: Optional[int] = field(metadata=config(field_name="width"), default=None)
    crop: Optional[str] = field(metadata=config(field_name="crop"), default=None)
    height: Optional[int] = field(metadata=config(field_name="height"), default=None)
    resize: Optional[str] = field(metadata=config(field_name="resize"), default=None)
