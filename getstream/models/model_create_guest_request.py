from dataclasses import dataclass

from models.model_user_request import UserRequest


@dataclass
class CreateGuestRequest:
    user: UserRequest
