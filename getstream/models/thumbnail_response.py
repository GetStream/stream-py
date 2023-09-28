from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class ThumbnailResponse:
    image_url: str = field(metadata=config(field_name="image_url"))
