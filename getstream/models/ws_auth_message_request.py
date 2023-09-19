from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.models.connect_user_details_request import ConnectUserDetailsRequest


@dataclass_json
@dataclass
class WsauthMessageRequest:
    user_details: ConnectUserDetailsRequest = field(
        metadata=config(field_name="user_details")
    )
    token: str = field(metadata=config(field_name="token"))
