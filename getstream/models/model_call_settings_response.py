from dataclasses import dataclass

from .model_audio_settings import AudioSettings
from .model_backstage_settings import BackstageSettings
from .model_broadcast_settings import BroadcastSettings
from .model_geofence_settings import GeofenceSettings
from .model_record_settings import RecordSettings
from .model_ring_settings import RingSettings
from .model_screensharing_settings import ScreensharingSettings
from .model_transcription_settings import TranscriptionSettings

from .model_video_settings import VideoSettings

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
