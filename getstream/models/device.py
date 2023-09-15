from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class Device:
    id: str = field(metadata=config(field_name="id"))
    push_provider: str = field(metadata=config(field_name="push_provider"))
    created_at: str = field(metadata=config(field_name="created_at"))
    disabled: Optional[bool] = field(
        metadata=config(field_name="disabled"), default=None
    )
    disabled_reason: Optional[str] = field(
        metadata=config(field_name="disabled_reason"), default=None
    )
    push_provider_name: Optional[str] = field(
        metadata=config(field_name="push_provider_name"), default=None
    )
    voip: Optional[bool] = field(metadata=config(field_name="voip"), default=None)
