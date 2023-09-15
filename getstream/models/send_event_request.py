from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class SendEventRequest:
    custom: Optional[dict[str, object]] = field(
        metadata=config(field_name="custom"), default=None
    )
