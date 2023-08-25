from dataclasses import dataclass

from .model_user_request import UserRequest


@dataclass
class CreateGuestRequest:
    user: UserRequest
