from dataclasses import dataclass
from datetime import datetime

from .model_reaction_response import ReactionResponse


@dataclass
class CallReactionEvent:
    call_cid: str
    created_at: datetime
    reaction: ReactionResponse
    type: str

    @classmethod
    def from_dict(cls, data: dict) -> "CallReactionEvent":
        data["reaction"] = ReactionResponse.from_dict(data["reaction"])
        return cls(**data)
