from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json

from getstream.models.call_state_response_fields import CallStateResponseFields


@dataclass_json
@dataclass
class ListCallTypeResponse:
    duration: str = field(metadata=config(field_name="duration"))
    call_types: dict[str, CallStateResponseFields] = field(
        metadata=config(field_name="call_types")
    )
