from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from ice_server import Iceserver
from sfu_response import Sfuresponse


@dataclass_json
@dataclass
class Credentials:
    ice_servers: list[Iceserver] = field(metadata=config(field_name="ice_servers"))
    server: Sfuresponse = field(metadata=config(field_name="server"))
    token: str = field(metadata=config(field_name="token"))
