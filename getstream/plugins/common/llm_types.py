from enum import Enum
from typing import List, Literal, NotRequired, TypedDict, Union


class TextPart(TypedDict):
    type: Literal["text"]
    text: str


class ImageBytesPart(TypedDict):
    type: Literal["image"]
    data: bytes
    mime_type: NotRequired[str]


class ImageURLPart(TypedDict):
    type: Literal["image"]
    url: str
    mime_type: NotRequired[str]


class AudioPart(TypedDict):
    type: Literal["audio"]
    data: bytes
    mime_type: str
    sample_rate: NotRequired[int]
    channels: NotRequired[int]


ContentPart = Union[TextPart, ImageBytesPart, ImageURLPart, AudioPart]


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(TypedDict):
    role: Role
    content: List[ContentPart]


__all__ = [
    "TextPart",
    "ImageBytesPart",
    "ImageURLPart",
    "AudioPart",
    "ContentPart",
    "Role",
    "Message",
]
