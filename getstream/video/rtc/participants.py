from typing import Optional, Callable, List
import inspect
import weakref

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
        self._map_handlers = []  # List of weak references to handler functions

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

    def _add_participant(self, participant: models_pb2.Participant):
        self._participant_by_prefix[participant.track_lookup_prefix] = participant
        self._notify_map_handlers()

    def _remove_participant(self, participant: models_pb2.Participant):
        if participant.track_lookup_prefix in self._participant_by_prefix:
            del self._participant_by_prefix[participant.track_lookup_prefix]
            self._notify_map_handlers()

    def get_participants(self) -> List[models_pb2.Participant]:
        """Get the current list of participants."""
        return list(self._participant_by_prefix.values())

    def map(self, handler: Callable[[List[models_pb2.Participant]], None]):
        """
        Subscribe to participant list changes. The handler is called immediately
        with the current list and whenever participants are added or removed.

        The handler is stored as a weak reference, so it will be automatically
        cleaned up when no other references to it exist.

        Args:
            handler: A function that takes a list of participants

        Returns:
            A subscription object that can be used to unsubscribe (optional)

        Example:
            >>> state = ParticipantsState()
            >>> def on_participants(participants):
            ...     print(f"Participants: {len(participants)}")
            >>> subscription = state.map(on_participants)
            Participants: 0
        """

        # Create a weak reference to the handler
        # Use a callback to remove dead references when they're collected
        def cleanup_callback(ref):
            try:
                # Remove this weak reference from the handlers list
                self._map_handlers.remove(ref)
            except (ValueError, AttributeError):
                pass

        # Create a weak reference to the handler
        # The Subscription object will hold a strong reference to the handler
        # to prevent it from being garbage collected (important for inline lambdas)
        # Use WeakMethod for bound methods, ref for other callables
        if inspect.ismethod(handler) or (
            hasattr(handler, "__self__") and hasattr(handler, "__func__")
        ):
            handler_ref = weakref.WeakMethod(handler, cleanup_callback)
        else:
            handler_ref = weakref.ref(handler, cleanup_callback)
        self._map_handlers.append(handler_ref)

        # Call handler immediately with current list
        try:
            handler_fn = handler_ref()
            if handler_fn:
                handler_fn(self.get_participants())
        except Exception as e:
            logger.error(f"Error calling map handler: {e}")

        # Return a simple subscription object
        class Subscription:
            def __init__(self, handlers_list, handler_ref, handler_to_keep_alive):
                self._handlers_list = handlers_list
                self._handler_ref = handler_ref
                # Keep handler alive with a strong reference
                # This is the key: the Subscription holds the only strong reference
                # to the handler, so when the Subscription is garbage collected,
                # the handler is also garbage collected and removed from _map_handlers
                self._handler = handler_to_keep_alive

            def unsubscribe(self):
                try:
                    self._handlers_list.remove(self._handler_ref)
                except (ValueError, AttributeError):
                    pass

        return Subscription(self._map_handlers, handler_ref, handler)

    def _notify_map_handlers(self):
        """Notify all map handlers about participant list changes."""
        participants = self.get_participants()

        # Clean up dead references and call active handlers
        active_handlers = []
        for handler_ref in self._map_handlers:
            handler = handler_ref()
            if handler is not None:
                active_handlers.append(handler_ref)
                try:
                    handler(participants)
                except Exception as e:
                    logger.error(f"Error calling map handler: {e}")

        # Update list to only include active handlers
        self._map_handlers[:] = active_handlers

    async def _on_participant_joined(self, event: events_pb2.ParticipantJoined):
        self._add_participant(event.participant)
        self.emit("participant_joined", event.participant)

    async def _on_participant_left(self, event: events_pb2.ParticipantLeft):
        self._remove_participant(event.participant)
        self.emit("participant_left", event.participant)
