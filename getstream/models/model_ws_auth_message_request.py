from dataclasses import dataclass

from .model_connect_user_details_request import ConnectUserDetailsRequest


@dataclass
class WSAuthMessageRequest:
    token: str
    user_details: ConnectUserDetailsRequest

    @classmethod
    def from_dict(cls, data: dict) -> "WSAuthMessageRequest":
        data["user_details"] = ConnectUserDetailsRequest.from_dict(data["user_details"])
        return cls(**data)
