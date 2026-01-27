"""Tests for Tracer class and sanitize_value function."""

from datetime import datetime


from getstream.video.rtc.tracer import Tracer, sanitize_value


class TestSanitizeValue:
    """Tests for sanitize_value function."""

    def test_primitives_unchanged(self):
        assert sanitize_value("hello") == "hello"
        assert sanitize_value(42) == 42
        assert sanitize_value(3.14) == 3.14
        assert sanitize_value(True) is True
        assert sanitize_value(None) is None

    def test_datetime_to_milliseconds(self):
        dt = datetime(2024, 1, 15, 12, 30, 45, 500000)  # 500ms
        result = sanitize_value(dt)
        assert isinstance(result, int)
        # Should be milliseconds timestamp
        assert result == int(dt.timestamp() * 1000)

    def test_protobuf_message_to_dict(self):
        from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2

        participant = models_pb2.Participant()
        participant.user_id = "test-user"
        participant.session_id = "session-123"

        result = sanitize_value(participant)
        assert isinstance(result, dict)
        assert result["userId"] == "test-user"  # camelCase from protobuf
        assert result["sessionId"] == "session-123"

    def test_nested_dict(self):
        data = {
            "outer": {
                "inner": datetime(2024, 1, 1, 0, 0, 0),
                "value": 123,
            }
        }
        result = sanitize_value(data)
        assert isinstance(result["outer"]["inner"], int)
        assert result["outer"]["value"] == 123

    def test_list(self):
        data = [datetime(2024, 1, 1), "string", 42]
        result = sanitize_value(data)
        assert isinstance(result[0], int)
        assert result[1] == "string"
        assert result[2] == 42

    def test_bytes_to_hex(self):
        data = b"\xde\xad\xbe\xef"
        result = sanitize_value(data)
        assert result == "deadbeef"


class TestTracer:
    """Tests for Tracer class."""

    def test_trace_adds_record_with_correct_format(self):
        tracer = Tracer()
        tracer.trace("test-tag", "0-pub", {"key": "value"})

        assert len(tracer) == 1
        snapshot = tracer.take()
        record = snapshot.snapshot[0]

        assert record[0] == "test-tag"  # tag
        assert record[1] == "0-pub"  # id
        assert record[2] == {"key": "value"}  # data
        assert isinstance(record[3], int)  # timestamp_ms

    def test_take_clears_buffer_and_returns_snapshot(self):
        tracer = Tracer()
        tracer.trace("event1", "id1", {})
        tracer.trace("event2", "id2", {})

        assert len(tracer) == 2

        snapshot = tracer.take()
        assert len(snapshot.snapshot) == 2
        assert len(tracer) == 0  # Buffer cleared

    def test_rollback_restores_buffer(self):
        tracer = Tracer()
        tracer.trace("event1", "id1", {})

        snapshot = tracer.take()
        assert len(tracer) == 0

        # Add new trace after take
        tracer.trace("event2", "id2", {})
        assert len(tracer) == 1

        # Rollback prepends original traces
        snapshot.rollback()
        assert len(tracer) == 2

        # Original trace should be first
        new_snapshot = tracer.take()
        assert new_snapshot.snapshot[0][0] == "event1"
        assert new_snapshot.snapshot[1][0] == "event2"

    def test_disabled_tracer_ignores_traces(self):
        tracer = Tracer()
        tracer.trace("event1", "id1", {})
        assert len(tracer) == 1

        tracer.set_enabled(False)
        tracer.trace("event2", "id2", {})
        assert len(tracer) == 0  # Cleared when disabled

        tracer.set_enabled(True)
        tracer.trace("event3", "id3", {})
        assert len(tracer) == 1

    def test_dispose_clears_buffer(self):
        tracer = Tracer()
        tracer.trace("event1", "id1", {})
        tracer.trace("event2", "id2", {})
        assert len(tracer) == 2

        tracer.dispose()
        assert len(tracer) == 0
