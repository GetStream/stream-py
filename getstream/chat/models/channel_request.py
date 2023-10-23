# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.chat.models.channel_member_request import ChannelMemberRequest
from getstream.chat.models.channel_config_request import ChannelConfigRequest
from getstream.chat.models.user_object_request import UserObjectRequest


@dataclass_json
@dataclass
class ChannelRequest:
    config_overrides: Optional[ChannelConfigRequest] = field(
        metadata=config(field_name="config_overrides"), default=None
    )
    disabled: Optional[bool] = field(
        metadata=config(field_name="disabled"), default=None
    )
    members: Optional[List[ChannelMemberRequest]] = field(
        metadata=config(field_name="members"), default=None
    )
    team: Optional[str] = field(metadata=config(field_name="team"), default=None)
    truncated_by: Optional[List[int]] = field(
        metadata=config(field_name="truncated_by"), default=None
    )
    truncated_by_id: Optional[str] = field(
        metadata=config(field_name="truncated_by_id"), default=None
    )
    auto_translation_enabled: Optional[bool] = field(
        metadata=config(field_name="auto_translation_enabled"), default=None
    )
    auto_translation_language: Optional[str] = field(
        metadata=config(field_name="auto_translation_language"), default=None
    )
    own_capabilities: Optional[List[int]] = field(
        metadata=config(field_name="own_capabilities"), default=None
    )
    truncated_at: Optional[List[int]] = field(
        metadata=config(field_name="truncated_at"), default=None
    )
    created_by: Optional[UserObjectRequest] = field(
        metadata=config(field_name="created_by"), default=None
    )
    frozen: Optional[bool] = field(metadata=config(field_name="frozen"), default=None)
