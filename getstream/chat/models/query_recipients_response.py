# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, List
from getstream.chat.models.campaign import Campaign
from getstream.chat.models.channel import Channel
from getstream.chat.models.recipient import Recipient
from getstream.chat.models.segment import Segment
from getstream.chat.models.user_object import UserObject


@dataclass_json
@dataclass
class QueryRecipientsResponse:
    users: Dict[str, UserObject] = field(metadata=config(field_name="users"))
    campaigns: Dict[str, Campaign] = field(metadata=config(field_name="campaigns"))
    channels: Dict[str, Channel] = field(metadata=config(field_name="channels"))
    duration: str = field(metadata=config(field_name="duration"))
    recipients: List[Recipient] = field(metadata=config(field_name="recipients"))
    segments: Dict[str, Segment] = field(metadata=config(field_name="segments"))
