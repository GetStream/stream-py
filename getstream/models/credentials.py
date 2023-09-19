from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from getstream.models.ice_server import Iceserver
from getstream.models.sfu_response import Sfuresponse


@dataclass_json
@dataclass
class Credentials:
    server: Sfuresponse = field(metadata=config(field_name="server"))
    token: str = field(metadata=config(field_name="token"))
    ice_servers: List[Iceserver] = field(metadata=config(field_name="ice_servers"))
