from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class WscallEvent:
    call_cid: Optional[str] = field(
        metadata=config(field_name="call_cid"), default=None
    )
