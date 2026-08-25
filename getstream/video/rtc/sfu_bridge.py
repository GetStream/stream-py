"""Map Rust RtcSession events onto the historic protobuf SFU event surface."""

from __future__ import annotations

import logging
from typing import Any, Optional

from getstream.video.rtc.connection_utils import ConnectionState
from getstream.video.rtc.pb.stream.video.sfu.event import events_pb2
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2

logger = logging.getLogger(__name__)

_CALLING_STATE = {
    "idle": ConnectionState.IDLE,
    "joining": ConnectionState.JOINING,
    "joined": ConnectionState.JOINED,
    "reconnecting": ConnectionState.RECONNECTING,
    "migrating": ConnectionState.MIGRATING,
    "reconnecting_failed": ConnectionState.RECONNECTING_FAILED,
    "left": ConnectionState.LEFT,
    "offline": ConnectionState.OFFLINE,
}

_TRACK_TYPE_NAME = {
    0: "unspecified",
    1: "audio",
    2: "video",
    3: "screenshare",
    4: "screenshare_audio",
}


def participant_from_dict(data: Optional[dict]) -> models_pb2.Participant:
    data = data or {}
    participant = models_pb2.Participant(
        user_id=data.get("user_id") or "",
        session_id=data.get("session_id") or "",
        name=data.get("name") or "",
        image=data.get("image") or "",
        track_lookup_prefix=data.get("track_lookup_prefix") or "",
        is_speaking=bool(data.get("is_speaking")),
        is_dominant_speaker=bool(data.get("is_dominant_speaker")),
        audio_level=float(data.get("audio_level") or 0.0),
        roles=list(data.get("roles") or []),
        published_tracks=list(data.get("published_tracks") or []),
        connection_quality=int(data.get("connection_quality") or 0),
        source=int(data.get("source") or 0),
    )
    return participant


async def dispatch_rust_event(connection_manager, event: dict[str, Any]) -> None:
    kind = event.get("kind")
    if not kind:
        return

    if kind == "participant_joined":
        payload = events_pb2.ParticipantJoined(
            participant=participant_from_dict(event.get("participant"))
        )
        await connection_manager.participants_state._on_participant_joined(payload)
        for track_type in payload.participant.published_tracks:
            published = events_pb2.TrackPublished(
                user_id=payload.participant.user_id,
                session_id=payload.participant.session_id,
                type=track_type,
            )
            published.participant.CopyFrom(payload.participant)
            await connection_manager._subscription_manager.handle_track_published(
                published
            )
        connection_manager.emit("participant_joined", payload)
        return

    if kind == "participant_left":
        payload = events_pb2.ParticipantLeft(
            participant=participant_from_dict(event.get("participant"))
        )
        await connection_manager.participants_state._on_participant_left(payload)
        connection_manager.emit("participant_left", payload)
        return

    if kind == "participant_updated":
        payload = events_pb2.ParticipantUpdated(
            participant=participant_from_dict(event.get("participant"))
        )
        connection_manager.participants_state._add_participant(payload.participant)
        connection_manager.emit("participant_updated", payload)
        return

    if kind == "track_published":
        payload = events_pb2.TrackPublished(
            user_id=event.get("user_id") or "",
            session_id=event.get("session_id") or "",
            type=int(event.get("track_type") or 0),
        )
        for participant in connection_manager.participants_state.get_participants():
            if participant.session_id == payload.session_id:
                payload.participant.CopyFrom(participant)
                break
        await connection_manager._subscription_manager.handle_track_published(payload)
        connection_manager.emit("track_published", payload)
        return

    if kind == "track_unpublished":
        payload = events_pb2.TrackUnpublished(
            user_id=event.get("user_id") or "",
            session_id=event.get("session_id") or "",
            type=int(event.get("track_type") or 0),
        )
        await connection_manager._subscription_manager.handle_track_unpublished(payload)
        connection_manager.emit("track_unpublished", payload)
        return

    if kind == "dominant_speaker_changed":
        payload = events_pb2.DominantSpeakerChanged(
            user_id=event.get("user_id") or "",
            session_id=event.get("session_id") or "",
        )
        connection_manager.emit("dominant_speaker_changed", payload)
        return

    if kind == "audio_level_changed":
        payload = events_pb2.AudioLevelChanged()
        for level in event.get("levels") or []:
            payload.audio_levels.add(
                user_id=level.get("user_id") or "",
                session_id=level.get("session_id") or "",
                level=float(level.get("level") or 0.0),
                is_speaking=bool(level.get("is_speaking")),
            )
        connection_manager.emit("audio_level_changed", payload)
        return

    if kind == "connection_quality_changed":
        payload = events_pb2.ConnectionQualityChanged()
        for item in event.get("updates") or []:
            payload.connection_quality_updates.add(
                user_id=item.get("user_id") or "",
                session_id=item.get("session_id") or "",
                connection_quality=int(item.get("connection_quality") or 0),
            )
        connection_manager.emit("connection_quality_changed", payload)
        return

    if kind == "pins_updated":
        payload = events_pb2.PinsChanged()
        for pin in event.get("pins") or []:
            payload.pins.add(
                user_id=pin.get("user_id") or "",
                session_id=pin.get("session_id") or "",
            )
        connection_manager.emit("pins_updated", payload)
        return

    if kind == "call_ended":
        connection_manager.emit("call_ended", events_pb2.CallEnded())
        return

    if kind == "error":
        error = models_pb2.Error(
            code=int(event.get("code") or 0),
            message=event.get("message") or "",
            should_retry=bool(event.get("should_retry")),
        )
        payload = events_pb2.Error(error=error)
        connection_manager.emit("error", payload)
        return

    if kind == "calling_state_changed":
        state = _CALLING_STATE.get(event.get("state"))
        if state is not None:
            previous = connection_manager.connection_state
            connection_manager.connection_state = state
            if (
                previous == ConnectionState.RECONNECTING
                and state == ConnectionState.JOINED
            ):
                connection_manager.emit(
                    "reconnection_success",
                    {"strategy": "FAST", "duration": 0},
                )
            if state == ConnectionState.RECONNECTING_FAILED:
                connection_manager.emit(
                    "reconnection_failed",
                    {"reason": "rust reconnect failed"},
                )
        return

    if kind == "coordinator":
        connection_manager.emit("coordinator", event)
        return

    connection_manager.emit(kind, event)


def track_type_name(track_type: int) -> str:
    return _TRACK_TYPE_NAME.get(int(track_type), "unspecified")
