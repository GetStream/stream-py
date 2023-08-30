from dataclasses import dataclass

from .model_reaction_response import ReactionResponse


@dataclass
class SendReactionResponse:
    duration: str
    reaction: ReactionResponse

    @classmethod
    def from_dict(cls, data: dict) -> "SendReactionResponse":
        data["reaction"] = ReactionResponse.from_dict(data["reaction"])
        return cls(**data)
