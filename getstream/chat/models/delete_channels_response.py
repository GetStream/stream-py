# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, Optional
from getstream.chat.models.delete_channels_result import DeleteChannelsResult


@dataclass_json
@dataclass
class DeleteChannelsResponse:
    duration: str = field(metadata=config(field_name="duration"))
    result: Optional[Dict[str, DeleteChannelsResult]] = field(
        metadata=config(field_name="result"), default=None
    )
    task_id: Optional[str] = field(metadata=config(field_name="task_id"), default=None)
