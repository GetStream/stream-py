from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.models.audio_settings import AudioSettings
from getstream.models.broadcast_settings import BroadcastSettings
from getstream.models.geofence_settings import GeofenceSettings
from getstream.models.record_settings import RecordSettings
from getstream.models.ring_settings import RingSettings
from getstream.models.transcription_settings import TranscriptionSettings
from getstream.models.backstage_settings import BackstageSettings
from getstream.models.screensharing_settings import ScreensharingSettings
from getstream.models.video_settings import VideoSettings


@dataclass_json
@dataclass
class CallSettingsResponse:
    video: VideoSettings = field(metadata=config(field_name="video"))
    backstage: BackstageSettings = field(metadata=config(field_name="backstage"))
    screensharing: ScreensharingSettings = field(
        metadata=config(field_name="screensharing")
    )
    geofencing: GeofenceSettings = field(metadata=config(field_name="geofencing"))
    recording: RecordSettings = field(metadata=config(field_name="recording"))
    ring: RingSettings = field(metadata=config(field_name="ring"))
    transcription: TranscriptionSettings = field(
        metadata=config(field_name="transcription")
    )
    audio: AudioSettings = field(metadata=config(field_name="audio"))
    broadcasting: BroadcastSettings = field(metadata=config(field_name="broadcasting"))
