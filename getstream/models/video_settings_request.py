# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.models.target_resolution_request import TargetResolutionRequest


@dataclass_json
@dataclass
class VideoSettingsRequest:
    access_request_enabled: Optional[bool] = field(
        metadata=config(field_name="access_request_enabled"), default=None
    )
    camera_default_on: Optional[bool] = field(
        metadata=config(field_name="camera_default_on"), default=None
    )
    camera_facing: Optional[str] = field(
        metadata=config(field_name="camera_facing"), default=None
    )
    enabled: Optional[bool] = field(metadata=config(field_name="enabled"), default=None)
    target_resolution: Optional[TargetResolutionRequest] = field(
        metadata=config(field_name="target_resolution"), default=None
    )
