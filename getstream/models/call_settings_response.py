# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json

from getstream.models.audio_settings import AudioSettings
from getstream.models.record_settings_response import RecordSettingsResponse
from getstream.models.transcription_settings import TranscriptionSettings
from getstream.models.video_settings import VideoSettings
from getstream.models.backstage_settings import BackstageSettings
from getstream.models.broadcast_settings_response import BroadcastSettingsResponse
from getstream.models.geofence_settings import GeofenceSettings
from getstream.models.ring_settings import RingSettings
from getstream.models.screensharing_settings import ScreensharingSettings
from getstream.models.thumbnails_settings import ThumbnailsSettings


@dataclass_json
@dataclass
class CallSettingsResponse:
    backstage: BackstageSettings = field(metadata=config(field_name="backstage"))
    broadcasting: BroadcastSettingsResponse = field(
        metadata=config(field_name="broadcasting")
    )
    geofencing: GeofenceSettings = field(metadata=config(field_name="geofencing"))
    ring: RingSettings = field(metadata=config(field_name="ring"))
    screensharing: ScreensharingSettings = field(
        metadata=config(field_name="screensharing")
    )
    thumbnails: ThumbnailsSettings = field(metadata=config(field_name="thumbnails"))
    audio: AudioSettings = field(metadata=config(field_name="audio"))
    recording: RecordSettingsResponse = field(metadata=config(field_name="recording"))
    transcription: TranscriptionSettings = field(
        metadata=config(field_name="transcription")
    )
    video: VideoSettings = field(metadata=config(field_name="video"))
    external_storage: Optional[str] = field(
        metadata=config(field_name="external_storage"), default=None
    )
