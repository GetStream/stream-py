# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from __future__ import annotations

# TODO: fix generator to handle self-referencing types add ^ the above line
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.attachment import Attachment
from getstream.chat.models.user_object import UserObject
from getstream.chat.models.reaction import Reaction


@dataclass_json
@dataclass
class Message:
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    silent: bool = field(metadata=config(field_name="silent"))
    text: str = field(metadata=config(field_name="text"))
    reaction_counts: Dict[str, int] = field(
        metadata=config(field_name="reaction_counts")
    )
    visible_reply_count: int = field(metadata=config(field_name="visible_reply_count"))
    reply_count: int = field(metadata=config(field_name="reply_count"))
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    attachments: List[Attachment] = field(metadata=config(field_name="attachments"))
    html: str = field(metadata=config(field_name="html"))
    id: str = field(metadata=config(field_name="id"))
    pinned: bool = field(metadata=config(field_name="pinned"))
    cid: str = field(metadata=config(field_name="cid"))
    mentioned_users: List[UserObject] = field(
        metadata=config(field_name="mentioned_users")
    )
    own_reactions: List[Reaction] = field(metadata=config(field_name="own_reactions"))
    reaction_scores: Dict[str, int] = field(
        metadata=config(field_name="reaction_scores")
    )
    shadowed: bool = field(metadata=config(field_name="shadowed"))
    latest_reactions: List[Reaction] = field(
        metadata=config(field_name="latest_reactions")
    )
    type: str = field(metadata=config(field_name="type"))
    user: Optional[UserObject] = field(metadata=config(field_name="user"), default=None)
    deleted_at: Optional[datetime] = field(
        metadata=config(
            field_name="deleted_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    image_labels: Optional[Dict[str, List[str]]] = field(
        metadata=config(field_name="image_labels"), default=None
    )
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
    show_in_channel: Optional[bool] = field(
        metadata=config(field_name="show_in_channel"), default=None
    )
    mml: Optional[str] = field(metadata=config(field_name="mml"), default=None)
    quoted_message: Optional[Message] = field(
        metadata=config(field_name="quoted_message"), default=None
    )
    quoted_message_id: Optional[str] = field(
        metadata=config(field_name="quoted_message_id"), default=None
    )
    before_message_send_failed: Optional[bool] = field(
        metadata=config(field_name="before_message_send_failed"), default=None
    )
    command: Optional[str] = field(metadata=config(field_name="command"), default=None)
    i_18_n: Optional[Dict[str, str]] = field(
        metadata=config(field_name="i18n"), default=None
    )
    thread_participants: Optional[List[UserObject]] = field(
        metadata=config(field_name="thread_participants"), default=None
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
    pinned_by: Optional[UserObject] = field(
        metadata=config(field_name="pinned_by"), default=None
    )
