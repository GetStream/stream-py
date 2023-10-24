# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.reaction_request import ReactionRequest


@dataclass_json
@dataclass
class SendReactionRequest:
    reaction: ReactionRequest = field(metadata=config(field_name="reaction"))
    id: Optional[str] = field(metadata=config(field_name="ID"), default=None)
    enforce_unique: Optional[bool] = field(
        metadata=config(field_name="enforce_unique"), default=None
    )
    skip_push: Optional[bool] = field(
        metadata=config(field_name="skip_push"), default=None
    )
