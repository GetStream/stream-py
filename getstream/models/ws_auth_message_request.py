from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from connect_user_details_request import ConnectUserDetailsRequest


@dataclass_json
@dataclass
class WsauthMessageRequest:
    token: str = field(metadata=config(field_name="token"))
    user_details: ConnectUserDetailsRequest = field(
        metadata=config(field_name="user_details")
    )
