from dataclasses import dataclass

from models.model_reaction_response import ReactionResponse


@dataclass
class SendReactionResponse:
    duration: str
    reaction: ReactionResponse
