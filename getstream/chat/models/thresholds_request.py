# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.label_thresholds_request import LabelThresholdsRequest


@dataclass_json
@dataclass
class ThresholdsRequest:
    explicit: Optional[LabelThresholdsRequest] = field(
        metadata=config(field_name="explicit"), default=None
    )
    spam: Optional[LabelThresholdsRequest] = field(
        metadata=config(field_name="spam"), default=None
    )
    toxic: Optional[LabelThresholdsRequest] = field(
        metadata=config(field_name="toxic"), default=None
    )
