# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.attachment import Attachment


@dataclass_json
@dataclass
class Campaign:
    channel_type: str = field(metadata=config(field_name="channel_type"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    segment_id: str = field(metadata=config(field_name="segment_id"))
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    attachments: List[Attachment] = field(metadata=config(field_name="attachments"))
    description: str = field(metadata=config(field_name="description"))
    id: str = field(metadata=config(field_name="id"))
    name: str = field(metadata=config(field_name="name"))
    defaults: Dict[str, str] = field(metadata=config(field_name="defaults"))
    sender_id: str = field(metadata=config(field_name="sender_id"))
    text: str = field(metadata=config(field_name="text"))
    status: Optional[str] = field(metadata=config(field_name="status"), default=None)
    failed_at: Optional[datetime] = field(
        metadata=config(
            field_name="failed_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    resumed_at: Optional[datetime] = field(
        metadata=config(
            field_name="resumed_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    errored_messages: Optional[int] = field(
        metadata=config(field_name="errored_messages"), default=None
    )
    scheduled_for: Optional[datetime] = field(
        metadata=config(
            field_name="scheduled_for",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    sent_messages: Optional[int] = field(
        metadata=config(field_name="sent_messages"), default=None
    )
    stopped_at: Optional[datetime] = field(
        metadata=config(
            field_name="stopped_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    completed_at: Optional[datetime] = field(
        metadata=config(
            field_name="completed_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    details: Optional[str] = field(metadata=config(field_name="details"), default=None)
    scheduled_at: Optional[datetime] = field(
        metadata=config(
            field_name="scheduled_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    task_id: Optional[str] = field(metadata=config(field_name="task_id"), default=None)
