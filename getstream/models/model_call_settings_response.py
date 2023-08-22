from dataclasses import dataclass
from models.model_audio_settings import AudioSettings
from models.model_backstage_settings import BackstageSettings
from models.model_broadcast_settings import BroadcastSettings
from models.model_geofence_settings import GeofenceSettings
from models.model_record_settings import RecordSettings
from models.model_ring_settings import RingSettings
from models.model_screensharing_settings import ScreensharingSettings
from models.model_transcription_settings import TranscriptionSettings

from models.model_video_settings import VideoSettings


@dataclass
class CallSettingsResponse:
    audio: AudioSettings
    backstage: BackstageSettings
    broadcasting: BroadcastSettings
    geofencing: GeofenceSettings
    recording: RecordSettings
    ring: RingSettings
    screensharing: ScreensharingSettings
    transcription: TranscriptionSettings
    video: VideoSettings
