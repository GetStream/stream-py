# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.call import Call


@dataclass_json
@dataclass
class CreateCallResponse:
    duration: str = field(metadata=config(field_name="duration"))
    token: str = field(metadata=config(field_name="token"))
    agora_app_id: Optional[str] = field(
        metadata=config(field_name="agora_app_id"), default=None
    )
    agora_uid: Optional[int] = field(
        metadata=config(field_name="agora_uid"), default=None
    )
    call: Optional[Call] = field(metadata=config(field_name="call"), default=None)
