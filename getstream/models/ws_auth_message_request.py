# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.models.connect_user_details_request import ConnectUserDetailsRequest


@dataclass_json
@dataclass
class WsauthMessageRequest:
    token: str = field(metadata=config(field_name="token"))
    user_details: ConnectUserDetailsRequest = field(
        metadata=config(field_name="user_details")
    )
