# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.backstage_settings import BackstageSettings
from getstream.chat.models.broadcast_settings import BroadcastSettings
from getstream.chat.models.screensharing_settings import ScreensharingSettings
from getstream.chat.models.audio_settings import AudioSettings
from getstream.chat.models.geofence_settings import GeofenceSettings
from getstream.chat.models.record_settings import RecordSettings
from getstream.chat.models.ring_settings import RingSettings
from getstream.chat.models.transcription_settings import TranscriptionSettings
from getstream.chat.models.video_settings import VideoSettings


@dataclass_json
@dataclass
class CallSettings:
    broadcasting: Optional[BroadcastSettings] = field(
        metadata=config(field_name="broadcasting"), default=None
    )
    screensharing: Optional[ScreensharingSettings] = field(
        metadata=config(field_name="screensharing"), default=None
    )
    backstage: Optional[BackstageSettings] = field(
        metadata=config(field_name="backstage"), default=None
    )
    geofencing: Optional[GeofenceSettings] = field(
        metadata=config(field_name="geofencing"), default=None
    )
    recording: Optional[RecordSettings] = field(
        metadata=config(field_name="recording"), default=None
    )
    ring: Optional[RingSettings] = field(
        metadata=config(field_name="ring"), default=None
    )
    transcription: Optional[TranscriptionSettings] = field(
        metadata=config(field_name="transcription"), default=None
    )
    video: Optional[VideoSettings] = field(
        metadata=config(field_name="video"), default=None
    )
    audio: Optional[AudioSettings] = field(
        metadata=config(field_name="audio"), default=None
    )
