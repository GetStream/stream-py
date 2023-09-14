from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from broadcast_settings import BroadcastSettings
from record_settings import RecordSettings
from screensharing_settings import ScreensharingSettings
from transcription_settings import TranscriptionSettings
from audio_settings import AudioSettings
from backstage_settings import BackstageSettings
from geofence_settings import GeofenceSettings
from ring_settings import RingSettings
from video_settings import VideoSettings


@dataclass_json
@dataclass
class CallSettingsResponse:
    audio: AudioSettings = field(metadata=config(field_name="audio"))
    backstage: BackstageSettings = field(metadata=config(field_name="backstage"))
    geofencing: GeofenceSettings = field(metadata=config(field_name="geofencing"))
    ring: RingSettings = field(metadata=config(field_name="ring"))
    video: VideoSettings = field(metadata=config(field_name="video"))
    broadcasting: BroadcastSettings = field(metadata=config(field_name="broadcasting"))
    recording: RecordSettings = field(metadata=config(field_name="recording"))
    screensharing: ScreensharingSettings = field(
        metadata=config(field_name="screensharing")
    )
    transcription: TranscriptionSettings = field(
        metadata=config(field_name="transcription")
    )
