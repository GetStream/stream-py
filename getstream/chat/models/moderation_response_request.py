# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class ModerationResponseRequest:
    automod_response: Optional[object] = field(
        metadata=config(field_name="automod_response"), default=None
    )
    explicit: Optional[float] = field(
        metadata=config(field_name="explicit"), default=None
    )
    spam: Optional[float] = field(metadata=config(field_name="spam"), default=None)
    toxic: Optional[float] = field(metadata=config(field_name="toxic"), default=None)
    action: Optional[str] = field(metadata=config(field_name="action"), default=None)
