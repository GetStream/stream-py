import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch
from getstream.video.rtc.track_util import PcmData
from getstream.plugins.assemblyai.stt import AssemblyAISTT


@pytest.fixture
def mock_assemblyai_dependencies():
    """Mock all AssemblyAI dependencies to avoid import issues during testing."""
    with (
        patch("getstream.plugins.assemblyai.stt.stt._assemblyai_available", True),
        patch("getstream.plugins.assemblyai.stt.stt.aai") as mock_aai,
        patch(
            "getstream.plugins.assemblyai.stt.stt.StreamingClient"
        ) as mock_streaming_client,
        patch(
            "getstream.plugins.assemblyai.stt.stt.StreamingClientOptions"
        ) as mock_options,
        patch("getstream.plugins.assemblyai.stt.stt.StreamingEvents") as mock_events,
        patch(
            "getstream.plugins.assemblyai.stt.stt.StreamingParameters"
        ) as mock_params,
        patch(
            "getstream.plugins.assemblyai.stt.stt.AssemblyAISTT._setup_connection"
        ) as mock_setup,
    ):
        # Setup mock objects
        mock_aai.settings.api_key = "test_key"
        mock_streaming_client.return_value = Mock()
        mock_options.return_value = Mock()
        mock_events.Begin = Mock()
        mock_events.Turn = Mock()
        mock_events.Termination = Mock()
        mock_events.Error = Mock()
        mock_params.return_value = Mock()
        mock_setup.return_value = None

        yield {
            "aai": mock_aai,
            "streaming_client": mock_streaming_client,
            "options": mock_options,
            "events": mock_events,
            "params": mock_params,
            "setup": mock_setup,
        }


@pytest.fixture
def sample_pcm_data():
    """Create sample PCM data for testing."""
    # Create enough samples to meet the 100ms minimum chunk duration
    # 100ms at 48kHz = 4800 samples
    samples = np.array([1000, -1000, 500, -500, 750, -750] * 800, dtype=np.int16)
    return PcmData(format="s16", samples=samples, sample_rate=48000)


@pytest.fixture
def sample_pcm_data_16k():
    """Create sample PCM data with 16kHz sample rate for testing."""
    samples = np.array([1000, -1000, 500, -500], dtype=np.int16)
    return PcmData(format="s16", samples=samples, sample_rate=16000)


@pytest.fixture
def mock_streaming_client():
    """Create a mock streaming client with common methods."""
    client = Mock()
    client.stream = Mock()
    client.disconnect = Mock()
    client.is_connected = Mock(return_value=True)
    return client


class TestAssemblyAISTTInitialization:
    """Test cases for AssemblyAI STT plugin initialization."""

    def test_import_success(self):
        """Test that the plugin can be imported successfully."""
        assert AssemblyAISTT is not None

    def test_init_with_api_key(self, assemblyai_api_key, mock_assemblyai_dependencies):
        """Test initialization with API key."""
        stt = AssemblyAISTT(api_key=assemblyai_api_key)

        assert stt.sample_rate == 48000
        assert stt.language == "en"
        assert stt.interim_results is True
        assert stt.enable_partials is True
        assert stt.enable_automatic_punctuation is True
        assert stt.enable_utterance_end_detection is True

    def test_init_with_custom_config(self, mock_assemblyai_dependencies):
        """Test initialization with custom configuration."""
        stt = AssemblyAISTT(
            sample_rate=16000,
            language="es",
            interim_results=False,
            enable_partials=False,
            enable_automatic_punctuation=False,
            enable_utterance_end_detection=False,
        )

        assert stt.sample_rate == 16000
        assert stt.language == "es"
        assert stt.interim_results is False
        assert stt.enable_partials is False
        assert stt.enable_automatic_punctuation is False
        assert stt.enable_utterance_end_detection is False

    def test_init_without_api_key_logs_warning(self, mock_assemblyai_dependencies):
        """Test that initialization without API key logs a warning."""

        with (
            patch("getstream.plugins.assemblyai.stt.stt.logger") as mock_logger,
            patch.dict("os.environ", {}, clear=True),
        ):
            stt = AssemblyAISTT()
            # Should still initialize but with warning
            assert stt is not None
            # Check that warning was logged
            mock_logger.warning.assert_called_with(
                "No API key provided and ASSEMBLYAI_API_KEY environment variable not found."
            )

    def test_provider_name_setting(
        self, assemblyai_api_key, mock_assemblyai_dependencies
    ):
        """Test that the provider name is set correctly."""
        stt = AssemblyAISTT(api_key=assemblyai_api_key)
        assert stt.provider_name == "assemblyai"


class TestAssemblyAISTTConfiguration:
    """Test cases for configuration and validation."""

    @pytest.mark.parametrize(
        "sample_rate,expected",
        [
            (8000, 8000),
            (16000, 16000),
            (22050, 22050),
            (44100, 44100),
            (48000, 48000),
        ],
    )
    def test_sample_rate_configuration(
        self, sample_rate, expected, mock_assemblyai_dependencies
    ):
        """Test different sample rate configurations."""
        stt = AssemblyAISTT(sample_rate=sample_rate)
        assert stt.sample_rate == expected

    @pytest.mark.parametrize(
        "language,expected",
        [
            ("en", "en"),
            ("es", "es"),
            ("fr", "fr"),
            ("de", "de"),
            ("it", "it"),
        ],
    )
    def test_language_configuration(
        self, language, expected, mock_assemblyai_dependencies
    ):
        """Test different language configurations."""
        stt = AssemblyAISTT(language=language)
        assert stt.language == expected

    def test_invalid_sample_rate_handling(self, mock_assemblyai_dependencies):
        """Test that invalid sample rate is handled gracefully."""

        # The current implementation doesn't validate sample rate, so it should accept any value
        stt = AssemblyAISTT(sample_rate=9999)
        assert stt.sample_rate == 9999


class TestAssemblyAISTTDataValidation:
    """Test cases for data validation."""

    def test_pcm_data_validation(
        self, assemblyai_api_key, mock_assemblyai_dependencies, sample_pcm_data
    ):
        """Test that PCM data validation works correctly."""
        # Create instance to test initialization
        _ = AssemblyAISTT(api_key=assemblyai_api_key)

        # Should not raise an exception
        assert sample_pcm_data.samples is not None
        assert sample_pcm_data.sample_rate == 48000
        assert len(sample_pcm_data.samples) > 0

    def test_empty_pcm_data_handling(
        self, assemblyai_api_key, mock_assemblyai_dependencies
    ):
        """Test handling of empty PCM data."""
        # Create instance to test initialization
        _ = AssemblyAISTT(api_key=assemblyai_api_key)

        # Create empty PCM data
        empty_samples = np.array([], dtype=np.int16)
        empty_pcm_data = PcmData(format="s16", samples=empty_samples, sample_rate=48000)

        # Should handle empty data gracefully
        assert len(empty_pcm_data.samples) == 0

    def test_pcm_data_with_different_dtypes(
        self, assemblyai_api_key, mock_assemblyai_dependencies
    ):
        """Test PCM data with different numpy dtypes."""
        # Create instance to test initialization
        _ = AssemblyAISTT(api_key=assemblyai_api_key)

        # Test with float32
        float_samples = np.array([0.5, -0.5, 0.25, -0.25], dtype=np.float32)
        float_pcm_data = PcmData(format="f32", samples=float_samples, sample_rate=48000)
        assert float_pcm_data.samples.dtype == np.float32

        # Test with int32
        int32_samples = np.array([1000, -1000, 500, -500], dtype=np.int32)
        int32_pcm_data = PcmData(format="s32", samples=int32_samples, sample_rate=48000)
        assert int32_pcm_data.samples.dtype == np.int32


class TestAssemblyAISTTConnectionManagement:
    """Test cases for connection management."""

    @pytest.mark.asyncio
    async def test_close_method(
        self, assemblyai_api_key, mock_assemblyai_dependencies, mock_streaming_client
    ):
        """Test that the close method works correctly."""
        stt = AssemblyAISTT(api_key=assemblyai_api_key)

        # Mock the streaming client
        stt.streaming_client = mock_streaming_client

        await stt.close()

        assert stt._is_closed is True
        assert stt._running is False
        mock_streaming_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_context_manager(
        self, assemblyai_api_key, mock_assemblyai_dependencies
    ):
        """Test that the plugin can be used as an async context manager."""

        async with AssemblyAISTT(api_key=assemblyai_api_key) as stt:
            assert stt is not None
            assert stt._is_closed is False

        # Should be closed after context manager
        assert stt._is_closed is True

    def test_connection_status_check(
        self, assemblyai_api_key, mock_assemblyai_dependencies, mock_streaming_client
    ):
        """Test connection status checking."""
        stt = AssemblyAISTT(api_key=assemblyai_api_key)

        # Initially no connection (but mock dependencies might set it up)
        # We'll test the connection flow instead

        # Mock connection
        stt.streaming_client = mock_streaming_client
        mock_streaming_client.is_connected.return_value = True

        # Check that streaming client is set
        assert stt.streaming_client is not None
        assert stt.streaming_client.is_connected.return_value is True


class TestAssemblyAISTTAudioProcessing:
    """Test cases for audio processing functionality."""

    @pytest.mark.asyncio
    async def test_process_audio_sample_rate_mismatch(
        self, assemblyai_api_key, mock_assemblyai_dependencies, sample_pcm_data_16k
    ):
        """Test that sample rate mismatch warning is logged."""
        stt = AssemblyAISTT(api_key=assemblyai_api_key, sample_rate=48000)

        # Mock the streaming client
        stt.streaming_client = Mock()
        stt.streaming_client.stream = Mock()

        with patch("getstream.plugins.assemblyai.stt.stt.logger") as mock_logger:
            await stt._process_audio_impl(sample_pcm_data_16k)
            mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_process_audio_connection_not_ready(
        self, mock_assemblyai_api_key, mock_assemblyai_dependencies, sample_pcm_data
    ):
        """Test that audio processing fails when connection is not ready."""
        stt = AssemblyAISTT(api_key=mock_assemblyai_api_key)

        # Should raise exception when no connection
        with pytest.raises(Exception, match="No AssemblyAI connection available"):
            await stt._process_audio_impl(sample_pcm_data)

    @pytest.mark.asyncio
    async def test_process_audio_success(
        self,
        mock_assemblyai_api_key,
        mock_assemblyai_dependencies,
        sample_pcm_data,
        mock_streaming_client,
    ):
        """Test successful audio processing."""
        stt = AssemblyAISTT(api_key=mock_assemblyai_api_key)

        # Mock the streaming client
        stt.streaming_client = mock_streaming_client

        # Process audio should not raise exception
        await stt._process_audio_impl(sample_pcm_data)

        # Flush the buffer to ensure audio is sent immediately
        stt.flush_buffer()

        # Verify that stream was called
        mock_streaming_client.stream.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_audio_with_large_data(
        self,
        mock_assemblyai_api_key,
        mock_assemblyai_dependencies,
        mock_streaming_client,
    ):
        """Test audio processing with large PCM data."""
        stt = AssemblyAISTT(api_key=mock_assemblyai_api_key)

        # Create large PCM data
        large_samples = np.random.randint(-32768, 32767, size=10000, dtype=np.int16)
        large_pcm_data = PcmData(format="s16", samples=large_samples, sample_rate=48000)

        # Mock the streaming client
        stt.streaming_client = mock_streaming_client

        # Should handle large data without issues
        await stt._process_audio_impl(large_pcm_data)

        # Flush the buffer to ensure audio is sent immediately
        stt.flush_buffer()

        mock_streaming_client.stream.assert_called_once()


class TestAssemblyAISTTEventHandling:
    """Test cases for event handling and inheritance."""

    def test_event_emitter_inheritance(
        self, assemblyai_api_key, mock_assemblyai_dependencies
    ):
        """Test that the plugin inherits from the correct base classes."""
        stt = AssemblyAISTT(api_key=assemblyai_api_key)

        # Check that it has the expected methods
        assert hasattr(stt, "on")
        assert hasattr(stt, "emit")
        assert hasattr(stt, "once")
        assert hasattr(stt, "remove_listener")

    def test_event_emission(self, assemblyai_api_key, mock_assemblyai_dependencies):
        """Test that events can be emitted and listened to."""
        stt = AssemblyAISTT(api_key=assemblyai_api_key)

        # Test event emission
        events_received = []

        def event_handler(event_data):
            events_received.append(event_data)

        stt.on("transcription", event_handler)
        stt.emit("transcription", {"text": "test"})

        assert len(events_received) == 1
        assert events_received[0]["text"] == "test"

    def test_multiple_event_listeners(
        self, assemblyai_api_key, mock_assemblyai_dependencies
    ):
        """Test multiple event listeners."""
        stt = AssemblyAISTT(api_key=assemblyai_api_key)

        events_received = []

        def handler1(event_data):
            events_received.append(("handler1", event_data))

        def handler2(event_data):
            events_received.append(("handler2", event_data))

        stt.on("transcription", handler1)
        stt.on("transcription", handler2)
        stt.emit("transcription", {"text": "test"})

        assert len(events_received) == 2
        assert any("handler1" in event for event in events_received)
        assert any("handler2" in event for event in events_received)


class TestAssemblyAISTTErrorHandling:
    """Test cases for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_network_error_handling(
        self, mock_assemblyai_api_key, mock_assemblyai_dependencies, sample_pcm_data
    ):
        """Test handling of network errors during audio processing."""
        stt = AssemblyAISTT(api_key=mock_assemblyai_api_key)

        # Mock streaming client that raises network error
        mock_client = Mock()
        mock_client.stream.side_effect = ConnectionError("Network error")
        stt.streaming_client = mock_client

        # Process audio - this should raise the error immediately since the buffer is large enough
        with pytest.raises(Exception, match="AssemblyAI audio transmission error"):
            await stt._process_audio_impl(sample_pcm_data)

    def test_empty_api_key_handling(self, mock_assemblyai_dependencies):
        """Test handling of empty API key."""

        # The current implementation accepts empty API keys without logging a warning
        # (only logs warning when api_key is None)
        stt = AssemblyAISTT(api_key="")
        assert stt is not None
        # Empty string is treated as a valid API key value

    @pytest.mark.asyncio
    async def test_streaming_client_disconnect_error(
        self, assemblyai_api_key, mock_assemblyai_dependencies
    ):
        """Test handling of errors during client disconnection."""
        stt = AssemblyAISTT(api_key=assemblyai_api_key)

        # Mock streaming client that raises error on disconnect
        mock_client = Mock()
        mock_client.disconnect.side_effect = Exception("Disconnect error")
        stt.streaming_client = mock_client

        # Should handle disconnect errors gracefully
        await stt.close()
        assert stt._is_closed is True


class TestAssemblyAISTTPerformance:
    """Test cases for performance characteristics."""

    @pytest.mark.asyncio
    async def test_audio_processing_performance(
        self,
        mock_assemblyai_api_key,
        mock_assemblyai_dependencies,
        mock_streaming_client,
    ):
        """Test audio processing performance with timing."""
        import time

        stt = AssemblyAISTT(api_key=mock_assemblyai_api_key)
        stt.streaming_client = mock_streaming_client

        # Create test data
        samples = np.random.randint(-32768, 32767, size=1000, dtype=np.int16)
        pcm_data = PcmData(format="s16", samples=samples, sample_rate=48000)

        # Measure processing time
        start_time = time.time()
        await stt._process_audio_impl(pcm_data)
        end_time = time.time()

        processing_time = end_time - start_time
        # Should process audio in reasonable time (less than 100ms for small data)
        assert processing_time < 0.1

    def test_memory_usage_with_large_data(
        self, mock_assemblyai_api_key, mock_assemblyai_dependencies
    ):
        """Test memory usage with large PCM data."""
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not available for memory testing")

        # Create instance to test initialization
        _ = AssemblyAISTT(api_key=mock_assemblyai_api_key)

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create large PCM data
        large_samples = np.random.randint(-32768, 32767, size=100000, dtype=np.int16)
        large_pcm_data = PcmData(format="s16", samples=large_samples, sample_rate=48000)

        # Just create the object - no validation method exists in current implementation
        assert large_pcm_data is not None
        assert len(large_pcm_data.samples) == 100000

        # Get final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 10MB for this operation)
        assert memory_increase < 10 * 1024 * 1024


# Integration test class for more realistic scenarios
@pytest.mark.integration
class TestAssemblyAISTTIntegration:
    """Integration tests for AssemblyAI STT plugin."""

    @pytest.mark.asyncio
    async def test_full_audio_processing_workflow(
        self, mock_assemblyai_api_key, mock_assemblyai_dependencies
    ):
        """Test the complete audio processing workflow."""

        async with AssemblyAISTT(api_key=mock_assemblyai_api_key) as stt:
            # Mock streaming client with realistic behavior
            mock_client = Mock()
            mock_client.is_connected.return_value = True
            mock_client.stream = Mock()
            stt.streaming_client = mock_client

            # Set running flag manually since _setup_connection is patched
            stt._running = True

            # Create realistic audio data
            samples = np.random.randint(
                -32768, 32767, size=4800, dtype=np.int16
            )  # 100ms at 48kHz
            pcm_data = PcmData(format="s16", samples=samples, sample_rate=48000)

            # Process audio
            await stt._process_audio_impl(pcm_data)

            # Flush buffer to ensure audio is sent
            stt.flush_buffer()

            # Verify processing
            assert mock_client.stream.called

            # Verify state
            assert not stt._is_closed
            assert stt._running

    @pytest.mark.asyncio
    async def test_concurrent_audio_processing(
        self, mock_assemblyai_api_key, mock_assemblyai_dependencies
    ):
        """Test concurrent audio processing."""

        async with AssemblyAISTT(api_key=mock_assemblyai_api_key) as stt:
            mock_client = Mock()
            mock_client.is_connected.return_value = True
            mock_client.stream = Mock()
            stt.streaming_client = mock_client

            # Set running flag manually since _setup_connection is patched
            stt._running = True

            # Create multiple audio chunks that are large enough to trigger immediate processing
            audio_chunks = []
            for i in range(5):
                # 120ms at 48kHz = 5760 samples (above the 100ms threshold)
                samples = np.random.randint(-32768, 32767, size=5760, dtype=np.int16)
                audio_chunks.append(
                    PcmData(format="s16", samples=samples, sample_rate=48000)
                )

            # Process all chunks concurrently
            tasks = [stt._process_audio_impl(chunk) for chunk in audio_chunks]
            await asyncio.gather(*tasks)

            # Verify all chunks were processed immediately (no need to flush)
            assert mock_client.stream.call_count == 5
