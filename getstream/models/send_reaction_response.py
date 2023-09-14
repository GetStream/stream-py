from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from reaction_response import ReactionResponse


@dataclass_json
@dataclass
class SendReactionResponse:
    reaction: ReactionResponse = field(metadata=config(field_name="reaction"))
    duration: str = field(metadata=config(field_name="duration"))
