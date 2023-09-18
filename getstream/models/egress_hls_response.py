from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class EgressHlsresponse:
    playlist_url: str = field(metadata=config(field_name="playlist_url"))
