# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class ImageDataRequest:
    size: Optional[str] = field(metadata=config(field_name="size"), default=None)
    url: Optional[str] = field(metadata=config(field_name="url"), default=None)
    width: Optional[str] = field(metadata=config(field_name="width"), default=None)
    frames: Optional[str] = field(metadata=config(field_name="frames"), default=None)
    height: Optional[str] = field(metadata=config(field_name="height"), default=None)
