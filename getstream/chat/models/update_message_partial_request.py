# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from getstream.chat.models.user_object_request import UserObjectRequest


@dataclass_json
@dataclass
class UpdateMessagePartialRequest:
    unset: List[str] = field(metadata=config(field_name="unset"))
    set: Dict[str, object] = field(metadata=config(field_name="set"))
    user: Optional[UserObjectRequest] = field(
        metadata=config(field_name="user"), default=None
    )
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
    skip_enrich_url: Optional[bool] = field(
        metadata=config(field_name="skip_enrich_url"), default=None
    )
