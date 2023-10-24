# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.push_provider_request import PushProviderRequest


@dataclass_json
@dataclass
class UpsertPushProviderRequest:
    push_provider: Optional[PushProviderRequest] = field(
        metadata=config(field_name="push_provider"), default=None
    )
