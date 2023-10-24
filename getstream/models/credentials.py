# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from getstream.models.ice_server import Iceserver
from getstream.models.sfu_response import Sfuresponse


@dataclass_json
@dataclass
class Credentials:
    token: str = field(metadata=config(field_name="token"))
    ice_servers: List[Iceserver] = field(metadata=config(field_name="ice_servers"))
    server: Sfuresponse = field(metadata=config(field_name="server"))
