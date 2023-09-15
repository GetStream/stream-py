from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from backstage_settings_request import BackstageSettingsRequest
from geofence_settings_request import GeofenceSettingsRequest
from record_settings_request import RecordSettingsRequest
from ring_settings_request import RingSettingsRequest
from transcription_settings_request import TranscriptionSettingsRequest
from video_settings_request import VideoSettingsRequest
from audio_settings_request import AudioSettingsRequest
from screensharing_settings_request import ScreensharingSettingsRequest
from broadcast_settings_request import BroadcastSettingsRequest


@dataclass_json
@dataclass
class CallSettingsRequest:
    audio: Optional[AudioSettingsRequest] = field(
        metadata=config(field_name="audio"), default=None
    )
    backstage: Optional[BackstageSettingsRequest] = field(
        metadata=config(field_name="backstage"), default=None
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
    transcription: Optional[TranscriptionSettingsRequest] = field(
        metadata=config(field_name="transcription"), default=None
    )
    video: Optional[VideoSettingsRequest] = field(
        metadata=config(field_name="video"), default=None
    )
    broadcasting: Optional[BroadcastSettingsRequest] = field(
        metadata=config(field_name="broadcasting"), default=None
    )
    screensharing: Optional[ScreensharingSettingsRequest] = field(
        metadata=config(field_name="screensharing"), default=None
    )
