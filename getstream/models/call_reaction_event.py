from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from reaction_response import ReactionResponse


@dataclass_json
@dataclass
class CallReactionEvent:
    call_cid: str = field(metadata=config(field_name="call_cid"))
    created_at: str = field(metadata=config(field_name="created_at"))
    reaction: ReactionResponse = field(metadata=config(field_name="reaction"))
    type: str = field(metadata=config(field_name="type"))
