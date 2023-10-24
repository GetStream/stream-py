# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.chat.models.channel_export_request import ChannelExportRequest


@dataclass_json
@dataclass
class ExportChannelsRequest:
    clear_deleted_message_text: Optional[bool] = field(
        metadata=config(field_name="clear_deleted_message_text"), default=None
    )
    export_users: Optional[bool] = field(
        metadata=config(field_name="export_users"), default=None
    )
    include_truncated_messages: Optional[bool] = field(
        metadata=config(field_name="include_truncated_messages"), default=None
    )
    version: Optional[str] = field(metadata=config(field_name="version"), default=None)
    channels: Optional[List[ChannelExportRequest]] = field(
        metadata=config(field_name="channels"), default=None
    )
