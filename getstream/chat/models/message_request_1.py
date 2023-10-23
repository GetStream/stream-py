# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.user_object_request import UserObjectRequest
from getstream.chat.models.reaction_request import ReactionRequest
from getstream.chat.models.attachment_request import AttachmentRequest
from getstream.chat.models.message_request_1 import MessageRequest1


@dataclass_json
@dataclass
class MessageRequest1:
    text: str = field(metadata=config(field_name="text"))
    mml: str = field(metadata=config(field_name="mml"))
    html: Optional[str] = field(metadata=config(field_name="html"), default=None)
    type: Optional[str] = field(metadata=config(field_name="type"), default=None)
    user: Optional[UserObjectRequest] = field(
        metadata=config(field_name="user"), default=None
    )
    mentioned_users: Optional[List[UserObjectRequest]] = field(
        metadata=config(field_name="mentioned_users"), default=None
    )
    id: Optional[str] = field(metadata=config(field_name="id"), default=None)
    reply_count: Optional[int] = field(
        metadata=config(field_name="reply_count"), default=None
    )
    thread_participants: Optional[List[UserObjectRequest]] = field(
        metadata=config(field_name="thread_participants"), default=None
    )
    attachments: Optional[List[AttachmentRequest]] = field(
        metadata=config(field_name="attachments"), default=None
    )
    deleted_at: Optional[datetime] = field(
        metadata=config(
            field_name="deleted_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    latest_reactions: Optional[List[ReactionRequest]] = field(
        metadata=config(field_name="latest_reactions"), default=None
    )
    own_reactions: Optional[List[ReactionRequest]] = field(
        metadata=config(field_name="own_reactions"), default=None
    )
    silent: Optional[bool] = field(metadata=config(field_name="silent"), default=None)
    image_labels: Optional[Dict[str, List[str]]] = field(
        metadata=config(field_name="image_labels"), default=None
    )
    pinned: Optional[bool] = field(metadata=config(field_name="pinned"), default=None)
    quoted_message: Optional[MessageRequest1] = field(
        metadata=config(field_name="quoted_message"), default=None
    )
    quoted_message_id: Optional[str] = field(
        metadata=config(field_name="quoted_message_id"), default=None
    )
    reaction_counts: Optional[Dict[str, int]] = field(
        metadata=config(field_name="reaction_counts"), default=None
    )
    updated_at: Optional[datetime] = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    visible_reply_count: Optional[int] = field(
        metadata=config(field_name="visible_reply_count"), default=None
    )
    cid: Optional[str] = field(metadata=config(field_name="cid"), default=None)
    reaction_scores: Optional[Dict[str, int]] = field(
        metadata=config(field_name="reaction_scores"), default=None
    )
    shadowed: Optional[bool] = field(
        metadata=config(field_name="shadowed"), default=None
    )
    show_in_channel: Optional[bool] = field(
        metadata=config(field_name="show_in_channel"), default=None
    )
    before_message_send_failed: Optional[bool] = field(
        metadata=config(field_name="before_message_send_failed"), default=None
    )
    i_18_n: Optional[Dict[str, str]] = field(
        metadata=config(field_name="i18n"), default=None
    )
    parent_id: Optional[str] = field(
        metadata=config(field_name="parent_id"), default=None
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
    command: Optional[str] = field(metadata=config(field_name="command"), default=None)
    created_at: Optional[datetime] = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
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
    pinned_by: Optional[UserObjectRequest] = field(
        metadata=config(field_name="pinned_by"), default=None
    )
