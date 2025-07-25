from typing import Optional

from pyee.asyncio import AsyncIOEventEmitter

from getstream.video.rtc.pb.stream.video.sfu.event import events_pb2
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2

import logging

logger = logging.getLogger(__name__)


class ParticipantsState(AsyncIOEventEmitter):
    """Tracks participants and stream mapping received from the SFU."""

    def __init__(self):
        super().__init__()
        self._participant_by_prefix = {}
        self._track_stream_mapping = {}

    def get_user_from_track_id(self, track_id: str) -> Optional[models_pb2.Participant]:
        # Track IDs have format: participant_id:track_type:...
        # We can extract the participant prefix directly from the track ID
        if ":" in track_id:
            # Extract the participant prefix from the track ID
            prefix = track_id.split(":")[0]
            user = self._participant_by_prefix.get(prefix)
            if user:
                return user

        # Fallback to the old mapping approach if it exists
        stream_id = self._track_stream_mapping.get(track_id)
        if stream_id:
            prefix = stream_id.split(":")[0]
            return self._participant_by_prefix.get(prefix)

        return None

    def get_stream_id_from_track_id(self, track_id: str) -> Optional[str]:
        return self._track_stream_mapping.get(track_id)

    def set_track_stream_mapping(self, mapping: dict):
        logger.debug(f"Setting track stream mapping: {mapping}")
        self._track_stream_mapping = mapping

    def add_participant(self, participant: models_pb2.Participant):
        self._participant_by_prefix[participant.track_lookup_prefix] = participant

    def remove_participant(self, participant: models_pb2.Participant):
        if participant.track_lookup_prefix in self._participant_by_prefix:
            del self._participant_by_prefix[participant.track_lookup_prefix]

    async def _on_participant_joined(self, event: events_pb2.ParticipantJoined):
        self.add_participant(event.participant)
        self.emit("participant_joined", event.participant)

    async def _on_participant_left(self, event: events_pb2.ParticipantLeft):
        self.remove_participant(event.participant)
        self.emit("participant_left", event.participant)
