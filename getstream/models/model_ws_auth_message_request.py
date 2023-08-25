from dataclasses import dataclass

from .model_connect_user_details_request import ConnectUserDetailsRequest


@dataclass
class WSAuthMessageRequest:
    token: str
    user_details: ConnectUserDetailsRequest
