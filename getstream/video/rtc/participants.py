from typing import Any, Callable, List
import inspect
import weakref

from pyee.asyncio import AsyncIOEventEmitter

from getstream import _rust

import logging

logger = logging.getLogger(__name__)


class ParticipantsState(AsyncIOEventEmitter):
    """Tracks the participants of the call, this participant included."""

    def __init__(self):
        super().__init__()
        self._participant_by_session_id = {}
        self._map_handlers = []  # List of weak references to handler functions

    def emit(self, event: str, *args: Any, unsafe: bool = False, **kwargs: Any) -> bool:
        """Calls the handlers of `event`. Unless `unsafe`, a handler that raises
        is logged, so it cannot stop the task that emits."""
        if unsafe:
            return super().emit(event, *args, **kwargs)
        try:
            return super().emit(event, *args, **kwargs)
        except Exception:
            logger.exception(f"A {event!r} handler failed")
            return True

    def _add_participant(self, participant: _rust.RemoteParticipant):
        self._participant_by_session_id[participant.session_id] = participant
        self._notify_map_handlers()

    def _remove_participant(self, participant: _rust.RemoteParticipant):
        if participant.session_id in self._participant_by_session_id:
            del self._participant_by_session_id[participant.session_id]
            self._notify_map_handlers()

    def _replace_participants(self, participants: List[_rust.RemoteParticipant]):
        self._participant_by_session_id = {p.session_id: p for p in participants}
        self._notify_map_handlers()

    def get_participants(self) -> List[_rust.RemoteParticipant]:
        """Get the current list of participants."""
        return list(self._participant_by_session_id.values())

    def map(self, handler: Callable[[List[_rust.RemoteParticipant]], None]):
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

    async def _on_participant_joined(self, event: _rust.ParticipantJoined):
        self._add_participant(event.participant)
        self.emit("participant_joined", event.participant)

    async def _on_participant_left(self, event: _rust.ParticipantLeft):
        self._remove_participant(event.participant)
        self.emit("participant_left", event.participant)
