# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class AudioSettings:
    mic_default_on: bool = field(metadata=config(field_name="mic_default_on"))
    opus_dtx_enabled: bool = field(metadata=config(field_name="opus_dtx_enabled"))
    redundant_coding_enabled: bool = field(
        metadata=config(field_name="redundant_coding_enabled")
    )
    speaker_default_on: bool = field(metadata=config(field_name="speaker_default_on"))
    access_request_enabled: bool = field(
        metadata=config(field_name="access_request_enabled")
    )
    default_device: str = field(metadata=config(field_name="default_device"))
