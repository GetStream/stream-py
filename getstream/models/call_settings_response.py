from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.models.record_settings_response import RecordSettingsResponse
from getstream.models.ring_settings import RingSettings
from getstream.models.screensharing_settings import ScreensharingSettings
from getstream.models.transcription_settings import TranscriptionSettings
from getstream.models.backstage_settings import BackstageSettings
from getstream.models.broadcast_settings_response import BroadcastSettingsResponse
from getstream.models.thumbnails_settings import ThumbnailsSettings
from getstream.models.video_settings import VideoSettings
from getstream.models.audio_settings import AudioSettings
from getstream.models.geofence_settings import GeofenceSettings


@dataclass_json
@dataclass
class CallSettingsResponse:
    audio: AudioSettings = field(metadata=config(field_name="audio"))
    geofencing: GeofenceSettings = field(metadata=config(field_name="geofencing"))
    thumbnails: ThumbnailsSettings = field(metadata=config(field_name="thumbnails"))
    video: VideoSettings = field(metadata=config(field_name="video"))
    backstage: BackstageSettings = field(metadata=config(field_name="backstage"))
    broadcasting: BroadcastSettingsResponse = field(
        metadata=config(field_name="broadcasting")
    )
    recording: RecordSettingsResponse = field(metadata=config(field_name="recording"))
    ring: RingSettings = field(metadata=config(field_name="ring"))
    screensharing: ScreensharingSettings = field(
        metadata=config(field_name="screensharing")
    )
    transcription: TranscriptionSettings = field(
        metadata=config(field_name="transcription")
    )
