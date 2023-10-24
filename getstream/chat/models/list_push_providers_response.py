# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from getstream.chat.models.push_provider_response import PushProviderResponse


@dataclass_json
@dataclass
class ListPushProvidersResponse:
    duration: str = field(metadata=config(field_name="duration"))
    push_providers: List[PushProviderResponse] = field(
        metadata=config(field_name="push_providers")
    )
