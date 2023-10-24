# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class Hmscall:
    room_name: str = field(metadata=config(field_name="room_name"))
    room_id: str = field(metadata=config(field_name="room_id"))
