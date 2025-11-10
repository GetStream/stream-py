"""Tests for ParticipantsState class."""

import gc
from getstream.video.rtc.participants import ParticipantsState
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2


class TestParticipantsState:
    """Test suite for ParticipantsState."""

    def test_initial_state_empty(self):
        """Test that ParticipantsState starts with empty participant list."""
        state = ParticipantsState()
        participants = state.get_participants()
        assert participants == []
        assert len(participants) == 0

    def test_add_participant(self):
        """Test adding a single participant."""
        state = ParticipantsState()

        p1 = models_pb2.Participant()
        p1.user_id = "user1"
        p1.track_lookup_prefix = "prefix1"

        state._add_participant(p1)

        participants = state.get_participants()
        assert len(participants) == 1
        assert participants[0].user_id == "user1"
        assert participants[0].track_lookup_prefix == "prefix1"

    def test_add_multiple_participants(self):
        """Test adding multiple participants."""
        state = ParticipantsState()

        p1 = models_pb2.Participant()
        p1.user_id = "user1"
        p1.track_lookup_prefix = "prefix1"

        p2 = models_pb2.Participant()
        p2.user_id = "user2"
        p2.track_lookup_prefix = "prefix2"

        p3 = models_pb2.Participant()
        p3.user_id = "user3"
        p3.track_lookup_prefix = "prefix3"

        state._add_participant(p1)
        state._add_participant(p2)
        state._add_participant(p3)

        participants = state.get_participants()
        assert len(participants) == 3

        user_ids = {p.user_id for p in participants}
        assert user_ids == {"user1", "user2", "user3"}

    def test_remove_participant(self):
        """Test removing a participant."""
        state = ParticipantsState()

        p1 = models_pb2.Participant()
        p1.user_id = "user1"
        p1.track_lookup_prefix = "prefix1"

        p2 = models_pb2.Participant()
        p2.user_id = "user2"
        p2.track_lookup_prefix = "prefix2"

        state._add_participant(p1)
        state._add_participant(p2)
        assert len(state.get_participants()) == 2

        state._remove_participant(p1)
        participants = state.get_participants()
        assert len(participants) == 1
        assert participants[0].user_id == "user2"

    def test_remove_nonexistent_participant(self):
        """Test removing a participant that doesn't exist (should not raise error)."""
        state = ParticipantsState()

        p1 = models_pb2.Participant()
        p1.user_id = "user1"
        p1.track_lookup_prefix = "prefix1"

        # Should not raise an error
        state._remove_participant(p1)
        assert len(state.get_participants()) == 0

    def test_map_called_immediately(self):
        """Test that map handler is called immediately with current participant list."""
        state = ParticipantsState()

        call_count = 0
        last_participants = None

        def handler(participants):
            nonlocal call_count, last_participants
            call_count += 1
            last_participants = participants

        _subscription = state.map(handler)

        assert call_count == 1
        assert last_participants == []

    def test_map_called_on_add_participant(self):
        """Test that map handler is called when participant is added."""
        state = ParticipantsState()

        results = []

        def handler(participants):
            results.append(len(participants))

        _subscription = state.map(handler)
        assert results == [0]

        p1 = models_pb2.Participant()
        p1.user_id = "user1"
        p1.track_lookup_prefix = "prefix1"
        state._add_participant(p1)

        assert results == [0, 1]

        p2 = models_pb2.Participant()
        p2.user_id = "user2"
        p2.track_lookup_prefix = "prefix2"
        state._add_participant(p2)

        assert results == [0, 1, 2]

    def test_map_called_on_remove_participant(self):
        """Test that map handler is called when participant is removed."""
        state = ParticipantsState()

        p1 = models_pb2.Participant()
        p1.user_id = "user1"
        p1.track_lookup_prefix = "prefix1"
        state._add_participant(p1)

        results = []

        def handler(participants):
            results.append(len(participants))

        _subscription = state.map(handler)
        assert results == [1]

        state._remove_participant(p1)
        assert results == [1, 0]

    def test_map_with_lambda(self):
        """Test that map works with lambda expressions."""
        state = ParticipantsState()

        results = []
        _subscription = state.map(
            lambda participants: results.append(len(participants))
        )

        assert results == [0]

        p1 = models_pb2.Participant()
        p1.user_id = "user1"
        p1.track_lookup_prefix = "prefix1"
        state._add_participant(p1)

        assert results == [0, 1]

    def test_map_multiple_handlers(self):
        """Test that multiple handlers can be registered."""
        state = ParticipantsState()

        results1 = []
        results2 = []
        results3 = []

        _sub1 = state.map(lambda participants: results1.append(len(participants)))
        _sub2 = state.map(lambda participants: results2.append(len(participants)))
        _sub3 = state.map(lambda participants: results3.append(len(participants)))

        assert results1 == [0]
        assert results2 == [0]
        assert results3 == [0]

        p1 = models_pb2.Participant()
        p1.user_id = "user1"
        p1.track_lookup_prefix = "prefix1"
        state._add_participant(p1)

        assert results1 == [0, 1]
        assert results2 == [0, 1]
        assert results3 == [0, 1]

    def test_unsubscribe(self):
        """Test that unsubscribe stops handler from being called."""
        state = ParticipantsState()

        results = []

        def handler(participants):
            results.append(len(participants))

        subscription = state.map(handler)
        assert results == [0]

        p1 = models_pb2.Participant()
        p1.user_id = "user1"
        p1.track_lookup_prefix = "prefix1"
        state._add_participant(p1)
        assert results == [0, 1]

        # Unsubscribe
        subscription.unsubscribe()

        # Add another participant - handler should NOT be called
        p2 = models_pb2.Participant()
        p2.user_id = "user2"
        p2.track_lookup_prefix = "prefix2"
        state._add_participant(p2)

        assert results == [0, 1]  # Should not have changed

    def test_weak_reference_cleanup_with_regular_function(self):
        """Test that handler is cleaned up when subscription is garbage collected."""
        state = ParticipantsState()

        results = []

        def handler(participants):
            results.append(len(participants))

        subscription = state.map(handler)
        assert results == [0]
        assert len(state._map_handlers) == 1

        # Delete subscription and handler, force garbage collection
        del subscription
        del handler
        gc.collect()

        # Handler should be cleaned up
        p1 = models_pb2.Participant()
        p1.user_id = "user1"
        p1.track_lookup_prefix = "prefix1"
        state._add_participant(p1)

        # Results should not have changed (handler was garbage collected)
        assert results == [0]
        assert len(state._map_handlers) == 0

    def test_weak_reference_cleanup_with_lambda(self):
        """Test that lambda handler is cleaned up when subscription is garbage collected."""
        state = ParticipantsState()

        results = []
        subscription = state.map(lambda participants: results.append(len(participants)))

        assert results == [0]
        assert len(state._map_handlers) == 1

        # Delete subscription, force garbage collection
        del subscription
        gc.collect()

        # Handler should be cleaned up
        p1 = models_pb2.Participant()
        p1.user_id = "user1"
        p1.track_lookup_prefix = "prefix1"
        state._add_participant(p1)

        # Results should not have changed (handler was garbage collected)
        assert results == [0]
        assert len(state._map_handlers) == 0

    def test_selective_cleanup_multiple_subscriptions(self):
        """Test that only deleted subscriptions are cleaned up."""
        state = ParticipantsState()

        results1 = []
        results2 = []
        results3 = []

        _sub1 = state.map(lambda participants: results1.append(len(participants)))
        sub2 = state.map(lambda participants: results2.append(len(participants)))
        _sub3 = state.map(lambda participants: results3.append(len(participants)))

        assert len(state._map_handlers) == 3

        # Delete sub2
        del sub2
        gc.collect()

        # Add a participant
        p1 = models_pb2.Participant()
        p1.user_id = "user1"
        p1.track_lookup_prefix = "prefix1"
        state._add_participant(p1)

        # Only sub1 and sub3 should have been called
        assert results1 == [0, 1]
        assert results2 == [0]  # Not called after deletion
        assert results3 == [0, 1]
        assert len(state._map_handlers) == 2

    def test_map_handler_receives_actual_participants(self):
        """Test that handler receives the actual participant objects."""
        state = ParticipantsState()

        received_participants = []

        def handler(participants):
            # Store a copy of the list
            received_participants.clear()
            received_participants.extend(participants)

        _subscription = state.map(handler)

        p1 = models_pb2.Participant()
        p1.user_id = "alice"
        p1.track_lookup_prefix = "alice_123"
        state._add_participant(p1)

        assert len(received_participants) == 1
        assert received_participants[0].user_id == "alice"
        assert received_participants[0].track_lookup_prefix == "alice_123"

        p2 = models_pb2.Participant()
        p2.user_id = "bob"
        p2.track_lookup_prefix = "bob_456"
        state._add_participant(p2)

        assert len(received_participants) == 2
        user_ids = {p.user_id for p in received_participants}
        assert user_ids == {"alice", "bob"}

    def test_map_with_existing_participants(self):
        """Test that map handler is called immediately with existing participants."""
        state = ParticipantsState()

        # Add participants before subscribing
        p1 = models_pb2.Participant()
        p1.user_id = "user1"
        p1.track_lookup_prefix = "prefix1"

        p2 = models_pb2.Participant()
        p2.user_id = "user2"
        p2.track_lookup_prefix = "prefix2"

        state._add_participant(p1)
        state._add_participant(p2)

        # Now subscribe
        results = []

        def handler(participants):
            results.append(len(participants))

        _subscription = state.map(handler)

        # Handler should be called immediately with existing 2 participants
        assert results == [2]

    def test_get_user_from_track_id_with_prefix(self):
        """Test get_user_from_track_id using track prefix."""
        state = ParticipantsState()

        p1 = models_pb2.Participant()
        p1.user_id = "user1"
        p1.track_lookup_prefix = "prefix1"
        state._add_participant(p1)

        # Track ID format: participant_id:track_type:...
        user = state.get_user_from_track_id("prefix1:audio:123")
        assert user is not None
        assert user.user_id == "user1"

    def test_get_user_from_track_id_not_found(self):
        """Test get_user_from_track_id returns None for unknown track."""
        state = ParticipantsState()

        user = state.get_user_from_track_id("unknown:audio:123")
        assert user is None

    def test_get_stream_id_from_track_id(self):
        """Test get_stream_id_from_track_id."""
        state = ParticipantsState()

        mapping = {
            "track1": "stream1",
            "track2": "stream2",
        }
        state.set_track_stream_mapping(mapping)

        stream_id = state.get_stream_id_from_track_id("track1")
        assert stream_id == "stream1"

        stream_id = state.get_stream_id_from_track_id("track2")
        assert stream_id == "stream2"

        stream_id = state.get_stream_id_from_track_id("track3")
        assert stream_id is None

    def test_map_with_bound_method(self):
        """Test that map works with bound methods."""
        state = ParticipantsState()

        class Handler:
            def __init__(self):
                self.results = []

            def on_participants(self, participants):
                self.results.append(len(participants))

        handler_obj = Handler()

        # Subscribe with a bound method
        _subscription = state.map(handler_obj.on_participants)

        # Should be called immediately
        assert handler_obj.results == [0]

        # Add a participant
        p1 = models_pb2.Participant()
        p1.user_id = "user1"
        p1.track_lookup_prefix = "prefix1"
        state._add_participant(p1)

        # Handler should be called
        assert handler_obj.results == [0, 1]

        # Add another participant
        p2 = models_pb2.Participant()
        p2.user_id = "user2"
        p2.track_lookup_prefix = "prefix2"
        state._add_participant(p2)

        # Handler should be called again
        assert handler_obj.results == [0, 1, 2]

    def test_weak_reference_cleanup_with_bound_method(self):
        """Test that bound method handlers are cleaned up when object is garbage collected."""
        state = ParticipantsState()

        class Handler:
            def __init__(self):
                self.results = []

            def on_participants(self, participants):
                self.results.append(len(participants))

        handler_obj = Handler()
        _subscription = state.map(handler_obj.on_participants)

        assert handler_obj.results == [0]
        assert len(state._map_handlers) == 1

        # Delete the handler object and subscription, force garbage collection
        del handler_obj
        del _subscription
        gc.collect()

        # Handler should be cleaned up
        p1 = models_pb2.Participant()
        p1.user_id = "user1"
        p1.track_lookup_prefix = "prefix1"
        state._add_participant(p1)

        # No handlers should remain
        assert len(state._map_handlers) == 0
