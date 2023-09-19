from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from datetime import datetime
from marshmallow import fields


@dataclass_json
@dataclass
class UserResponse:
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    custom: Dict[str, object] = field(metadata=config(field_name="custom"))
    id: str = field(metadata=config(field_name="id"))
    role: str = field(metadata=config(field_name="role"))
    teams: List[str] = field(metadata=config(field_name="teams"))
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    image: Optional[str] = field(metadata=config(field_name="image"), default=None)
    deleted_at: Optional[datetime] = field(
        metadata=config(
            field_name="deleted_at",
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    name: Optional[str] = field(metadata=config(field_name="name"), default=None)
