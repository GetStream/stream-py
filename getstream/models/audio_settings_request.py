# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class AudioSettingsRequest:
    default_device: str = field(metadata=config(field_name="default_device"))
    redundant_coding_enabled: Optional[bool] = field(
        metadata=config(field_name="redundant_coding_enabled"), default=None
    )
    speaker_default_on: Optional[bool] = field(
        metadata=config(field_name="speaker_default_on"), default=None
    )
    access_request_enabled: Optional[bool] = field(
        metadata=config(field_name="access_request_enabled"), default=None
    )
    mic_default_on: Optional[bool] = field(
        metadata=config(field_name="mic_default_on"), default=None
    )
    opus_dtx_enabled: Optional[bool] = field(
        metadata=config(field_name="opus_dtx_enabled"), default=None
    )
