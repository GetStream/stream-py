# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class ModerationResponse:
    action: str = field(metadata=config(field_name="action"))
    automod_response: object = field(metadata=config(field_name="automod_response"))
    explicit: float = field(metadata=config(field_name="explicit"))
    spam: float = field(metadata=config(field_name="spam"))
    toxic: float = field(metadata=config(field_name="toxic"))
