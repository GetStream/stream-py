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

    @classmethod
    def from_dict(cls, data: dict) -> "CallSettingsResponse":
        data["audio"] = AudioSettings.from_dict(data["audio"])
        data["backstage"] = BackstageSettings.from_dict(data["backstage"])
        data["broadcasting"] = BroadcastSettings.from_dict(data["broadcasting"])
        data["geofencing"] = GeofenceSettings.from_dict(data["geofencing"])
        data["recording"] = RecordSettings.from_dict(data["recording"])
        data["ring"] = RingSettings.from_dict(data["ring"])
        data["screensharing"] = ScreensharingSettings.from_dict(data["screensharing"])
        data["transcription"] = TranscriptionSettings.from_dict(data["transcription"])
        data["video"] = VideoSettings.from_dict(data["video"])
        return cls(**data)
