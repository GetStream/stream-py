from dataclasses import dataclass
from typing import List, Optional

from .model_audio_settings_request import AudioSettingsRequest
from .model_backstage_settings_request import BackstageSettingsRequest
from .model_broadcast_settings_request import BroadcastSettingsRequest
from .model_geofence_settings_request import GeofenceSettingsRequest
from .model_record_settings_request import RecordSettingsRequest
from .model_ring_settings_request import RingSettingsRequest
from .model_screensharing_settings_request import ScreensharingSettingsRequest
from .model_transcription_settings_request import TranscriptionSettingsRequest
from .model_video_settings_request import VideoSettingsRequest


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
    auto_on: Optional[bool] = None
    enabled: Optional[bool] = None
    quality_tracks: Optional[List[str]] = None
