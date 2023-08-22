from dataclasses import dataclass
from typing import Optional

from models.model_audio_settings_request import AudioSettingsRequest
from models.model_backstage_settings_request import BackstageSettingsRequest
from models.model_broadcast_settings_request import BroadcastSettingsRequest
from models.model_geofence_settings_request import GeofenceSettingsRequest
from models.model_record_settings_request import RecordSettingsRequest
from models.model_ring_settings_request import RingSettingsRequest
from models.model_screensharing_settings_request import ScreensharingSettingsRequest
from models.model_transcription_settings_request import TranscriptionSettingsRequest
from models.model_video_settings_request import VideoSettingsRequest


@dataclass
class CallSettingsRequest:
    audio: Optional[AudioSettingsRequest] = None
    backstage: Optional[BackstageSettingsRequest] = None
    broadcasting: Optional[BroadcastSettingsRequest] = None
    geofencing: Optional[GeofenceSettingsRequest] = None
    recording: Optional[RecordSettingsRequest] = None
    ring: Optional[RingSettingsRequest] = None
    screensharing: Optional[ScreensharingSettingsRequest] = None
    transcription: Optional[TranscriptionSettingsRequest] = None
    video: Optional[VideoSettingsRequest] = None
