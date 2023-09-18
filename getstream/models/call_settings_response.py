from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.models.ring_settings import RingSettings
from getstream.models.video_settings import VideoSettings
from getstream.models.audio_settings import AudioSettings
from getstream.models.backstage_settings import BackstageSettings
from getstream.models.broadcast_settings import BroadcastSettings
from getstream.models.record_settings import RecordSettings
from getstream.models.geofence_settings import GeofenceSettings
from getstream.models.screensharing_settings import ScreensharingSettings
from getstream.models.transcription_settings import TranscriptionSettings


@dataclass_json
@dataclass
class CallSettingsResponse:
    recording: RecordSettings = field(metadata=config(field_name="recording"))
    ring: RingSettings = field(metadata=config(field_name="ring"))
    video: VideoSettings = field(metadata=config(field_name="video"))
    audio: AudioSettings = field(metadata=config(field_name="audio"))
    backstage: BackstageSettings = field(metadata=config(field_name="backstage"))
    broadcasting: BroadcastSettings = field(metadata=config(field_name="broadcasting"))
    geofencing: GeofenceSettings = field(metadata=config(field_name="geofencing"))
    screensharing: ScreensharingSettings = field(
        metadata=config(field_name="screensharing")
    )
    transcription: TranscriptionSettings = field(
        metadata=config(field_name="transcription")
    )
