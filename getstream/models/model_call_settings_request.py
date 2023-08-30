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

    @classmethod
    def from_dict(cls, data: dict) -> "CallSettingsRequest":
        if data.get("audio"):
            data["audio"] = AudioSettingsRequest.from_dict(data["audio"])
        if data.get("backstage"):
            data["backstage"] = BackstageSettingsRequest.from_dict(data["backstage"])
        if data.get("broadcasting"):
            data["broadcasting"] = BroadcastSettingsRequest.from_dict(
                data["broadcasting"]
            )
        if data.get("geofencing"):
            data["geofencing"] = GeofenceSettingsRequest.from_dict(data["geofencing"])
        if data.get("recording"):
            data["recording"] = RecordSettingsRequest.from_dict(data["recording"])
        if data.get("ring"):
            data["ring"] = RingSettingsRequest.from_dict(data["ring"])
        if data.get("screensharing"):
            data["screensharing"] = ScreensharingSettingsRequest.from_dict(
                data["screensharing"]
            )
        if data.get("transcription"):
            data["transcription"] = TranscriptionSettingsRequest.from_dict(
                data["transcription"]
            )
        if data.get("video"):
            data["video"] = VideoSettingsRequest.from_dict(data["video"])
        if data.get("quality_tracks"):
            data["quality_tracks"] = [str(i) for i in data["quality_tracks"]]
        if data.get("auto_on"):
            data["auto_on"] = bool(data["auto_on"])
        if data.get("enabled"):
            data["enabled"] = bool(data["enabled"])

        return cls(**data)
