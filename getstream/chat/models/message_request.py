# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.user_object_request import UserObjectRequest
from getstream.chat.models.attachment_request import AttachmentRequest


@dataclass_json
@dataclass
class MessageRequest:
    attachments: List[AttachmentRequest] = field(
        metadata=config(field_name="attachments")
    )
    html: Optional[str] = field(metadata=config(field_name="html"), default=None)
    id: Optional[str] = field(metadata=config(field_name="id"), default=None)
    pinned: Optional[bool] = field(metadata=config(field_name="pinned"), default=None)
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
    cid: Optional[List[int]] = field(metadata=config(field_name="cid"), default=None)
    parent_id: Optional[str] = field(
        metadata=config(field_name="parent_id"), default=None
    )
    pinned_at: Optional[datetime] = field(
        metadata=config(
            field_name="pinned_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    reaction_scores: Optional[List[int]] = field(
        metadata=config(field_name="reaction_scores"), default=None
    )
    show_in_channel: Optional[bool] = field(
        metadata=config(field_name="show_in_channel"), default=None
    )
    silent: Optional[bool] = field(metadata=config(field_name="silent"), default=None)
    user: Optional[UserObjectRequest] = field(
        metadata=config(field_name="user"), default=None
    )
    parent: Optional[List[int]] = field(
        metadata=config(field_name="parent"), default=None
    )
    pin_expires: Optional[datetime] = field(
        metadata=config(
            field_name="pin_expires",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    quoted_message_id: Optional[str] = field(
        metadata=config(field_name="quoted_message_id"), default=None
    )
    mentioned_users: Optional[List[str]] = field(
        metadata=config(field_name="mentioned_users"), default=None
    )
    pinned_by: Optional[List[int]] = field(
        metadata=config(field_name="pinned_by"), default=None
    )
    text: Optional[str] = field(metadata=config(field_name="text"), default=None)
    type: Optional[str] = field(metadata=config(field_name="type"), default=None)
    mml: Optional[str] = field(metadata=config(field_name="mml"), default=None)
