from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.models.geofence_settings_request import GeofenceSettingsRequest
from getstream.models.record_settings_request import RecordSettingsRequest
from getstream.models.ring_settings_request import RingSettingsRequest
from getstream.models.screensharing_settings_request import ScreensharingSettingsRequest
from getstream.models.transcription_settings_request import TranscriptionSettingsRequest
from getstream.models.video_settings_request import VideoSettingsRequest
from getstream.models.audio_settings_request import AudioSettingsRequest
from getstream.models.broadcast_settings_request import BroadcastSettingsRequest
from getstream.models.backstage_settings_request import BackstageSettingsRequest


@dataclass_json
@dataclass
class CallSettingsRequest:
    backstage: Optional[BackstageSettingsRequest] = field(
        metadata=config(field_name="backstage"), default=None
    )
    broadcasting: Optional[BroadcastSettingsRequest] = field(
        metadata=config(field_name="broadcasting"), default=None
    )
    video: Optional[VideoSettingsRequest] = field(
        metadata=config(field_name="video"), default=None
    )
    audio: Optional[AudioSettingsRequest] = field(
        metadata=config(field_name="audio"), default=None
    )
    geofencing: Optional[GeofenceSettingsRequest] = field(
        metadata=config(field_name="geofencing"), default=None
    )
    recording: Optional[RecordSettingsRequest] = field(
        metadata=config(field_name="recording"), default=None
    )
    ring: Optional[RingSettingsRequest] = field(
        metadata=config(field_name="ring"), default=None
    )
    screensharing: Optional[ScreensharingSettingsRequest] = field(
        metadata=config(field_name="screensharing"), default=None
    )
    transcription: Optional[TranscriptionSettingsRequest] = field(
        metadata=config(field_name="transcription"), default=None
    )
