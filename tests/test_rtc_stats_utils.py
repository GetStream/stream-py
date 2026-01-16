from getstream.video.rtc.stats_tracer import StatsTracer


class _DummyConnectionManager:
    twirp_signaling_client = None
    twirp_context = None
    session_id = None


def test_delta_compress_removes_unchanged_and_sets_timestamp():
    tracer = StatsTracer(_DummyConnectionManager())
    old_stats = {
        "id1": {"id": "id1", "timestamp": 1000, "foo": 1, "bar": 2},
    }
    new_stats = {
        "id1": {"id": "id1", "timestamp": 2000, "foo": 1, "bar": 3},
    }

    compressed = tracer._delta_compress(old_stats, new_stats)

    report = compressed["id1"]
    assert "foo" not in report
    assert report["bar"] == 3
    assert report["timestamp"] == 0
    assert compressed["timestamp"] == 2000


def test_aggregate_samples_uses_weighted_average():
    tracer = StatsTracer(_DummyConnectionManager())
    samples = [
        {"avg_frame_time_ms": 10.0, "avg_fps": 24.0, "weight": 10},
        {"avg_frame_time_ms": 20.0, "avg_fps": 30.0, "weight": 30},
    ]

    aggregated = tracer._aggregate_samples(samples)

    assert aggregated["avg_frame_time_ms"] == 17.5
    assert aggregated["avg_fps"] == 28.5
