from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from call_settings_request import CallSettingsRequest


@dataclass_json
@dataclass
class UpdateCallRequest:
    custom: Optional[dict[str, object]] = field(
        metadata=config(field_name="custom"), default=None
    )
    settings_override: Optional[CallSettingsRequest] = field(
        metadata=config(field_name="settings_override"), default=None
    )
    starts_at: Optional[str] = field(
        metadata=config(field_name="starts_at"), default=None
    )
