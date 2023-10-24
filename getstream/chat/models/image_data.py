# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class ImageData:
    height: str = field(metadata=config(field_name="height"))
    size: str = field(metadata=config(field_name="size"))
    url: str = field(metadata=config(field_name="url"))
    width: str = field(metadata=config(field_name="width"))
    frames: str = field(metadata=config(field_name="frames"))
