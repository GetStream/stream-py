# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.async_moderation_callback_config_request import (
    AsyncModerationCallbackConfigRequest,
)


@dataclass_json
@dataclass
class AsyncModerationConfigurationRequest:
    callback: Optional[AsyncModerationCallbackConfigRequest] = field(
        metadata=config(field_name="callback"), default=None
    )
    timeout_ms: Optional[int] = field(
        metadata=config(field_name="timeout_ms"), default=None
    )
