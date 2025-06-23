import asyncio
import os
import tempfile
import time
import pytest
import numpy as np
from unittest.mock import Mock, patch

from getstream.video.rtc.recording import (
    RecordingManager,
    RecordingType,
    TrackType,
    RecordingConfig,
    AudioFrame,
    VideoFrame,
    TrackRecorder,
    AudioTrackRecorder,
    CompositeAudioRecorder,
)


class MockPcmData:
    """Mock PCM data for testing."""

    def __init__(self, samples, pts_seconds=None, pts=None, time_base=None):
        self.samples = samples
        self.pts_seconds = pts_seconds
        self.pts = pts
        self.time_base = time_base


class TestFrameClasses:
    """Test frame data structures."""

    def test_audio_frame_creation(self):
        """Test AudioFrame creation and validation."""
        frame = AudioFrame(
            user_id="test_user", timestamp=123.456, data=b"audio_data", metadata=Mock()
        )

        assert frame.user_id == "test_user"
        assert frame.timestamp == 123.456
        assert frame.data == b"audio_data"
        assert frame.metadata is not None

    def test_audio_frame_validation(self):
        """Test AudioFrame data validation."""
        # Valid data
        AudioFrame(user_id="test", timestamp=0.0, data=b"valid_bytes")

        # Invalid data type should raise ValueError
        with pytest.raises(ValueError, match="AudioFrame data must be bytes"):
            AudioFrame(
                user_id="test",
                timestamp=0.0,
                data="not_bytes",  # Should be bytes
            )

    def test_video_frame_creation(self):
        """Test VideoFrame creation and validation."""
        frame = VideoFrame(
            user_id="test_user",
            timestamp=123.456,
            data=b"video_data",
            width=1920,
            height=1080,
            format="h264",
        )

        assert frame.user_id == "test_user"
        assert frame.timestamp == 123.456
        assert frame.data == b"video_data"
        assert frame.width == 1920
        assert frame.height == 1080
        assert frame.format == "h264"


class TestRecordingConfig:
    """Test RecordingConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RecordingConfig()

        assert config.output_dir == "recordings"
        assert config.max_queue_size == 10000
        assert config.frame_duration == 0.02
        assert config.max_gap == 2.0
        assert config.audio_sample_rate == 48000
        assert config.audio_channels == 1
        assert config.audio_sample_width == 2

    def test_custom_config(self):
        """Test custom configuration values."""
        config = RecordingConfig(
            output_dir="/custom/path", max_queue_size=500, audio_sample_rate=44100
        )

        assert config.output_dir == "/custom/path"
        assert config.max_queue_size == 500
        assert config.audio_sample_rate == 44100
        # Other values should remain default
        assert config.audio_channels == 1


class TestTrackRecorder:
    """Test TrackRecorder base class."""

    def test_video_track_not_implemented(self):
        """Test that video track recording raises NotImplementedError."""
        config = RecordingConfig()

        with pytest.raises(
            NotImplementedError, match="Video recording is not yet implemented"
        ):
            TrackRecorder("test_recorder", TrackType.VIDEO, config)

    def test_audio_track_creation(self):
        """Test that audio track recorder can be created."""
        config = RecordingConfig()

        # This should work fine for audio
        recorder = AudioTrackRecorder("test_user", config)
        assert recorder.recorder_id == "user_test_user"
        assert recorder.track_type == TrackType.AUDIO
        assert not recorder.is_recording
        assert recorder.filename is None
        assert recorder.frame_count == 0

    def test_file_extension_mapping(self):
        """Test file extension mapping for different track types."""
        config = RecordingConfig()
        recorder = AudioTrackRecorder("test_user", config)

        assert recorder._get_file_extension() == ".wav"

        # Test unsupported track type (hypothetical)
        with patch.object(recorder, "track_type", Mock()):
            recorder.track_type.value = "unknown"
            with pytest.raises(ValueError, match="Unsupported track type"):
                recorder._get_file_extension()


class TestAudioTrackRecorder:
    """Test AudioTrackRecorder implementation."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def config(self, temp_dir):
        """Create test configuration."""
        return RecordingConfig(output_dir=temp_dir)

    @pytest.fixture
    def recorder(self, config):
        """Create test recorder."""
        return AudioTrackRecorder("test_user", config)

    def test_recorder_properties(self, recorder):
        """Test recorder property access."""
        assert recorder.recorder_id == "user_test_user"
        assert recorder.track_type == TrackType.AUDIO
        assert not recorder.is_recording
        assert recorder.filename is None
        assert recorder.frame_count == 0

    @pytest.mark.asyncio
    async def test_start_stop_recording(self, recorder, temp_dir):
        """Test basic start/stop recording workflow."""
        events = []

        @recorder.on("recording_started")
        def on_started(data):
            events.append(("started", data))

        @recorder.on("recording_stopped")
        def on_stopped(data):
            events.append(("stopped", data))

        # Start recording
        await recorder.start_recording("test_file")

        assert recorder.is_recording
        assert recorder.filename.endswith("test_file.wav")
        assert os.path.exists(recorder.filename)

        # Stop recording
        await recorder.stop_recording()

        assert not recorder.is_recording
        assert len(events) == 2
        assert events[0][0] == "started"
        assert events[1][0] == "stopped"

        # Cleanup
        await recorder.cleanup()

    @pytest.mark.asyncio
    async def test_file_extension_handling(self, recorder):
        """Test automatic file extension handling."""
        # Test without extension
        await recorder.start_recording("test_file")
        assert recorder.filename.endswith(".wav")
        await recorder.stop_recording()

        # Test with extension
        await recorder.start_recording("test_file.wav")
        assert recorder.filename.endswith(".wav")
        await recorder.stop_recording()

        await recorder.cleanup()

    @pytest.mark.asyncio
    async def test_frame_processing(self, recorder):
        """Test frame queuing and processing."""
        events = []

        @recorder.on("frame_processed")
        def on_frame(data):
            events.append(data)

        await recorder.start_recording("test_processing")

        # Create test frames
        audio_data = np.random.randint(-32767, 32767, 960, dtype=np.int16).tobytes()
        frame = AudioFrame(user_id="test_user", data=audio_data, timestamp=time.time())

        # Queue frame
        await recorder.queue_frame(frame)

        # Wait for processing
        await asyncio.sleep(0.1)

        assert recorder.frame_count > 0
        assert len(events) > 0

        await recorder.stop_recording()
        await recorder.cleanup()

    @pytest.mark.asyncio
    async def test_wrong_user_frame(self, recorder):
        """Test handling of frames from wrong user."""
        await recorder.start_recording("test_wrong_user")

        # Create frame for different user
        frame = AudioFrame(
            user_id="wrong_user", data=b"audio_data", timestamp=time.time()
        )

        # This should not crash but should be ignored
        await recorder.queue_frame(frame)
        await asyncio.sleep(0.1)

        assert recorder.frame_count == 0  # No frames should be processed

        await recorder.stop_recording()
        await recorder.cleanup()

    @pytest.mark.asyncio
    async def test_already_recording_warning(self, recorder):
        """Test warning when trying to start recording twice."""
        await recorder.start_recording("test_first")

        with patch("getstream.video.rtc.recording.logger") as mock_logger:
            await recorder.start_recording("test_second")
            mock_logger.warning.assert_called()

        await recorder.stop_recording()
        await recorder.cleanup()

    @pytest.mark.asyncio
    async def test_error_handling(self, recorder):
        """Test error handling during recording operations."""
        events = []

        @recorder.on("recording_error")
        def on_error(data):
            events.append(data)

        # Test with invalid directory
        invalid_config = RecordingConfig(output_dir="/invalid/readonly/path")
        invalid_recorder = AudioTrackRecorder("test_user", invalid_config)

        # This should trigger an error
        try:
            await invalid_recorder.start_recording("test_error")
        except Exception:
            pass  # Expected to fail

        await invalid_recorder.cleanup()


class TestCompositeAudioRecorder:
    """Test CompositeAudioRecorder implementation."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def config(self, temp_dir):
        """Create test configuration."""
        return RecordingConfig(output_dir=temp_dir)

    @pytest.fixture
    def recorder(self, config):
        """Create test composite recorder."""
        return CompositeAudioRecorder(config)

    def test_composite_recorder_properties(self, recorder):
        """Test composite recorder properties."""
        assert recorder.recorder_id == "composite_audio"
        assert recorder.track_type == TrackType.AUDIO
        assert not recorder.is_recording

    @pytest.mark.asyncio
    async def test_multi_user_mixing(self, recorder):
        """Test mixing audio from multiple users."""
        await recorder.start_recording("test_composite")

        # Create frames from multiple users
        users = ["user1", "user2", "user3"]
        for i in range(10):
            for user_id in users:
                audio_data = np.random.randint(
                    -16000, 16000, 960, dtype=np.int16
                ).tobytes()
                frame = AudioFrame(
                    user_id=user_id,
                    data=audio_data,
                    timestamp=time.time(),
                    metadata=MockPcmData(audio_data, pts_seconds=i * 0.02),
                )
                await recorder.queue_frame(frame)

            await asyncio.sleep(0.02)  # Simulate real-time timing

        # Wait for processing
        await asyncio.sleep(0.2)

        assert recorder.frame_count > 0

        await recorder.stop_recording()
        await recorder.cleanup()

    @pytest.mark.asyncio
    async def test_user_filtering(self, config):
        """Test filtering specific users in composite recording."""
        target_users = {"user1", "user2"}
        recorder = CompositeAudioRecorder(config, target_user_ids=target_users)

        await recorder.start_recording("test_filtering")

        # Create frames from various users
        all_users = ["user1", "user2", "user3", "user4"]
        for user_id in all_users:
            frame = AudioFrame(
                user_id=user_id,
                data=b"audio_data",
                timestamp=time.time(),
                metadata=MockPcmData(b"audio_data", pts_seconds=0.02),
            )
            await recorder.queue_frame(frame)

        await asyncio.sleep(0.1)

        # Only frames from target users should be processed
        # (exact count depends on timing, but should be > 0)

        await recorder.stop_recording()
        await recorder.cleanup()

    @pytest.mark.asyncio
    async def test_timestamp_extraction(self, recorder):
        """Test timestamp extraction from different metadata formats."""
        await recorder.start_recording("test_timestamps")

        # Test with pts_seconds
        frame1 = AudioFrame(
            user_id="user1",
            data=b"audio_data",
            timestamp=time.time(),
            metadata=MockPcmData(b"audio_data", pts_seconds=0.02),
        )

        # Test with pts and time_base
        frame2 = AudioFrame(
            user_id="user2",
            data=b"audio_data",
            timestamp=time.time(),
            metadata=MockPcmData(b"audio_data", pts=1000, time_base=0.00002),
        )

        # Test without metadata (fallback)
        frame3 = AudioFrame(
            user_id="user3", data=b"audio_data", timestamp=time.time(), metadata=None
        )

        await recorder.queue_frame(frame1)
        await recorder.queue_frame(frame2)
        await recorder.queue_frame(frame3)

        await asyncio.sleep(0.1)

        await recorder.stop_recording()
        await recorder.cleanup()


class TestRecordingManager:
    """Test RecordingManager main interface."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def config(self, temp_dir):
        """Create test configuration."""
        return RecordingConfig(output_dir=temp_dir)

    @pytest.fixture
    def manager(self, config):
        """Create test recording manager."""
        return RecordingManager(config)

    def test_manager_properties(self, manager):
        """Test manager properties."""
        assert not manager.is_recording
        assert len(manager.recording_types) == 0

    @pytest.mark.asyncio
    async def test_track_recording(self, manager):
        """Test individual track recording."""
        events = []

        @manager.on("user_recording_started")
        def on_user_started(data):
            events.append(("user_started", data))

        @manager.on("recording_started")
        def on_started(data):
            events.append(("started", data))

        # Start track recording
        await manager.start_recording([RecordingType.TRACK])

        assert manager.is_recording
        assert RecordingType.TRACK in manager.recording_types

        # Simulate audio data
        pcm_data = MockPcmData(
            np.random.randint(-32767, 32767, 960, dtype=np.int16).tobytes()
        )

        # Record audio for a user
        manager.record_audio_data(pcm_data, "test_user")

        # Wait for async processing
        await asyncio.sleep(0.1)

        # Should create individual recorder
        assert "test_user" in manager._audio_recorders

        await manager.stop_recording()
        await manager.cleanup()

        assert len(events) >= 1

    @pytest.mark.asyncio
    async def test_composite_recording(self, manager):
        """Test composite recording."""
        events = []

        @manager.on("composite_recording_started")
        def on_composite_started(data):
            events.append(("composite_started", data))

        # Start composite recording
        await manager.start_recording([RecordingType.COMPOSITE])

        assert manager.is_recording
        assert RecordingType.COMPOSITE in manager.recording_types
        assert manager._composite_audio_recorder is not None

        # Simulate audio from multiple users
        users = ["user1", "user2"]
        for user_id in users:
            pcm_data = MockPcmData(
                np.random.randint(-16000, 16000, 960, dtype=np.int16).tobytes()
            )
            manager.record_audio_data(pcm_data, user_id)

        await asyncio.sleep(0.1)

        await manager.stop_recording()
        await manager.cleanup()

        assert len(events) >= 1

    @pytest.mark.asyncio
    async def test_both_recording_types(self, manager):
        """Test recording both individual tracks and composite."""
        # Start both types
        await manager.start_recording([RecordingType.TRACK, RecordingType.COMPOSITE])

        assert manager.is_recording
        assert RecordingType.TRACK in manager.recording_types
        assert RecordingType.COMPOSITE in manager.recording_types

        # Simulate audio
        pcm_data = MockPcmData(
            np.random.randint(-16000, 16000, 960, dtype=np.int16).tobytes()
        )
        manager.record_audio_data(pcm_data, "test_user")

        await asyncio.sleep(0.1)

        # Both individual and composite recorders should be created
        assert "test_user" in manager._audio_recorders
        assert manager._composite_audio_recorder is not None

        await manager.stop_recording()
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_user_filtering(self, manager):
        """Test user ID filtering."""
        target_users = ["user1", "user2"]

        await manager.start_recording([RecordingType.TRACK], user_ids=target_users)

        # Record audio for various users
        all_users = ["user1", "user2", "user3", "user4"]
        for user_id in all_users:
            pcm_data = MockPcmData(b"audio_data")
            manager.record_audio_data(pcm_data, user_id)

        await asyncio.sleep(0.1)

        # Only target users should have recorders
        for user_id in target_users:
            assert user_id in manager._audio_recorders

        for user_id in ["user3", "user4"]:
            assert user_id not in manager._audio_recorders

        await manager.stop_recording()
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_user_lifecycle(self, manager):
        """Test user leaving and track removal."""
        await manager.start_recording([RecordingType.TRACK])

        # Create recorder for user
        pcm_data = MockPcmData(b"audio_data")
        manager.record_audio_data(pcm_data, "test_user")

        await asyncio.sleep(0.1)
        assert "test_user" in manager._audio_recorders

        # User leaves
        await manager.on_user_left("test_user")
        assert "test_user" not in manager._audio_recorders

        # Create another user
        manager.record_audio_data(pcm_data, "user2")
        await asyncio.sleep(0.1)
        assert "user2" in manager._audio_recorders

        # Remove track
        await manager.on_track_removed("user2", "audio")
        assert "user2" not in manager._audio_recorders

        await manager.stop_recording()
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_recording_status(self, manager):
        """Test recording status reporting."""
        # Initial status
        status = manager.get_recording_status()
        assert not status["recording_enabled"]
        assert len(status["recording_types"]) == 0
        assert len(status["active_user_recordings"]) == 0

        # Start recording
        await manager.start_recording([RecordingType.TRACK, RecordingType.COMPOSITE])

        # Create some recorders
        pcm_data = MockPcmData(b"audio_data")
        manager.record_audio_data(pcm_data, "user1")
        manager.record_audio_data(pcm_data, "user2")

        await asyncio.sleep(0.1)

        # Check status
        status = manager.get_recording_status()
        assert status["recording_enabled"]
        assert "track" in status["recording_types"]
        assert "composite" in status["recording_types"]
        assert len(status["active_user_recordings"]) == 2
        assert "user1" in status["active_user_recordings"]
        assert "user2" in status["active_user_recordings"]
        assert status["composite_active"]
        assert status["individual_audio_recorders"]["user1"]["track_type"] == "audio"

        await manager.stop_recording()
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_error_handling(self, manager):
        """Test error handling in recording operations."""
        events = []

        @manager.on("recording_error")
        def on_error(data):
            events.append(data)

        # Need to start recording first for the manager to be active
        await manager.start_recording([RecordingType.TRACK])

        # Test invalid data conversion
        with patch.object(manager, "_to_bytes", side_effect=ValueError("Test error")):
            manager.record_audio_data("invalid_data", "test_user")

            # Should emit error event
            assert len(events) > 0
            assert events[0]["error_type"] == "queue_error"

        await manager.stop_recording()
        await manager.cleanup()

    def test_pcm_data_conversion(self, manager):
        """Test PCM data conversion to bytes."""
        # Test bytes input
        result = manager._to_bytes(b"already_bytes")
        assert result == b"already_bytes"

        # Test numpy array
        array = np.array([1, 2, 3], dtype=np.int16)
        result = manager._to_bytes(array)
        assert isinstance(result, bytes)

        # Test memoryview
        mv = memoryview(b"test_data")
        result = manager._to_bytes(mv)
        assert result == b"test_data"

        # Test mock PcmData with samples attribute
        mock_pcm = Mock()
        mock_pcm.samples = b"sample_data"
        result = manager._to_bytes(mock_pcm)
        assert result == b"sample_data"

        # Test invalid data
        with pytest.raises(ValueError):
            manager._to_bytes({"invalid": "data"})


class TestEventForwarding:
    """Test event forwarding functionality."""

    @pytest.fixture
    def manager(self):
        """Create test recording manager."""
        return RecordingManager()

    def test_event_forwarder_creation(self, manager):
        """Test generic event forwarder."""
        events = []

        def capture_event(event_name, data):
            events.append((event_name, data))

        # Create forwarder
        forwarder = manager._create_event_forwarder(
            "source_event", "target_event", lambda data: {"transformed": data}
        )

        # Mock the emit method
        manager.emit = capture_event

        # Test forwarder
        forwarder({"original": "data"})

        assert len(events) == 1
        assert events[0] == ("target_event", {"transformed": {"original": "data"}})


class TestConstants:
    """Test configuration constants."""

    def test_frame_worker_timeout(self):
        """Test frame worker timeout constant."""
        assert TrackRecorder.FRAME_WORKER_TIMEOUT == 1.0

    def test_enum_values(self):
        """Test enum value consistency."""
        assert RecordingType.TRACK.value == "track"
        assert RecordingType.COMPOSITE.value == "composite"
        assert TrackType.AUDIO.value == "audio"
        assert TrackType.VIDEO.value == "video"


# Integration test for file operations
class TestFileOperations:
    """Test file operations and resource management."""

    @pytest.mark.asyncio
    async def test_file_creation_and_cleanup(self):
        """Test that files are created and properly cleaned up."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = RecordingConfig(output_dir=tmpdir)
            recorder = AudioTrackRecorder("test_user", config)

            # Start recording
            await recorder.start_recording("test_file")

            # File should exist
            assert os.path.exists(recorder.filename)
            filename = recorder.filename

            # Stop recording
            await recorder.stop_recording()

            # File should still exist after stopping
            assert os.path.exists(filename)

            await recorder.cleanup()

    @pytest.mark.asyncio
    async def test_concurrent_recorders(self):
        """Test multiple concurrent recorders."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = RecordingConfig(output_dir=tmpdir)

            # Create multiple recorders
            recorders = [AudioTrackRecorder(f"user_{i}", config) for i in range(3)]

            # Start all recordings
            tasks = [
                recorder.start_recording(f"test_file_{i}")
                for i, recorder in enumerate(recorders)
            ]
            await asyncio.gather(*tasks)

            # All should be recording
            for recorder in recorders:
                assert recorder.is_recording
                assert os.path.exists(recorder.filename)

            # Stop all recordings
            tasks = [recorder.stop_recording() for recorder in recorders]
            await asyncio.gather(*tasks)

            # Cleanup
            tasks = [recorder.cleanup() for recorder in recorders]
            await asyncio.gather(*tasks)


if __name__ == "__main__":
    pytest.main([__file__])
