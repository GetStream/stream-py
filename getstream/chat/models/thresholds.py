# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.label_thresholds import LabelThresholds


@dataclass_json
@dataclass
class Thresholds:
    spam: Optional[LabelThresholds] = field(
        metadata=config(field_name="spam"), default=None
    )
    toxic: Optional[LabelThresholds] = field(
        metadata=config(field_name="toxic"), default=None
    )
    explicit: Optional[LabelThresholds] = field(
        metadata=config(field_name="explicit"), default=None
    )
