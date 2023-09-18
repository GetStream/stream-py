from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from datetime import datetime
from getstream.models.reaction_response import ReactionResponse


@dataclass_json
@dataclass
class CallReactionEvent:
    reaction: ReactionResponse = field(metadata=config(field_name="reaction"))
    type: str = field(metadata=config(field_name="type"))
    call_cid: str = field(metadata=config(field_name="call_cid"))
    created_at: datetime = field(metadata=config(field_name="created_at"))
