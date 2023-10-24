# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.chat.models.field_request import FieldRequest
from getstream.chat.models.action_request import ActionRequest
from getstream.chat.models.images_request import ImagesRequest


@dataclass_json
@dataclass
class AttachmentRequest:
    pretext: Optional[str] = field(metadata=config(field_name="pretext"), default=None)
    title: Optional[str] = field(metadata=config(field_name="title"), default=None)
    title_link: Optional[str] = field(
        metadata=config(field_name="title_link"), default=None
    )
    author_icon: Optional[str] = field(
        metadata=config(field_name="author_icon"), default=None
    )
    fallback: Optional[str] = field(
        metadata=config(field_name="fallback"), default=None
    )
    footer: Optional[str] = field(metadata=config(field_name="footer"), default=None)
    original_height: Optional[int] = field(
        metadata=config(field_name="original_height"), default=None
    )
    asset_url: Optional[str] = field(
        metadata=config(field_name="asset_url"), default=None
    )
    color: Optional[str] = field(metadata=config(field_name="color"), default=None)
    fields: Optional[List[FieldRequest]] = field(
        metadata=config(field_name="fields"), default=None
    )
    footer_icon: Optional[str] = field(
        metadata=config(field_name="footer_icon"), default=None
    )
    author_link: Optional[str] = field(
        metadata=config(field_name="author_link"), default=None
    )
    original_width: Optional[int] = field(
        metadata=config(field_name="original_width"), default=None
    )
    thumb_url: Optional[str] = field(
        metadata=config(field_name="thumb_url"), default=None
    )
    type: Optional[str] = field(metadata=config(field_name="type"), default=None)
    og_scrape_url: Optional[str] = field(
        metadata=config(field_name="og_scrape_url"), default=None
    )
    text: Optional[str] = field(metadata=config(field_name="text"), default=None)
    actions: Optional[List[ActionRequest]] = field(
        metadata=config(field_name="actions"), default=None
    )
    author_name: Optional[str] = field(
        metadata=config(field_name="author_name"), default=None
    )
    giphy: Optional[ImagesRequest] = field(
        metadata=config(field_name="giphy"), default=None
    )
    image_url: Optional[str] = field(
        metadata=config(field_name="image_url"), default=None
    )
