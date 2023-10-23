# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.chat.models.field import Field
from getstream.chat.models.action import Action
from getstream.chat.models.images import Images


@dataclass_json
@dataclass
class Attachment:
    pretext: Optional[str] = field(metadata=config(field_name="pretext"), default=None)
    asset_url: Optional[str] = field(
        metadata=config(field_name="asset_url"), default=None
    )
    author_icon: Optional[str] = field(
        metadata=config(field_name="author_icon"), default=None
    )
    fields: Optional[List[Field]] = field(
        metadata=config(field_name="fields"), default=None
    )
    og_scrape_url: Optional[str] = field(
        metadata=config(field_name="og_scrape_url"), default=None
    )
    original_width: Optional[int] = field(
        metadata=config(field_name="original_width"), default=None
    )
    actions: Optional[List[Action]] = field(
        metadata=config(field_name="actions"), default=None
    )
    color: Optional[str] = field(metadata=config(field_name="color"), default=None)
    title_link: Optional[str] = field(
        metadata=config(field_name="title_link"), default=None
    )
    type: Optional[str] = field(metadata=config(field_name="type"), default=None)
    author_name: Optional[str] = field(
        metadata=config(field_name="author_name"), default=None
    )
    fallback: Optional[str] = field(
        metadata=config(field_name="fallback"), default=None
    )
    giphy: Optional[Images] = field(metadata=config(field_name="giphy"), default=None)
    thumb_url: Optional[str] = field(
        metadata=config(field_name="thumb_url"), default=None
    )
    title: Optional[str] = field(metadata=config(field_name="title"), default=None)
    text: Optional[str] = field(metadata=config(field_name="text"), default=None)
    author_link: Optional[str] = field(
        metadata=config(field_name="author_link"), default=None
    )
    footer: Optional[str] = field(metadata=config(field_name="footer"), default=None)
    footer_icon: Optional[str] = field(
        metadata=config(field_name="footer_icon"), default=None
    )
    image_url: Optional[str] = field(
        metadata=config(field_name="image_url"), default=None
    )
    original_height: Optional[int] = field(
        metadata=config(field_name="original_height"), default=None
    )
