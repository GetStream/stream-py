from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class RingSettingsRequest:
    auto_cancel_timeout_ms: Optional[int] = field(
        metadata=config(field_name="auto_cancel_timeout_ms"), default=None
    )
    incoming_call_timeout_ms: Optional[int] = field(
        metadata=config(field_name="incoming_call_timeout_ms"), default=None
    )
