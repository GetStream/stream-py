# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, Optional
from getstream.chat.models.limit_info import LimitInfo


@dataclass_json
@dataclass
class GetRateLimitsResponse:
    duration: str = field(metadata=config(field_name="duration"))
    android: Optional[Dict[str, LimitInfo]] = field(
        metadata=config(field_name="android"), default=None
    )
    ios: Optional[Dict[str, LimitInfo]] = field(
        metadata=config(field_name="ios"), default=None
    )
    server_side: Optional[Dict[str, LimitInfo]] = field(
        metadata=config(field_name="server_side"), default=None
    )
    web: Optional[Dict[str, LimitInfo]] = field(
        metadata=config(field_name="web"), default=None
    )
