from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.models.reaction_response import ReactionResponse


@dataclass_json
@dataclass
class SendReactionResponse:
    duration: str = field(metadata=config(field_name="duration"))
    reaction: ReactionResponse = field(metadata=config(field_name="reaction"))
